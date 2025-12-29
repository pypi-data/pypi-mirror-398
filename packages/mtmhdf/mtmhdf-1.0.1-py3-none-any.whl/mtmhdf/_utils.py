import numpy as np
from numbers import Number

def int2binarystring(num: int, length: int = 0) -> str:
    return bin(num)[2:].zfill(length)

def bitoffset(data:np.ndarray | Number, bit_start_pos:int, bit_end_pos:int) -> np.ndarray | Number:
    # 左开右闭区间，即从bit_start_pos开始，到bit_end_pos结束，不包含bit_end_pos
    return (data >> bit_start_pos) % (2 ** (bit_end_pos - bit_start_pos))

def scale(data:np.ndarray | Number, scale_factor:Number=1, add_offset:Number=0) -> np.ndarray | Number:
    return data * scale_factor + add_offset

def mask(data:np.ndarray | Number, fill_value:Number) -> np.ma.MaskedArray:
    return np.ma.masked_values(data, fill_value, rtol=1e-8, atol=1e-9)