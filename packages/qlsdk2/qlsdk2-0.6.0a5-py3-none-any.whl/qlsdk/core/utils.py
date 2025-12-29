from bitarray import bitarray
from loguru import logger
# 通道数组[1,2,3,...]转换为bytes
def to_bytes(channels: list[int], upper=256) -> bytes:
    byte_len = int(upper / 8)
    channel = [0] * byte_len
    result = bitarray(upper)
    result.setall(0)
    for i in range(len(channels)):
        if channels[i] > 0 and channels[i] <= upper: 
            # 每个字节从低位开始计数
            m = (channels[i] - 1) % 8
            result[channels[i] + 6 - 2 * m] = 1
    return result.tobytes()

# 通道bytes转换为数组[1,2,3,...]
def to_channels(data: bytes) -> list[int]:
    ba = bitarray()
    ba.frombytes(data)
    channels = []
    for i in range(len(ba)):
        if ba[i] == 1:
            m = i % 8
            channels.append(i + 8 - 2 * m)
            
    channels.sort()
    return channels

def bytes_to_ints(b):
    """将小端字节序的3字节bytes数组转换为int数组"""
    if len(b) % 3 != 0:
        raise ValueError("输入的bytes长度必须是3的倍数")
    return [
        b[i] | (b[i + 1] << 8) | (b[i + 2] << 16)
        for i in range(0, len(b), 3)
    ]
    
def bytes_to_int(b: bytes) -> int:
    """将小端字节序的3字节bytes数组转换为int数组"""
    if len(b)  != 3:
        raise ValueError("输入的bytes长度必须是3的倍数")
    return b[0] | (b[1] << 8) | (b[2] << 16)
def bytes_to_ints2(b):
    """将小端字节序的3字节bytes数组转换为int数组"""
    if len(b) % 3 != 0:
        raise ValueError("输入的bytes长度必须是3的倍数")
    return [
        b[i] | (b[i + 1] << 8) | (b[i + 2] << 16)
        for i in range(0, len(b), 3)
    ]
   
import numpy as np 
if __name__ == "__main__":
    
    # channels = [1]
    # channels1 = [1, 2, 3, 4]
    # channels2 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46,47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64]
    # channels3 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86,87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119,120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145,146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176,177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207,208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238,239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256]
    # channels4 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63]
    # logger.info(to_bytes(channels).hex())
    # logger.info(to_bytes(channels1).hex())
    # logger.info(to_bytes(channels2).hex())
    # logger.info(to_bytes(channels3).hex())
    # logger.info(to_bytes(channels4).hex())
    
    # bs = 'ffffffffffffff7f000000000000000000000000000000000000000000000000'
    # bs1 = '8000000000000000000000000000000000000000000000000000000000000000'
    # bs2 = '0100000000000000000000000000000000000000000000000000000000000000'

    # logger.info(to_channels(bytes.fromhex(bs1)))
    # logger.info(to_channels(bytes.fromhex(bs2)))
    
    aa = 'ff3fff3fff3fff3f000000000000000000000000000000000000000000000000'
    
    logger.info(to_channels(bytes.fromhex(aa)))