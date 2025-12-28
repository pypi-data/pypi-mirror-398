"""
icraft xrt python interface
"""
from __future__ import annotations
import datetime
import io
import typing
import xir
__all__ = ['ADDR', 'BOTH', 'Backend', 'BuyiDevice', 'CPTR', 'Device', 'HostDevice', 'HostMemRegion', 'MemChunk', 'MemManager', 'MemPtr', 'MemRegion', 'PtrType', 'RegRegion', 'Session', 'Tensor', 'ZG330Device']
class Backend(xir.ObjectRef):
    """
    表示后端的类型
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::BackendNode'
    @staticmethod
    def Create(backend_type: type, network_view: xir.NetworkView, device: Device) -> Backend:
        """
        				创建指定类型的Backend.
        
        				:param	backend_type:	后端的类型
        				:param	network_view:	网络
        				:param	device:			设备
        """
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
    def apply(self) -> None:
        """
        应用Backend的一些选项
        """
    def clone(self, depth: int = 1) -> Backend:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def deinit(self) -> None:
        """
        				释放Backend.
        """
    def enableTimeProfile(self, enable: bool) -> None:
        """
        使能时间分析
        """
    def fork(self) -> Backend:
        """
        复制一个Backend用于多线程
        """
    def forwardOp(self, op: xir.Operation, inputs: list[Tensor], outputs: list[Tensor] = []) -> list[Tensor]:
        """
        				前向指定的算子.
        
        				:param	op:			指定的算子
        				:param	inputs:		输入的Tensors
        				:param	outputs:	输出的Tensors
        				:return:			前向的结果
        """
    def getForwardFunc(self, op: xir.Operation) -> typing.Callable[[xir.Operation, list[Tensor], list[Tensor], Backend], list[Tensor]] | None:
        """
        				获取指定算子的前向函数.
        
        				:param	op:			指定的算子
        				:return:			前向函数(Optional)
        """
    def getInitFunc(self, op: xir.Operation) -> typing.Callable[[xir.Operation, Backend], None] | None:
        """
        				获取指定算子的初始化函数.
        
        				:param	op:			指定的算子
        				:return:			初始化函数(Optional)
        """
    def init(self, network_view: xir.NetworkView, device: Device) -> None:
        """
        				初始化Backend.
        
        				:param	network_view:		网络
        				:param	device:				设备
        """
    def initOp(self, op: xir.Operation) -> None:
        """
        				初始化指定的算子.
        
        				:param	op:			指定的算子
        """
    def isOpSupported(self, op: xir.Operation) -> bool:
        """
        				检查指定算子是否被支持.
        
        				:param	op:			指定的算子
        				:return:			如果该算子被支持，后端有该算子的前向实现，则返回True
        """
    def setDevice(self, device: Device) -> Backend:
        """
        				为Backend绑定Device.
        
        				:param	device:			被绑定的Device
        """
    def setTimeElapses(self, op_id: int, memcpy_time: float, hard_time: float) -> None:
        """
        				记录指定算子的前向时间（用于Backend的TimeProfile实现）.
        
        				:param	op_id:			指定的Op ID
        				:param	memcpy_time:	数据复制时间
        				:param	hard_time:		硬件计算时间
        """
    @property
    def device(self) -> Device:
        """
        绑定到该后端的设备
        """
    @property
    def network_view(self) -> xir.NetworkView:
        """
        绑定到该后端的网络视图
        """
    @property
    def snapshot(self) -> bool:
        """
        是否是快照模式
        """
    @property
    def time_profile(self) -> bool:
        """
        是否开启时间分析
        """
class BuyiDevice(xir.ObjectRef):
    type_key: typing.ClassVar[str] = 'icraft::xrt::BuyiDeviceNode'
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def calcTime(self) -> float:
        """
        获取执行时间
        """
    def clkFreq(self) -> float:
        """
        获取运行频率
        """
    def clone(self, depth: int = 1) -> BuyiDevice:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def getRowsCols(self) -> tuple[int, int]:
        """
        获取设备使能的MPE的行数和列数
        """
    def icoreCalc(self, addr: int, size: int) -> None:
        """
        启动Icore计算
        """
    def layerCount(self) -> int:
        """
        获取当前的执行计数
        """
    def mmuModeSwitch(self, is_on配置mmu模式: bool) -> None:
        ...
    def modeInfo(self) -> int:
        """
        获取当前mmu模式状态
        """
    def readReg(self, cid: int, rid: int, offset: int) -> int:
        """
        获取设备使能的MPE的行数和列数
        """
    def setClkFreq(self, clk_freq: float) -> None:
        """
        设置运行频率
        """
    def setDType(self, dtype: int) -> None:
        """
        设置NPU计算的数据类型，是8位还是16位
        """
    def setEnabledMPE(self, rows: int, cols: int) -> None:
        """
        设置使能的MPE阵列
        """
    def updateBuffer(self, seg_table更新mmu段表: ...) -> None:
        ...
    def writeReg(self, cid: int, rid: int, offset: int, data: int) -> None:
        """
        写指定行列位置的寄存器
        """
class Device(xir.ObjectRef):
    """
    表示设备的类型
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::DeviceNode'
    @staticmethod
    def Close(device: Device) -> None:
        """
        				关闭设备.
        
        				:param	device:	被关闭的设备对象URL
        """
    @staticmethod
    def Open(url: str) -> Device:
        """
        				打开设备.
        
        				:param	url:	设备的URL
        				:return:		打开的设备对象
        """
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
    def check(self, level: int) -> bool:
        """
        				检查设备.
        				
        				:param level:	检查等级
        
        				Note:
        					不同的设备具有不同的定义和实现，详见具体设备的使用说明
        """
    def clone(self, depth: int = 1) -> Device:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def defaultMemRegion(self) -> MemRegion:
        """
        获取设备默认的MemRegion
        """
    def defaultRegRegion(self) -> RegRegion:
        """
        获取设备默认的RegRegion
        """
    def getMemRegion(self, name: str) -> MemRegion:
        """
        				根据名字获取设备的MemRegion.
        
        				:param name:	MemRegion的名字
        				:return:		相对应的MemRegion对象
        """
    def getRegRegion(self, name: str) -> RegRegion:
        """
        				根据名字获取设备的MemRegion.
        
        				:param name:	RegRegion的名字
        				:return:		相对应的RegRegion对象
        """
    @typing.overload
    def malloc(self, byte_size: int) -> MemChunk:
        """
        				在默认的MemRegion上申请分配内存.
        
        				:param byte_size:	申请的内存大小的名字
        				:return:			申请得到的MemChunk对象
        """
    @typing.overload
    def malloc(self, mem_region: str, byte_size: int) -> MemChunk:
        """
        				在指定的MemRegion上申请分配内存.
        
        				:param mem_region:	指定的MemRegion的名字
        				:param byte_size:	申请的内存大小
        				:return:			申请得到的MemChunk对象
        """
    @typing.overload
    def readReg(self, byte_size: int, relative: bool = False) -> int:
        """
        				在默认的RegRegion上读取寄存器.
        
        				:param addr:		读取的地址
        				:param relative:	是否以相对地址读取寄存器
        				:return:			读取得到的寄存器数据
        """
    @typing.overload
    def readReg(self, region_name: str, byte_size: int, relative: bool = False) -> int:
        """
        				在指定的的RegRegion上读取寄存器.
        
        				:param region_name:		指定的RegRegion的名字
        				:param addr:			读取的地址
        				:param relative:		是否以相对地址读取寄存器
        				:return:				读取得到的寄存器数据
        """
    def reset(self, level: int) -> None:
        """
        				复位设备.
        				
        				:param level:	复位等级
        
        				Note:
        					不同的设备具有不同的定义和实现，详见具体设备的使用说明
        """
    def setDefaultMemRegion(self, region_name: str) -> Device:
        """
        				将指定的MemRegion设置为默认MemRegion.
        
        				:param region_name:	指定的MemRegion名字
        """
    def setDefaultRegRegion(self, region_name: str) -> Device:
        """
        				将指定的MemRegion设置为默认MemRegion.
        
        				:param region_name:	指定的RegRegion名字
        """
    def setWaitTime(self, wait_time: int) -> None:
        """
        				设置同步tensor的最长等待时间
        				
        				:param wait_time:	等待时间，单位ms
        """
    def showStatus(self, level: int) -> None:
        """
        				显示设备状态.
        				
        				:param level:	状态等级
        
        				Note:
        					不同的设备具有不同的定义和实现，详见具体设备的使用说明
        """
    def version(self) -> dict[str, str]:
        """
        获取设备的版本
        """
    @typing.overload
    def writeReg(self, addr: int, data: int, relative: bool = False) -> None:
        """
        				将数据写入默认的RegRegion上的寄存器.
        
        				:param addr:		写入的地址
        				:param data:		写入的数据
        				:param relative:	是否以相对地址写入寄存器
        """
    @typing.overload
    def writeReg(self, region_name: str, addr: int, data: int, relative: bool = False) -> None:
        """
        				将数据写入指定的RegRegion上的寄存器.
        				
        				:param region_name:		指定的RegRegion的名字
        				:param addr:			写入的地址
        				:param data:			写入的数据
        				:param relative:		是否以相对地址写入寄存器
        """
class HostDevice(Device):
    @staticmethod
    def Default() -> HostDevice:
        """
        获取全局默认的HostDevice对象
        """
    @staticmethod
    def MemRegion() -> HostMemRegion:
        """
        获取全局默认的HostDevice的内存区域对象
        """
    def __init__(self) -> None:
        ...
class HostMemRegion(MemRegion):
    def __init__(self) -> None:
        ...
class MemChunk(xir.ObjectRef):
    """
    表示一块连续的内存块
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::MemChunkNode'
    @staticmethod
    def Init() -> MemChunk:
        """
        创建一个初始化(非空)对象
        """
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
    def clone(self, depth: int = 1) -> MemChunk:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def copyFrom(self, dest_offset: int, src_chunk: MemChunk, src_offset: int, byte_size: int) -> None:
        """
        				从其它MemChunk复制数据.
        
        				:param	dest_offset:	数据被写入的偏移位置
        				:param	src_chunk:		源MemChunk
        				:param	src_offset:		源偏移位置
        				:param	byte_size:		复制的字节大小
        """
    def free(self) -> None:
        """
        释放该MemChunk所占用的内存
        """
    def isOn(self, arg0: MemRegion) -> bool:
        """
        检查该MemChunk是否位于某个MemRegion上
        """
    def read(self, dest: typing_extensions.Buffer, src_offset: int, byte_size: int) -> None:
        """
        				读取指定偏移的数据.
        
        				:param	dest:		数据被读取到的位置
        				:param	src_offset:	从该偏移开始读取数据
        				:param	byte_size:	读取数据的字节大小
        """
    def write(self, dest_offset: int, src: typing_extensions.Buffer, byte_size: int) -> None:
        """
        				将数据写到指定偏移位置.
        
        				:param	dest_offset:	数据被写入的偏移位置
        				:param	src:			源数据
        				:param	byte_size:		写入数据的字节大小
        """
    @property
    def begin(self) -> MemPtr:
        """
        内存块开始的位置
        """
    @property
    def byte_size(self) -> int:
        """
        内存块的字节大小
        """
    @property
    def region(self) -> MemRegion:
        """
        内存块所在的内存区域
        """
class MemManager(xir.ObjectRef):
    """
    表示内存管理器的引用类型
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::MemManagerNode'
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def clone(self, depth: int = 1) -> MemManager:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def getAllMemChunk(self) -> list[...]:
        """
        				"获得当前已分配的所有MemChunk"
        """
    def getMemChunk(self, ptr: MemPtr, byte_size: int) -> ... | None:
        """
        				"获取指定的已分配内存"
        
        				:param ptr:			内存起始位置
        				:param byte_size:	内存大小
        				:return:			若指定起始位置和大小的内存存在，返回对应的MemChunk，否则返回nullopt
        """
    def getMemRegionInfo(self) -> dict[str, xir.ObjectRef]:
        """
        				"获得设备信息，不同设备保存的信息不同，详见具体设备的内存管理器使用说明"
        """
class MemPtr(xir.ObjectRef):
    """
    表示内存指针的引用类型
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::MemPtrNode'
    @staticmethod
    def Init() -> MemPtr:
        """
        创建一个初始化(非空)对象
        """
    @staticmethod
    def NullPtr() -> MemPtr:
        """
        				创建一个空指针.
        """
    def __add__(self, arg0: int) -> MemPtr:
        ...
    def __ge__(self, arg0: MemPtr) -> bool:
        ...
    def __gt__(self, arg0: MemPtr) -> bool:
        ...
    @typing.overload
    def __init__(self) -> None:
        """
        默认构造函数
        """
    @typing.overload
    def __init__(self, cptr: typing_extensions.Buffer, addr: int) -> None:
        """
        				构造函数，构造一个PtrType::BOTH类型的MemPtr.
        
        				:param cptr:	C指针的值
        				:param	addr:	物理地址的值
        """
    @typing.overload
    def __init__(self, cptr: typing_extensions.Buffer) -> None:
        """
        				构造函数，构造一个PtrType::CPTR类型的MemPtr.
        
        				:param cptr:	C指针的值
        """
    @typing.overload
    def __init__(self, addr: int) -> None:
        """
        				构造函数，构造一个PtrType::ADDR类型的MemPtr.
        
        				:param addr:	物理地址的值
        """
    @typing.overload
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def __le__(self, arg0: MemPtr) -> bool:
        ...
    def __lt__(self, arg0: MemPtr) -> bool:
        ...
    def __radd__(self, arg0: int) -> MemPtr:
        ...
    @typing.overload
    def __sub__(self, arg0: int) -> MemPtr:
        ...
    @typing.overload
    def __sub__(self, arg0: MemPtr) -> int:
        ...
    def addr(self) -> int:
        """
        				"获取该MemPtr的物理地址, 如果MemPtr为PtrType::CPTR类型时，抛出异常"
        """
    def clone(self, depth: int = 1) -> MemPtr:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def cptr(self) -> str:
        """
        				获取该MemPtr的C指针, 如果MemPtr为PtrType::ADDR类型时，抛出异常.
        """
    def isNull(self) -> bool:
        """
        				检查该MemPtr是否是空指针.
        """
    def ptype(self) -> PtrType:
        """
        获取该MemPtr的类型
        """
class MemRegion(xir.ObjectRef):
    """
    
    			表示内存区域的类
    			内存区域表示一块受管理的内存空间，比如NPU的PLDDR或者PS上的UDMABuf区域
    			
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::MemRegionNode'
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
    def clone(self, depth: int = 1) -> MemRegion:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def device(self) -> ...:
        """
        获取所在的Device
        """
    @typing.overload
    def malloc(self, byte_size: int, auto_free: bool = True, alignment: int = 1) -> ...:
        """
        				申请分配指定大小的内存.
        
        				:param	byte_size:	分配内存的大小
        				:param	auto_free:	指定分配的内存是否会被自动释放
        				:param	alignment:	指定分配的内存地址字节对齐
        """
    @typing.overload
    def malloc(self, begin: MemPtr, byte_size: int, deleter: typing.Callable[[MemPtr], None] = ..., auto_free: bool = True) -> ...:
        """
        				申请分配指定位置开始的内存.
        
        				:param	byte_size:	分配内存的大小
        				:param	deleter:	内存释放的自定义函数，若指定了Deleter，则调用该函数来释放内存
        				:param	auto_free:	指定分配的内存是否会被自动释放
        """
    def memManager(self) -> MemManager:
        """
        获取所属的MemManager
        """
class PtrType:
    """
    表示指针类型的枚举
    
    Members:
    
      CPTR : C指针
    
      ADDR : 物理地址
    
      BOTH : 既包含C指针，又包含物理地址
    """
    ADDR: typing.ClassVar[PtrType]  # value = <PtrType.ADDR: 1>
    BOTH: typing.ClassVar[PtrType]  # value = <PtrType.BOTH: 2>
    CPTR: typing.ClassVar[PtrType]  # value = <PtrType.CPTR: 0>
    __members__: typing.ClassVar[dict[str, PtrType]]  # value = {'CPTR': <PtrType.CPTR: 0>, 'ADDR': <PtrType.ADDR: 1>, 'BOTH': <PtrType.BOTH: 2>}
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
class RegRegion(xir.ObjectRef):
    """
    表示寄存器区域的类
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::RegRegionNode'
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
    def clone(self, depth: int = 1) -> RegRegion:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def device(self) -> ...:
        """
        获取该RegRegion所在的Device
        """
    def read(self, addr: int, relative: bool = False) -> int:
        """
        				读取指定地址的数据.
        
        				:param	addr:		读取的地址
        				:param	relative:	是否以相对地址读取数据
        				:return:			读取到的寄存器数据
        """
    def write(self, addr: int, data: int, relative: bool = False) -> None:
        """
        				将数据写入指定地址.
        
        				:param	addr:		写入的地址
        				:param	data:		写入的数据
        				:param	relative:	是否以相对地址写入数据
        """
class Session(xir.ObjectRef):
    """
    表示会话的类型
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::SessionNode'
    @staticmethod
    def Create(backend_types: list[type], network: xir.NetworkView, devices: list[Device]) -> Session:
        """
        				创建一个会话，按优先级绑定到指定的后端类型.
        
        				:param	backend_types:		会话绑定的后端类型列表
        				:param	network:			网络视图
        				:param	devices:			设备列表
        
        				Note:
        					设备列表中的Device和后端类型列表中的后端是一一对应的
        """
    @staticmethod
    def CreateByOrder(network: xir.NetworkView, backends: list[Backend], devices: list[Device]) -> Session:
        """
        				创建一个会话，按优先级绑定到指定的后端.
        
        				:param	network:		网络视图
        				:param	backends:		后端列表
        				:param	devices:		设备列表
        
        				Note:
        					设备列表中的Device和后端类型列表中的后端是一一对应的
        """
    @staticmethod
    def CreateWithBackends(network: xir.NetworkView, backends: list[Backend]) -> Session:
        """
        				创建一个会话，使用绑定好网络和设备的后端.
        
        				:param	network:		网络视图
        				:param	backends:		后端列表
        
        				Note:
        					backends中的后端均已绑定好了网络视图和后端，因此该方法创建Session时不再进行绑定
        """
    @staticmethod
    def CreateWithSnapshot(filePath: str, backends: list[type], devices: list[Device]) -> Session:
        """
        					根据二进制文件反序列化得到session
        
        					:param	filePath:	二进制文件保存路径
        					:param	backends:	后端列表
        					:param	devices:	设备列表
        """
    @staticmethod
    def Init() -> Session:
        """
        创建一个初始化(非空)对象
        """
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
    def apply(self) -> None:
        """
        应用Session的一些选项
        """
    def backendBindings(self) -> dict[int, Backend]:
        """
        				获取会话中所有算子的后端绑定关系.
        
        				:return:	dict[int, xrt.Backend]表示的算子后端绑定关系，其键为Op ID, 值为该算子绑定的后端
        """
    def clone(self, depth: int = 1) -> Session:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def dumpSnapshot(self, filePath: str) -> None:
        """
        					对当前session进行序列化得到二进制文件
        				
        					:params filePath:	二进制文件保存路径
        """
    def enableTimeProfile(self, enable: bool) -> None:
        """
        使能时间分析
        """
    @typing.overload
    def forward(self, inputs: list[Tensor]) -> list[Tensor]:
        """
        				前向会话中绑定的整个网络视图.
        
        				:param	inputs:		输入的Tensor列表
        				:return:			整个网络视图的前向结果
        				
        
        2. forward(self: xrt.Session, inputs: List[xrt.Tensor], outputs
        				前向会话中绑定的整个网络视图.
        
        				:param	inputs:		输入的Tensor列表
        				:param	outputs:	输出的Tensor列表
        				: List[xrt.Tensor]) -> None
        """
    def getForwards(self) -> list[tuple[xir.Operation, Backend, typing.Callable[[xir.Operation, list[Tensor], list[Tensor], Backend], list[Tensor]], list[int], list[int]]]:
        """
        				获取会话的前向算子列表
        				
        				:return:	前向算子列表
        """
    def setDumpOutputs(self, flag: bool, path: str, format: str) -> None:
        """
        				设置每层前向结束后是否保存输出结果至指定路径下，默认关闭
        				
        				:params flag:	开启标志
        				:params path:	保存输出结果路径
        				:params format:	指定的输出格式
        				
        				Note:
        
        					支持的格式由三个字母表示：
        
        					* 第一个字母表示排布，H表示硬件，S表示软件
        					* 第二个字母表示数值，F表示浮点，Q表示定点
        					* 第三个字母表示序列化形式，B表示二进制，T表示文本
        					
        					若一个Tensor原本的排布时H，那么可以转为S；若原本的数值为Q，那么可以转为F；反之不可
        """
    def setLogIO(self, flag: bool) -> None:
        """
        				设置每层前向结束后是否打印IO信息，默认关闭
        				
        				:params flag:	开启标志
        """
    def setLogTime(self, flag: bool) -> None:
        """
        				设置每层前向结束后是否打印耗时信息，默认关闭
        				
        				:params flag:	开启标志
        """
    def setPostCallBack(self, func: typing.Callable[[Session, xir.Operation, Backend, list[Tensor]], None]) -> None:
        """
        				为会话添加回调函数，该回调函数在会话前向之后执行
        				
        				:params func:	回调函数
        """
    def setPreCallBack(self, func: typing.Callable[[Session, xir.Operation, Backend, list[Tensor]], None]) -> None:
        """
        				为会话添加回调函数，该回调函数在会话前向之前执行
        				
        				:params func:	回调函数
        """
    def stepTo(self, op_id: int, inputs: list[Tensor] = []) -> list[Tensor]:
        """
        				前向到指定的算子.
        
        				:param	op_id:		指定算子的Op ID
        				:param	inputs:		输入的Tensor列表
        				:return:			指定算子的前向结果
        
        				Note:
        					只有在算子的输入来自外部时，才会取输入Tensor列表中的，否则使用生产者算子产生的Tensor
        """
    @typing.overload
    def sub(self, start_index: int, end_index: int) -> Session:
        """
        				从该session创建一个新的session, 共享相同的backends, 但是network_view不同.
        
        				:param	start_index:	NetworkView包含的算子在原网络中的开始索引(包含)，支持负数索引
        				:param	end_index:		NetworkView包含的算子在原网络中的结束索引(不包含)，支持负数索引
        				:return:	创建的session
        				
        
        2. sub(self: xrt.Session, start_index
        				从该session创建一个新的session, 共享相同的backends, 但是network_view不同.
        
        				:param	start_index:	NetworkView包含的算子在原网络中的开始索引(包含)，支持负数索引
        				:return:	创建的session
        				: int) -> xrt.Session
        """
    def timeProfileResults(self) -> dict[int, tuple[float, float, float, float]]:
        """
        				获取时间分析的结果.
        
        				:return:	Dict[int, Tuple[float, float, float, float]]表示的时间分析结果
        				
        				时间分析结果的键表示Op ID，值表示不同的时间类型，依次如下（单位：ms）：
        
        				* 总时间，即墙上时间
        				* 数据复制时间
        				* 硬件计算时间
        				* 其他时间
        """
    def totalTime(self) -> float:
        """
        获取会话总时间（单位：ms）
        """
    @property
    def backends(self) -> list[Backend]:
        """
        绑定到该session的后端
        """
    @property
    def network_view(self) -> xir.NetworkView:
        """
        会话中的网络视图
        """
class Tensor(xir.ObjectRef):
    """
    表示张量的类型
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::TensorNode'
    @staticmethod
    def Init() -> Tensor:
        """
        创建一个初始化(非空)对象
        """
    @typing.overload
    def __init__(self) -> None:
        """
        默认构造函数
        """
    @typing.overload
    def __init__(self, dtype: xir.TensorType, chunk: MemChunk, offset: int = 0, check_func: typing.Callable[[Device], bool] = None) -> None:
        """
        				构造函数.
        
        				:param	dtype:			数据类型
        				:param	chunk:			数据所在的内存块
        				:param	offset:			数据在内存块中的偏移
        				:param	check_func:		状态检查函数
        """
    @typing.overload
    def __init__(self, dtype: xir.TensorType) -> None:
        """
        				构造函数，构造一个没有数据的Tensor.
        
        				:param	dtype:			数据类型
        				
        
        4. __init__(self: xrt.Tensor, dtype: xir.TensorType, check_func
        				构造函数，构造一个没有数据的Tensor.
        
        				:param	dtype:			数据类型
        				:param	check_func:		状态检查函数
        				: Callable[[xrt.Device], bool]) -> None
        
        5. __init__(self: xrt.Tensor, value: xir.Value) -> None
        
        
        				构造函数，从xir.Value构造.
        				
        
        6. __init__(self: xrt.Tensor, b: buffer, layout: xir.Layout = <xir.Layout object at 0x7f221b4d59f0>) -> None
        
        
        				构造函数, 构造一个HostMemRegion上的Tensor, 从buffer推断数据类型并复制数据.
        
        				:param b:			python buffer
        				:param layout:		数据排布
        				
        
        7. __init__(self: xrt.Tensor, b: buffer, dtype: xir.TensorType) -> None
        
        
        				构造函数, 使用指定的数据类型, 构造一个HostMemRegion上的Tensor, 复制指定buffer的数据.
        
        				:param b:			python buffer
        				:param dtype:		数据类型
        				
        
        8. __init__(self: xrt.Tensor, arg0: xir.ObjectRef) -> None
        
        将父类强制转换为子类（该类型）
        """
    def chunk(self) -> MemChunk:
        """
        获取该Tensor数据所在的内存块
        """
    def clone(self, depth: int = 1) -> Tensor:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def copyData(self, b: typing_extensions.Buffer) -> None:
        """
        复制别的数据作为参数数据.
        """
    def copyFrom(self, dest_offset: int, src_tensor: Tensor, src_offset: int, byte_size: int) -> None:
        """
        				从指定的Tensor复制数据.
        
        				:param	dest_offset:	目标偏移位置
        				:param	src_tensor:		源Tensor
        				:param	src_offset:		源偏移位置
        				:param	byte_size:		字节大小
        """
    def data(self) -> MemPtr:
        """
        获取该Tensor数据的起始位置指针
        """
    def dtype(self) -> xir.TensorType:
        """
        获取该Tensor的数据类型
        """
    def dump(self, os: io.BytesIO, format: str = '') -> None:
        """
        				将Tensor的数据按指定格式导出到指定的输出流中.
        
        				:param	os:		指定的输出流
        				:param	format:	指定的输出格式
        
        				Note:
        
        					支持的格式由三个字母表示：
        
        					* 第一个字母表示排布，H表示硬件，S表示软件
        					* 第二个字母表示数值，F表示浮点，Q表示定点
        					* 第三个字母表示序列化形式，B表示二进制，T表示文本
        					
        					若一个Tensor原本的排布时H，那么可以转为S；若原本的数值为Q，那么可以转为F；反之不可
        """
    @typing.overload
    def fill(self, f: typing.Callable[[int], float]) -> Tensor:
        """
        填充数据
        """
    @typing.overload
    def fill(self, f: typing.Callable[[int], int]) -> Tensor:
        """
        填充数据
        """
    def hasData(self) -> bool:
        """
        检查该Tensor是否具有数据
        """
    def isOn(self, mregion: MemRegion) -> bool:
        """
        检查该Tensor是否在指定的MemRegion上
        """
    def isReady(self) -> bool:
        """
        检查该Tensor是否ready
        """
    def mallocOn(self, mregion: MemRegion) -> Tensor:
        """
        				在指定的MemRegion上分配Tensor所需要的内存.
        
        				:param	mregion:			指定的MemRegion
        				
        				Note:
        					如果Tensor已经分配了内存块，该方法会覆盖原有的内存块
        """
    def memRegion(self) -> MemRegion:
        """
        获取该Tensor所在的MemRegion
        """
    def offset(self) -> int:
        """
        获取该Tensor数据在内存块中的偏移
        """
    def read(self, dest: typing_extensions.Buffer, src_offset: int, byte_size: int) -> None:
        """
        				读取指定偏移的数据.
        
        				:param	dest:			读取到目标位置
        				:param	src_offset:		源偏移位置
        				:param	byte_size:		字节大小
        """
    def setCheckFunc(self, check_func: typing.Callable[[Device], bool]) -> Tensor:
        """
        				设置张量的数据检查函数.
        
        				:param	check_func:			状态检查函数
        """
    def setDType(self, dtype: xir.TensorType) -> Tensor:
        """
        				设置张量的数据类型.
        
        				:param	dtype:			数据类型
        """
    def setData(self, chunk: MemChunk, offset: int = 0) -> Tensor:
        """
        				设置张量数据所在的内存块.
        
        				:param	chunk:			数据所在内存块
        				:param	offset:			数据在内存块中的偏移
        """
    def setReady(self, ready: bool) -> Tensor:
        """
        				设置张量的的状态.
        
        				:param	ready:			状态是否ready
        """
    def to(self, mregion: MemRegion) -> Tensor:
        """
        				将Tensor复制到指定的MemRegion的上.
        
        				:param	mregion:	指定的MemRegion
        				:return:			在指定MemRegion复制得到的Tensor
        
        				Note:
        					如果该Tensor已经在指定的MemRegion上，则复制不会发生，而是直接返回原Tensor
        """
    def waitForReady(self, timeout: datetime.timedelta, sleep: datetime.timedelta = ...) -> bool:
        """
        				等待Tensor的状态ready.
        
        				:param	timeout:	等待的超时时间，超时则返回false
        				:param	sleep:		两次查询之间的休眠时间，默认为0
        				:return:			若timeout时间内查询到状态ready则返回true，否则返回false
        """
    def write(self, arg0: int, arg1: typing_extensions.Buffer, arg2: int) -> None:
        """
        				将数据写到指定偏移位置.
        
        				:param	dest_offset:	数据被写入的偏移位置
        				:param	src:			数据源
        				:param	byte_size:		字节大小
        """
class ZG330Device(xir.ObjectRef):
    type_key: typing.ClassVar[str] = 'icraft::xrt::ZG330DeviceNode'
    @typing.overload
    def __init__(self) -> None:
        ...
    @typing.overload
    def __init__(self, arg0: xir.ObjectRef) -> None:
        """
        将父类强制转换为子类（该类型）
        """
    def calcTime(self) -> float:
        """
        获取执行时间
        """
    def clone(self, depth: int = 1) -> ZG330Device:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def configProfiler(self, chunk: MemChunk) -> None:
        """
        配置Profiler的空间
        """
    def configTimer(self, chunk: MemChunk) -> None:
        """
        配置计时器的空间
        """
    def getRowsCols(self) -> tuple[int, int]:
        """
        获取设备使能的MPE的行数和列数
        """
    def icoreCalc(self, addr: int, size: int) -> None:
        """
        启动Icore计算
        """
    def layerCount(self) -> int:
        """
        获取当前的执行计数
        """
    def rTileCount(self, cid: int) -> int:
        """
        获取当前的读Tile计数
        """
    def readReg(self, cid: int, rid: int, offset: int) -> int:
        """
        获取设备使能的MPE的行数和列数
        """
    def setDDRClkFreq(self, freq_hz: int) -> None:
        """
        设置DDR的时钟频率(Hz)
        """
    def setIcoreClkFreq(self, freq_hz: int) -> None:
        """
        设置Icore的时钟频率(Hz)
        """
    def setMasterCID(self, master_cid: int) -> None:
        """
        设置master_cid
        """
    def showLayerTime(self, from_idx: int, op_cnt: int) -> None:
        """
        输出显示计时结果
        """
    def wTileCount(self, cid: int) -> int:
        """
        获取当前的写Tile计数
        """
    def writeReg(self, cid: int, rid: int, offset: int, data: int) -> None:
        """
        写指定行列位置的寄存器
        """
ADDR: PtrType  # value = <PtrType.ADDR: 1>
BOTH: PtrType  # value = <PtrType.BOTH: 2>
CPTR: PtrType  # value = <PtrType.CPTR: 0>
