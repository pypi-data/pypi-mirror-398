import tkinter as tk
import platform
from datetime import datetime
import os
import time
import math
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import shutil
from tkinter.scrolledtext import ScrolledText
from tkinter.colorchooser import askcolor
import tkinter.colorchooser
from tkinter.dnd import Tester, Icon
import tkinter.dnd
import tkinter.simpledialog as simpledialog
import turtle
import sys
import random
import psutil
import importlib
import subprocess
import asyncio
import warnings
import webbrowser
import webview
from setuptools import setup, find_packages
from tkinter import ttk
from tkhtmlview import HTMLLabel
from tkinter import Toplevel
sys.stdout = open(os.devnull, 'w')
import pygame
sys.stdout = sys.__stdout__
from colorama import init, Style, Fore, Back
import pandas as pd
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import keyboard
from itertools import cycle
from functools import reduce
import pytz
import socket
import json, json.tool
import pkgutil
import matplotlib.pyplot as plt
import markovify
import librosa
from librosa.util import matching
from librosa.feature import delta
import numpy as np
import re
import scipy
import pathlib
import inspect
import functools
import contextlib
import warnings
import msgpack
import pooch
import mpmath
from mpmath import lambertw, agm
from collections import Counter

variables = {}
functions = {}
classes = {}
objects = {}
customerrors = {}
structures = {}
namespaces = {}
efnvars = {}

efn_root = None
items = 0

true = True
false = False
none = None
Length = len
Int = int
Float = float
String = str
Dictionary = dict
Type = type
All = all
exception = Exception
customdialog = simpledialog.Dialog
In = lambda item, container: item in container
As = lambda obj, alias: alias
From = lambda source, key: source.get(key)
Pass = lambda: None
Exit = lambda: exit()
Quit = lambda: quit()
Continue = lambda: None
args = sys.argv[1:]
Arguments = args
Argument = args[-1] if args else None
And = lambda a, b: a and b
Or = lambda a, b: a or b
Not = lambda a: not a

def less(a, b): return a < b and not math.isclose(a, b)
def more(a, b): return a > b and not math.isclose(a, b)
def lessorequal(a, b): return a <= b
def moreorequal(a, b): return a >= b
def equal(a, b): return math.isclose(a, b)
def notequal(a, b): return not math.isclose(a, b)

def unlockKeywordArguments(**kwargs):
    KeywordArguments = kwargs
    return KeywordArguments

for arg in args:
    Argument = arg

def write(text, end="\n", flush=False, file=sys.stdout, seperate=""):
    text = str(text)
    modifiedtext = text.replace(" ", seperate)
    print(modifiedtext, end=end, file=file, flush=flush)

def showmachinefulldata():
    return f"""{platform.platform()}
{platform.system()}
{platform.version()}
{platform.release()}
{platform.architecture()}
{platform.machine()}
{platform.processor()}"""

def showplatformdata():
    return f"{platform.platform()}"

def showsystemdata():
    return f"{platform.system()}"

def showversiondata():
    return f"{platform.version()}"

def showreleasedata():
    return f"{platform.release()}"

def showarchitecturedata():
    return f"{platform.architecture()}"

def showmachinedata():
    return f"{platform.machine()}"

def showprocessordata():
    return f"{platform.processor()}"

def startswith(string, prefix):
    return string.startswith(prefix)

def endswith(string, suffix):
    return string.endswith(suffix)

def Char(value):
    if isinstance(value, str) and len(value) == 1:
        return value
    raise ValueError(f"'{value}' is not a valid char.")

def F(variable):
    return eval(str(variable))

def drawbird():
    return """('>
|//
V_/_"""

def drawcat():
    return '''/\_/\  
( o.o ) 
> ^ <  
/  |  \ 
(   |   )
/    \  \
(      )  )
(        )/
 """""""""'''

def leftshift(num1, num2):
    return num1 << num2

def rightshift(num1, num2):
    return num1 >> num2

def bitwiseor(num1, num2):
    return num1 | num2

def bitwiseand(num1, num2):
    return num1 & num2

def binarytotext(binary):
    def binarytostring(binary):
        return ''.join(chr(int(b, 2)) for b in binary.split())

    binarycode = binary
    text = binarytostring(binarycode)
    return text

def texttobinary(text):
    def stringtobinary(text):
        return ' '.join(format(ord(char), '08b') for char in text)

    binary = stringtobinary(text)
    return binary

def numbertobinary(num):
    number = bin(num)
    return number

def binarytonumber(binarystr):
    return int(binarystr, 2)

def Next(variable):
    global items
    try:
        items += 1
        return f"{variable[items]}"
    except Exception:
        items = 1
        return f"{variable[items]}"

def Previous(variable):
    global items
    try:
        items -= 1
        return f"{variable[items]}"
    except Exception:
        items = 1
        return f"{variable[items]}"

def Item(variable, itemnumber):
    try:
        return f"{variable[itemnumber]}"
    except Exception:
        itemnumber = 0
        return f"{variable[itemnumber]}"

def Map(function, iterable):
    for item in iterable:
        yield function(item)

def palindrome(text):
    cleaned = ''.join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1]

def randomflip(text):
    return ''.join(
        c.upper() if random.choice([True, False]) else c.lower()
        for c in text
    )

def getbytememorysizeof(val):
    return sys.getsizeof(val)

def string(value):
    return f"{str(value)}"

def Floatnumber(value):
    return f"{float(value)}"

def bytestring(value):
    return bytes(value, 'utf-8')

def rawstring(value):
    return repr(value)[1:-1]

def Bytes(value, textencoding):
    return bytes(value, textencoding)

def encodetext(variable, textencoding):
    return variable.encode(textencoding)

def decodetext(variable, decoding):
    return variable.decode(decoding)

def evaluate(value):
    return f"{eval(value)}"

def Sort(value):
    return f"{sort(value)}"

def Reversedsort(value):
    toreverse = sort(value)
    return f"{toreverse.reverse()}"

def initobject(name, *args, **kwargs):
    obj = objects.get(name)
    if not obj: return print(f"Object '{name}' not found.")

    classname = obj.get("__class__")
    if classname and classname in classes:
        local_env = {"self": obj}
        exec(classes[classname], {}, local_env)
        init_func = local_env.get("__init__")
        if init_func:
            init_func(obj, *args, **kwargs)
    else:
        print(f"Class '{classname}' not found or not associated with object '{name}'.")

def supercall(objname, methodname, *args, **kwargs):
    obj = objects.get(objname)
    parent = obj.get("__parent__") if obj else None

    if parent and parent in classes:
        env = {"self": obj}
        exec(classes[parent], {}, env)
        super_func = env.get(methodname)
        if super_func:
            return super_func(obj, *args, **kwargs)
        else:
            print(f"Method '{methodname}' not found in superclass '{parent}'.")
    else:
        print(f"No superclass defined for object '{objname}'.")

def injectkeywordarguements(objname, **kwargs):
    obj = objects.get(objname)
    if obj is None:
        return print(f"Object '{objname}' does not exist.")

    for key, value in kwargs.items():
        obj[key] = value

def copytoclipboard(text):
    efn_root.clipboard_clear()
    efn_root.clipboard_append(text)

def typeof(varname):
    val = globals().get(varname)
    return type(val).__name__

def systemuptime():
    seconds = time.time() - psutil.boot_time()
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"

def rollrandom(sides=6):
    return random.randint(1, sides)

def randomto(n1, n2):
    return random.randint(n1, n2)

def listfiles(path="."):
    return os.listdir(path)

def readfile(filename):
    with open(filename, "r") as f:
        content = f.read()
        return content

def appendtextinfile(filename, text):
    with open(filename, "a") as f:
        f.write(text)

def createfilewithcontent(filename, text):
    with open(filename, "x") as f:
        f.write(text)

def overwritecontentoffile(filename, text):
    with open(filename, "w") as f:
        f.write(text)

def readandoverwritefilecontent(filename, text):
    with open(filename, "r+") as f:
        data = f.read()
        f.seek(0)
        f.write(text)
        return data

def overwriteandreadfilecontent(filename, text):
    with open(filename, "w+") as f:
        f.write(text)
        f.seek(0)
        readfile = f.read()
        return readfile

def appendandreadcontent(filename, text):
    with open(filename, "a+") as f:
        f.write(text)
        f.seek(0)
        readcontent = f.read()
        return readcontent

def inlinefunction(thing, functiontodo):
    if thing:
        return lambda arg: functiontodo(arg)
    else:
        return lambda: functiontodo()

def newlineafter(line, times):
    return line + '\n' * times

def newlinebefore(line, times):
    return '\n' * times + line

def splittext(text, tosplit=None, delimiter=" ", maxsplit=None):
    if tosplit is None:
        if maxsplit is not None:
            return text.split(delimiter, maxsplit)
        else:
            return text.split(delimiter)
    else:
        if maxsplit is not None:
            return tosplit.split(delimiter, maxsplit)
        else:
            return tosplit.split(delimiter)

def jointext(items, delimiter=" "):
    return delimiter.join(items)

def slicefrom(text, start):
    return text[start:]

def sliceto(text, end):
    return text[:end]

def slicerange(text, start, end):
    return text[start:end]

def splitlistfrom(lst, start):
    return lst[start:]

def splitlistto(lst, end):
    return lst[:end]

def splitlistbetween(lst, start, end):
    return lst[start:end]

def slice(obj, start=None, end=None):
    return obj[start:end]

def formattext(text, style=None, color=None, case=None, padding=0, wrap=None, do_print=False):
    if case == "upper":
        text = text.upper()
    elif case == "lower":
        text = text.lower()
    elif case == "title":
        text = text.title()
    elif case == "normal" or case is None:
        pass

    if padding > 0:
        text = " " * padding + text + " " * padding

    if wrap:
        import textwrap
        text = textwrap.fill(text, width=wrap)

    if style:
        text = f"[{style}]{text}[/{style}]"
    if color:
        text = f"<{color}>{text}</{color}>"

    if do_print:
        print(text)
        
    return text

def rgb(efn_root, red, green, blue):
    r = red
    g = green
    b = blue
    return f"#{r:02x}{g:02x}{b:02x}"

def changeatrun(codetochange, changedcode):
    return changedcode

def private(code):
    return None

def protected(name, code, context):
    functions[name] = code
    if context == "disallowed":
        return None
    elif context == "allowed":
        return functions[name]()
    elif context == "protected":
        if caller == "subclass" or caller == "same_class":
            return code
        else:
            return None
    else:
        exit()

def isuppercase(text): return text.isupper()
def islowercase(text): return text.islower()
def countcharacter(text, char): return text.count(char)
def removecharacter(text, char): return text.replace(char, "")
def replacecharacter(text, text2, char): return text.replace(char, text2)
def replaceword(text, old, new): return text.replace(old, new)
def removeword(text, toremove): return text.replace(toremove, "")
def swapcase(text): return text.swapcase()
def reversetext(text): return text[::-1]
def writeuppercase(text): return text.upper()
def writelowercase(text): return text.lower()
def find(text, tofind): return text.find(tofind)
def capitalize(text, tocapitalize): return text.capitalize(tocapitalize)
def removestart(text, starttoremove): return text.removeprefix(starttoremove)
def removeend(text, endtoremove): return text.removesuffix(endtoremove)
def maximum(dictionary, key=None): return max(dictionary, key)
def minimum(dictionary, key=None): return min(dictionary, key)
def sortby(dictionary, key=None): return sorted(dictionary, key)

def msgboxerror(title, text):
    messagebox.showerror(title, text)

def msgboxinfo(title, text):
    messagebox.showinfo(title, text)

def msgboxwarning(title, text):
    messagebox.showwarning(title, text)

def msgboxokcancel(title, text):
    return messagebox.askokcancel(title, text)

def msgboxquestion(title, text):
    return messagebox.askquestion(title, text)

def msgboxyesno(title, text, onyes, onno):
    msgbox = messagebox.askyesno(title, text)
    if msgbox == True:
        onyes()
    else:
        onno()
    return msgbox
    
def msgboxyesnocancel(title, text, onyes, onno):
    msgbox = messagebox.askyesnocancel(title, text)
    if msgbox == True:
        onyes()
    elif msgbox == False:
        onno()
    else:
        pass
    return msgbox

def msgboxretrycancel(title, text, onretry):
    msgbox = messagebox.askretrycancel(title, text)
    if msgbox == True:
        onretry()
    else:
        pass
    return msgbox

def creategui(title, geometry, bg, icon, fullscreen=False):
    efn_root = tk.Tk()
    efn_root.title(title)
    efn_root.geometry(geometry)
    efn_root.configure(bg=bg)
    if platform.system() == "Windows":
        efn_root.iconbitmap(icon)
    else:
        iconimg = tk.PhotoImage(file=icon)
        efn_root.iconphoto(False, iconimg)
    efn_root.attributes("-fullscreen", fullscreen)
    return efn_root

def fullscreenmode(efn_root, fullscr=False):
    efn_root.attributes("-fullscreen", fullscr)

def bind(efn_root, widgetorroot, how, function):
    widgetorroot.bind(f"<{how}>", function)

def setfocus(efn_root, widgetorroot):
    widgetorroot.focus_set()

def listbox(efn_root, efnframe, width):
    tk.Listbox(efnframe, width=width)

def getsystemarguementvector():
    return sys.argv

def getlengthofsystemarguementvector():
    return len(sys.argv)

def efnimport(module_name):
    return importlib.import_module(module_name)

def efnfromimport(module_name, symbol_name):
    module = importlib.import_module(module_name)
    return getattr(module, symbol_name)

def efnimportas(module_name, alias_name):
    module = importlib.import_module(module_name)
    globals()[alias_name] = module

def efnfromimportas(module_name, symbol_name, alias_name):
    module = importlib.import_module(module_name)
    globals()[alias_name] = getattr(module, symbol_name)

def tryexcept(try_action, except_type=None, except_action=None, finally_action=None):
    if except_type == "AllError":
        except_type = "Exception"
    elif except_type == "InputOutputError":
        except_type = "IOError"
    try:
        try_action()
    except Exception as e:
        if except_type is None or isinstance(e, eval(except_type)):
            if except_action:
                except_action(e)
            else:
                return f"Caught exception: {e}"
        else:
            return f"Unhandled exception: {e}"
    finally:
        if finally_action:
            finally_action()
        
def textingui(efn_root, efnframe, label_id, text, color, bgcolor, fonttype, fontsize, side):
    if efnframe is None:
        efnframe = efn_root

    if not hasattr(efnframe, "textinguiLabels"):
        efnframe.textinguiLabels = {}

    if label_id in efnframe.textinguiLabels and efnframe.textinguiLabels[label_id].winfo_exists():
        label = efnframe.textinguiLabels[label_id]
        label.config(text=text, fg=color, bg=bgcolor, font=(fonttype, fontsize))
    else:
        label = tk.Label(efnframe, text=text, fg=color, bg=bgcolor, font=(fonttype, fontsize))
        label.pack(side=side)
        efnframe.textinguiLabels[label_id] = label

    return label

def buttonthreed(efn_root, efnframe, text, color, bgcolor, fonttype, fontsize, command, side): 
    tk.Button(efnframe, text=text, fg=color, bg=bgcolor, font=(fonttype, fontsize), command=command).pack(side=side)

def buttonflat(efn_root, efnframe, text, color, bgcolor, fonttype, fontsize, command, side): 
    tk.Button(efnframe, text=text, fg=color, bg=bgcolor, relief="flat", font=(fonttype, fontsize), command=command).pack(side=side)

def waitforguianswer(efn_root, efnframe, name, side):
    globals()[name] = tk.Entry(efnframe)
    globals()[name].pack(side=side)

def readfromentry(efn_root, name):
    return globals()[name].get()

def waittimegui(seconds, function):
    Timer(seconds, function).start()

def integervargui(*args, **kwargs):
    return tk.IntVar(*args, **kwargs)

def floatvargui(*args, **kwargs):
    return tk.FloatVar(*args, **kwargs)

def stringvargui(*args, **kwargs):
    return tk.StringVar(*args, **kwargs)

def booleanvargui(*args, **kwargs):
    return tk.BooleanVar(*args, **kwargs)

def activeguiitem(efn_root, widget):
    widget.configure(state=tk.ACTIVE)

def disabledguiitem(efn_root, widget):
    widget.configure(state=tk.DISABLED)

def normalguiitem(efn_root, widget):
    widget.configure(state=tk.NORMAL)

def atend(efn_root=False):
    return tk.END

def value(variable):
    return variable

def getwidgetstate(efn_root, widget):
    widget.cget("state")

def getwidgetdata(efn_root, widget, toget):
    widget.cget(toget)

def hasattribute(obj, attributename):
    return hasattr(obj, attributename)

def getattribute(obj, attributename, default=None):
    return getattr(obj, attributename, default)

def structure(name, *args, **kwargs):
    structures[name] = {"args": args, "kwargs": kwargs}

def callstructure(name, variablename=None):
    if variablename is not None:
        variablename = exec(structures[name], globals())
    else:
        exec(structures[name], globals())

def createnamespace(name, code):
    namespaces[name] = code

def runnamespace(name):
    exec(namespaces[name], globals())

def Isinstance(obj, type_):
    return isinstance(obj, type_)

def createiterator(value):
    return iter(value)

def calldictionaryvalue(dictionary, value, defualt=None):
    return dictionary.get(value, default)

def flipwidgetstate(efn_root, widget):
    current = widget.cget("state")
    new_state = "normal" if current == "disabled" else "disabled"
    widget.configure(state=new_state)

def setdataonwidget(efn_root, widget, value):
    if hasattr(widget, "set"):
        widget.set(value)
    elif hasattr(widget, "insert"):
        widget.delete(0, tk.END)
        widget.insert(0, value)
    else:
        print("Unsupported widget type for setting data.")

def getdatafromwidget(efn_root, widget, *args, **kwargs):
    return widget.get(*args, **kwargs)

def updategui(efn_root):
    efn_root.update()

def exitfromgui(efn_root):
    efn_root.destroy()

def hidemaingui(efn_root):
    efn_root.withdraw()

def waitguiwindow(efn_root):
    efn_root.wait_window()

def setmodalonguiwindow(efn_root):
    efn_root.grab_set()

def setfocusongui(efn_root):
    efn_root.focus_set()

def keepguiontop(efn_root):
    efn_root.transistent()

def topgeometryofwidget(efn_root, widget, topgeometry):
    widget.top.geometry(topgeometry)
    
def createcanvas(efn_root, width=300, height=200, bg="white"):
    canvas = tk.Canvas(efn_root, width=width, height=height, bg=bg)
    canvas.pack()
    return canvas

def drawoncanvas(canvas, todraw, *args, **kwargs):
    draw_method = getattr(canvas, todraw, None)
    if callable(draw_method):
        return draw_method(*args, **kwargs)
    else:
        print(f"Error: '{todraw}' is not a valid canvas method.")

def dialogaskstring(title, question):
    simpledialog.askstring(title, question)

def dialogaskint(title, question):
    simpledialog.askint(title, question)

def dialogaskfloat(title, question):
    simpledialog.askfloat(title, question)

def colorwindow(color=None, title=None, parent=None, initialcolor=None):
    askcolor(color=color, title=title, parent=parent, initialcolor=initialcolor)

def case(variabletocase, tocase, casingaction, defaultaction=None):
    if variabletocase == tocase:
        exec(casingaction, globals())
    else:
        if defaultaction is not None:
            exec(defaultaction, globals())
        else:
            print("Fell back to default action.")

def scrolledtext(efn_root, efnframe, text, typeof, side):
    if typeof == "readonly":
        scrolled = ScrolledText(efnframe)
        scrolled.pack(side=side)
        
        scrolled.insert("1.0", text)
        scrolled.configure(state="disabled")
        
    elif typeof == "editable":
        scrolled = ScrolledText(efnframe)
        scrolled.pack(side=side)

        scrolled.insert(tk.END, text)
        content = scrolled.get("1.0", tk.END)
        
    else:
        print("Unsupported scrolledtext type.")
    return scrolled

def textwidget(efn_root, efnframe, text, typeof, side):
    if typeof == "readonly":
        txt = tk.Text(efnframe)
        txt.pack(side=side)

        txt.insert(tk.END, text)
        txt.configure(state="disabled")

    elif typeof == "editable":
        txt = tk.Text(efnframe)
        txt.pack(side=side)

        txt.insert(tk.END, text)
        content = txt.get("1.0", tk.END)

    else:
        print("Unsupported textwidget type.")
    return txt

def messagewidget(efn_root, efnframe, text, width, bgcolor, fgcolor, fonttype, fontsize, side):
    tk.Message(efnframe, text=text, width=width, bg=bgcolor, fg=fgcolor, font=(fonttype, fontsize)).pack(side=side)

def checkbutton(efn_root, efnframe, text, side):
    var = tk.IntVar()
    cb = tk.Checkbutton(efnframe, text=text, variable=var)
    cb.pack(side=side)
    return var

def radiobutton(efn_root, efnframe, options, side, variable=None):
    if variable is None:
        variable = tk.StringVar()
    for text, value in options:
        rb = tk.Radiobutton(efnframe, text=text, variable=variable, value=value)
        rb.pack(side=side)
    return variable

def hidewidget(efn_root, widget):
    widget.pack_forget()

def hideplaceforget(efn_root, widget):
    widget.place_forget()

def showwidget(efn_root, widget, side):
    widget.pack(side=side)

def pausewindow(efn_root):
    efn_root.quit()

def minimizewindow(efn_root):
    efn_root.iconify()

def restorewindow(efn_root):
    efn_root.deiconify()

def updaterootidletasks(efn_root):
    efn_root.update_idletasks()

def makewindowtransparent(efn_root, transfloat):
    efn_root.attributes("-alpha", transfloat)

def disableuserinteractiongui(efn_root, userinteraction):
    efn_root.attributes("-disabled", userinteraction)

def shrinkwindowtools(efn_root, shrinktools):
    efn_root.attributes("-toolwindow", shrinktools)

def makeguicolortransparent(efn_root, color):
    efn_root.attributes("-transparentcolor", color)

def guitypelinux(efn_root, typeofgui):
    efn_root.attributes("-type", typeofgui)

def zoomedgui(efn_root, zoomed):
    efn_root.attributes("-zoomed", zoomed)

def stayguiontop(efn_root, stayontop):
    efn_root.attributes("-topmost", stayontop)

def addmenu(efn_root, efnframe, menus: dict):
    if not isinstance(menus, dict) or not menus:
        raise ValueError("The 'menus' argument must be a non-empty dictionary.")

    parent = efnframe if efnframe else efn_root
    flag = f"addmenu_{'_'.join(menus.keys())}_created"

    if not hasattr(parent, flag):
        menubar = tk.Menu(parent)

        for menu_name, items in menus.items():
            menu = tk.Menu(menubar, tearoff=0)
            for label, command in items:
                menu.add_command(label=label, command=lambda cmd=command: call(cmd))
            menubar.add_cascade(label=menu_name, menu=menu)

        efn_root.config(menu=menubar)
        setattr(parent, flag, True)
        return menubar, menus

    return None, None

def waittimemillisecondsgui(efn_root, ms, func):
    efn_root.after(ms, func)

def packguielement(efn_root, widget):
    widget.pack()

def internalpaddingofwidget(efn_root, widget, ipadx, ipady):
    try:
        widget.pack_configure(ipadx=ipadx, ipady=ipady)
    except:
        try:
            widget.grid_configure(ipadx=ipadx, ipady=ipady)
        except Exception as e:
            print(f"Error: {e}")

def paddingofwidget(efn_root, widget, padx, pady):
    try:
        widget.pack_configure(padx=padx, pady=pady)
    except:
        try:
            widget.grid_configure(padx=padx, pady=pady)
        except Exception as e:
            print(f"Error: {e}")

def placeofwidget(efn_root, widget, x, y):
    try:
        widget.place(x=x, y=y)
    except Exception as e:
        print(f"Could not place widget: {e}")

def setpositionofwidget(efn_root, widget, anchor):
    try:
        widget.pack_configure(anchor=anchor)
    except:
        try:
            widget.place_configure(anchor=anchor)
        except:
            try:
                widget.grid_configure(sticky=anchor)
            except Exception as e:
                print(f"Could not apply anchor '{anchor}' to widget.")

def alignwidget(efn_root, widget, sticky):
    try:
        widget.grid_configure(sticky=sticky)
    except Exception as e:
        print(f"Couldn't align the widget '{widget}'. Error: {e}")

def rowandcolumnofwidget(efn_root, widget, row, column):
    try:
        widget.grid(row=row, column=column)
    except Exception as e:
        print(f"Could not grid widget: {e}")

def rowspanandcolumnspanofwidget(efn_root, widget, rowspan, columnspan):
    try:
        widget.grid_configure(rowspan=rowspan, columnspan=columnspan)
    except:
        print(f"Could not apply the rowspan and the columnspan. Error: {e}")

def relativepositionofwidget(efn_root, widget, relx, rely):
    try:
        widget.place(relx=relx, rely=rely)
    except Exception as e:
        print(f"Could not apply relative position: {e}")

def sideofwidget(efn_root, widget, side):
    try:
        widget.pack_configure(side=side)
    except Exception as e:
        print(f"Error while applying the side argument. Error: {e}")

def stateofwidget(efn_root, widget, state):
    try:
        widget.pack_configure(state=state)
    except Exception as e1:
        try:
            widget.place_configure(state=state)
        except Exception as e2:
            try:
                widget.grid_configure(state=state)
            except Exception as e3:
                print(f"Error while applying the state of the widget. Error: {e3}")

def widthandheightofwidget(efn_root, widget, width, height):
    try:
        widget.pack_configure(width=width, height=height)
    except Exception as e1:
        try:
            widget.place_configure(width=width, height=height)
        except Exception as e2:
            try:
                widget.grid_configure(width=width, height=height)
            except Exception as e3:
                print(f"Error while applying the width and the height of the widget. Error: {e3}")

def textofwidget(efn_root, widget, text):
    try:
        widget.pack_configure(text=text)
    except Exception as e1:
        try:
            widget.place_configure(text=text)
        except Exception as e2:
            try:
                widget.grid_configure(text=text)
            except Exception as e3:
                print(f"Error while applying the text of the widget. Error: {e3}")

def Set(target, key=None, value=None):
    if key in None:
        return set(target)
    else:
        if hasattr(target, "configure"):
            target.configure({key: value})
        elif isinstance(target, dict):
            target[key] = value
        else:
            setattr(target, key, value)

def setattribute(objectclass, attributetoset, valuetoset):
    return setattr(objectclass, attributetoset, valuetoset)

def createfilter(filtername, tofilter):
    return filter(filtername, tofilter)

def listnumbersorvalues(start, stop):
    return range(start, stop)

def configuretowidget(efn_root, widget, toconfigure):
    widget.configure(toconfigure)

def gridwidget(efn_root, widget):
    widget.grid()

def Event(event, toget=None):
    data = {
        "keysym": event.keysym,
        "keycode": getattr(event, "keycode", None),
        "char": event.char,
        "num": getattr(event, "num", None),
        "delta": getattr(event, "delta", None),
        "type": event.type,
        "time": getattr(event, "time", None),
        "state": getattr(event, "state", None),
        "x": event.x,
        "y": event.y,
        "xroot": event.x_root,
        "yroot": event.y_root,
        "width": getattr(event, "width", None),
        "height": getattr(event, "height", None),
        "widget": event.widget,
        "focus": event.widget.focus_get(),
        "sendevent": getattr(event, "send_event", None),
        "serial": getattr(event, "serial", None)
    }
    if toget is None:
        return data
    return {k: data[k] for k in toget if k in data}

def windowinfo(widget, toget=None):
    data = {
        "x": widget.winfo_x(),
        "y": widget.winfo_y(),
        "width": widget.winfo_width(),
        "height": widget.winfo_height(),
        "reqwidth": widget.winfo_reqwidth(),
        "reqheight": widget.winfo_reqheight(),
        "rootx": widget.winfo_rootx(),
        "rooty": widget.winfo_rooty(),
        "geometry": widget.winfo_geometry(),
        "parent": widget.winfo_parent(),
        "toplevel": widget.winfo_toplevel(),
        "children": widget.winfo_children(),
        "class": widget.winfo_class(),
        "name": widget.winfo_name(),
        "id": widget.winfo_id(),
        "exists": widget.winfo_exists(),
        "ismapped": widget.winfo_ismapped(),
        "viewable": widget.winfo_viewable(),
        "manager": widget.winfo_manager(),
        "pointerx": widget.winfo_pointerx(),
        "pointery": widget.winfo_pointery(),
        "pointerxy": widget.winfo_pointerxy(),
        "screen": widget.winfo_screen(),
        "screenwidth": widget.winfo_screenwidth(),
        "screenheight": widget.winfo_screenheight(),
        "screenmmwidth": widget.winfo_screenmmwidth(),
        "screenmmheight": widget.winfo_screenmmheight(),
        "screendepth": widget.winfo_screendepth(),
        "screencells": widget.winfo_screencells(),
        "depth": widget.winfo_depth(),
        "pixels1in": widget.winfo_pixels("1i"),
        "fpixels1in": widget.winfo_fpixels("1i"),
        "visual": widget.winfo_visual(),
        "visualid": widget.winfo_visualid(),
        "visualsavailable": widget.winfo_visualsavailable(),
        "pathname": widget.winfo_pathname(widget.winfo_id())
    }
    if toget is None:
        return data
    return {k: data[k] for k in toget if k in data}

def setobjectoperator(objname, op, func):
    objects[objname][f"__{op}__"] = func

def loadplugin(path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("plugin", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "register"):
        mod.register()

def createtoplevelwindow(
    master,
    title,
    geometry,
    bg,
    icon,
    fullscreen
):
    popup = Toplevel(master)
    popup.title(title)
    popup.geometry(geometry)
    popup.configure(bg=bg)

    if icon:
        popup.iconbitmap(icon)

    popup.attributes("-fullscreen", fullscreen)

    return popup

def placewidget(widgetname, horizontal, vertical):
    widgetname.place(x=horizontal, y=vertical)

def frame(efn_root, width, side):
    efnframe = tk.Frame(efn_root, width=width)
    efnframe.pack(side=side)
    return efnframe

def showimagegui(efn_root, efnframe, image_path, width, height, side):
    img1 = Image.open(image_path).resize((width, height))
    photo1 = ImageTk.PhotoImage(img1)
    tk.Label(efn_root, image=photo1).pack(side=side)

def sharecharacter(text, text2, custom_action=None, custom_action2=None):
    shared = set(text) & set(text2)
    
    if shared:
        if custom_action:
            custom_action(text, text2)
        else:
            print("True")
        return True
    else:
        if custom_action2:
            custom_action2(text, text2)
        else:
            print("False")
        return False

def showdatetime():
    return datetime.now()

def twodigityear(variable):
    return variable.strftime("%y")

def fourdigityear(variable):
    return variable.strftime("%Y")

def fullweekdayname(variable):
    return variable.strftime("%A")

def threeletterweekdayname(variable):
    return variable.strftime("%a")

def weekdaynumbersundayfirst(variable):
    return variable.strftime("%w")

def daynumber(variable):
    return variable.strftime("%d")

def dayofyear(variable):
    return variable.strftime("%j")

def weeknumbersundayfirst(variable):
    return variable.strftime("%U")

def weeknumbermondayfirst(variable):
    return variable.strftime("%W")

def shortenedmonthname(variable):
    return variable.strftime("%b")

def fullmonthname(variable):
    return variable.strftime("%B")

def monthinnumbers(variable):
    return variable.strftime("%m")

def twentyfourhourtimeformat(variable):
    return variable.strftime("%H")

def twelvehourtimeformat(variable):
    return variable.strftime("%I")

def minutes(variable):
    return variable.strftime("%M")

def seconds(variable):
    return variable.strftime("%S")

def microseconds(variable):
    return variable.strftime("%f")

def amorpm(variable):
    return variable.strftime("%p")

def timezoneoffset(variable):
    return variable.strftime("%z")

def timezonename(variable):
    return variable.strftime("%Z")

def localedatetime(variable):
    return variable.strftime("%c")

def localedate(variable):
    return variable.strftime("%x")

def localetime(variable):
    return variable.strftime("%X")

def literalpercent(variable):
    return variable.strftime("%%")

def systemdo(todo):
    os.system(todo)

def systemstart(filename):
    os.startfile(filename)

def systemdeletefile(filename):
    os.remove(filename)

def systemdeletefolder(foldername):
    shutil.rmtree(foldername)

def systemcopyfile(file, towhere):
    shutil.copy(file, towhere)

def systemcopydir(directory, towhere):
    shutil.copytree(directory, towhere)

def systemmove(fileorfolder, towhere):
    shutil.move(fileorfolder, towhere)

def wait(timewait):
    time.sleep(timewait)

def c(text):
    pass

def o(line):
    return f"# {line}"

def multistring(text):
    return '"""{text}"""'

def executecode(code):
    exec(code, globals())

def preprocess(code, tocode, fromcode):
    return code.replace(f"{tocode}", f"{fromcode}")

def varplusplus(variable):
    variables[variable] += 1

def varminusminus(variable):
    variables[variable] -= 1

def varmultiplymultiply(variable):
    variables[variable] *= 2

def vardividedivide(variable):
    variables[variable] /= 2

def varbxorbxor(variable):
    variables[variable] ^= 2

def varfloordivfloordiv(var):
    variables[var] //= 2

def varpowerpower(var):
    variables[var] **= 2

def varmodulomodulo(var):
    variables[var] %= 2

def varbandband(var):
    variables[var] &= 2

def varborbor(var):
    variables[var] |= 2

def varshiftleft(var):
    variables[var] <<= 1

def varshiftright(var):
    variables[var] >>= 1

def addto(var, amount):
    variables[var] += amount

def subtractto(var, amount):
    variables[var] -= amount

def multiplyto(var, amount):
    variables[var] *= amount

def divideto(var, amount):
    if amount == 0:
        if variables[var] == 0:
            variables[var] = float("nan")
        else:
            variables[var] = float("inf")
    else:
        variables[var] /= amount

def bxorto(var, amount):
    variables[var] ^= amount

def floordivideto(var, amount):
    if amount == 0:
        if variables[var] == 0:
            variables[var] = float("nan")
        else:
            variables[var] = float("inf")
    else:
        variables[var] //= amount

def powerto(var, amount):
    variables[var] **= amount

def moduloto(var, amount):
    variables[var] %= amount

def bitwiseandto(var, amount):
    variables[var] &= amount

def bitwiseorto(var, amount):
    variables[var] |= amount

def shiftleftto(var, amount):
    variables[var] <<= amount

def shiftrightto(var, amount):
    variables[var] >>= amount

def If(condition, action):
    if eval(condition, {}, variables):
        exec(action)

def elseif(condition, action):
    if not variables.get("__last_condition", False):
        if eval(condition, {}, variables):
            variables["__last_condition"] = True
            exec(action)

def Else(action):
    if not variables.get("__last_condition", False):
        exec(action)
    variables["__last_condition"] = False

def define(name, code):
    functions[name] = code

def updatefunction(name, code):
    if name in functions:
        functions[name] = code
    else:
        print(f"Function '{name}' not found.")

def limitedexecution(name, timeout):
    if name in functions:
        def exitfromfunc():
            return None
        exec(functions[name], globals())
        Timer(timeout, exitfromfunc).start()
    else:
        print(f"Function '{name}' not found.")

def intfunction(name, code):
    nameint = "int" + name 
    functions[nameint] = code

def floatfunction(name, code):
    namefloat = "float" + name 
    functions[namefloat] = code

def call(name, undo=False, *args, **kwargs):
    if undo:
        return None
    else:
        if name in functions:
            return functions[name](*args, **kwargs)
        else:
            print(f"Function '{name}' not found.")

def callintfunction(nameint, undo=False, *args, **kwargs):
    if undo:
        return None
    else:
        if nameint in functions:
            return functions[nameint](
            *map(int, args),
            **{k: int(v) for k, v in kwargs.items()})
        else:
            print(f"Integer function '{nameint}' not found.")

def callfloatfunction(namefloat, undo=False, *args, **kwargs):
    if undo:
        return None
    else:
        if namefloat in functions:
            return functions[namefloat](
            *map(float, args),
            **{k: float(v) for k, v in kwargs.items()})
        else:
            print(f"Float function '{namefloat}' not found.")

def Class(name, body):
    classes[name] = body

def newobject(name, classname):
    if classname not in classes:
        print(f"Class {classname} was not found.")
        return None
    obj = {}
    obj["__class__"] = classname
    objects[name] = obj

    ns = {"self": obj}
    exec(classes[classname], ns, ns)
    return obj

def contains(textct, text, custom_action=None, custom_action2=None):
    if textct in text:
        if custom_action:
            custom_action(textct, text)
        else:
            print(f"'{textct}' found in '{text}' but no custom action was specified.")
            return True
    else:
        if custom_action2:
            custom_action2(textct, text)
        else:
            print(f"'{textct}' not found in '{text}' and no custom action was specified.")
            return False

def Break():
    return False

def repeat(thing, times, custom_action=None):
    for thing in range(times):
        if custom_action:
            result = custom_action(thing)
            if Break():
                break
        else:
            print("No custom action was specified.")

def lengthrepeat(thing, string, custom_action=None):
    for thing in format(string):
        if custom_action:
            result = custom_action(thing)
            if Break():
                break
        else:
            print("No custom action was specified.")

def whilerepeat(condition, custom_action=None):
    while condition():
        if custom_action:
            result = custom_action()
            if Break():
                break
        else:
            print("No custom action was specified.")

def whiletrue(custom_action=None):
    if custom_action:
        while True:
            result = custom_action()
            if Break():
                break
    else:
        print("No custom action was specified.")

def until(condition, custom_action=None):
    if custom_action:
        while not condition():
            result = custom_action()
            if result is None:
                break
    else:
        print("No custom action was specified.")

def foreach(varname, collection, custom_action=None):
    for item in collection:
        if custom_action:
            result = custom_action(item)
            if Break():
                break
        else:
            print(f"No custom action was specified.")

def let(name, value=None, scope=None):
    if scope is None:
        scope = globals()
    scope[name] = value if value is not None else None

def Makeitemglobal(name, value):
    globals()[name] = value

def Getfromglobalitem(name):
    globals()[name].get()

def inputconsole(varname, text, inputtype):
    if inputtype == "float":
        value = float(input(text))
    elif inputtype == "int":
        value = int(input(text))
    elif inputtype == "standard":
        value = input(text)
    else:
        exit()

    globals()[varname.__name__] = value
    return value

def createlist(lst, sep=", "):
    return sep.join(map(str, lst))

def Sepjoin(*args, sep=" ", start="", end=""):
    parts = [str(arg) for arg in args]
    joined = sep.join(parts)
    return f"{start}{joined}{end}"

def Isdigit(*args):
    return [str(arg).isdigit() for arg in args]

def connectdraw(title, bg):
    screen = turtle.Screen()
    screen.title(title)
    screen.bgcolor(bg)
    return screen

def drawcircle(color, size):
    turtle.color(color)
    turtle.begin_fill()
    turtle.circle(size)
    turtle.end_fill()

def drawtriangle(color):
    turtle.color(color)
    turtle.begin_fill()
    for _ in range(3):
        turtle.forward(100)
        turtle.left(120)
    turtle.end_fill()

def drawsquare(color):
    turtle.color(color)
    turtle.begin_fill()
    for _ in range(4):
        turtle.forward(100)
        turtle.left(90)
    turtle.end_fill()

def Return(value=None):
    if value is not None:
        return value
    else:
        return

def Yieldpause(value=None):
    if value is not None:
        yield value
    else:
        yield

def represent(value):
    return repr(value)

def List(listvariable):
    return f"{list(listvariable)}"

def getvalue(dictionary, key):
    return dictionary.get(key)

def popvalue(dictionary, key):
    return dictionary.pop(key, None)

def listkeys(dictionary):
    return list(dictionary.keys())

def listvalues(dictionary):
    return list(dictionary.values())

def listitems(dictionary):
    return list(dictionary.items())

def updateitems(dictionary, newitems):
    dictionary.update(newitems)
    return dictionary

def cleardictionary(dictionary):
    dictionary.clear()
    return dictionary

def Raise(errororclass):
    raise errororclass

def attachto(variable, toattach):
    variable.attach(toattach)

def draganddropicon(text):
    Icon(text)

def draganddropbase(efn_root):
    Tester(efn_root)

def createcustomerror(name, code):
    customerrors[name] = code

def raisecustomerror(name):
    exec(customerrors[name], globals())

def removecustomerror(name):
    customerrors.remove(name)

def concat(args):
    result = ""
    for arg in args:
        result += str(arg)
    return result

def Append(variable, toappend):
    variable.append(toappend)

def Extend(variable, toextend):
    variable.extend(toextend)

def Insert(variable, index, toinsert):
    variable.insert(index, toinsert)

def Remove(variable, toremove):
    variable.remove(toremove)

def Removebyindex(variable, index):
    variable.pop(index)

def Clear(variable):
    variable.clear()

def Findbyindex(variable, tofind):
    return variable.index(tofind)

def Sort(variable):
    variable.sort()

def Reverse(variable):
    variable.reverse()

def Shallowcopy(variable):
    return variable.copy()

def randomchoice(options):
    return random.choice(options)

def shufflelist(lst):
    random.shuffle(lst)
    return lst

def add(num1, num2):
    return round(num1 + num2, ndigits=12)

def subtract(num1, num2):
    return round(num1 - num2, ndigits=12)

def multiply(num1, num2):
    return round(num1 * num2, ndigits=12)

def divide(num1, num2):
    if num2 == 0:
        if num1 == 0:
            return "NaN"
        else:
            return "Infinity"
    else:
        return round(num1 / num2, ndigits=12)      

def sin(num1):
    return math.sin(num1)

def cos(num1):
    return math.cos(num1)

def tan(num1):
    return math.tan(num1)

def log(num1, num2):
    return math.log(num1, num2)

def factorial(num1):
    return math.factorial(num1)

def percentage(num1):
    return divide(num1, 100)

def floordivide(num1, num2):
    return num1 // num2

def bxor(num1, num2):
    return num1 ^ num2

def root(num1, num2):
    return math.pow(num1, 1/num2)
    
def pi():
    return 3.14159265358979323846264338327950288319716939937510

def e():
    return math.e

def phi():
    phi = (1 + math.sqrt(5)) / 2
    return phi

def gamma():
    return 0.577215664901

def apery():
    return 1.2020569031595942

def feigenbaumdelta():
    return 4.6692016091029

def naturallogoftwo():
    return 0.69314718055994530941723212145

def imaginaryself():
    return 0.2078795763507619085469556198349787700339

def liouvillenumber():
    return 0.110001000000000000000001000

def G():
    return 4.2432723820187182387231789037807870238466580344023094560327632965932456329650965065936563656953042693043456635496532497128778237652238970466650426065095346534625630245602546590345639630469536594695346594969650659046326953434372372898198278760665353663727818818187548745789548326721073279378467839416854707760346704737734875834784365653627812899087264664553537178891907276464646738282847387743282818018271872128273247381244536271890186535353632897650134267832632735909234304936543693926543921649304528967541302298056347145

def floatG():
    return 4.243272382018

def intG():
    return 4

def modulo(num1, num2):
    return num1 % num2

def sqrt(num):
    return math.sqrt(num)

def rounddowntopreviousnumber(num):
    return math.floor(num)

def rounduptonextnumber(num):
    return math.ceil(num)

def roundbyone(num):
    if num % 1 == 0.5 or num % 1 == -0.5:
        return math.ceil(num)
    else:
        return round(num)

def roundbyten(num):
    remainder = num % 10

    if remainder > 5:
        return num + (10 - remainder)
    elif remainder < 5:
        return num - remainder
    elif remainder == 5:
        if num < 0:
            return num - 5
        else:
            return num + 5
    else:
        return num

def roundbyonehundred(num):
    remainder = num % 100

    if remainder > 50:
        return num + (100 - remainder)
    elif remainder < 50:
        return num - remainder
    elif remainder == 50:
        if num < 0:
            return num - 50
        else:
            return num + 50
    else:
        return num

def roundbyonethousand(num):
    remainder = num % 1000

    if remainder > 500:
        return num + (1000 - remainder)
    elif remainder < 500:
        return num - remainder
    elif remainder == 500:
        if num < 0:
            return num - 500
        else:
            return num + 500
    else:
        return num

def parentheses(*args):
    return tuple(float(arg) for arg in args)

def immutable(*args):
    {"args": args}
    return tuple(args)

def leftstrip(text, tostrip=None):
    return text.lstrip(tostrip)

def rightstrip(text, tostrip=None):
    return text.rstrip(tostrip)

def everyitem(dictionarytoread):
    return all(dictionarytoread)

def anyitemnotall(dictionarytoread):
    return any(dictionarytoread)

def fontofwidget(efn_root, widget, fonttype, fontsize):
    try:
        widget.configure(font=((fonttype, fontsize)))
    except Exception as e:
        print(f"Error while applying the font of the widget. Error: {e}")

def configurefontcolor(efn_root, widget, color):
    widget.configure(fg=color)

def configurebackgroundcolor(efn_root, widget, color):
    widget.configure(bg=color)

def red(efn_root, quantity):
    r = quantity
    return f"{r:02x}"

def green(efn_root, quantity):
    g = quantity
    return f"{g:02x}"

def blue(efn_root, quantity):
    b = quantity
    return f"{b:02x}"

def alpha(efn_root, quantity):
    a = int(quantity * 255)
    return f"{a:02x}"

def rgba(efn_root, red, green, blue, alpha):
    Alpha = int(alpha * 255)
    return f"#{red:02x}{green:02x}{blue:02x}{Alpha:02x}"

def ForIn(forarg, inarg):
    return [forarg(x) for x in inarg]

def subprocesspop(subprocessname):
    subprocess.Popen(subprocessname)

def runsubprocess(task, file, shell=False):
    subprocess.run([task, file], shell=shell)

def Typeofvariablevalue(variable):
    return type(variable)

def Stringstr(variable):
    return str(variable)

def integernumber(variable):
    return int(variable)

def assignwithwalrus(value):
    return (temp := value)

def mediatype(variablename, typeofmedia):
    return variablename[typeofmedia]

def asyncdef(functionname, code, *args, **kwargs):
    func_code = f"""
async def {functionname}(*args, **kwargs):
    {code}
"""
    exec(func_code, globals())

    return globals()[functionname]

def runasync(func, *args, **kwargs):
    return asyncio.run(func(*args, **kwargs))

def removeprefix(prefix, variable):
    if variable.startswith(prefix):
        return variable[len(prefix):]
    return variable

def addprefix(prefix, variable):
    return prefix + variable

def createtask(taskname):
    return asyncio.create_task(taskname)

def sleepwait(delay, result=None):
    return asyncio.sleep(delay, result)
    return result

def awaitfor(coro):
    async def runner():
        await coro
    asyncio.run(runner())

def createwarning(text: str, classofwarning=None):
    warnings.warn(text, classofwarning)

def addsuffix(suffix, variable):
    return variable + suffix

def removesuffix(suffix, variable):
    if variable.endswith(suffix):
        return variable[:-len(suffix)]
    return variable

def openinbrowser(link):
    webbrowser.open(link)

def createwebview(title, link, height=None, width=None, resizable=False):
    webview.create_window(title, link, height=height, width=width, resizable=resizable)

def startwebview():
    webview.start()

def stopwebview():
    webview.stop()

def isnumeric(variable):
    return variable.isnumeric()

def isalphanumeric(variable):
    return variable.isalnum()

def findallin(variable, whattofind):
    return [item for item in variable if item == whattofind]

def guihorizontal(widget):
    widget.configure(orient=tk.HORIZONTAL)

def guivertical(widget):
    widget.configure(orient=tk.VERTICAL)

def commandinguiwidget(widget, command):
    widget.configure(command=command)

def scalewidget(efnframe, fromdata, todata, orient=None):
    scale = tk.Scale(efnframe, from_=fromdata, to=todata, orient=tk.HORIZONTAL if orient is None else orient)
    scale.pack()
    return scale

def bothgui(efn_root):
    return tk.BOTH

def selectorwidget(efnframe, values, orient=None):
    if orient is None or tk.HORIZONTAL or guihorizontal():
        class HorizontalCombo(tk.Frame):
            def __init__(self, master, items, command=None, **kwargs):
                super().__init__(master, **kwargs)
                self.items = items
                self.command = command
                self.selected = tk.StringVar()
        
                self.entry = tk.Entry(self, textvariable=self.selected, state="readonly", width=20)
                self.entry.pack(side="left")
        
                self.button = tk.Button(self, text="▼", command=self.toggle_menu)
                self.button.pack(side="left")

                self.menu_frame = tk.Frame(self)
                self.menu_buttons = []
                for item in items:
                    btn = tk.Button(self.menu_frame, text=item, command=lambda i=item: self.select(i))
                    btn.pack(side="left", padx=2)
                    self.menu_buttons.append(btn)

                self.menu_visible = False

            def toggle_menu(self):
                if self.menu_visible:
                    self.menu_frame.pack_forget()
                else:
                    self.menu_frame.pack(side="bottom", pady=5)
                self.menu_visible = not self.menu_visible

            def select(self, item):
                self.selected.set(item)
                self.toggle_menu()
                if self.command:
                    self.command(item)
                    
        combo = HorizontalCombo(efn_root, items=values)
        combo.pack(padx=20, pady=20)
                    
        return combo

    elif orient is tk.VERTICAL or guivertical():
        combo = ttk.Combobox(efnframe, values=values)
        combo.pack()
        return combo

    else:
        warnings.warn("The GUI element selectorwidget() excepts tk.VERTICAL, tk.HORIZONTAL or None. You can also set the orient up with these predefined functions: horizontalgui() and verticalgui().")

def setselectorcurrent(efn_root, selectorwidgetvariable, number):
    selectorwidgetvariable.current(number)

def guianalogclock(efn_root):
    class GUIAnalogClock(tk.Canvas):
        def __init__(self, master, size=300):
            super().__init__(master, width=size, height=size, bg="white", highlightthickness=0)
            self.size = size
            self.center = size // 2
            self.radius = self.center - 10
            self.hands = {
                "hour": self.create_line(0, 0, 0, 0, width=6, fill="#222"),
                "minute": self.create_line(0, 0, 0, 0, width=4, fill="#444"),
                "second": self.create_line(0, 0, 0, 0, width=2, fill="#e33")
            }
            self.draw_face()
            self.update_clock()

        def draw_face(self):
            self.create_oval(10, 10, self.size-10, self.size-10, outline="#aaa", width=2)
            for i in range(12):
                angle = math.radians(i * 30 - 90)
                x = self.center + self.radius * 0.85 * math.cos(angle)
                y = self.center + self.radius * 0.85 * math.sin(angle)
                self.create_text(x, y, text=str(i if i != 0 else 12), font=("Arial", 12, "bold"))

        def update_clock(self):
            now = time.localtime()
            self.draw_hand("hour", (now.tm_hour % 12 + now.tm_min / 60) * 30, self.radius * 0.5)
            self.draw_hand("minute", now.tm_min * 6, self.radius * 0.75)
            self.draw_hand("second", now.tm_sec * 6, self.radius * 0.9)
            self.after(1000, self.update_clock)

        def draw_hand(self, name, angle_deg, length):
            angle_rad = math.radians(angle_deg - 90)
            x = self.center + length * math.cos(angle_rad)
            y = self.center + length * math.sin(angle_rad)
            self.coords(self.hands[name], self.center, self.center, x, y)
            
    analogclock = GUIAnalogClock(efn_root)
    return analogclock

def gcw(green, cyan, white):
    greenRGB = (0, 255, 0)
    cyanRGB = (0, 255, 255)
    whiteRGB = (255, 255, 255)

    red   = int(green * greenRGB[0] + cyan * cyanRGB[0] + white * whiteRGB[0])
    green = int(green * greenRGB[1] + cyan * cyanRGB[1] + white * whiteRGB[1])
    blue  = int(green * greenRGB[2] + cyan * cyanRGB[2] + white * whiteRGB[2])

    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))

    return f"#{red:02x}{green:02x}{blue:02x}"

def rungui(efn_root):
    efn_root.mainloop()

def updatewidget(efn_root, widget):
    widget.update()

def afterwidget(efn_root, widget, milliseconds, function):
    widget.after(milliseconds, function)

def buttonflat(efn_root, efnframe, text, color, bgcolor, fonttype, fontsize, command, side):
    target = efnframe if efnframe else efn_root
    flag = f"buttonflat_{text}_created"
    if not hasattr(target, flag):
        button = tk.Button(target, text=text, fg=color, bg=bgcolor, relief="flat", font=(fonttype, fontsize), command=command)
        button.pack(side=side)
        setattr(target, flag, True)
        return button
    return getattr(target, flag)
    
def buttonthreed(efn_root, efnframe, text, color, bgcolor, fonttype, fontsize, command, side):
    target = efnframe if efnframe else efn_root
    flag = f"buttonthreed_{text}_created"
    if not hasattr(target, flag):
        button = tk.Button(target, text=text, fg=color, bg=bgcolor, font=(fonttype, fontsize), command=command)
        button.pack(side=side)
        setattr(target, flag, True)
        return button
    return getattr(target, flag)
    
def waitforguianswer(efn_root, efnframe, name, side):
    target = efnframe if efnframe else efn_root
    flag = f"entry_{name}_created"
    if not hasattr(target, flag):
        globals()[name] = tk.Entry(target)
        globals()[name].pack(side=side)
        setattr(target, flag, True)

def scrolledtext(efn_root, efnframe, text, typeof, side):
    target = efnframe if efnframe else efn_root
    flag = f"scrolledtext_{text[:10]}_created"
    if not hasattr(target, flag):
        scrolled = ScrolledText(target)
        scrolled.pack(side=side)
        if typeof == "readonly":
            scrolled.insert("1.0", text)
            scrolled.configure(state="disabled")
        elif typeof == "editable":
            scrolled.insert(tk.END, text)
        setattr(target, flag, True)
        return scrolled

def textwidget(efn_root, efnframe, text, typeof, side):
    target = efnframe if efnframe else efn_root
    flag = f"textwidget_{text[:10]}_created"
    if not hasattr(target, flag):
        txt = tk.Text(target)
        txt.pack(side=side)
        if typeof == "readonly":
            txt.insert(tk.END, text)
            txt.configure(state="disabled")
        elif typeof == "editable":
            txt.insert(tk.END, text)
        setattr(target, flag, True)
        return txt

def messagewidget(efn_root, efnframe, text, width, bgcolor, fgcolor, fonttype, fontsize, side):
    target = efnframe if efnframe else efn_root
    flag = f"message_{text[:10]}_created"
    if not hasattr(target, flag):
        tk.Message(target, text=text, width=width, bg=bgcolor, fg=fgcolor, font=(fonttype, fontsize)).pack(side=side)
        setattr(target, flag, True)

def checkbutton(efn_root, efnframe, text, side):
    target = efnframe if efnframe else efn_root
    flag = f"checkbutton_{text}_created"
    if not hasattr(target, flag):
        var = tk.IntVar()
        tk.Checkbutton(target, text=text, variable=var).pack(side=side)
        setattr(target, flag, True)
        return var

def radiobutton(efn_root, efnframe, options, side, variable=None):
    target = efnframe if efnframe else efn_root
    flag = f"radiobutton_{str(options)}_created"
    if not hasattr(target, flag):
        if variable is None:
            variable = tk.StringVar()
        for text, value in options:
            tk.Radiobutton(target, text=text, variable=variable, value=value).pack(side=side)
        setattr(target, flag, True)
        return variable

def digitaldatetimewidget(efn_root):
    target = efn_root
    if not hasattr(target, "digitaldatetime_created"):
        label = tk.Label(target)
        label.pack()
        def updatetime():
            label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            label.after(1000, updatetime)
        updatetime()
        setattr(target, "digitaldatetime_created", True)
        return label

def analogclock(efn_root):
    target = efn_root
    if not hasattr(target, "analogclock_created"):
        canvas = tk.Canvas(target, width=200, height=200, bg="white")
        canvas.pack()
        def drawclock():
            canvas.delete("all")
            canvas.create_oval(10, 10, 190, 190)
            now = datetime.now()
            sec = now.second
            min = now.minute
            hr = now.hour % 12
            sec_angle = math.radians(sec * 6)
            min_angle = math.radians(min * 6)
            hr_angle = math.radians(hr * 30 + min * 0.5)
            canvas.create_line(100, 100, 100 + 80 * math.sin(sec_angle), 100 - 80 * math.cos(sec_angle), fill="red")
            canvas.create_line(100, 100, 100 + 60 * math.sin(min_angle), 100 - 60 * math.cos(min_angle), width=2)
            canvas.create_line(100, 100, 100 + 40 * math.sin(hr_angle), 100 - 40 * math.cos(hr_angle), width=4)
            canvas.after(1000, drawclock)
        drawclock()
        setattr(target, "analogclock_created", True)
        return canvas

def numstrscale(efn_root, efnframe, items, fromdata):
    target = efnframe if efnframe else efn_root
    flag = f"stringscale_{str(items)}_created"
    if not hasattr(target, flag):
        values = items if isinstance(items, list) else []
        var = tk.IntVar()
        scale = tk.Scale(target, from_=fromdata if fromdata else 0, to=len(values) - 1, orient="horizontal", variable=var)
        scale.pack()
        label = tk.Label(target, text=values[0] if values else "")
        label.pack()
        def update_label(*_):
            index = var.get()
            label.config(text=values[index] if 0 <= index < len(values) else "")
        var.trace_add("write", update_label)
        setattr(target, flag, True)
        return scale

def customvarscale(efn_root, efnframe, values, orient, bg):
    parent = efnframe if efnframe else efn_root
    flag = f"customvarscale_{str(values)}_created"
    if not hasattr(parent, flag):
        mainframe = tk.Frame(parent, bg=bg if bg else "white")
        mainframe.pack()
        var = tk.StringVar(value=values[0])
        index = tk.IntVar(value=0)
        display = tk.Label(mainframe, text=values[0], bg=bg if bg else "white")
        display.pack()
        scale = tk.Scale(
            mainframe,
            from_=0,
            to=len(values) - 1,
            orient=orient if orient else tk.HORIZONTAL,
            showvalue=0,
            tickinterval=0,
            variable=index,
            command=lambda v: (var.set(values[int(v)]), display.config(text=values[int(v)])),
            bg=bg if bg else "white"
        )
        scale.pack()
        setattr(parent, flag, True)
        return mainframe, var

def donotshowvalue(efn_root, scalevariable):
    scalevariable.config(showvalue=0)

def canresizewindow(efn_root, itswidth, itsheight):
    efn_root.resizable(itswidth if itswidth else True, itsheight if itsheight else True)

def setminimumsize(efn_root, width, height):
    efn_root.minsize(width, height)

def setmaximumsize(efn_root, width, height):
    efn_root.maxsize(width, height)

def windowsetstate(efn_root, normal=True, iconic=False, zoomed=False, withdrawn=False):
    if normal:
        efn_root.state("normal")
    if iconic:
        efn_root.state("iconic")
    if zoomed:
        efn_root.state("zoomed")
    if withdrawn:
        efn_root.state("withdrawn")

def handlewhen(efn_root, tohandle, function):
    if tohandle == "appexit":
        efn_root.protocol("WM_DELETE_WINDOW", function)
    elif tohandle == "savestate":
        efn_root.protocol("WM_SAVE_STATE", function)
    elif tohandle == "takefocus":
        efn_root.protocol("WM_TAKE_FOCUS", function)
    else:
        raise TypeError("handlewhen() requires appexit, savestate or takefocus.")

def raisewindowabove(efn_root):
    efn_root.lift()

def raisewindowbehind(efn_root):
    efn_root.lower()

def stayaboveparent(efn_root, popup):
    popup.transient(efn_root)

def removeborders(efn_root):
    efn_root.wm_overrideredirect(True)

def playmusic(musictoplay):
    pygame.mixer.init()
    pygame.mixer.music.load(musictoplay)
    pygame.mixer.music.play()

def stopmusic():
    pygame.mixer.music.stop()

def tooltip(efn_root, widget, text, color, bgcolor, fonttype, fontsize):
    if widget is None:
        raise ValueError("tooltip(): widget must not be None")
    if widget == efn_root:
        raise ValueError("tooltip(): window is not a widget (won't work correctly)")

    class CustomTooltip:
        def __init__(self):
            self.tooltip_window = None
            widget.bind("<Enter>", self.show_tooltip)
            widget.bind("<Leave>", self.hide_tooltip)

        def show_tooltip(self, event=None):
            x = widget.winfo_rootx() + 25
            y = widget.winfo_rooty() - 20
            self.tooltip_window = tk.Toplevel(efn_root)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            label = tk.Label(
                self.tooltip_window,
                text=text,
                fg=color,
                bg=bgcolor,
                relief="solid",
                borderwidth=1,
                font=(fonttype, fontsize),
            )
            label.pack(ipadx=1)

        def hide_tooltip(self, event=None):
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None

    tooltip = CustomTooltip()
    return tooltip

def configurerelief(efn_root, widget, relief):
    widget.configure(relief=relief)

class DynamicIsland:
    def __init__(self, title="", text="", color="lime", disappearafter=10000):
        self.title = title
        self.text = text
        self.color = color
        self.disappearafter = disappearafter
        self.expanded = False

        self.root = tk.Toplevel()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.geometry("300x60+600+50")

        self.canvas = tk.Canvas(self.root, width=300, height=60, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.text_id = self.canvas.create_text(150, 30, text=self.title, fill=self.color, font=("Arial", 14, "bold"))
        self.canvas.bind("<Button-1>", self.toggle)

        self.root.after(disappearafter, self.root.destroy)

    def toggle(self, event=None):
        if not self.expanded:
            self.root.geometry("400x120+550+50")
            self.canvas.config(width=400, height=120)
            self.canvas.itemconfig(self.text_id, text=self.text)
            self.expanded = True
        else:
            self.root.geometry("300x60+600+50")
            self.canvas.config(width=300, height=60)
            self.canvas.itemconfig(self.text_id, text=self.title)
            self.expanded = False

    def auto_shrink(self, delay=5000):
        self.root.after(delay, lambda: self.toggle() if self.expanded else None)

    def show(self):
        self.root.mainloop()

def configuretransglass(efn_root, widget, width=None, height=None):
    efn_root.attributes("-topmost", True)
    efn_root.attributes("-transparentcolor", efn_root["bg"])
    widget.configure(bg=efn_root["bg"], fg="white", font=("Arial", 16))
    widget.place(x=50, y=50)
    frame = tk.Frame(efn_root, bg="#FFFFFF", width=width if width else 200, height=height if height else 100)
    frame.place(x=40, y=40)
    frame.lower(widget)
    frame.configure(highlightbackground="white", highlightthickness=2)

def oddoreven(num):
    if isinstance(num, float):
        return "This number is decimal. It is neither odd nor even."
    if num % 2 == 0:
        return "This number is even."
    else:
        return "This number is odd."

def primeorcomposite(num):
    if isinstance(num, float):
        return "This number is decimal. It is neither prime nor composite."
    if num < 2:
        return "This number is neither prime nor composite."
    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return "This number is composite."
    return "This number is prime."

def getid(variable):
    return id(variable)

def tocenter(variable, width, fillchar=None):
    return variable.center(width, fillchar=fillchar if fillchar else "")

def initstylesandformats():
    init(autoreset=False)

def settextstyle(style, variable):
    styles = {
        "dim": Style.DIM,
        "normal": Style.NORMAL,
        "bold": Style.BRIGHT
    }
    return styles.get(style.lower(), "Error.") + variable

def settextcolor(color, variable):
    return getattr(Fore, color.upper(), "Error.") + variable

def setbgcolor(color, variable):
    return getattr(Back, color.upper(), "Error.") + variable

def resetstylesandformats():
    return Style.RESET_ALL + Fore.RESET + Back.RESET

def converttostring(variable):
    return variable.to_string()

def sayfor(seconds, text):
    print(text)
    time.sleep(seconds)

def printinlines(linecount, text, inline=False):
    if inline:
        for i in range(linecount):
            print(text, end="")
    else:
        for i in range(linecount):
            print(text)

def whenfileran(code):
    if __name__ == "__main__":
        exec(code, globals())

def analyzedata(excelorcsvfile):
    if excelorcsvfile.endswith(".csv"):
        df = pd.read_csv(excelorcsvfile)
        return df
    elif excelorcsvfile.endswith(".xls" or ".xlsx"):
        xls = pd.ExcelFile(excelorcsvfile)
        parseddata = xls.parse(xls.sheet_names[0])
        return parseddata
    else:
        print("Error.")

def showpreviewdata(variable):
    return variable.head()

def openfile(filename, operationinsomeletters):
    return open(filename, mode=operationinsomeletters)

def readcontent(filenamevar):
    filenamevar.read()

def writecontent(filenamevar, content):
    filenamevar.write(content)

def manuallyclose(filenamevar):
    filenamevar.close()

def getfromenvfile(variable):
    os.getenv(variable)

def writemultiplelines(filenamevar, content):
    filenamevar.writelines(content)

def octal(value):
    return oct(value)

def getstatus(file):
    return os.stat(file)

def getsize(file):
    return os.path.getsize(file)

def getmodificationtime(file):
    return os.path.getmtime(file)

def getabsolutepath(file):
    return os.path.getabspath(file)

def readline(filenamevar):
    return filenamevar.readline()

def readlinesaslist(filenamevar):
    return filenamevar.readlines()

def getpermissions(filenamevar):
    return oct(filenamevar.st_mode)

def lastmodifieddata(filenamevar):
    return time.ctime(filenamevar.st_mtime)

def lastaccesseddata(filenamevar):
    return time.ctime(filenamevar.st_atime)

def With(ctxmanager, alias, code):
    globals()[alias] = ctxmanager.__enter__()
    try:
        exec(code, globals()) 
        
    finally:
        ctxmanager.__exit__(None, None, None)
        if alias in globals():
            del globals()[alias]

def delete(variable):
    try:
        del globals()[variable]
    except NameError:
        print("When using delete(variable), you must quote the variable you wanna delete.")

def spinbox(efn_root, efnframe, fromdata, todata, bg=None):
    parent = efnframe if efnframe else efn_root
    
    flag_data = f"{fromdata}_{todata}"
    flag = f"spinbox_{flag_data}_created"
    
    current_value = tk.StringVar(value=str(fromdata))

    if not hasattr(parent, flag):
        mainframe = tk.Frame(parent, bg=bg if bg else "white")
        mainframe.pack()
        
        spin_box = ttk.Spinbox(
            mainframe,
            from_=fromdata,
            to=todata,
            textvariable=current_value,
            wrap=True
        )
        spin_box.pack()
        
        setattr(parent, flag, True)
        
        return mainframe, current_value 
    
    return None, None

def stringspinbox(efn_root, efnframe, values: list):
    if not isinstance(values, list) or not values:
        raise ValueError("The 'values' argument must be a non-empty list of strings.")
        
    parent = efnframe if efnframe else efn_root
    
    flag = f"stringspinbox_{'_'.join(map(str, values))}_created"
    
    if not hasattr(parent, flag):
        mainframe = tk.Frame(parent)
        mainframe.pack()
        
        var = tk.StringVar(value=values[0])
        
        spin_box = ttk.Spinbox(
            mainframe,
            values=values,
            textvariable=var,
            wrap=True
        )
        spin_box.pack()
        
        setattr(parent, flag, True)
        return mainframe, var
    
    return None, None

def encode(variable):
    return variable.encode()

def decode(variable):
    return variable.decode()

def createfastapi():
    app = FastAPI()
    return app

def getfrom(content, mediatype):
    return Response(content=content, media_type=mediatype)

def getfilestats(filename):
    return os.fstat(filename)

def getstats(getfilestatsvarname, toget):
    return stats.st_toget

def createbranch(appvar, funcname, code, branch="/"):
    indentedcode = "\n    ".join(code.splitlines())
    fullcode = (
        f"@{appvar}.get('{branch}', response_class=HTMLResponse)\n"
        f"def {funcname}():\n"
        f"    {indentedcode}"
    )
    exec(fullcode, globals())
    return fullcode

def keypressed(key):
    return keyboard.is_pressed(key)

def onpress(callback):
    return keyboard.on_press(callback)

def onrelease(callback):
    return keyboard.on_release(callback)

def addhotkey(keys, callback):
    return keyboard.add_hotkey(keys, callback)

def endwhen(key):
    return keyboard.wait(key)

def getpythonversion():
    return sys.version

def extendedget(name, toget=None):
    return name.get(toget if toget else None)

def index(toindex, findinindex):
    return toindex.index(findinindex)

def createlabelframe(efn_root, efnframe, labeltext, bg=None, fg=None):
    parent = efnframe if efnframe else efn_root

    flag = f"labelframe_{labeltext}_created"

    if not hasattr(parent, flag):
        mainframe = ttk.LabelFrame(parent, text=labeltext, fg=fg if fg else "white")
        mainframe.configure(style="Custom.TLabelframe")
        mainframe.pack(padx=10, pady=10, fill="both", expand=True)

        if bg:
            style = ttk.Style()
            style.configure("Custom.TLabelframe", background=bg)
            style.configure("Custom.TLabelframe.Label", background=bg)

        setattr(parent, flag, True)

        return mainframe

    return None

def mathgamma(number):
    return math.gamma(number)

def sumof(numberlist):
    return sum(numberlist)

def multiplicationof(numberlist):
    return math.prod(numberlist)

def floatrandom(num1, num2):
    return random.uniform(num1, num2)

def setexactlengthlimit(variable, number):
    if len(variable) < number:
        return "Too short."
    else:
        return variable[:number]

def setminimumlengthlimit(variable, number):
    if len(variable) < number:
        return "Too short."
    else:
        return variable[:number]

def setmaximumlengthlimit(variable, number):
    if len(variable) > number:
        return "Too long."
    else:
        return variable

def createcycle(listname):
    return cycle(listname)

def divisionof(numberlist):
    return reduce(lambda a, b: a / b, numberlist)

def subtractionof(numberlist):
    return reduce(lambda a, b: a - b, numberlist)

def customreduce(*args):
    return reduce(*args)

def radians(radiansof):
    return math.radians(radiansof)

def times(howmanytimes):
    return range(howmanytimes)

def gettimeinzone(timezone):
    return pytz.timezone(timezone)

def datetimein(timezonevariable):
    return datetime.now(timezonevariable)

def enumerateit(iterable, start=None):
    return enumerate(iterable, start=start if start else 0)

def pair(*iterables):
    return zip(*iterables)

def timezonewidget(efn_root, efnframe=None, bg=None, fg=None):
    parent = efnframe if efnframe else efn_root
    flag = "timezone_widget_created"
    cities = {
        "New York": "America/New_York",
        "London": "Europe/London",
        "Tokyo": "Asia/Tokyo",
        "Sydney": "Australia/Sydney",
        "Budapest": "Europe/Budapest",
        "Shanghai": "Asia/Shanghai",
        "Vienna": "Europe/Vienna",
        "Berlin": "Europe/Berlin",
        "Madrid": "Europe/Madrid",
        "Casablanca": "Africa/Casablanca"
    }

    if not hasattr(parent, flag):
        mainframe = tk.Frame(parent, bg=bg if bg else "white")
        mainframe.pack()

        labels = {}
        for city in cities:
            label = tk.Label(mainframe, font=('Arial', 14), bg=bg if bg else "white", fg=fg if fg else "black")
            label.pack(anchor='w')
            labels[city] = label

        def update_time():
            for city, zone in cities.items():
                tz = pytz.timezone(zone)
                time = datetime.now(tz).strftime('%H:%M:%S')
                labels[city].config(text=f"{city}: {time}")
            mainframe.after(1000, update_time)

        update_time()
        setattr(parent, flag, True)
        return mainframe, labels

    return None, None

def getbattery():
    battery = psutil.sensors_battery()
    percent = battery.percent
    return f"{percent}%"

def batterywidget(efn_root, efnframe=None, bg=None, fg=None):
    parent = efnframe if efnframe else efn_root
    flag = "battery_widget_created"

    if not hasattr(parent, flag):
        battery = psutil.sensors_battery()
        percent = battery.percent if battery else 0

        mainframe = tk.Frame(parent, bg=bg if bg else "white")
        mainframe.pack()

        status = f"{percent}% Low battery." if percent <= 20 else f"{percent}%"
        label = tk.Label(mainframe, text=status, bg=bg if bg else "white", fg=fg if fg else "black")
        label.pack()

        setattr(parent, flag, True)
        return mainframe, label

    return None, None

def pop(pophost, topop):
    return pophost.pop(topop)

def raisewidgetabove(*args):
    widget.lift(*args)

def getmasterofwidget(widget):
    return widget.master

def createroundedwidgetconfiguration(efn_root, widget=None, text="Text", x=0, y=0, width=None, height=None, radius=15, bg="#4CAF50", fg="white", font=("Arial", 12), command=None, corners=None):
    corners = corners or {
        "top_left": True,
        "top_right": True,
        "bottom_left": True,
        "bottom_right": True
    }

    temp = tk.Label(efn_root, text=text, font=font)
    temp.update_idletasks()
    width = width or temp.winfo_reqwidth() + 20
    height = height or temp.winfo_reqheight() + 10
    temp.destroy()

    canvas = tk.Canvas(efn_root, width=width, height=height, highlightthickness=0, bd=0, bg=efn_root["bg"])
    canvas.place(x=x, y=y)

    r = radius

    if corners["top_left"]:
        canvas.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg, outline=bg)
    else:
        canvas.create_rectangle(0, 0, r, r, fill=bg, outline=bg)
    if corners["top_right"]:
        canvas.create_arc(width-2*r, 0, width, 2*r, start=0, extent=90, fill=bg, outline=bg)
    else:
        canvas.create_rectangle(width-r, 0, width, r, fill=bg, outline=bg)
    if corners["bottom_left"]:
        canvas.create_arc(0, height-2*r, 2*r, height, start=180, extent=90, fill=bg, outline=bg)
    else:
        canvas.create_rectangle(0, height-r, r, height, fill=bg, outline=bg)
    if corners["bottom_right"]:
        canvas.create_arc(width-2*r, height-2*r, width, height, start=270, extent=90, fill=bg, outline=bg)
    else:
        canvas.create_rectangle(width-r, height-r, width, height, fill=bg, outline=bg)

    canvas.create_rectangle(r, 0, width-r, height, fill=bg, outline=bg)
    canvas.create_rectangle(0, r, width, height-r, fill=bg, outline=bg)

    text_id = canvas.create_text(width//2, height//2, text=text, fill=fg, font=font)

    if callable(command):
        canvas.tag_bind(text_id, "<Button-1>", lambda e: command())

    return canvas

def configurehighlightthickness(efn_root, widget, highlightthickness):
    widget.configure(highlightthickness=highlightthickness)

def configureborderwidth(efn_root, widget, borderwidth):
    widget.configure(borderwidth=borderwidth)

def configurefillcolor(efn_root, widget, fillcolor):
    widget.configure(fill=fillcolor)

def configureoutlinecolor(efn_root, widget, outlinecolor):
    widget.configure(outline=outlinecolor)

def inserttoentry(efn_root, entrywidget, index, text):
    entrywidget.insert(index, text)

def labelframebox(efn_root, efnframe, text="Group", **kwargs):
    parent = efnframe if efnframe else efn_root
    flag = f"labelframebox_{text}_created"

    if not hasattr(parent, flag):
        frame = tk.LabelFrame(parent, text=text, **kwargs)
        frame.pack()
        setattr(parent, flag, True)
        return frame

    return None

def panedwindow(efn_root, efnframe, orient="horizontal", **kwargs):
    parent = efnframe if efnframe else efn_root
    flag = f"panedframebox_{orient}_created"

    if not hasattr(parent, flag):
        pane = tk.PanedWindow(parent, orient=orient, **kwargs)
        pane.pack(fill="both", expand=True)
        setattr(parent, flag, True)
        return pane

    return None

def iscallable(function):
    return callable(function)

def createcirclewindow(diameter=300, title="Circle", backgroundcolor="lime"):
    def destroyroot():
        root.destroy()

    root = tk.Tk()
    root.title(title)
    root.geometry(f"{diameter}x{diameter}+100+100")
    root.overrideredirect(True)
    root.wm_attributes("-transparentcolor", "pink")
    root.configure(bg="pink")

    circle_canvas = tk.Canvas(root, width=diameter, height=diameter, bg="pink", highlightthickness=0, bd=0)
    circle_canvas.place(x=0, y=0)

    circle_canvas.create_oval(0, 0, diameter, diameter, fill=backgroundcolor, outline="")
    circle_canvas.create_text(diameter//2, diameter//10, text=title, font=("Helvetica", 16), fill="#222222")

    btn_size = 35
    createroundedwidgetconfiguration(
        root,
        text="X",
        x=diameter - btn_size - 10,
        y=10,
        width=btn_size,
        height=btn_size,
        radius=btn_size//2,
        bg="red",
        fg="white",
        font=("Arial", 12, "bold"),
        command=destroyroot
    )
    root.update()
    root.mainloop()

def bindtag(efn_root, widget, tagOrId, sequence=None, function=None, add=None):
    widget.tag_bind(tagOrId, sequence, function, add)

def makestyle(efn_root):
    style = ttk.Style()
    return style

def configurestyle(efn_root, stylename, **options):
    return style.configure(stylename, **options)

def floor(num1, num2):
    return num1 // num2

def tetration(littlenumber, bignumber):
    if bignumber == 1:
        return littlenumber
    else:
        return littlenumber ** tetration(littlenumber, bignumber - 1)

def pentation(littlenumber, bignumber):
    if bignumber == 1:
        return littlenumber
    else:
        return tetration(littlenumber, pentation(littlenumber, bignumber - 1))

def hexation(littlenumber, bignumber):
    if bignumber == 1:
        return littlenumber
    else:
        return pentation(littlenumber, hexation(littlenumber, bignumber - 1))

def septation(littlenumber, bignumber):
    if bignumber == 1:
        return littlenumber
    else:
        return hexation(littlenumber, septation(littlenumber, bignumber - 1))

def octation(littlenumber, bignumber):
    if bignumber == 1:
        return littlenumber
    else:
        return septation(littlenumber, octation(littlenumber, bignumber - 1))

def nonation(littlenumber, bignumber):
    if bignumber == 1:
        return littlenumber
    else:
        return octation(littlenumber, nonation(littlenumber, bignumber - 1))

def decation(littlenumber, bignumber):
    if bignumber == 1:
        return littlenumber
    else:
        return nonation(littlenumber, decation(littlenumber, bignumber - 1))

def setrecursionlimit(number):
    return sys.setrecursionlimit(number)

def safepower(num1, num2):
    return math.pow(num1, num2)

def dangerouspower(num1, num2):
    return num1 ** num2

def configurestyletowidget(efn_root, widget, style):
    widget.configure(style=style)

def raised(efn_root):
    return tk.RAISED

def configureexpand(efn_root, widget, value):
    widget.configure(expand=value)

def flatstyle(efn_root):
    return tk.FLAT

def groovystyle(efn_root):
    return tk.GROOVE

def ridgedstyle(efn_root):
    return tk.RIDGE

def sunkenstyle(efn_root):
    return tk.SUNKEN

class Switch(tk.Canvas):
    def __init__(self, master=None, width=50, height=25, bg_off="#ccc", bg_on="#4CAF50", fillcolor="#317173", command=None):
        super().__init__(master, width=width, height=height, bg=master["bg"], highlightthickness=0)
        self.bg_off = bg_off
        self.bg_on = bg_on
        self.fillcolor = fillcolor
        self.command = command
        self.is_on = False

        self.circle = self.create_oval(2, 2, height-2, height-2, fill=fillcolor, outline="")
        self.rect = self.create_rectangle(0, 0, width, height, fill=bg_off, outline="")
        self.tag_lower(self.circle)

        self.bind("<Button-1>", self.toggle)

        self.draw_switch()

    def draw_switch(self):
        if self.is_on:
            self.itemconfig(self.rect, fill=self.bg_on)
            self.coords(self.circle, self.winfo_width() - self.winfo_height() + 2, 2, self.winfo_width() - 2, self.winfo_height() - 2)
        else:
            self.itemconfig(self.rect, fill=self.bg_off)
            self.coords(self.circle, 2, 2, self.winfo_height() - 2, self.winfo_height() - 2)

    def toggle(self, event=None):
        self.is_on = not self.is_on
        self.draw_switch()
        if self.command:
            self.command(self.is_on)

class TabView(tk.Frame):
    def __init__(self, master, tabs, **kwargs):
        super().__init__(master, **kwargs)
        self.tabs = tabs
        self.buttons = {}
        self.frames = {}
        self.active_tab = None

        self.tab_bar = tk.Frame(self)
        self.tab_bar.pack(side=tk.TOP, fill=tk.X)

        for tab_name in tabs:
            btn = tk.Button(self.tab_bar, text=tab_name, command=lambda n=tab_name: self.select_tab(n))
            btn.pack(side=tk.LEFT, padx=2, pady=2)
            self.buttons[tab_name] = btn

            frame = tk.Frame(self)
            self.frames[tab_name] = frame

        self.select_tab(list(tabs.keys())[0])

    def select_tab(self, tab_name):
        if self.active_tab:
            self.frames[self.active_tab].pack_forget()
            self.buttons[self.active_tab].config(relief=tk.RAISED)
        self.frames[tab_name].pack(fill=tk.BOTH, expand=True)
        self.buttons[tab_name].config(relief=tk.SUNKEN)
        self.active_tab = tab_name

def configurecommand(efn_root, widget, function):
    widget.configure(command=function)
    
class OptionMenu:
    def __init__(self, efn_root, options):
        self.efn_root = efn_root
        self.options = options
        self.btn = {}
        for i, option in enumerate(options):
            self.btn[option] = tk.Button(efn_root, text=option)

    def placebutton(self, valueofbutton, x, y):
        if valueofbutton in self.btn:
            self.btn[valueofbutton].place(x=x, y=y)

    def packbutton(self, valueofbutton, *args, **kwargs):
        if valueofbutton in self.btn:
            self.btn[valueofbutton].pack(*args, **kwargs)

    def gridbutton(self, valueofbutton, *args, **kwargs):
        if valueofbutton in self.btn:
            self.btn[valueofbutton].grid(*args, **kwargs)

    def onoption(self, value, command):
        if value in self.btn:
            self.btn[value].configure(command=command)

def configureboundary(efn_root, widget, value):
    widget.configure(bd=value)

def west(efn_root):
    return tk.W

def east(efn_root):
    return tk.E

def north(efn_root):
    return tk.N

def south(efn_root):
    return tk.S

def southeast(efn_root):
    return tk.SE

def northeast(efn_root):
    return tk.NE

def southwest(efn_root):
    return tk.SW

def northwest(efn_root):
    return tk.NW

def center(efn_root):
    return tk.CENTER

def noneanchor(efn_root):
    return tk.NONE

def leftjustify(text, width, fillchar=None):
    text.ljust(width, fillchar=fillchar if fillchar else "")

def rightjustify(text, width, fillchar=None):
    text.rjust(width, fillchar=fillchar if fillchar else "")

def staticmethod(funcname, code):
    indentedcode = "\n    ".join(code.splitlines())
    fullcode = f"@staticmethod\ndef {funcname}():\n    {indentedcode}"
    return fullcode

def property(funcname, code):
    indentedcode = "\n    ".join(code.splitlines())
    fullcode = f"@property\ndef {funcname}():\n    {indentedcode}"
    return fullcode

def topgui(efn_root):
    return tk.TOP

def bottomgui(efn_root):
    return tk.BOTTOM

def boundbox(efn_root, widget, tobbox):
    return widget.bbox(f"{tobbox}")

def configurescrollregion(efn_root, widget, scrollregion):
    widget.configure(scrollregion=scrollregion)

def rightgui(efn_root):
    return tk.RIGHT

def leftgui(efn_root):
    return tk.LEFT

def xview(efn_root, widget):
    return widget.xview

def yview(efn_root, widget):
    return widget.yview

def configurefill(efn_root, widget, fill):
    widget.configure(fill=fill)

def setviewscrollbar(efn_root, scrollbarvariable):
    return scrollbarvariable.set

def configurexscrollcommand(efn_root, widget, xscrollcommand):
    widget.configure(widget, xscrollcommand=xscrollcommand)

def configureyscrollcommand(efn_root, widget, yscrollcommand):
    widget.configure(widget, yscrollcommand=yscrollcommand)

def configuredash(efn_root, canvas, dash):
    canvas.configure(dash=dash)

def configureoffset(efn_root, canvas, offset):
    canvas.configure(offset=offset)

def configuredisableddash(efn_root, canvas, disableddash):
    canvas.configure(disableddash=disableddash)

def createwindow(efn_root, canvas, x, y, parent, anchor, width, height, tags, state):
    canvaswindow = canvas.create_window(x, y, window=parent, anchor=anchor, width=width, height=height, tags=tags, state=state)
    return canvaswindow

def callthis(tocall, subfunction=None, *args, **kwargs):
    if subfunction:
        tocall[subfunction](*args, **kwargs)
    else:
        tocall(*args, **kwargs)

def addxscroll(efn_root, widget, orient="horizontal"):
    parent = widget.master or efn_root
    xscroll = tk.Scrollbar(parent, orient=orient)
    widget.configure(xscrollcommand=xscroll.set)
    xscroll.configure(command=widget.xview)
    xscroll.pack(side="bottom", fill="x")
    return xscroll

def addyscroll(efn_root, widget, orient="horizontal"):
    parent = widget.master or efn_root
    yscroll = tk.Scrollbar(parent, orient=orient)
    widget.configure(yscrollcommand=yscroll.set)
    yscroll.configure(command=widget.yview)
    yscroll.pack(side="bottom", fill="y")
    return yscroll


class LoadingWidget(tk.Canvas):
    def __init__(self, efn_root, efnframe=None, size=100, line_width=10, speed=5):
        parent = efnframe if efnframe else efn_root
        flag = "_loading_widget_created"

        if hasattr(parent, flag):
            return

        super().__init__(parent, width=size, height=size, bg='white', highlightthickness=0)
        self.size = size
        self.line_width = line_width
        self.speed = speed
        self.angle = 0
        self.draw_arc()
        self.animate()
        self.pack()
        setattr(parent, flag, True)

    def draw_arc(self):
        self.delete("arc")
        self.create_arc(
            self.line_width,
            self.line_width,
            self.size - self.line_width,
            self.size - self.line_width,
            start=self.angle,
            extent=90,
            style='arc',
            outline='green',
            width=self.line_width,
            tags="arc"
        )

    def animate(self):
        self.angle = (self.angle + self.speed) % 360
        self.draw_arc()
        self.after(50, self.animate)

def greenwhiteload(efn_root, efnframe=None, width=200, height=50):
    parent = efnframe if efnframe else efn_root
    flag = "__greenwhiteload_widget_created"

    if hasattr(parent, flag):
        return None, None

    mainframe = tk.Frame(parent, width=width, height=height)
    mainframe.pack()

    greenlbl = tk.Label(mainframe, width=width, height=height, bg='green')
    greenlbl.pack()

    whitelbl = tk.Label(mainframe, width=width//4, height=height, bg='white')
    whitelbl.place(x=0, y=0)

    step = 5
    pos = 0

    def move():
        nonlocal pos
        pos += step
        if pos > width:
            pos = 0
        whitelbl.place(x=pos, y=0)
        whitelbl.after(50, move)

    move()
    setattr(parent, flag, True)
    return mainframe, whitelbl

def accessnonlocal(variable):
    def inner():
        nonlocal variable
    return inner()

def customizabletimezonewidget(efn_root, timezonesdict, efnframe=None, bg=None, fg=None):
    parent = efnframe if efnframe else efn_root
    flag = f"timezone_widget_created_with_{timezonesdict.get()}"
    cities = timezonesdict.get()

    if not hasattr(parent, flag):
        mainframe = tk.Frame(parent, bg=bg if bg else "white")
        mainframe.pack()

        labels = {}
        for city in cities:
            label = tk.Label(mainframe, font=('Arial', 14), bg=bg if bg else "white", fg=fg if fg else "black")
            label.pack(anchor='w')
            labels[city] = label

        def update_time():
            for city, zone in cities.items():
                tz = pytz.timezone(zone)
                time = datetime.now(tz).strftime('%H:%M:%S')
                labels[city].config(text=f"{city}: {time}")
            mainframe.after(1000, update_time)

        update_time()
        setattr(parent, flag, True)
        return mainframe, labels

    return None, None

class ComplexSwitch(tk.Frame):
    def __init__(self, efn_root, efnframe=None, text='Switch', command=None, **kwargs):        
        parent = efn_root if not efnframe else efnframe
        super().__init__(parent, **kwargs)
        
        self._command = command
        self._state = False

        self.main_label = tk.Label(self, text=text, width=10, fg='white',
                                   font=('Arial', 12, 'bold'))
        self.main_label.pack(side='left', padx=(0,5), pady=5)
        
        self.sub_label = tk.Label(self, text='OFF', bg='white', fg='black',
                                  width=5, font=('Arial', 10))
        self.sub_label.pack(side='left', pady=5)

        self.bind_widgets(self.main_label)
        self.bind_widgets(self.sub_label)
        self.bind_widgets(self)

        self._update_appearance()

    def bindwidgets(self, widget):
        widget.bind('<Button-1>', self._on_click)

    def onclick(self, event):
        self._state = not self._state
        self._update_appearance()
        if self._command:
            self._command(self._state)

    def updateappearance(self):
        if self._state:
            self.main_label.config(bg='green')
            self.sub_label.config(text='ON')
        else:
            self.main_label.config(bg='gray')
            self.sub_label.config(text='OFF')

def newline():
    return "\n"

def isanagram(wordone, wordtwo):
    counterwordone = Counter(wordone)
    counterwordtwo = Counter(wordtwo)
    return counterwordone == counterwordtwo

def counter(data):
    Counter(data)

def carriagereturn():
    return f"\r"

def carriagereturnbefore(times, line):
    return '\r' * times + line

def carriagereturnafter(times, line):
    return line + '\r' * times

def tab():
    return f"\t"

def tabbefore(times, text):
    return '\t' * times + text

def tabafter(times, text):
    return text + '\t' * times

def backspace():
    return f"\b"

def backspacebefore(times, text):
    return '\b' * times + text

def backspaceafter(times, text):
    return text + '\b' * times

def formfeed():
    return f"\f"

def formfeedbefore(times, text):
    return '\f' * times + text

def formfeedafter(times, text):
    return text + '\f' * times

def verticaltab():
    return f"\v"

def verticaltabbefore(times, text):
    return '\v' * times + text

def verticaltabafter(times, text):
    return text + '\v' * times

def octalline(code):
    return f"\{code}"

def octallinebefore(times, code, text):
    return f"\{code}" * times + text

def octallineafter(times, code, text):
    return text + f"\{code}" * times

def hexa():
    return fr"\x"

def hexabefore(times, code, text):
    return fr"\x{code}" * times + text

def hexaafter(times, code, text):
    return text + fr"\x{code}" * times

def unicode16():
    return fr"\u"

def unicode16before(times, code, text):
    return fr"\u{code}" * times + text

def unicode16after(times, code, text):
    return text + fr"\u{code}" * times

def unicode32():
    return fr"\U"

def unicode32before(times, code, text):
    return fr"\U{code}" * times + text

def unicode32after(times, code, text):
    return text + fr"\U{code}" * times

def createdictionary(data):
    return {data}

def createlistarray(data):
    return [data]

def pathorfileexists(pathorfile):
    return os.path.exists(pathorfile)

def isfile(fileorpath):
    return os.path.isfile(fileorpath)

def isdirectory(pathorfile):
    return os.path.isdir(pathorfile)

def isfibonacci(number):
    return number >= 0 and (
        (lambda x: int(math.isqrt(x))**2 == x)(5*number*number + 4) or
        (lambda x: int(math.isqrt(x))**2 == x)(5*number*number - 4)
    )

def dataclass(classname, code):
    indentedcode = "\n    ".join(code.splitlines())
    fullcode = f"@dataclass\nclass {classname}():\n    {indentedcode}"
    return fullcode

def widgetx(efn_root, widget):
    return widget.x

def widgety(efn_root, widget):
    return widget.y

def returnunicode(value):
    return ord(value)

def bytearrayof(value):
    return bytearray(value)

def unicodepoint(value):
    return chr(value)

def configurecompound(efn_root, widget, compound):
    widget.configure(compound=compound)

def createwinaerowindow(title, geometry, bg, icon, fullscreen=False):
    RESIZEBORDER = 6
    efn_root = tk.Tk()
    efn_root.title(title)
    efn_root.geometry(geometry)
    efn_root.configure(bg=bg)
    efn_root.wm_overrideredirect(True)
    
    EFNPATH = os.path.dirname(__file__)
    imageborderpath = os.path.join(EFNPATH, "WinAero Border.png")
    original = Image.open(imageborderpath)
    left = original.crop((0, 0, 10, 20))
    middle = original.crop((10, 0, original.width-10, 20))
    right = original.crop((original.width-10, 0, original.width, 20))

    lefttk = ImageTk.PhotoImage(left)
    righttk = ImageTk.PhotoImage(right)

    leftlbl = tk.Label(efn_root, image=lefttk, bg=bg)
    leftlbl.image = lefttk
    leftlbl.place(x=0, y=0)

    middlelbl = tk.Label(efn_root, bg=bg)
    middlelbl.place(x=10, y=0)

    rightlbl = tk.Label(efn_root, image=righttk, bg=bg)
    rightlbl.image = righttk
    rightlbl.place(x=0, y=0)

    titlelbl = tk.Label(efn_root, text=title, fg="black", bg="#285a77")
    titlelbl.place(x=1, y=1)

    imagexbtnpath = os.path.join(EFNPATH, "WinAero X.png")
    xbtnimg = Image.open(imagexbtnpath).resize((30, 15))
    xbtntk = ImageTk.PhotoImage(xbtnimg)
    xbtn = tk.Button(efn_root, image=xbtntk, command=efn_root.destroy, bg="#2b5a74", relief="flat")
    xbtn.image = xbtntk

    imageminusbtnpath = os.path.join(EFNPATH, "WinAero -.png")
    minusbtnimg = Image.open(imageminusbtnpath).resize((20, 15))
    minusbtntk = ImageTk.PhotoImage(minusbtnimg)
    minusbtn = tk.Button(efn_root, image=minusbtntk, command=efn_root.withdraw, bg="#2b5a74", relief="flat")
    minusbtn.image = minusbtntk

    efn_root.update_idletasks()
    w = max(efn_root.winfo_width(), 20)
    middle_resized = middle.resize((w-20, 20))
    middletk = ImageTk.PhotoImage(middle_resized)
    middlelbl.config(image=middletk)
    middlelbl.image = middletk
    rightlbl.place(x=w-10, y=0)
    xbtn.place(x=w-35, y=0)
    minusbtn.place(x=w-55, y=0)

    if platform.system() == "Windows":
        efn_root.iconbitmap(icon)
    else:
        iconimg = tk.PhotoImage(file=icon)
        efn_root.iconphoto(False, iconimg)

    efn_root.attributes("-fullscreen", fullscreen)
    keyboard.add_hotkey(("Ctrl", "R"), lambda: efn_root.deiconify())

    def startmove(event):
        efn_root.offsetx = event.x
        efn_root.offsety = event.y

    def stopmove(event):
        efn_root.offsetx = None
        efn_root.offsety = None

    def domove(event):
        x = event.x_root - efn_root.offsetx
        y = event.y_root - efn_root.offsety
        efn_root.geometry(f"+{x}+{y}")

    def getresizezone(event):
        x = event.x
        y = event.y
        w = efn_root.winfo_width()
        h = efn_root.winfo_height()
        left = x <= RESIZEBORDER
        right = x >= w - RESIZEBORDER
        top = y <= RESIZEBORDER
        bottom = y >= h - RESIZEBORDER
        if left and top: return "topleft"
        if right and top: return "topright"
        if left and bottom: return "bottomleft"
        if right and bottom: return "bottomright"
        if left: return "left"
        if right: return "right"
        if top: return "top"
        if bottom: return "bottom"
        return None

    def startresize(event):
        efn_root.dragstartx = event.x_root
        efn_root.dragstarty = event.y_root
        efn_root.startwidth = efn_root.winfo_width()
        efn_root.startheight = efn_root.winfo_height()
        efn_root.startx = efn_root.winfo_x()
        efn_root.starty = efn_root.winfo_y()
        efn_root.resize_dir = getresizezone(event)

    def doresize(event):
        zone = efn_root.resize_dir
        if not zone: return
        dx = event.x_root - efn_root.dragstartx
        dy = event.y_root - efn_root.dragstarty
        x = efn_root.startx
        y = efn_root.starty
        w = efn_root.startwidth
        h = efn_root.startheight
        if "right" in zone: w = max(150, w + dx)
        if "left" in zone: w = max(150, w - dx); x += dx
        if "bottom" in zone: h = max(100, h + dy)
        if "top" in zone: h = max(100, h - dy); y += dy
        efn_root.geometry(f"{w}x{h}+{x}+{y}")
        w = max(w, 20)
        middle_resized = middle.resize((w-20, 20))
        middletk_new = ImageTk.PhotoImage(middle_resized)
        middlelbl.config(image=middletk_new)
        middlelbl.image = middletk_new
        rightlbl.place(x=w-10, y=0)
        xbtn.place(x=w-35, y=0)
        minusbtn.place(x=w-55, y=0)

    efn_root.bind("<ButtonPress-1>", startresize)
    efn_root.bind("<B1-Motion>", doresize)
    leftlbl.bind("<ButtonPress-1>", startmove)
    leftlbl.bind("<ButtonRelease-1>", stopmove)
    leftlbl.bind("<B1-Motion>", domove)
    middlelbl.bind("<ButtonPress-1>", startmove)
    middlelbl.bind("<ButtonRelease-1>", stopmove)
    middlelbl.bind("<B1-Motion>", domove)
    rightlbl.bind("<ButtonPress-1>", startmove)
    rightlbl.bind("<ButtonRelease-1>", stopmove)
    rightlbl.bind("<B1-Motion>", domove)

    efn_root.update()
    return efn_root

def directory(objectlist):
    return dir(objectlist)

def processiterator(attributes=None, advalue=None):
    return psutil.process_iter(attrs=attributes, ad_value=advalue)

def processpid(process):
    return process.pid

def processmemoryinfo(process):
    return process.memory_info().rss

def processmemorypercent(process):
    return process.memory_percent()

def processuser(process):
    return process.user()

def processname(process):
    return process.name()

def processexe(process):
    return process.exe()

def processcmdline(process):
    return process.cmdline()

def processenvironment(process):
    return process.environ()

def processuids(process):
    return process.uids()

def processgids(process):
    return process.gids()

def processterminal(process):
    return process.terminal()

def processstatus(process):
    return process.status()

def cputimes(percpu=False):
    return psutil.cpu_times(percpu=percpu)

def cputimespercent(interval=None, percpu=False):
    return psutil.cpu_times_percent(interval=interval, percpu=percpu)

def cpucount(logical=True):
    return psutil.cpu_count(logical=logical)

def usablecpus():
    return len(psutil.Process().cpu_affinity())

def cpuaffinity(process, cpus=None):
    return process.cpu_affinity(cpus=cpus)

def Process(pid=None):
    return psutil.Process(pid=pid)

def psutilveresion():
    return psutil.version_info

def diskusage(path):
    return psutil.disk_usage(path)

def cpustats():
    return psutil.cpu_stats()

def cpufrequency(percpu=False):
    return psutil.cpu_freq(percpu=percpu)

def averagesysload():
    return psutil.getloadavg()

def virtualmemorystats():
    return psutil.virtual_memory()

def swapmemorystats():
    return psutil.swap_memory()

def diskpartitions(allvar=False):
    return psutil.disk_partitions(all=allvar)

def diskiocounters(perdisk=False, nowrap=True):
    return psutil.disk_io_counters(perdisk=perdisk, nowrap=nowrap)

def netiocounters(pernic=False, nowrap=True):
    return psutil.net_io_counters(pernic=pernic, nowrap=nowrap)

def netconnections(kind='inet'):
    return psutil.net_connections(kind=kind)

def netifaddress():
    return psutil.net_if_addrs()

def netifstats():
    return psutil.net_if_stats()

def hardwaretemperatures(fahrenheit=False):
    return psutil.sensors_temperatures(fahrenheit=fahrenheit)

def fanspeed():
    return psutil.sensors_fans()

def battery():
    return psutil.sensors_battery()

def batterypercentobject(batteryvar):
    return batteryvar.percent

def secondssince1970():
    return psutil.boot_time()

def connectedusers():
    return psutil.users()

def currentpids():
    return psutil.pids()

def pidexists(pid):
    return psutil.pid_exists(pid)

def waitprocesses(procs, timeout=None, callback=None):
    return psutil.wait_procs(procs, timeout=timeout, callback=callback)

def terminatedreturncode(process):
    return process.returncode

def childrenof(process, recursive=False):
    return process.children(recursive=recursive)

def terminate(process):
    return process.terminate()

def kill(process):
    return process.kill()

def oneshot(process):
    return process.oneshot()

def retrieveasdict(attributes=None, advalue=None):
    return as_dict(attrs=attributes, ad_value=advalue)

def parentof(process):
    return process.parent()

def parentsof(process):
    return process.parents()

def currentworkingdir(process):
    return process.cwd()

def setniceness(process, value=None):
    return process.nice(value=value)

def setioniceness(process, ioclass=None, value=None):
    return process.ionice(ioclass=ioclass, value=value)

def psutilvariable(variablenameafterpsutil):
    return getattr(psutil, variablenameafterpsutil)

def getsetresourcelimit(resource, limits=None):
    return psutil.rlimit(resource, limits=limits)

def iocounters(process):
    return process.io_counters()

def numctxswitches(process):
    return process.num_ctx_switches()

def numfiledescrs(process):
    return process.num_fds()

def numhandles(process):
    return process.num_handles()

def numthreads(process):
    return process.num_threads()

def threads(process):
    return process.threads()

def cputimes(process):
    return process.cpu_times()

def cpupercent(process, interval=None):
    return process.cpu_times(interval=interval)

def cpunumber(process):
    return process.cpu_num()

def fullmemoryinfo(process):
    return process.memory_full_info()

def memorypercent(process, memorytype='rss'):
    return process.memory_percent(memorytype=memorytype)

def memorymaps(process, grouped=True):
    return process.memory_maps(grouped=grouped)

def openfiles(process):
    return process.open_files()

def processrunning(process):
    return process.is_running()

def sendsignal(process, signal):
    return process.send_signal(signal)

def suspend(process):
    return process.suspend()

def resume(process):
    return process.resume()

def waitprocess(process, timeout=None):
    return process.wait(timeout=timeout)

def heapinfo():
    return psutil.heap_info()

def heaptrim():
    return psutil.heap_trim()

def windowsserviceiterator():
    return psutil.win_service_iter()

def windowsserviceget(name):
    return psutil.win_service_get(name)

def servicename(winservice):
    return winservice.name()

def displayname(winservice):
    return winservice.display_name()

def binpath(winservice):
    return winservice.binpath()

def ownername(winservice):
    return winservice.username()

def starttype(winservice):
    return winservice.start_type()

def winservicepid(winservice):
    return winservice.pid()

def winservicestatus(winservice):
    return winservice.status()

def winservicedescription(winservice):
    return winservice.description()

def retrievewinservicedataasdict(winservice):
    return winservice.as_dict()

def convertEnum(value, enumType, default):
    return socket._intenum_converter(value, enumType, default)

def makeConnection(address, port, timeout=None):
    return socket.create_connection((address, port), timeout=timeout)

def makeServer(address, port, family=socket.AF_INET, backlog=None, reuse_port=False):
    return socket.create_server((address, port), family=family, backlog=backlog, reuse_port=reuse_port)

def fromFileDescriptor(fd, family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
    return socket.fromfd(fd, family, type, proto)

def fromShare(info):
    return socket.fromshare(info)

def getAddressInfo(host, port, family=0, type=0, proto=0, flags=0):
    return socket.getaddrinfo(host, port, family, type, proto, flags)

def getFqdn(name=""):
    return socket.getfqdn(name)

def hasDualstackIpv6():
    return socket.has_dualstack_ipv6()

def makeSocketPair(family=None, type=socket.SOCK_STREAM, proto=0):
    if family is None:
        family = getattr(socket, "AF_UNIX", socket.AF_INET)
    return socket.socketpair(family, type, proto)

def makeSocket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
    return socket.socket(family, type, proto)

def bindSocket(sock, address):
    return sock.bind(address)

def listenSocket(sock, backlog=5):
    return sock.listen(backlog)

def acceptConnection(sock):
    return sock.accept()

def connectSocket(sock, address):
    return sock.connect(address)

def connectEx(sock, address):
    return sock.connect_ex(address)

def sendData(sock, data, flags=0):
    return sock.send(data, flags)

def sendAllData(sock, data, flags=0):
    return sock.sendall(data, flags)

def receiveData(sock, bufsize=1024, flags=0):
    return sock.recv(bufsize, flags)

def receiveIntoBuffer(sock, buffer, nbytes=0, flags=0):
    return sock.recv_into(buffer, nbytes, flags)

def receiveMessage(sock, bufsize=1024, ancbufsize=0, flags=0):
    return sock.recvmsg(bufsize, ancbufsize, flags)

def receiveMessageInto(sock, buffers, ancbufsize=0, flags=0):
    return sock.recvmsg_into(buffers, ancbufsize, flags)

def sendMessage(sock, buffers, ancdata=(), flags=0, address=None):
    return sock.sendmsg(buffers, ancdata, flags, address)

def sendFile(sock, file, offset=0, count=None):
    return sock.sendfile(file, offset, count)

def closeSocket(sock):
    return sock.close()

def detachSocket(sock):
    return sock.detach()

def setSocketOption(sock, level, option, value):
    return sock.setsockopt(level, option, value)

def getSocketOption(sock, level, option, bufsize=0):
    return sock.getsockopt(level, option, bufsize)

def setTimeout(sock, value):
    return sock.settimeout(value)

def getTimeout(sock):
    return sock.gettimeout()

def shutdownSocket(sock, how):
    return sock.shutdown(how)

def getFileDescriptor(sock):
    return sock.fileno()

def getSocketName(sock):
    return sock.getsockname()

def getPeerName(sock):
    return sock.getpeername()

def duplicateSocket(sock):
    return sock.dup()

def makeFileObject(sock, mode="r", buffering=None):
    return sock.makefile(mode, buffering)

def getBlockingMode(sock):
    return sock.getblocking()

def setBlockingMode(sock, flag):
    return sock.setblocking(flag)

def getInheritable(sock):
    return sock.get_inheritable()

def setInheritable(sock, inheritable):
    return sock.set_inheritable(inheritable)

def ioctlSocket(sock, control, option):
    return sock.ioctl(control, option)

def socketvariable(variablenameaftersocket):
    return getattr(socket, variablenameaftersocket)

def pythonlicense():
    return license()

def helpaboutpython():
    return help()

def pythoncopyright():
    return copyright()

def pythoncredits():
    return credits()

def helpaboutpyobject(object):
    return help(object)

def pyfunction(functionname, code, *args, **kwargs):
    positional = list(args)
    keyword = [f"{k}={v!r}" for k, v in kwargs.items()]
    params = ", ".join(positional + keyword)

    indented_code = "\n".join("    " + line for line in code.split("\n"))

    src = f"def {functionname}({params}):\n{indented_code}"

    namespace = {}
    exec(src, namespace)

    return namespace[functionname]

def callpyfunctionorclass(functionorclassname, *args, **kwargs):
    functionorclassname(*args, **kwargs)

def pyclass(classname, code, *args, **kwargs):
    positional = list(args)
    keyword = [f"{k}={v!r}" for k, v in kwargs.items()]
    params = ", ".join(positional + keyword)

    indented_code = "\n".join("    " + line for line in code.split("\n"))

    src = f"class {classname}({params}):\n{indented_code}"

    cnamespace = {}
    exec(src, cnamespace)

    return cnamespace[classname]

def standardoutput():
    return sys.stdout

def standardinput():
    return sys.stdin

def standardwrite(text):
    sys.stdout.write(text)

def standardreadline(size=-1):
    sys.stdin.readline(size=size)

class strip:
    def __init__(self, variable, charstoremove=None):
        self.original = variable
        self.stripped = variable.strip(charstoremove)

    def restore(self):
        return self.original

def convertwithstring(var, format=None):
    return f"{var!s:{format}}"

def convertwithrepresent(var, format=None):
    return f"{var!r:{format}}"

def convertwithascii(var, format=None):
    return f"{var!a:{format}}"

def newimport(stringcustomname, stringmodulename, submodule=None):
    if not submodule:
        let(stringcustomname, value=__import__(stringmodulename))
    else:
        let(stringcustomname, value=__import__(stringmodulename).submodule)

def mathisclose(num1, num2, relativetolerance=1e-9, absolutetolerance=0.0):
    return math.isclose(num1, num2, rel_tol=relativetolerance, abs_tol=absolutetolerance)

def nameof(object):
    return object.__name__

defaultdecoder = json._default_decoder
defaultencoder = json._default_encoder
codecsvar = json.codecs
decodervar = json.decoder
encodervar = json.encoder
scannervar = json.scanner
toolvar = json.tool

def detectencoding(data):
    return json.detect_encoding(data)

def dump(obj, file, skipkeys=False, ensureascii=True, checkcircular=True, allownan=True,
         cls=None, indent=None, separators=None, default=None, sortkeys=False, **kw):
    return json.dump(obj, file, skipkeys=skipkeys, ensure_ascii=ensureascii,
                     check_circular=checkcircular, allow_nan=allownan, cls=cls,
                     indent=indent, separators=separators, default=default, sort_keys=sortkeys, **kw)

def dumps(obj, skipkeys=False, ensureascii=True, checkcircular=True, allownan=True,
          cls=None, indent=None, separators=None, default=None, sortkeys=False, **kw):
    return json.dumps(obj, skipkeys=skipkeys, ensure_ascii=ensureascii,
                      check_circular=checkcircular, allow_nan=allownan, cls=cls,
                      indent=indent, separators=separators, default=default, sort_keys=sortkeys, **kw)

def load(file, cls=None, objecthook=None, parsefloat=None, parseint=None, parseconstant=None,
         objectpairshook=None, **kw):
    return json.load(file, cls=cls, object_hook=objecthook, parse_float=parsefloat,
                     parse_int=parseint, parse_constant=parseconstant,
                     object_pairs_hook=objectpairshook, **kw)

def loads(string, cls=None, objecthook=None, parsefloat=None, parseint=None, parseconstant=None,
          objectpairshook=None, **kw):
    return json.loads(string, cls=cls, object_hook=objecthook, parse_float=parsefloat,
                      parse_int=parseint, parse_constant=parseconstant,
                      object_pairs_hook=objectpairshook, **kw)

escape = json.encoder.ESCAPE
escapeascii = json.encoder.ESCAPE_ASCII
escapedct = json.encoder.ESCAPE_DCT
hasutf8 = json.encoder.HAS_UTF8
infinity = json.encoder.INFINITY
cencodebasestring = json.encoder.c_encode_basestring
cencodebasestringascii = json.encoder.c_encode_basestring_ascii
encodebasestring = json.encoder.encode_basestring
encodebasestringascii = json.encoder.encode_basestring_ascii
reencoder = json.encoder.re

backslash = json.decoder.BACKSLASH
flags = json.decoder.FLAGS
nan = json.decoder.NaN
neginf = json.decoder.NegInf
posinf = json.decoder.PosInf
stringchunk = json.decoder.STRINGCHUNK
whitespace = json.decoder.WHITESPACE
whitespacestr = json.decoder.WHITESPACE_STR
constants = json.decoder._CONSTANTS
cscanstring = json.decoder.c_scanstring
scannerdecoder = json.decoder.scanner
scanstring = json.decoder.scanstring

numberre = json.scanner.NUMBER_RE

argparsevar = json.tool.argparse
jsonvar = json.tool.json
sysvar = json.tool.sys

def pyencodebasestring(string):
    return json.encoder.py_encode_basestring(string)

def pyencodebasestringascii(string):
    return json.encoder.py_encode_basestring_ascii(string)

def makeiterencode(obj, currentindentlevel=0, indent=None, floatstr=None, keyseparator=None,
                   itemseparator=None, sortkeys=False, skipkeys=False, allownan=True, default=None):
    return json.encoder._make_iterencode(obj, current_indent_level=currentindentlevel, indent=indent,
                                         floatstr=floatstr, key_separator=keyseparator,
                                         item_separator=itemseparator, sort_keys=sortkeys, skipkeys=skipkeys,
                                         allow_nan=allownan, default=default)

def jsonarray(sandend, scanonce, **kw):
    return json.decoder.JSONArray(sandend, scanonce, **kw)

def jsonobject(sandend, scanonce, **kw):
    return json.decoder.JSONObject(sandend, scanonce, **kw)

def decodeuxxxx(s, end):
    return json.decoder._decode_uXXXX(s, end)

def pyscanstring(s, end, strict=True, b='\\'):
    return json.decoder.py_scanstring(s, end, strict=strict, b=b)

def pymakescanner(context):
    return json.scanner.py_make_scanner(context)

def main():
    return json.tool.main()

class Jsonencoder:
    def __init__(self, skipkeys=False, ensureascii=True, checkcircular=True, allownan=True,
                 sortkeys=False, indent=None, separators=None, default=None):
        self.encoder = json.encoder.JSONEncoder(skipkeys=skipkeys, ensure_ascii=ensureascii,
                                                check_circular=checkcircular, allow_nan=allownan,
                                                sort_keys=sortkeys, indent=indent,
                                                separators=separators, default=default)
    def encode(self, obj):
        return self.encoder.encode(obj)
    def iterencode(self, obj):
        return self.encoder.iterencode(obj)
    def default(self, obj):
        return self.encoder.default(obj)

class Jsondecodeerror(Exception):
    def __init__(self, msg, doc, pos):
        self.error = json.decoder.JSONDecodeError(msg, doc, pos)
    def __str__(self):
        return str(self.error)

class Jsondecoder:
    def __init__(self, encoding=None, objecthook=None, parsefloat=None, parseint=None,
                 parseconstant=None, strict=True, objectpairshook=None):
        self.decoder = json.decoder.JSONDecoder(encoding=encoding, object_hook=objecthook,
                                                parse_float=parsefloat, parse_int=parseint,
                                                parse_constant=parseconstant, strict=strict,
                                                object_pairs_hook=objectpairshook)
    def decode(self, s):
        return self.decoder.decode(s)
    def rawdecode(self, s, idx=0):
        return self.decoder.raw_decode(s, idx)
    def scanstring(self, s, end, strict=True):
        return self.decoder.scanstring(s, end, strict=strict)
    def parsearray(self, s_and_end, scan_once):
        return self.decoder.JSONArray(s_and_end, scan_once)
    def parseobject(self, s_and_end, scan_once):
        return self.decoder.JSONObject(s_and_end, scan_once)
    def decodeuxxxx(self, s, end):
        return json.decoder._decode_uXXXX(s, end)
    def pyscanstring(self, s, end, strict=True, b='\\'):
        return json.decoder.py_scanstring(s, end, strict=strict, b=b)

class Jsonscanner:
    def __init__(self, context):
        self.scanner = json.scanner.py_make_scanner(context)
    def scan(self, s):
        return self.scanner(s)
    def pymakescanner(self):
        return json.scanner.py_make_scanner(self.scanner)

def walkpackages(path=None, prefix='', onerror=None):
    return pkgutil.walk_packages(path=path, prefix=prefix, onerror=onerror)

def pathof(object):
    return object.__path__

def underscorewrapper(namewithoutunderscore, *args):
    attr = getattr(__, "_" + namewithoutunderscore)
    return attr(*args) if args else attr

def pyround(value, ndigits=None):
    return round(value, ndigits=ndigits)

Beat = librosa.beat
Cache = librosa._cache
Core = librosa.core
Decompose = librosa.decompose
Display = librosa.display
Effects = librosa.effects
Feature = librosa.feature
Filters = librosa.filters
Onset = librosa.onset
Segment = librosa.segment
SequenceModule = librosa.sequence
Util = librosa.util

CacheManagerClass = librosa._cache.CacheManager
DecoratorApply = librosa._cache._decorator_apply
CacheCallable = librosa._cache.Callable
CacheF = librosa._cache._F
CacheCache = librosa._cache.cache
CacheOS = librosa._cache.os

EnsureNotReachable = librosa._typing._ensure_not_reachable
ArrayLike = librosa._typing.ArrayLike
CallableType = librosa._typing.Callable
GeneratorType = librosa._typing.Generator
ListType = librosa._typing.List
LiteralType = librosa._typing.Literal
NeverType = librosa._typing.Never
SequenceType = librosa._typing.Sequence
TupleType = librosa._typing.Tuple
UnionType = librosa._typing.Union
BoolLike = librosa._typing._BoolLike_co
CharLike = librosa._typing._CharLike_co
ComplexLike = librosa._typing._ComplexLike_co
FloatLike = librosa._typing._FloatLike_co
IntLike = librosa._typing._IntLike_co
IterableLike = librosa._typing._IterableLike
ModeKind = librosa._typing._ModeKind
NumberLike = librosa._typing._NumberLike_co
PadMode = librosa._typing._PadMode
PadModeSTFT = librosa._typing._PadModeSTFT
STFTPad = librosa._typing._STFTPad
ScalarLike = librosa._typing._ScalarLike_co
ScalarOrSequence = librosa._typing._ScalarOrSequence
SequenceLike = librosa._typing._SequenceLike
TType = librosa._typing._T
TD64Like = librosa._typing._TD64Like_co
UIntLike = librosa._typing._UIntLike_co
VoidLike = librosa._typing._VoidLike_co
WindowSpec = librosa._typing._WindowSpec
TypingAnnotations = librosa._typing.annotations
Numpy = librosa._typing.np

BeatTracker = librosa.beat.__beat_tracker
LastBeat = librosa.beat.__last_beat
NormalizeOnsets = librosa.beat.__normalize_onsets
BeatTrack = librosa.beat.beat_track
PLP = librosa.beat.plp
BeatOptional = librosa.beat.Optional
BeatTuple = librosa.beat.Tuple
BeatUnion = librosa.beat.Union
BeatFloatLike = librosa.beat._FloatLike_co
BeatCore = librosa.beat.core
BeatNumpy = librosa.beat.np
BeatNumba = librosa.beat.numba
BeatOnset = librosa.beat.onset
BeatScipy = librosa.beat.scipy
BeatUtil = librosa.beat.util

AudioAudioreadLoad = librosa.core.audio.__audioread_load
AudioSoundfileLoad = librosa.core.audio.__soundfile_load
Autocorrelate = librosa.core.audio.autocorrelate
Chirp = librosa.core.audio.chirp
Clicks = librosa.core.audio.clicks
GetDuration = librosa.core.audio.get_duration
GetSamplerate = librosa.core.audio.get_samplerate
LoadAudio = librosa.core.audio.load
LPC = librosa.core.audio.lpc
MuCompress = librosa.core.audio.mu_compress
MuExpand = librosa.core.audio.mu_expand
ResampleAudio = librosa.core.audio.resample
StreamAudio = librosa.core.audio.stream
ToMono = librosa.core.audio.to_mono
Tone = librosa.core.audio.tone
ZeroCrossings = librosa.core.audio.zero_crossings
AudioCallable = librosa.core.audio.Callable
AudioDTypeLike = librosa.core.audio.DTypeLike
AudioGenerator = librosa.core.audio.Generator
AudioOptional = librosa.core.audio.Optional
AudioTuple = librosa.core.audio.Tuple
AudioUnion = librosa.core.audio.Union
AudioFloatLike = librosa.core.audio._FloatLike_co
AudioIntLike = librosa.core.audio._IntLike_co
AudioSequenceLike = librosa.core.audio._SequenceLike
ZCStencil = librosa.core.audio._zc_stencil
ZCWrapper = librosa.core.audio._zc_wrapper
AudioAnnotations = librosa.core.audio.annotations
AudioAudioread = librosa.core.audio.audioread
AudioCache = librosa.core.audio.cache
AudioLazy = librosa.core.audio.lazy
AudioNP = librosa.core.audio.np
AudioOS = librosa.core.audio.os
AudioPathlib = librosa.core.audio.pathlib
AudioResampy = librosa.core.audio.resampy
AudioSamplerate = librosa.core.audio.samplerate
AudioScipy = librosa.core.audio.scipy
AudioSF = librosa.core.audio.sf
AudioSoxr = librosa.core.audio.soxr
AudioUtil = librosa.core.audio.util
AudioWarnings = librosa.core.audio.warnings

CQTResponse = librosa.core.constantq.__cqt_response
EarlyDownsample = librosa.core.constantq.__early_downsample
EarlyDownsampleCount = librosa.core.constantq.__early_downsample_count
ETRelativeBW = librosa.core.constantq.__et_relative_bw
TrimStack = librosa.core.constantq.__trim_stack
VQTFilterFFT = librosa.core.constantq.__vqt_filter_fft
CQT = librosa.core.constantq.cqt
GriffinLimCQT = librosa.core.constantq.griffinlim_cqt
HybridCQT = librosa.core.constantq.hybrid_cqt
ICQT = librosa.core.constantq.icqt
PseudoCQT = librosa.core.constantq.pseudo_cqt
VQT = librosa.core.constantq.vqt
CQTCollection = librosa.core.constantq.Collection
CQTDTypeLike = librosa.core.constantq.DTypeLike
CQTList = librosa.core.constantq.List
CQTOptional = librosa.core.constantq.Optional
CQTUnion = librosa.core.constantq.Union
CQTFloatLike = librosa.core.constantq._FloatLike_co
CQTPadMode = librosa.core.constantq._PadMode
CQTWindowSpec = librosa.core.constantq._WindowSpec
CQTAudio = librosa.core.constantq.audio
CQTCache = librosa.core.constantq.cache
CQTFilters = librosa.core.constantq.filters
CQTNumpy = librosa.core.constantq.np
CQTUtil = librosa.core.constantq.util
CQTWarnings = librosa.core.constantq.warnings

A4ToTuning = librosa.core.convert.A4_to_tuning
AWeighting = librosa.core.convert.A_weighting
BWeighting = librosa.core.convert.B_weighting
CWeighting = librosa.core.convert.C_weighting
DWeighting = librosa.core.convert.D_weighting
ZWeighting = librosa.core.convert.Z_weighting
BlocksToFrames = librosa.core.convert.blocks_to_frames
BlocksToSamples = librosa.core.convert.blocks_to_samples
BlocksToTime = librosa.core.convert.blocks_to_time
CQTFrequencies = librosa.core.convert.cqt_frequencies
FFTFrequencies = librosa.core.convert.fft_frequencies
FourierTempoFrequencies = librosa.core.convert.fourier_tempo_frequencies
FramesToSamples = librosa.core.convert.frames_to_samples
FramesToTime = librosa.core.convert.frames_to_time
FrequencyWeighting = librosa.core.convert.frequency_weighting
HzToFJS = librosa.core.convert.hz_to_fjs
HzToMel = librosa.core.convert.hz_to_mel
HzToMidi = librosa.core.convert.hz_to_midi
HzToNote = librosa.core.convert.hz_to_note
HzToOcts = librosa.core.convert.hz_to_octs
HzToSvaraC = librosa.core.convert.hz_to_svara_c
HzToSvaraH = librosa.core.convert.hz_to_svara_h
MelFrequencies = librosa.core.convert.mel_frequencies
MelToHz = librosa.core.convert.mel_to_hz
MidiToHz = librosa.core.convert.midi_to_hz
MidiToNote = librosa.core.convert.midi_to_note
MidiToSvaraC = librosa.core.convert.midi_to_svara_c
MidiToSvaraH = librosa.core.convert.midi_to_svara_h
MultiFrequencyWeighting = librosa.core.convert.multi_frequency_weighting
NoteToHz = librosa.core.convert.note_to_hz
NoteToMidi = librosa.core.convert.note_to_midi
NoteToSvaraC = librosa.core.convert.note_to_svara_c
NoteToSvaraH = librosa.core.convert.note_to_svara_h
OctsToHz = librosa.core.convert.octs_to_hz
SamplesLike = librosa.core.convert.samples_like
SamplesToFrames = librosa.core.convert.samples_to_frames
SamplesToTime = librosa.core.convert.samples_to_time
TempoFrequencies = librosa.core.convert.tempo_frequencies
TimeToFrames = librosa.core.convert.time_to_frames
TimeToSamples = librosa.core.convert.time_to_samples
TimesLike = librosa.core.convert.times_like
TuningToA4 = librosa.core.convert.tuning_to_A4
ConvertCallable = librosa.core.convert.Callable
ConvertDict = librosa.core.convert.Dict
ConvertIterable = librosa.core.convert.Iterable
ConvertOptional = librosa.core.convert.Optional
ConvertSized = librosa.core.convert.Sized
ConvertUnion = librosa.core.convert.Union
ConvertWeightingFunctions = librosa.core.convert.WEIGHTING_FUNCTIONS
ConvertFloatLike = librosa.core.convert._FloatLike_co
ConvertIntLike = librosa.core.convert._IntLike_co
ConvertIterableLike = librosa.core.convert._IterableLike
ConvertScalarOrSequence = librosa.core.convert._ScalarOrSequence
ConvertSequenceLike = librosa.core.convert._SequenceLike
ConvertAnnotations = librosa.core.convert.annotations
ConvertNotation = librosa.core.convert.notation
ConvertNumpy = librosa.core.convert.np

GetFFTLib = librosa.core.fft.get_fftlib
SetFFTLib = librosa.core.fft.set_fftlib
FFTOptional = librosa.core.fft.Optional
FFTScipy = librosa.core.fft.scipy

F0Harmonics = librosa.core.harmonic.f0_harmonics
InterpHarmonics = librosa.core.harmonic.interp_harmonics
Salience = librosa.core.harmonic.salience
HarmonicArrayLike = librosa.core.harmonic.ArrayLike
HarmonicCallable = librosa.core.harmonic.Callable
HarmonicOptional = librosa.core.harmonic.Optional
HarmonicSequence = librosa.core.harmonic.Sequence
HarmonicNP = librosa.core.harmonic.np
HarmonicScipy = librosa.core.harmonic.scipy
HarmonicWarnings = librosa.core.harmonic.warnings

HarmonicDistance = librosa.core.intervals.__harmonic_distance
CrystalTieBreak = librosa.core.intervals._crystal_tie_break
IntervalFrequencies = librosa.core.intervals.interval_frequencies
PLimitIntervals = librosa.core.intervals.plimit_intervals
PythagoreanIntervals = librosa.core.intervals.pythagorean_intervals
IntervalsArrayLike = librosa.core.intervals.ArrayLike
IntervalsCollection = librosa.core.intervals.Collection
IntervalsDict = librosa.core.intervals.Dict
IntervalsConstant = librosa.core.intervals.INTERVALS
IntervalsIterable = librosa.core.intervals.Iterable
IntervalsList = librosa.core.intervals.List
IntervalsLiteral = librosa.core.intervals.Literal
IntervalsUnion = librosa.core.intervals.Union
IntervalsFloatLike = librosa.core.intervals._FloatLike_co
IntervalsFDesc = librosa.core.intervals._fdesc
IntervalsCache = librosa.core.intervals.cache
IntervalsImsgpack = librosa.core.intervals.imsgpack
IntervalsMsgpack = librosa.core.intervals.msgpack
IntervalsNP = librosa.core.intervals.np

ModeToKey = librosa.core.notation.__mode_to_key
NoteToDegree = librosa.core.notation.__note_to_degree
SimplifyNote = librosa.core.notation.__simplify_note
FifthsToNote = librosa.core.notation.fifths_to_note
IntervalToFJS = librosa.core.notation.interval_to_fjs
KeyToDegrees = librosa.core.notation.key_to_degrees
KeyToNotes = librosa.core.notation.key_to_notes
ListMela = librosa.core.notation.list_mela
ListThaat = librosa.core.notation.list_thaat
MelaToDegrees = librosa.core.notation.mela_to_degrees
MelaToSvara = librosa.core.notation.mela_to_svara
ThaatToDegrees = librosa.core.notation.thaat_to_degrees
NotationACCMap = librosa.core.notation.ACC_MAP
NotationDict = librosa.core.notation.Dict
NotationIntervals = librosa.core.notation.INTERVALS
NotationIterable = librosa.core.notation.Iterable
NotationKEYRE = librosa.core.notation.KEY_RE
NotationList = librosa.core.notation.List
NotationMajorDict = librosa.core.notation.MAJOR_DICT
NotationMelakartaMap = librosa.core.notation.MELAKARTA_MAP
NotationNoteRE = librosa.core.notation.NOTE_RE
NotationOffsetDict = librosa.core.notation.OFFSET_DICT
NotationSubTrans = librosa.core.notation.SUB_TRANS
NotationSuperTrans = librosa.core.notation.SUPER_TRANS
NotationThaatMap = librosa.core.notation.THAAT_MAP
NotationFloatLike = librosa.core.notation._FloatLike_co
NotationIterableLike = librosa.core.notation._IterableLike
NotationScalarOrSequence = librosa.core.notation._ScalarOrSequence
NotationSequenceLike = librosa.core.notation._SequenceLike
NotationCache = librosa.core.notation.cache
NotationNP = librosa.core.notation.np
NotationRE = librosa.core.notation.re

CheckYinParams = librosa.core.pitch.__check_yin_params
PyinHelper = librosa.core.pitch.__pyin_helper
CumulativeMeanNormalizedDifference = librosa.core.pitch._cumulative_mean_normalized_difference
ParabolicInterpolation = librosa.core.pitch._parabolic_interpolation
EstimateTuning = librosa.core.pitch.estimate_tuning
Piptrack = librosa.core.pitch.piptrack
PitchTuning = librosa.core.pitch.pitch_tuning
Pyin = librosa.core.pitch.pyin
Yin = librosa.core.pitch.yin
PitchArrayLike = librosa.core.pitch.ArrayLike
PitchCallable = librosa.core.pitch.Callable
PitchOptional = librosa.core.pitch.Optional
PitchTuple = librosa.core.pitch.Tuple
PitchUnion = librosa.core.pitch.Union
PitchPadMode = librosa.core.pitch._PadMode
PitchPadModeSTFT = librosa.core.pitch._PadModeSTFT
PitchWindowSpec = librosa.core.pitch._WindowSpec
PiStencil = librosa.core.pitch._pi_stencil
PiWrapper = librosa.core.pitch._pi_wrapper
PitchAudio = librosa.core.pitch.audio
PitchCache = librosa.core.pitch.cache
PitchConvert = librosa.core.pitch.convert
PitchNP = librosa.core.pitch.np
PitchNumba = librosa.core.pitch.numba
PitchScipy = librosa.core.pitch.scipy
PitchSequence = librosa.core.pitch.sequence
PitchUtil = librosa.core.pitch.util
PitchWarnings = librosa.core.pitch.warnings

ReassignFrequencies = librosa.core.spectrum.__reassign_frequencies
ReassignTimes = librosa.core.spectrum.__reassign_times
Spectrogram = librosa.core.spectrum._spectrogram
AmplitudeToDB = librosa.core.spectrum.amplitude_to_db
DBToAmplitude = librosa.core.spectrum.db_to_amplitude
DBToPower = librosa.core.spectrum.db_to_power
FMT = librosa.core.spectrum.fmt
GriffinLimSpectrum = librosa.core.spectrum.griffinlim
IIRT = librosa.core.spectrum.iirt
ISTFT = librosa.core.spectrum.istft
MagPhase = librosa.core.spectrum.magphase
PCEN = librosa.core.spectrum.pcen
PerceptualWeighting = librosa.core.spectrum.perceptual_weighting
PhaseVocoder = librosa.core.spectrum.phase_vocoder
PowerToDB = librosa.core.spectrum.power_to_db
ReassignedSpectrogram = librosa.core.spectrum.reassigned_spectrogram
STFT = librosa.core.spectrum.stft
SpectrumCallable = librosa.core.spectrum.Callable
SpectrumDTypeLike = librosa.core.spectrum.DTypeLike
SpectrumList = librosa.core.spectrum.List
SpectrumLiteral = librosa.core.spectrum.Literal
SpectrumOptional = librosa.core.spectrum.Optional
SpectrumTuple = librosa.core.spectrum.Tuple
SpectrumUnion = librosa.core.spectrum.Union
SpectrumComplexLike = librosa.core.spectrum._ComplexLike_co
SpectrumFloatLike = librosa.core.spectrum._FloatLike_co
SpectrumPadMode = librosa.core.spectrum._PadMode
SpectrumPadModeSTFT = librosa.core.spectrum._PadModeSTFT
SpectrumScalarOrSequence = librosa.core.spectrum._ScalarOrSequence
SpectrumSequenceLike = librosa.core.spectrum._SequenceLike
SpectrumWindowSpec = librosa.core.spectrum._WindowSpec
SpectrumAnnotations = librosa.core.spectrum.annotations
SpectrumCache = librosa.core.spectrum.cache
SpectrumConvert = librosa.core.spectrum.convert
SpectrumNP = librosa.core.spectrum.np
SpectrumScipy = librosa.core.spectrum.scipy
SpectrumUtil = librosa.core.spectrum.util
SpectrumWarnings = librosa.core.spectrum.warnings

NNFilterHelper = librosa.decompose.__nn_filter_helper
DecomposeFunc = librosa.decompose.decompose
HPSS = librosa.decompose.hpss
NNFilter = librosa.decompose.nn_filter
DecomposeCallable = librosa.decompose.Callable
DecomposeList = librosa.decompose.List
DecomposeOptional = librosa.decompose.Optional
DecomposeTuple = librosa.decompose.Tuple
DecomposeUnion = librosa.decompose.Union
DecomposeFloatLike = librosa.decompose._FloatLike_co
DecomposeIntLike = librosa.decompose._IntLike_co
DecomposeCache = librosa.decompose.cache
DecomposeCore = librosa.decompose.core
DecomposeNP = librosa.decompose.np
DecomposeScipy = librosa.decompose.scipy
DecomposeSegment = librosa.decompose.segment
DecomposeSklearn = librosa.decompose.sklearn
DecomposeUtil = librosa.decompose.util

AdaptiveWaveplot = librosa.display.AdaptiveWaveplot
ChromaFJSFormatter = librosa.display.ChromaFJSFormatter
ChromaFormatter = librosa.display.ChromaFormatter
ChromaSvaraFormatter = librosa.display.ChromaSvaraFormatter
FJSFormatter = librosa.display.FJSFormatter
LogHzFormatter = librosa.display.LogHzFormatter
NoteFormatter = librosa.display.NoteFormatter
SvaraFormatter = librosa.display.SvaraFormatter
TimeFormatter = librosa.display.TimeFormatter
TonnetzFormatter = librosa.display.TonnetzFormatter
CheckAxes = librosa.display.__check_axes
CoordChroma = librosa.display.__coord_chroma
CoordCQTHz = librosa.display.__coord_cqt_hz
CoordFFTHz = librosa.display.__coord_fft_hz
CoordFourierTempo = librosa.display.__coord_fourier_tempo
CoordMelHz = librosa.display.__coord_mel_hz
CoordN = librosa.display.__coord_n
CoordTempo = librosa.display.__coord_tempo
CoordTime = librosa.display.__coord_time
CoordVQTHz = librosa.display.__coord_vqt_hz
DecorateAxis = librosa.display.__decorate_axis
Envelope = librosa.display.__envelope
MeshCoords = librosa.display.__mesh_coords
SameAxes = librosa.display.__same_axes
ScaleAxes = librosa.display.__scale_axes
SetCurrentImage = librosa.display.__set_current_image
Cmap = librosa.display.cmap
Specshow = librosa.display.specshow
Waveshow = librosa.display.waveshow
DisplayCallable = librosa.display.Callable
DisplayCollection = librosa.display.Collection
DisplayDict = librosa.display.Dict
DisplayOptional = librosa.display.Optional
DisplayTypeChecking = librosa.display.TYPE_CHECKING
DisplayUnion = librosa.display.Union
AxisCompat = librosa.display._AXIS_COMPAT
DisplayFloatLike = librosa.display._FloatLike_co
ChromaAxisTypes = librosa.display._chroma_ax_types
CQTAxisTypes = librosa.display._cqt_ax_types
FreqAxisTypes = librosa.display._freq_ax_types
LagAxisTypes = librosa.display._lag_ax_types
MiscAxisTypes = librosa.display._misc_ax_types
TimeAxisTypes = librosa.display._time_ax_types
DisplayAnnotations = librosa.display.annotations
DisplayCore = librosa.display.core
DisplayMCM = librosa.display.mcm
DisplayMPLAxes = librosa.display.mplaxes
DisplayMPLTicker = librosa.display.mplticker
DisplayNP = librosa.display.np
DisplayPLT = librosa.display.plt
DisplayUtil = librosa.display.util
DisplayWarnings = librosa.display.warnings

SignalToFrameNonsilent = librosa.effects._signal_to_frame_nonsilent
Deemphasis = librosa.effects.deemphasis
HarmonicEffect = librosa.effects.harmonic
HPSS = librosa.effects.hpss
Percussive = librosa.effects.percussive
PitchShift = librosa.effects.pitch_shift
Preemphasis = librosa.effects.preemphasis
Remix = librosa.effects.remix
Split = librosa.effects.split
TimeStretch = librosa.effects.time_stretch
Trim = librosa.effects.trim
EffectsArrayLike = librosa.effects.ArrayLike
EffectsCallable = librosa.effects.Callable
EffectsIterable = librosa.effects.Iterable
EffectsList = librosa.effects.List
EffectsLiteral = librosa.effects.Literal
EffectsOptional = librosa.effects.Optional
EffectsTuple = librosa.effects.Tuple
EffectsUnion = librosa.effects.Union
EffectsFloatLike = librosa.effects._FloatLike_co
EffectsIntLike = librosa.effects._IntLike_co
EffectsPadModeSTFT = librosa.effects._PadModeSTFT
EffectsWindowSpec = librosa.effects._WindowSpec
EffectsCore = librosa.effects.core
EffectsDecompose = librosa.effects.decompose
EffectsFeature = librosa.effects.feature
EffectsNP = librosa.effects.np
EffectsScipy = librosa.effects.scipy
EffectsUtil = librosa.effects.util

FeatureInverseMelToAudio = librosa.feature.inverse.mel_to_audio
FeatureInverseMelToSTFT = librosa.feature.inverse.mel_to_stft
FeatureInverseMFCCToAudio = librosa.feature.inverse.mfcc_to_audio
FeatureInverseMFCCToMel = librosa.feature.inverse.mfcc_to_mel
FeatureInverseDTypeLike = librosa.feature.inverse.DTypeLike
FeatureInverseOptional = librosa.feature.inverse.Optional
FeatureInversePadModeSTFT = librosa.feature.inverse._PadModeSTFT
FeatureInverseWindowSpec = librosa.feature.inverse._WindowSpec
FeatureInverseFilters = librosa.feature.inverse.filters
FeatureInverseNP = librosa.feature.inverse.np
FeatureInverseWarnings = librosa.feature.inverse.warnings

FourierTempogram = librosa.feature.rhythm.fourier_tempogram
TempoFeature = librosa.feature.rhythm.tempo
Tempogram = librosa.feature.rhythm.tempogram
TempogramRatio = librosa.feature.rhythm.tempogram_ratio
RhythmCallable = librosa.feature.rhythm.Callable
RhythmOptional = librosa.feature.rhythm.Optional
RhythmWindowSpec = librosa.feature.rhythm._WindowSpec
RhythmCache = librosa.feature.rhythm.cache
RhythmNP = librosa.feature.rhythm.np
RhythmScipy = librosa.feature.rhythm.scipy
RhythmUtil = librosa.feature.rhythm.util

ChromaCENS = librosa.feature.spectral.chroma_cens
ChromaCQT = librosa.feature.spectral.chroma_cqt
ChromaSTFT = librosa.feature.spectral.chroma_stft
ChromaVQT = librosa.feature.spectral.chroma_vqt
MelSpectrogram = librosa.feature.spectral.melspectrogram
MFCC = librosa.feature.spectral.mfcc
PolyFeatures = librosa.feature.spectral.poly_features
RMS = librosa.feature.spectral.rms
SpectralBandwidth = librosa.feature.spectral.spectral_bandwidth
SpectralCentroid = librosa.feature.spectral.spectral_centroid
SpectralContrast = librosa.feature.spectral.spectral_contrast
SpectralFlatness = librosa.feature.spectral.spectral_flatness
SpectralRolloff = librosa.feature.spectral.spectral_rolloff
Tonnetz = librosa.feature.spectral.tonnetz
ZeroCrossingRate = librosa.feature.spectral.zero_crossing_rate
SpectralCollection = librosa.feature.spectral.Collection
SpectralDTypeLike = librosa.feature.spectral.DTypeLike
SpectralLiteral = librosa.feature.spectral.Literal
SpectralOptional = librosa.feature.spectral.Optional
SpectralUnion = librosa.feature.spectral.Union
SpectralFloatLike = librosa.feature.spectral._FloatLike_co
SpectralPadMode = librosa.feature.spectral._PadMode
SpectralPadModeSTFT = librosa.feature.spectral._PadModeSTFT
SpectralWindowSpec = librosa.feature.spectral._WindowSpec
SpectralFilters = librosa.feature.spectral.filters
SpectralNP = librosa.feature.spectral.np
SpectralScipy = librosa.feature.spectral.scipy
SpectralUtil = librosa.feature.spectral.util

Delta = librosa.feature.utils.delta
StackMemory = librosa.feature.utils.stack_memory
FeatureUtilsCache = librosa.feature.utils.cache
FeatureUtilsNP = librosa.feature.utils.np
FeatureUtilsScipy = librosa.feature.utils.scipy

FloatWindow = librosa.filters.__float_window
MultirateFB = librosa.filters._multirate_fb
RelativeBandwidth = librosa.filters._relative_bandwidth
ChromaFilter = librosa.filters.chroma
ConstantQ = librosa.filters.constant_q
ConstantQLengths = librosa.filters.constant_q_lengths
CQToChroma = librosa.filters.cq_to_chroma
DiagonalFilter = librosa.filters.diagonal_filter
GetWindow = librosa.filters.get_window
MelFilter = librosa.filters.mel
MRFrequencies = librosa.filters.mr_frequencies
SemitoneFilterbank = librosa.filters.semitone_filterbank
WaveletFilter = librosa.filters.wavelet
WaveletLengths = librosa.filters.wavelet_lengths
WindowBandwidth = librosa.filters.window_bandwidth
WindowSumSquare = librosa.filters.window_sumsquare
FiltersArrayLike = librosa.filters.ArrayLike
FiltersDTypeLike = librosa.filters.DTypeLike
FiltersList = librosa.filters.List
FiltersLiteral = librosa.filters.Literal
FiltersOptional = librosa.filters.Optional
FiltersTuple = librosa.filters.Tuple
FiltersUnion = librosa.filters.Union
FiltersWindowBandwidths = librosa.filters.WINDOW_BANDWIDTHS
FiltersFloatLike = librosa.filters._FloatLike_co
FiltersWindowSpec = librosa.filters._WindowSpec
FiltersCache = librosa.filters.cache
FiltersNP = librosa.filters.np
FiltersScipy = librosa.filters.scipy
FiltersUtil = librosa.filters.util
FiltersWarnings = librosa.filters.warnings

OnsetBacktrack = librosa.onset.onset_backtrack
OnsetDetect = librosa.onset.onset_detect
OnsetStrength = librosa.onset.onset_strength
OnsetStrengthMulti = librosa.onset.onset_strength_multi
OnsetCallable = librosa.onset.Callable
OnsetOptional = librosa.onset.Optional
OnsetSequence = librosa.onset.Sequence
OnsetUnion = librosa.onset.Union
OnsetCache = librosa.onset.cache
OnsetCore = librosa.onset.core
OnsetNP = librosa.onset.np
OnsetScipy = librosa.onset.scipy
OnsetUtil = librosa.onset.util

AffinityBandwidth = librosa.segment.__affinity_bandwidth
Agglomerative = librosa.segment.agglomerative
CrossSimilarity = librosa.segment.cross_similarity
LagToRecurrence = librosa.segment.lag_to_recurrence
PathEnhance = librosa.segment.path_enhance
RecurrenceMatrix = librosa.segment.recurrence_matrix
RecurrenceToLag = librosa.segment.recurrence_to_lag
Subsegment = librosa.segment.subsegment
TimeLagFilter = librosa.segment.timelag_filter
SegmentCallable = librosa.segment.Callable
SegmentLiteral = librosa.segment.Literal
SegmentOptional = librosa.segment.Optional
SegmentUnion = librosa.segment.Union
SegmentArrayOrSparseMatrix = librosa.segment._ArrayOrSparseMatrix
SegmentF = librosa.segment._F
SegmentFloatLike = librosa.segment._FloatLike_co
SegmentWindowSpec = librosa.segment._WindowSpec
SegmentCache = librosa.segment.cache
SegmentNP = librosa.segment.np
SegmentScipy = librosa.segment.scipy
SegmentSklearn = librosa.segment.sklearn
SegmentUtil = librosa.segment.util

RQABacktrack = librosa.sequence.__rqa_backtrack
DTW = librosa.sequence.dtw
DTWBacktracking = librosa.sequence.dtw_backtracking
RQA = librosa.sequence.rqa
TransitionCycle = librosa.sequence.transition_cycle
TransitionLocal = librosa.sequence.transition_local
TransitionLoop = librosa.sequence.transition_loop
TransitionUniform = librosa.sequence.transition_uniform
Viterbi = librosa.sequence.viterbi
ViterbiBinary = librosa.sequence.viterbi_binary
ViterbiDiscriminative = librosa.sequence.viterbi_discriminative
SequenceIterable = librosa.sequence.Iterable
SequenceList = librosa.sequence.List
SequenceLiteral = librosa.sequence.Literal
SequenceOptional = librosa.sequence.Optional
SequenceTuple = librosa.sequence.Tuple
SequenceUnion = librosa.sequence.Union
SequenceWindowSpec = librosa.sequence._WindowSpec
SequenceViterbi = librosa.sequence._viterbi
SequenceAnnotations = librosa.sequence.annotations
SequenceNP = librosa.sequence.np

MaxMemBlock = librosa.util.MAX_MEM_BLOCK
Decorators = librosa.util.decorators
Exceptions = librosa.util.exceptions

NNLSLbfgsBlock = librosa.util._nnls._nnls_lbfgs_block
NNLSObj = librosa.util._nnls._nnls_obj
NNLS = librosa.util._nnls.nnls
NNLSMaxMemBlock = librosa.util._nnls.MAX_MEM_BLOCK
NNLSOptional = librosa.util._nnls.Optional
NNLSSequence = librosa.util._nnls.Sequence
NNLSTuple = librosa.util._nnls.Tuple
NNLSNP = librosa.util._nnls.np
NNLSScipy = librosa.util._nnls.scipy

Deprecated = librosa.util.deprecation.Deprecated
RenameKW = librosa.util.deprecation.rename_kw
DeprecationInspect = librosa.util.deprecation.inspect
DeprecationWarnings = librosa.util.deprecation.warnings

LibrosaError = librosa.util.exceptions.LibrosaError
ParameterError = librosa.util.exceptions.ParameterError

GetFiles = librosa.util.files.__get_files
ResourceFile = librosa.util.files._resource_file
Cite = librosa.util.files.cite
Ex = librosa.util.files.ex
Example = librosa.util.files.example
ExampleInfo = librosa.util.files.example_info
FindFiles = librosa.util.files.find_files
ListExamples = librosa.util.files.list_examples
FilesList = librosa.util.files.List
FilesOptional = librosa.util.files.Optional
FilesSet = librosa.util.files.Set
FilesUnion = librosa.util.files.Union
FilesFdesc = librosa.util.files._fdesc
FilesAnnotations = librosa.util.files.annotations
FilesContextlib = librosa.util.files.contextlib
FilesGlob = librosa.util.files.glob
FilesIndex = librosa.util.files.index
FilesJSON = librosa.util.files.json
FilesLibrosaVersion = librosa.util.files.librosa_version
FilesMsgpack = librosa.util.files.msgpack
FilesOS = librosa.util.files.os
FilesPooch = librosa.util.files.pooch
FilesReg = librosa.util.files.reg
FilesResources = librosa.util.files.resources
FilesSys = librosa.util.files.sys

MatchEvents = librosa.util.matching.match_events
MatchIntervals = librosa.util.matching.match_intervals
MatchingSequenceLike = librosa.util.matching._SequenceLike
MatchingNP = librosa.util.matching.np
MatchingNumba = librosa.util.matching.numba

ShearSparse = librosa.util.utils.__shear_sparse
Abs2 = librosa.util.utils.abs2
AxisSort = librosa.util.utils.axis_sort
BufToFloat = librosa.util.utils.buf_to_float
CountUnique = librosa.util.utils.count_unique
CyclicGradient = librosa.util.utils.cyclic_gradient
DtypeC2R = librosa.util.utils.dtype_c2r
DtypeR2C = librosa.util.utils.dtype_r2c
ExpandTo = librosa.util.utils.expand_to
FillOffDiagonal = librosa.util.utils.fill_off_diagonal
FixFrames = librosa.util.utils.fix_frames
FixLength = librosa.util.utils.fix_length
Frame = librosa.util.utils.frame
IndexToSlice = librosa.util.utils.index_to_slice
IsPositiveInt = librosa.util.utils.is_positive_int
IsUnique = librosa.util.utils.is_unique
LocalMax = librosa.util.utils.localmax
LocalMin = librosa.util.utils.localmin
Normalize = librosa.util.utils.normalize
PadCenter = librosa.util.utils.pad_center
PeakPick = librosa.util.utils.peak_pick
Phasor = librosa.util.utils.phasor
Shear = librosa.util.utils.shear
Softmask = librosa.util.utils.softmask
SparsifyRows = librosa.util.utils.sparsify_rows
Stack = librosa.util.utils.stack
Sync = librosa.util.utils.sync
Tiny = librosa.util.utils.tiny
ValidAudio = librosa.util.utils.valid_audio
ValidInt = librosa.util.utils.valid_int
ValidIntervals = librosa.util.utils.valid_intervals
UtilsCallable = librosa.util.utils.Callable
UtilsDTypeLike = librosa.util.utils.DTypeLike
UtilsDict = librosa.util.utils.Dict
UtilsList = librosa.util.utils.List
UtilsLiteral = librosa.util.utils.Literal
UtilsMaxMemBlock = librosa.util.utils.MAX_MEM_BLOCK
UtilsOptional = librosa.util.utils.Optional
UtilsSequence = librosa.util.utils.Sequence
UtilsTuple = librosa.util.utils.Tuple
UtilsUnion = librosa.util.utils.Union
UtilsArrayOrSparseMatrix = librosa.util.utils._ArrayOrSparseMatrix
UtilsComplexLike = librosa.util.utils._ComplexLike_co
UtilsFloatLike = librosa.util.utils._FloatLike_co
UtilsNumber = librosa.util.utils._Number
UtilsNumberOrArray = librosa.util.utils._NumberOrArray
UtilsReal = librosa.util.utils._Real
UtilsSequenceLike = librosa.util.utils._SequenceLike
UtilsCabs2 = librosa.util.utils._cabs2
UtilsLocalMax = librosa.util.utils._localmax
UtilsLocalMaxStencil = librosa.util.utils._localmax_sten
UtilsLocalMin = librosa.util.utils._localmin
UtilsLocalMinStencil = librosa.util.utils._localmin_sten
UtilsPhasorAngles = librosa.util.utils._phasor_angles
UtilsAnnotations = librosa.util.utils.annotations
UtilsCache = librosa.util.utils.cache
UtilsNP = librosa.util.utils.np
UtilsNumba = librosa.util.utils.numba
UtilsScipy = librosa.util.utils.scipy

GetModVersion = librosa.version.__get_mod_version
ShowVersions = librosa.version.show_versions
VersionImportlib = librosa.version.importlib
VersionShort = librosa.version.short_version
VersionSys = librosa.version.sys
VersionFull = librosa.version.version

Autocorrelate = librosa.core.audio.autocorrelate
Chirp = librosa.core.audio.chirp
Clicks = librosa.core.audio.clicks
GetDuration = librosa.core.audio.get_duration
GetSamplerate = librosa.core.audio.get_samplerate
LoadAudio = librosa.core.audio.load
LPC = librosa.core.audio.lpc
MuCompress = librosa.core.audio.mu_compress
MuExpand = librosa.core.audio.mu_expand
ResampleAudio = librosa.core.audio.resample
StreamAudio = librosa.core.audio.stream
ToMono = librosa.core.audio.to_mono
Tone = librosa.core.audio.tone
ZeroCrossings = librosa.core.audio.zero_crossings

def loadaudio(path, sr=22050, mono=True, offset=0.0, duration=None, dtype=np.float32, res_type="kaiser_best"):
    return librosa.load(path, sr=sr, mono=mono, offset=offset, duration=duration, dtype=dtype, res_type=res_type)

def resampleaudio(y, orig_sr, target_sr, res_type="kaiser_best", fix=True, scale=False):
    return librosa.resample(y, orig_sr, target_sr, res_type=res_type, fix=fix, scale=scale)

def getduration(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, center=True):
    return librosa.get_duration(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, center=center)

def tomono(y):
    return librosa.to_mono(y)

def stftaudio(y, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, dtype=np.complex64, pad_mode="reflect"):
    return librosa.stft(y, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, dtype=dtype, pad_mode=pad_mode)

def istftaudio(D, hop_length=512, win_length=None, window="hann", center=True, dtype=np.float32, length=None):
    return librosa.istft(D, hop_length=hop_length, win_length=win_length, window=window, center=center, dtype=dtype, length=length)

def amplitudetodb(S, ref=1.0, amin=1e-10, top_db=80.0):
    return librosa.amplitude_to_db(S, ref=ref, amin=amin, top_db=top_db)

def powertodb(S, ref=1.0, amin=1e-10, top_db=80.0):
    return librosa.power_to_db(S, ref=ref, amin=amin, top_db=top_db)

def beattrack(y=None, sr=22050, start_bpm=120.0, tightness=100, trim=True, hop_length=512, units="frames"):
    return librosa.beat.beat_track(y=y, sr=sr, start_bpm=start_bpm, tightness=tightness, trim=trim, hop_length=hop_length, units=units)

def plp(y=None, sr=22050, win_length=384, hop_length=512, fmin=150.0, fmax=400.0, ref=None):
    return librosa.beat.plp(y=y, sr=sr, win_length=win_length, hop_length=hop_length, fmin=fmin, fmax=fmax, ref=ref)

def onsetdetect(y=None, sr=22050, onset_envelope=None, hop_length=512, backtrack=False, units="frames"):
    return librosa.onset.onset_detect(y=y, sr=sr, onset_envelope=onset_envelope, hop_length=hop_length, backtrack=backtrack, units=units)

def mfccfeatures(y=None, sr=22050, S=None, n_mfcc=20, dct_type=2, norm="ortho", lifter=0, **kwargs):
    return librosa.feature.mfcc(y=y, sr=sr, S=S, n_mfcc=n_mfcc, dct_type=dct_type, norm=norm, lifter=lifter, **kwargs)

def melspectrogram(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, pad_mode="reflect", power=2.0, **kwargs):
    return librosa.feature.melspectrogram(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, pad_mode=pad_mode, power=power, **kwargs)

def chromastft(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, pad_mode="reflect", tuning=None, norm=2, **kwargs):
    return librosa.feature.chroma_stft(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, pad_mode=pad_mode, tuning=tuning, norm=norm, **kwargs)

def spectralcentroid(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, pad_mode="reflect"):
    return librosa.feature.spectral_centroid(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, pad_mode=pad_mode)

def spectralbandwidth(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, pad_mode="reflect", p=2):
    return librosa.feature.spectral_bandwidth(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, pad_mode=pad_mode, p=p)

def spectralcontrast(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, pad_mode="reflect", fmin=200.0, n_bands=6, quantile=0.02):
    return librosa.feature.spectral_contrast(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, pad_mode=pad_mode, fmin=fmin, n_bands=n_bands, quantile=quantile)

def spectralflatness(y=None, S=None, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, pad_mode="reflect"):
    return librosa.feature.spectral_flatness(y=y, S=S, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, pad_mode=pad_mode)

def spectralrolloff(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, win_length=None, window="hann", center=True, pad_mode="reflect", roll_percent=0.85):
    return librosa.feature.spectral_rolloff(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, win_length=win_length, window=window, center=center, pad_mode=pad_mode, roll_percent=roll_percent)

def zerocrossingrate(y, frame_length=2048, hop_length=512, center=True):
    return librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length, center=center)

def miditohz(notes):
    return librosa.midi_to_hz(notes)

def hztomidi(frequencies):
    return librosa.hz_to_midi(frequencies)

def notetomidi(note):
    return librosa.note_to_midi(note)

def miditonote(midi):
    return librosa.midi_to_note(midi)

def hztomel(frequencies, htk=False):
    return librosa.hz_to_mel(frequencies, htk=htk)

def meltOhz(mels, htk=False):
    return librosa.mel_to_hz(mels, htk=htk)

def cqttransform(y, sr=22050, hop_length=512, fmin=None, n_bins=84, bins_per_octave=12, tuning=0.0, filter_scale=1, pad_mode="reflect", res_type=None):
    return librosa.cqt(y=y, sr=sr, hop_length=hop_length, fmin=fmin, n_bins=n_bins, bins_per_octave=bins_per_octave, tuning=tuning, filter_scale=filter_scale, pad_mode=pad_mode, res_type=res_type)

def icqttransform(C, sr=22050, hop_length=512, fmin=None, bins_per_octave=12, tuning=0.0, filter_scale=1):
    return librosa.icqt(C=C, sr=sr, hop_length=hop_length, fmin=fmin, bins_per_octave=bins_per_octave, tuning=tuning, filter_scale=filter_scale)

def griffinlimspectrogram(S, n_iter=32, hop_length=512, win_length=None, window="hann", center=True, dtype=np.float32, length=None):
    return librosa.griffinlim(S, n_iter=n_iter, hop_length=hop_length, win_length=win_length, window=window, center=center, dtype=dtype, length=length)

def timestringlike(n, sr=22050, hop_length=512):
    return librosa.times_like(n, sr=sr, hop_length=hop_length)

def samplestringlike(n, sr=22050, hop_length=512):
    return librosa.samples_like(n, sr=sr, hop_length=hop_length)

def framestotime(frames, sr=22050, hop_length=512, n_fft=None):
    return librosa.frames_to_time(frames, sr=sr, hop_length=hop_length, n_fft=n_fft)

def timetoframes(times, sr=22050, hop_length=512, n_fft=None):
    return librosa.time_to_frames(times, sr=sr, hop_length=hop_length, n_fft=n_fft)

def framestosamples(frames, hop_length=512):
    return librosa.frames_to_samples(frames, hop_length=hop_length)

def samplestoframes(samples, hop_length=512):
    return librosa.samples_to_frames(samples, hop_length=hop_length)

def pitchyin(y, sr=22050, fmin=50.0, fmax=500.0, frame_length=2048, hop_length=512, trough_threshold=0.1, center=True, pad_mode="reflect"):
    return librosa.yin(y=y, sr=sr, fmin=fmin, fmax=fmax, frame_length=frame_length, hop_length=hop_length, trough_threshold=trough_threshold, center=center, pad_mode=pad_mode)

def pitchpyin(y=None, sr=22050, fmin=50.0, fmax=500.0, hop_length=512, win_length=None, center=True, trough_threshold=0.1, fill_na=None, pad_mode="reflect"):
    return librosa.pyin(y=y, sr=sr, fmin=fmin, fmax=fmax, hop_length=hop_length, win_length=win_length, center=center, trough_threshold=trough_threshold, fill_na=fill_na, pad_mode=pad_mode)

def pitchpiptrack(y=None, sr=22050, S=None, n_fft=2048, hop_length=512, fmin=0.0, fmax=np.inf, threshold=0.75):
    return librosa.piptrack(y=y, sr=sr, S=S, n_fft=n_fft, hop_length=hop_length, fmin=fmin, fmax=fmax, threshold=threshold)

def timestretch(y, rate):
    return librosa.effects.time_stretch(y, rate)

def pitchshift(y, sr, n_steps, bins_per_octave=12):
    return librosa.effects.pitch_shift(y, sr, n_steps, bins_per_octave=bins_per_octave)

def trimaudio(y, top_db=60, ref=None):
    return librosa.effects.trim(y, top_db=top_db, ref=ref)

def hpsseffects(y, kernel_size=(31, 31), power=2.0, mask=False):
    return librosa.decompose.hpss(y, kernel_size=kernel_size, power=power, mask=mask)

def rmsenergy(y=None, S=None, frame_length=2048, hop_length=512, center=True, pad_mode="reflect"):
    return librosa.feature.rms(y=y, S=S, frame_length=frame_length, hop_length=hop_length, center=center, pad_mode=pad_mode)

def chromacqt(y=None, sr=22050, C=None, hop_length=512, fmin=None, n_chroma=12, bins_per_octave=None, tuning=0.0, norm=2, threshold=0.0):
    return librosa.feature.chroma_cqt(y=y, sr=sr, C=C, hop_length=hop_length, fmin=fmin, n_chroma=n_chroma, bins_per_octave=bins_per_octave, tuning=tuning, norm=norm, threshold=threshold)

def chromavqt(y=None, sr=22050, C=None, hop_length=512, fmin=None, n_chroma=12, bins_per_octave=None, tuning=0.0, norm=2, threshold=0.0):
    return librosa.feature.chroma_vqt(y=y, sr=sr, C=C, hop_length=hop_length, fmin=fmin, n_chroma=n_chroma, bins_per_octave=bins_per_octave, tuning=tuning, norm=norm, threshold=threshold)

def deltafeatures(data, width=9, order=1, axis=-1, mode="interp"):
    return librosa.feature.delta(data, width=width, order=order, axis=axis, mode=mode)

def stackmemory(data, n_steps=2, delay=1, index=False):
    return librosa.feature.stack_memory(data, n_steps=n_steps, delay=delay, index=index)

def dtwsequence(X, Y, metric="euclidean", step_sizes_sigma=None, weights_add=0.0, weights_mul=1.0, subseq=False, open_end=False, open_begin=False):
    return librosa.sequence.dtw(X=X, Y=Y, metric=metric, step_sizes_sigma=step_sizes_sigma, weights_add=weights_add, weights_mul=weights_mul, subseq=subseq, open_end=open_end, open_begin=open_begin)

def viterbisequence(X, p_init=None, p_trans=None, p_obs=None, viterbi=False):
    return librosa.sequence.viterbi(X=X, p_init=p_init, p_trans=p_trans, p_obs=p_obs, viterbi=viterbi)

class CacheManager(librosa._cache.CacheManager):
    def __new__(cls, cache=None, max_size=None, policy="lru"):
        return librosa._cache.CacheManager(cache=cache, max_size=max_size, policy=policy)

class AdaptiveWaveplot(librosa.display.AdaptiveWaveplot):
    def __new__(cls, y, sr=22050, max_points=50000, **kwargs):
        return librosa.display.AdaptiveWaveplot(y=y, sr=sr, max_points=max_points, **kwargs)

class ChromaFjsFormatter(librosa.display.ChromaFJSFormatter):
    def __new__(cls, bins_per_octave=12, **kwargs):
        return librosa.display.ChromaFJSFormatter(bins_per_octave=bins_per_octave, **kwargs)

class ChromaFormatter(librosa.display.ChromaFormatter):
    def __new__(cls, bins_per_octave=12, **kwargs):
        return librosa.display.ChromaFormatter(bins_per_octave=bins_per_octave, **kwargs)

class ChromaSvaraFormatter(librosa.display.ChromaSvaraFormatter):
    def __new__(cls, bins_per_octave=12, **kwargs):
        return librosa.display.ChromaSvaraFormatter(bins_per_octave=bins_per_octave, **kwargs)

class FjsFormatter(librosa.display.FJSFormatter):
    def __new__(cls, bins_per_octave=12, **kwargs):
        return librosa.display.FJSFormatter(bins_per_octave=bins_per_octave, **kwargs)

class LogHzFormatter(librosa.display.LogHzFormatter):
    def __new__(cls, sr=22050, n_fft=2048, **kwargs):
        return librosa.display.LogHzFormatter(sr=sr, n_fft=n_fft, **kwargs)

class NoteFormatter(librosa.display.NoteFormatter):
    def __new__(cls, octave=True, **kwargs):
        return librosa.display.NoteFormatter(octave=octave, **kwargs)

class SvaraFormatter(librosa.display.SvaraFormatter):
    def __new__(cls, bins_per_octave=12, **kwargs):
        return librosa.display.SvaraFormatter(bins_per_octave=bins_per_octave, **kwargs)

class TimeFormatter(librosa.display.TimeFormatter):
    def __new__(cls, sr=22050, hop_length=512, **kwargs):
        return librosa.display.TimeFormatter(sr=sr, hop_length=hop_length, **kwargs)

class TonnetzFormatter(librosa.display.TonnetzFormatter):
    def __new__(cls, **kwargs):
        return librosa.display.TonnetzFormatter(**kwargs)

class Deprecated(librosa.util.deprecation.Deprecated):
    def __new__(cls, name, alternative=None, version=None):
        return librosa.util.deprecation.Deprecated(name=name, alternative=alternative, version=version)

class LibrosaError(librosa.util.exceptions.LibrosaError):
    def __new__(cls, message=""):
        return librosa.util.exceptions.LibrosaError(message)

class ParameterError(librosa.util.exceptions.ParameterError):
    def __new__(cls, message=""):
        return librosa.util.exceptions.ParameterError(message)

def allof(object):
    return object.__all__

class Pen(turtle.Pen):
    def __new__(cls):
        return turtle.Pen()

class RawPen(turtle.RawPen):
    def __new__(cls, canvas):
        return turtle.RawPen(canvas)

class RawTurtle(turtle.RawTurtle):
    def __new__(cls, canvas, shape="classic", undobuffersize=1000, visible=True):
        return turtle.RawTurtle(canvas=canvas, shape=shape, undobuffersize=undobuffersize, visible=visible)

class ScrolledCanvas(turtle.ScrolledCanvas):
    def __new__(cls, master=None, width=500, height=350, canvwidth=600, canvheight=500):
        return turtle.ScrolledCanvas(master=master, width=width, height=height,
                                     canvwidth=canvwidth, canvheight=canvheight)

class Shape(turtle.Shape):
    def __new__(cls, type_, data=None):
        return turtle.Shape(type_, data)

class TNavigator(turtle.TNavigator):
    def __new__(cls):
        return turtle.TNavigator()

class TPen(turtle.TPen):
    def __new__(cls):
        return turtle.TPen()

class Tbuffer(turtle.Tbuffer):
    def __new__(cls, size=1000):
        return turtle.Tbuffer(size)

class Terminator(turtle.Terminator):
    def __new__(cls):
        return turtle.Terminator()

class Turtle(turtle.Turtle):
    def __new__(cls, shape="classic", undobuffersize=1000, visible=True):
        return turtle.Turtle(shape=shape, undobuffersize=undobuffersize, visible=visible)

class TurtleGraphicsError(turtle.TurtleGraphicsError):
    def __new__(cls, *args):
        return turtle.TurtleGraphicsError(*args)

class TurtleScreen(turtle.TurtleScreen):
    def __new__(cls, cv):
        return turtle.TurtleScreen(cv)

class TurtleScreenBase(turtle.TurtleScreenBase):
    def __new__(cls, cv):
        return turtle.TurtleScreenBase(cv)

class Vec2D(turtle.Vec2D):
    def __new__(cls, x, y):
        return turtle.Vec2D(x, y)

class Root(turtle._Root):
    def __new__(cls):
        return turtle._Root()

class Screen(turtle._Screen):
    def __new__(cls):
        return turtle._Screen()

class TurtleImage(turtle._TurtleImage):
    def __new__(cls, name, data):
        return turtle._TurtleImage(name, data)

def forward(distance):
    return turtle.forward(distance)

def backward(distance):
    return turtle.backward(distance)

def left(angle):
    return turtle.left(angle)

def right(angle):
    return turtle.right(angle)

def circle(radius, extent=None, steps=None):
    return turtle.circle(radius, extent=extent, steps=steps)

def goto(x, y=None):
    return turtle.goto(x, y)

def dot(size=None, *color):
    return turtle.dot(size, *color)

def writeintodrawing(arg, move=False, align="left", font=("Arial", 8, "normal")):
    return turtle.write(arg, move=move, align=align, font=font)

def bgcolor(*args):
    return turtle.bgcolor(*args)

def setup(width=0.5, height=0.75, startx=None, starty=None):
    return turtle.setup(width=width, height=height, startx=startx, starty=starty)

def exitonclick():
    return turtle.exitonclick()

def speed(speed=None):
    return turtle.speed(speed)

def hideturtle():
    return turtle.hideturtle()

def showturtle():
    return turtle.showturtle()

def pensize(width=None):
    return turtle.pensize(width)

def pencolor(*args):
    return turtle.pencolor(*args)

def fillcolor(*args):
    return turtle.fillcolor(*args)

def beginfill():
    return turtle.begin_fill()

def endfill():
    return turtle.end_fill()

def reset():
    return turtle.reset()

def clear():
    return turtle.clear()

def home():
    return turtle.home()

def position():
    return turtle.position()

def heading():
    return turtle.heading()

def xcor():
    return turtle.xcor()

def ycor():
    return turtle.ycor()

def distance(x, y=None):
    return turtle.distance(x, y)

def towards(x, y=None):
    return turtle.towards(x, y)

def tracer(n=None, delay=None):
    return turtle.tracer(n, delay)

def update():
    return turtle.update()

def listen():
    return turtle.listen()

def onclick(func, btn=1, add=None):
    return turtle.onclick(func, btn=btn, add=add)

def onkey(func, key):
    return turtle.onkey(func, key)

def ontimer(func, t=0):
    return turtle.ontimer(func, t)

def bye():
    return turtle.bye()

def done():
    return turtle.done()

def mainloop():
    return turtle.mainloop()

TK = turtle.TK
CFG = turtle._CFG
LANGUAGE = turtle._LANGUAGE
aliaslist = turtle._alias_list
tgclasses = turtle._tg_classes
tgscreen_functions = turtle._tg_screen_functions
tgturtle_functions = turtle._tg_turtle_functions
tgutilities = turtle._tg_utilities

class NDArray(np.ndarray):
    def __new__(cls, shape, dtype=float, buffer=None, offset=0,
                strides=None, order=None):
        return np.ndarray(shape=shape, dtype=dtype, buffer=buffer,
                          offset=offset, strides=strides, order=order)

    def reshape(self, *shape, order='C'):
        return super().reshape(*shape, order=order)

    def transpose(self, *axes):
        return super().transpose(*axes)

    def sum(self, axis=None, dtype=None, out=None, keepdims=False):
        return super().sum(axis=axis, dtype=dtype, out=out, keepdims=keepdims)

    def mean(self, axis=None, dtype=None, out=None, keepdims=False):
        return super().mean(axis=axis, dtype=dtype, out=out, keepdims=keepdims)

    def dot(self, other):
        return super().dot(other)

    def __matmul__(self, other):
        return super().__matmul__(other)


def inv(a):
    return np.linalg.inv(a)

def pinv(a, rcond=1e-15):
    return np.linalg.pinv(a, rcond=rcond)

def det(a):
    return np.linalg.det(a)

def eig(a):
    return np.linalg.eig(a)

def eigh(a, UPLO='L'):
    return np.linalg.eigh(a, UPLO=UPLO)

def eigvals(a):
    return np.linalg.eigvals(a)

def eigvalsh(a, UPLO='L'):
    return np.linalg.eigvalsh(a, UPLO=UPLO)

def svd(a, full_matrices=True, compute_uv=True, hermitian=False):
    return np.linalg.svd(a, full_matrices=full_matrices,
                         compute_uv=compute_uv, hermitian=hermitian)

def qr(a, mode='reduced'):
    return np.linalg.qr(a, mode=mode)

def cholesky(a):
    return np.linalg.cholesky(a)

def norm(x, ord=None, axis=None, keepdims=False):
    return np.linalg.norm(x, ord=ord, axis=axis, keepdims=keepdims)

def solve(a, b):
    return np.linalg.solve(a, b)

def lstsq(a, b, rcond=None):
    return np.linalg.lstsq(a, b, rcond=rcond)

def matrixpower(a, n):
    return np.linalg.matrix_power(a, n)

def matrixmultiply(a, b, out=None):
    return np.matmul(a, b, out=out)

def businessdaycount(begin, end, weekmask='1111100', holidays=None):
    return np.busday_count(begin, end, weekmask=weekmask, holidays=holidays)

def trapezoidalmath(y, x=None, dx=1.0, axis=-1):
    return np.trapz(y, x=x, dx=dx, axis=axis)

def setprecision(digits=10):
    mpmath.mp.dps = digits

def scientificpi():
    return mpmath.pi

def scientifice():
    return mpmath.e

def lambertwof(z, k=0):
    return lambertw(z, k=k)

def arithmeticgeometricmean(a, b):
    return agm(a, b)

def scientificsqrt(number):
    return mpmath.sqrt(number)

def scientificoperation(operation, number, number2=None):
    if not number2:
        attr = getattr(mpmath, operation)
        return attr(number)
    else:
        attr = getattr(mpmath, operation)
        return attr(number, number2)

def siegeltheta(number):
    return mpmath.siegeltheta(number)

def zeta(number):
    return mpmath.zeta(number)

def broadcastshapes(shape1, shape2):
    return np.broadcast_shapes(shape1, shape2)

def kaiser(number, beta=14):
    return np.kaiser(number, beta=beta)

def averageofarray(array):
    return np.mean(array)

def piecewise(number, ifstatement, elsestatement, taskofif, taskofelse):
    return np.piecewise(number, [ifstatement, elsestatement], [taskofif, taskofelse])

def numberlist(start, stop, num=50, endpoint=True, retstep=False, dtype=None):
    return numpy.linspace(start, stop, num=num, endpoint=endpoint, retstep=retstep, dtype=dtype)

def besselj(order, value):
    return mpmath.besselj(order, value)

def kleinj(number):
    return mpmath.kleinj(number)

def webere(number):
    return mpmath.webere(number)

def arange(number):
    return np.arange(number)

def reshape(array, desiredshape, order=None):
    return np.reshape(array, desiredshape, order=order)

def transpose(array):
    return np.transpose(array)

def riemannr(number):
    return mpmath.riemannr(number)

def polylog(order, number):
    return mpmath.polylog(order, number)

def limitarray(array, minimum, maximum, outputarray=None):
    return np.clip(array, minimum, maximum, out=outputarray)

def hurwitz(order, parameter):
    return mpmath.hurwitz(order, parameter)

def bernoulli(number):
    return mpmath.bernoulli(number)

def sortarray(array, axis=-1, kind="quicksort", order=None):
    return np.sort(array, axis=axis, kind=kind, order=order)

def createnumarray(dtype=None, copy=True, order=None, subok=False, ndmin=0, like=None):
    return numpy.array(object, dtype=dtype, copy=copy, order=order, subok=subok, ndmin=ndmin, like=like)

def asarray(array, dtype=None, order=None, like=None):
    return numpy.asarray(array, dtype=dtype, order=order, like=like)

def scientificapery():
    return mpmath.apery

def scientificnumber(numberlikepi):
    return getattr(mpmath, numberlikepi)

def scientificcatalan():
    return mpmath.catalan

class MainMarkovChain:
    def __init__(self, model, statesize=2):
        self.statesize = statesize
        self.model = model
        self.chain = markovify.chain.Chain(self.model, state_size=self.statesize)

def accumulate(chain, state, nextword):
    return markovify.chain.accumulate(chain, state, nextword)

def compilenext(chain, state):
    return markovify.chain.compile_next(chain, state)

def isabbreviation(word):
    return markovify.splitters.is_abbreviation(word)

def issentenceender(word):
    return markovify.splitters.is_sentence_ender(word)

def splitintosentences(text):
    return markovify.splitters.split_into_sentences(text)

class Text:
    def __init__(self, inputtext, statesize=2, chain=None, parsedsentences=None, retainoriginal=False, wellformed=True):
        self.inputtext = inputtext
        self.statesize = statesize
        self.chain = chain
        self.parsedsentences = parsedsentences
        self.retainoriginal = retainoriginal
        self.wellformed = wellformed
        self.text = markovify.text.Text(self.inputtext, state_size=self.statesize, chain=self.chain, parsed_sentences=self.parsedsentences, retain_original=self.retainoriginal, well_formed=self.wellformed)

class NewlineText:
    def __init__(self, inputtext, statesize=2, chain=None, parsedsentences=None, retainoriginal=False, wellformed=True):
        self.inputtext = inputtext
        self.statesize = statesize
        self.chain = chain
        self.parsedsentences = parsedsentences
        self.retainoriginal = retainoriginal
        self.wellformed = wellformed
        self.newlinetext = markovify.text.NewlineText(self.inputtext, state_size=self.statesize, chain=self.chain, parsed_sentences=self.parsedsentences, retain_original=self.retainoriginal, well_formed=self.wellformed)

class ParameterError(Exception):
    def __init__(self, message="Invalid parameters."):
        super().__init__(message)
        self.error = markovify.text.ParamError(message)

def combine(models, weights=None):
    return markovify.utils.combine(models, weights=weights)

def getmodeldictionary(model):
    return markovify.utils.get_model_dict(model)

mainchain = markovify.chain
mainsplitters = markovify.splitters
maintext = markovify.text
mainutils = markovify.utils
chainbegin = markovify.chain.BEGIN
chainend = markovify.chain.END
chainbisect = markovify.chain.bisect
chaincopy = markovify.chain.copy
chainjson = markovify.chain.json
chainoperator = markovify.chain.operator
chainrandom = markovify.chain.random
chainabbrcapped = markovify.splitters.abbr_capped
chainabbrlowercase = markovify.splitters.abbr_lowercase
chaininitialismpat = markovify.splitters.initialism_pat
chainre = markovify.splitters.re
chainuppercaseletterpat = markovify.splitters.uppercase_letter_pat
chaintextbegin = markovify.text.BEGIN
chaindefaultmaxoverlapratio = markovify.text.DEFAULT_MAX_OVERLAP_RATIO
chaindefaultmaxoverlaptotal = markovify.text.DEFAULT_MAX_OVERLAP_TOTAL
chaindefaulttries = markovify.text.DEFAULT_TRIES
chaintextfunctools = markovify.text.functools
chaintextjson = markovify.text.json
chaintextrandom = markovify.text.random
chaintextre = markovify.text.re

def pyinitializeplussuperparentcall(toinitialize, *args, **kwargs):
    return super().__init__(*args, **kwargs)

def pysuperparentcall():
    return super()

def getenvironmentpath(key, default=None):
    return os.environ.get(key, default=default)

def joinpath(path, *paths):
    return os.path.join(path, *paths)

def underscoredfile():
    return __file__

def pathdirectoryname(path):
    return os.path.dirname(path)

def systempath():
    return sys.path

def systemexecutable():
    return sys.executable

def filterwarnings(task="ignore", message='', warningtype=DeprecationWarning, module='', lineno=0, append=False):
    return warnings.filterwarnings(task, message=message, category=warningtype, module=module, lineno=lineno, append=append)

def setuptoolsfindpackages():
    return find_packages()

def setuptoolssetup(name="", version="", description="", longdescription="", longdescriptioncontenttype="", author="", authoremail="", url="", license="", packages=None, installrequires=None, extrasrequire=None, pythonrequires="", classifiers=None, entrypoints=None, includepackagedata=True):
    return setup(name=name, version=version, description=description, long_description=longdescription, long_description_content_type=longdescriptioncontenttype, author=author, author_email=authoremail, url=url, license=license, packages=packages or find_packages(), install_requires=installrequires or [], extras_require=extrasrequire or {}, python_requires=pythonrequires, classifiers=classifiers or [], entry_points=entrypoints or {}, include_package_data=includepackagedata)

def osenvironment(key):
    return os.environ[key]

def getenvironmentos(key, default=None):
    return os.getenv(ley, default=default)

def putenvironment(key, value):
    return os.putenv(key, value)

def countervalues(counter):
    return counter.values()

def uniqueoccurrences(array):
    counter = Counter(array)
    s = set()
    for v in counter.values():
        if v in s:
            return False
        else:
            s.add(v)
    return True

class AlphaGlassEngine:
    def __init__(self, width, height, radius=28, tint=(255, 255, 255, 100),
                 base_bg=(32, 32, 40, 255), blur=18, parallax_intensity=8):
        self.w = max(32, int(width))
        self.h = max(32, int(height))
        self.radius = int(radius)
        self.tint = tint
        self.base_bg = base_bg
        self.blur = int(blur)
        self.parallax_intensity = float(parallax_intensity)

        self.layers = []
        self.displacement = None
        self.mask = None
        self.result = None
        self.frame = 0

        self.mask = self._rounded_mask(self.w, self.h, self.radius)


    def step(self, mouse_x=None, mouse_y=None, t=None):
        self.frame += 1
        t = time.time() if t is None else t

        px, py = self._parallax(mouse_x, mouse_y)

        base = self._animated_gradients(self.w, self.h, t)

        frosted = base.filter(ImageFilter.GaussianBlur(12))
        frosted = frosted.filter(ImageFilter.GaussianBlur(self.blur))

        disp = self._animated_displacement(self.w, self.h, t)
        displaced = self._apply_displacement(frosted, disp, strength=8)

        tinted = Image.alpha_composite(displaced, Image.new("RGBA", (self.w, self.h), self.tint))

        shifted = self._shift_image(tinted, dx=px, dy=py)

        final = shifted.copy()
        final.putalpha(self.mask)

        self.layers = [base, frosted, displaced, tinted, shifted]
        self.displacement = disp
        self.result = final
        return final

    def _rounded_mask(self, w, h, r):
        mask = Image.new("L", (w, h), 0)
        d = ImageDraw.Draw(mask)
        d.rounded_rectangle((0, 0, w, h), radius=r, fill=255)
        return mask

    def _parallax(self, mx, my):
        if mx is None or my is None or self.w <= 0 or self.h <= 0:
            return 0.0, 0.0
        fx = (mx / max(1, self.w) - 0.5) * self.parallax_intensity
        fy = (my / max(1, self.h) - 0.5) * self.parallax_intensity
        return fx, fy

    def _animated_gradients(self, w, h, t):
        """
        Create multiple animated radial gradients with soft colors.
        """
        img = Image.new("RGBA", (w, h), self.base_bg)
        d = ImageDraw.Draw(img)

        palette = [
            (255, 150, 180, 130),
            (140, 210, 255, 120),
            (190, 255, 210, 110),
            (255, 220, 150, 90)
        ]

        cx = w // 2
        cy = h // 2
        R = min(w, h) // 3

        for idx, col in enumerate(palette):
            angle = t * (0.2 + idx * 0.07)
            ox = int(cx + R * 0.6 * math.cos(angle + idx))
            oy = int(cy + R * 0.5 * math.sin(angle * 0.8 + idx))

            max_r = int(min(w, h) * (0.8 - 0.1 * idx))
            steps = 24
            for i in range(steps):
                a = int(col[3] * (1 - i / steps))
                size = max_r - i * 12
                if size <= 0:
                    break
                x0 = ox - size
                y0 = oy - size
                x1 = ox + size
                y1 = oy + size
                if x1 <= x0 or y1 <= y0:
                    break
                d.ellipse((x0, y0, x1, y1), fill=(col[0], col[1], col[2], a))

        return img

    def _animated_displacement(self, w, h, t):
        disp = Image.new("RGBA", (w, h), (128, 128, 0, 255))
        d = ImageDraw.Draw(disp)

        bands = 5
        for i in range(bands):
            phase = t * (0.7 + i * 0.13)
            y = int(h * (0.2 + 0.15 * i) + 12 * math.sin(phase))
            thickness = 18 + int(6 * math.sin(phase * 0.93))
            strength_x = 12 + int(4 * math.sin(phase * 1.2))
            strength_y = 10 + int(3 * math.cos(phase * 1.1))

            rx = 128 + strength_x
            gx = 128 + strength_y
            d.rectangle((0, max(0, y - thickness), w, min(h, y + thickness)),
                        fill=(rx, gx, 0, 255))
        disp = disp.filter(ImageFilter.GaussianBlur(6))
        return disp

    def _apply_displacement(self, img, disp, strength=8):
        w, h = img.size
        tile = 24
        out = Image.new("RGBA", (w, h))
        src = img

        disp_px = disp.load()
        for ty in range(0, h, tile):
            for tx in range(0, w, tile):
                cx = min(w - 1, tx + tile // 2)
                cy = min(h - 1, ty + tile // 2)
                rx, gx, _, _ = disp_px[cx, cy]
                dx = int((rx - 128) * (strength / 12.0))
                dy = int((gx - 128) * (strength / 12.0))

                box = (tx, ty, min(w, tx + tile), min(h, ty + tile))
                region = src.crop(box)
                out.paste(region, (tx + dx, ty + dy))
        return out.filter(ImageFilter.GaussianBlur(2))

    def _shift_image(self, img, dx=0.0, dy=0.0):
        w, h = img.size
        dx = int(dx)
        dy = int(dy)
        out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        out.paste(img, (dx, dy))
        return out


class AlphaGlassWrapper:
    def __init__(self, root, target_widget, radius=28, tint=(255, 255, 255, 100),
                 blur=18, parallax_intensity=8, fps=30):
        self.root = root
        self.widget = target_widget
        self.fps = max(10, int(fps))

        root.update_idletasks()
        w = max(64, target_widget.winfo_width())
        h = max(64, target_widget.winfo_height())

        self.canvas = tk.Canvas(root, width=w, height=h, highlightthickness=0, bd=0, bg=root["bg"])
        self.canvas.place(in_=target_widget, relx=0, rely=0, x=0, y=0)

        self.engine = LiquidGlassEngine(width=w, height=h, radius=radius, tint=tint,
                                        blur=blur, parallax_intensity=parallax_intensity)

        self.photo = None
        self.mouse_x = None
        self.mouse_y = None
        self.running = False

        self.widget.bind("<Motion>", self._on_motion)
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)

    def start(self):
        self.running = True
        self._tick()

    def stop(self):
        self.running = False

    def _on_motion(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def _on_enter(self, event):
        self.mouse_x = self.widget.winfo_width() // 2
        self.mouse_y = self.widget.winfo_height() // 2

    def _on_leave(self, event):
        self.mouse_x = None
        self.mouse_y = None

    def _tick(self):
        if not self.running:
            return
        frame = self.engine.step(mouse_x=self.mouse_x, mouse_y=self.mouse_y)
        self.photo = ImageTk.PhotoImage(frame)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo, tags=("glass",))
        self.canvas.image_ref = self.photo

        self.widget.lift(self.canvas)

        self.root.after(int(1000 / self.fps), self._tick)


def createglassbg(w, h, blur=16, tint=(255,255,255,110), radius=20, t=None):
    bg = Image.new("RGBA", (w, h), (40,40,50,255))
    d = ImageDraw.Draw(bg)

    colors = [
        (255,120,150,120),
        (120,200,255,120),
        (180,255,200,110)
    ]
    cx, cy = w//2, h//2
    r = min(w,h)//2
    t = time.time() if t is None else t

    for idx, c in enumerate(colors):
        angle = t*(0.3+0.1*idx)
        ox = int(cx + r*0.3*math.cos(angle))
        oy = int(cy + r*0.3*math.sin(angle))
        for i in range(15):
            a = int(c[3]*(1-i/15))
            size = r - i*10
            if size<=0: break
            d.ellipse((ox-size, oy-size, ox+size, oy+size),
                      fill=(c[0],c[1],c[2],a))

    bg = bg.filter(ImageFilter.GaussianBlur(12))
    blur_layer = bg.filter(ImageFilter.GaussianBlur(blur))
    tint_layer = Image.new("RGBA",(w,h),tint)
    result = Image.alpha_composite(blur_layer,tint_layer)

    mask = Image.new("L",(w,h))
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0,0,w,h),radius=radius,fill=255)
    result.putalpha(mask)
    return result

def isspace(variable):
    return variable.isspace()

def safeevaluate(toevaluate):
    if isinstance(toevaluate, (int, float)):
        return toevaluate
    s=text
    i=0
    n=len(s)
    def ws():
        nonlocal i
        while i<n and s[i].isspace():
            i+=1
    def peek():
        return s[i] if i<n else ''
    def consume(c=None):
        nonlocal i
        if c and s[i]!=c:
            raise ValueError("expected "+c)
        ch=s[i]
        i+=1
        return ch
    def readstring():
        q=consume()
        out=[]
        while True:
            if i>=n:
                raise ValueError("string")
            c=consume()
            if c==q:
                return "".join(out)
            if c=="\\":
                if i>=n:
                    raise ValueError("escape")
                e=consume()
                m={"n":"\n","t":"\t","r":"\r","\\":"\\","'":"'",'"':'"'}
                out.append(m.get(e,e))
            else:
                out.append(c)
    def readnumber():
        nonlocal i
        j=i
        if peek() in "+-":
            consume()
        dig=False
        while peek().isdigit():
            consume()
            dig=True
        if peek()==".":
            consume()
            while peek().isdigit():
                consume()
                dig=True
        num=s[j:i]
        if not dig:
            raise ValueError("number")
        if "." in num or "e" in num.lower():
            return float(num)
        return int(num)
    def readword():
        nonlocal i
        j=i
        while peek().isalpha():
            consume()
        return s[j:i]
    def parseexpr():
        return parseor()
    def parseor():
        v=parseand()
        ws()
        while s[i:i+2]=="or":
            i_plus_two=i+2
            nonlocal_i=i_plus_two
            i=nonlocal_i
            ws()
            v=v or parseand()
            ws()
        return v
    def parseand():
        v=parsenot()
        ws()
        while s[i:i+3]=="and":
            i_plus_three=i+3
            nonlocal_i=i_plus_three
            i=nonlocal_i
            ws()
            v=v and parsenot()
            ws()
        return v
    def parsenot():
        ws()
        if s[i:i+3]=="not":
            i_plus_three=i+3
            nonlocal_i=i_plus_three
            i=nonlocal_i
            ws()
            return not parsenot()
        return parsecompare()
    def parsecompare():
        v=parsearith()
        ws()
        while True:
            ops=[("==",lambda a,b:a==b),
                 ("!=",lambda a,b:a!=b),
                 ("<=",lambda a,b:a<=b),
                 (">=",lambda a,b:a>=b),
                 ("<",lambda a,b:a<b),
                 (">",lambda a,b:a>b)]
            matched=False
            for op,fn in ops:
                L=len(op)
                if s[i:i+L]==op:
                    i_new=i+L
                    nonlocal_i=i_new
                    i=nonlocal_i
                    ws()
                    r=parsearith()
                    v=fn(v,r)
                    matched=True
                    break
            if not matched:
                return v
    def parsearith():
        v=parseterm()
        ws()
        while True:
            if peek()=='+':
                consume()
                ws()
                v=add(v, parseterm())
            elif peek()=='-':
                consume()
                ws()
                v=subtract(v, parseterm())
            else:
                return v
    def parseterm():
        v=parsepower()
        ws()
        while True:
            if s[i:i+2]=="//":
                i_plus_two=i+2
                nonlocal_i=i_plus_two
                i=nonlocal_i
                ws()
                v=v//parsepower()
            elif peek()=='*':
                consume()
                ws()
                v=multiply(v, parsepower())
            elif peek()=='/':
                consume()
                ws()
                v=divide(v, parsepower())
            elif peek()=='%':
                consume()
                ws()
                v=v%parsepower()
            else:
                return v
    def parsepower():
        v=parsefactor()
        ws()
        if s[i:i+2]=="**":
            i_plus_two=add(i, 2)
            nonlocal_i=i_plus_two
            i=nonlocal_i
            ws()
            v=v**parsefactor()
        return v
    def parsefactor():
        ws()
        c=peek()
        if c=='(':
            consume()
            ws()
            v=parseexpr()
            ws()
            consume(')')
            return v
        if c in "'\"":
            return readstring()
        if c.isdigit() or c in "+-":
            j=i
            try:
                return readnumber()
            except:
                i=j
        if c=='[':
            return parselist()
        if c=='{':
            return parsedictorset()
        if c=='(':
            return parsetuple()
        w=readword()
        if w=="True":
            return True
        if w=="False":
            return False
        if w=="None":
            return None
        raise ValueError("literal "+w)
    def parselist():
        consume('[')
        ws()
        if peek()==']':
            consume(']')
            return []
        out=[]
        while True:
            out.append(parseexpr())
            ws()
            if peek()==']':
                consume(']')
                return out
            consume(',')
            ws()
    def parsetuple():
        consume('(')
        ws()
        if peek()==')':
            consume(')')
            return ()
        first=parseexpr()
        ws()
        if peek()==')':
            consume(')')
            return first
        consume(',')
        ws()
        out=[first]
        while True:
            out.append(parseexpr())
            ws()
            if peek()==')':
                consume(')')
                return tuple(out)
            consume(',')
            ws()
    def parsedictorset():
        consume('{')
        ws()
        if peek()=='}':
            consume('}')
            return {}
        pos=i
        k=parseexpr()
        ws()
        if peek()==':':
            consume(':')
            ws()
            v=parseexpr()
            d={k:v}
            ws()
            while peek()==',':
                consume(',')
                ws()
                if peek()=='}':
                    break
                k=parseexpr()
                ws()
                consume(':')
                ws()
                v=parseexpr()
                ws()
                d[k]=v
            consume('}')
            return d
        i=pos
        k=parseexpr()
        ws()
        out={k}
        while peek()==',':
            consume(',')
            ws()
            if peek()=='}':
                break
            out.add(parseexpr())
            ws()
        consume('}')
        return out
    ws()
    result=parseexpr()
    ws()
    if i!=n:
        raise ValueError("extra")
    return result

def createonesarray(shape, dtype, order='C', like=None):
    return np.ones(shape, dtype, order, like=like)

def numpyrandomrand(*args):
    return numpy.random.rand(*args)

def saveimagefromdata(filename, imagevariable):
    return plt.imsave(filename, imagevariable.numpy())

def Reversed(variable):
    return reversed(variable)

def showimage(image, axeson=False, numpysqueeze=False, block=None, title="Figure 1", fontsize=16, color='black'):
    if numpysqueeze:
        img = image.numpy().squeeze()
        plt.imshow(img)
        plt.axis('off' if not axeson else 'on')
        plt.title(title, fontsize=fontsize, color=color)
        plt.show(block=block)
    else:
        plt.show(image)
        plt.axis('off' if not axeson else 'on')
        plt.title(title, fontsize=fontsize, color=color)
        plt.show(block=block)

def localitems():
    return locals()

def globalitems():
    return globals()

def expressionevalution(toevaluate):
    if isinstance(toevaluate, (int, float)):
        return toevaluate
    toevaluate = toevaluate.replace(" ", "")
    if '+' in toevaluate:
        a, b = toevaluate.split('+')
        return add(a, b)
    elif '-' in toevaluate:
        a, b = toevaluate.split('-')
        return subtract(a, b)
    elif '*' in toevaluate:
        a, b = toevaluate.split('*')
        return multiply(a, b)
    elif '/' in toevaluate:
        a, b = toevaluate.split('/')
        return divide(a, b)
    elif '//' in toevaluate:
        a, b = toevaluate.split('//')
        return floordivide(a, b)
    elif '!' in toevaluate:
        n = toevaluate.replace('!', '')
        return factorial(n)
    elif '^' in toevaluate:
        a, b = toevaluate.replace('^')
        return safepower(a, b)
    else:
        return None

def walkwithos(top, topdown=True, onerror=None, followlinks=False):
    return os.walk(top, topdown=topdown, onerror=onerror, followlinks=followlinks)

def openfile(file, mode='r', buffering=-1, encoding=None, errors=None, newline=None, closefd=True, opener=None):
    return open(file, mode=mode, buffering=buffering, encoding=encoding, errors=errors, newline=newline, closefd=closefd, opener=opener)

asciiflag = re.ASCII
ignorecase = re.IGNORECASE
localeflag = re.LOCALE
multiline = re.MULTILINE
dotall = re.DOTALL
verbose = re.VERBOSE
debug = re.DEBUG
template = re.TEMPLATE

def match(pattern, string, flags=0):
    return re.match(pattern, string, flags)

def fullmatch(pattern, string, flags=0):
    return re.fullmatch(pattern, string, flags)

def search(pattern, string, flags=0):
    return re.search(pattern, string, flags)

def findall(pattern, string, flags=0):
    return re.findall(pattern, string, flags)

def finditer(pattern, string, flags=0):
    return re.finditer(pattern, string, flags)

def sub(pattern, repl, string, count=0, flags=0):
    return re.sub(pattern, repl, string, count, flags)

def subn(pattern, repl, string, count=0, flags=0):
    return re.subn(pattern, repl, string, count, flags)

def split(pattern, string, maxsplit=0, flags=0):
    return re.split(pattern, string, maxsplit, flags)

def compile(pattern, flags=0):
    return re.compile(pattern, flags)

def escape(pattern):
    return re.escape(pattern)

class Pattern:
    def __init__(self, pattern, flags=0):
        self.task = re.compile(pattern, flags)

    def match(self, string, pos=0, endpos=None):
        return self.task.match(string, pos, endpos if endpos is not None else len(string))

    def fullmatch(self, string, pos=0, endpos=None):
        return self.task.fullmatch(string, pos, endpos if endpos is not None else len(string))

    def search(self, string, pos=0, endpos=None):
        return self.task.search(string, pos, endpos if endpos is not None else len(string))

    def findall(self, string, pos=0, endpos=None):
        return self.task.findall(string, pos, endpos if endpos is not None else len(string))

    def finditer(self, string, pos=0, endpos=None):
        return self.task.finditer(string, pos, endpos if endpos is not None else len(string))

    def sub(self, repl, string, count=0):
        return self.task.sub(repl, string, count)

    def subn(self, repl, string, count=0):
        return self.task.subn(repl, string, count)

    def split(self, string, maxsplit=0):
        return self.task.split(string, maxsplit)

class Match:
    def __init__(self, match_obj):
        self.task = match_obj

    def group(self, *args):
        return self.task.group(*args)

    def groups(self, default=None):
        return self.task.groups(default)

    def groupdict(self, default=None):
        return self.task.groupdict(default)

    def start(self, group=0):
        return self.task.start(group)

    def end(self, group=0):
        return self.task.end(group)

    def span(self, group=0):
        return self.task.span(group)

    @property
    def string(self):
        return self.task.string

    @property
    def re(self):
        return self.task.re

    @property
    def pos(self):
        return self.task.pos

    @property
    def endpos(self):
        return self.task.endpos

    @property
    def lastindex(self):
        return self.task.lastindex

    @property
    def lastgroup(self):
        return self.task.lastgroup
