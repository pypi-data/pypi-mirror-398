from multiprocessing import shared_memory
import struct
import sys
import ctypes

TYPE_INT = 1
TYPE_FLOAT = 2
TYPE_STR = 3
TOTAL_SIZE = 64
MAX_DATA_SIZE = 60

class createurml:
    def __init__(self, varname, vardata):
        if isinstance(vardata, int):
            code = TYPE_INT
            data_bytes = struct.pack("i", vardata)
        elif isinstance(vardata, float):
            code = TYPE_FLOAT
            data_bytes = struct.pack("f", vardata)
        elif isinstance(vardata, str):
            code = TYPE_STR
            encoded_str = vardata.encode('utf-8')
            if len(encoded_str) > MAX_DATA_SIZE:
                return
            data_bytes = encoded_str.ljust(MAX_DATA_SIZE, b'\0')
        else:
            return

        try:
            self.shm = shared_memory.SharedMemory(create=True, size=TOTAL_SIZE, name=varname)
        except:
            return

        self.varname = varname
        self.shm.buf[:4] = struct.pack("i", code)
        self.shm.buf[4:4 + len(data_bytes)] = data_bytes

    @staticmethod
    def getvalue(varname):
        try:
            shm = shared_memory.SharedMemory(name=varname)
        except FileNotFoundError:
            return None

        code = struct.unpack("i", shm.buf[:4])[0]
        if code == TYPE_INT:
            value = struct.unpack("i", shm.buf[4:8])[0]
        elif code == TYPE_FLOAT:
            value = struct.unpack("f", shm.buf[4:8])[0]
        elif code == TYPE_STR:
            raw = bytes(shm.buf[4:4 + MAX_DATA_SIZE]).rstrip(b'\0')
            value = raw.decode('utf-8')
        else:
            value = None
        shm.close()
        return value

def createsharedmemory(size, name, create=True):
    shm = shared_memory.SharedMemory(create=create if create else False, size=size, name=name)
    return shm

def closesharedmemory(shmvar):
    return shmvar.close()

def unlinksharedmemory(shmvar):
    return shmvar.unlink()

def packfromstruct(topack, *args):
    return struct.pack(topack, *args)

def unpackfromstruct(tounpack, *args):
    return struct.unpack(tounpack, *args)

def packinto(topackinto, *args):
    return struct.pack_into(topackinto, *args)

def unpackinto(tounpackinto, *args):
    return struct.unpack_into(tounpackinto, *args)

class createpointer:
    def __init__(self, pointername, pointerdata):
        self.pointername = pointername
        if isinstance(pointerdata, int):
            self._data = ctypes.c_longlong(pointerdata)
        elif isinstance(pointerdata, float):
            self._data = ctypes.c_float(pointerdata)
        elif isinstance(pointerdata, str):
            self._data = ctypes.create_string_buffer(pointerdata.encode('utf-8'))
        else:
            raise TypeError("Unsupported type.")
        
        self.ptr = ctypes.pointer(self._data)

    def getaddress(self):
        return f"""0x{ctypes.addressof(self.ptr.contents)}"""

    def getdata(self):
        if isinstance(self._data, ctypes.Array):
            return self.ptr.contents.value.decode('utf-8')
        return self.ptr.contents.value

    def setdata(self, value):
        if isinstance(self._data, ctypes.Array):
            self._data.value = value.encode('utf-8')
        else:
            self.ptr.contents.value = value

    def togglebit(self, whichbit):
        if not isinstance(self._data, (ctypes.c_longlong, ctypes.c_int)):
            raise TypeError("Bit operations are only supported for integers.")
        val = self.getdata()
        val ^= (1 << (whichbit - 1))
        self.setdata(val)

    def modifybit(self, whichbit, replacedvalue):
        if not isinstance(self._data, (ctypes.c_longlong, ctypes.c_int)):
            raise TypeError("Bit operations are only supported for integers.")
    
        if replacedvalue not in (0, 1):
            raise ValueError("replacedvalue must be 0 or 1.")

        val = self.getdata()
    
        if replacedvalue == 1:
            val |= (1 << (whichbit - 1))
        else:
            val &= ~(1 << (whichbit - 1))
    
        self.setdata(val)
