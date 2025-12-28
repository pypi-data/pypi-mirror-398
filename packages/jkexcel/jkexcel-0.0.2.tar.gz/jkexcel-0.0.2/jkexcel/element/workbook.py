import os
from enum import Enum
from typing import List, Union, Optional

import pythoncom

from jkexcel.element.excel_base import ExcelElement
from jkexcel.element.sheet import Sheet


class FileFormat(Enum):
    """
    Excel 文件格式
    """
    xlAddIn = (18, ".xla")  # Microsoft Excel 97-2003 外接程序
    xlAddIn8 = (18, ".xla")  # Microsoft Excel 97-2003 外接程序
    xlCSV = (6, ".csv")  # CSV
    xlCSVMac = (22, ".csv")  # Macintosh CSV
    xlCSVMSDOS = (24, ".csv")  # MSDOS CSV
    xlCSVUTF8 = (62, ".csv")  # UTF8 CSV
    xlCSVWindows = (23, ".csv")  # Windows CSV
    xlCurrentPlatformText = (-4158, ".txt")  # 当前平台文本
    xlDBF2 = (7, ".dbf")  # Dbase2
    xlDBF3 = (8, ".dbf")  # Dbase3
    xlDBF4 = (11, ".dbf")  # Dbase4
    xlDIF = (9, ".dif")  # 数据交换格式
    xlExcel12 = (50, ".xlsb")  # xlExcel12
    xlExcel2 = (16, ".xls")  # Excel 2.0 (1987)
    xlExcel2FarEast = (27, ".xls")  # Excel 2.0 Asia (1987)
    xlExcel3 = (29, ".xls")  # Excel 3.0 (1990)
    xlExcel4 = (33, ".xls")  # Excel 4.0 (1992)
    xlExcel4Workbook = (34, ".xls")  # Excel 4.0 工作簿格式 (1992)
    xlExcel5 = (39, ".xls")  # Excel 5.0 (1994)
    xlExcel7 = (39, ".xls")  # Excel 95 7.0
    xlExcel8 = (56, ".xls")  # Excel 97-2003 工作簿
    xlExcel9795 = (43, ".xls")  # Excel 95 和 97
    xlHtml = (44, ".html")  # HTML
    xlIntlAddIn = (26, "")  # 国际外接程序
    xlIntlMacro = (25, "")  # 国际宏
    xlOpenDocumentSpreadsheet = (60, ".ods")  # OpenDocument电子表格
    xlOpenXMLAddIn = (55, ".xlam")  # Open XML 外接程序
    xlOpenXMLStrictWorkbook = (61, ".xlsx")  # Strict Open XML 文件
    xlOpenXMLTemplate = (54, ".xltx")  # Open XML 模板
    xlOpenXMLTemplateMacroEnabled = (53, ".xltm")  # 启用 Open XML 模板宏
    xlOpenXMLWorkbook = (51, ".xlsx")  # Open XML 工作簿
    xlOpenXMLWorkbookMacroEnabled = (52, ".xlsm")  # 启用 Open XML 工作簿宏
    xlSYLK = (2, ".slk")  # 符号链接格式
    xlTemplate = (17, ".xlt")  # Excel 模板格式
    xlTemplate8 = (17, ".xlt")  # 模板 8
    xlTextMac = (19, ".txt")  # Macintosh 文本
    xlTextMSDOS = (21, ".txt")  # MSDOS 文本
    xlTextPrinter = (36, ".prn")  # 打印机文本
    xlTextWindows = (20, ".txt")  # Windows 文本
    xlUnicodeText = (42, "")  # Unicode 文本
    xlWebArchive = (45, ".mhtml")  # Web 档案
    xlWJ2WD1 = (14, ".wj2")  # 日语1-2-3
    xlWJ3 = (40, ".wj3")  # 日语1-2-3
    xlWJ3FJ3 = (41, ".wj3")  # 日语1-2-3 格式
    xlWK1 = (5, ".wk1")  # Lotus 1-2-3 格式
    xlWK1ALL = (31, ".wk1")  # Lotus 1-2-3 格式
    xlWK1FMT = (30, ".wk1")  # Lotus 1-2-3 格式
    xlWK3 = (15, ".wk3")  # Lotus 1-2-3 格式
    xlWK3FM3 = (32, ".wk3")  # Lotus 1-2-3 格式
    xlWK4 = (38, ".wk4")  # Lotus 1-2-3 格式
    xlWKS = (4, ".wks")  # Lotus 1-2-3 格式
    xlWorkbookDefault = (51, ".xlsx")  # 默认工作簿
    xlWorkbookNormal = (-4143, ".xls")  # 常规工作簿
    xlWorks2FarEast = (28, ".wks")  # Microsoft Works 2.0 亚洲格式
    xlWQ1 = (34, ".wq1")  # Quattro Pro 格式
    xlXMLSpreadsheet = (46, ".xml")  # XML 电子表格


class SaveAsAccessMode(Enum):
    """
    指定另存为函数访问模式
    """
    xlExclusive = (3, "独占模式")
    xlNoChange = (1, "不更改访问模式")
    xlShared = (2, "共享模式")


class SaveConflictResolution(Enum):
    """
    指定更新共享工作簿时解决冲突的方式
    """
    xlLocalSessionChanges = (2, "总是接受本地用户所做的更改")
    xlOtherSessionChanges = (3, "总是拒绝本地用户所做的更改")
    xlUserResolution = (1, "弹出对话框请求用户解决冲突")


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

    def save_as(self, file_name: str, file_format: Optional[FileFormat] = None,
                password: Optional[str] = pythoncom.Missing,
                write_res_password: Optional[str] = pythoncom.Missing,
                read_only_recommended: Optional[bool] = pythoncom.Missing,
                create_backup: Optional[bool] = pythoncom.Missing,
                access_mode: Optional[SaveAsAccessMode] = None,
                conflict_resolution: Optional[SaveConflictResolution] = None,
                add_to_mru: Optional[bool] = pythoncom.Missing,
                text_code_page: Optional[str] = pythoncom.Missing,
                text_visual_layout: Optional[object] = pythoncom.Missing,
                local: Optional[bool] = pythoncom.Missing):
        if file_format:
            name_without_ext, _ = os.path.splitext(file_name)
            file_name = name_without_ext + file_format.value[1]
        full_path = os.path.abspath(file_name)
        dir_path = os.path.dirname(full_path)
        os.makedirs(dir_path, exist_ok=True)
        file_name = os.path.normpath(file_name)
        self._wb.SaveAs(file_name, file_format.value[0] if file_format else pythoncom.Missing, password,
                        write_res_password,
                        read_only_recommended, create_backup,
                        access_mode.value[0] if access_mode else pythoncom.Missing,
                        conflict_resolution.value[0] if conflict_resolution else pythoncom.Missing, add_to_mru,
                        text_code_page,
                        text_visual_layout, local)

    def close(self) -> None:
        self._wb.Close(SaveChanges=True)

    @property
    def name(self) -> str:
        return self._wb.Name

    def __repr__(self) -> str:
        return f"<Workbook: {self.name}>"
