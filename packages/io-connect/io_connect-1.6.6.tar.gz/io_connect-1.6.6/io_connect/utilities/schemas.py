from typing import Union, TypedDict


# Define the structure for the dictionary inside the list
class DateDict(TypedDict, total=False):
    startDate: Union[int, str]
    endDate: Union[int, str]
    timeFormat: str
