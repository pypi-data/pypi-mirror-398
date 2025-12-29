from .crctools import crc16

# packet crc validate
def check_crc(data):
    return int.from_bytes(data[-2:], 'little')  == crc16(data[:-2])