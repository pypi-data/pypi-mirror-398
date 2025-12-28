"""
icraft buyibackend python interface
"""
from __future__ import annotations
import typing
import xir
import xrt
__all__ = ['BuyiBackend', 'FTMP', 'ForwardInfo', 'HardOpInfo', 'INPUT', 'INSTR', 'LogicSegment', 'OUTPUT', 'PhySegment', 'Segment', 'ValueInfo', 'WEIGHT']
class BuyiBackend(xir.ObjectRef):
    """
    表示后端的类型
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::BuyiBackendNode'
    @staticmethod
    def Init() -> BuyiBackend:
        ...
    @typing.overload
    def __init__(self) -> None:
        """
        默认构造函数
        """
    @typing.overload
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> BuyiBackend:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def compressFtmp(self) -> None:
        """
        				开启中间层压缩
        """
    def getDeploySize(self) -> int:
        """
        				初始化指定的算子.
        				:return:			部署的字节大小
        """
    def log(self) -> None:
        """
        				输出逻辑地址和物理地址log
        """
    def precheck(self) -> bool:
        """
        				预检功能
        				:return:			预检的结果
        """
    def setUserSegment(self, memchunk: xrt.MemChunk, segment_type: Segment, offset: int = 0) -> None:
        """
        				用户配置网络数据段存放的memchunk
        				
                        :param  memchunk:		用户申请的memchunk
                        :param  segment_type	网络数据段的type
                        :param  offset          memchunk的偏移，数据会放到memchunk的首地址+偏移的位置
        """
    def speedMode(self) -> None:
        """
        				合并HardOp
        """
    @property
    def buyibackend_id(self) -> int:
        """
        绑定到该后端的buyibackend_id, 返回当前BuyiBackend id
        """
    @property
    def forward_info(self) -> ForwardInfo:
        """
        绑定到该后端的forward_info, 包含net_workview中前向所需要的信息forward_info
        """
    @property
    def is_applied_(self) -> bool:
        """
        绑定到该后端的is_applied_, 判断是否完成部署
        """
    @property
    def is_compressftmp_(self) -> bool:
        """
        绑定到该后端的is_compressftmp_, 判断是否开启中间层压缩
        """
    @property
    def logic_segment_map(self) -> dict[Segment, LogicSegment]:
        """
        绑定到该后端的logic_segment_map, 包含网络内存的逻辑分段 <segement_type, LogicSegment>
        """
    @property
    def phy_segment_map(self) -> dict[Segment, PhySegment]:
        """
        绑定到该后端的phy_segment_map, 包含网络内存的真实物理地址分段 <segement_type, PhySegment>
        """
    @property
    def value_info(self) -> dict[int, ValueInfo]:
        """
        绑定到该后端的value_info, 包含net_workview中所有ValueInfo <v_id, ValueInfo>
        """
    @property
    def value_list(self) -> list[xir.Value]:
        """
        绑定到该后端的value_list, 包含network_view 真实分配物理地址的value_info
        """
class ForwardInfo(xir.ObjectRef):
    """
    BuyiBackend前向时所需的信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::ForwardInfoNode'
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> ForwardInfo:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    @property
    def hardop_map(self) -> dict[int, HardOpInfo]:
        """
        绑定到该后端的hardop_map, 包含network_view中所有hardop_info的集合 <op_id, hardop_info>
        """
    @property
    def idx_map(self) -> dict[int, tuple[int, int]]:
        """
        绑定到该后端的idx_map, 包含net_workview中所有hardop的同步信息集合 <op_id, sync_idx>
        """
    @property
    def value_map(self) -> dict[int, ValueInfo]:
        """
        绑定到该后端的value_map, 包含network_view中所有value_info的集合 <v_id, value_info>
        """
class HardOpInfo(xir.ObjectRef):
    """
    和icraft::xir::hardop对应, 保存BuyiBackend的相关信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::HardOpInfoNode'
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> HardOpInfo:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    @property
    def instr_data(self) -> list[int]:
        """
        绑定到该后端的instr_data, 返回hardop对应的修改后的指令数据
        """
    @property
    def instr_logic_addr(self) -> int:
        """
        绑定到该后端的instr_logic_addr, 返回hardop指令在etm上的逻辑地址
        """
    @property
    def instr_logic_size(self) -> int:
        """
        绑定到该后端的instr_logic_size, 返回hardop指令在etm上的字节大小
        """
    @property
    def instr_phy_addr(self) -> int:
        """
        绑定到该后端的instr_phy_addr, 返回hardop指令在etm上的真实物理地址
        """
    @property
    def merge_from(self) -> list[int]:
        """
        绑定到该后端的merge_from, 返回hardop对应的合并前的算子op_id集合
        """
    @property
    def net_hardop(self) -> xir.HardOp:
        """
        绑定到该后端的net_hardop, 返回hardop对应的icraft::xir::hardop
        """
    @property
    def sync_idx(self) -> tuple[int, int]:
        """
        绑定到该后端的sync_idx, 返回hardop对应的同步信号
        """
    @property
    def user_used(self) -> bool:
        """
        绑定到该后端的user_used, 判断是否分配在用户申请的memchunk上
        """
    @property
    def weight_phy_addr(self) -> int:
        """
        绑定到该后端的weight_phy_addr, 返回hardop权重在etm上的真实物理地址
        """
    @property
    def weights_logic_addr(self) -> int:
        """
        绑定到该后端的weights_logic_addr, 返回hardop权重在etm上的逻辑地址
        """
    @property
    def weights_size(self) -> int:
        """
        绑定到该后端的weights_size, 返回hardop权重在etm上的字节大小
        """
class LogicSegment(xir.ObjectRef):
    """
    网络内存分段的逻辑地址信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::LogicSegmentNode'
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> LogicSegment:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    @property
    def byte_size(self) -> int:
        """
        绑定到该后端的byte_size, 返回logic_segment对应的字节大小
        """
    @property
    def hardop_map(self) -> dict[int, HardOpInfo]:
        """
        绑定到该后端的hardop_map, 返回logic_segment对应的hardopInfo map
        """
    @property
    def info_map(self) -> dict[int, ValueInfo]:
        """
        绑定到该后端的info_map, 返回logic_segment对应的valueInfo map
        """
    @property
    def logic_addr(self) -> int:
        """
        绑定到该后端的logic_addr, 返回logic_segment对应的逻辑地址
        """
    @property
    def segment_type(self) -> Segment:
        """
        绑定到该后端的segment_type, 返回logic_segment对应的网络分段属性
        """
class PhySegment(xir.ObjectRef):
    """
    网络内存分段的物理地址信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::PhySegmentNode'
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> PhySegment:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    @property
    def byte_size(self) -> int:
        """
        绑定到该后端的byte_size, 返回phy_segment对应的字节大小
        """
    @property
    def hardop_map(self) -> dict[int, HardOpInfo]:
        """
        绑定到该后端的hardop_map, 返回phy_segment对应的hardopInfo的map
        """
    @property
    def info_map(self) -> dict[int, ValueInfo]:
        """
        绑定到该后端的info_map, 返回phy_segment对应的valueInfo的map
        """
    @property
    def memchunk(self) -> xrt.MemChunk:
        """
        绑定到该后端的memchunk, 返回phy_segment对应的etm上的memchunk
        """
    @property
    def phy_addr(self) -> int:
        """
        绑定到该后端的phy_addr, 返回phy_segment真实物理地址
        """
    @property
    def segment_type(self) -> Segment:
        """
        绑定到该后端的segment_type, 返回phy_segment对应的网络分段属性
        """
    @property
    def user_used(self) -> bool:
        """
        绑定到该后端的user_used, 判断memchunk是否是用户申请的memchunk
        """
class Segment:
    """
    表示网络内存分段的类型
    
    Members:
    
      WEIGHT : 权重层
    
      INSTR : 指令层
    
      INPUT : 输入层
    
      OUTPUT : 输出层
    
      FTMP : 中间层
    """
    FTMP: typing.ClassVar[Segment]  # value = <Segment.FTMP: 4>
    INPUT: typing.ClassVar[Segment]  # value = <Segment.INPUT: 2>
    INSTR: typing.ClassVar[Segment]  # value = <Segment.INSTR: 1>
    OUTPUT: typing.ClassVar[Segment]  # value = <Segment.OUTPUT: 3>
    WEIGHT: typing.ClassVar[Segment]  # value = <Segment.WEIGHT: 0>
    __members__: typing.ClassVar[dict[str, Segment]]  # value = {'WEIGHT': <Segment.WEIGHT: 0>, 'INSTR': <Segment.INSTR: 1>, 'INPUT': <Segment.INPUT: 2>, 'OUTPUT': <Segment.OUTPUT: 3>, 'FTMP': <Segment.FTMP: 4>}
    def __eq__(self, other: typing.Any) -> bool:
        ...
    def __getstate__(self) -> int:
        ...
    def __hash__(self) -> int:
        ...
    def __index__(self) -> int:
        ...
    def __init__(self, value: int) -> None:
        ...
    def __int__(self) -> int:
        ...
    def __ne__(self, other: typing.Any) -> bool:
        ...
    def __repr__(self) -> str:
        ...
    def __setstate__(self, state: int) -> None:
        ...
    def __str__(self) -> str:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def value(self) -> int:
        ...
class ValueInfo(xir.ObjectRef):
    """
    和icraft::xir::value对应, 保存BuyiBackend的相关信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::ValueInfoNode'
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> ValueInfo:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    @property
    def byte_size(self) -> int:
        """
        绑定到该后端的byte_size, 返回value在etm上的字节大小
        """
    @property
    def fake_from(self) -> xir.Value:
        """
        绑定到该后端的fake_from, 返回对应没有指令为了优化存储共用地址的value_info
        """
    @property
    def is_host(self) -> bool:
        """
        绑定到该后端的is_host, 判断是否在host上
        """
    @property
    def is_ocm(self) -> bool:
        """
        绑定到该后端的is_ocm, 判断是否在ocm上
        """
    @property
    def logic_addr(self) -> int:
        """
        绑定到该后端的logic_addr, 返回value在etm上的逻辑地址
        """
    @property
    def phy_addr(self) -> int:
        """
        绑定到该后端的phy_addr, 返回value在etm上的实际物理地址
        """
    @property
    def real_to(self) -> list[xir.Value]:
        """
        绑定到该后端的real_to, 返回对应真实分配etm地址的valueInfo
        """
    @property
    def segment(self) -> Segment:
        """
        绑定到该后端的segment, 返回value在etm属于网络的分段类型
        """
    @property
    def user_used(self) -> bool:
        """
        绑定到该后端的user_used, 判断是否分配在用户申请的memchunk上
        """
    @property
    def value(self) -> xir.Value:
        """
        绑定到该后端的value
        """
FTMP: Segment  # value = <Segment.FTMP: 4>
INPUT: Segment  # value = <Segment.INPUT: 2>
INSTR: Segment  # value = <Segment.INSTR: 1>
OUTPUT: Segment  # value = <Segment.OUTPUT: 3>
WEIGHT: Segment  # value = <Segment.WEIGHT: 0>
