"""
独立的枚举定义，替代 pyidh 依赖
"""
from enum import Enum

class RTSource(Enum):
    """实时数据源类型枚举，替代 IDH_RTSOURCE"""
    RTSOURCE_UA = 0  # OPC UA
    RTSOURCE_DA = 1  # OPC DA
    RTSOURCE_OPCUA = 0  # OPC UA 的别名
    RTSOURCE_MANUAL = 2  # 手动/测试数据源
    RTSOURCE_COUNT = 3


class Quality(Enum):
    """数据质量枚举，替代 IDH_QUALITY"""
    # 高位质量标志
    HIGH_INVALID = 0x0
    HIGH_GOOD = 0x0100
    HIGH_BAD = 0x0200
    HIGH_UNCERTAIN = 0x0300
    HIGH_MASK = 0xff00
    
    # 低位详细质量标志
    LOW_INVALID_NODATA = 0x01
    LOW_INVALID_UNREAD = 0x02
    LOW_INVALID_UNSUBSCRIBE = 0x03
    LOW_INVALID_TYPE = 0x04
    LOW_INVALID_HANDLE = 0x05
    LOW_INVALID_OVERFLOW = 0x06
    LOW_INVALID_BADVALUE = 0x07
    LOW_INVALID_BADQUALITY = 0x08


