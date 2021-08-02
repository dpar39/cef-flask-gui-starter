import threading
from cefpython3 import cefpython as cef
import platform
import sys
import socket

from gevent.pywsgi import WSGIServer

from server import app
from mainwindow import CefApp

MAC = platform.system() == "Darwin"


def find_port() -> int:
    """
    Finds available port for Gevent / Flask
    :return: Available port
    """
    port_attempts = 0
    while port_attempts < 1000:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', 0))
            app_port = sock.getsockname()[1]
            sock.close()
            print("PORT: " + str(app_port))
            return app_port
        except:
            port_attempts += 1

    print("FAILED AFTER 1000 PORT ATTEMPTS")
    sys.exit(1)


app_port = find_port()


def start_server(app_port):
    http_server = WSGIServer(('127.0.0.1', app_port), app)
    http_server.serve_forever()


def main():
    check_versions()

    t = threading.Thread(target=start_server, args=(app_port,))
    t.daemon = True
    t.start()

    settings = {'web_security_disabled': True}
    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    settings = {}
    cef.Initialize(settings=settings)
    app = CefApp(False, url=f'http://127.0.0.1:{app_port}')
    app.MainLoop()
    del app  # Must destroy before calling Shutdown
    if not MAC:
        # On Mac shutdown is called in OnClose
        cef.Shutdown()


def check_versions():
    ver = cef.GetVersion()
    print("CEF Python {ver}".format(ver=ver["version"]))
    print("Chromium {ver}".format(ver=ver["chrome_version"]))
    print("CEF {ver}".format(ver=ver["cef_version"]))
    print("Python {ver} {arch}".format(
        ver=platform.python_version(),
        arch=platform.architecture()[0]))
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


if __name__ == '__main__':
    main()
