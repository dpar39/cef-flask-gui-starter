import threading
from cefpython3 import cefpython as cef
import platform
import sys
import os
import socket

from gevent.pywsgi import WSGIServer
from server import app 

os.sep = '/'
this_dir = os.path.dirname(__file__)


def find_port() -> int:
    """
    Finds available port for Gevent / Flask
    :return: Available port
    """

    port_attempts = 0
    while port_attempts < 1000:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', 0))
            app_port = sock.getsockname()[1]
            sock.close()
            print("PORT: " + str(app_port))
            return app_port
        except:
            port_attempts += 1

    print("FAILED AFTER 1000 PORT ATTEMPTS")
    sys.exit(1)

app_port = 5559

def start_server(app_port):
    http_server = WSGIServer(('', app_port), app)
    http_server.serve_forever()


def main():
    check_versions()

    t = threading.Thread(target=start_server, args=(app_port,))
    t.daemon = True
    t.start()

    sys.excepthook = cef.ExceptHook  # To shutdown all CEF processes on error
    cef.Initialize()
    cef.CreateBrowserSync(url=f"http://localhost:{app_port}",
                          window_title="Photo ID Creator", settings={'web_security_disabled': True})
    cef.MessageLoop()
    cef.Shutdown()


def check_versions():
    ver = cef.GetVersion()
    print("[hello_world.py] CEF Python {ver}".format(ver=ver["version"]))
    print("[hello_world.py] Chromium {ver}".format(ver=ver["chrome_version"]))
    print("[hello_world.py] CEF {ver}".format(ver=ver["cef_version"]))
    print("[hello_world.py] Python {ver} {arch}".format(
        ver=platform.python_version(),
        arch=platform.architecture()[0]))
    assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"


if __name__ == '__main__':
    main()
