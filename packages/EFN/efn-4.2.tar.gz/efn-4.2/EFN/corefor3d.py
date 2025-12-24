import sys, os
sys.stdout = open(os.devnull, 'w')
from ursina import *
sys.stdout = sys.__stdout__
import warnings

def threedgraphicssetup():
    app = Ursina()
    return app

def settings(title, geometry, bg, icon, fullscreen, resizable):
    window.title = title
    window.size = tuple(map(int, geometry.lower().replace('x', ' ').split()))
    window.color = bg
    window.fullscreen = fullscreen
    window.borderless = not resizable
    if icon:
        window.icon = icon
    
def waitsometime(app, function, delay):
    invoke(function, delay)

def removeentity(app, entity):
    destroy(entity)

def quitapp():
    warnings.warn("If the 3D app won't quit, it can freeze. This can eat your CPU.")
    sys.exit()

def createentity(app, entityname, colorname, rotation=(None, None, None), rotate=(None, None, None)):
    entity = Entity(model=entityname, color=getattr(color, colorname), rotation=rotation).rotate=rotate
    return entity

def copyentity(app, entity):
    duplicate(entity)

def playsound(app, soundfile):
    Audio(f"{soundfile}")

def getdistance(app, a, b):
    distance(a, b)

def createbutton(
    command,
    text='Button',
    icon=None,
    tooltip=None,
    parent=camera.ui,
    model='quad',
    origin=(0,0),
    scale=(.3,.1),
    position=(0,0),
    rotation=(0,0,0),
    color=color.azure,
    highlight_color=color.lime,
    pressed_color=color.gray,
    text_color=color.white,
    z=0,
    collider='box',
    enabled=True,
    eternal=False
):
    button = Button(
        text=text,
        icon=icon,
        tooltip=tooltip,
        parent=parent,
        model=model,
        origin=origin,
        scale=scale,
        position=position,
        rotation=rotation,
        color=color,
        highlight_color=highlight_color,
        pressed_color=pressed_color,
        text_color=text_color,
        z=z,
        collider=collider,
        enabled=enabled,
        eternal=eternal
    )
    button.on_click = command if command else None
    return button

def createtext(
    text='Hello',
    start_tag='<',
    end_tag='>',
    ignore=True,
    font='VeraMono.ttf',
    size=1,
    origin=(0,0),
    position=(0,0),
    rotation=(0,0,0),
    scale=1,
    parent=camera.ui,
    color=color.white,
    background=False,
    line_height=1.2,
    wordwrap=None,
    resolution=1080,
    z=0,
    enabled=True,
    eternal=False
):
    txt = Text(
        text=text,
        start_tag=start_tag,
        end_tag=end_tag,
        ignore=ignore,
        font=font,
        size=size,
        origin=origin,
        position=position,
        rotation=rotation,
        scale=scale,
        parent=parent,
        color=color,
        background=background,
        line_height=line_height,
        wordwrap=wordwrap,
        resolution=resolution,
        z=z,
        enabled=enabled,
        eternal=eternal
    )
    return txt

def createinputfield(
    default_value='',
    label='',
    max_lines=1,
    character_limit=None,
    limit_content_to=None,
    active=True,
    parent=camera.ui,
    position=(0,0),
    scale=(.5,.05),
    rotation=(0,0,0),
    text_color=color.black,
    model='quad',
    color=color.white,
    z=0,
    collider='box',
    enabled=True,
    eternal=False
):
    inputfield = InputField(
        default_value=default_value,
        label=label,
        max_lines=max_lines,
        character_limit=character_limit,
        limit_content_to=limit_content_to,
        active=active,
        parent=parent,
        position=position,
        scale=scale,
        rotation=rotation,
        text_color=text_color,
        model=model,
        color=color,
        z=z,
        collider=collider,
        enabled=enabled,
        eternal=eternal
    )
    return inputfield

def createslider(
    min=0,
    max=1,
    default=0.5,
    step=0,
    vertical=False,
    dynamic=True,
    text='',
    parent=camera.ui,
    position=(0,0),
    scale=(.5,.05),
    rotation=(0,0,0),
    model='quad',
    color=color.white,
    z=0,
    collider='box',
    enabled=True,
    eternal=False
):
    slider = Slider(
        min=min,
        max=max,
        default=default,
        step=step,
        vertical=vertical,
        dynamic=dynamic,
        text=text,
        parent=parent,
        position=position,
        scale=scale,
        rotation=rotation,
        model=model,
        color=color,
        z=z,
        collider=collider,
        enabled=enabled,
        eternal=eternal
    )
    return slider

def createwindowpanel(
    title='Panel',
    content=(),
    popup=False,
    draggable=True,
    parent=camera.ui,
    position=(0,0),
    scale=(.6,.6),
    rotation=(0,0,0),
    model='quad',
    color=color.dark_gray,
    z=0,
    collider='box',
    enabled=True,
    eternal=False
):
    panel = WindowPanel(
        title=title,
        content=content,
        popup=popup,
        draggable=draggable,
        parent=parent,
        position=position,
        scale=scale,
        rotation=rotation,
        model=model,
        color=color,
        z=z,
        collider=collider,
        enabled=enabled,
        eternal=eternal
    )
    return panel

def setposition(app, widget, position=(0, 0, 0)):
    widget.position = position

def animateposition(app, widget, duration, position=(0, 5, 0),):
    widget.animate_position(position, duration=duration)

def setcamera(position=(0,0,-10), rotation=(0,0,0)):
    camera.position = position
    camera.rotation = rotation

def configuresetting(app, widget, setting, data):
    widget.setting = data
