import re
import subprocess
import sys
import time

import win32con
import win32gui
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow

from demo import Ui_Dialog

process = "StudentMain.exe"


def ResultShow(text, status):
    window.ui.label.setText(f"执行结果: {status}, 输出: {text}")


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StudentMainKiller")
        self.resize(800, 600)
        self.show()

        # 延迟 100ms 确保窗口就绪后再嵌入
        QtCore.QTimer.singleShot(100, self.embed_target_window)

    def embed_target_window(self):
        parent_hwnd = int(self.winId())  # 获取 PyQt 窗口句柄
        calc_hwnd = win32gui.FindWindow(None, "屏幕广播")

        if not calc_hwnd:
            ResultShow("未找到窗口", "失败")
            return

        try:
            # 修改窗口样式为子窗口
            style = win32gui.GetWindowLong(calc_hwnd, win32con.GWL_STYLE)
            win32gui.SetWindowLong(
                calc_hwnd,
                win32con.GWL_STYLE,
                style & ~win32con.WS_POPUP | win32con.WS_CHILD,
            )

            # 设置父窗口
            win32gui.SetParent(calc_hwnd, parent_hwnd)

            # 调整位置和大小
            win32gui.MoveWindow(calc_hwnd, 10, 10, 500, 400, True)

            # 确保窗口可见
            win32gui.ShowWindow(calc_hwnd, win32con.SW_SHOW)

            ResultShow("窗口嵌入成功", "成功")
        except Exception as e:
            ResultShow(str(e), "失败")


class MyDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.label.setText("初始化成功")

        self.ui.label.setWordWrap(True)
        font = self.ui.label.font()
        font.setPointSize(12)
        self.ui.label.setFont(font)

        self.ui.pushButton.clicked.connect(self.click_kill_exe)
        self.ui.pushButton_2.clicked.connect(self.show_embedded_window)
        self.ui.pushButton.setText("结束进程")
        self.ui.pushButton_2.setText("缩小极域窗口")

    def click_kill_exe(self):
        result = subprocess.run(
            ["wmic", "process", "where", "name='StudentMain.exe'", "delete"],
            capture_output=True,
            text=True,
        )
        if "No" not in result.stdout:
            ResultShow(result.stdout, "成功")
        else:
            ResultShow(result.stdout, "可能失败")

    def show_embedded_window(self):
        self.embedded_window = MyWindow()
        self.embedded_window.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyDialog()
    window.show()
    sys.exit(app.exec_())
