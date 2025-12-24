import torch
from PIL import Image
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import matplotlib.pyplot as plt
import torch.nn.functional as F

def imageblur():
    kernel = torch.ones(1, 1, 5, 5) / 25
    image = torch.rand(1, 1, 128, 128)
    blurred = F.conv2d(image, kernel, padding=2)
    return blurred

def convert1d(inputtensor, weight, bias=None, shide=1, padding=0, dilation=1, groups=1):
    return F.conv1d(inputtensor, weight, bias=bias, shide=shide, padding=padding, dilation=dilation, groups=groups)

def convert2d(inputtensor, weight, bias=None, shide=1, padding=0, dilation=1, groups=1):
    return F.conv2d(inputtensor, weight, bias=bias, shide=shide, padding=padding, dilation=dilation, groups=groups)

def convert3d(inputtensor, weight, bias=None, shide=1, padding=0, dilation=1, groups=1):
    return F.conv3d(inputtensor, weight, bias=bias, shide=shide, padding=padding, dilation=dilation, groups=groups)

def converttranspose3d(inputtensor, weight, bias=None, outputpadding=0, padding=0, dilation=1, groups=1):
    return F.conv_transpose3d(inputtensor, weight, bias=bias, output_padding=outputpadding, padding=padding, dilation=dilation, groups=groups)

def converttranspose2d(inputtensor, weight, bias=None, outputpadding=0, padding=0, dilation=1, groups=1):
    return F.conv_transpose2d(inputtensor, weight, bias=bias, output_padding=outputpadding, padding=padding, dilation=dilation, groups=groups)

def converttranspose1d(inputtensor, weight, bias=None, outputpadding=0, padding=0, dilation=1, groups=1):
    return F.conv_transpose1d(inputtensor, weight, bias=bias, output_padding=outputpadding, padding=padding, dilation=dilation, groups=groups)

def unfold(inputtensor, kernelsize, dilation=1, padding=0, stride=1):
    return F.unfold(inputtensor, kernelsize, dilation=1, padding=0, stride=1)

def fold(inputtensor, outputsize, kernelsize, dilation=1, padding=0, stride=1):
    return f.fold(inputtensor, outputsize, kernelsize, dilation=1, padding=0, stride=1)

def torchones(*size, out=None, dtype=None, layout=torch.strided, device=None, requiresgrad=False):
    return torch.ones(*size, out=out, dtype=dtype, layout=layout, device=device, requiresgrad=requiresgrad)

def torchrandom(*size, generator=None, out=None, dtype=None, layout=torch.strided, device=None, requiresgrad=False, pinmemory=False):
    return torch.rand(*size, generator=generator, out=out, dtype=dtype, layout=layout, device=device, requires_grad=requiresgrad, pin_memory=pinmemory)

strided = torch.strided

def saveresultimage(result, resultimagename):
    result.save(resultimagename)

def stylizeimageto(image, style='green', alpha=1.0):
    model = hub.load("https://tfhub.dev/google/magenta/arbitrary-image-stylization-v1-256/2")

    def loadimage(image, size=256):
        img = tf.io.read_file(image)
        img = tf.image.decode_image(img, channels=3)
        img = tf.image.convert_image_dtype(img, tf.float32)
        img = tf.image.resize(img, (size, size))
        img = img[tf.newaxis, :]
        return img

    def makestyleimage(image, style):
        hsvimage = tf.image.rgb_to_hsv(image)
        if style == 'redrose':
            hueshift = -0.15
        elif style == 'warm':
            hueshift = 0.071
        elif style == 'green':
            hueshift = 0.2
        elif style == 'cold':
            hueshift = 0.4
        elif style == 'similar':
            hueshift = 0.01
        else:
            raise ValueError("The argument 'style' must be 'similar', 'redrose', 'warm', 'green' or 'cold'.")

        hsvimage = hsvimage + hueshift
        hsvimage = tf.math.mod(hsvimage, 1.0)
        
        return tf.image.hsv_to_rgb(hsvimage)

    def stylize(image, style, alpha):
        contentimage = loadimage(image)
        styleimage = makestyleimage(contentimage, style)
    
        stylized = model(contentimage, styleimage)[0]
    
        output = alpha * stylized + (1 - alpha) * contentimage
        output = tf.clip_by_value(output, 0.0, 1.0)
    
        return output

    return stylize(image, style, alpha)

def shapeof(theobject):
    return theobject.shape
