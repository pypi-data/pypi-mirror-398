from jkexcel.workbook.excel_base import ExcelElement
from jkexcel.workbook.workbook import Workbook


class Workbooks(ExcelElement):

    def __init__(self, com_workbooks, app):
        super().__init__(app)
        self._wbs = com_workbooks

    def open(self, file_path: str) -> Workbook:
        """打开一个工作簿"""
        com_wb = self._wbs.Open(file_path)
        return Workbook(com_wb, self._app)

    def close_all(self):
        self._wbs.Close()

    def __repr__(self) -> str:
        return f"<Workbooks: {self._wbs.Count} open>"