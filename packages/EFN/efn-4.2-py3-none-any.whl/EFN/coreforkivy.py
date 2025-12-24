def createwidget(widgettype, **kwargs):
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.checkbox import CheckBox
    from kivy.uix.togglebutton import ToggleButton
    from kivy.uix.switch import Switch
    from kivy.uix.slider import Slider
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.textinput import TextInput
    from kivy.uix.image import Image
    from kivy.uix.video import Video
    from kivy.uix.filechooser import FileChooserListView, FileChooserIconView
    from kivy.uix.spinner import Spinner
    from kivy.uix.dropdown import DropDown
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.recycleview import RecycleView
    from kivy.uix.popup import Popup
    from kivy.uix.modalview import ModalView
    from kivy.uix.screenmanager import ScreenManager, Screen
    from kivy.uix.tabbedpanel import TabbedPanel
    from kivy.uix.accordion import Accordion
    from kivy.uix.treeview import TreeView
    from kivy.uix.camera import Camera
    from kivy.uix.videoplayer import VideoPlayer
    from kivy.core.audio import SoundLoader

    widgetmap = {
        'label': Label,
        'button': Button,
        'checkbox': CheckBox,
        'togglebutton': ToggleButton,
        'switch': Switch,
        'slider': Slider,
        'progressbar': ProgressBar,
        'textinput': TextInput,
        'image': Image,
        'video': Video,
        'filechooserlist': FileChooserListView,
        'filechoosericon': FileChooserIconView,
        'spinner': Spinner,
        'dropdown': DropDown,
        'scrollview': ScrollView,
        'recycleview': RecycleView,
        'popup': Popup,
        'modalview': ModalView,
        'screenmanager': ScreenManager,
        'screen': Screen,
        'tabbedpanel': TabbedPanel,
        'accordion': Accordion,
        'treeview': TreeView,
        'camera': Camera,
        'videoplayer': VideoPlayer,
        'sound': SoundLoader.load
    }

    if widgettype not in widgetmap:
        raise ValueError(f"Unsupported widget type: {widgettype}")
    return widgetmap[widgettype](**kwargs)

def configurelayout(layouttype, widgets, **kwargs):
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.floatlayout import FloatLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.anchorlayout import AnchorLayout
    from kivy.uix.stacklayout import StackLayout
    from kivy.uix.relativelayout import RelativeLayout
    from kivy.uix.pagelayout import PageLayout
    from kivy.uix.scatterlayout import ScatterLayout

    layoutmap = {
        'box': BoxLayout,
        'float': FloatLayout,
        'grid': GridLayout,
        'anchor': AnchorLayout,
        'stack': StackLayout,
        'relative': RelativeLayout,
        'page': PageLayout,
        'scatter': ScatterLayout
    }

    if layouttype not in layoutmap:
        raise ValueError(f"Unsupported layout type: {layouttype}")
    
    layout = layoutmap[layouttype](**kwargs)
    for widget in widgets:
        layout.add_widget(widget)
    return layout

def configurewindow(section: str, *args):
    from kivy.config import Config
    from kivy.core.window import Window

    if not all(isinstance(arg, tuple) and len(arg) == 2 for arg in args):
        print("Error: Arguments should be a list of tuples (key, value).")
        return

    if section in ['graphics', 'input', 'kivy']:
        for key, value in args:
            try:
                Config.set(section, key, value)
            except Exception as e:
                print(f"Failed to set Config[{section}][{key}]: {e}")
        Config.write()

    elif section == 'window':
        for key, value in args:
            try:
                if key == 'size':
                    Window.size = value
                elif key == 'minimum_width':
                    Window.minimum_width = value
                elif key == 'minimum_height':
                    Window.minimum_height = value
                elif key == 'clearcolor':
                    Window.clearcolor = value
                elif key == 'borderless':
                    Window.borderless = value
                elif key == 'fullscreen':
                    Window.fullscreen = value
                elif key == 'icon':
                    Window.set_icon(value)
                elif key == 'title':
                    Window.set_title(value)
                elif key == 'show_cursor':
                    Window.show_cursor = value
                elif key == 'system_cursor':
                    Window.system_cursor = value
                elif key == 'top':
                    Window.top = value
                elif key == 'left':
                    Window.left = value
                elif key == 'rotation':
                    Window.rotation = value
                else:
                    print(f"Unsupported window key: {key}")
            except Exception as e:
                print(f"Failed to set Window.{key}: {e}")
    else:
        print(f"Unsupported section: {section}")

def runapp(appname):
    appname().run()

def copytext(text):
    from kivy.core.clipboard import Clipboard
    Clipboard.copy(text)

def paste():
    from kivy.core.clipboard import Clipboard
    Clipboard.paste()
