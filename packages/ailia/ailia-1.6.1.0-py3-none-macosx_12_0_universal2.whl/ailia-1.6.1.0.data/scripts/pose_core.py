#### ailia pose estimator python binding core api ####

import ctypes
import os
import sys
import numpy
import platform

#### loading DLL / DYLIB / SO  ####
if sys.platform == "win32":
    dll_platform = "windows/x64"
    dll_name = "ailia_pose_estimate.dll"
    load_fn = ctypes.WinDLL
elif sys.platform == "darwin":
    dll_platform = "mac"
    dll_name = "libailia_pose_estimate.dylib"
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
    dll_name = "libailia_pose_estimate.so"
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

#### Struct Definition ####


class PoseEstimatorKeypoint(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z_local", ctypes.c_float),
        ("score", ctypes.c_float),
        ("interpolated", ctypes.c_int)]
    VERSION = ctypes.c_uint(1)


class PoseEstimatorObjectPose(ctypes.Structure):
    _fields_ = [
        ('points', PoseEstimatorKeypoint * 19),
        ("total_score", ctypes.c_float),
        ("num_valid_points", ctypes.c_int),
        ("id", ctypes.c_int),
        ("angle_x", ctypes.c_float),
        ("angle_y", ctypes.c_float),
        ("angle_z", ctypes.c_float)
    ]
    VERSION = ctypes.c_uint(1)

    def __init__(self):
        num_of_structs = 19
        for num in range(0, num_of_structs):
            self.points[num].x = 0
            self.points[num].y = 0
            self.points[num].z_local = 0
            self.points[num].score = 0
            self.points[num].interpolated = 0


class PoseEstimatorObjectUpPose(ctypes.Structure):
    _fields_ = [
        ('points', PoseEstimatorKeypoint * 15),
        ("total_score", ctypes.c_float),
        ("num_valid_points", ctypes.c_int),
        ("id", ctypes.c_int),
        ("angle_x", ctypes.c_float),
        ("angle_y", ctypes.c_float),
        ("angle_z", ctypes.c_float)
    ]
    VERSION = ctypes.c_uint(1)

    def __init__(self):
        num_of_structs = 15
        for num in range(0, num_of_structs):
            self.points[num].x = 0
            self.points[num].y = 0
            self.points[num].z_local = 0
            self.points[num].score = 0
            self.points[num].interpolated = 0


class PoseEstimatorObjectHand(ctypes.Structure):
    _fields_ = [
        ('points', PoseEstimatorKeypoint * 21),
        ("total_score", ctypes.c_float)
    ]
    VERSION = ctypes.c_uint(1)

    def __init__(self):
        num_of_structs = 21
        for num in range(0, num_of_structs):
            self.points[num].x = 0
            self.points[num].y = 0


# ailiaCreatePoseEstimator
dll.ailiaCreatePoseEstimator.restype = ctypes.c_int
dll.ailiaCreatePoseEstimator.argtypes = (
    ctypes.POINTER(ctypes.c_void_p),  # pose_estimator
    ctypes.c_void_p,                 # net
    ctypes.c_int,                    # algorithm
)

# ailiaDestroyPoseEstimator
dll.ailiaDestroyPoseEstimator.restype = None
dll.ailiaDestroyPoseEstimator.argtypes = (
    ctypes.c_void_p,                 # pose_estimator
)

# ailiaPoseEstimatorCompute
dll.ailiaPoseEstimatorCompute.restype = ctypes.c_int
dll.ailiaPoseEstimatorCompute.argtypes = (
    ctypes.c_void_p,                 # pose_estimator
    numpy.ctypeslib.ndpointer(
        dtype=numpy.uint8, flags='CONTIGUOUS'
    ),                               # src
    ctypes.c_uint,                   # src_stride
    ctypes.c_uint,                   # src_width
    ctypes.c_uint,                   # src_height
    ctypes.c_uint,                   # src_format
)

# ailiaPoseEstimatorGetObjectCount
dll.ailiaPoseEstimatorGetObjectCount.restype = ctypes.c_int
dll.ailiaPoseEstimatorGetObjectCount.argtypes = (
    ctypes.c_void_p,                 # pose_estimator
    ctypes.POINTER(ctypes.c_uint),   # count
)

# ailiaPoseEstimatorGetObjectPose
dll.ailiaPoseEstimatorGetObjectPose.restype = ctypes.c_int
dll.ailiaPoseEstimatorGetObjectPose.argtypes = (
    ctypes.c_void_p,                 # pose_estimator
    ctypes.POINTER(PoseEstimatorObjectPose),           # obj
    ctypes.c_uint,                   # obj_idx
    ctypes.c_uint,                   # version
)

# ailiaPoseEstimatorGetObjectUpPose
dll.ailiaPoseEstimatorGetObjectUpPose.restype = ctypes.c_int
dll.ailiaPoseEstimatorGetObjectUpPose.argtypes = (
    ctypes.c_void_p,                 # pose_estimator
    ctypes.POINTER(PoseEstimatorObjectUpPose),           # obj
    ctypes.c_uint,                   # obj_idx
    ctypes.c_uint,                   # version
)

# ailiaPoseEstimatorGetObjectHand
dll.ailiaPoseEstimatorGetObjectHand.restype = ctypes.c_int
dll.ailiaPoseEstimatorGetObjectHand.argtypes = (
    ctypes.c_void_p,                 # pose_estimator
    ctypes.POINTER(PoseEstimatorObjectHand),           # obj
    ctypes.c_uint,                   # obj_idx
    ctypes.c_uint,                   # version
)

# ailiaPoseEstimatorSetThreshold
dll.ailiaPoseEstimatorSetThreshold.restype = ctypes.c_int
dll.ailiaPoseEstimatorSetThreshold.argtypes = (
    ctypes.c_void_p,                 # pose_estimator
    ctypes.c_float,                  # threshold
)


def convert_input_ndarray_uint8(data):
    if data.flags['C_CONTIGUOUS'] and data.dtype is numpy.uint8:
        return data
    return data.astype(numpy.uint8, order='C')
