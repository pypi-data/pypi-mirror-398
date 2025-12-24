from pathlib import Path

boot = bytearray(512)
pointer = 0

def writeasm(byte_or_bytes):
    global pointer
    if isinstance(byte_or_bytes, int):
        boot[pointer] = byte_or_bytes
        pointer += 1
    else:
        for b in byte_or_bytes:
            boot[pointer] = b
            pointer += 1

def at(position):
    global pointer
    pointer = position

def showtext(text):
    for ch in text:
        write([0xB4, 0x0E])
        write([0xB0, ord(ch)])
        write([0xCD, 0x10])

def jumpto(address):
    offset = address & 0xFFFF
    seg = (address >> 4) & 0xFFFF
    write([0xEA])
    write([offset & 0xFF, (offset >> 8) & 0xFF])
    write([seg & 0xFF, (seg >> 8) & 0xFF])

def readsector(sector_num, into=0x7E00):
    es = (into >> 4) & 0xFFFF
    bx = into & 0xF
    write([0xB8, es & 0xFF, (es >> 8) & 0xFF])
    write([0x8E, 0xD8])
    write([0x8E, 0xC0])
    write([0xBE, bx & 0xFF, (bx >> 8) & 0xFF])
    write([0xB9, 0x01, 0x00])
    write([0xBA, sector_num & 0xFF, (sector_num >> 8) & 0xFF])
    write([0xB8, 0x02, 0x00])
    write([0xCD, 0x13])

def infiniteloop():
    write([0xEB, 0xFE])

def saveas(filename="bootloader.asm"):
    boot[510] = 0x55
    boot[511] = 0xAA
    Path(filename).write_bytes(boot)
    print(f"Saved: {filename}")
