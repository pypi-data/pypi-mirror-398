#### API wrapper (common in library module) ####

import collections
import ctypes
import sys
import warnings
import dataclasses
import typing
from collections import namedtuple

import numpy

from . import core, pose_core
from .const import *
from .license import *


def set_temporary_cache_path(path):
    """ set system cache path.
    """
    if sys.platform == "win32":
        code = core.dll.ailiaSetTemporaryCachePathW(ctypes.create_unicode_buffer(path))
    else:
        code = core.dll.ailiaSetTemporaryCachePathA(ctypes.create_string_buffer(path.encode("utf-8")))
    core.check_error(code)


def get_environment_count():
    """ get available environments count.

    Returns
    -------
    int
        available execution environments count

    See Also
    ----------
    get_environmnet()
    """
    result = ctypes.c_uint(0)
    code = core.dll.ailiaGetEnvironmentCount(ctypes.byref(result))
    core.check_error(code)
    return result.value


def get_environment(idx):
    """ get environment detail.

    Parameters
    ----------
    idx : int
        env_id. 0 to (get_environment_count()-1).

    Returns
    -------
    namedtuple("Environment")
        execution environment detail.
        id : int, used for create() function's env_id argument.
        type : str, one of the following :
            'CPU', 'BLAS', 'GPU'
        name : str, detail description of execution environment.
        backend : str, one of the following :
            'NONE', 'CUDA', 'MPS', 'VULKAN'
        props : list(str), is empty or contains one or more following:
            'LOWPOWER', 'FP16'

    See Also
    ----------
    get_environment_count()
    """
    #warnings.warn("\'ailia.get_environment\' is deprecated , please use \'ailia.get_environment_list\' instead.", UserWarning, stacklevel=2)

    env = ctypes.POINTER(core.Environment)()
    code = core.dll.ailiaGetEnvironment(ctypes.byref(env), ctypes.c_uint(idx), core.Environment.VERSION)
    core.check_error(code)
    env = env[0]
    r = Environment(
        id=env.id,
        type=env.get_type_string(),
        name=env.name.decode(),
        backend=env.get_backend_string(),
        props=env.get_props_list())
    return r


def get_environment_list():
    """ get environment detail.

    Returns
    -------
    list of namedtuple("Environment")
        namedtuple("Environment")
            execution environment detail.
            id : int, used for create() function's env_id argument.
            type : str, one of the following :
                'CPU', 'BLAS', 'GPU'
            name : str, detail description of execution environment.
            backend : str, one of the following :
                'NONE', 'CUDA', 'MPS', 'VULKAN'
            props : list(str), is empty or contains one or more following:
                'LOWPOWER', 'FP16'
    """
    env_list = []
    cnt = get_environment_count()
    for idx in range(cnt):
        env = ctypes.POINTER(core.Environment)()
        code = core.dll.ailiaGetEnvironment(ctypes.byref(env), ctypes.c_uint(idx), core.Environment.VERSION)
        core.check_error(code)
        env = env[0]
        r = Environment(
            id=env.id,
            type=env.get_type_string(),
            name=env.name.decode(),
            backend=env.get_backend_string(),
            props=env.get_props_list())
        env_list.append(r)
    return env_list


def get_version():
    """ get version string of ailia library.

    Returns
    -------
    str
        version string.
    """
    return core.dll.ailiaGetVersion().decode()


def get_gpu_environment_id():
    """ utility function to get GPU execution environment.

    Returns
    -------
    int
        first env_id of GPU execution environment.

    Note
    -------
        if there were no GPU execution environment, this function
        returns ENVIRONMENT_AUTO(-1).
    """
    env_list = get_environment_list()
    env_id = ENVIRONMENT_AUTO
    for env in env_list:
        if env.type == 'GPU':
            if 'LOWPOWER' in env.props:
                if env_id == ENVIRONMENT_AUTO:
                    env_id = env.id
            else:
                env_id = env.id
            if env.backend == 'CUDA':
                return env_id
    return env_id


def finalize():
    """ release global (ex:GPU) resources allocated ailia.

    Note
    -------
        This function must be called when all ailia.Net instances
        have been released.
    """
    code = core.dll.ailiaFinalize()
    core.check_error(code)


def get_memory_mode(reduce_constant=False, ignore_input_with_initializer=False, reduce_interstage=False, reuse_interstage=False, use_memory_mapped=False):
    """ get memory management mode combined argument.

    Returns
    -------
    int
        memory management mode. ( for ailia.Net() )

    Parameters
    ----------
    reduce_constant : bool, optional, default=False
        free a constant intermediate blob.
    ignore_input_with_initializer : bool, optional, default=False
        consider all initializer as constant. (even if they overlap with input)
    reduce_interstage : bool, optional, default=False
        free an intermediate blob.
    reuse_interstage : bool, optional, default=False
        reuse an available intermediate blob.
    use_memory_mapped : bool, optional, default=False
        use memory mapped file due to reduce constant intermediate blobs.
        need to call set_temporary_cache_path in advance.
    """
    r = 0
    if (reduce_constant):
        r |= 1
    if (ignore_input_with_initializer):
        r |= 2
    if (reduce_interstage):
        r |= 4
    if (reuse_interstage):
        r |= 8
    if (use_memory_mapped):
        r |= 16
    return r


class Net:
    """ wrapper class for ailia network model instance
    """
    @dataclasses.dataclass
    class Blob:
        idx: int
        name: str
        data: typing.Optional[numpy.ndarray]
    
    __net = None
    
    def __init__(self, stream=None, weight=None, env_id=ENVIRONMENT_AUTO, num_thread=MULTITHREAD_AUTO, memory_mode=None, debug_log=False, enable_layer_fusion=True):
        """ constructor of ailia network model instance.

        Parameters
        ----------
        stream : str, numpy.ndarray
            network model file path (ex. "foobar.prototxt")
            network model data
            for use onnx file, please specify None.
        weight : str, numpy.ndarray
            network weight file path (ex. "foobar.caffemodel" "foobar.onnx" )
            network weight data
        env_id : int, optional, default:ENVIRONMENT_AUTO(-1)
            environment id of ailia excecution.
            To retrieve env_id value, use
                get_environment_count() / get_environment() pair
            or
                get_gpu_environment_id() .
        num_thread : int, optional, default: MULTITHREAD_AUTO(0)
            number of threads.
            valid values:
                MULTITHREAD_AUTO=0 [means systems's logical processor count],
                1 to 32.
        memory_mode : int or None, optional, default: None
            memory management mode of ailia excecution.
            To retrieve memory_mode value, use get_memory_mode() .
        debug_log : bool, optional, default: False
            enable trace logging and verbose log for ailia.
        enable_layer_fusion : bool, optional, default: True
            enable layer fusion optimization.
        """
        # license check
        if "time_license" in get_version():
            check_and_download_license()

        # create
        self.__net = ctypes.c_void_p(None)
        code = core.dll.ailiaCreate(ctypes.byref(self.__net), ctypes.c_int(env_id), ctypes.c_int(num_thread))
        core.check_error(code)
        # enable debug log
        if debug_log:
            code = core.dll.ailiaEnableDebugLog(self.__net)
            core.check_error(code)
        if not enable_layer_fusion:
            code = core.dll.ailiaDisableLayerFusion(self.__net)
            core.check_error(code)
        # set memory mode
        if (memory_mode != None):
            code = core.dll.ailiaSetMemoryMode(self.__net, ctypes.c_uint(memory_mode))
            core.check_error(code)
        if stream:
            self._open_stream(stream)
        if weight:
            self._open_weight(weight)
        if stream or weight:
            self._input_blobs = []
            self._input_name2blob = {}
            for idx in self._get_input_blob_list():
                name = self.get_blob_name(idx)
                next = len(self._input_blobs)
                self._input_blobs.append( self.Blob(idx=idx, name=name, data=None) )
                self._input_name2blob[name] = self._input_blobs[next]
            self._output_blobs = []
            self._output_name2blob = {}
            for idx in self._get_output_blob_list():
                name = self.get_blob_name(idx)
                next = len(self._output_blobs)
                self._output_blobs.append( self.Blob(idx=idx, name=name, data=None) )
                self._output_name2blob[name] = self._output_blobs[next]


    def __del__(self):
        """ destructor of ailia network model instance. """
        if self.__net is not None:
            core.dll.ailiaDestroy(self.__net)

    def _open_stream(self, stream):
        # open_stream
        code = ctypes.c_int(0)
        if isinstance(stream, numpy.ndarray):
            code = core.dll.ailiaOpenStreamMem(self.__net, stream, stream.nbytes)
        else:
            core.check_file_exist(stream)
            if sys.platform == "win32":
                code = core.dll.ailiaOpenStreamFileW(self.__net, ctypes.create_unicode_buffer(stream))
            else:
                code = core.dll.ailiaOpenStreamFileA(self.__net, ctypes.create_string_buffer(stream.encode("utf-8")))
        core.check_error(code, self.__net)

    def _open_weight(self, weight):
        # open_weight
        code = ctypes.c_int(0)
        if isinstance(weight, numpy.ndarray):
            code = core.dll.ailiaOpenWeightMem(self.__net, weight, weight.nbytes)
        else:
            core.check_file_exist(weight)
            if sys.platform == "win32":
                code = core.dll.ailiaOpenWeightFileW(self.__net, ctypes.create_unicode_buffer(weight))
            else:
                code = core.dll.ailiaOpenWeightFileA(self.__net, ctypes.create_string_buffer(weight.encode("utf-8")))
        core.check_error(code, self.__net)

    def _get_input_blob_list(self):
        count = ctypes.c_uint(0)
        code = core.dll.ailiaGetInputBlobCount(self.__net, ctypes.byref(count))
        core.check_error(code, self.__net)
        r = []
        for i in range(count.value):
            idx = ctypes.c_uint(0)
            code = core.dll.ailiaGetBlobIndexByInputIndex(self.__net, ctypes.byref(idx), ctypes.c_uint(i))
            core.check_error(code, self.__net)
            r.append(idx.value)
        return r

    def _get_output_blob_list(self):
        count = ctypes.c_uint(0)
        code = core.dll.ailiaGetOutputBlobCount(self.__net, ctypes.byref(count))
        core.check_error(code, self.__net)
        r = []
        for i in range(count.value):
            idx = ctypes.c_uint(0)
            code = core.dll.ailiaGetBlobIndexByOutputIndex(self.__net, ctypes.byref(idx), ctypes.c_uint(i))
            core.check_error(code, self.__net)
            r.append(idx.value)
        return r

    def get_input_shape(self):
        """ get input blob shape.

        Returns
        -------
        tuple of ints
            input blob shape. (same as numpy's shape)
        """
        dim = ctypes.c_uint(0)
        code = core.dll.ailiaGetInputDim(self.__net, ctypes.byref(dim))
        core.check_error(code, self.__net)
        shape = numpy.zeros(dim.value, dtype=numpy.uint32)
        code = core.dll.ailiaGetInputShapeND(self.__net, shape, dim)
        core.check_error(code, self.__net)
        return tuple(shape.astype(int).tolist())

    def get_output_shape(self):
        """ get output blob shape.

        Returns
        -------
        tuple of ints
            output blob shape. (same as numpy's shape)
        """
        dim = ctypes.c_uint(0)
        code = core.dll.ailiaGetOutputDim(self.__net, ctypes.byref(dim))
        core.check_error(code, self.__net)
        shape = numpy.zeros(dim.value, dtype=numpy.uint32)
        code = core.dll.ailiaGetOutputShapeND(self.__net, shape, dim)
        core.check_error(code, self.__net)
        return tuple(shape.astype(int).tolist())

    def set_input_shape(self, shape):
        """ change input blob shape.

        Parameters
        ----------
        shape : tuple of ints
            new input layer shape.
        """
        dim = ctypes.c_uint(len(shape))
        shape = numpy.array(shape, dtype=numpy.uint32)
        code = core.dll.ailiaSetInputShapeND(self.__net, shape, dim)
        core.check_error(code, self.__net)

    def __get_output_blobs(self, output_buffer=None):
        """create output blobs for predict/run(internal use)

        Parameters
        ----------
        output_buffer : numpy.ndarray or sequence( numpy.ndarray ), optional
            if specifyed, ailia does't create net output buffer every call and get only top N (len(output_buffer)) blobs of model.

        Returns
        -------
        list( numpy.ndarray )
            output blob data.
        """
        r = []
        if output_buffer is not None:
            if isinstance(output_buffer, collections.abc.Sequence):
                num = min(len(self._output_blobs), len(output_buffer))
                for i in range(num):
                    idx = self._output_blobs[i].idx
                    r.append(self.get_blob_data(idx, output_buffer[i]))
            else:
                idx = self._output_blobs[0].idx
                r.append(self.get_blob_data(idx, output_buffer))
        else:
            for x in self._output_blobs:
                r.append(self.get_blob_data(x.idx))
        return r


    def predict(self, input, output=None):
        """ run ailia network model.

        Parameters
        ----------
        input : numpy.ndarray or dict(str, numpy.ndarray) or sequence( numpy.ndarray )
            input blob data.
            requirements :
                input.shape is the same as a.get_input_shape() .
        output : numpy.ndarray or sequence( numpy.ndarray ), optional
            output blob buffer. (for the performance freak)
            if used, ailia doesn't create new output buffer every call and get only top N (len(output)) blobs of model.
            requirements :
                output.dtype is numpy.float32 .
                output.flags['C_CONTIGUOUS'] is True .
                output.shape is the same as a.get_output_shape() .

        Returns
        -------
        numpy.ndarray or list( numpy.ndarray )
            output blob data.
            when input is a ndarray, return is single ndarray (return output[0])
            when input is dict|sequence, return is list( ndarray )
        """
        #warnings.warn("\'Net.predict\' is deprecated , please use \'Net.run\' instead.", UserWarning, stacklevel=2)

        compatibility = False
        if isinstance(input, dict):
            for k,v in input.items():
                idx = 0
                if type(k) is str:
                    idx = self._input_name2blob[k].idx
                else:
                    idx = self._input_blobs[k].idx
                self.set_input_blob_data(v, idx)
        elif isinstance(input, collections.abc.Sequence):
            for i,v in enumerate(input):
                idx = self._input_blobs[i].idx
                self.set_input_blob_data(v, idx)
        else:
            compatibility = True
            idx = self._input_blobs[0].idx
            self.set_input_blob_data(input, idx)
        self.update()
        r = self.__get_output_blobs(output)
        if compatibility:
            return r[0]
        return r

    def run(self, input, output=None):
        """ run ailia network model.

        Parameters
        ----------
        input : numpy.ndarray or dict(str, numpy.ndarray) or sequence( numpy.ndarray )
            input blob data.
            requirements :
                input.shape is the same as a.get_input_shape() .
        output : numpy.ndarray or sequence( numpy.ndarray ), optional
            output blob buffer. (for the performance freak)
            if used, ailia doesn't create new output buffer every call and get only top N (len(output)) blobs of model.
            requirements :
                output.dtype is numpy.float32 .
                output.flags['C_CONTIGUOUS'] is True .
                output.shape is the same as a.get_output_shape() .

        Returns
        -------
        list( numpy.ndarray )
            list of output blob data.
            return is a list in any case.
        """
        if isinstance(input, dict):
            for k,v in input.items():
                idx = 0
                if type(k) is str:
                    idx = self._input_name2blob[k].idx
                else:
                    idx = self._input_blobs[k].idx
                self.set_input_blob_data(v, idx)
        elif isinstance(input, collections.abc.Sequence):
            for i,v in enumerate(input):
                idx = self._input_blobs[i].idx
                self.set_input_blob_data(v, idx)
        else:
            idx = self._input_blobs[0].idx
            self.set_input_blob_data(input, idx)
        self.update()
        r = self.__get_output_blobs(output)
        return r

    def get_blob_count(self):
        """ get blob count.

        Returns
        -------
        int
            blob count.
        """
        count = ctypes.c_uint(0)
        code = core.dll.ailiaGetBlobCount(self.__net, ctypes.byref(count))
        core.check_error(code, self.__net)
        return count.value

    def get_blob_shape(self, idx):
        """ get the shape of the blob specified by idx.

        Parameters
        ----------
        idx : int or str
            blob index (int) or blob name (str).
            valid values (int) : range(0, a.get_blob_count()) .

        Returns
        -------
        tuple of ints
            blob shape.
        """
        if type(idx) == str:
            idx = self.find_blob_index_by_name(idx)
        dim = ctypes.c_uint(0)
        code = core.dll.ailiaGetBlobDim(self.__net, ctypes.byref(dim), ctypes.c_uint(idx))
        core.check_error(code, self.__net)
        shape = numpy.zeros(dim.value, dtype=numpy.uint32)
        code = core.dll.ailiaGetBlobShapeND(self.__net, shape, dim, ctypes.c_uint(idx))
        core.check_error(code, self.__net)
        return tuple(shape.astype(int).tolist())

    def get_blob_name(self, idx):
        """ get the name of the blob specified by idx.

        Parameters
        ----------
        idx : int
            blob index.
            valid values : range(0, a.get_blob_count()) .

        Returns
        -------
        str
            blob name.
        """
        size = ctypes.c_uint(0)
        code = core.dll.ailiaGetBlobNameLengthByIndex(self.__net, idx, ctypes.byref(size))
        core.check_error(code, self.__net)
        buf = ctypes.create_string_buffer(size.value)
        code = core.dll.ailiaFindBlobNameByIndex(self.__net, buf, size, ctypes.c_uint(idx))
        core.check_error(code, self.__net)
        return buf.raw.decode()[:-1]

    def get_blob_data(self, idx, buffer=None):
        """ get the data of the blob specified by idx.

        Parameters
        ----------
        idx : int or str
            blob index (int) or blob name (str).
            valid values (int) : range(0, a.get_blob_count()) .
        buffer : numpy.ndarray, optional
            output blob buffer. (for the performance freak)
            if used, ailia doesn't create new output buffer every call.
            requirements :
                buffer.dtype is numpy.float32 .
                buffer.flags['C_CONTIGUOUS'] is True .
                buffer.shape is the same as a.get_blob_shape(idx) .

        Returns
        -------
        numpy.ndarray
            output blob data.
        """
        if type(idx) == str:
            idx = self.find_blob_index_by_name(idx)

        buf = buffer
        buf_shape = self.get_blob_shape(idx)
        if buffer is None:
            buf = numpy.zeros(buf_shape, dtype=numpy.float32, order='C')
        else:
            core.check_output_argument_ndarray(buffer, buf_shape, "buffer")

        code = core.dll.ailiaGetBlobData(self.__net, buf, buf.nbytes, ctypes.c_uint(idx))
        core.check_error(code, self.__net)

        blob_type = ctypes.c_int()
        code = core.dll.ailiaGetBlobDataType(self.__net, ctypes.byref(blob_type), ctypes.c_uint(idx))
        core.check_error(code, self.__net)
        blob_type = core.DataType(blob_type.value)

        if blob_type in core.DataTypeToDtype:
            dtype = core.DataTypeToDtype[blob_type]
            if buf.dtype != dtype:
                buf = buf.astype(dtype)

        return buf

    def find_blob_index_by_name(self, name):
        """ retrieve blob index by name.

        Parameters
        ----------
        name : str
            blob name.

        Returns
        -------
        int
            blob index.
        """
        result = ctypes.c_uint(0)
        code = core.dll.ailiaFindBlobIndexByName(self.__net, ctypes.byref(result), ctypes.create_string_buffer(name.encode("utf-8")))
        core.check_error(code, self.__net)
        return result.value

    def get_summary(self):
        """ get, as a string, a summary of all layers and blobs.

        Returns
        -------
        str
            summary string.
        """
        size = ctypes.c_uint(0)
        code = core.dll.ailiaGetSummaryLength(self.__net, ctypes.byref(size))
        core.check_error(code, self.__net)
        buf = ctypes.create_string_buffer(size.value)
        code = core.dll.ailiaSummary(self.__net, buf, size)
        core.check_error(code, self.__net)
        return buf.raw.decode()[:-1]

    def get_input_blob_list(self):
        """ get input blob indices list.

        Returns
        -------
        list(int)
            input blob indices.
        """
        return [d.idx for d in self._input_blobs]

    def get_output_blob_list(self):
        """ get output blob indices list.

        Returns
        -------
        list(int)
            output blob indices.
        """
        return [d.idx for d in self._output_blobs]

    def set_input_blob_data(self, input, idx):
        """ set input blob data. (for multiple input network model)

        Parameters
        ----------
        input : numpy.ndarray
            input data.
            requirements :
                input.shape is model's acceptable shape .
        idx : int or str
            blob index (int) or blob name (str).
            valid values (int) : range(0, a.get_blob_count())

        See Also
        ----------
        update()
        """
        if type(idx) == str:
            idx = self.find_blob_index_by_name(idx)
        try:
            buf_shape = self.get_blob_shape(idx)
            if buf_shape != input.shape:
                self.set_input_blob_shape(input.shape, idx)
        except core.AiliaUnsettledShapeException:
            buf_shape = input.shape
            self.set_input_blob_shape(buf_shape, idx)
        input = core.convert_input_ndarray(input)
        code = core.dll.ailiaSetInputBlobData(self.__net, input, input.nbytes, ctypes.c_uint(idx))
        core.check_error(code, self.__net)

    def set_input_blob_shape(self, shape, idx):
        """ set input blob shape. (for multiple input network model)

        Parameters
        ----------
        shape : tuple of ints
            new input blob shape.
        idx : int or str
            blob index (int) or blob name (str).
            valid values (int) : range(0, a.get_blob_count())

        See Also
        ----------
        update()
        """
        if type(idx) == str:
            idx = self.find_blob_index_by_name(idx)
        dim = ctypes.c_uint(len(shape))
        shape = numpy.array(shape, dtype=numpy.uint32)
        code = core.dll.ailiaSetInputBlobShapeND(self.__net, shape, dim, ctypes.c_uint(idx))
        core.check_error(code, self.__net)

    def copy_blob_data(self, dst_idx, src_idx, src_net = None):
        """ copy blobs inter Net object

        Parameters
        ----------
        dst_idx : int or str
            The destination blob index (int) or blob name (str).
        src_idx : int or str
            The source blob index (int) or blob name (str).
        src_net : Net or None
            If specifyed Net object, copy blob from src_net.
            Otherwise, copy from self.
        """
        if type(dst_idx) == str:
            dst_idx = self.find_blob_index_by_name(dst_idx)
        if type(src_idx) == str:
            src_idx = (src_net if src_net is not None else self).find_blob_index_by_name(src_idx)
        code = core.dll.ailiaCopyBlobData(self.__net, ctypes.c_uint(dst_idx), src_net.__net if src_net else self.__net, ctypes.c_uint(src_idx))
        core.check_error(code, self.__net)

    def update(self):
        """ run ailia network model with pre stored input data.

        using with a.set_input_blob_data() / a.get_results()
        ex.
            # set input [A]
            idx = a.find_blob_index_by_name(net, "input_a")
            a.set_input_blob_data(data_a, idx)
            # set other input [B]
            idx = a.find_blob_index_by_name(net, "input_b")
            a.set_input_blob_data(data_b, idx)
            # run ailia network model
            a.update(t)
            # get result
            list_of_outputs = a.get_results()
        """
        code = core.dll.ailiaUpdate(self.__net)
        core.check_error(code, self.__net)

    def get_results(self):
        """ get the list of output blobs data.

        Returns
        -------
        list(numpy.ndarray)
            output blob data.
        """
        return self.__get_output_blobs()

    def get_selected_environment(self):
        """ get current execution environment.

        Returns
        -------
        namedtuple("Environment")
            id : int, used for create() function's env_id argument.
            type : str, one of the following :
                'CPU', 'BLAS', 'GPU'
            name : str, detail description of execution environment.
            backend : str, one of the following :
                'NONE', 'CUDA', 'MPS', 'VULKAN'
            props : list(str), is empty or contains one or more following:
                'LOWPOWER', 'FP16'
        """
        env = ctypes.POINTER(core.Environment)()
        code = core.dll.ailiaGetSelectedEnvironment(self.__net, ctypes.byref(env), core.Environment.VERSION)
        core.check_error(code, self.__net)
        env = env[0]
        r = Environment(
            id=env.id,
            type=env.get_type_string(),
            name=env.name.decode(),
            backend=env.get_backend_string(),
            props=env.get_props_list())
        return r

    def get_error_detail(self):
        """ get error detail.

        Returns
        -------
        str
            error detail.
        """
        return core.dll.ailiaGetErrorDetail(self.__net).decode()

    def set_profile_mode(self, mode=PROFILE_AVERAGE):
        """ change profile mode.

        Parameters
        ----------
        mode : int, optional, default=PROFILE_AVERAGE(1)
            valid values:
                PROFILE_DISABLE(0)
                PROFILE_AVERAGE(1)
        """
        code = core.dll.ailiaSetProfileMode(self.__net, ctypes.c_uint(mode))
        core.check_error(code, self.__net)

    def get_raw_pointer(self):
        """ get raw instance of ailia

        Returns
        -------
        ctypes.c_void_p
            raw instance of ailia.
        """
        return self.__net


class Detector(Net):
    """ wrapper class for ailia object detector (YOLO style) instance
    """

    def __init__(
            self,
            stream_path,
            weight_path,
            category_count,
            env_id=ENVIRONMENT_AUTO,
            num_thread=MULTITHREAD_AUTO,
            format=NETWORK_IMAGE_FORMAT_RGB,
            channel=NETWORK_IMAGE_CHANNEL_FIRST,
            range=NETWORK_IMAGE_RANGE_S_FP32,
            algorithm=DETECTOR_ALGORITHM_YOLOV1,
            flags=DETECTOR_FLAG_NORMAL,
            debug_log=False,
            enable_layer_fusion=True,
            memory_mode=None):
        """ constructor of ailia object detector instance.

        Parameters
        ----------
        stream_path : str,
            network model file path (ex. "foobar.prototxt")
            for use onnx file, please specify None.
        weight_path : str,
            network weight file path (ex. "foobar.caffemodel")
        category_count : int
            use same value as model training time.
        env_id : int, optional, default:ENVIRONMENT_AUTO(-1)
            environment id of ailia excecution.
            To retrieve env_id value, use
                get_environment_count() / get_environment() pair
            or
                get_gpu_environment_id() .
        num_thread : int, optional, default: MULTITHREAD_AUTO(0)
            number of threads.
            valid values:
                MULTITHREAD_AUTO=0 [means systems's logical processor count],
                1 to 32.
        format : int, optional, default=NETWORK_IMAGE_FORMAT_RGB(1)
        channel : int, optional, default=NETWORK_IMAGE_CHANNEL_FIRST(0)
        range : int, optional, default=NETWORK_IMAGE_RANGE_S_FP32(3)
            use network model's expected input data format.
        algorithm : int, optional, default=DETECTOR_ALGORITHM_YOLOV1(0)
            algorithm selector, use
                DETECTOR_ALGORITHM_YOLOV1(0)
            or
                DETECTOR_ALGORITHM_YOLOV2(1)
            or
                DETECTOR_ALGORITHM_YOLOV3(2) .
            or
                DETECTOR_ALGORITHM_YOLOV4(3) .
            or
                DETECTOR_ALGORITHM_YOLOX(4) .
            or
                DETECTOR_ALGORITHM_SSD(8) .
        flags : int, optional, default=DETECTOR_FLAGS_NORMAL(0)
            reserved for future use.
        debug_log : bool, optional, default: False
            enable trace logging and verbose log for ailia.
        enable_layer_fusion : bool, optional, default: True
            enable layer fusion optimization.
        memory_mode : int or None, optional, default: None
            memory management mode of ailia excecution.
            To retrieve memory_mode value, use get_memory_mode() .
        """
        self.__det = ctypes.c_void_p(None)
        super().__init__(stream_path, weight_path, env_id, num_thread, memory_mode=memory_mode, debug_log=debug_log, enable_layer_fusion=enable_layer_fusion)
        code = core.dll.ailiaCreateDetector(
            ctypes.byref(self.__det),
            super().get_raw_pointer(),
            ctypes.c_uint(format),
            ctypes.c_uint(channel),
            ctypes.c_uint(range),
            ctypes.c_uint(algorithm),
            ctypes.c_uint(category_count),
            ctypes.c_uint(flags))
        core.check_error(code, super().get_raw_pointer())

    def __del__(self):
        """ destructor of ailia object detector instance. """
        if self.__det is not None:
            core.dll.ailiaDestroyDetector(self.__det)
        super().__del__()

    def compute(self, image, threshold, iou):
        """ run the ailia object detector with a input image.

        Parameters
        ----------
        image : numpy.ndarray
            input image data. expect a result of cv2.imread(img_path, cv2.IMREAD_UNCHANGED) .
        threshold : float
            object recognition threshold.
            an object whose probability is less than the threshold is undetected.
        iou : float
            intersection over union threshold, used for non-maximum suppression.
        """
        core.check_image_argument_ndarray(image, "image")
        image = core.convert_image_ndarray(image)
        stride = image.shape[1] * image.shape[2]
        width = image.shape[1]
        height = image.shape[0]
        format = core.get_image_format(image)
        code = core.dll.ailiaDetectorCompute(self.__det, image, stride, width, height, format, threshold, iou)
        core.check_error(code, super().get_raw_pointer())

    def get_object_count(self):
        """ get detected object count.

        Returns
        -------
        int
            number of objects.
        """
        result = ctypes.c_uint(0)
        code = core.dll.ailiaDetectorGetObjectCount(self.__det, ctypes.byref(result))
        core.check_error(code, super().get_raw_pointer())
        return result.value

    def get_object(self, idx):
        """ get a detected object detail specified by idx.

        Parameters
        ----------
        idx : int
            object index.
            vaild values : range(0, a.get_object_count())

        Returns
        -------
        namedtuple("DetectedObject")
            category : int, object category index.
            prob : float, object probability.
            x : float, object rectangle's top-left x coordinate.
            y : float, object rectangle's top-left y coordinate.
            w : float, object rectangle's width.
            h : float, object rectangle's height.
        """
        #warnings.warn("\'Detector.get_object\' is deprecated , please use \"Detector.run\" instead.", UserWarning, stacklevel=2)
        obj = core.DetectorObject()
        code = core.dll.ailiaDetectorGetObject(self.__det, ctypes.byref(obj), ctypes.c_uint(idx), core.DetectorObject.VERSION)
        core.check_error(code, super().get_raw_pointer())
        r = DetectorObject(
            category=obj.category,
            prob=obj.prob,
            x=obj.x,
            y=obj.y,
            w=obj.w,
            h=obj.h)
        return r

    def run(self, image, threshold, iou):
        """ run the ailia object detector with a input image.

        Parameters
        ----------
        image : numpy.ndarray
            input image data. expect a result of cv2.imread(img_path, cv2.IMREAD_UNCHANGED) .
        threshold : float
            object recognition threshold.
            an object whose probability is less than the threshold is undetected.
        iou : float
            intersection over union threshold, used for non-maximum suppression.

        Returns
        -------
        array of numpy structured array("DetectorObject")
            numpy structured array("DetectorObject")
                category : int, object category index.
                prob : float, object probability.
                box : numpy structured array ("DetecorRectangle")
                    x : float, object rectangle's top-left x coordinate.
                    y : float, object rectangle's top-left y coordinate.
                    w : float, object rectangle's width.
                    h : float, object rectangle's height.
        """
        self.compute(image, threshold, iou)

        rr = self._get_all_objects()

        return rr

    def _get_all_objects(self):
        """ get details of all detected object.

        Parameters
        ----------

        Returns
        -------
        array of numpy structured array("DetectorObject")
            numpy structured array("DetectorObject")
                category : int, object category index.
                prob : float, object probability.
                box: numpy structured array ("DetecorRectangle")
                    x : float, object rectangle's top-left x coordinate.
                    y : float, object rectangle's top-left y coordinate.
                    w : float, object rectangle's width.
                    h : float, object rectangle's height.
        """
        cnt = self.get_object_count()
        rr = numpy.zeros((cnt,), dtype=NumpyDetectorObject)
        for idx in range(cnt):
            obj = core.DetectorObject()
            code = core.dll.ailiaDetectorGetObject(self.__det, ctypes.byref(obj), ctypes.c_uint(idx), core.DetectorObject.VERSION)
            core.check_error(code, super().get_raw_pointer())
            rr[idx] = numpy.asarray([(obj.category, obj.prob, (obj.x, obj.y, obj.w, obj.h))], dtype=NumpyDetectorObject)

        return rr

    def set_anchors(self, data):
        """ sets the anchor information for YOLOv2 or other models.

        Parameters
        ----------
        data : numpy.ndarray
            extra data. anchors or biasis, etc.
        """
        data = core.convert_input_ndarray(data)
        count = int(data.size / 2)
        code = core.dll.ailiaDetectorSetAnchors(self.__det, data, ctypes.c_uint(count))
        core.check_error(code, super().get_raw_pointer())

    def set_input_shape(self, input_width, input_height):
        """ set model input image size (for YOLOv3)

        Parameters
        ----------
        input_width : int, input model image width
        input_height : int, input model image height
        """
        code = core.dll.ailiaDetectorSetInputShape(self.__det, ctypes.c_uint(input_width), ctypes.c_uint(input_height))
        core.check_error(code, super().get_raw_pointer())


class Classifier(Net):
    """ wrapper class for ailia image classifier instance
    """

    def __init__(
            self,
            stream_path,
            weight_path,
            env_id=ENVIRONMENT_AUTO,
            num_thread=MULTITHREAD_AUTO,
            format=NETWORK_IMAGE_FORMAT_BGR,
            channel=NETWORK_IMAGE_CHANNEL_FIRST,
            range=NETWORK_IMAGE_RANGE_S_FP32,
            debug_log=False,
            enable_layer_fusion=True,
            memory_mode=None):
        """ constructor of ailia image classifier instance.

        Parameters
        ----------
        stream_path : str,
            network model file path (ex. "foobar.prototxt")
            for use onnx file, please specify None.
        weight_path : str,
            network weight file path (ex. "foobar.caffemodel")
        env_id : int, optional, default:ENVIRONMENT_AUTO(-1)
            environment id of ailia excecution.
            To retrieve env_id value, use
                get_environment_count() / get_environment() pair
            or
                get_gpu_environment_id() .
        num_thread : int, optional, default: MULTITHREAD_AUTO(0)
            number of threads.
            valid values:
                MULTITHREAD_AUTO=0 [means systems's logical processor count],
                1 to 32.
        format : int, optional, default=NETWORK_IMAGE_FORMAT_BGR(0)
        channel : int, optional, default=NETWORK_IMAGE_CHANNEL_FIRST(0)
        range : int, optional, default=NETWORK_IMAGE_RANGE_S_FP32(3)
            use network model's expected input data format.
        debug_log : bool, optional, default: False
            enable trace logging and verbose log for ailia.
        enable_layer_fusion : bool, optional, default: True
            enable layer fusion optimization.
        memory_mode : int or None, optional, default: None
            memory management mode of ailia excecution.
            To retrieve memory_mode value, use get_memory_mode() .
        """
        self.__cls = ctypes.c_void_p(None)
        super().__init__(stream_path, weight_path, env_id, num_thread, memory_mode=memory_mode, debug_log=debug_log, enable_layer_fusion=enable_layer_fusion)
        code = core.dll.ailiaCreateClassifier(
            ctypes.byref(self.__cls),
            super().get_raw_pointer(),
            ctypes.c_uint(format),
            ctypes.c_uint(channel),
            ctypes.c_uint(range))
        core.check_error(code, super().get_raw_pointer())

    def __del__(self):
        """ destructor of ailia object detector instance. """
        if self.__cls is not None:
            core.dll.ailiaDestroyClassifier(self.__cls)
        super().__del__()

    def compute(self, image, max_class_count=1):
        """ run the ailia image classifier with a input image.

        Parameters
        ----------
        image : numpy.ndarray
            input image data. expect a result of cv2.imread(img_path, cv2.IMREAD_UNCHANGED) .
        max_class_count : int, optional, default=1
            maximum number of listed classes.
            finds N classes in decending order of probability.
        """
        core.check_image_argument_ndarray(image, "image")
        stride = image.shape[1] * image.shape[2]
        width = image.shape[1]
        height = image.shape[0]
        format = core.get_image_format(image)
        code = core.dll.ailiaClassifierCompute(self.__cls, image, stride, width, height, format, max_class_count)
        core.check_error(code, super().get_raw_pointer())

    def get_class_count(self):
        """ get listed classes count.

        Returns
        -------
        int
            number of classes.
        """
        result = ctypes.c_uint(0)
        code = core.dll.ailiaClassifierGetClassCount(self.__cls, ctypes.byref(result))
        core.check_error(code, super().get_raw_pointer())
        return result.value

    def get_class(self, idx):
        """ get a class information specified by idx.

        Parameters
        ----------
        idx : int
            class index.
            vaild values : range(0, a.get_class_count())

        Returns
        -------
        namedtuple("ClassifierClass")
            category : int, class category index.
            prob : float, class probability.
        """
        #warnings.warn("\'Classifier.get_class\' is deprecated , please use \'Classifier.run\' instead.", UserWarning, stacklevel=2)
        res = core.ClassifierClass()
        code = core.dll.ailiaClassifierGetClass(self.__cls, ctypes.byref(res), ctypes.c_uint(idx), core.ClassifierClass.VERSION)
        core.check_error(code, super().get_raw_pointer())
        r = ClassifierClass(
            category=res.category,
            prob=res.prob)
        return r

    def run(self, image, max_class_count=1):
        """ run the ailia image classifier with a input image.

        Parameters
        ----------
        image : numpy.ndarray
            input image data. expect a result of cv2.imread(img_path, cv2.IMREAD_UNCHANGED) .
        max_class_count : int, optional, default=1
            maximum number of listed classes.
            finds N classes in decending order of probability.

        Returns
        -------
        array of numpy structured array("ClassifierClass")
            numpy structured array("ClassifierClass")
                category : int, class category index.
                prob : float, class probability.
        """
        self.compute(image, max_class_count)

        rr = self._get_all_class()

        return rr

    def _get_all_class(self):
        """ get informations in terms of all class.

        Parameters
        ----------
        idx : int
            class index.
            vaild values : range(0, a.get_class_count())

        Returns
        -------
        array of numpy structured array("ClassifierClass")
            numpy structured array("ClassifierClass")
                category : int, class category index.
                prob : float, class probability.
        """

        cnt = self.get_class_count()
        rr = numpy.zeros((cnt,), dtype=NumpyClassifierClass)
        for idx in range(cnt):
            res = core.ClassifierClass()
            code = core.dll.ailiaClassifierGetClass(self.__cls, ctypes.byref(res), ctypes.c_uint(idx), core.ClassifierClass.VERSION)
            core.check_error(code, super().get_raw_pointer())
            rr[idx] = numpy.asarray([(res.category, res.prob)], dtype=NumpyClassifierClass)

        return rr


class PoseEstimator(Net):
    """ ailia pose estimator instance wrapper class """

    def __init__(self, stream_path, weight_path, env_id=ENVIRONMENT_AUTO, num_thread=MULTITHREAD_AUTO, algorithm=POSE_ALGORITHM_ACCULUS_POSE, memory_mode=None, debug_log=False, enable_layer_fusion=True):
        """ constructor of ailia pose stimator instance.

        Parameters
        ----------
        stream_path : str,
            network model file path (ex. "foobar.prototxt")
            for use onnx file, please specify None.
        weight_path : str,
            network weight file path (ex. "foobar.caffemodel")
        env_id : int, optional, default:ENVIRONMENT_AUTO(-1)
            environment id of ailia excecution.
            To retrieve env_id value, use
                get_environment_count() / get_environment() pair
            or
                get_gpu_environment_id() .
        num_thread : int, optional, default: MULTITHREAD_AUTO(0)
            number of threads.
            valid values:
                MULTITHREAD_AUTO=0 [means systems's logical processor count],
                1 to 32.
        algorithm : int, optional, default=POSE_ALGORITHM_ACCULUS_POSE(0)
            algorithm selector, use ALGORITHM_*
        debug_log : bool, optional, default: False
            enable trace logging and verbose log for ailia.
        enable_layer_fusion : bool, optional, default: True
            enable layer fusion optimization.
        memory_mode : int or None, optional, default: None
            memory management mode of ailia excecution.
            To retrieve memory_mode value, use get_memory_mode() .
        """
        self.__pose = ctypes.c_void_p(None)
        super().__init__(stream_path, weight_path, env_id, num_thread, memory_mode=memory_mode, debug_log=debug_log, enable_layer_fusion=enable_layer_fusion)
        code = pose_core.dll.ailiaCreatePoseEstimator(ctypes.byref(self.__pose), super().get_raw_pointer(), ctypes.c_int(algorithm))
        core.check_error(code)
        self.persons = None
        self._algorithm = algorithm

    def __del__(self):
        """ destructor of ailia pose estimator instance. """
        if self.__pose is not None:
            pose_core.dll.ailiaDestroyPoseEstimator(self.__pose)
        super().__del__()

    def compute(self, image):
        """ run the ailia pose stimator with a input image.

        Parameters
        ----------
        image : numpy.ndarray
            input image data. expect a result of cv2.imread(img_path, cv2.IMREAD_UNCHANGED) .
        """
        core.check_image_argument_ndarray(image, "image")
        stride = image.shape[1] * image.shape[2]
        width = image.shape[1]
        height = image.shape[0]
        format = core.get_image_format(image)
        code = pose_core.dll.ailiaPoseEstimatorCompute(self.__pose, image, stride, width, height, format)
        core.check_error(code, super().get_raw_pointer())

    def run(self, image, max_class_count=1):
        """ run the ailia pose stimator with a input image.

        Parameters
        ----------
        image : numpy.ndarray
            input image data. expect a result of cv2.imread(img_path, cv2.IMREAD_UNCHANGED) .

        Returns
        -------
        algorithm==POSE_ALGORITHM_ACCULUS_POSE or algorithm==POSE_ALGORITHM_OPEN_POSE
        or algorithm==POSE_ALGORITHM_LW_HUMAN_POSE or algorithm==POSE_ALGORITHM_OPEN_POSE_SINGLE_SCALE

        array of numpy structured array("PoseEstimatorObjectPose")
            numpy structured array("PoseEstimatorObjectPose")
                points : array of numpy structured array("PoseEstimatorKeypoint")
                    numpy strucuted array("PoseEstimatorKeypoint")
                        x : float, keypoint position
                        y : float, keypoint position
                        z_local : float, keypoint position
                        score : float, keypoint probablity
                        interpolated : int, 0 or 1
                total_score : float, sum of object probability.
                num_valid_points : int, number of valid key points
                id : int, person id
                angle_x : float, object angle
                angle_y : float, object angle
                angle_z : float, object angle

        algorithm==POSE_ALGORITHM_ACCULUS_UPPOSE or algorithm==POSE_ALGORITHM_ACCULUS_UPPOSE_FPGA

        array of numpy structured array("PoseEstimatorObjectUpPose")
            numpy structured array("PoseEstimatorObjectUpPose")
                points : array of numpy structured array("PoseEstimatorKeypoint")
                    numpy strucuted array("PoseEstimatorKeypoint")
                        x : float, keypoint position
                        y : float, keypoint position
                        z_local : float, keypoint position
                        score : float, keypoint probablity
                        interpolated : int, 0 or 1
                total_score : float, sum of object probability.
                num_valid_points : int, number of valid key points
                id : int, person id
                angle_x : float, object angle
                angle_y : float, object angle
                angle_z : float, object angle

        algorithm==POSE_ALGORITHM_ACCULUS_HAND

        array of numpy structured array("PoseEstimatorObjectHand")
            numpy structured array("PoseEstimatorObjectHand")
                points : array of numpy structured array("PoseEstimatorKeypoint")
                    numpy strucuted array("PoseEstimatorKeypoint")
                        x : float, keypoint position
                        y : float, keypoint position
                        z_local : float, keypoint position
                        score : float, keypoint probablity
                        interpolated : int, 0 or 1
                total_score : float, sum of object probability.
        """

        self.compute(image)

        if self._algorithm == POSE_ALGORITHM_ACCULUS_POSE or self._algorithm == POSE_ALGORITHM_OPEN_POSE or self._algorithm == POSE_ALGORITHM_LW_HUMAN_POSE or self._algorithm == POSE_ALGORITHM_OPEN_POSE_SINGLE_SCALE:
            return self._get_all_objects_pose()
        if self._algorithm == POSE_ALGORITHM_ACCULUS_UPPOSE or self._algorithm == POSE_ALGORITHM_ACCULUS_UPPOSE_FPGA:
            return self._get_all_objects_up_pose()
        if self._algorithm == POSE_ALGORITHM_ACCULUS_HAND:
            return self._get_all_objects_hand()
        raise core.AiliaException(core.AiliaInvalidArgumentException)

    def get_object_count(self):
        """ get detected object count.

        Returns
        -------
        int
            number of objects.
        """
        result = ctypes.c_uint(0)
        code = pose_core.dll.ailiaPoseEstimatorGetObjectCount(self.__pose, ctypes.byref(result))
        core.check_error(code, super().get_raw_pointer())
        return result.value

    def get_object_pose(self, idx):
        """ get a detected object detail specified by idx.

        Parameters
        ----------
        idx : int
            object index.
            vaild values : range(0, a.get_object_count())

        Returns
        -------
        namedtuple("PoseEstimatorObjectPose")
            points : list of namedtuple("PoseEstimatorKeypoint")
                namedtuple("PoseEstimatorKeypoint")
                    x : float, keypoint position
                    y : float, keypoint position
                    z_local : float, keypoint position
                    score : float, keypoint probablity
                    interpolated : int, 0 or 1
            total_score : float, sum of object probability.
            num_valid_points : int, number of valid key points
            id : int, person id
            angle_x : float, object angle
            angle_y : float, object angle
            angle_z : float, object angle
        """
        #warnings.warn("\'PoseEstimator.get_object_pose\' is deprecated , please use \'PoseEstimator.run\' instead.", UserWarning, stacklevel=2)
        obj = pose_core.PoseEstimatorObjectPose()
        code = pose_core.dll.ailiaPoseEstimatorGetObjectPose(self.__pose, ctypes.byref(obj), ctypes.c_uint(idx), obj.VERSION)
        core.check_error(code, super().get_raw_pointer())

        k_list = []
        for i in range(POSE_KEYPOINT_CNT):
            k = PoseEstimatorKeypoint(
                x=obj.points[i].x,
                y=obj.points[i].y,
                z_local=obj.points[i].z_local,
                score=obj.points[i].score,
                interpolated=obj.points[i].interpolated,
            )
            k_list.append(k)

        r = PoseEstimatorObjectPose(
            points=k_list,
            total_score=obj.total_score,
            num_valid_points=obj.num_valid_points,
            id=obj.id,
            angle_x=obj.angle_x,
            angle_y=obj.angle_y,
            angle_z=obj.angle_z
        )

        return r

    def _get_all_objects_pose(self):
        """ get details of all detected 'pose' objects.

        Returns
        -------
        array of numpy structured array("PoseEstimatorObjectPose")
            numpy structured array("PoseEstimatorObjectPose")
                points : array of numpy structured array("PoseEstimatorKeypoint")
                    numpy strucuted array("PoseEstimatorKeypoint")
                        x : float, keypoint position
                        y : float, keypoint position
                        z_local : float, keypoint position
                        score : float, keypoint probablity
                        interpolated : int, 0 or 1
                total_score : float, sum of object probability.
                num_valid_points : int, number of valid key points
                id : int, person id
                angle_x : float, object angle
                angle_y : float, object angle
                angle_z : float, object angle
        """
        cnt = self.get_object_count()
        rr = numpy.zeros((cnt,), dtype=NumpyPoseEstimatorObjectPose)
        for idx in range(cnt):
            obj = pose_core.PoseEstimatorObjectPose()
            code = pose_core.dll.ailiaPoseEstimatorGetObjectPose(self.__pose, ctypes.byref(obj), ctypes.c_uint(idx), obj.VERSION)
            core.check_error(code, super().get_raw_pointer())

            pose_keypoints = numpy.zeros((POSE_KEYPOINT_CNT,), dtype=NumpyPoseEstimatorKeypoint)
            for i in range(POSE_KEYPOINT_CNT):
                op = obj.points[i]
                pose_keypoints[i] = numpy.asarray([(op.x, op.y, op.z_local, op.score, op.interpolated)], dtype=NumpyPoseEstimatorKeypoint)

            rr[idx] = numpy.asarray([(
                pose_keypoints,
                obj.total_score,
                obj.num_valid_points,
                obj.id,
                obj.angle_x,
                obj.angle_y,
                obj.angle_z
            )], dtype=NumpyPoseEstimatorObjectPose)

        return rr

    def get_object_up_pose(self, idx):
        """ get a detected object detail specified by idx.

        Parameters
        ----------
        idx : int
            object index.
            vaild values : range(0, a.get_object_count())

        Returns
        -------
        namedtuple("PoseEstimatorObjectUpPose")
            points : list of namedtuple("PoseEstimatorKeypoint")
                namedtuple("PoseEstimatorKeypoint")
                    x : float, keypoint position
                    y : float, keypoint position
                    z_local : float, keypoint position
                    score : float, keypoint probablity
                    interpolated : int, 0 or 1
            total_score : float, sum of object probability.
            num_valid_points : int, number of valid key points
            id : int, person id
            angle_x : float, object angle
            angle_y : float, object angle
            angle_z : float, object angle
        """
        #warnings.warn("\'PoseEstimator.get_object_up_pose\' is deprecated , please use \'PoseEstimator.run\' instead.", UserWarning, stacklevel=2)

        obj = pose_core.PoseEstimatorObjectUpPose()
        code = pose_core.dll.ailiaPoseEstimatorGetObjectUpPose(self.__pose, ctypes.byref(obj), ctypes.c_uint(idx), obj.VERSION)
        core.check_error(code, super().get_raw_pointer())

        k_list = []
        for i in range(POSE_UPPOSE_KEYPOINT_CNT):
            k = PoseEstimatorKeypoint(
                x=obj.points[i].x,
                y=obj.points[i].y,
                z_local=obj.points[i].z_local,
                score=obj.points[i].score,
                interpolated=obj.points[i].interpolated,
            )
            k_list.append(k)

        r = PoseEstimatorObjectUpPose(
            points=k_list,
            total_score=obj.total_score,
            num_valid_points=obj.num_valid_points,
            id=obj.id,
            angle_x=obj.angle_x,
            angle_y=obj.angle_y,
            angle_z=obj.angle_z
        )

        return r

    def _get_all_objects_up_pose(self):
        """ get details of all detected 'up-pose' objects.

        Returns
        -------
        array of numpy structured array("PoseEstimatorObjectUpPose")
            numpy structured array("PoseEstimatorObjectUpPose")
                points : array of numpy structured array("PoseEstimatorKeypoint")
                    numpy strucuted array("PoseEstimatorKeypoint")
                        x : float, keypoint position
                        y : float, keypoint position
                        z_local : float, keypoint position
                        score : float, keypoint probablity
                        interpolated : int, 0 or 1
                total_score : float, sum of object probability.
                num_valid_points : int, number of valid key points
                id : int, person id
                angle_x : float, object angle
                angle_y : float, object angle
                angle_z : float, object angle
        """
        cnt = self.get_object_count()
        rr = numpy.zeros((cnt,), dtype=NumpyPoseEstimatorObjectUpPose)
        for idx in range(cnt):
            obj = pose_core.PoseEstimatorObjectUpPose()
            code = pose_core.dll.ailiaPoseEstimatorGetObjectUpPose(self.__pose, ctypes.byref(obj), ctypes.c_uint(idx), obj.VERSION)
            core.check_error(code, super().get_raw_pointer())
            pose_keypoints = numpy.zeros((POSE_UPPOSE_KEYPOINT_CNT,), dtype=NumpyPoseEstimatorKeypoint)
            for i in range(POSE_UPPOSE_KEYPOINT_CNT):
                op = obj.points[i]
                pose_keypoints[i] = numpy.asarray([(op.x, op.y, op.z_local, op.score, op.interpolated)], dtype=NumpyPoseEstimatorKeypoint)

            rr[idx] = numpy.asarray([(
                pose_keypoints,
                obj.total_score,
                obj.num_valid_points,
                obj.id,
                obj.angle_x,
                obj.angle_y,
                obj.angle_z
            )], dtype=NumpyPoseEstimatorObjectUpPose)

        return rr

    def get_object_hand(self, idx):
        """ get a detected object detail specified by idx.

        Parameters
        ----------
        idx : int
            object index.
            vaild values : range(0, a.get_object_count())

        Returns
        -------
        r : namedtuple("PoseEstimatorObjectHand")
            points : list of namedtuple("PoseEstimatorKeypoint")
                namedtuple("PoseEstimatorKeypoint")
                    x : float, keypoint position
                    y : float, keypoint position
                    z_local : float, keypoint position
                    score : float, keypoint probablity
                    interpolated : int, 0 or 1
            total_score : float, sum of object probability.
        """
        #warnings.warn("\'PoseEstimator.get_object_hand\' is deprecated , please use \'PoseEstimator.run\' instead.", UserWarning, stacklevel=2)
        obj = pose_core.PoseEstimatorObjectHand()
        code = pose_core.dll.ailiaPoseEstimatorGetObjectHand(self.__pose, ctypes.byref(obj), ctypes.c_uint(idx), obj.VERSION)
        core.check_error(code, super().get_raw_pointer())

        k_list = []
        for i in range(POSE_HAND_KEYPOINT_CNT):
            k = PoseEstimatorKeypoint(
                x=obj.points[i].x,
                y=obj.points[i].y,
                z_local=obj.points[i].z_local,
                score=obj.points[i].score,
                interpolated=obj.points[i].interpolated,
            )
            k_list.append(k)

        r = PoseEstimatorObjectHand(
            points=k_list,
            total_score=obj.total_score
        )

        return r

    def _get_all_objects_hand(self):
        """ get details of all detected 'hand' objects.

        Returns
        -------
        array of numpy structured array("PoseEstimatorObjectHand")
            numpy structured array("PoseEstimatorObjectHand")
                points : array of numpy structured array("PoseEstimatorKeypoint")
                    numpy strucuted array("PoseEstimatorKeypoint")
                        x : float, keypoint position
                        y : float, keypoint position
                        z_local : float, keypoint position
                        score : float, keypoint probablity
                        interpolated : int, 0 or 1
                total_score : float, sum of object probability.
        """
        cnt = self.get_object_count()
        rr = numpy.zeros((cnt,), dtype=NumpyPoseEstimatorObjectHand)
        for i in range(cnt):

            obj = pose_core.PoseEstimatorObjectHand()
            code = pose_core.dll.ailiaPoseEstimatorGetObjectHand(self.__pose, ctypes.byref(obj), ctypes.c_uint(i), obj.VERSION)
            core.check_error(code, super().get_raw_pointer())
            keypoints = numpy.zeros((POSE_HAND_KEYPOINT_CNT,), dtype=NumpyPoseEstimatorKeypoint)
            for i in range(POSE_HAND_KEYPOINT_CNT):
                keypoints[i] = numpy.asarray([(
                    obj.points[i].x,
                    obj.points[i].y,
                    obj.points[i].z_local,
                    obj.points[i].score,
                    obj.points[i].interpolated,
                )], dtype=NumpyPoseEstimatorKeypoint)

            rr[i] = numpy.asarray([(
                keypoints,
                obj.total_score
            )], dtype=NumpyPoseEstimatorObjectHand)

        return rr

    def set_threshold(self, thre):
        code = pose_core.dll.ailiaPoseEstimatorSetThreshold(self.__pose, thre)
        core.check_error(code, super().get_raw_pointer())
