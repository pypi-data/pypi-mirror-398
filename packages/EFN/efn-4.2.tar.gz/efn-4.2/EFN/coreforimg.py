from PIL import Image, ImageTk
from tkinter import Tk, Label
from PIL import ImageFilter, ImageEnhance, ImageOps, ImageChops, ImageDraw, ImageFont, ImageGrab, ImageTransform, ImageSequence, ImagePalette, ImageCms, ImageFile, ImageMode

def showimage(image_path, width, height):
    img = Image.open(image_path).resize((width, height))
    img.show()

def resizeimage(imgvar, width, height):
    imgvar.resize((width, height))

def createimagewidget(
    root,
    width,
    height,
    image_path,
    horizontal=0,
    vertical=0,
    start_pos=False,
    drag=True,
    clickable=True,
    on_click=None
):
    pil_img = Image.open(image_path).resize((width, height))
    tk_img = ImageTk.PhotoImage(pil_img)

    label = Label(root, image=tk_img, bg="white")
    label.image = tk_img
    label.place(x=horizontal, y=vertical)

    drag_data = {"x": 0, "y": 0}

    def handle_click(event):
        if on_click:
            on_click(event)
        else:
            print("Image clicked at: ", event.x, event.y)

    def on_drag_start(event):
        drag_data["x"] = event.x
        drag_data["y"] = event.y

    def on_drag_motion(event):
        dx = event.x - drag_data["x"]
        dy = event.y - drag_data["y"]
        x = label.winfo_x() + dx
        y = label.winfo_y() + dy
        label.place(x=x, y=y)
        drag_data["x"] = event.x
        drag_data["y"] = event.y

    if clickable:
        label.bind("<Button-1>", handle_click)
    if drag:
        label.bind("<ButtonPress-1>", on_drag_start)
        label.bind("<B1-Motion>", on_drag_motion)

    return label

def rotateimage(imgvar, degree):
    imgvar.rotate(degree, expand=True)

def openimage(path):
    return Image.open(path)

def newimage(mode, size, color=0):
    return Image.new(mode, size, color)

def frombytes(mode, size, data, decoder_name='raw', *args):
    return Image.frombytes(mode, size, data, decoder_name, *args)

def fromarray(obj, mode=None):
    return Image.fromarray(obj, mode)

def frombuffer(mode, size, data, decoder_name='raw', *args):
    return Image.frombuffer(mode, size, data, decoder_name, *args)

def frompilimage(img):
    return Image.Image(img)

def copyimage(img):
    return img.copy()

def cropimage(img, box):
    return img.crop(box)

def pasteimage(img, pasteimg, box=None):
    img.paste(pasteimg, box)
    return img

def transposeimage(img, method):
    return img.transpose(method)

def rotateimage(img, angle, resample=0, expand=0, center=None, translate=None, fillcolor=None):
    return img.rotate(angle, resample=resample, expand=expand, center=center, translate=translate, fillcolor=fillcolor)

def resizeimage(img, size, resample=0):
    return img.resize(size, resample=resample)

def convertimage(img, mode):
    return img.convert(mode)

def splitimage(img):
    return img.split()

def mergeimage(mode, bands):
    return Image.merge(mode, bands)

def getpixel(img, xy):
    return img.getpixel(xy)

def putpixel(img, xy, value):
    img.putpixel(xy, value)
    return img

def getimagesize(img):
    return img.size

def getimagemode(img):
    return img.mode

def getimageformat(img):
    return img.format

def saveimage(img, path, format=None):
    img.save(path, format=format)
    return img

def showimage(img):
    img.show()
    return img

def applyfilter(img, filterobj):
    return img.filter(filterobj)

def blurimage(img):
    return img.filter(ImageFilter.BLUR)

def contourimage(img):
    return img.filter(ImageFilter.CONTOUR)

def detailimage(img):
    return img.filter(ImageFilter.DETAIL)

def edgeenhanceimage(img):
    return img.filter(ImageFilter.EDGE_ENHANCE)

def edgeenhancemoreimage(img):
    return img.filter(ImageFilter.EDGE_ENHANCE_MORE)

def embossimage(img):
    return img.filter(ImageFilter.EMBOSS)

def findedgesimage(img):
    return img.filter(ImageFilter.FIND_EDGES)

def sharpenimage(img):
    return img.filter(ImageFilter.SHARPEN)

def smoothimage(img):
    return img.filter(ImageFilter.SMOOTH)

def smoothmoreimage(img):
    return img.filter(ImageFilter.SMOOTH_MORE)

def maxfilterimage(img, size=3):
    return img.filter(ImageFilter.MaxFilter(size))

def minfilterimage(img, size=3):
    return img.filter(ImageFilter.MinFilter(size))

def medianfilterimage(img, size=3):
    return img.filter(ImageFilter.MedianFilter(size))

def rankfilterimage(img, size, rank):
    return img.filter(ImageFilter.RankFilter(size, rank))

def modefilterimage(img, size=3):
    return img.filter(ImageFilter.ModeFilter(size))

def gaussianblurimage(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius))

def unsharpmaskimage(img, radius=2, percent=150, threshold=3):
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

def enhancebrightness(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def enhancecontrast(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def enhancecolor(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def enhancesharpness(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def flipimage(img):
    return ImageOps.flip(img)

def mirrorimage(img):
    return ImageOps.mirror(img)

def grayscaleimage(img):
    return ImageOps.grayscale(img)

def invertimage(img):
    return ImageOps.invert(img)

def solarizeimage(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def posterizeimage(img, bits):
    return ImageOps.posterize(img, bits)

def autocontrastimage(img, cutoff=0, ignore=None):
    return ImageOps.autocontrast(img, cutoff=cutoff, ignore=ignore)

def equalizeimage(img, mask=None):
    return ImageOps.equalize(img, mask=mask)

def expandimage(img, border=0, fill=0):
    return ImageOps.expand(img, border=border, fill=fill)

def fitimage(img, size, method=3, bleed=0.0, centering=(0.5,0.5)):
    return ImageOps.fit(img, size, method=method, bleed=bleed, centering=centering)

def cropborderimage(img, border):
    return ImageOps.crop(img, border)

def padimage(img, size, method=3, color=0):
    return ImageOps.pad(img, size, method=method, color=color)

def scaleimage(img, factor, resample=3):
    return ImageOps.scale(img, factor, resample=resample)

def exiftransposeimage(img):
    return ImageOps.exif_transpose(img)

def choppimagesum(img1, img2):
    return ImageChops.add(img1, img2)

def choppimagesubtract(img1, img2):
    return ImageChops.subtract(img1, img2)

def choppimagemultiply(img1, img2):
    return ImageChops.multiply(img1, img2)

def choppimagedifference(img1, img2):
    return ImageChops.difference(img1, img2)

def choppimageinvert(img):
    return ImageChops.invert(img)

def choppimagescreen(img1, img2):
    return ImageChops.screen(img1, img2)

def choppimagemax(img1, img2):
    return ImageChops.lighter(img1, img2)

def choppimagemin(img1, img2):
    return ImageChops.darker(img1, img2)

def choppimagesoftlight(img1, img2):
    return ImageChops.soft_light(img1, img2)

def choppimageoffset(img, xoffset, yoffset=0):
    return ImageChops.offset(img, xoffset, yoffset)

def choppimageconstant(image, value):
    return ImageChops.constant(image, value)

def choppimagetimes(image, factor):
    return ImageChops.multiply(image, Image.new(image.mode, image.size, factor))

def createdraw(img):
    return ImageDraw.Draw(img)

def drawline(draw, xy, fill=None, width=0):
    draw.line(xy, fill=fill, width=width)
    return draw

def drawrectangle(draw, xy, fill=None, outline=None, width=0):
    draw.rectangle(xy, fill=fill, outline=outline, width=width)
    return draw

def drawellipse(draw, xy, fill=None, outline=None, width=0):
    draw.ellipse(xy, fill=fill, outline=outline, width=width)
    return draw

def drawpolygon(draw, xy, fill=None, outline=None):
    draw.polygon(xy, fill=fill, outline=outline)
    return draw

def drawtext(draw, xy, text, fill=None, font=None, anchor=None, spacing=0, align="left", direction=None):
    draw.text(xy, text, fill=fill, font=font, anchor=anchor, spacing=spacing, align=align, direction=direction)
    return draw

def drawarc(draw, xy, start, end, fill=None, width=1):
    draw.arc(xy, start, end, fill=fill, width=width)
    return draw

def drawchord(draw, xy, start, end, fill=None, outline=None):
    draw.chord(xy, start, end, fill=fill, outline=outline)
    return draw

def drawpieslice(draw, xy, start, end, fill=None, outline=None):
    draw.pieslice(xy, start, end, fill=fill, outline=outline)
    return draw

def drawlineimagedraw(draw, xy, fill=None, width=0):
    draw.line(xy, fill=fill, width=width)
    return draw

def loadfont(path, size):
    return ImageFont.truetype(path, size)

def loaddefaultfont():
    return ImageFont.load_default()

def fontgetsize(font, text):
    return font.getsize(text)

def fontgetmask(font, text, mode="L"):
    return font.getmask(text, mode=mode)

def fontgetbbox(font, text):
    return font.getbbox(text)

def fontgetlength(font, text):
    return font.getlength(text)

def flipimageops(img):
    return ImageOps.flip(img)

def mirrorimageops(img):
    return ImageOps.mirror(img)

def invertimageops(img):
    return ImageOps.invert(img)

def grayscaleimageops(img):
    return ImageOps.grayscale(img)

def autocontrastimageops(img, cutoff=0, ignore=None):
    return ImageOps.autocontrast(img, cutoff=cutoff, ignore=ignore)

def equalizeimageops(img, mask=None):
    return ImageOps.equalize(img, mask=mask)

def solarizeimageops(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def posterizeimageops(img, bits):
    return ImageOps.posterize(img, bits)

def expandimageops(img, border=0, fill=0):
    return ImageOps.expand(img, border=border, fill=fill)

def cropborderimageops(img, border):
    return ImageOps.crop(img, border)

def fitimageops(img, size, method=3, bleed=0.0, centering=(0.5,0.5)):
    return ImageOps.fit(img, size, method=method, bleed=bleed, centering=centering)

def padimageops(img, size, method=3, color=0):
    return ImageOps.pad(img, size, method=method, color=color)

def scaleimageops(img, factor, resample=3):
    return ImageOps.scale(img, factor, resample=resample)

def exiftransposeimageops(img):
    return ImageOps.exif_transpose(img)

def addchop(img1, img2):
    return ImageChops.add(img1, img2)

def subtractchop(img1, img2):
    return ImageChops.subtract(img1, img2)

def multiplychop(img1, img2):
    return ImageChops.multiply(img1, img2)

def differencechop(img1, img2):
    return ImageChops.difference(img1, img2)

def invertchop(img):
    return ImageChops.invert(img)

def screenchop(img1, img2):
    return ImageChops.screen(img1, img2)

def lighterchop(img1, img2):
    return ImageChops.lighter(img1, img2)

def darkerchop(img1, img2):
    return ImageChops.darker(img1, img2)

def softlightchop(img1, img2):
    return ImageChops.soft_light(img1, img2)

def offsetchop(img, xoffset, yoffset=0):
    return ImageChops.offset(img, xoffset, yoffset)

def constantchop(img, value):
    return ImageChops.constant(img, value)

def multiplyconstantchop(img, factor):
    return ImageChops.multiply(img, Image.new(img.mode, img.size, factor))

def autolevelsimage(img):
    return ImageOps.autocontrast(img)

def histogramimage(img):
    return img.histogram()

def splitbands(img):
    return img.split()

def mergebands(mode, bands):
    return Image.merge(mode, bands)

def isanimatedimage(img):
    return getattr(img, "is_animated", False)

def nframesimage(img):
    return getattr(img, "n_frames", 1)

def seekframeimage(img, frame):
    img.seek(frame)
    return img

def tellframeimage(img):
    return img.tell()

def convertimagepalette(img, palette):
    return img.convert("P", palette=palette)

def quantizeimage(img, colors=256, method=0, kmeans=0, palette=None):
    return img.quantize(colors=colors, method=method, kmeans=kmeans, palette=palette)

def draftimage(img, mode, size):
    img.draft(mode, size)
    return img

def getexifimage(img):
    return getattr(img, "_getexif", lambda: None)()

def getbandsimage(img):
    return img.getbands()

def getcolorsimage(img, maxcolors=256):
    return img.getcolors(maxcolors)

def getextremaimage(img):
    return img.getextrema()

def getimagetile(img):
    return img.tile

def getimagedata(img):
    return img.getdata()

def putimagedata(img, data):
    img.putdata(data)
    return img

def getimagedraft(img):
    return getattr(img, "draft", None)

def tobytesimage(img, encoder_name="raw", *args):
    return img.tobytes(encoder_name, *args)

def toarrayimage(img):
    import numpy as np
    return np.array(img)

def fromarrayimage(arr, mode=None):
    return Image.fromarray(arr, mode)

def transformimage(img, size, method, data=None, resample=0, fill=1):
    return img.transform(size, method, data, resample=resample, fill=fill)

def affineimage(img, matrix, resample=0, fillcolor=None):
    return img.transform(img.size, Image.AFFINE, matrix, resample=resample, fillcolor=fillcolor)

def perspectiveimage(img, data, resample=0, fillcolor=None):
    return img.transform(img.size, Image.PERSPECTIVE, data, resample=resample, fillcolor=fillcolor)

def meshtransformimage(img, mesh, resample=0, fillcolor=None):
    return img.transform(img.size, Image.MESH, mesh, resample=resample, fillcolor=fillcolor)

def cropimagebox(img, box):
    return img.crop(box)

def pasteimagebox(img, source, box=None, mask=None):
    img.paste(source, box, mask)
    return img

def resizeimagebox(img, size, resample=0):
    return img.resize(size, resample=resample)

def rotateimageangle(img, angle, resample=0, expand=0, center=None, translate=None, fillcolor=None):
    return img.rotate(angle, resample=resample, expand=expand, center=center, translate=translate, fillcolor=fillcolor)

def transposeimagetranspose(img, method):
    return img.transpose(method)

def convertimagemode(img, mode):
    return img.convert(mode)

def splitimagemode(img):
    return img.split()

def mergeimagemode(mode, bands):
    return Image.merge(mode, bands)

def getpixelvalue(img, xy):
    return img.getpixel(xy)

def putpixelvalue(img, xy, value):
    img.putpixel(xy, value)
    return img

def getcolorsimg(img, maxcolors=256):
    return img.getcolors(maxcolors)

def getextremaimg(img):
    return img.getextrema()

def histogramimg(img):
    return img.histogram()

def draftimg(img, mode, size):
    img.draft(mode, size)
    return img

def quantizeimg(img, colors=256, method=0, kmeans=0, palette=None):
    return img.quantize(colors=colors, method=method, kmeans=kmeans, palette=palette)

def getbandsimg(img):
    return img.getbands()

def getdataimg(img):
    return img.getdata()

def putdataimg(img, data):
    img.putdata(data)
    return img

def tobytesimg(img, encoder_name="raw", *args):
    return img.tobytes(encoder_name, *args)

def frombytesimg(mode, size, data, decoder_name="raw", *args):
    return Image.frombytes(mode, size, data, decoder_name, *args)

def frombufferimg(mode, size, data, decoder_name="raw", *args):
    return Image.frombuffer(mode, size, data, decoder_name, *args)

def fromarrayimg(obj, mode=None):
    return Image.fromarray(obj, mode)

def copyimg(img):
    return img.copy()

def showimg(img):
    img.show()
    return img

def saveimg(img, path, format=None):
    img.save(path, format=format)
    return img

def isanimatedimg(img):
    return getattr(img, "is_animated", False)

def nframesimg(img):
    return getattr(img, "n_frames", 1)

def seekframeimg(img, frame):
    img.seek(frame)
    return img

def tellframeimg(img):
    return img.tell()

def getexifimg(img):
    return getattr(img, "_getexif", lambda: None)()

def exiftransposeimg(img):
    return ImageOps.exif_transpose(img)

def autocontrastimg(img, cutoff=0, ignore=None):
    return ImageOps.autocontrast(img, cutoff=cutoff, ignore=ignore)

def equalizeimg(img, mask=None):
    return ImageOps.equalize(img, mask=mask)

def solarizeimg(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def posterizeimg(img, bits):
    return ImageOps.posterize(img, bits)

def invertimg(img):
    return ImageOps.invert(img)

def flipimg(img):
    return ImageOps.flip(img)

def mirrorimg(img):
    return ImageOps.mirror(img)

def expandimg(img, border=0, fill=0):
    return ImageOps.expand(img, border=border, fill=fill)

def cropborderimg(img, border):
    return ImageOps.crop(img, border)

def fitimg(img, size, method=3, bleed=0.0, centering=(0.5,0.5)):
    return ImageOps.fit(img, size, method=method, bleed=bleed, centering=centering)

def padimg(img, size, method=3, color=0):
    return ImageOps.pad(img, size, method=method, color=color)

def scaleimg(img, factor, resample=3):
    return ImageOps.scale(img, factor, resample=resample)

def blurimg(img):
    return img.filter(ImageFilter.BLUR)

def contourimg(img):
    return img.filter(ImageFilter.CONTOUR)

def detailimg(img):
    return img.filter(ImageFilter.DETAIL)

def edgeenhanceimg(img):
    return img.filter(ImageFilter.EDGE_ENHANCE)

def edgeenhancemoreimg(img):
    return img.filter(ImageFilter.EDGE_ENHANCE_MORE)

def embossimg(img):
    return img.filter(ImageFilter.EMBOSS)

def findedgesimg(img):
    return img.filter(ImageFilter.FIND_EDGES)

def sharpenimg(img):
    return img.filter(ImageFilter.SHARPEN)

def smoothimg(img):
    return img.filter(ImageFilter.SMOOTH)

def smoothmoreimg(img):
    return img.filter(ImageFilter.SMOOTH_MORE)

def maxfilterimg(img, size=3):
    return img.filter(ImageFilter.MaxFilter(size))

def minfilterimg(img, size=3):
    return img.filter(ImageFilter.MinFilter(size))

def medianfilterimg(img, size=3):
    return img.filter(ImageFilter.MedianFilter(size))

def rankfilterimg(img, size, rank):
    return img.filter(ImageFilter.RankFilter(size, rank))

def modefilterimg(img, size=3):
    return img.filter(ImageFilter.ModeFilter(size))

def gaussianblurimg(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius))

def unsharpmaskimg(img, radius=2, percent=150, threshold=3):
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

def enhancebrightnessimg(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def enhancecontrastimg(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def enhancecolorimg(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def enhancesharpnessimg(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def createdrawimg(img):
    return ImageDraw.Draw(img)

from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageChops, ImageDraw, ImageFont, ImageGrab

def grabimage(bbox=None, include_layered_windows=False, all_screens=False):
    return ImageGrab.grab(bbox=bbox, include_layered_windows=include_layered_windows, all_screens=all_screens)

def grabclipboardimage():
    return ImageGrab.grabclipboard()

def bboximage(img):
    return img.getbbox()

def splitbandsimg(img):
    return img.split()

def mergebandsimg(mode, bands):
    return Image.merge(mode, bands)

def addchopimg(img1, img2):
    return ImageChops.add(img1, img2)

def subtractchopimg(img1, img2):
    return ImageChops.subtract(img1, img2)

def multiplychopimg(img1, img2):
    return ImageChops.multiply(img1, img2)

def differencechopimg(img1, img2):
    return ImageChops.difference(img1, img2)

def invertchopimg(img):
    return ImageChops.invert(img)

def screenchopimg(img1, img2):
    return ImageChops.screen(img1, img2)

def lighterchopimg(img1, img2):
    return ImageChops.lighter(img1, img2)

def darkerchopimg(img1, img2):
    return ImageChops.darker(img1, img2)

def softlightchopimg(img1, img2):
    return ImageChops.soft_light(img1, img2)

def offsetchopimg(img, xoffset, yoffset=0):
    return ImageChops.offset(img, xoffset, yoffset)

def constantchopimg(img, value):
    return ImageChops.constant(img, value)

def multiplyconstantchopimg(img, factor):
    return ImageChops.multiply(img, Image.new(img.mode, img.size, factor))

def histogramimgdata(img):
    return img.histogram()

def draftimgmode(img, mode, size):
    img.draft(mode, size)
    return img

def getcolorsimgdata(img, maxcolors=256):
    return img.getcolors(maxcolors)

def getextremaimgdata(img):
    return img.getextrema()

def getbandsimgdata(img):
    return img.getbands()

def getdataimgdata(img):
    return img.getdata()

def putdataimgdata(img, data):
    img.putdata(data)
    return img

def getpixelimg(img, xy):
    return img.getpixel(xy)

def putpixelimg(img, xy, value):
    img.putpixel(xy, value)
    return img

def resizeimagefactor(img, size, resample=0):
    return img.resize(size, resample=resample)

def rotateimagefull(img, angle, resample=0, expand=0, center=None, translate=None, fillcolor=None):
    return img.rotate(angle, resample=resample, expand=expand, center=center, translate=translate, fillcolor=fillcolor)

def transposeimagetype(img, method):
    return img.transpose(method)

def convertimagemodefull(img, mode):
    return img.convert(mode)

def cropimagefull(img, box):
    return img.crop(box)

def pasteimagefull(img, source, box=None, mask=None):
    img.paste(source, box, mask)
    return img

def splitimagefull(img):
    return img.split()

def mergeimagefull(mode, bands):
    return Image.merge(mode, bands)

def copyimagefull(img):
    return img.copy()

def showimagefull(img):
    img.show()
    return img

def saveimagefull(img, path, format=None):
    img.save(path, format=format)
    return img

def isanimatedimagefull(img):
    return getattr(img, "is_animated", False)

def nframesimagefull(img):
    return getattr(img, "n_frames", 1)

def seekframeimagefull(img, frame):
    img.seek(frame)
    return img

def tellframeimagefull(img):
    return img.tell()

def getexifimagefull(img):
    return getattr(img, "_getexif", lambda: None)()

def tobytesimagefull(img, encoder_name="raw", *args):
    return img.tobytes(encoder_name, *args)

def frombytesimagefull(mode, size, data, decoder_name="raw", *args):
    return Image.frombytes(mode, size, data, decoder_name, *args)

def frombufferimagefull(mode, size, data, decoder_name="raw", *args):
    return Image.frombuffer(mode, size, data, decoder_name, *args)

def fromarrayimagefull(obj, mode=None):
    return Image.fromarray(obj, mode)

def toarrayimagefull(img):
    import numpy as np
    return np.array(img)

def quantizeimagefull(img, colors=256, method=0, kmeans=0, palette=None):
    return img.quantize(colors=colors, method=method, kmeans=kmeans, palette=palette)

def getimagetile(img):
    return img.tile

def getimagedraft(img):
    return getattr(img, "draft", None)

def flipimageopsfull(img):
    return ImageOps.flip(img)

def mirrorimageopsfull(img):
    return ImageOps.mirror(img)

def invertimageopsfull(img):
    return ImageOps.invert(img)

def grayscaleimageopsfull(img):
    return ImageOps.grayscale(img)

def autocontrastimageopsfull(img, cutoff=0, ignore=None):
    return ImageOps.autocontrast(img, cutoff=cutoff, ignore=ignore)

def equalizeimageopsfull(img, mask=None):
    return ImageOps.equalize(img, mask=mask)

def solarizeimageopsfull(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def posterizeimageopsfull(img, bits):
    return ImageOps.posterize(img, bits)

def expandimageopsfull(img, border=0, fill=0):
    return ImageOps.expand(img, border=border, fill=fill)

def cropborderimageopsfull(img, border):
    return ImageOps.crop(img, border)

def fitimageopsfull(img, size, method=3, bleed=0.0, centering=(0.5,0.5)):
    return ImageOps.fit(img, size, method=method, bleed=bleed, centering=centering)

def padimageopsfull(img, size, method=3, color=0):
    return ImageOps.pad(img, size, method=method, color=color)

def scaleimageopsfull(img, factor, resample=3):
    return ImageOps.scale(img, factor, resample=resample)

def exiftransposeimageopsfull(img):
    return ImageOps.exif_transpose(img)

def affinetransform(img, matrix, resample=0, fillcolor=None):
    return img.transform(img.size, Image.AFFINE, matrix, resample=resample, fillcolor=fillcolor)

def perspectivetransform(img, data, resample=0, fillcolor=None):
    return img.transform(img.size, Image.PERSPECTIVE, data, resample=resample, fillcolor=fillcolor)

def quadtransform(img, data, resample=0, fillcolor=None):
    return img.transform(img.size, Image.QUAD, data, resample=resample, fillcolor=fillcolor)

def meshtransform(img, mesh, resample=0, fillcolor=None):
    return img.transform(img.size, Image.MESH, mesh, resample=resample, fillcolor=fillcolor)

def filterblur(img):
    return img.filter(ImageFilter.BLUR)

def filtercontour(img):
    return img.filter(ImageFilter.CONTOUR)

def filterdetail(img):
    return img.filter(ImageFilter.DETAIL)

def filteredgeenhance(img):
    return img.filter(ImageFilter.EDGE_ENHANCE)

def filteredgeenhancemore(img):
    return img.filter(ImageFilter.EDGE_ENHANCE_MORE)

def filteremboss(img):
    return img.filter(ImageFilter.EMBOSS)

def filterfindedges(img):
    return img.filter(ImageFilter.FIND_EDGES)

def filtersharpen(img):
    return img.filter(ImageFilter.SHARPEN)

def filtersmooth(img):
    return img.filter(ImageFilter.SMOOTH)

def filtersmoothmore(img):
    return img.filter(ImageFilter.SMOOTH_MORE)

def filtermax(img, size=3):
    return img.filter(ImageFilter.MaxFilter(size))

def filtermin(img, size=3):
    return img.filter(ImageFilter.MinFilter(size))

def filtermedian(img, size=3):
    return img.filter(ImageFilter.MedianFilter(size))

def filterrank(img, size, rank):
    return img.filter(ImageFilter.RankFilter(size, rank))

def filtermode(img, size=3):
    return img.filter(ImageFilter.ModeFilter(size))

def filtergaussianblur(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius))

def filterunsharpmask(img, radius=2, percent=150, threshold=3):
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

def enhancebrightnessimg(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def enhancecontrastimg(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def enhancecolorimg(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def enhancesharpnessimg(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def drawlineimg(draw, xy, fill=None, width=0):
    draw.line(xy, fill=fill, width=width)
    return draw

def drawrectangleimg(draw, xy, fill=None, outline=None, width=0):
    draw.rectangle(xy, fill=fill, outline=outline, width=width)
    return draw

def drawellipseimg(draw, xy, fill=None, outline=None, width=0):
    draw.ellipse(xy, fill=fill, outline=outline, width=width)
    return draw

def drawpolygonimg(draw, xy, fill=None, outline=None):
    draw.polygon(xy, fill=fill, outline=outline)
    return draw

def drawarcimg(draw, xy, start, end, fill=None, width=1):
    draw.arc(xy, start, end, fill=fill, width=width)
    return draw

def drawchordimg(draw, xy, start, end, fill=None, outline=None):
    draw.chord(xy, start, end, fill=fill, outline=outline)
    return draw

def drawpiesliceimg(draw, xy, start, end, fill=None, outline=None):
    draw.pieslice(xy, start, end, fill=fill, outline=outline)
    return draw

def drawtextimg(draw, xy, text, fill=None, font=None, anchor=None, spacing=0, align="left", direction=None):
    draw.text(xy, text, fill=fill, font=font, anchor=anchor, spacing=spacing, align=align, direction=direction)
    return draw

def loadtruetypefont(path, size):
    return ImageFont.truetype(path, size)

def loaddefaultfontimg():
    return ImageFont.load_default()

def fontgetsizeimg(font, text):
    return font.getsize(text)

def fontgetmaskimg(font, text, mode="L"):
    return font.getmask(text, mode=mode)

def fontgetbboximg(font, text):
    return font.getbbox(text)

def fontgetlengthimg(font, text):
    return font.getlength(text)

def grabimagebbox(bbox=None, include_layered_windows=False, all_screens=False):
    return ImageGrab.grab(bbox=bbox, include_layered_windows=include_layered_windows, all_screens=all_screens)

def grabimageclipboard():
    return ImageGrab.grabclipboard()

def getbboximg(img):
    return img.getbbox()

def draftimgmode(img, mode, size):
    img.draft(mode, size)
    return img

def histogramimgdata(img):
    return img.histogram()

def getexifimgdata(img):
    return getattr(img, "_getexif", lambda: None)()

def seekframeimgdata(img, frame):
    img.seek(frame)
    return img

def tellframeimgdata(img):
    return img.tell()

def isanimatedimgdata(img):
    return getattr(img, "is_animated", False)

def nframesimgdata(img):
    return getattr(img, "n_frames", 1)

def tobytesimgdata(img, encoder_name="raw", *args):
    return img.tobytes(encoder_name, *args)

def frombytesimgdata(mode, size, data, decoder_name="raw", *args):
    return Image.frombytes(mode, size, data, decoder_name, *args)

def frombufferimgdata(mode, size, data, decoder_name="raw", *args):
    return Image.frombuffer(mode, size, data, decoder_name, *args)

def fromarrayimgdata(obj, mode=None):
    return Image.fromarray(obj, mode)

def toarrayimgdata(img):
    import numpy as np
    return np.array(img)

def flipimgops(img):
    return ImageOps.flip(img)

def mirrorimgops(img):
    return ImageOps.mirror(img)

def invertimgops(img):
    return ImageOps.invert(img)

def grayscaleimgops(img):
    return ImageOps.grayscale(img)

def autocontrastimgops(img, cutoff=0, ignore=None):
    return ImageOps.autocontrast(img, cutoff=cutoff, ignore=ignore)

def equalizeimgops(img, mask=None):
    return ImageOps.equalize(img, mask=mask)

def solarizeimgops(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def posterizeimgops(img, bits):
    return ImageOps.posterize(img, bits)

def expandimgops(img, border=0, fill=0):
    return ImageOps.expand(img, border=border, fill=fill)

def cropborderimgops(img, border):
    return ImageOps.crop(img, border)

def fitimgops(img, size, method=3, bleed=0.0, centering=(0.5,0.5)):
    return ImageOps.fit(img, size, method=method, bleed=bleed, centering=centering)

def padimgops(img, size, method=3, color=0):
    return ImageOps.pad(img, size, method=method, color=color)

def scaleimgops(img, factor, resample=3):
    return ImageOps.scale(img, factor, resample=resample)

def exiftransposeimgops(img):
    return ImageOps.exif_transpose(img)

def addchop(img1, img2):
    return ImageChops.add(img1, img2)

def subtractchop(img1, img2):
    return ImageChops.subtract(img1, img2)

def multiplychop(img1, img2):
    return ImageChops.multiply(img1, img2)

def differencechop(img1, img2):
    return ImageChops.difference(img1, img2)

def invertchop(img):
    return ImageChops.invert(img)

def screenchop(img1, img2):
    return ImageChops.screen(img1, img2)

def lighterchop(img1, img2):
    return ImageChops.lighter(img1, img2)

def darkerchop(img1, img2):
    return ImageChops.darker(img1, img2)

def softlightchop(img1, img2):
    return ImageChops.soft_light(img1, img2)

def offsetchop(img, xoffset, yoffset=0):
    return ImageChops.offset(img, xoffset, yoffset)

def constantchop(img, value):
    return ImageChops.constant(img, value)

def logicalandchop(img1, img2):
    return ImageChops.logical_and(img1, img2)

def logicalorchop(img1, img2):
    return ImageChops.logical_or(img1, img2)

def logicalxorchop(img1, img2):
    return ImageChops.logical_xor(img1, img2)

def multiplyconstantchop(img, factor):
    return ImageChops.multiply(img, Image.new(img.mode, img.size, factor))

def evaluateimagemath(expr, **kwargs):
    return ImageMath.eval(expr, **kwargs)

def roundimagemath(expr, **kwargs):
    return ImageMath.eval("round(%s)" % expr, **kwargs)

def floorimagemath(expr, **kwargs):
    return ImageMath.eval("floor(%s)" % expr, **kwargs)

def ceilimagemath(expr, **kwargs):
    return ImageMath.eval("ceil(%s)" % expr, **kwargs)

def sinimagemath(expr, **kwargs):
    return ImageMath.eval("sin(%s)" % expr, **kwargs)

def cosimagemath(expr, **kwargs):
    return ImageMath.eval("cos(%s)" % expr, **kwargs)

def tanimagemath(expr, **kwargs):
    return ImageMath.eval("tan(%s)" % expr, **kwargs)

def logimagemath(expr, **kwargs):
    return ImageMath.eval("log(%s)" % expr, **kwargs)

def expimagemath(expr, **kwargs):
    return ImageMath.eval("exp(%s)" % expr, **kwargs)

def powimagemath(expr, **kwargs):
    return ImageMath.eval("pow(%s)" % expr, **kwargs)

def modimagemath(expr, **kwargs):
    return ImageMath.eval("mod(%s)" % expr, **kwargs)

def convertimagemode(img, mode):
    return img.convert(mode)

def splitbands(img):
    return img.split()

def mergebands(mode, bands):
    return Image.merge(mode, bands)

def cropimage(img, box):
    return img.crop(box)

def pasteimage(img, source, box=None, mask=None):
    img.paste(source, box, mask)
    return img

def resizeimage(img, size, resample=0):
    return img.resize(size, resample=resample)

def rotateimage(img, angle, resample=0, expand=0, center=None, translate=None, fillcolor=None):
    return img.rotate(angle, resample=resample, expand=expand, center=center, translate=translate, fillcolor=fillcolor)

def transposeimage(img, method):
    return img.transpose(method)

def filterblur(img):
    return img.filter(ImageFilter.BLUR)

def filtercontour(img):
    return img.filter(ImageFilter.CONTOUR)

def filterdetail(img):
    return img.filter(ImageFilter.DETAIL)

def filteredgeenhance(img):
    return img.filter(ImageFilter.EDGE_ENHANCE)

def filteredgeenhancemore(img):
    return img.filter(ImageFilter.EDGE_ENHANCE_MORE)

def filteremboss(img):
    return img.filter(ImageFilter.EMBOSS)

def filterfindedges(img):
    return img.filter(ImageFilter.FIND_EDGES)

def filtersharpen(img):
    return img.filter(ImageFilter.SHARPEN)

def filtersmooth(img):
    return img.filter(ImageFilter.SMOOTH)

def filtersmoothmore(img):
    return img.filter(ImageFilter.SMOOTH_MORE)

def filtermax(img, size=3):
    return img.filter(ImageFilter.MaxFilter(size))

def filtermin(img, size=3):
    return img.filter(ImageFilter.MinFilter(size))

def filtermedian(img, size=3):
    return img.filter(ImageFilter.MedianFilter(size))

def filterrank(img, size, rank):
    return img.filter(ImageFilter.RankFilter(size, rank))

def filtermode(img, size=3):
    return img.filter(ImageFilter.ModeFilter(size))

def filtergaussianblur(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius))

def filterunsharpmask(img, radius=2, percent=150, threshold=3):
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

def enhancebrightness(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def enhancecontrast(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def enhancecolor(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def enhancesharpness(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def grabimage(bbox=None):
    return ImageGrab.grab(bbox=bbox)

def grabclipboardimage():
    return ImageGrab.grabclipboard()

def getbbox(img):
    return img.getbbox()

def getbands(img):
    return img.getbands()

def getcolors(img, maxcolors=256):
    return img.getcolors(maxcolors)

def getextrema(img):
    return img.getextrema()

def getdata(img):
    return img.getdata()

def putdata(img, data):
    img.putdata(data)
    return img

def getpixel(img, xy):
    return img.getpixel(xy)

def putpixel(img, xy, value):
    img.putpixel(xy, value)
    return img

def draft(img, mode, size):
    img.draft(mode, size)
    return img

def histogram(img):
    return img.histogram()

def copy(img):
    return img.copy()

def show(img):
    img.show()
    return img

def save(img, path, format=None):
    img.save(path, format=format)
    return img

def isanimated(img):
    return getattr(img, "is_animated", False)

def nframes(img):
    return getattr(img, "n_frames", 1)

def seek(img, frame):
    img.seek(frame)
    return img

def tell(img):
    return img.tell()

def getexif(img):
    return getattr(img, "_getexif", lambda: None)()

def iterframes(img):
    return ImageSequence.Iterator(img)

def seekframe(img, frame):
    img.seek(frame)
    return img

def tellframe(img):
    return img.tell()

def copyframe(img):
    return img.copy()

def nframesimage(img):
    return getattr(img, "n_frames", 1)

def isanimatedimage(img):
    return getattr(img, "is_animated", False)

def appendframes(img, frames):
    img.info["append_images"] = frames
    return img

def setduration(img, duration):
    img.info["duration"] = duration
    return img

def getduration(img):
    return img.info.get("duration", 0)

def setloop(img, loop):
    img.info["loop"] = loop
    return img

def getloop(img):
    return img.info.get("loop", 0)

def getframe(img, index):
    img.seek(index)
    return img.copy()

def saveanimated(img, path, format=None, save_all=True, append_images=None, loop=0, duration=0):
    img.save(path, format=format, save_all=save_all, append_images=append_images, loop=loop, duration=duration)
    return img

def readpnginfo(img):
    return img.info

def setpnginfo(img, info):
    img.info.update(info)
    return img

def frombytes(mode, size, data, decoder_name="raw", *args):
    return Image.frombytes(mode, size, data, decoder_name, *args)

def frombuffer(mode, size, data, decoder_name="raw", *args):
    return Image.frombuffer(mode, size, data, decoder_name, *args)

def fromarray(obj, mode=None):
    return Image.fromarray(obj, mode)

def tobytes(img, encoder_name="raw", *args):
    return img.tobytes(encoder_name, *args)

def toarray(img):
    import numpy as np
    return np.array(img)

def crop(img, box):
    return img.crop(box)

def resize(img, size, resample=0):
    return img.resize(size, resample=resample)

def rotate(img, angle, resample=0, expand=0, center=None, translate=None, fillcolor=None):
    return img.rotate(angle, resample=resample, expand=expand, center=center, translate=translate, fillcolor=fillcolor)

def transpose(img, method):
    return img.transpose(method)

def convert(img, mode):
    return img.convert(mode)

def split(img):
    return img.split()

def merge(mode, bands):
    return Image.merge(mode, bands)

def paste(img, source, box=None, mask=None):
    img.paste(source, box, mask)
    return img

def getpixel(img, xy):
    return img.getpixel(xy)

def putpixel(img, xy, value):
    img.putpixel(xy, value)
    return img

def copy(img):
    return img.copy()

def show(img):
    img.show()
    return img

def save(img, path, format=None):
    img.save(path, format=format)
    return img

def getbands(img):
    return img.getbands()

def getcolors(img, maxcolors=256):
    return img.getcolors(maxcolors)

def getextrema(img):
    return img.getextrema()

def getdata(img):
    return img.getdata()

def putdata(img, data):
    img.putdata(data)
    return img

def histogram(img):
    return img.histogram()

def draft(img, mode, size):
    img.draft(mode, size)
    return img

def getexif(img):
    return getattr(img, "_getexif", lambda: None)()

def isanimated(img):
    return getattr(img, "is_animated", False)

def nframes(img):
    return getattr(img, "n_frames", 1)

def seek(img, frame):
    img.seek(frame)
    return img

def tell(img):
    return img.tell()

def autocontrast(img, cutoff=0, ignore=None):
    return ImageOps.autocontrast(img, cutoff=cutoff, ignore=ignore)

def equalize(img, mask=None):
    return ImageOps.equalize(img, mask=mask)

def solarize(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def posterize(img, bits):
    return ImageOps.posterize(img, bits)

def invert(img):
    return ImageOps.invert(img)

def flip(img):
    return ImageOps.flip(img)

def mirror(img):
    return ImageOps.mirror(img)

def expand(img, border=0, fill=0):
    return ImageOps.expand(img, border=border, fill=fill)

def cropborder(img, border):
    return ImageOps.crop(img, border)

def fit(img, size, method=3, bleed=0.0, centering=(0.5,0.5)):
    return ImageOps.fit(img, size, method=method, bleed=bleed, centering=centering)

def pad(img, size, method=3, color=0):
    return ImageOps.pad(img, size, method=method, color=color)

def scale(img, factor, resample=3):
    return ImageOps.scale(img, factor, resample=resample)

def exiftranspose(img):
    return ImageOps.exif_transpose(img)

def brightness(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def contrast(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def color(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def sharpness(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def draw(img):
    return ImageDraw.Draw(img)

def truetypefont(path, size):
    return ImageFont.truetype(path, size)

def loaddefaultfont():
    return ImageFont.load_default()

def newpalette(mode="RGB", color_list=None):
    pal = ImagePalette.ImagePalette(mode)
    if color_list:
        pal.palette = color_list
    return pal

def getpalette(img):
    return img.getpalette()

def putpalette(img, palette):
    img.putpalette(palette)
    return img

def getcolorspace(img):
    return getattr(img, "getcolorspace", lambda: None)()

def setcolorspace(img, mode):
    img.mode = mode
    return img

def getpalettecolors(img):
    return img.getcolors()

def copypalette(pal):
    return pal.copy()

def profile(img):
    return getattr(img, "info", {}).get("icc_profile", None)

def assignprofile(img, profile_bytes):
    img.info["icc_profile"] = profile_bytes
    return img

def buildtransform(img, matrix, filter=Image.BICUBIC):
    return img.transform(img.size, Image.AFFINE, matrix, resample=filter)

def filtermin(img, size=3):
    return img.filter(ImageFilter.MinFilter(size))

def filtermax(img, size=3):
    return img.filter(ImageFilter.MaxFilter(size))

def filtermedian(img, size=3):
    return img.filter(ImageFilter.MedianFilter(size))

def filtermode(img, size=3):
    return img.filter(ImageFilter.ModeFilter(size))

def filterrank(img, size, rank):
    return img.filter(ImageFilter.RankFilter(size, rank))

def filtergaussian(img, radius=2):
    return img.filter(ImageFilter.GaussianBlur(radius))

def filterunsharp(img, radius=2, percent=150, threshold=3):
    return img.filter(ImageFilter.UnsharpMask(radius=radius, percent=percent, threshold=threshold))

def convertmode(img, mode):
    return img.convert(mode)

def draftmode(img, mode, size):
    img.draft(mode, size)
    return img

def getformat(img):
    return img.format

def getformatdescription(img):
    return img.format_description

def getmode(img):
    return img.mode

def getsize(img):
    return img.size

def getinfo(img):
    return img.info

def getpaletteimg(img):
    return img.getpalette()

def putpaletteimg(img, palette):
    img.putpalette(palette)
    return img

def isanimatedimg(img):
    return getattr(img, "is_animated", False)

def nframesimg(img):
    return getattr(img, "n_frames", 1)

def seekimg(img, frame):
    img.seek(frame)
    return img

def tellimg(img):
    return img.tell()

def saveimg(img, path, format=None, **kwargs):
    img.save(path, format=format, **kwargs)
    return img

def showimg(img):
    img.show()
    return img

def copyimg(img):
    return img.copy()

def cropimg(img, box):
    return img.crop(box)

def resizeimg(img, size, resample=0):
    return img.resize(size, resample=resample)

def rotateimg(img, angle, resample=0, expand=0, center=None, translate=None, fillcolor=None):
    return img.rotate(angle, resample=resample, expand=expand, center=center, translate=translate, fillcolor=fillcolor)

def transposeimg(img, method):
    return img.transpose(method)

def splitimg(img):
    return img.split()

def mergeimg(mode, bands):
    return Image.merge(mode, bands)

def pasteimg(img, source, box=None, mask=None):
    img.paste(source, box, mask)
    return img

def getpixelimg(img, xy):
    return img.getpixel(xy)

def putpixelimg(img, xy, value):
    img.putpixel(xy, value)
    return img

def getbandsimg(img):
    return img.getbands()

def getcolorsimg(img, maxcolors=256):
    return img.getcolors(maxcolors)

def getextremaimg(img):
    return img.getextrema()

def getdataimg(img):
    return img.getdata()

def putdataimg(img, data):
    img.putdata(data)
    return img

def histogramimg(img):
    return img.histogram()

def getexifimg(img):
    return getattr(img, "_getexif", lambda: None)()

def brightnessimg(img, factor):
    return ImageEnhance.Brightness(img).enhance(factor)

def contrastimg(img, factor):
    return ImageEnhance.Contrast(img).enhance(factor)

def colorimg(img, factor):
    return ImageEnhance.Color(img).enhance(factor)

def sharpnessimg(img, factor):
    return ImageEnhance.Sharpness(img).enhance(factor)

def flipimg(img):
    return ImageOps.flip(img)

def mirrorimg(img):
    return ImageOps.mirror(img)

def invertimg(img):
    return ImageOps.invert(img)

def grayscaleimg(img):
    return ImageOps.grayscale(img)

def autocontrastimg(img, cutoff=0, ignore=None):
    return ImageOps.autocontrast(img, cutoff=cutoff, ignore=ignore)

def equalizeimg(img, mask=None):
    return ImageOps.equalize(img, mask=mask)

def solarizeimg(img, threshold=128):
    return ImageOps.solarize(img, threshold)

def posterizeimg(img, bits):
    return ImageOps.posterize(img, bits)

def expandimg(img, border=0, fill=0):
    return ImageOps.expand(img, border=border, fill=fill)

def cropborderimg(img, border):
    return ImageOps.crop(img, border)

def fitimg(img, size, method=3, bleed=0.0, centering=(0.5,0.5)):
    return ImageOps.fit(img, size, method=method, bleed=bleed, centering=centering)

def padimg(img, size, method=3, color=0):
    return ImageOps.pad(img, size, method=method, color=color)

def scaleimg(img, factor, resample=3):
    return ImageOps.scale(img, factor, resample=resample)

def exiftransposeimg(img):
    return ImageOps.exif_transpose(img)

def drawimg(img):
    return ImageDraw.Draw(img)

def truetype(img, path, size):
    return ImageFont.truetype(path, size)

def loaddefaultfontimg():
    return ImageFont.load_default()

def grabimg(bbox=None):
    return ImageGrab.grab(bbox=bbox)

def grabclipboardimg():
    return ImageGrab.grabclipboard()
