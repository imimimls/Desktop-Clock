"""防屏幕锁屏：计时期间阻止系统自动锁屏/休眠
使用 PowerShell 调用 Windows API，避免 ctypes 依赖"""
import subprocess
import threading
import time


class AntiScreensaver:
    """计时期间通过定期模拟按键防止锁屏"""

    def __init__(self):
        self._active = False
        self._thread = None
        self._interval = 120  # 每120秒按一次 SCROLLLOCK

    def _keep_alive(self):
        """后台线程：定期切换 SCROLLLOCK 防止锁屏"""
        while self._active:
            try:
                subprocess.run(
                    ['powershell', '-NoProfile', '-Command',
                     'Add-Type -AssemblyName System.Windows.Forms; '
                     '$wsh = New-Object -ComObject WScript.Shell; '
                     '$wsh.SendKeys("{SCROLLLOCK}"); '
                     'Start-Sleep -Milliseconds 200; '
                     '$wsh.SendKeys("{SCROLLLOCK}")'],
                    capture_output=True, timeout=10,
                    creationflags=0x08000000  # CREATE_NO_WINDOW
                )
            except Exception:
                pass
            for _ in range(self._interval):
                if not self._active:
                    break
                time.sleep(1)

    def enable(self):
        if not self._active:
            self._active = True
            self._thread = threading.Thread(target=self._keep_alive, daemon=True)
            self._thread.start()

    def disable(self):
        self._active = False

    @property
    def is_active(self):
        return self._active
