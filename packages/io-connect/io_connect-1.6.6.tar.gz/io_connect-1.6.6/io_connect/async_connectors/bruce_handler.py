import asyncio
import logging
import aiohttp

# External Imports
import requests
from typeguard import typechecked
import io_connect.constants as c
from typing import Optional, Literal, Union
import json
import logging
from io_connect.async_connectors.file_logger import AsyncLoggerConfigurator
from io_connect.utilities.store import AsyncLogger, ASYNC_ERROR_MESSAGE


@typechecked
class AsyncBruceHandler:
    __version__ = c.VERSION

    # Class-level shared connection pool
    _shared_connector: Optional[aiohttp.TCPConnector] = None
    _connector_lock = asyncio.Lock()

    # Connection pool configuration (class-level, shared across all instances)
    # These can be modified directly: AsyncDataAccess._pool_limit = 1000
    _pool_limit: int = 200  # Total connection pool size
    _pool_limit_per_host: int = 50  # Max connections per host
    _pool_keepalive_timeout: int = 30  # Keep connections alive (seconds)
    _pool_dns_cache_ttl: int = 300  # DNS cache TTL (seconds)

    def __init__(
        self,
        user_id: str,
        data_url: str,
        organisation_id=str,
        on_prem: Optional[bool] = False,
        logger: Optional[
            Union[AsyncLogger, AsyncLoggerConfigurator, logging.Logger]
        ] = None,
        extra_params: Optional[dict] = {},
    ):
        self.user_id = user_id
        self.data_url = data_url
        self.organisation_id = organisation_id
        self.header = {"userID": user_id}
        self.on_prem = on_prem
        self.logger = logger if logger is not None else AsyncLogger()
        self.extra_params = extra_params
        self.timeout = aiohttp.ClientTimeout(total=60, connect=30)

    @classmethod
    async def _get_shared_connector(cls) -> aiohttp.TCPConnector:
        """
        Get or create a shared connection pool for all AsyncDataAccess instances.

        Returns:
            aiohttp.TCPConnector: Shared connector with configurable connection pooling
        """
        async with cls._connector_lock:
            # Check if connector exists and is healthy
            if cls._shared_connector is None or cls._shared_connector.closed:
                # Clean up old connector if it exists
                if cls._shared_connector is not None:
                    await cls._shared_connector.close()

                # Create new healthy connector
                cls._shared_connector = aiohttp.TCPConnector(
                    limit=cls._pool_limit,  # Total connection pool size
                    limit_per_host=cls._pool_limit_per_host,  # Max connections per host
                    ttl_dns_cache=cls._pool_dns_cache_ttl,  # DNS cache TTL
                    use_dns_cache=True,  # Enable DNS caching
                    keepalive_timeout=cls._pool_keepalive_timeout,  # Keep connections alive
                    enable_cleanup_closed=True,
                    force_close=False,  # Don't force close connections
                    ssl=False,  # Disable SSL verification for better reliability
                )
        return cls._shared_connector

    @classmethod
    async def cleanup_shared_connector(cls):
        """
        Clean up the shared connector. Call this when shutting down the application.
        """
        async with cls._connector_lock:
            if cls._shared_connector is not None:
                await cls._shared_connector.close()
                cls._shared_connector = None

    @classmethod
    async def refresh_shared_connector(cls):
        """
        Refresh the shared connector by closing and recreating it.
        Useful when connections are in a bad state.
        """
        async with cls._connector_lock:
            if cls._shared_connector is not None:
                await cls._shared_connector.close()
                cls._shared_connector = None
            # Next call to _get_shared_connector will create a new one

    async def get_insight_details(
        self,
        populate: list,
        sort: Optional[dict] = None,
        projection: Optional[dict] = None,
        filter: Optional[dict] = {},
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Asynchronously fetches detailed insights with filtering, sorting, and projection options.

        Args:
            populate (list): List of fields or related entities to populate in the response.
            sort (dict, optional): Sorting criteria in MongoDB-style format (e.g., {"timestamp": -1}). Defaults to None.
            projection (dict, optional): Fields to include or exclude in the response (e.g., {"name": 1, "value": 0}). Defaults to None.
            filter (dict, optional): Query filters to apply. Defaults to an empty dict ({}).
            on_prem (bool, optional): Specifies whether to use on-premises data server. If not provided, uses the class default.

        Returns:
            list: A list of detailed insight records matching the query.

        Example:
            >>> events_handler = AsyncEventsHandler(user_id="my_user_id", data_url="data.url.com", ds_url="example_ds.com")
            >>> insights = await events_handler.get_insight_details(
            ...     populate=["device", "metrics"],
            ...     sort={"timestamp": -1},
            ...     projection={"_id": 0, "device": 1, "metrics": 1},
            ...     filter={"status": "active"},
            ...     on_prem=True
            ... )
            >>> print(insights)
            [{'device': 'device123', 'metrics': {...}}, ...]

        Raises:
            ValueError: If the API response indicates failure (e.g., `success` is False).
            aiohttp.ClientError: If an error occurs during the HTTP request, such as a network issue or timeout.
            Exception: If an unexpected error occurs during data retrieval, such as parsing JSON data or other unexpected issues.
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.GET_INSIGHT_DETAILS.format(
                protocol=protocol,
                data_url=self.data_url,
            )

            # Prepare the request payload
            payload = {
                "pagination": {"page": 1, "count": 1000},
                "populate": populate,
                "sort": sort,
                "projection": projection,
                "user": {"id": self.user_id},
                "filters": filter,
            }
            session = None
            async with self.logger.timer("Get Insight Details:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.put(url, json=payload, ssl=False) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                    if not response_content["success"]:
                        raise ValueError(response_content)

                    return response_content["data"]["data"]

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return []

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return []

    async def add_insight_result(
        self,
        insight_id: str,
        workbench_id: str,
        result: list,
        devID: str,
        whitelisted_users: list,
        metadata: dict,
        tags: list,
        on_prem: Optional[bool] = None,
    ) -> bool:
        """
        Adds an insight result.

        This function adds an insight result using the specified parameters.

        Args:
            insight_id (str): The ID of the insight.
            workbench_id (str): The ID of the workbench.
            result (list): List of results.
            devID (str): Parameters related to the result.
            class_type (str): Metadata related to the result.
            tags (list): List of tags associated with the result.

        Returns:
            bool: True if the result was added successfully, False otherwise.
        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID")

            # Example: Adding an insight result
            >>> insight_added = bruce_handler.add_insight_result(
            ...     insight_id="insightID",
            ...     workbench_id="workbenchID",
            ...     result=["result1", "result2"],
            ...     devID="devID",
            ...     class_type="class type",
            ...     tags=['tags']
            ... )

        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.ADD_INSIGHT_RESULT.format(
                protocol=protocol,
                data_url=self.data_url,
            )

            # Prepare the request payload
            payload = {
                "insightID": insight_id,
                "workbenchID": workbench_id,
                "result": result,
                "parameters": {"devID": devID},
                "metadata": metadata,
                "whitelistedUIsers": whitelisted_users,
                "tags": tags,
            }
            session = None
            async with self.logger.timer("Add Insight Result:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.post(url, json=payload, ssl=False) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                    return True

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return False

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return False

    async def get_insight_results(
        self,
        insight_id: str,
        filter: Optional[dict] = {},
        page: int = 1,
        count: int = 10,
        single_page: bool = False,
        on_prem: Optional[bool] = None,
    ) -> Union[list, dict]:
        """
        Fetches insights results.

        This function fetches insights results using the specified parameters.

        Args:
            insight_id (str): The ID of the insight.
            filter (Optional[dict]): Dictionary for filtering the results.

        Returns:
            list: A list containing the fetched insight results.

        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID",organisation_id ="organisation_id")
            # Example
            >>> insight_id = "insightID"
            >>> fetched_results = bruce_handler.get_insight_results(insight_id=insight_id)
            # Example
            >>> insight_id = "insightID"
            >>> filter = {}
            >>> fetched_results = bruce_handler.get_insight_results(insight_id=insight_id,filter=filter)

        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.GET_INSIGHT_RESULT.format(
                protocol=protocol, data_url=self.data_url, insight_id=insight_id
            )

            all_results = []
            total_pages = page  # Initialize with page to enter the loop
            async with self.logger.timer("Get Insight Result:", self.extra_params):
                # Loop to fetch data until there is no more data to fetch
                while page <= total_pages:
                    # Prepare the request payload
                    payload = {
                        "filter": filter,
                        "pagination": {"page": page, "count": count},
                        "user": {
                            "id": self.user_id,
                            "organisation": self.organisation_id,
                        },
                    }

                    session = None
                    try:
                        # Use shared connector with proper session management
                        connector = await self._get_shared_connector()

                        session = aiohttp.ClientSession(
                            connector=connector,
                            timeout=self.timeout,
                            headers=self.header,
                            connector_owner=False,  # Don't close the shared connector
                        )

                        # Send a PUT request to fetch data from the current page
                        async with session.put(url, json=payload) as response:
                            response_content = await response.json()
                            # Check the response status code
                            response.raise_for_status()

                        if not response_content.get("success", False):
                            raise ValueError(response_content)
                        if single_page:
                            return response_content["data"]
                        page_data = response_content["data"]["data"]
                        total_pages = response_content["data"]["pagination"][
                            "totalPages"
                        ]
                        all_results.extend(page_data)
                        page += 1

                    finally:
                        # Always close the session to prevent resource leaks
                        if session and not session.closed:
                            await session.close()

            return all_results

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return [] if not single_page else {}

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return [] if not single_page else {}

    async def vector_upsert(
        self,
        insight_id: str,
        vector: list,
        payload: dict,
        on_prem: Optional[bool] = None,
    ) -> dict:
        """
        Upserts a vector for a given insight.

        This function inserts or updates a vector along with its associated payload
        for the specified insight.

        Args:
            insight_id (str): The ID of the insight.
            vector (list): The vector data to be upserted.
            payload (dict): Additional metadata or payload to be stored with the vector.
            on_prem (Optional[bool]): Flag to determine whether to use on-premise setup.
                                      Defaults to the class attribute if not provided.

        Returns:
            dict: A dictionary containing the response data after the vector upsert.

        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID", organisation_id="organisation_id")
            # Example upsert
            >>> insight_id = "insightID"
            >>> vector = [0.1, 0.2, 0.3]
            >>> payload = {"key": "value"}
            >>> result = bruce_handler.vector_upsert(insight_id=insight_id, vector=vector, payload=payload)
        """
        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.VECTOR_UPSERT.format(protocol=protocol, data_url=self.data_url)

            # Prepare the request payload
            data = {
                "insightID": insight_id,
                "vector": vector,
                "payload": payload,
            }
            session = None
            async with self.logger.timer("Vector Upsert:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.post(url, json=data, ssl=False) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                        if not response_content["success"]:
                            raise ValueError(response_content)

                    return response_content["data"]

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return {}

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return {}

    async def vector_search(
        self,
        query_vector: list,
        insight_list: list,
        document_list: list,
        limit: int = 100,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Performs a vector search across insights and documents.

        This function searches for the closest matches to the given query vector
        within the specified list of insights and documents.

        Args:
            query_vector (list): The vector used as the query for similarity search.
            insight_list (list): List of insight IDs to search within.
            document_list (list): List of document IDs to search within.
            limit (int, optional): Maximum number of results to return. Defaults to 100.
            on_prem (Optional[bool]): Flag to determine whether to use on-premise setup.
                                      Defaults to the class attribute if not provided.

        Returns:
            list: A list containing the search results.

        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID", organisation_id="organisation_id")
            # Example vector search
            >>> query_vector = [0.1, 0.2, 0.3]
            >>> insight_list = ["insightID1", "insightID2"]
            >>> document_list = ["docID1", "docID2"]
            >>> results = bruce_handler.vector_search(query_vector=query_vector, insight_list=insight_list, document_list=document_list)
        """

        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.VECTOR_SEARCH.format(protocol=protocol, data_url=self.data_url)

            # Prepare the request payload
            payload = {
                "query_vector": query_vector,
                "insightIDList": insight_list,
                "documentIDList": document_list,
                "limit": limit,
            }
            session = None
            async with self.logger.timer("Vector Search:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.post(url, json=payload, ssl=False) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                        if not response_content["success"]:
                            raise ValueError(response_content)

                    return response_content["data"]

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return []

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return []

    async def process_file(
        self,
        insight_id: str,
        insight_mongo_id: str,
        file_type: str,
        file_name: str,
        operation: Literal["upload", "download"] = None,
        on_prem: Optional[bool] = None,
    ) -> str:
        """
        Processes a file related to a given insight by uploading or downloading it.

        This function handles file operations such as upload or download
        for a specified insight and its associated MongoDB ID.

        Args:
            insight_id (str): The ID of the insight.
            insight_mongo_id (str): The MongoDB ID of the insight.
            file_type (str): The type of the file (e.g., "pdf", "csv").
            file_name (str): The name of the file to be processed.
            operation (Literal["upload", "download"], optional): The operation to perform.
                                                                 Can be either "upload" or "download".
            on_prem (Optional[bool]): Flag to determine whether to use on-premise setup.
                                      Defaults to the class attribute if not provided.

        Returns:
            str: A string containing the result of the file operation.

        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID", organisation_id="organisation_id")
            # Example upload
            >>> result = bruce_handler.process_file(
            ...     insight_id="insightID",
            ...     insight_mongo_id="mongoID",
            ...     file_type="pdf",
            ...     file_name="report.pdf",
            ...     operation="upload"
            ... )
            # Example download
            >>> result = bruce_handler.process_file(
            ...     insight_id="insightID",
            ...     insight_mongo_id="mongoID",
            ...     file_type="csv",
            ...     file_name="data.csv",
            ...     operation="download"
            ... )
        """

        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.PROCESS_FILE.format(protocol=protocol, data_url=self.data_url)

            # Prepare the request payload
            payload = {
                "insightID": insight_id,
                "insightMongoID": insight_mongo_id,
                "fileType": file_type,
                "fileName": file_name,
            }

            session = None
            async with self.logger.timer("Process File:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.post(
                        url + operation, json=payload, ssl=False
                    ) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                        if not response_content["success"]:
                            raise ValueError(response_content)

                    return response_content["data"]

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return ""

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return ""

    async def get_insight_tags(
        self,
        insight_id: str,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Retrieves the tags associated with a given insight.

        This function fetches all tags linked to the specified insight ID.

        Args:
            insight_id (str): The ID of the insight.
            on_prem (Optional[bool]): Flag to determine whether to use on-premise setup.
                                      Defaults to the class attribute if not provided.

        Returns:
            list: A list containing the tags for the given insight.

        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID", organisation_id="organisation_id")
            # Example usage
            >>> tags = bruce_handler.get_insight_tags(insight_id="insightID")
        """

        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.GET_INSIGHT_TAGS.format(protocol=protocol, data_url=self.data_url)
            session = None
            async with self.logger.timer("Get Insight Tags:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.get(url + insight_id, ssl=False) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                        if not response_content["success"]:
                            raise ValueError(response_content)

                    return response_content["data"]["tags"]

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return []

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return []

    async def get_related_insight(
        self,
        insight_id: str,
        on_prem: Optional[bool] = None,
    ) -> list:
        """
        Fetches all related insights for a given insight ID.

        This function retrieves all insight IDs from Qdrant that belong to the same
        dimension/collection as the specified insight ID.

        Args:
            insight_id (str): The ID of the insight whose related insights are to be fetched.
            on_prem (Optional[bool]): Flag to determine whether to use on-premise setup.
                                      Defaults to the class attribute if not provided.

        Returns:
            list: A list containing the related insight IDs.

        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID", organisation_id="organisation_id")
            # Example usage
            >>> related_insights = bruce_handler.get_related_insight(insight_id="insightID")
        """

        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.GET_RELATED_INSIGHTS.format(
                protocol=protocol,
                data_url=self.data_url,
                insight_id=insight_id,
            )
            session = None
            async with self.logger.timer("Get Related Insights:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.get(url, ssl=False) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                        if not response_content["success"]:
                            raise ValueError(response_content)

                    return response_content["data"]

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return []

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return []

    async def save_file_metadata(
        self,
        insight_id: str,
        file_name: str,
        file_type: str,
        file_size: int,
        tags: list,
        application_type: Literal["Workbench", "Insight"] = "Workbench",
        on_prem: Optional[bool] = None,
    ) -> str:
        """
        Saves file metadata and retrieves a signed URL for file upload.

        This function saves the metadata of a given file to MongoDB and returns
        a signed URL that can be used to upload the file to S3.

        Args:
            insight_id (str): The ID of the insight to associate with the file.
            file_name (str): The name of the file.
            file_type (str): The type of the file (e.g., "pdf", "csv").
            file_size (int): The size of the file in bytes.
            tags (list): A list of tags associated with the file.
            application_type (Literal["Workbench", "Insight"], optional): The application
                type where the file is being used. Defaults to "Workbench".
            on_prem (Optional[bool]): Flag to determine whether to use on-premise setup.
                                      Defaults to the class attribute if not provided.

        Returns:
            str: A signed URL to upload the file to S3.

        Example:
            # Instantiate BruceHandler
            >>> bruce_handler = BruceHandler(data_url="example.com", user_id="userID", organisation_id="organisation_id")
            # Example usage
            >>> signed_url = bruce_handler.save_file_metadata(
            ...     insight_id="insightID",
            ...     file_name="report.pdf",
            ...     file_type="pdf",
            ...     file_size=2048,
            ...     tags=["finance", "q1"],
            ...     application_type="Workbench"
            ... )
        """

        try:
            # If on_prem is not provided, use the default value from the class attribute
            if on_prem is None:
                on_prem = self.on_prem

            # Construct the URL based on the on_prem flag
            protocol = "http" if on_prem else "https"

            # Endpoint URL
            url = c.SAVE_FILE_METADATA.format(
                protocol=protocol,
                data_url=self.data_url,
                insight_id=insight_id,
            )

            data = {
                "file": {
                    "fileName": file_name,
                    "fileType": file_type,
                    "fileSize": file_size,
                },
                "tags": tags,  # convert from string to list
                "insightID": insight_id,
                "user": {"id": self.user_id},
                "applicationType": application_type,
            }
            session = None
            async with self.logger.timer("Save File Metadata:", self.extra_params):
                try:
                    # Use shared connector with proper session management
                    connector = await self._get_shared_connector()

                    session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=self.timeout,
                        headers=self.header,
                        connector_owner=False,  # Don't close the shared connector
                    )

                    async with session.post(url, json=data, ssl=False) as response:
                        response_content = await response.json()
                        # Check the response status code
                        response.raise_for_status()

                        if not response_content["success"]:
                            raise ValueError(response_content)

                    return response_content["data"]

                finally:
                    # Always close the session to prevent resource leaks
                    if session and not session.closed:
                        await session.close()

        except aiohttp.ClientError as e:
            error_message = (
                await ASYNC_ERROR_MESSAGE(response, url, response_content)
                if "response" in locals()
                else f"{e} \n[URL] {url}"
            )
            await self.logger.error(
                f"[EXCEPTION] {type(e).__name__}: {error_message}", self.extra_params
            )
            return ""

        except Exception as e:
            await self.logger.error(f"[EXCEPTION] {e}", self.extra_params)
            return ""
