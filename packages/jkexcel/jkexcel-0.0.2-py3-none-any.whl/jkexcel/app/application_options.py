from typing import Literal


class ExcelOptions:
    """
    Excel/WPS 应用启动选项配置
    所有属性均有合理默认值，模拟“安静但可见”的自动化行为
    """

    def __init__(self):
        self.visible: bool = True
        # 是否显示警告对话框（如文件覆盖、宏安全等）
        self.display_alerts: bool = False
        # 是否启用屏幕刷新（关闭可提升批量操作性能）
        self.screen_updating: bool = True
        # 启动后是否最大化窗口
        self.window_state: Literal["normal", "minimized", "maximized"] = "normal"
        # 是否启用用户控制（影响进程是否随脚本退出而关闭）
        self.user_control: bool = True

    def set_visible(self, visible: bool):
        """设置可见性（默认为True）"""
        self.visible = visible

    def set_display_alerts(self, display_alerts: bool):
        """设置是否显示警告对话框（默认False）"""
        self.display_alerts = display_alerts

    def set_screen_updating(self, screen_updating: bool):
        """设置是否启用屏幕刷新（默认True）"""
        self.screen_updating = screen_updating

    def set_window_state(self, window_state: Literal["normal", "minimized", "maximized"]):
        """设置窗口状态（默认normal）"""
        self.window_state = window_state

    def set_user_control(self, user_control: bool):
        """设置是否启用用户控制（默认True）"""
        self.user_control = user_control
