"""
icraft host_backend python interface
"""
from __future__ import annotations
import typing
import xir
import xrt
__all__ = ['Cast', 'CudaDevice', 'CudaMemRegion', 'DecodeWithDecoder', 'Ftmp2Tensor', 'HostBackend', 'Image2Tensor']
class CudaDevice(xrt.Device):
    @staticmethod
    def Default() -> CudaDevice:
        """
        获取全局默认的CudaDevice对象
        """
    @staticmethod
    def MemRegion() -> CudaMemRegion:
        """
        获取全局默认的CudaDevice的内存区域对象
        """
    def __init__(self) -> None:
        ...
class CudaMemRegion(xrt.MemRegion):
    def __init__(self) -> None:
        ...
class HostBackend(xrt.Backend):
    """
    表示Host类型的后端
    """
    type_key: typing.ClassVar[str] = 'icraft::xrt::HostBackendNode'
    @staticmethod
    def Init() -> HostBackend:
        """
        创建一个初始化(非空)对象
        """
    @staticmethod
    def getThreadsNum() -> int:
        """
        查询CPU前向推理时算子库自动启用的线程数.
        
        				:return int:		CPU前向推理时将启用的线程数
        """
    @staticmethod
    def setThreadsNum(num_threads: int) -> None:
        """
        				设置CPU前向推理时算子库自动启用的线程数, 默认值为4，在某些情况下占用过多资源会导致问题，需要手动降低线程数.
        
        				:param num_threads:     int变量，期望用于CPU推理加速的线程数
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
    def clone(self, depth: int = 1) -> HostBackend:
        """
        				克隆一份该对象
        				:param depth:	克隆的深度，默认为1，即浅克隆
        				:return:		克隆得到的新对象
        """
    def getFakeQf(self) -> bool:
        """
        获取fakeQF信息.
        
        				:return bool:		当前fakeQF状态
        """
    def setFakeQf(self, fakeQF: bool) -> None:
        """
        				修改fakeQF状态，默认状态为false。激活时定点前向过程中不进行截位和饱和操作，主要用于Adapted和Generated阶段的结果对比.
        
        				:param fakeQF:			bool变量，fakeQF设为ture或false
        """
def Cast(input: xrt.Tensor, input_type: xir.TensorType, output_type: xir.TensorType, backend: HostBackend) -> xrt.Tensor:
    """
    将input Tensor转化为output_type所对应的Tensor。
    
    			:param input:       输入Tensor
    			:param input_type:  输入Tensor的data type
    			:param output_type: 期望的Tensor data type
    			:param backend:     执行该操作的hostbackend
    """
def DecodeWithDecoder(dll_path: str, file_path: str, data_type: list[xir.TensorType]) -> list[xrt.Tensor]:
    """
    将数据文件使用用户提供的CustomDecoder模块解析为HostDevice上的Xrt Tensor。
    
    			:param dll_path:    dll或so路径
    			:param file_path:   数据文件路径
    			:param data_type:   输出Tensors的TensorTypes，表示Tensor信息
    			:return:            转自数据文件的Tensors			
    """
def Ftmp2Tensor(ftmp_path: str, value: xir.Value) -> xrt.Tensor:
    """
    将ftmp_path上的ftmp二进制文件的数据转化为value对应的Tensor。
    
    			:param ftmp_path:   ftmp文件路径
    			:param value:       ftmp对应的xir value
    			:return:            ftmp转化而来的Tensor
    """
@typing.overload
def Image2Tensor(img_path: str, height: int, width: int) -> xrt.Tensor:
    """
    将img_path上的图片初始化为一个IcraftTensor并把高和宽resize为height和width对应的数值。
    
    			:param img_path:    图片路径
    			:param height:      resize 高
    			:param width:       resize 宽
    			:return:            图片转化而来的Tensor
    """
@typing.overload
def Image2Tensor(img_path: str, value: xir.Value, bgr_order: bool) -> xrt.Tensor:
    """
    将img_path上的图片初始化为一个IcraftTensor并把高和宽resize为height和width对应的数值。
    
    			:param img_path:    图片路径
    			:param value:       图片对应的xir::Value
    			:param bgr_order:	图片读取格式
    			:return:            图片转化而来的Tensor
    """
