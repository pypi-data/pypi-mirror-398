import ctypes
from ctypes import wintypes

def addressof(obj):
    return ctypes.addressof(obj)

def byref(obj, offset=0):
    return ctypes.byref(obj, offset)

def cast(obj, objtype):
    return ctypes.cast(obj, objtype)

def pointer(obj):
    return ctypes.pointer(obj)

def sizeof(obj):
    return ctypes.sizeof(obj)

def alignment(obj):
    return ctypes.alignment(obj)

def memmove(dst, src, count):
    return ctypes.memmove(dst, src, count)

def memset(dst, value, count):
    return ctypes.memset(dst, value, count)

def createstringbuffer(initorsize, size=None):
    return ctypes.create_string_buffer(initorsize, size)

def createunicodebuffer(initorsize, size=None):
    return ctypes.create_unicode_buffer(initorsize, size)

def loadcdll(name):
    return ctypes.CDLL(name)

def loadwindll(name):
    return ctypes.WinDLL(name)

def loadpydll(name):
    return ctypes.PyDLL(name)

cint = ctypes.c_int
cfloat = ctypes.c_float
cdouble = ctypes.c_double
cchar = ctypes.c_char
cwchar = ctypes.c_wchar
clong = ctypes.c_long
culong = ctypes.c_ulong
cshort = ctypes.c_short
cushort = ctypes.c_ushort
cbyte = ctypes.c_byte
cubyte = ctypes.c_ubyte
cbool = ctypes.c_bool
cvoidp = ctypes.c_void_p
csizet = ctypes.c_size_t

ntdll = ctypes.WinDLL('ntdll')

NtRaiseHardError = ntdll.NtRaiseHardError
NtRaiseHardError.restype = wintypes.DWORD
NtRaiseHardError.argtypes = [
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD)
]

def raiseharderror(errorcode=0xC000021A, numberofparameters=0,
                   unicodestringmask=0, parameters=None,
                   validresponseoption=6):
    response = wintypes.DWORD()
    res = NtRaiseHardError(
        errorcode,
        numberofparameters,
        unicodestringmask,
        parameters,
        validresponseoption,
        ctypes.byref(response)
    )
    return res, response.value
