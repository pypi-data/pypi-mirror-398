from typing import Any


class Sheet:
    """封装 Worksheet 对象，提供简洁 API"""

    def __init__(self, com_worksheet):
        self._ws = com_worksheet

    @property
    def name(self) -> str:
        return self._ws.Name

    def activate(self) -> None:
        """激活该工作表"""
        self._ws.Activate()

    def __getitem__(self, address: str) -> Any:
        """读取单元格值，如 sheet['A1']"""
        return self._ws.Range(address).Value

    def __setitem__(self, address: str, value: Any) -> None:
        """写入单元格，如 sheet['A1'] = 'Hello'"""
        self._ws.Range(address).Value = value

    def range(self, address: str):
        """返回原生 Range 对象（用于高级操作）"""
        return self._ws.Range(address)

    def delete(self):
        """删除该工作表"""
        self._ws.Delete()

    def __repr__(self) -> str:
        return f"<Sheet: {self.name}>"
