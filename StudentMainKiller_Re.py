import subprocess
import sys
import time
import ctypes
import urllib.request
import requests
import os
from ctypes import wintypes
import win32con
import win32gui
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from demo import Ui_Dialog

url = "https://update.eleven.icu:8081/version"
version = "1.0.1-beta"
version_new = requests.post(url).text



def ResultShow(text, status):
    window.ui.label.setText(f"执行结果: {status}, 输出: {text}")


def RunCommand(Command):
    return subprocess.run(
        Command,
        capture_output=True,
        text=True,
    )


class KeyboardHookThread(QThread):
    finished_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.user32 = ctypes.WinDLL('user32', use_last_error=True)
        
        # 定义回调函数类型
        self.HOOKPROC = ctypes.WINFUNCTYPE(
            wintypes.LPARAM,
            wintypes.INT,
            wintypes.WPARAM,
            wintypes.LPARAM
        )

        # 定义 Windows API 函数
        self.user32.SetWindowsHookExW.restype = wintypes.HHOOK
        self.user32.SetWindowsHookExW.argtypes = (
            wintypes.INT,      # idHook
            self.HOOKPROC,     # lpfn
            wintypes.HINSTANCE,  # hMod
            wintypes.DWORD,    # dwThreadId
        )

        self.user32.UnhookWindowsHookEx.restype = wintypes.BOOL
        self.user32.UnhookWindowsHookEx.argtypes = (wintypes.HHOOK,)

        self.user32.CallNextHookEx.restype = wintypes.LPARAM
        self.user32.CallNextHookEx.argtypes = (
            wintypes.HHOOK,
            wintypes.INT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        )

    def hook_proc(self, nCode, wParam, lParam):
        print(f"Key event: nCode={nCode}, wParam={wParam}, lParam={lParam}")
        return self.user32.CallNextHookEx(None, nCode, wParam, lParam)

    def run(self):
        hook_callback = self.HOOKPROC(self.hook_proc)
        try:
            while self.running:
                # 设置钩子
                hHook = self.user32.SetWindowsHookExW(
                    13,  # WH_KEYBOARD_LL = 13
                    hook_callback,
                    None,  # 当前模块
                    0      # 全局钩子
                )
                time.sleep(0.025)  # 25ms
                # 卸载钩子
                if hHook:
                    self.user32.UnhookWindowsHookEx(hHook)
            self.finished_signal.emit("键盘钩子已停止", "成功")
        except Exception as e:
            self.finished_signal.emit(str(e), "失败")

    def stop(self):
        self.running = False


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
            self.hide()
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
        self.ui.label.setText(f"初始化成功,当前版本:{version},云端版本:{version_new}")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.keyboard_hook_thread = None

        # 初始化置顶
        self.set_topmost()
        
        # 设置定时器
        self.timer = self.startTimer(50)  # 每50毫秒检查一次
        
        self.ui.label.setWordWrap(True)
        font = self.ui.label.font()
        font.setPointSize(12)
        self.ui.label.setFont(font)

        self.ui.pushButton.clicked.connect(self.kill_exe)
        self.ui.pushButton_2.clicked.connect(self.show_embedded_window)
        self.ui.pushButton_3.clicked.connect(self.disable_internet_ban)
        self.ui.pushButton_4.clicked.connect(self.disable_Udisk_ban)
        self.ui.pushButton_5.clicked.connect(self.disable_keyboard_ban)
        #self.ui.pushButton_6.clicked.connect(self.update)

        self.ui.pushButton.setText("结束进程")
        self.ui.pushButton_2.setText("缩小极域窗口")
        self.ui.pushButton_3.setText("解除网络禁用")
        self.ui.pushButton_4.setText("解除U盘禁用")
        self.ui.pushButton_5.setText("解除键盘锁")
        self.ui.pushButton_6.setText("更新(todo)")

    def timerEvent(self, event):
        self.set_topmost()
    
    def set_topmost(self):
        """使用pywin32设置窗口置顶"""
        hwnd = self.winId()
        win32gui.SetWindowPos(
            hwnd,
            win32con.HWND_TOPMOST,
            0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
        )
    
    def showEvent(self, event):
        self.set_topmost()
        super().showEvent(event)

    def kill_exe(self):
        result = RunCommand("wmic process where name='StudentMain.exe' delete")
        if "No" not in result.stdout:
            ResultShow(result.stdout, "成功")
        else:
            ResultShow(result.stdout, "可能失败")

    def show_embedded_window(self):
        self.embedded_window = MyWindow()
        self.embedded_window.show()

    def disable_internet_ban(self):
        result = RunCommand("sc stop TDNetFilter")
        if "STOPPED" or "失败" or "P"in result.stdout:
            ResultShow(result.stdout, "失败")
        else:
            ResultShow(result.stdout, "成功")
    
    def disable_Udisk_ban(self):
        result = RunCommand("sc stop TDFileFilter")
        if "STOPPED" or "失败" in result.stdout:
            ResultShow(result.stdout, "失败")
        else:
            ResultShow(result.stdout, "成功")

    def disable_keyboard_ban(self):
        if self.keyboard_hook_thread and self.keyboard_hook_thread.isRunning():
            self.keyboard_hook_thread.stop()
            self.ui.pushButton_5.setText("解除键盘锁")
            ResultShow("KeyBoardHook已停止", "成功")
        else:
            self.keyboard_hook_thread = KeyboardHookThread()
            self.keyboard_hook_thread.finished_signal.connect(ResultShow)
            self.keyboard_hook_thread.start()
            self.ui.pushButton_5.setText("停止Hook")
            ResultShow("KeyBoardHook已启动", "成功")

    def closeEvent(self, event):
        if self.keyboard_hook_thread and self.keyboard_hook_thread.isRunning():
            self.keyboard_hook_thread.stop()
            self.keyboard_hook_thread.wait()
        super().closeEvent(event)
'''
    def update(self):
        if version == version_new:
            ResultShow("当前已是最新！","")
        else:
            ResultShow("正在更新中...","Loading...")
            download_url = "https://eleven.icu/%E4%B8%80%E4%BA%9B%E6%9D%82%E7%89%A9/latest.exe"
            path = os.environ.get("USERPROFILE")
            try:
                ResultShow(path + "\desktop","")
                urllib.request.urlretrieve(download_url, "E:/")
            except Exception as e:
                ResultShow(str(e), "失败")
'''

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyDialog()
    window.show()
    sys.exit(app.exec_())