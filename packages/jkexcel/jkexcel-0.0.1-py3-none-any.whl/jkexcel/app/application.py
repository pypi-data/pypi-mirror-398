from jkexcel.app.com_base import ExcelApplicationService
from jkexcel.app.application_options import ExcelOptions
from jkexcel.app.excel_type import ExcelType
from jkexcel.workbook.workbook import Workbook


class ExcelApplication:

    def __init__(self, excel_type: ExcelType = ExcelType.OFFICE, excel_option: ExcelOptions = ExcelOptions()):
        self.excel_app = ExcelApplicationService.attach_to_running_application(excel_type)
        if not self.excel_app:
            self.excel_app = ExcelApplicationService.create_application(excel_type)
        self.excel_app.Visible = excel_option.visible
        self.excel_app.DisplayAlerts = excel_option.display_alerts
        self.excel_app.ScreenUpdating = excel_option.screen_updating
        try:
            self.excel_app.UserControl = excel_option.user_control
        except AttributeError:
            # WPS 免费版或旧版可能无此属性，忽略
            pass
        # 窗口状态
        if excel_option.window_state == "minimized":
            self.excel_app.WindowState = -4140  # xlMinimized
        elif excel_option.window_state == "maximized":
            self.excel_app.WindowState = -4137  # xlMaximized
        else:
            self.excel_app.WindowState = -4143  # xlNormal

    def open_workbook(self, full_name: str):
        _wb = self.excel_app.Workbooks.Open(full_name)
        return Workbook(_wb, self)

    def close(self):
        self.excel_app.quit()