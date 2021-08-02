
import socket
import platform
import threading
import sys
import os

import wx
from cefpython3 import cefpython as cef

g_count_windows = 0

TITLE = 'My Cool CEF App'
WIDTH = 1920
HEIGHT = 1080

WINDOWS = platform.system() == "Windows"
LINUX = platform.system() == "Linux"
MAC = platform.system() == "Darwin"

WindowUtils = cef.WindowUtils()

class MainFrame(wx.Frame):
    def __init__(self, url):
        wx.Frame.__init__(self, parent=None, id=wx.ID_ANY,
                          title=TITLE, size=(WIDTH, HEIGHT))
        self.browser = None

        if LINUX:
            pass  # WindowUtils.InstallX11ErrorHandlers()

        global g_count_windows
        g_count_windows += 1

        self.setup_icon()
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Set wx.WANTS_CHARS style for the keyboard to work.
        # This style also needs to be set for all parent controls.
        self.browser_panel = wx.Panel(self, style=wx.WANTS_CHARS)
        self.browser_panel.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self.browser_panel.Bind(wx.EVT_SIZE, self.OnSize)

        if MAC:
            try:
                # noinspection PyUnresolvedReferences
                from AppKit import NSApp
                # Make the content view for the window have a layer.
                # This will make all sub-views have layers. This is
                # necessary to ensure correct layer ordering of all
                # child views and their layers. This fixes Window
                # glitchiness during initial loading on Mac (Issue #371).
                NSApp.windows()[0].contentView().setWantsLayer_(True)
            except ImportError:
                print("[wxpython.py] Warning: PyObjC package is missing, "
                      "cannot fix Issue #371")
                print("[wxpython.py] To install PyObjC type: "
                      "pip install -U pyobjc")

        if LINUX:
            # On Linux must show before embedding browser, so that handle
            # is available (Issue #347).
            self.Show()
            # In wxPython 3.0 and wxPython 4.0 on Linux handle is
            # still not yet available, so must delay embedding browser
            # (Issue #349).
            if wx.version().startswith("3.") or wx.version().startswith("4."):
                wx.CallLater(100, self.embed_browser)
            else:
                # This works fine in wxPython 2.8 on Linux
                self.embed_browser(url)
        else:
            self.embed_browser(url)
            self.Show()

    def setup_icon(self):
        ib = wx.IconBundle()
        ib.AddIcon('gui/dist/gui/favicon.ico', wx.BITMAP_TYPE_ANY)
        self.SetIcons(ib)

    def embed_browser(self, url):
        window_info = cef.WindowInfo()
        (width, height) = self.browser_panel.GetClientSize().Get()
        assert self.browser_panel.GetHandle(), "Window handle not available yet"
        window_info.SetAsChild(self.browser_panel.GetHandle(),
                               [0, 0, width, height])
        self.browser = cef.CreateBrowserSync(window_info, url=url)
        self.browser.SetClientHandler(FocusHandler())

    def OnSetFocus(self, _):
        if not self.browser:
            return
        if WINDOWS:
            WindowUtils.OnSetFocus(self.browser_panel.GetHandle(), 0, 0, 0)
        self.browser.SetFocus(True)

    def OnSize(self, _):
        if not self.browser:
            return
        if WINDOWS:
            WindowUtils.OnSize(self.browser_panel.GetHandle(), 0, 0, 0)
        elif LINUX:
            (x, y) = (0, 0)
            (width, height) = self.browser_panel.GetSize().Get()
            self.browser.SetBounds(x, y, width, height)
        self.browser.NotifyMoveOrResizeStarted()

    def OnClose(self, event):
        print("[wxpython.py] OnClose called")
        if not self.browser:
            # May already be closing, may be called multiple times on Mac
            return

        if MAC:
            # On Mac things work differently, other steps are required
            self.browser.CloseBrowser()
            self.clear_browser_references()
            self.Destroy()
            global g_count_windows
            g_count_windows -= 1
            if g_count_windows == 0:
                cef.Shutdown()
                wx.GetApp().ExitMainLoop()
                # Call _exit otherwise app exits with code 255 (Issue #162).
                # noinspection PyProtectedMember
                os._exit(0)
        else:
            # Calling browser.CloseBrowser() and/or self.Destroy()
            # in OnClose may cause app crash on some paltforms in
            # some use cases, details in Issue #107.
            self.browser.ParentWindowWillClose()
            event.Skip()
            self.clear_browser_references()

    def clear_browser_references(self):
        # Clear browser references that you keep anywhere in your
        # code. All references must be cleared for CEF to shutdown cleanly.
        self.browser = None


class FocusHandler(object):
    def OnGotFocus(self, browser, **_):
        # Temporary fix for focus issues on Linux (Issue #284).
        if LINUX:
            print("[wxpython.py] FocusHandler.OnGotFocus:"
                  " keyboard focus fix (Issue #284)")
            browser.SetFocus(True)


class CefApp(wx.App):

    def __init__(self, redirect, url):
        self.timer = None
        self.timer_id = 1
        self.is_initialized = False
        self.url = url
        super(CefApp, self).__init__(redirect=redirect)

    def OnPreInit(self):
        super(CefApp, self).OnPreInit()
        # On Mac with wxPython 4.0 the OnInit() event never gets
        # called. Doing wx window creation in OnPreInit() seems to
        # resolve the problem (Issue #350).
        if MAC and wx.version().startswith("4."):
            print("[wxpython.py] OnPreInit: initialize here"
                  " (wxPython 4.0 fix)")
            self.initialize()

    def OnInit(self):
        self.initialize()
        return True

    def initialize(self):
        if self.is_initialized:
            return
        self.is_initialized = True
        self.create_timer()
        frame = MainFrame(self.url)
        self.SetTopWindow(frame)
        frame.Show()

    def create_timer(self):
        # See also "Making a render loop":
        # http://wiki.wxwidgets.org/Making_a_render_loop
        # Another way would be to use EVT_IDLE in MainFrame.
        self.timer = wx.Timer(self, self.timer_id)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(10)  # 10ms timer

    def on_timer(self, _):
        cef.MessageLoopWork()

    def OnExit(self):
        self.timer.Stop()
        return 0
