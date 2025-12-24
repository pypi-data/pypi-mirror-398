import qrcode

def qrcode(text, filename):
    img = qrcode.make(text)
    img.save(filename)
    return filename
