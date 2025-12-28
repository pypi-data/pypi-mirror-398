from enum import Enum


class ExcelType(Enum):
    OFFICE = ("Excel.Application", "EXCEL", "Office")
    WPS = ("KET.Application", "wps", "Wps")