from . import core as audio_core
from .. import core
import numpy
import ctypes

# ailia_audio APIs


def log1p(signal):
    """ calculate log1p ( y = log_e(1.0 + x) )

    Parameters
    ----------
    signal : numpy.ndarray
        input signal.

    Returns
    -------
    res : numpy.ndarray
        output signal.

    """
    res = audio_core.convert_ndarray(signal)
    code = audio_core.dll.ailiaAudioLog1p(res, res, signal.size)
    core.check_error(code)

    return res


def fft(signal):
    """ run fast fourier transform (FFT)

    Parameters
    ----------
    signal : numpy.ndarray
        input signal.

    Returns
    -------
    res : numpy.ndarray
        created spectrum.

    """
    fft_n = audio_core.nextpow2(len(signal))
    res_ = numpy.zeros((fft_n, 2), dtype=numpy.float32, order='C')
    sig_ = numpy.zeros((fft_n,), dtype=numpy.float32, order='C')
    sig_[:len(signal)] = signal

    code = audio_core.dll.ailiaAudioFFT(res_, sig_, fft_n)
    core.check_error(code)
    res = res_[:, 0] + 1j * res_[:, 1]

    return res


def ifft(spec):
    """ run inverse fast fourier transform (IFFT)

    Parameters
    ----------
    signal : numpy.ndarray(dtype=complex)
        input spectrum.

    Returns
    -------
    res : numpy.ndarray(dytpe=complex)
        created spectrum.

    """
    fft_n = audio_core.nextpow2(len(spec))
    res_ = numpy.zeros((fft_n, 2), dtype=numpy.float32, order='C')
    spec_ = numpy.zeros((fft_n, 2), dtype=numpy.float32, order='C')
    spec_[:len(spec), 0] = spec.real
    spec_[:len(spec), 1] = spec.imag

    code = audio_core.dll.ailiaAudioIFFT(res_, spec_, fft_n)
    core.check_error(code)
    res = res_[:, 0] + 1j * res_[:, 1]

    return res


def convert_power_to_db(signal, top_db=None):
    """ turn a spectrogram from the power scale to the decibel scale.

    Parameters
    ----------
    signal : numpy.ndarray
        input signal in power scale.
    top_db : float, optional, default: 80.0
        threshold the output at top_db below the peak.

    Returns
    -------
    res : numpy.ndarray
        output signal in decibel scale.

    """
    if (top_db == None):
        top_db = 80.0
    res = audio_core.convert_ndarray(signal)
    code = audio_core.dll.ailiaAudioConvertPowerToDB(res, res, signal.size, top_db)
    core.check_error(code)

    return res


def get_frame_len(sample_n, fft_n, hop_n=None, center_mode=1):
    """ Calculate the number of frames when a spectrogram is created.

    Parameters
    ----------
    sample_n : int
        length of audio signal.
    fft_n : int
        size of FFT, creates fft_n // 2 + 1 bins
        requirements :
            fft_n == 2 ** m (m = 1,2,...)
    hop_n : int, optional, default: (fft_n//4)
        length of hop between STFT window
    center_mode : int, optional, default: 1
        whether to pad an audio signal on both sides.
            0 : ignored.
            1 : audio signal is padded on both sides with its own reflection, mirrored around its first and last sample respectively.
            2 : audio signal is padded on both sides with zero. Then,it is padded to integer number of windowed segments.

    Returns
    -------
    frame_n : int
        frame number of created spectrogram.

    """
    if hop_n == None:
        hop_n = int(fft_n // 4)
    frame_n = ctypes.c_int(0)
    code = audio_core.dll.ailiaAudioGetFrameLen(ctypes.byref(frame_n), sample_n, fft_n, hop_n, center_mode)
    core.check_error(code)

    return frame_n.value


def get_sample_len(frame_n, freq_n, hop_n=None, center=True):
    """ Calculate the number of samples when a signal is inversely transformed from a spectrogram

    Parameters
    ----------
    frame_n : int
        frame number of spectrogram.
    freq_n : int
        frequency of spectrgram.
        freq_n =  fft_n // 2 + 1
    hop_n : int, optional, default: (fft_n//4)
        length of hop between STFT window
    center : bool, optional, default: True
            True : input spectrogram is assumed to habe centered frames.
            False : input spectrogram is assumed to have left-aligned frames.

    Returns
    -------
    sample_n : int
        length of signal.

    """
    if hop_n == None:
        fft_n = (freq_n - 1) * 2
        hop_n = int(fft_n // 4)
    sample_n = ctypes.c_int(0)
    code = audio_core.dll.ailiaAudioGetSampleLen(ctypes.byref(sample_n), frame_n, freq_n, hop_n, center)
    core.check_error(code)

    return sample_n.value


def get_window(win_n, win_type):
    """ Create a window of a given length and type.

    Parameters
    ----------
    win_n : int, optional, default: fft_n
        window size.
    win_type : str or int, optional, default: 1
        type of window function.
        requirements :
            use hann window : "hann" or 1
                hamming window : "hamming" or 2

    Returns
    -------
    res : numpy.ndarray
        a window of given length and type.

    """
    win = audio_core.set_window_param(win_type)
    res = numpy.zeros((win_n,), dtype=numpy.float32, order='C')

    code = audio_core.dll.ailiaAudioGetWindow(res, win_n, win)
    core.check_error(code)

    return res


def get_fb_matrix(sample_rate, freq_n, f_min=0.0, f_max=None, mel_n=128, norm=False, htk=False):
    """ Create a Filterbank matrix to combine FFT bins into Mel-frequency bins

    Parameters
    ----------
    sample_rate : int
        sampling rate of the incoming signal
    freq_n : int
        number of FFT bins.
    f_min : float, optional, default: 0.0
        minimum frequency.
    f_max : float, optional, default: sample_rate // 2
        maximum frequency.
    mel_n : int, optional, default: 128
        number of mel bands.
    norm : bool, optional, default: False
        normalize created filterbank matrix.
    htk : bool, optional, default: False
        use HTK formula instead of Slaney's formula.

    Returns
    -------
    res : numpy.ndarray
        created filterbank matrix.

    """
    if f_max == None:
        f_max = sample_rate // 2

    res = numpy.zeros((mel_n, freq_n), dtype=numpy.float32, order='C')
    code = audio_core.dll.ailiaAudioGetFBMatrix(res, freq_n, f_min, f_max, mel_n, sample_rate, norm, htk)
    core.check_error(code)

    return res


def standardize(signal):
    """ Standardize input signal.

    Parameters
    ----------
    signal : numpy.ndarray
        input signal.

    Returns
    -------
    res : numpy.ndarray
        standardized signal.
    """
    res = audio_core.convert_ndarray(signal)
    code = audio_core.dll.ailiaAudioStandardize(res, res, signal.size)
    core.check_error(code)

    return res


def complex_norm(spec, power=1.0):
    """ Compute the norm of complex spectrogram

    Parameters
    ----------
    spec : numpy.ndarray(dtype=complex)
        input spectrogram.

    Returns
    -------
    res : numpy.ndarray
        the norm of complex spectrogram
    """
    ndim = spec.ndim
    spec, frame_n, freq_n, ch_n = audio_core.set_spec_param(spec)
    spec = audio_core.convert_ndarray(spec, dtype=numpy.complex64)
    spec_ = numpy.zeros((ch_n, freq_n, frame_n, 2), dtype=numpy.float32, order='C')
    spec_[..., 0] = spec.real
    spec_[..., 1] = spec.imag
    res = numpy.zeros((ch_n, freq_n, frame_n), dtype=numpy.float32, order='C')
    code = audio_core.dll.ailiaAudioComplexNorm(res, spec_, res.size, power)
    core.check_error(code)
    if ndim <= 2:
        res = res[0]
    return res


def fix_frame_len(spec, fix_frame_n, pad=0.0):
    """ Adjust frame length of a spectrogram.

    Parameters
    ----------
    spec : numpy.ndarray
        input data.
        requirements :
            input.shape must be (ch_n, freq_n, frame_n) or (freq_n, frame_n)
    fix_frame_n : int
            target number of time frames.
    pad : float, optional, default: 0.0
        constant value to fill the added frames.

    Returns
    -------
    res : numpy.ndarray

    """
    ndim = spec.ndim
    spec, frame_n, freq_n, ch_n = audio_core.set_spec_param(spec)
    spec = core.convert_input_ndarray(spec)
    res = numpy.zeros((ch_n, freq_n, fix_frame_n), dtype=numpy.float32, order='C')
    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioFixFrameLen(res[i], spec, freq_n, fix_frame_n, frame_n, pad)
        core.check_error(code)

    if ndim <= 2:
        res = res[0]

    return res


def magphase(spec, power=1.0, complex_out=True):
    """ Separate a complex-valued spectrogram into its magnitude and phase components.

    Parameters
    ----------
    spec : numpy.ndarray
        input data.
        requirements :
            input.shape must be (ch_n, freq_n, frame_n) or (freq_n, frame_n)
    power : float, optional, default: 1.0
        exponent for the magnitude spectrogram, e.g., 1 for energy, 2 for power, etc.
        requirements :
            power > 0.0
    complex_out : bool, optional, default: True
        return phase as complex value.
            True : compatible with librosa
            False : compatible with pytorch

    Returns
    -------
    res_mag : numpy.ndarray
        magnitude components of the input spectrogram.
    res_phase : numpy.ndarray
        phase components of the input spectrogram.

    """
    ndim = spec.ndim
    spec, frame_n, freq_n, ch_n = audio_core.set_spec_param(spec)
    spec = audio_core.convert_ndarray(spec, dtype=numpy.complex64)
    spec_ = numpy.zeros((ch_n, freq_n, frame_n, 2), dtype=numpy.float32, order='C')
    spec_[..., 0] = spec.real
    spec_[..., 1] = spec.imag
    res_mag = numpy.zeros((ch_n, freq_n, frame_n), dtype=numpy.float32, order='C')
    res_phase = numpy.zeros((ch_n, freq_n, frame_n), dtype=numpy.complex64, order='C')
    phase_buf = numpy.zeros((freq_n, frame_n, 2), dtype=numpy.float32, order='C')

    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioMagPhase(res_mag[i], phase_buf, spec_[i], freq_n, frame_n, power, complex_out)
        core.check_error(code)
        res_phase[i] = phase_buf[..., 0] + 1j * phase_buf[..., 1]
    if (ndim <= 2):
        res_mag = res_mag[0]
        res_phase = res_phase[0]

    return res_mag, res_phase


def mel_scale(spec, mel_fb):
    """ convert spectorogram to Mel spectrogram,using mel filter bank

    Parameters
    ----------
    spec : numpy.ndarray
        input real spectrogram.
        spec.shape must be (ch_n, freq_n, frame_n) or (freq_n, frame_n)
    mel_fb : numpy.ndarray
        Filterbank matrix to combine FFT bins into Mel-frequency bins
        mel_fb.shape must be (mel_n, freq_n)

    Returns
    -------
    res : numpy.ndarray
        created mel spectrogram.

    """
    if mel_fb.ndim == 2:
        mel_n, mel_freq_n = mel_fb.shape
    else:
        raise ValueError("Invalid mel_fb shape.")
    mel_fb = audio_core.convert_ndarray(mel_fb, dtype=numpy.float32)

    ndim = spec.ndim
    spec, frame_n, freq_n, ch_n = audio_core.set_spec_param(spec)
    spec = audio_core.convert_ndarray(spec, dtype=numpy.float32)
    if mel_freq_n != freq_n:
        raise ValueError("Do not match input spectrogram freq_n and mel_fb freq_n.")
    res = numpy.zeros((ch_n, mel_n, frame_n), dtype=numpy.float32, order='C')

    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioConvertToMel(res[i], spec[i, :], mel_fb, freq_n, frame_n, mel_n)
        core.check_error(code)

    if ndim <= 2:
        res = res[0]

    return res


def spectrogram(wav, fft_n=1024, hop_n=None, win_n=None, win_type=None, center_mode=1, power=None, norm_type=None):
    """ Create a spectrogram from a audio signal.

    Parameters
    ----------
    wav : numpy.ndarray
        input audio signal.
        wav.shape must be (sample_n,) or (channel_n, sample_n).
    fft_n : int, optional, default: 1024
        size of FFT, creates fft_n // 2 + 1 bins
        requirements :
            fft_n == 2 ** m, where m is a natural number
    hop_n : int, optional, default: fft_n // 4
        length of hop between STFT windows
    win_n : int, optional, default: fft_n
        window size.
    win_type : str or int, optional, default: 1
        type of window function.
        requirements :
            "hann" or 1 : hann window
            "hamming" or 2 : hamming window
    center_mode : int, optional, default: 1
        whether to pad an audio signal on both sides.
            0 : ignored.
            1 : audio signal is padded on both sides with its own reflection, mirrored around its first and last sample respectively.
            2 : audio signal is padded on both sides with zero. Then,it is padded to integer number of windowed segments.
    power : float, optional, default: 1.0
        exponent for the magnitude spectrogram, e.g., 1 for energy, 2 for power, etc.
        If None, then the complex spectrum is returned instead.
        requirements :
            power > 0.0
    norm_type : int, optional, default: 0
        types of output normalization.
        requirements :
            0 : ignored.
            1 : compatible with librosa and pytorch.
            2 : compatible with scipy.

    Returns
    -------
    res : numpy.ndarray
        created spectrogram.
        res.shape :
            (freq_n, frame_n) if input.ndim == 1
            (ch_n, freq_n, frame_n) if input.ndim == 2
    """

    ndim = wav.ndim
    wav, sample_n, ch_n = audio_core.set_wav_param(wav)
    wav = audio_core.convert_ndarray(wav)
    fft_n, hop_n, freq_n, win_n = audio_core.set_fft_param(fft_n, hop_n, win_n)
    win = audio_core.set_window_param(win_type)
    norm = audio_core.set_fft_norm(norm_type)

    frame_n = get_frame_len(sample_n, fft_n, hop_n, center_mode)
    res = numpy.zeros((ch_n, freq_n, frame_n), dtype=numpy.complex64, order='C')
    res_buf = numpy.zeros((freq_n, frame_n, 2), dtype=numpy.float32, order='C')

    if power is None:
        power = 0.0

    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioGetSpectrogram(res_buf, wav[i, :], sample_n, fft_n, hop_n, win_n, win, frame_n, center_mode, power, norm)
        core.check_error(code)
        res[i] = res_buf[..., 0] + 1j * res_buf[..., 1]

    if power != 0.0:
        res = numpy.real(numpy.abs(res))

    if (ndim == 1):
        res = res[0]

    return res


def inverse_spectrogram(spec, hop_n=None, win_n=None, win_type=None, center=True, norm_type=None):
    """ Inverse Transform from a spectrogram.

    Parameters
    ----------
    spec : numpy.ndarray(shape=(1 + fft_n/2, frame_n ) or (ch_n, 1 + fft_n/2, frame_n) ,dtype=complex)
        input spectrogram.
    hop_n : int, optional, default: win_n // 4
        length of hop between STFT windows
    win_n : int, optional, default: fft_n
        window size.
    win_type : str or int, optional, default: 1
        type of window function.
        requirements :
            "hann" or 1 : hann window
            "hamming" or 2 : hamming window
    center : bool, optional, default: True
            True : input spectrogram is assumed to habe centered frames.
            False : input spectrogram is assumed to have left-aligned frames.
    norm_type : int, optional, default: 0
        types of output normalization.
        requirements :
            0 : ignored.
            1 : compatible with librosa and pytorch.
            2 : compatible with scipy.

    Returns
    -------
    res : numpy.ndarray(dtype=float)
        signal with inverse transformation of spectrogram
        res.shape :
            (sample_n) if input.ndim == 1
            (ch_n, sample_n) if input.ndim == 2
    """

    ndim = spec.ndim
    spec, frame_n, freq_n, ch_n = audio_core.set_spec_param(spec)
    spec = audio_core.convert_ndarray(spec, dtype=numpy.complex64)
    spec_ = numpy.zeros((ch_n, freq_n, frame_n, 2), dtype=numpy.float32, order='C')
    spec_[..., 0] = spec.real
    spec_[..., 1] = spec.imag

    fft_n, hop_n, freq_n, win_n = audio_core.set_invfft_param(freq_n, hop_n, win_n)
    win = audio_core.set_window_param(win_type)
    norm = audio_core.set_fft_norm(norm_type)

    sample_n = get_sample_len(frame_n, freq_n, hop_n, center)
    res = numpy.zeros((ch_n, sample_n), dtype=numpy.float32, order='C')
    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioGetInverseSpectrogram(res[i], spec_[i, :], frame_n, freq_n, hop_n, win_n, win, sample_n, center, norm)
        core.check_error(code)

    if (ndim <= 2):
        res = res[0]

    return res


def mel_spectrogram(wav,
                    sample_rate=16000,
                    fft_n=1024,
                    hop_n=None,
                    win_n=None,
                    win_type=1,
                    center_mode=1,
                    power=1.0,
                    fft_norm_type=None,
                    f_min=0.0,
                    f_max=None,
                    mel_n=128,
                    mel_norm=True,
                    htk=False,
                    ):
    """ Create a melspectrogram.

    Parameters
    ----------
    wav : numpy.ndarray
        input audio signal.
        wav.shape must be (sample_n,) or (channel_n, sample_n).
    sample_rate : int, optional, default: 16000
        sample rate of input audio signal.
    fft_n : int, optional, default: 1024
        size of FFT, creates fft_n // 2 + 1 bins
        requirements :
            fft_n == 2 ** m, where m is a natural number
    hop_n : int, optional, default: fft_n // 4
        length of hop between STFT windows
    win_n : int, optional, default: fft_n
        window size.
    win_type : str or int, optional, default: 1
        type of window function.
        requirements :
            "hann" or 1 : hann window
            "hamming" or 2 : hamming window
    center_mode : int, optional, default: 1
        whether to pad an audio signal on both sides.
            0 : ignored.
            1 : audio signal is padded on both sides with its own reflection, mirrored around its first and last sample respectively.
            2 : audio signal is padded on both sides with zero. Then,it is padded to integer number of windowed segments.
    power : float, optional, default: 1.0
        exponent for the magnitude spectrogram, e.g., 1 for energy, 2 for power, etc.
        requirements :
            power > 0.0
    fft_norm_type : int, optional, default: 0
        types of spectrogram normalization.
        requirements :
            0 : ignored.
            1 : compatible with librosa and pytorch.
            2 : compatible with scipy.
    f_min : float, optional, default: 0.0
        minimum frequency.
    f_max : float, optional, default: sample_rate // 2
        maximum frequency.
    mel_n : int, optional, default: 128
        number of mel filter banks.
    mel_norm : bool, optional, default: True
        normalize melspectrofram.
    htk : bool, optional, default: False
        convert frequency to mel scale using htk formula.
            True : using htk formula. (compatible with pytorch. )
            False : using Slaney's formula. (compatible with a default setting of librosa. )

    Returns
    -------
    res : numpy.ndarray
        created melspectrogram.

    """
    if f_max == None:
        f_max = sample_rate // 2
    ndim = wav.ndim
    wav, sample_n, ch_n = audio_core.set_wav_param(wav)
    wav = audio_core.convert_ndarray(wav)
    fft_n, hop_n, freq_n, win_n = audio_core.set_fft_param(fft_n, hop_n, win_n)
    win = audio_core.set_window_param(win_type)
    fft_norm = audio_core.set_fft_norm(fft_norm_type)
    mel_norm = audio_core.set_mel_norm(mel_norm)
    frame_n = get_frame_len(sample_n, fft_n, hop_n, center_mode)
    res = numpy.zeros((ch_n, mel_n, frame_n), dtype=numpy.float32, order='C')

    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioGetMelSpectrogram(res[i], wav[i, :], sample_n, sample_rate, fft_n, hop_n, win_n, win, frame_n, center_mode, power, fft_norm, f_min, f_max, mel_n, mel_norm, htk)

        core.check_error(code)

    if ndim == 1:
        res = res[0]

    return res


# compatible function with a specific model

def compute_mel_spectrogram_with_fixed_length(wav, sample_rate=16000, fft_n=2048, hop_n=None, win_n=None, mel_n=128, max_frame_n=128):
    """ Create a melspectrogram.

    Parameters
    ----------
    wav : numpy.ndarray
        input audio signal.
        wav.shape must be (sample_n,) or (channel_n, sample_n).
    sample_rate : int, optional, default: 16000
        sample rate of input audio signal.
    fft_n : int, optional, default: 2048
        size of FFT, creates fft_n // 2 + 1 bins
        requirements :
            fft_n == 2 ** m (m = 1,2,...)
    hop_n : int, optional, default: fft_n // 4
        length of hop between STFT windows
    win_n : int, optional, default: fft_n // 4
        window size.
    mel_n : int, optional, default: 128
        number of mel filter banks.
    max_frame_n : int, optional, default: 128
        number of time frames of mel spectrogram.

    Returns
    -------
    res : numpy.ndarray
        created melspectrogram.

    """
    ndim = wav.ndim
    wav, sample_n, ch_n = audio_core.set_wav_param(wav)
    wav = audio_core.convert_ndarray(wav)
    if hop_n == None:
        hop_n = int(fft_n // 4)
    if win_n == None:
        win_n = int(fft_n // 4)
    win = audio_core.set_window_param("hann")
    power = 2.
    fft_norm = 0
    mel_norm = 1
    f_min = 0.0
    f_max = sample_rate // 2
    center_mode = 1
    frame_n = get_frame_len(sample_n, fft_n, hop_n, center_mode)
    htk = False
    pad_data = ctypes.c_float(-80.0)
    top_db = 80.0

    # compute a mel-scaled spectrogram
    res = numpy.zeros((ch_n, mel_n, max_frame_n), dtype=numpy.float32, order='C')
    res_ = numpy.zeros((mel_n, frame_n), dtype=numpy.float32, order='C')
    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioGetMelSpectrogram(res_, wav[i, :], sample_n, sample_rate, fft_n, hop_n, win_n, win, frame_n, center_mode, power, fft_norm, f_min, f_max, mel_n, mel_norm, htk)
        core.check_error(code)
        code = audio_core.dll.ailiaAudioConvertPowerToDB(res_, res_, frame_n * mel_n, top_db)
        core.check_error(code)
        code = audio_core.dll.ailiaAudioFixFrameLen(res[i], res_, mel_n, max_frame_n, frame_n, pad_data)
        core.check_error(code)

    if ndim == 1:
        res = res[0]

    return res


def get_resample_len(sample_n, org_sr, target_sr):
    """ Calculate the number of samples after resample.

    Parameters
    ----------
    sample_n : int
        length of audio signal.
    org_sr : int
        sampling rate of input audio signal
        requirements :
            org_sr > 0
    target_sr : int
        target sampling rate
        requirements :
            target_sr > 0

    Returns
    -------
    resample_n : int
        length of resampled audio signal.

    """
    resample_n = ctypes.c_int(0)
    code = audio_core.dll.ailiaAudioGetResampleLen(ctypes.byref(resample_n), target_sr, sample_n, org_sr)
    core.check_error(code)

    return resample_n.value


def resample(wav, org_sr, target_sr):
    """ resample  a audio signal form original sampling rate to target sampring rate

    Parameters
    ----------
    wav : numpy.ndarray
        input audio signal.
        wav.shape must be (sample_n,) or (channel_n, sample_n).
    org_sr : int
        sampling rate of input audio signal
        requirements :
            org_sr > 0
    target_sr : int
        target sampling rate
        requirements :
            target_sr > 0

    Returns
    -------
    res : numpy.ndarray
        created resample audio signal.

    """
    ndim = wav.ndim
    wav, sample_n, ch_n = audio_core.set_wav_param(wav)
    wav = audio_core.convert_ndarray(wav)
    resample_n = get_resample_len(sample_n, org_sr, target_sr)
    res_buf = numpy.zeros((ch_n, resample_n), dtype=numpy.float32, order='C')
    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioResample(res_buf[i], wav[i, ...], target_sr, resample_n, org_sr, sample_n)
        core.check_error(code)

    if (ndim == 1):
        res_buf = res_buf[0]

    return res_buf


def linerfilter(n_coef, d_coef, wav, axis=-1, zi=None):
    """ filter a audio signal, using a digital filter(ex.IIR or FIR)

    Parameters
    ----------
    n_coef : numpy.ndarray(ndim = 1)
        numerator coefficient.
    d_coef : numpy.ndarray(ndim = 1)
        denominator coefficient.
        If d_coef[0] is not 1, n_coef and d_coef are normalized by d_coef[0]
    wav : numpy.ndarray
        input audio signal.
        wav.shape must be (sample_n,) or (channel_n, sample_n).
    axis : int
        TBD
    zi : numpy.ndarray
        initial conditions for the filter delays.
        if zi is None, initial condition uses 0.

    Returns
    -------
    res : numpy.ndarray
        output filterd audio signal.

    zf : numpy.ndarray, optional
        final conditions for the filter delays.
        If `zi` is None, this is not returned.

    """
    ndim = wav.ndim
    wav, sample_n, ch_n = audio_core.set_wav_param(wav)
    wav = audio_core.convert_ndarray(wav)
    n_coef = audio_core.convert_ndarray(n_coef)
    d_coef = audio_core.convert_ndarray(d_coef)
    res_buf = numpy.zeros((ch_n, sample_n), dtype=numpy.float32, order='C')

    if n_coef.ndim != 1:
        raise ValueError('illegal n_coef shape.')
    if d_coef.ndim != 1:
        raise ValueError('illegal d_coef shape.')

    if zi is not None:
        zi, zi_n, zi_ch_n = audio_core.set_wav_param(zi)
        if zi_ch_n != ch_n:
            raise ValueError('illegal zi shape.')
        zi = audio_core.convert_ndarray(zi)

        for i in range(ch_n):
            code = audio_core.dll.ailiaAudioLinerFilter(res_buf[i], wav[i, ...], n_coef, d_coef, zi[i], sample_n, sample_n, n_coef.shape[0], d_coef.shape[0], zi_n)
            core.check_error(code)

        if (ndim == 1):
            res_buf = res_buf[0]
            zi = zi[0]

        return res_buf, zi
    else:
        zi = numpy.zeros((1), dtype=numpy.float32, order='C')
        for i in range(ch_n):
            code = audio_core.dll.ailiaAudioLinerFilter(res_buf[i], wav[i, ...], n_coef, d_coef, zi, sample_n, sample_n, n_coef.shape[0], d_coef.shape[0], 0)
            core.check_error(code)

        if (ndim == 1):
            res_buf = res_buf[0]

        return res_buf


def get_linerfilter_zi_coef(n_coef, d_coef):
    """ Create coefficents of initial condition for the liner filter delay.

    Parameters
    ----------
    n_coef : numpy.ndarray(ndim = 1)
        numerator coefficient.
    d_coef : numpy.ndarray(ndim = 1)
        denominator coefficient.
        If d_coef[0] is not 1, n_coef and d_coef are normalized by d_coef[0]

    Returns
    -------
    zi : numpy.ndarray
        coefficents of initial condition for the liner filter delay.

    """
    n_coef = audio_core.convert_ndarray(n_coef)
    d_coef = audio_core.convert_ndarray(d_coef)
    zi_n = max(n_coef.shape[0], d_coef.shape[0]) - 1
    res_buf = numpy.zeros(zi_n, dtype=numpy.float32, order='C')

    if n_coef.ndim != 1:
        raise ValueError('illegal n_coef shape.')
    if d_coef.ndim != 1:
        raise ValueError('illegal d_coef shape.')

    code = audio_core.dll.ailiaAudioGetLinerFilterZiCoef(res_buf, n_coef, d_coef, zi_n, n_coef.shape[0], d_coef.shape[0])
    core.check_error(code)

    return res_buf


def filterfilter(n_coef, d_coef, wav, axis=-1, padtype='odd', padlen=None):
    """ filter forward and backward to a audio signal

    Parameters
    ----------
    n_coef : numpy.ndarray(ndim = 1)
        numerator coefficient.
    d_coef : numpy.ndarray(ndim = 1)
        denominator coefficient.
        If d_coef[0] is not 1, n_coef and d_coef are normalized by d_coef[0]
    wav : numpy.ndarray
        input audio signal.
        wav.shape must be (sample_n,) or (channel_n, sample_n).
    axis : int
        TBD
    padtype : str, int or None, optional, default: odd
        type of padding for the input signal extention.
        requirements :
            None or 0 : no padding
            "odd" or 1 : padding odd mode
            "even" or 2 : padding even mode
            "constant" or 3 : padding constant mode
    padlen : int or None, optional, default: 3 * max(len(n_coef), len(d_coef))
        number of padding samples at both ends of input signal before forward filtering.

    Returns
    -------
    res : numpy.ndarray
        output filtered audio signal.

    """
    ndim = wav.ndim
    wav, sample_n, ch_n = audio_core.set_wav_param(wav)
    wav = audio_core.convert_ndarray(wav)
    n_coef = audio_core.convert_ndarray(n_coef)
    d_coef = audio_core.convert_ndarray(d_coef)
    if n_coef.ndim != 1:
        raise ValueError('illegal n_coef shape.')
    if d_coef.ndim != 1:
        raise ValueError('illegal d_coef shape.')

    padtype = audio_core.set_filtflit_pad_type(padtype)
    if padtype == 0:
        padlen = 0
    if padlen is None:
        padlen = 3 * max(n_coef.shape[0], d_coef.shape[0])
    elif padlen < 0:
        padlen = 0

    res_buf = numpy.zeros((ch_n, sample_n), dtype=numpy.float32, order='C')
    for i in range(ch_n):
        code = audio_core.dll.ailiaAudioFilterFilter(res_buf[i], wav[i, ...], n_coef, d_coef, sample_n, sample_n, n_coef.shape[0], d_coef.shape[0], padtype, padlen)
        core.check_error(code)

    if (ndim == 1):
        res_buf = res_buf[0]

    return res_buf


def trim(wav, thr_db=60, ref=numpy.max, frame_length=2048, hop_length=512):
    """ Truncate the silence before and after a audio signal

    Parameters
    ----------
    wav : numpy.ndarray
        input audio signal.
        wav.shape must be (sample_n,) or (channel_n, sample_n).
    thr_db : float, optional, default: 60
        Threshold for determining silence
    ref : 
        TBD
    frame_length : int, optional, default=2048
        length of analysis windows
    hop_length : int, optional, default=512
        length of hop between analysis windows

    Returns
    -------
    res_trimmed : numpy.ndarray
        output trimmed audio signal.
    res_pos : numpy.ndarray shape=(2,)
        non silent position [start,end]

    """
    mono = audio_core.to_mono(wav)
    mono = audio_core.convert_ndarray(mono)
    res_start_pos = ctypes.c_int(0)
    res_nonsilent_length = ctypes.c_int(0)
    code = audio_core.dll.ailiaAudioGetNonSilentPos(ctypes.byref(res_start_pos), ctypes.byref(res_nonsilent_length), mono, mono.shape[0], frame_length, hop_length, thr_db)
    core.check_error(code)

    if res_nonsilent_length.value == 0:
        res_start_pos.value = 0
        end_pos = 0
    else:
        end_pos = res_start_pos.value + res_nonsilent_length.value

    nonsilent_index = [slice(None)] * wav.ndim
    nonsilent_index[-1] = slice(res_start_pos.value, end_pos)

    return wav[tuple(nonsilent_index)], numpy.array((res_start_pos.value, end_pos))
