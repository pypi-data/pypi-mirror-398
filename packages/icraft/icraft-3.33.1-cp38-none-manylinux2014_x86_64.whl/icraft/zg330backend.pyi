"""
icraft zg330backend python interface
"""
from __future__ import annotations
import typing
import xir
import xrt
__all__ = ['BEST_SCORE', 'FTMP', 'ForwardInfo', 'HardOpInfo', 'INPUT', 'INSTR', 'LogicSegment', 'MemChunkInfo', 'NONE', 'OPTION1', 'OPTION2', 'OPTION3', 'OUTPUT', 'OcmOpt', 'PhySegment', 'SegmentType', 'ValueInfo', 'WEIGHT', 'ZG330Backend']
class ForwardInfo(xir.ObjectRef):
    """
    ZG330Backend前向所需要的信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::zg330::ForwardInfoNode'
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
        network_view包含的所有hardopInfo的集合: <op_id, HardOpInfo>
        """
    @property
    def idx_map(self) -> dict[int, tuple[int, int]]:
        """
        network_view中所有op的同步信息集合: <op_id, <sync_idx,layer_count>>
        """
    @property
    def memchunk_map(self) -> dict[int, MemChunkInfo]:
        """
        network_view中所有value对应的物理内存集合
        """
    @property
    def value_map(self) -> dict[int, ValueInfo]:
        """
        network_view包含的所有valueInfo的集合: <v_id, ValueInfo>
        """
class HardOpInfo(xir.ObjectRef):
    """
    和icraft::xir::hardop对应, 包含ZG330Backend中一些补充信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::zg330::HardOpInfoNode'
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
    def instr_logic_addr(self) -> int:
        """
        对应HardOp的指令在etm上分配的逻辑字节地址
        """
    @property
    def instr_phy_addr(self) -> int:
        """
        对应HardOp的指令在etm上的真实物理字节地址
        """
    @property
    def instr_size(self) -> int:
        """
        对应HardOp的指令在etm上分配的逻辑字节大小
        """
    @property
    def merge_from(self) -> list[int]:
        """
        如果在算子连贯执行模式下，表示合并前的hardop op_id集合
        """
    @property
    def net_hardop(self) -> xir.HardOp:
        """
        对应icraft::xir::HardOp类的指针
        """
    @property
    def sync_idx(self) -> tuple[int, int]:
        """
        对应HardOp的同步信息: <network_view_idx，layer_count>
        """
    @property
    def weight_phy_addr(self) -> int:
        """
        对应HardOp的权重在etm上的真实物理字节地址
        """
    @property
    def weights_logic_addr(self) -> int:
        """
        对应HardOp的权重在etm上分配的逻辑字节地址
        """
    @property
    def weights_size(self) -> int:
        """
        对应HardOp的权重在etm上的字节大小
        """
class LogicSegment(xir.ObjectRef):
    """
    在ZG330Backend初始化时生成，表示对应network_view的各分段的逻辑地址相关数据
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::zg330::LogicSegmentNode'
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
        逻辑分段在etm的字节大小
        """
    @property
    def hardop_map(self) -> dict[int, HardOpInfo]:
        """
        逻辑分段包含的hardOp信息: <op_id, hardopInfo>
        """
    @property
    def info_map(self) -> dict[int, ValueInfo]:
        """
        逻辑分段包含的valueInfo信息: <v_id, valueInfo>
        """
    @property
    def logic_addr(self) -> int:
        """
        逻辑分段在etm的逻辑字节地址
        """
    @property
    def segment_type(self) -> SegmentType:
        """
        逻辑分段的分段类型
        """
class MemChunkInfo(xir.ObjectRef):
    """
    物理内存类，表示物理分段中分配的内存相关数据
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::zg330::MemChunkInfoNode'
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> MemChunkInfo:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    @property
    def memChunk(self) -> xrt.MemChunk:
        """
        在etm/ocm上申请的memchunk
        """
    @property
    def staged_chunk(self) -> dict[int, xrt.MemChunk]:
        """
        用于输入/输出内存复用时无法直接复用同一块memchunk的情况
        """
    @property
    def user_used(self) -> bool:
        """
        若为true，表示对应的memchunk是用户申请的
        """
class OcmOpt:
    """
    OCM优化方案
    
    Members:
    
      NONE : 无
    
      OPTION1 : 方案一,全局评分法
    
      OPTION2 : 方案二,局部最优动态规划法
    
      OPTION3 : 方案三,顺序按评分踢出法
    
      BEST_SCORE : 选取三个方案中评分最优的一个
    """
    BEST_SCORE: typing.ClassVar[OcmOpt]  # value = <OcmOpt.BEST_SCORE: -1>
    NONE: typing.ClassVar[OcmOpt]  # value = <OcmOpt.NONE: 0>
    OPTION1: typing.ClassVar[OcmOpt]  # value = <OcmOpt.OPTION1: 1>
    OPTION2: typing.ClassVar[OcmOpt]  # value = <OcmOpt.OPTION2: 2>
    OPTION3: typing.ClassVar[OcmOpt]  # value = <OcmOpt.OPTION3: 3>
    __members__: typing.ClassVar[dict[str, OcmOpt]]  # value = {'NONE': <OcmOpt.NONE: 0>, 'OPTION1': <OcmOpt.OPTION1: 1>, 'OPTION2': <OcmOpt.OPTION2: 2>, 'OPTION3': <OcmOpt.OPTION3: 3>, 'BEST_SCORE': <OcmOpt.BEST_SCORE: -1>}
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
class PhySegment(xir.ObjectRef):
    """
    在ZG330Backend在apply部署后生成，表示对应network_view的各分段的真实物理地址相关数据
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::zg330::PhySegmentNode'
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
        物理分段在etm上的字节大小
        """
    @property
    def hardop_map(self) -> dict[int, HardOpInfo]:
        """
        物理分段包含的hardOp信息: <op_id, hardopInfo>
        """
    @property
    def info_map(self) -> dict[int, ValueInfo]:
        """
        物理分段包含的valueInfo信息: <v_id, valueInfo>
        """
    @property
    def multi_chunk(self) -> dict[int, MemChunkInfo]:
        """
        输入、输出分段根据value在etm上申请的多段memchunk: <v_id, MemChunkInfo>
        """
    @property
    def phy_addr(self) -> int:
        """
        物理分段在etm上的真实物理字节地址
        """
    @property
    def segment_type(self) -> SegmentType:
        """
        物理分段的分段类型
        """
    @property
    def single_chunk(self) -> MemChunkInfo:
        """
        权重、指令、中间层段在etm/ocm上申请的一段memchunk
        """
class SegmentType:
    """
    网络分段属性的枚举类
    
    Members:
    
      WEIGHT : 权重分段
    
      INSTR : 指令分段
    
      FTMP : 中间层分段
    
      INPUT : 输入分段
    
      OUTPUT : 输出分段
    """
    FTMP: typing.ClassVar[SegmentType]  # value = <SegmentType.FTMP: 2>
    INPUT: typing.ClassVar[SegmentType]  # value = <SegmentType.INPUT: 3>
    INSTR: typing.ClassVar[SegmentType]  # value = <SegmentType.INSTR: 1>
    OUTPUT: typing.ClassVar[SegmentType]  # value = <SegmentType.OUTPUT: 4>
    WEIGHT: typing.ClassVar[SegmentType]  # value = <SegmentType.WEIGHT: 0>
    __members__: typing.ClassVar[dict[str, SegmentType]]  # value = {'WEIGHT': <SegmentType.WEIGHT: 0>, 'INSTR': <SegmentType.INSTR: 1>, 'FTMP': <SegmentType.FTMP: 2>, 'INPUT': <SegmentType.INPUT: 3>, 'OUTPUT': <SegmentType.OUTPUT: 4>}
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
    和icraft::xir::value对应, 包含ZG330Backend中一些补充信息
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::zg330::ValueInfoNode'
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
        value占据的字节大小
        """
    @property
    def fake_from(self) -> xir.Value:
        """
        real若为false，必定存在预期共用etm地址且为true的value
        """
    @property
    def is_host(self) -> bool:
        """
        若为true，表示对应的value数据存放在host端
        """
    @property
    def is_ocm(self) -> bool:
        """
        若为true，表示对应的value数据存放在ocm上
        """
    @property
    def logic_addr(self) -> int:
        """
        value在etm/ocm分配的逻辑字节地址
        """
    @property
    def phy_addr(self) -> int:
        """
        value在etm/ocm分配的真实物理字节地址
        """
    @property
    def real(self) -> bool:
        """
        若为true，表示对应的value在etm/ocm上真实分配了地址；若为false表示，其地址与fake_from的value地址共用
        """
    @property
    def real_to(self) -> list[xir.Value]:
        """
        real若为true, 可能包含与其共用etm为false的value
        """
    @property
    def segment(self) -> SegmentType:
        """
        value对应的分段类型
        """
    @property
    def value(self) -> xir.Value:
        """
        获得对应的icraft::xir::value指针
        """
class ZG330Backend(xir.ObjectRef):
    """
    表示执行在ZG330芯片的后端
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::zg330::ZG330BackendNode'
    @staticmethod
    def Init() -> ZG330Backend:
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
    def clone(self, depth: int = 1) -> ZG330Backend:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def disableEtmOptimize(self) -> None:
        """
        				关闭etm内存回收
                        :note	在apply前调用
        """
    def disableMergeHardOp(self) -> None:
        """
        				关闭算子连贯执行模式
                        :note	在apply前调用
        """
    def log(self) -> None:
        """
        				生成ZG330Backend对应的log，log保存在 ${工作目录}/.icraft/logs/ 路径下
        """
    def ocmOptimize(self, option: OcmOpt) -> None:
        """
        				选择ocm优化方案，关闭ocm优化选择None
         
                        :param  option:		ocm优化方案
                        :note	在apply前调用
        """
    def precheck(self) -> bool:
        """
        				对ZG330Backend进行预检，会检查内存中的指令以及权重数据是否正确上传至etm指定地址
        				:return:			预检结果
        """
    def userConnectNetwork(self, memchunk: xrt.MemChunk, v_id: int) -> None:
        """
        				用户配置网络输入/输出数据段的memchunk，用于连接多网络在etm上的输入和输出
        				
                        :param  memchunk:		用户自行申请的 memchunk
                        :param  v_id:			网络中指定的value id
                        :note	在apply前调用
        """
    def userReuseSegment(self, memchunk: xrt.MemChunk, segment_type: SegmentType) -> None:
        """
        				用户配置网络权重/指令/中间层数据段的memchunk，用于复用数据或内存空间，减少多网络部署对etm的使用量
        				
                        :param  memchunk:		用户自行申请的 memchunk
                        :param  segment_type:	物理数据段phySegment的类型
                        :note	在apply前调用
        """
    @property
    def forward_info(self) -> ForwardInfo:
        """
        包含zg330backend的所有前向所需要信息
        """
    @property
    def is_applied(self) -> bool:
        """
        若为true, zg330backend已完成部署
        """
    @property
    def is_etmOptimize(self) -> bool:
        """
        若为true, zg330backend开启中间层内存回收
        """
    @property
    def is_mergeHardop(self) -> bool:
        """
        若为true，zg330backend开启算子连贯执行模式
        """
    @property
    def logic_segment_map(self) -> dict[SegmentType, LogicSegment]:
        """
        包含zg330backend的所有逻辑分段信息: <segment_type, logicSegment>
        """
    @property
    def ocmopt(self) -> OcmOpt:
        """
        使用的ocm优化方案，如果是使用BEST_SCORE，apply后更新为最后选择的方案
        """
    @property
    def phy_segment_map(self) -> dict[SegmentType, PhySegment]:
        """
        包含zg330backend的所有物理分段信息: <segment_type, phySegment>
        """
    @property
    def value_info(self) -> dict[int, ValueInfo]:
        """
        包含network_view所有valueInfo的信息: <v_id, ValueInfo>
        """
    @property
    def zg330backend_id(self) -> int:
        """
        当前zg330backend的id
        """
BEST_SCORE: OcmOpt  # value = <OcmOpt.BEST_SCORE: -1>
FTMP: SegmentType  # value = <SegmentType.FTMP: 2>
INPUT: SegmentType  # value = <SegmentType.INPUT: 3>
INSTR: SegmentType  # value = <SegmentType.INSTR: 1>
NONE: OcmOpt  # value = <OcmOpt.NONE: 0>
OPTION1: OcmOpt  # value = <OcmOpt.OPTION1: 1>
OPTION2: OcmOpt  # value = <OcmOpt.OPTION2: 2>
OPTION3: OcmOpt  # value = <OcmOpt.OPTION3: 3>
OUTPUT: SegmentType  # value = <SegmentType.OUTPUT: 4>
WEIGHT: SegmentType  # value = <SegmentType.WEIGHT: 0>
