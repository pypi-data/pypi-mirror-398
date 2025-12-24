from tkhtmlview import HTMLLabel
from tkinter import Tk

efn_html_root = None

def createhtmlgui(title, geometry, bg, icon, htmlcode, fullscreen=False):
    efn_html_root = Tk()
    efn_html_root.title(title)
    efn_html_root.geometry(geometry)
    efn_htnl_root.configure(bg=bg)
    efn_html_root.iconbitmap(icon)
    efn_html_root.attributes("-fullscreen", fullscreen)

    html_content = htmlcode

    label = HTMLLabel(root, html=html_content)
    label.pack(padx=10, pady=10)

    efn_html_root.mainloop()
