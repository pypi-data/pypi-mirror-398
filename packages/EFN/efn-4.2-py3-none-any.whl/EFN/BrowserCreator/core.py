import sys
import requests
from bs4 import BeautifulSoup
from cefpython3 import cefpython as cef

def fullgui(url, windowname):
    sys.excepthook = cef.ExceptHook
    cef.Initialize()
    cef.CreateBrowserSync(url=url, window_title=windowname)
    cef.MessageLoop()
    cef.Shutdown()

def halfguiconsole(urltext, windowname):
    url = input(f"{urltext}")
    sys.excepthook = cef.excepthook
    cef.Initialize()
    cef.CreateBrowserSync(url=url, window_title=windowname)
    cef.MessageLoop()
    cef.Shutdown()

def fullconsole(urltext):
    url = input(f"{urltext}")
    html = requests.get(url).text
    print(BeautifulSoup(html, "html.parser").get_text())
