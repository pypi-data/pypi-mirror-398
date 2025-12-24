import os
html = "<html><body>"
file = "temprint.html"
title = 0;
font = "arial"
fontsize = 16
titlefont = "arial"
ncolor = "black"
tcolor = "blue"
def init():
    global html
    html = "<html><body>\n"
    with open(file, "w") as f:
        f.write(html)

def set(what, value):
    global font, titlefont, tcolor, ncolor
    if what == "font":
        font = value
    if what == "Titlefont":
        titlefont = value
    if what == "Titlecolor":
        tcolor = value
    if what == "Fontcolor":
        ncolor = value
    

def addtext(text):
    global html
    html += f'<p style="font-family:{font}; color:{ncolor};">{text}</p><hr>\n'


    with open(file, "w") as f:
        f.write(html + "</body></html>")
def addtitle(title):
    global html
    html += f'<p style="font-size:{fontsize * 2}px; font-weight:bold; font-family:{titlefont}; color:{tcolor};">{title}</p><hr>\n'

    with open(file, "w") as f:
        f.write(html + "</body></html>")
def addphoto(fotopath,photosize):
    global html
    html += f'<img src="{fotopath}" style="width:{photosize}px;"><br>'
    with open(file, "w") as f:
        f.write(html + "</body></html>")
def print():
    file = os.path.abspath("temprint.html")
    os.system("print {file}")
def end():
    os.remove("temprint.html")


def debug():
    init()
    addtitle("mango")
    addtext("sigma")
    print()
    
