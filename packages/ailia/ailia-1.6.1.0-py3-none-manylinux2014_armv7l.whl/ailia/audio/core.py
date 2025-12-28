#### ailia audio python binding core api ####

import ctypes
import os
import sys
import numpy
import platform

#### loading DLL / DYLIB / SO  ####
if sys.platform == "win32":
    dll_platform = "windows/x64"
    dll_name = "ailia_audio.dll"
    load_fn = ctypes.WinDLL
elif sys.platform == "darwin":
    dll_platform = "mac"
    dll_name = "libailia_audio.dylib"
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
    dll_name = "libailia_audio.so"
    load_fn = ctypes.CDLL

dll_found = False
candidate = ["", str(os.path.dirname(os.path.abspath(__file__))) + str(os.sep), str(os.path.dirname(os.path.abspath(__file__))) + str(os.sep) + ".." + str(os.sep), str(os.path.dirname(os.path.abspath(__file__))) + str(os.sep) + ".." + str(os.sep) + dll_platform + str(os.sep)]
for dir in candidate:
    try:
        dll = load_fn(dir + dll_name)
        dll_found = True
    except:
        pass
if not dll_found:
    msg = "DLL load failed : \'" + dll_name + "\' is not found"
    raise ImportError(msg)

#### API Definition ####

# ailiaAudioConvertPowerToDB
dll.ailiaAudioConvertPowerToDB.restype = ctypes.c_int
dll.ailiaAudioConvertPowerToDB.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                             # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                             # src
    ctypes.c_int,                                  # src_n
    ctypes.c_float                                 # top_db
)

# ailiaAudioLog1p
dll.ailiaAudioLog1p.restype = ctypes.c_int
dll.ailiaAudioLog1p.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                             # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                             # src
    ctypes.c_int                                   # src_n
)

# ailiaAudioFFT
dll.ailiaAudioFFT.restype = ctypes.c_int
dll.ailiaAudioFFT.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int                                    # fft_n
)

# ailiaAudioGetSpectrogram
dll.ailiaAudioGetSpectrogram.restype = ctypes.c_int
dll.ailiaAudioGetSpectrogram.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                   # sample_n
    ctypes.c_int,                                   # fft_n
    ctypes.c_int,                                   # hop_n
    ctypes.c_int,                                   # win_n
    ctypes.c_int,                                   # win_type
    ctypes.c_int,                                   # frame_n
    ctypes.c_int,                                   # center
    ctypes.c_float,                                 # power
    ctypes.c_int                                    # norm_type
)

# ailiaAudioGetFrameLen
dll.ailiaAudioGetFrameLen.restype = ctypes.c_int
dll.ailiaAudioGetFrameLen.argtypes = (
    ctypes.POINTER(ctypes.c_int),                   # frame_n
    ctypes.c_int,                                   # sample_n
    ctypes.c_int,                                   # fft_n
    ctypes.c_int,                                   # hop_n
    ctypes.c_int,                                   # center
)

# ailiaAudioGetWindow
dll.ailiaAudioGetWindow.restype = ctypes.c_int
dll.ailiaAudioGetWindow.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    ctypes.c_int,                                   # fft_n
    ctypes.c_int,                                   # win_type
)

# ailiaAudioGetFBMatrix
dll.ailiaAudioGetFBMatrix.restype = ctypes.c_int
dll.ailiaAudioGetFBMatrix.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    ctypes.c_int,                                   # freq_n
    ctypes.c_float,                                 # f_min
    ctypes.c_float,                                 # f_max
    ctypes.c_int,                                   # mel_n
    ctypes.c_int,                                   # sample_rate
    ctypes.c_int,                                   # norm_type
    ctypes.c_int                                    # mel_formula
)

# ailiaAudioGetMelSpectrogram
dll.ailiaAudioGetMelSpectrogram.restype = ctypes.c_int
dll.ailiaAudioGetMelSpectrogram.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                   # sample_n
    ctypes.c_int,                                   # sample_rate
    ctypes.c_int,                                   # fft_n
    ctypes.c_int,                                   # hop_n
    ctypes.c_int,                                   # win_n
    ctypes.c_int,                                   # win_type
    ctypes.c_int,                                   # frame_n
    ctypes.c_int,                                   # center
    ctypes.c_float,                                 # power
    ctypes.c_int,                                   # norm_type (stft)
    ctypes.c_float,                                 # f_min
    ctypes.c_float,                                 # f_max
    ctypes.c_int,                                   # mel_n
    ctypes.c_int,                                   # norm_type (mel)
    ctypes.c_int                                    # mel_formula
)

# ailiaAudioMagPhase
dll.ailiaAudioMagPhase.restype = ctypes.c_int
dll.ailiaAudioMagPhase.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst_mag
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst_phase
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                   # freq_n
    ctypes.c_int,                                   # frame_n
    ctypes.c_float,                                 # power
    ctypes.c_int                                    # phase_form
)

# ailiaAudioStandardize
dll.ailiaAudioStandardize.restype = ctypes.c_int
dll.ailiaAudioStandardize.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int                                    # src_n
)


# ailiaAudioFixFrameLen
dll.ailiaAudioFixFrameLen.restype = ctypes.c_int
dll.ailiaAudioFixFrameLen.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                   # freq_n
    ctypes.c_int,                                   # dst_frame_n
    ctypes.c_int,                                   # src_frame_n
    ctypes.c_float                                  # pad_data
)

# ailiaAudioIFFT
dll.ailiaAudioIFFT.restype = ctypes.c_int
dll.ailiaAudioIFFT.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int                                    # fft_n
)

# ailiaAudioGetSampleLen
dll.ailiaAudioGetSampleLen.restype = ctypes.c_int
dll.ailiaAudioGetSampleLen.argtypes = (
    ctypes.POINTER(ctypes.c_int),                   # sample_n
    ctypes.c_int,                                   # frame_n
    ctypes.c_int,                                   # fft_n
    ctypes.c_int,                                   # hop_n
    ctypes.c_int,                                   # center
)

# ailiaAudioGetSpectrogram
dll.ailiaAudioGetInverseSpectrogram.restype = ctypes.c_int
dll.ailiaAudioGetInverseSpectrogram.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                   # frame_n
    ctypes.c_int,                                   # freq_n
    ctypes.c_int,                                   # hop_n
    ctypes.c_int,                                   # win_n
    ctypes.c_int,                                   # win_type
    ctypes.c_int,                                   # max_sample_n
    ctypes.c_int,                                   # center
    ctypes.c_int                                    # norm_type
)

# ailiaAudioComplexNorm
dll.ailiaAudioComplexNorm.restype = ctypes.c_int
dll.ailiaAudioComplexNorm.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                    # src_n
    ctypes.c_float                                   # power
)

# ailiaAudioConvertToMel
dll.ailiaAudioConvertToMel.restype = ctypes.c_int
dll.ailiaAudioConvertToMel.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # fb_mtrx
    ctypes.c_int,                                   # freq_n
    ctypes.c_int,                                   # frame_n
    ctypes.c_int                                    # mel_n
)

# ailiaAudioResample
dll.ailiaAudioResample.restype = ctypes.c_int
dll.ailiaAudioResample.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                   # dst_sample_rate
    ctypes.c_int,                                   # dst_n
    ctypes.c_int,                                   # src_sample_rate
    ctypes.c_int                                    # src_n
)

# ailiaAudioGetResampleLen
dll.ailiaAudioGetResampleLen.restype = ctypes.c_int
dll.ailiaAudioGetResampleLen.argtypes = (
    ctypes.POINTER(ctypes.c_int),                   # dst_sample_n
    ctypes.c_int,                                   # dst_sample_rate
    ctypes.c_int,                                   # src_sample_n
    ctypes.c_int                                    # src_sample_rate
)

# ailiaAudioLinerFilter
dll.ailiaAudioLinerFilter.restype = ctypes.c_int
dll.ailiaAudioLinerFilter.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # n_coef
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # d_coef
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # zi
    ctypes.c_int,                                   # dst_n
    ctypes.c_int,                                   # src_n
    ctypes.c_int,                                   # n_coef_n
    ctypes.c_int,                                   # d_coef_n
    ctypes.c_int                                    # zi_n
)

# ailiaAudioGetLinerFilterZiCoef
dll.ailiaAudioGetLinerFilterZiCoef.restype = ctypes.c_int
dll.ailiaAudioGetLinerFilterZiCoef.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst_zi
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # n_coef
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # d_coef
    ctypes.c_int,                                   # dst_n
    ctypes.c_int,                                   # n_coef_n
    ctypes.c_int                                   # d_coef_n
)

# ailiaAudioFilterFilter
dll.ailiaAudioFilterFilter.restype = ctypes.c_int
dll.ailiaAudioFilterFilter.argtypes = (
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # dst
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # n_coef
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # d_coef
    ctypes.c_int,                                   # dst_n
    ctypes.c_int,                                   # src_n
    ctypes.c_int,                                   # n_coef_n
    ctypes.c_int,                                   # d_coef_n
    ctypes.c_int,                                   # pad_type
    ctypes.c_int                                    # pad_len
)

# ailiaAudioGetNonSilentPos
dll.ailiaAudioGetNonSilentPos.restype = ctypes.c_int
dll.ailiaAudioGetNonSilentPos.argtypes = (
    ctypes.POINTER(ctypes.c_int),                   # dst_start_pos
    ctypes.POINTER(ctypes.c_int),                   # dst_length
    numpy.ctypeslib.ndpointer(
        dtype=numpy.float32, flags='CONTIGUOUS'
    ),                                              # src
    ctypes.c_int,                                   # sample_n
    ctypes.c_int,                                   # win_n
    ctypes.c_int,                                   # hop_n
    ctypes.c_float                                   # thr_db
)

# utils


def set_wav_param(wav):
    if wav.ndim == 1:
        wav = wav[None, :]
        ch_n, sample_n = wav.shape
    elif wav.ndim == 2:
        ch_n, sample_n = wav.shape
        ch_n_limit = 128
        if ch_n > ch_n_limit:
            raise ValueError(f"Too many channels. Upper limit is {ch_n_limit}, but {ch_n} was given.")
    else:
        raise ValueError("Invalid input shape")

    return wav, sample_n, ch_n


def set_spec_param(spec):
    if spec.ndim == 1:
        spec = spec[None, None, :]
    elif spec.ndim == 2:
        spec = spec[None, :, :]

    if spec.ndim == 3:
        ch_n, freq_n, frame_n = spec.shape
    else:
        raise ValueError("Invalid input shape.")

    return spec, frame_n, freq_n, ch_n


def set_fft_param(fft_n, hop_n, win_n):
    if hop_n == None:
        hop_n = int(fft_n // 4)

    freq_n = int(fft_n // 2 + 1)

    if win_n == None:
        win_n = fft_n

    return fft_n, hop_n, freq_n, win_n


def set_invfft_param(freq_n, hop_n, win_n):
    fft_n = int((freq_n - 1) * 2)

    if hop_n == None:
        hop_n = int(fft_n // 4)

    if win_n == None:
        win_n = fft_n

    return fft_n, hop_n, freq_n, win_n


def set_window_param(win_type):
    if type(win_type) == int:
        return win_type

    if win_type == "hann":
        win = 1
    elif win_type == "hamming":
        win = 2
    else:
        win = 1

    return win


def set_fft_norm(norm_type):
    if type(norm_type) == int:
        return norm_type

    if norm_type == None:
        norm = 0
    elif norm_type == "scipy":
        norm = 2
    elif norm_type in ("librosa", "torch"):
        norm = 1
    else:
        norm = 0

    return norm


def set_mel_norm(norm_type):
    if type(norm_type) == int:
        return norm_type

    if norm_type == None:
        norm = 0

    elif norm_type == True:
        norm = 1
    else:
        norm = 0

    return norm


def set_filtflit_pad_type(pad_type):
    if pad_type is None:
        return 0

    if type(pad_type) == int:
        return pad_type

    if pad_type == "odd":
        pad = 1
    elif pad_type == "even":
        pad = 2
    elif pad_type == "constant":
        pad = 3
    else:
        pad = 0

    return pad


def nextpow2(n):
    m_f = numpy.log2(n)
    m_i = numpy.ceil(m_f)
    return int(2 ** m_i)


def convert_ndarray(data, dtype=numpy.float32):
    if isinstance(data, numpy.ndarray):
        if data.flags['C_CONTIGUOUS'] and data.dtype is dtype:
            return data
        return data.astype(dtype, order='C')
    else:
        return numpy.array(data, dtype=numpy.float32, order='C')


def to_mono(wav):
    wav, _, ch_n = set_wav_param(wav)
    if(ch_n > 1):
        wav = numpy.mean(wav, axis=0)
        return wav
    return wav[0]
