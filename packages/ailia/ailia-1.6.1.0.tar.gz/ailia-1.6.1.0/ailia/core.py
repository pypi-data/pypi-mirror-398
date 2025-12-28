#### python binding of ailia : core implementation ####

import ctypes
import os
import sys
from enum import Enum

import numpy
import platform

from .const import *


#### dependency check
if sys.platform == "win32":
    import ctypes
    try:
        for library in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]:
            ctypes.windll.LoadLibrary(library)
    except:
        print("  WARNING Please install MSVC 2015-2019 runtime from https://docs.microsoft.com/ja-jp/cpp/windows/latest-supported-vc-redist")


#### loading DLL / DYLIB / SO  ####
if sys.platform == "win32":
    dll_platform = "windows/x64"
    dll_name = "ailia.dll"
    load_fn = ctypes.WinDLL
elif sys.platform == "darwin":
    dll_platform = "mac"
    dll_name = "libailia.dylib"
    load_fn = ctypes.CDLL
else:
    is_arm = "arm" in platform.machine() or platform.machine() == "aarch64"
    if is_arm:
        if platform.architecture()[0] == "32bit":
            dll_platform = "linux/armeabi-v7a"
        else:
            dll_platform = "linux/arm64-v8a"
    else:
        dll_platform = "linux/x64"
    dll_name = "libailia.so"
    load_fn = ctypes.CDLL

dll_found = False
candidate = ["", str(os.path.dirname(os.path.abspath(__file__))) + str(os.sep), str(os.path.dirname(os.path.abspath(__file__))) + str(os.sep) + dll_platform + str(os.sep)]
for dir in candidate:
    try:
        dll = load_fn(dir + dll_name)
        dll_found = True
    except:
        pass
if not dll_found:
    msg = "DLL load failed : \'" + dll_name + "\' is not found"
    raise ImportError(msg)


#### data structure definition ####

# AILIAShape
class Shape(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_uint),
        ("y", ctypes.c_uint),
        ("z", ctypes.c_uint),
        ("w", ctypes.c_uint),
        ("dim", ctypes.c_uint)]
    VERSION = ctypes.c_uint(1)

# AILIAEnvironment


class Environment(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("type", ctypes.c_int),
        ("name", ctypes.c_char_p),
        ("backend", ctypes.c_int),
        ("props", ctypes.c_int)]
    VERSION = ctypes.c_uint(2)
    TYPE_CPU = ctypes.c_int(0)
    TYPE_BLAS = ctypes.c_int(1)
    TYPE_GPU = ctypes.c_int(2)
    BACKEND_NONE = ctypes.c_int(0)
    BACKEND_CUDA = ctypes.c_int(2)
    BACKEND_MPS = ctypes.c_int(3)
    BACKEND_VULKAN = ctypes.c_int(6)

    PROPERTY_NORMAL = ctypes.c_int(0)
    PROPERTY_LOWPOWER = ctypes.c_int(1)
    PROPERTY_FP16 = ctypes.c_int(2)
    PROPERTY_INT8 = ctypes.c_int(4)
    PROPERTY_INT16 = ctypes.c_int(8)

    def get_type_string(self):
        if self.type == self.TYPE_CPU.value:
            return 'CPU'
        elif self.type == self.TYPE_BLAS.value:
            return 'BLAS'
        elif self.type == self.TYPE_GPU.value:
            return 'GPU'
        else:
            return 'UNKNOWN'

    def get_backend_string(self):
        if self.backend == self.BACKEND_NONE.value:
            return 'NONE'
        elif self.backend == self.BACKEND_CUDA.value:
            return 'CUDA'
        elif self.backend == self.BACKEND_MPS.value:
            return 'MPS'
        elif self.backend == self.BACKEND_VULKAN.value:
            return 'VULKAN'
        else:
            return 'UNKNOWN'

    def get_props_list(self):
        r = []
        if (self.props & self.PROPERTY_LOWPOWER.value) != 0:
            r.append('LOWPOWER')
        if (self.props & self.PROPERTY_FP16.value) != 0:
            r.append('FP16')
        elif (self.props & self.PROPERTY_INT8.value) != 0:
            r.append('INT8')
        elif (self.props & self.PROPERTY_INT16.value) != 0:
            r.append('INT16')
        return r

# AILIADetectorObject


class DetectorObject(ctypes.Structure):
    _fields_ = [
        ("category", ctypes.c_uint),
        ("prob", ctypes.c_float),
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("w", ctypes.c_float),
        ("h", ctypes.c_float)]
    VERSION = ctypes.c_uint(1)

# AILIAClassifierClass


class ClassifierClass(ctypes.Structure):
    _fields_ = [
        ("category", ctypes.c_int),
        ("prob", ctypes.c_float)]
    VERSION = ctypes.c_uint(1)

# Taken from library/Util/Protobufmodel/OnnxTensorDataType.h
class DataType(Enum):
    UNDEFINED = 0

    FLOAT = 1
    UINT8 = 2
    INT8 = 3
    UINT16 = 4
    INT16 = 5
    INT32 = 6
    INT64 = 7
    BOOL = 9
    FLOAT16 = 10

    DOUBLE = 11
    UINT32 = 12
    UINT64 = 13
    BFLOAT16 = 16

DataTypeToDtype = {
    DataType.FLOAT: numpy.float32,
    DataType.UINT8: numpy.uint8,
    DataType.INT8: numpy.int8,
    DataType.UINT16: numpy.uint16,
    DataType.INT16: numpy.int16,
    DataType.INT32: numpy.int32,
    DataType.INT64: numpy.int64,
    DataType.BOOL: numpy.bool_,
    DataType.FLOAT16: numpy.float16,

    DataType.DOUBLE: numpy.double,
    DataType.UINT32: numpy.uint32,
    DataType.UINT64: numpy.uint64,

    # bfloat16 is not existed in numpy
    # DataType.BFLOAT16: numpy.?,
 }

#### API IO specification ####


# ailiaCreate
dll.ailiaCreate.restype = ctypes.c_int
dll.ailiaCreate.argtypes = (
    ctypes.POINTER(ctypes.c_void_p),  # net
    ctypes.c_int,                    # env_id
    ctypes.c_int,                    # num_thread
)

# ailiaDestroy
dll.ailiaDestroy.restype = None
dll.ailiaDestroy.argtypes = (
    ctypes.c_void_p,                 # net
)

# ailiaOpenStreamFile
dll.ailiaOpenStreamFileW.restype = ctypes.c_int
dll.ailiaOpenStreamFileW.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_wchar_p,                # path
)
dll.ailiaOpenStreamFileA.restype = ctypes.c_int
dll.ailiaOpenStreamFileA.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_char_p,                 # path
)

# ailiaOpenStreamMem
dll.ailiaOpenStreamMem.restype = ctypes.c_int
dll.ailiaOpenStreamMem.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint8, flags='CONTIGUOUS'
    ),                               # buf
    ctypes.c_uint,                   # buf_size
)

# ailiaOpenWeightFile
dll.ailiaOpenWeightFileW.restype = ctypes.c_int
dll.ailiaOpenWeightFileW.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_wchar_p,                # path
)
dll.ailiaOpenWeightFileA.restype = ctypes.c_int
dll.ailiaOpenWeightFileA.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_char_p,                 # path
)

# ailiaOpenWeightMem
dll.ailiaOpenWeightMem.restype = ctypes.c_int
dll.ailiaOpenWeightMem.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint8, flags='CONTIGUOUS'
    ),                               # buf
    ctypes.c_uint,                   # buf_size
)

# ailiaGetInputDim
dll.ailiaGetInputDim.restype = ctypes.c_int
dll.ailiaGetInputDim.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # dim
)

# ailiaGetInputShape
dll.ailiaGetInputShape.restype = ctypes.c_int
dll.ailiaGetInputShape.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(Shape),           # shape
    ctypes.c_uint,                   # version
)

# ailiaGetInputShapeND
dll.ailiaGetInputShapeND.restype = ctypes.c_int
dll.ailiaGetInputShapeND.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint32, flags='CONTIGUOUS'
    ),                               # shape
    ctypes.c_uint,                   # dim
)

# ailiaGetOutputDim
dll.ailiaGetOutputDim.restype = ctypes.c_int
dll.ailiaGetOutputDim.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # dim
)

# ailiaGetOutputShape
dll.ailiaGetOutputShape.restype = ctypes.c_int
dll.ailiaGetOutputShape.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(Shape),           # shape
    ctypes.c_uint,                   # version
)

# ailiaGetOutputShapeND
dll.ailiaGetOutputShapeND.restype = ctypes.c_int
dll.ailiaGetOutputShapeND.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint32, flags='CONTIGUOUS'
    ),                               # shape
    ctypes.c_uint,                   # dim
)

# ailiaSetInputShape
dll.ailiaSetInputShape.restype = ctypes.c_int
dll.ailiaSetInputShape.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(Shape),           # shape
    ctypes.c_uint,                   # version
)

# ailiaSetInputShapeND
dll.ailiaSetInputShapeND.restype = ctypes.c_int
dll.ailiaSetInputShapeND.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint32, flags='CONTIGUOUS'
    ),                               # shape
    ctypes.c_uint,                   # dim
)

# ailiaPredict
dll.ailiaPredict.restype = ctypes.c_int
dll.ailiaPredict.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                               # dst
    ctypes.c_uint,                   # dst_size
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                               # src
    ctypes.c_uint,                   # src_size
)

# ailiaGetBlobCount
dll.ailiaGetBlobCount.restype = ctypes.c_int
dll.ailiaGetBlobCount.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # count
)

# ailiaGetInputBlobCount
dll.ailiaGetInputBlobCount.restype = ctypes.c_int
dll.ailiaGetInputBlobCount.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # count
)

# ailiaGetOutputBlobCount
dll.ailiaGetOutputBlobCount.restype = ctypes.c_int
dll.ailiaGetOutputBlobCount.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # count
)

# ailiaGetBlobDim
dll.ailiaGetBlobDim.restype = ctypes.c_int
dll.ailiaGetBlobDim.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # dim
    ctypes.c_uint,                   # blob_idx
)

# ailiaGetBlobShape
dll.ailiaGetBlobShape.restype = ctypes.c_int
dll.ailiaGetBlobShape.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(Shape),           # shape
    ctypes.c_uint,                   # blob_idx
    ctypes.c_uint,                   # version
)

# ailiaGetBlobShapeND
dll.ailiaGetBlobShapeND.restype = ctypes.c_int
dll.ailiaGetBlobShapeND.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint32, flags='CONTIGUOUS'
    ),                               # shape
    ctypes.c_uint,                   # dim
    ctypes.c_uint,                   # blob_idx
)

# ailiaGetBlobData
dll.ailiaGetBlobData.restype = ctypes.c_int
dll.ailiaGetBlobData.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                               # dst
    ctypes.c_uint,                   # dst_size
    ctypes.c_uint,                   # blob_idx
)

dll.ailiaGetBlobDataType.restype = ctypes.c_int
dll.ailiaGetBlobDataType.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_int),   # data_type
    ctypes.c_uint,                   # blob_idx
)

# ailiaFindBlobIndexByName
dll.ailiaFindBlobIndexByName.restype = ctypes.c_int
dll.ailiaFindBlobIndexByName.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # blob_idx
    ctypes.c_char_p,                 # name
)

# ailiaGetBlobIndexByInputIndex
dll.ailiaGetBlobIndexByInputIndex.restype = ctypes.c_int
dll.ailiaGetBlobIndexByInputIndex.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # blob_idx
    ctypes.c_uint,                   # input_blob_idx
)

# ailiaGetBlobIndexByOutputIndex
dll.ailiaGetBlobIndexByOutputIndex.restype = ctypes.c_int
dll.ailiaGetBlobIndexByOutputIndex.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # blob_idx
    ctypes.c_uint,                   # output_blob_idx
)

# ailiaGetBlobNameLengthByIndex
dll.ailiaGetBlobNameLengthByIndex.restype = ctypes.c_int
dll.ailiaGetBlobNameLengthByIndex.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_uint,                   # blob_idx
    ctypes.POINTER(ctypes.c_uint),   # buffer_size
)

# ailiaFindBlobNameByIndex
dll.ailiaFindBlobNameByIndex.restype = ctypes.c_int
dll.ailiaFindBlobNameByIndex.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_char_p,                 # buffer
    ctypes.c_uint,                   # buffer_size
    ctypes.c_uint,                   # blob_idx
)

# ailiaGetSummaryLength
dll.ailiaGetSummaryLength.restype = ctypes.c_int
dll.ailiaGetSummaryLength.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(ctypes.c_uint),   # buffer_size
)

# ailiaGetSummary
dll.ailiaSummary.restype = ctypes.c_int
dll.ailiaSummary.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_char_p,                 # buffer
    ctypes.c_uint,                   # buffer_size
)

# ailiaSetInputBlobData
dll.ailiaSetInputBlobData.restype = ctypes.c_int
dll.ailiaSetInputBlobData.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                               # src
    ctypes.c_uint,                   # src_size
    ctypes.c_uint,                   # blob_idx
)

# ailiaSetInputBlobShape
dll.ailiaSetInputBlobShape.restype = ctypes.c_int
dll.ailiaSetInputBlobShape.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(Shape),           # shape
    ctypes.c_uint,                   # blob_idx
    ctypes.c_uint,                   # version
)

# ailiaSetInputBlobShapeND
dll.ailiaSetInputBlobShapeND.restype = ctypes.c_int
dll.ailiaSetInputBlobShapeND.argtypes = (
    ctypes.c_void_p,                 # net
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint32, flags='CONTIGUOUS'
    ),                               # shape
    ctypes.c_uint,                   # dim
    ctypes.c_uint,                   # blob_idx
)

# ailiaUpdate
dll.ailiaCopyBlobData.restype = ctypes.c_int
dll.ailiaCopyBlobData.argtypes = (
    ctypes.c_void_p,                 # dst_net
    ctypes.c_uint,                   # dst_blob_idx
    ctypes.c_void_p,                 # src_net
    ctypes.c_uint,                   # src_blob_idx
)

# ailiaUpdate
dll.ailiaUpdate.restype = ctypes.c_int
dll.ailiaUpdate.argtypes = (
    ctypes.c_void_p,                 # net
)

# ailiaFindBlobIndexByName
dll.ailiaSetForceCpuExecutionLayersFwdMatching.restype = ctypes.c_int
dll.ailiaSetForceCpuExecutionLayersFwdMatching.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_char_p,                 # pattern
)

# ailiaSetTemporaryCachePathA
dll.ailiaSetTemporaryCachePathA.restype = ctypes.c_int
dll.ailiaSetTemporaryCachePathA.argtypes = (
    ctypes.c_char_p,                 # path
)

# ailiaSetTemporaryCachePathW
dll.ailiaSetTemporaryCachePathW.restype = ctypes.c_int
dll.ailiaSetTemporaryCachePathW.argtypes = (
    ctypes.c_wchar_p,                # path
)

# ailiaGetEnvironmentCount
dll.ailiaGetEnvironmentCount.restype = ctypes.c_int
dll.ailiaGetEnvironmentCount.argtypes = (
    ctypes.POINTER(ctypes.c_uint),   # env_count
)

# ailiaGetEnvironment
dll.ailiaGetEnvironment.restype = ctypes.c_int
dll.ailiaGetEnvironment.argtypes = (
    ctypes.POINTER(
        ctypes.POINTER(Environment)
    ),                               # env
    ctypes.c_uint,                   # env_idx
    ctypes.c_uint,                   # version
)

# ailiaGetselectedEnvironment
dll.ailiaGetSelectedEnvironment.restype = ctypes.c_int
dll.ailiaGetSelectedEnvironment.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.POINTER(
        ctypes.POINTER(Environment)
    ),                               # env
    ctypes.c_uint,                   # version
)

# ailiaSetMemoryMode
dll.ailiaSetMemoryMode.restype = ctypes.c_int
dll.ailiaSetMemoryMode.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_uint,                   # mode
)

# ailiaGetStatusString
dll.ailiaGetStatusString.restype = ctypes.c_char_p
dll.ailiaGetStatusString.argtypes = (
    ctypes.c_int,                    # status_code
)

# ailiaGetErrorDetail
dll.ailiaGetErrorDetail.restype = ctypes.c_char_p
dll.ailiaGetErrorDetail.argtypes = (
    ctypes.c_void_p,                 # net
)

# ailiaGetVersion
dll.ailiaGetVersion.restype = ctypes.c_char_p
dll.ailiaGetVersion.argtypes = (
)

# ailiaSetProfileMode
dll.ailiaSetProfileMode.restype = ctypes.c_int
dll.ailiaSetProfileMode.argtypes = (
    ctypes.c_void_p,                 # net
    ctypes.c_uint,                   # mode
)

# ailiaFinalize
dll.ailiaFinalize.restype = ctypes.c_int
dll.ailiaFinalize.argtypes = (
)

# ailiaEnableDebugLog
dll.ailiaEnableDebugLog.restype = ctypes.c_int
dll.ailiaEnableDebugLog.argtypes = (
    ctypes.c_void_p,                 # net
)

# ailiaDisablelayerFusion
dll.ailiaDisableLayerFusion.restype = ctypes.c_int
dll.ailiaDisableLayerFusion.argtypes = (
    ctypes.c_void_p,                 # net
)


# ailiaCreateDetector
dll.ailiaCreateDetector.restype = ctypes.c_int
dll.ailiaCreateDetector.argtypes = (
    ctypes.POINTER(ctypes.c_void_p),  # detector
    ctypes.c_void_p,                 # net
    ctypes.c_uint,                   # format
    ctypes.c_uint,                   # channel
    ctypes.c_uint,                   # range
    ctypes.c_uint,                   # algorithm
    ctypes.c_uint,                   # category_count
    ctypes.c_uint,                   # flags
)

# ailiaDestroyDetector
dll.ailiaDestroyDetector.restype = None
dll.ailiaDestroyDetector.argtypes = (
    ctypes.c_void_p,                 # detector
)

# ailiaDetectorCompute
dll.ailiaDetectorCompute.restype = ctypes.c_int
dll.ailiaDetectorCompute.argtypes = (
    ctypes.c_void_p,                 # detector
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint8, flags='CONTIGUOUS'
    ),                               # src
    ctypes.c_uint,                   # src_stride
    ctypes.c_uint,                   # src_width
    ctypes.c_uint,                   # src_height
    ctypes.c_uint,                   # src_format
    ctypes.c_float,                  # threshold
    ctypes.c_float,                  # iou
)

# ailiaDetectorGetObjectCount
dll.ailiaDetectorGetObjectCount.restype = ctypes.c_int
dll.ailiaDetectorGetObjectCount.argtypes = (
    ctypes.c_void_p,                 # detector
    ctypes.POINTER(ctypes.c_uint),   # obj_count
)

# ailiaDetectorGetObject
dll.ailiaDetectorGetObject.restype = ctypes.c_int
dll.ailiaDetectorGetObject.argtypes = (
    ctypes.c_void_p,                 # detector
    ctypes.POINTER(DetectorObject),  # obj
    ctypes.c_uint,                   # obj_idx
    ctypes.c_uint,                   # version
)

# ailiaDetectorSetAnchors
dll.ailiaDetectorSetAnchors.restype = ctypes.c_int
dll.ailiaDetectorSetAnchors.argtypes = (
    ctypes.c_void_p,                 # detector
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                               # anchors
    ctypes.c_uint,                   # anchors_count
)

# ailiaDetectorSetInputShape
dll.ailiaDetectorSetInputShape.restype = ctypes.c_int
dll.ailiaDetectorSetInputShape.argtypes = (
    ctypes.c_void_p,                 # detector
    ctypes.c_uint,                   # input_width
    ctypes.c_uint,                   # input_height
)

# ailiaCreateClassifier
dll.ailiaCreateClassifier.restype = ctypes.c_int
dll.ailiaCreateClassifier.argtypes = (
    ctypes.POINTER(ctypes.c_void_p),  # classifier
    ctypes.c_void_p,                 # net
    ctypes.c_uint,                   # format
    ctypes.c_uint,                   # channel
    ctypes.c_uint,                   # range
)

# ailiaDestroyClassifier
dll.ailiaDestroyClassifier.restype = None
dll.ailiaDestroyClassifier.argtypes = (
    ctypes.c_void_p,                 # classifier
)

# ailiaClassifierCompute
dll.ailiaClassifierCompute.restype = ctypes.c_int
dll.ailiaClassifierCompute.argtypes = (
    ctypes.c_void_p,                 # classifier
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint8, flags='CONTIGUOUS'
    ),                               # src
    ctypes.c_uint,                   # src_stride
    ctypes.c_uint,                   # src_width
    ctypes.c_uint,                   # src_height
    ctypes.c_uint,                   # src_format
    ctypes.c_uint,                   # max_class_count
)

# ailiaClassifierGetClassCount
dll.ailiaClassifierGetClassCount.restype = ctypes.c_int
dll.ailiaClassifierGetClassCount.argtypes = (
    ctypes.c_void_p,                 # classifier
    ctypes.POINTER(ctypes.c_uint),   # cls_count
)

# ailiaClassifierGetClass
dll.ailiaClassifierGetClass.restype = ctypes.c_int
dll.ailiaClassifierGetClass.argtypes = (
    ctypes.c_void_p,                 # classifier
    ctypes.POINTER(ClassifierClass),  # cls
    ctypes.c_uint,                   # cls_idx
    ctypes.c_uint,                   # version
)


#### exception class definition ####

class AiliaException(Exception):
    """ Base class for exceptions of ailia
    """


class AiliaInvalidArgumentException(AiliaException):
    """Incorrect argument

    Please check argument of called API.
    """
    pass


class AiliaFileIoException(AiliaException):
    """File access failed.

    Please check file is exist or not, and check access permission.
    """
    pass


class AiliaInvalidVersionException(AiliaException):
    """Incorrect struct version

    Please check struct version that passed with API and please pass correct struct version.
    """
    pass


class AiliaBrokenDataException(AiliaException):
    """A corrupt file was passed.

    Please check model file are correct or not, and please pass correct model.
    """
    pass


class AiliaResourceInsufficientException(AiliaException):
    """Insufficient system resource

    Please check usage of system resource (e.g. thread). And please call API after release system  resources.
    """
    pass


class AiliaInvalidStateException(AiliaException):
    """The internal status of the ailia is incorrect.

    Please check API document and API call steps.
    """
    pass


class AiliaUnsupportNetException(AiliaException):
    """Unsupported network

    Non supported model file was passed to wrapper functions (e.g. Detector). Please check document whether presented models are supported or not.
    """
    pass


class AiliaInvalidLayerException(AiliaException):
    """Incorrect layer weight, parameter, or input or output shape

    The layer of model had incorrect parameter or so on. Please call ailiaGetErrorDetail() and check detail message. And, please check model.
    """
    pass


class AiliaInvalidParamException(AiliaException):
    """The content of the parameter file is invalid.

    Please check parameter file are correct or not.
    """
    pass


class AiliaNotFoundException(AiliaException):
    """The specified element was not found.

    The specified element of passed name/index was not found. Please check the element are exisit on model or not.
    """
    pass


class AiliaGpuUnsupportLayerException(AiliaException):
    """A layer parameter not supported by the GPU was given.

    The layer or parameter that not supported by the GPU was given. Please check model file are correct or not and contact support desk that described on document.
    """
    pass


class AiliaGpuErrorException(AiliaException):
    """Error during processing on the GPU

    Please check the GPU driver are latest and VRAM are sufficient or not.
    """
    pass


class AiliaUnimplementedException(AiliaException):
    """Unimplemented error

    The called API are not available on current environment. Please contact support desk that described on document.
    """
    pass


class AiliaPermissionDeniedException(AiliaException):
    """Operation not allowed

    The called API are not allowed on this model (e.g. encrypted model are used.). Please check model file and change API call flow.
    """
    pass


class AiliaExpiredException(AiliaException):
    """Model Expired

    The model file are expired. Please re generate model with ailia_obfuscate_c.
    """
    pass


class AiliaUnsettledShapeException(AiliaException):
    """The shape is not yet determined

    The shape (e.g. output shape) are not determined. When called API that to get output shape, please set input shape and execute inference, then call API that to get output shape.
    """
    pass


class AiliaDataRemovedException(AiliaException):
    """The information was not available from the application

    The specified information was removed due to optimization. If you need the information, please disable optimization and call API.
    """
    pass


class AiliaDataHiddenException(AiliaDataRemovedException):
    pass


class AiliaLicenseNotFoundException(AiliaException):
    """No valid license found

    The license file are required for trial version. Please contact support desk that described on document.
    """
    pass


class AiliaLicenseBrokenException(AiliaException):
    """License is broken

    The license file that are required for trial version are broken. Please contact support desk that described on document.
    """
    pass


class AiliaLicenseExpiredException(AiliaException):
    """License expired

    The license file that are required for trial version are expired. Please contact support desk that described on document.
    """
    pass


class AiliaShapeHasExDimException(AiliaException):
    """Dimension of shape is 5 or more.

    The called API are supported up to 4 dimension. Please replace API that described on API document.
    """
    pass

#### utility functions ####


def check_error(code, net=None):
    SUCCESS = 0
    dict = {
        -1: AiliaInvalidArgumentException,
        -2: AiliaFileIoException,
        -3: AiliaInvalidVersionException,
        -4: AiliaBrokenDataException,
        -5: AiliaResourceInsufficientException,  # memory
        -6: AiliaResourceInsufficientException,  # thread
        -7: AiliaInvalidStateException,
        -8: AiliaGpuErrorException,  # old
        -9: AiliaUnsupportNetException,
        -10: AiliaInvalidLayerException,
        -11: AiliaInvalidParamException,
        -12: AiliaNotFoundException,
        -13: AiliaGpuUnsupportLayerException,
        -14: AiliaGpuErrorException,  # current
        -15: AiliaUnimplementedException,
        -16: AiliaPermissionDeniedException,
        -17: AiliaExpiredException,
        -18: AiliaUnsettledShapeException,
        -19: AiliaDataHiddenException,
        -20: AiliaLicenseNotFoundException,
        -21: AiliaLicenseBrokenException,
        -22: AiliaLicenseExpiredException,
        -23: AiliaShapeHasExDimException,
    }
    if code == SUCCESS:
        return

    detail = "code: " + str(code) + " (" + dll.ailiaGetStatusString(code).decode() + ")"
    if net != None:
        msg = dll.ailiaGetErrorDetail(net).decode()
        if len(msg) == 0:
            msg = "(empty)"
        detail += "\n+ error detail : " + msg

    if code in dict:
        e = dict[code]
        raise e(detail)
    else:
        raise AiliaException(detail)


def convert_to_numpy_style_shape(shape):
    if shape.dim == 1:
        return (shape.x, )
    elif shape.dim == 2:
        return (shape.y, shape.x)
    elif shape.dim == 3:
        return (shape.z, shape.y, shape.x)
    else:
        return (shape.w, shape.z, shape.y, shape.x)


def convert_from_numpy_style_shape(tuple):
    r = Shape()
    r.dim = len(tuple)
    ww = (1, 1, 1) + tuple
    r.w = ww[r.dim - 1]
    r.z = ww[r.dim + 0]
    r.y = ww[r.dim + 1]
    r.x = ww[r.dim + 2]
    return r


def check_output_argument_ndarray(target, shape, name):
    if not isinstance(target, numpy.ndarray):
        raise AiliaInvalidArgumentException(name + " isn't numpy.ndarray.")
    if target.shape != shape:
        raise AiliaInvalidArgumentException(name + ".shape isn't expected shape : (" + ",".join(map(str, shape)) + ")")
    if target.dtype != numpy.float32:
        raise AiliaInvalidArgumentException(name + ".dtype isn't numpy.float32.")
    if not target.flags['C_CONTIGUOUS']:
        raise AiliaInvalidArgumentException(name + " isn't created with \"order=\'C\'\".")


def check_input_argument_ndarray(target, shape, name):
    if not isinstance(target, numpy.ndarray):
        raise AiliaInvalidArgumentException(name + " isn't numpy.ndarray.")
    if target.shape != shape:
        raise AiliaInvalidArgumentException(name + ".shape isn't expected shape : (" + ",".join(map(str, shape)) + ")")


def convert_input_ndarray(data):
    if data.flags['C_CONTIGUOUS'] and data.dtype == numpy.float32:
        return data
    return data.astype(numpy.float32, order='C')


def check_image_argument_ndarray(data, name):
    if not isinstance(data, numpy.ndarray):
        raise AiliaInvalidArgumentException(name + " isn't numpy.ndarray.")
    if data.ndim != 3:
        raise AiliaInvalidArgumentException(name + ".ndim(" + str(data.ndim) + ") isn't expected dimension(3)")
    if data.shape[2] != 4 and data.shape[2] != 3:
        raise AiliaInvalidArgumentException(name + "'s channel count isn't 4 (BGRA) nor 3 (BGR).")


def convert_image_ndarray(data):
    if data.flags['C_CONTIGUOUS'] and data.dtype == numpy.uint8:
        return data
    return data.astype(numpy.uint8, order='C')


def get_image_format(image):
    if image.shape[2] == 3:
        return IMAGE_FORMAT_BGR
    else:
        return IMAGE_FORMAT_BGRA


def check_file_exist(name):
    if not os.path.exists(name):
        raise AiliaFileIoException(name + " does not exist")
