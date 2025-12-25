# encoding: utf-8
from . import sx
import win32gui
import win32con
import win32ui
import win32api
import win32process
import psutil
import time,os
import subprocess
class 句柄类():
    def 取句柄(self,窗口名称=None,类名=None):
        return win32gui.FindWindow(类名, 窗口名称)
    def 取窗口名(self,hwnd):
        return win32gui.GetWindowText(hwnd)
    def 取类名(self,hwnd):
        return win32gui.GetClassName(hwnd)
    def 取激活(self):
        return win32gui.GetForegroundWindow()
    def 取子句柄1(self,父类=0):
        hwndChildList = []
        win32gui.EnumChildWindows(父类, lambda hwnd, param: param.append(hwnd), hwndChildList)
        return hwndChildList
    def 取子句柄2(self,hwnd,className):
        hwnd1 = win32gui.FindWindowEx(hwnd, None, className, None)
    def 取坐标(self,hwnd):
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        return (left, top, right, bottom)
    def 取进程(self,hwnd):
        try:
            threadpid, procpid = win32process.GetWindowThreadProcessId(hwnd)
            mypyproc = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, procpid)
            filePath = win32process.GetModuleFileNameEx(mypyproc, 0)
            return threadpid, procpid, filePath
        except Exception as e:
            print(f'[{e.__traceback__.tb_lineno}]{e}')
            return None
    def 取文件句柄(self,fileName):
        rt=[]
        if os.path.exists(fileName):
            for hwnd in self.取子句柄1():
                p=self.取进程(hwnd)
                if p:
                    path1=p[-1].replace(r'\\', '\\').strip()
                    path2=fileName.replace(r'\\', '\\').strip()
                    name = self.取窗口名(hwnd)
                    if path1==path2:
                        rt.append(hwnd)
        return rt
    def 修改焦点(self,hwnd):
        win32gui.PostMessage(hwnd, win32con.WM_SETFOCUS)
    def 修改窗口大小(self,hwnd,x,y,w,h):
        win32gui.MoveWindow(hwnd, x, y, w, h, True)
    def 激活(self,hwnd):
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.1)
            self.修改焦点(hwnd)
        except Exception as e:
            pass
    def 取消激活(self,hwnd):
        try:
            win32gui.SetBkMode(hwnd, win32con.TRANSPARENT)
            time.sleep(0.1)
        except Exception as e:
            pass
    def 后台激活(self,hwnd):
        try:
            win32gui.SetActiveWindow(hwnd)
        except Exception as e:
            pass
    def 显示窗口(self,hwnd,nCmdShow=1):
        '''
        hwnd = win32gui.FindWindow(lpClassName=None, lpWindowName=None)  # 查找窗口，不找子窗口，返回值为0表示未找到窗口
        hwnd = win32gui.FindWindowEx(hwndParent=0, hwndChildAfter=0, lpszClass=None, lpszWindow=None)  # 查找子窗口，返回值为0表示未找到子窗口

        win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
        SW_HIDE：隐藏窗口并激活其他窗口。nCmdShow=0。
        SW_SHOWNORMAL：激活并显示一个窗口。如果窗口被最小化或最大化，系统将其恢复到原来的尺寸和大小。应用程序在第一次显示窗口的时候应该指定此标志。nCmdShow=1。
        SW_SHOWMINIMIZED：激活窗口并将其最小化。nCmdShow=2。
        SW_SHOWMAXIMIZED：激活窗口并将其最大化。nCmdShow=3。
        SW_SHOWNOACTIVATE：以窗口最近一次的大小和状态显示窗口。激活窗口仍然维持激活状态。nCmdShow=4。
        SW_SHOW：在窗口原来的位置以原来的尺寸激活和显示窗口。nCmdShow=5。
        SW_MINIMIZE：最小化指定的窗口并且激活在Z序中的下一个顶层窗口。nCmdShow=6。
        SW_SHOWMINNOACTIVE：窗口最小化，激活窗口仍然维持激活状态。nCmdShow=7。
        SW_SHOWNA：以窗口原来的状态显示窗口。激活窗口仍然维持激活状态。nCmdShow=8。
        SW_RESTORE：激活并显示窗口。如果窗口最小化或最大化，则系统将窗口恢复到原来的尺寸和位置。在恢复最小化窗口时，应用程序应该指定这个标志。nCmdShow=9。

        1 4 6 9
        '''
        if hwnd!=self.取激活():
            self.激活(hwnd)
        win32gui.ShowWindow(hwnd,nCmdShow)
        time.sleep(0.1)
        self.修改焦点(hwnd)
    def 显示窗口_PID(self, fileName, pid):
        hwnds = self.取文件句柄(fileName=fileName)
        for hwnd in hwnds:
            p = self.取进程(hwnd)
            if p and p[1] == pid:
                self.显示窗口(hwnd)
                return
    def 关闭窗口_PID(self, fileName, pid):
        if pid and not isinstance(pid, bool) and os.path.exists(fileName):
            hwnds = self.取文件句柄(fileName)
            for hwnd in hwnds:
                p = self.取进程(hwnd)
                if p and p[1] == pid:
                    self.关闭窗口(hwnd)
    def 关闭文件进程(self,fileName):
        for hwnd in self.取文件句柄(fileName):
            self.关闭窗口(hwnd)
    def 关闭窗口(self,hwnd):
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            logger.info(f'关闭 hwnd:{hwnd} {self.取窗口名(hwnd)}')
        except Exception as e:
            pass
    def 发送回车(self):
        win32api.keybd_event(13, 0, 0, 0)
        win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
    def 鼠标定位(self, x, y):
        win32api.SetCursorPos([x, y])
    def 鼠标右键单击(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP | win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    def 鼠标左单键击(self):
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP | win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    def 是否可用可见(self,hwnd):
        try:
            if win32gui.IsWindowEnabled(hwnd) and win32gui.IsWindowVisible(hwnd):
                return True
        except Exception as e:
            sx.打印错误(e)
        return False
class 运行EXE程序():
    '''运行exe程序'''
    run_pid=None
    def __init__(self):
        self.cmd=None
        self.句柄类=句柄类()
        self.flag_阻塞=False
    def __run_program__(self,cmd):
        for hwnd in self.句柄类.取文件句柄(fileName=cmd):
            self.句柄类.关闭窗口(hwnd)
        self.flag_阻塞=False
        path, name = os.path.split(cmd)
        self.run_pid=True
        self.run_pid=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, cwd=r'{}'.format(path))
        if self.run_pid:
            self.run_pid.communicate(input=None, timeout=None)
            self.flag_阻塞=False
    def __close_program__(self):
        logger.info('关闭程序')
        if self.run_pid and not isinstance(self.run_pid, bool):
            try:
                print(self.run_pid.pid)
                self.run_pid.terminate()
                self.run_pid.kill()
                self.run_pid.wait()
            except Exception as e:
                sx.打印错误(e)
            try:
                self.句柄类.关闭文件进程(fileName=self.cmd)
            except Exception as e:
                pass
        self.run_pid = None
    def 打开程序(self,cmd):
        self.cmd=cmd
        logger.info('打开程序 {}'.format(cmd))
        self.pr=threading.Thread(target=self.__run_program__,args=(cmd,))
        self.pr.setDaemon(True)
        self.pr.start()
    def 关闭程序(self):
        th=threading.Thread(target=self.__close_program__)
        th.setDaemon(True)
        th.start()
if __name__ == '__main__':
    x=获取句柄()
    print(x.hwnd,x.name)
    窗口获取焦点(x.hwnd)
