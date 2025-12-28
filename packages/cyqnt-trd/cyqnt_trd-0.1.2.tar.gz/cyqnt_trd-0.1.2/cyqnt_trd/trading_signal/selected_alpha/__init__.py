"""
选币Alpha因子模块

包含用于选币的Alpha因子计算（101个WorldQuant Alpha因子）
"""

# 导入所有alpha因子函数
from .alpha1 import alpha1_factor
from .alpha2 import alpha2_factor
from .alpha3 import alpha3_factor
from .alpha4 import alpha4_factor
from .alpha5 import alpha5_factor
from .alpha6 import alpha6_factor
from .alpha7 import alpha7_factor
from .alpha8 import alpha8_factor
from .alpha9 import alpha9_factor
from .alpha10 import alpha10_factor
from .alpha11 import alpha11_factor
from .alpha12 import alpha12_factor
from .alpha13 import alpha13_factor
from .alpha14 import alpha14_factor
from .alpha15 import alpha15_factor
from .alpha16 import alpha16_factor
from .alpha17 import alpha17_factor
from .alpha18 import alpha18_factor
from .alpha19 import alpha19_factor
from .alpha20 import alpha20_factor
from .alpha21 import alpha21_factor
from .alpha22 import alpha22_factor
from .alpha23 import alpha23_factor
from .alpha24 import alpha24_factor
from .alpha25 import alpha25_factor
from .alpha26 import alpha26_factor
from .alpha27 import alpha27_factor
from .alpha28 import alpha28_factor
from .alpha29 import alpha29_factor
from .alpha30 import alpha30_factor
from .alpha31 import alpha31_factor
from .alpha32 import alpha32_factor
from .alpha33 import alpha33_factor
from .alpha34 import alpha34_factor
from .alpha35 import alpha35_factor
from .alpha36 import alpha36_factor
from .alpha37 import alpha37_factor
from .alpha38 import alpha38_factor
from .alpha39 import alpha39_factor
from .alpha40 import alpha40_factor
from .alpha41 import alpha41_factor
from .alpha42 import alpha42_factor
from .alpha43 import alpha43_factor
from .alpha44 import alpha44_factor
from .alpha45 import alpha45_factor
from .alpha46 import alpha46_factor
from .alpha47 import alpha47_factor
from .alpha48 import alpha48_factor
from .alpha49 import alpha49_factor
from .alpha50 import alpha50_factor
from .alpha51 import alpha51_factor
from .alpha52 import alpha52_factor
from .alpha53 import alpha53_factor
from .alpha54 import alpha54_factor
from .alpha55 import alpha55_factor
from .alpha56 import alpha56_factor
from .alpha57 import alpha57_factor
from .alpha58 import alpha58_factor
from .alpha59 import alpha59_factor
from .alpha60 import alpha60_factor
from .alpha61 import alpha61_factor
from .alpha62 import alpha62_factor
from .alpha63 import alpha63_factor
from .alpha64 import alpha64_factor
from .alpha65 import alpha65_factor
from .alpha66 import alpha66_factor
from .alpha67 import alpha67_factor
from .alpha68 import alpha68_factor
from .alpha69 import alpha69_factor
from .alpha70 import alpha70_factor
from .alpha71 import alpha71_factor
from .alpha72 import alpha72_factor
from .alpha73 import alpha73_factor
from .alpha74 import alpha74_factor
from .alpha75 import alpha75_factor
from .alpha76 import alpha76_factor
from .alpha77 import alpha77_factor
from .alpha78 import alpha78_factor
from .alpha79 import alpha79_factor
from .alpha80 import alpha80_factor
from .alpha81 import alpha81_factor
from .alpha82 import alpha82_factor
from .alpha83 import alpha83_factor
from .alpha84 import alpha84_factor
from .alpha85 import alpha85_factor
from .alpha86 import alpha86_factor
from .alpha87 import alpha87_factor
from .alpha88 import alpha88_factor
from .alpha89 import alpha89_factor
from .alpha90 import alpha90_factor
from .alpha91 import alpha91_factor
from .alpha92 import alpha92_factor
from .alpha93 import alpha93_factor
from .alpha94 import alpha94_factor
from .alpha95 import alpha95_factor
from .alpha96 import alpha96_factor
from .alpha97 import alpha97_factor
from .alpha98 import alpha98_factor
from .alpha99 import alpha99_factor
from .alpha100 import alpha100_factor
from .alpha101 import alpha101_factor

# 导出所有alpha因子函数
__all__ = [
    'alpha1_factor', 'alpha2_factor', 'alpha3_factor', 'alpha4_factor', 'alpha5_factor',
    'alpha6_factor', 'alpha7_factor', 'alpha8_factor', 'alpha9_factor', 'alpha10_factor',
    'alpha11_factor', 'alpha12_factor', 'alpha13_factor', 'alpha14_factor', 'alpha15_factor',
    'alpha16_factor', 'alpha17_factor', 'alpha18_factor', 'alpha19_factor', 'alpha20_factor',
    'alpha21_factor', 'alpha22_factor', 'alpha23_factor', 'alpha24_factor', 'alpha25_factor',
    'alpha26_factor', 'alpha27_factor', 'alpha28_factor', 'alpha29_factor', 'alpha30_factor',
    'alpha31_factor', 'alpha32_factor', 'alpha33_factor', 'alpha34_factor', 'alpha35_factor',
    'alpha36_factor', 'alpha37_factor', 'alpha38_factor', 'alpha39_factor', 'alpha40_factor',
    'alpha41_factor', 'alpha42_factor', 'alpha43_factor', 'alpha44_factor', 'alpha45_factor',
    'alpha46_factor', 'alpha47_factor', 'alpha48_factor', 'alpha49_factor', 'alpha50_factor',
    'alpha51_factor', 'alpha52_factor', 'alpha53_factor', 'alpha54_factor', 'alpha55_factor',
    'alpha56_factor', 'alpha57_factor', 'alpha58_factor', 'alpha59_factor', 'alpha60_factor',
    'alpha61_factor', 'alpha62_factor', 'alpha63_factor', 'alpha64_factor', 'alpha65_factor',
    'alpha66_factor', 'alpha67_factor', 'alpha68_factor', 'alpha69_factor', 'alpha70_factor',
    'alpha71_factor', 'alpha72_factor', 'alpha73_factor', 'alpha74_factor', 'alpha75_factor',
    'alpha76_factor', 'alpha77_factor', 'alpha78_factor', 'alpha79_factor', 'alpha80_factor',
    'alpha81_factor', 'alpha82_factor', 'alpha83_factor', 'alpha84_factor', 'alpha85_factor',
    'alpha86_factor', 'alpha87_factor', 'alpha88_factor', 'alpha89_factor', 'alpha90_factor',
    'alpha91_factor', 'alpha92_factor', 'alpha93_factor', 'alpha94_factor', 'alpha95_factor',
    'alpha96_factor', 'alpha97_factor', 'alpha98_factor', 'alpha99_factor', 'alpha100_factor',
    'alpha101_factor',
]

# 创建alpha因子字典，方便批量调用
ALPHA_FACTORS = {
    1: alpha1_factor, 2: alpha2_factor, 3: alpha3_factor, 4: alpha4_factor, 5: alpha5_factor,
    6: alpha6_factor, 7: alpha7_factor, 8: alpha8_factor, 9: alpha9_factor, 10: alpha10_factor,
    11: alpha11_factor, 12: alpha12_factor, 13: alpha13_factor, 14: alpha14_factor, 15: alpha15_factor,
    16: alpha16_factor, 17: alpha17_factor, 18: alpha18_factor, 19: alpha19_factor, 20: alpha20_factor,
    21: alpha21_factor, 22: alpha22_factor, 23: alpha23_factor, 24: alpha24_factor, 25: alpha25_factor,
    26: alpha26_factor, 27: alpha27_factor, 28: alpha28_factor, 29: alpha29_factor, 30: alpha30_factor,
    31: alpha31_factor, 32: alpha32_factor, 33: alpha33_factor, 34: alpha34_factor, 35: alpha35_factor,
    36: alpha36_factor, 37: alpha37_factor, 38: alpha38_factor, 39: alpha39_factor, 40: alpha40_factor,
    41: alpha41_factor, 42: alpha42_factor, 43: alpha43_factor, 44: alpha44_factor, 45: alpha45_factor,
    46: alpha46_factor, 47: alpha47_factor, 48: alpha48_factor, 49: alpha49_factor, 50: alpha50_factor,
    51: alpha51_factor, 52: alpha52_factor, 53: alpha53_factor, 54: alpha54_factor, 55: alpha55_factor,
    56: alpha56_factor, 57: alpha57_factor, 58: alpha58_factor, 59: alpha59_factor, 60: alpha60_factor,
    61: alpha61_factor, 62: alpha62_factor, 63: alpha63_factor, 64: alpha64_factor, 65: alpha65_factor,
    66: alpha66_factor, 67: alpha67_factor, 68: alpha68_factor, 69: alpha69_factor, 70: alpha70_factor,
    71: alpha71_factor, 72: alpha72_factor, 73: alpha73_factor, 74: alpha74_factor, 75: alpha75_factor,
    76: alpha76_factor, 77: alpha77_factor, 78: alpha78_factor, 79: alpha79_factor, 80: alpha80_factor,
    81: alpha81_factor, 82: alpha82_factor, 83: alpha83_factor, 84: alpha84_factor, 85: alpha85_factor,
    86: alpha86_factor, 87: alpha87_factor, 88: alpha88_factor, 89: alpha89_factor, 90: alpha90_factor,
    91: alpha91_factor, 92: alpha92_factor, 93: alpha93_factor, 94: alpha94_factor, 95: alpha95_factor,
    96: alpha96_factor, 97: alpha97_factor, 98: alpha98_factor, 99: alpha99_factor, 100: alpha100_factor,
    101: alpha101_factor,
}
