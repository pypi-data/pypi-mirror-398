from typing import List, Union

from jkexcel.workbook.excel_base import ExcelElement
from jkexcel.workbook.sheet import Sheet


class Workbook(ExcelElement):
    """封装 Workbook 对象"""

    def __init__(self, com_workbook, app):
        super().__init__(app)
        self._wb = com_workbook

    @property
    def sheets(self) -> List[Sheet]:
        """返回所有工作表的 Sheet 对象列表"""
        return [Sheet(self._wb.Sheets(i + 1)) for i in range(self._wb.Sheets.Count)]

    def sheet(self, name_or_index: Union[str, int]) -> Sheet:
        """获取指定名称或索引的工作表"""
        if isinstance(name_or_index, str):
            ws = self._wb.Sheets(name_or_index)
        else:
            ws = self._wb.Sheets(name_or_index)
        return Sheet(ws)

    def save(self) -> None:
        self._wb.Save()

    def close(self) -> None:
        self._wb.Close(SaveChanges=True)

    @property
    def name(self) -> str:
        return self._wb.Name

    def __repr__(self) -> str:
        return f"<Workbook: {self.name}>"