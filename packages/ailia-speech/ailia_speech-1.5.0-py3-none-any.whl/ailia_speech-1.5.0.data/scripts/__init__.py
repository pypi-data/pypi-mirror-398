import ctypes
import os
import sys

import numpy
import ailia
import ailia.audio
import ailia_tokenizer

import urllib.request
import ssl
import shutil
import platform

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
    dll_name = "ailia_speech.dll"
    load_fn = ctypes.WinDLL
elif sys.platform == "darwin":
    dll_platform = "mac"
    dll_name = "libailia_speech.dylib"
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
    dll_name = "libailia_speech.so"
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

# ==============================================================================

from ctypes import *

AILIA_SPEECH_STATUS_SUCCESS = ( 0 )

AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_TINY = (0)
AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_BASE = (1)
AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_SMALL = (2)
AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_MEDIUM = (3)
AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE = (4)
AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3 = (5)
AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3_TURBO = (6)
AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL = (10)

AILIA_SPEECH_TASK_TRANSCRIBE = (0)
AILIA_SPEECH_TASK_TRANSLATE = (1)

AILIA_SPEECH_FLAG_NONE = (0)
AILIA_SPEECH_FLAG_LIVE = (1)

AILIA_SPEECH_VAD_TYPE_SILERO = (0)

AILIA_SPEECH_DIARIZATION_TYPE_PYANNOTE_AUDIO = (0)

AILIA_SPEECH_API_CALLBACK_VERSION = (6)

AILIA_SPEECH_TEXT_VERSION = (2)
AILIA_SPEECH_SPEAKER_ID_UNKNOWN = (0xFFFFFFFF)

AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_FRAME_LEN = CFUNCTYPE(POINTER(c_int), c_int, c_int, c_int, c_int)
AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_MEL_SPECTROGRAM = CFUNCTYPE((c_int), c_void_p, c_void_p, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_float, c_int, c_float, c_float, c_int, c_int, c_int)

AILIA_SPEECH_USER_API_AILIA_TOKENIZER_CREATE = CFUNCTYPE((c_int), POINTER(c_void_p) , c_int, c_int)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_OPEN_MODEL_FILE_A = CFUNCTYPE((c_int), c_void_p , c_char_p)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_OPEN_MODEL_FILE_W = CFUNCTYPE((c_int), c_void_p , c_wchar)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_ENCODE = CFUNCTYPE((c_int), c_void_p , c_char_p)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TOKEN_COUNT = CFUNCTYPE((c_int), c_void_p , POINTER(c_uint))
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TOKENS = CFUNCTYPE((c_int), c_void_p , POINTER(c_int) , c_uint)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_DECODE = CFUNCTYPE((c_int), c_void_p , POINTER(c_int), c_uint)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TEXT_LENGTH = CFUNCTYPE((c_int), c_void_p , POINTER(c_uint))
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TEXT = CFUNCTYPE((c_int), c_void_p , c_char_p , c_uint)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_DESTROY = CFUNCTYPE((c_int), c_void_p)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_UTF8_TO_UTF32 = CFUNCTYPE((c_int), POINTER(c_uint) , POINTER(c_uint) , c_char_p , c_uint)
AILIA_SPEECH_USER_API_AILIA_TOKENIZER_UTF32_TO_UTF8 = CFUNCTYPE((c_int), c_char_p, POINTER(c_uint) , c_uint)

AILIA_SPEECH_USER_API_AILIA_AUDIO_RESAMPLE = CFUNCTYPE((c_int), POINTER(c_float), POINTER(c_float), c_int, c_int, c_int, c_int)
AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_RESAMPLE_LEN = CFUNCTYPE((c_int), POINTER(c_int), c_int, c_int, c_int)
AILIA_SPEECH_USER_API_AILIA_CREATE = CFUNCTYPE((c_int), POINTER(c_void_p), c_int, c_int)
AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_FILE_A = CFUNCTYPE((c_int), c_void_p, c_char_p)
AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_FILE_W = CFUNCTYPE((c_int), c_void_p, POINTER(c_wchar))
AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_MEM = CFUNCTYPE((c_int), c_void_p, POINTER(c_byte), c_uint)
AILIA_SPEECH_USER_API_AILIA_SET_MEMORY_MODE = CFUNCTYPE((c_int), c_void_p, c_uint)
AILIA_SPEECH_USER_API_AILIA_DESTROY = CFUNCTYPE((None), c_void_p)
AILIA_SPEECH_USER_API_AILIA_UPDATE = CFUNCTYPE((c_int), c_void_p)
AILIA_SPEECH_USER_API_AILIA_GET_BLOB_INDEX_BY_INPUT_INDEX = CFUNCTYPE((c_int), c_void_p, POINTER(c_uint), c_uint)
AILIA_SPEECH_USER_API_AILIA_GET_BLOB_INDEX_BY_OUTPUT_INDEX = CFUNCTYPE((c_int), c_void_p, POINTER(c_uint), c_uint)
AILIA_SPEECH_USER_API_AILIA_GET_BLOB_DATA = CFUNCTYPE((c_int), c_void_p, POINTER(c_float), c_uint, c_uint)
AILIA_SPEECH_USER_API_AILIA_SET_INPUT_BLOB_DATA = CFUNCTYPE((c_int), c_void_p, POINTER(c_float), c_uint, c_uint)
AILIA_SPEECH_USER_API_AILIA_SET_INPUT_BLOB_SHAPE = CFUNCTYPE((c_int), c_void_p, c_void_p, c_uint, c_uint)
AILIA_SPEECH_USER_API_AILIA_GET_BLOB_SHAPE = CFUNCTYPE((c_int), c_void_p, c_void_p, c_uint, c_uint)
AILIA_SPEECH_USER_API_AILIA_GET_ERROR_DETAIL = CFUNCTYPE((c_char_p), c_void_p)

AILIA_SPEECH_USER_API_AILIA_COPY_BLOB_DATA = CFUNCTYPE((c_int), c_void_p, c_uint, c_void_p, c_uint)
AILIA_SPEECH_USER_API_AILIA_GET_ENVIRONMENT = CFUNCTYPE((c_int), POINTER(c_void_p), c_uint, c_uint)


class struct__AILIASpeechApiCallback(Structure):
    pass

struct__AILIASpeechApiCallback.__slots__ = [
    'ailiaAudioGetFrameLen',
    'ailiaAudioGetMelSpectrogram',
    'ailiaAudioResample',
    'ailiaAudioGetResampleLen',

    'ailiaTokenizerCreate',
    'ailiaTokenizerOpenModelFileA',
    'ailiaTokenizerOpenModelFileW',
    'ailiaTokenizerEncode',
    'ailiaTokenizerGetTokenCount',
    'ailiaTokenizerGetTokens',
    'ailiaTokenizerDecode',
    'ailiaTokenizerGetTextLength',
    'ailiaTokenizerGetText',
    'ailiaTokenizerDestroy',
    'ailiaTokenizerUtf8ToUtf32',
    'ailiaTokenizerUtf32ToUtf8',

    'ailiaCreate',
    'ailiaOpenWeightFileA',
    'ailiaOpenWeightFileW',
    'ailiaOpenWeightMem',
    'ailiaSetMemoryMode',
    'ailiaDestroy',
    'ailiaUpdate',
    'ailiaGetBlobIndexByInputIndex',
    'ailiaGetBlobIndexByOutputIndex',
    'ailiaGetBlobData',
    'ailiaSetInputBlobData',
    'ailiaSetInputBlobShape',
    'ailiaGetBlobShape',
    'ailiaGetErrorDetail',
    'ailiaCopyBlobData',
    'ailiaGetEnvironment',
]
struct__AILIASpeechApiCallback._fields_ = [
    ('ailiaAudioGetFrameLen', AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_FRAME_LEN),
    ('ailiaAudioGetMelSpectrogram', AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_MEL_SPECTROGRAM),
    ('ailiaAudioResample', AILIA_SPEECH_USER_API_AILIA_AUDIO_RESAMPLE),
    ('ailiaAudioGetResampleLen', AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_RESAMPLE_LEN),

    ('ailiaTokenizerCreate', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_CREATE),
    ('ailiaTokenizerOpenModelFileA', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_OPEN_MODEL_FILE_A),
    ('ailiaTokenizerOpenModelFileW', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_OPEN_MODEL_FILE_W),
    ('ailiaTokenizerEncode', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_ENCODE),
    ('ailiaTokenizerGetTokenCount', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TOKEN_COUNT),
    ('ailiaTokenizerGetTokens', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TOKENS),
    ('ailiaTokenizerDecode', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_DECODE),
    ('ailiaTokenizerGetTextLength', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TEXT_LENGTH),
    ('ailiaTokenizerGetText', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TEXT),
    ('ailiaTokenizerDestroy', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_DESTROY),
    ('ailiaTokenizerUtf8ToUtf32', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_UTF8_TO_UTF32),
    ('ailiaTokenizerUtf32ToUtf8', AILIA_SPEECH_USER_API_AILIA_TOKENIZER_UTF32_TO_UTF8),

    ('ailiaCreate', AILIA_SPEECH_USER_API_AILIA_CREATE),
    ('ailiaOpenWeightFileA', AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_FILE_A),
    ('ailiaOpenWeightFileW', AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_FILE_W),
    ('ailiaOpenWeightMem', AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_MEM),
    ('ailiaSetMemoryMode', AILIA_SPEECH_USER_API_AILIA_SET_MEMORY_MODE),
    ('ailiaDestroy', AILIA_SPEECH_USER_API_AILIA_DESTROY),
    ('ailiaUpdate', AILIA_SPEECH_USER_API_AILIA_UPDATE),
    ('ailiaGetBlobIndexByInputIndex', AILIA_SPEECH_USER_API_AILIA_GET_BLOB_INDEX_BY_INPUT_INDEX),
    ('ailiaGetBlobIndexByOutputIndex', AILIA_SPEECH_USER_API_AILIA_GET_BLOB_INDEX_BY_OUTPUT_INDEX),
    ('ailiaGetBlobData', AILIA_SPEECH_USER_API_AILIA_GET_BLOB_DATA),
    ('ailiaSetInputBlobData', AILIA_SPEECH_USER_API_AILIA_SET_INPUT_BLOB_DATA),
    ('ailiaSetInputBlobShape', AILIA_SPEECH_USER_API_AILIA_SET_INPUT_BLOB_SHAPE),
    ('ailiaGetBlobShape', AILIA_SPEECH_USER_API_AILIA_GET_BLOB_SHAPE),
    ('ailiaGetErrorDetail', AILIA_SPEECH_USER_API_AILIA_GET_ERROR_DETAIL),
    ('ailiaCopyBlobData', AILIA_SPEECH_USER_API_AILIA_COPY_BLOB_DATA),
    ('ailiaGetEnvironment', AILIA_SPEECH_USER_API_AILIA_GET_ENVIRONMENT),
]

AILIASpeechApiCallback = struct__AILIASpeechApiCallback

# ==============================================================================

dll.ailiaSpeechCreate.restype = c_int
dll.ailiaSpeechCreate.argtypes = (POINTER(c_void_p), c_int32, c_int32, c_int32, c_int32, c_int32, AILIASpeechApiCallback, c_int32)

dll.ailiaSpeechDestroy.restype = None
dll.ailiaSpeechDestroy.argtypes = (c_void_p, )

dll.ailiaSpeechOpenModelFileA.restype = c_int
dll.ailiaSpeechOpenModelFileA.argtypes = (c_void_p, c_char_p, c_char_p, c_int32)

dll.ailiaSpeechOpenModelFileW.restype = c_int
dll.ailiaSpeechOpenModelFileW.argtypes = (c_void_p, c_wchar_p, c_wchar_p, c_int32)

dll.ailiaSpeechOpenVadFileA.restype = c_int
dll.ailiaSpeechOpenVadFileA.argtypes = (c_void_p, c_char_p, c_int32)

dll.ailiaSpeechOpenVadFileW.restype = c_int
dll.ailiaSpeechOpenVadFileW.argtypes = (c_void_p, c_wchar_p, c_int32)

dll.ailiaSpeechOpenDiarizationFileA.restype = c_int
dll.ailiaSpeechOpenDiarizationFileA.argtypes = (c_void_p, c_char_p, c_char_p, c_int32)

dll.ailiaSpeechOpenDiarizationFileW.restype = c_int
dll.ailiaSpeechOpenDiarizationFileW.argtypes = (c_void_p, c_wchar_p, c_wchar_p, c_int32)

dll.ailiaSpeechPushInputData.restype = c_int
dll.ailiaSpeechPushInputData.argtypes = (c_void_p, numpy.ctypeslib.ndpointer(
                dtype=numpy.float32, flags='CONTIGUOUS'
            ),                               # src
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.c_uint)

dll.ailiaSpeechFinalizeInputData.restype = c_int
dll.ailiaSpeechFinalizeInputData.argtypes = (c_void_p, )

dll.ailiaSpeechBuffered.restype = c_int
dll.ailiaSpeechBuffered.argtypes = (c_void_p, POINTER(ctypes.c_uint))

dll.ailiaSpeechComplete.restype = c_int
dll.ailiaSpeechComplete.argtypes = (c_void_p, POINTER(ctypes.c_uint))

dll.ailiaSpeechTranscribe.restype = c_int
dll.ailiaSpeechTranscribe.argtypes = (c_void_p, )

dll.ailiaSpeechGetTextCount.restype = c_int
dll.ailiaSpeechGetTextCount.argtypes = (c_void_p, POINTER(ctypes.c_uint))

class AILIASpeechText(ctypes.Structure):
    _fields_ = [
        ("text", ctypes.c_char_p),
        ("time_stamp_begin", ctypes.c_float),
        ("time_stamp_end", ctypes.c_float),
        ("speaker_id", ctypes.c_uint),
        ("language", ctypes.c_char_p),
        ("confidence", ctypes.c_float)]

dll.ailiaSpeechGetText.restype = c_int
dll.ailiaSpeechGetText.argtypes = (c_void_p, POINTER(AILIASpeechText), ctypes.c_uint, ctypes.c_uint)

dll.ailiaSpeechResetTranscribeState.restype = c_int
dll.ailiaSpeechResetTranscribeState.argtypes = (c_void_p, )

AILIA_SPEECH_USER_API_INTERMEDIATE_CALLBACK = CFUNCTYPE((c_int), c_int64, c_char_p)

dll.ailiaSpeechSetIntermediateCallback.restype = c_int
dll.ailiaSpeechSetIntermediateCallback.argtypes = (c_void_p, AILIA_SPEECH_USER_API_INTERMEDIATE_CALLBACK, c_int64)

dll.ailiaSpeechSetLanguage.restype = c_int
dll.ailiaSpeechSetLanguage.argtypes = (c_void_p, c_char_p)

dll.ailiaSpeechSetSilentThreshold.restype = c_int
dll.ailiaSpeechSetSilentThreshold.argtypes = (c_void_p, c_float, c_float, c_float)

# ==============================================================================
# model download
# ==============================================================================

def progress_print(block_count, block_size, total_size):
    percentage = 100.0 * block_count * block_size / total_size
    if percentage > 100:
        # Bigger than 100 does not look good, so...
        percentage = 100
    max_bar = 50
    bar_num = int(percentage / (100 / max_bar))
    progress_element = '=' * bar_num
    if bar_num != max_bar:
        progress_element += '>'
    bar_fill = ' '  # fill the blanks
    bar = progress_element.ljust(max_bar, bar_fill)
    total_size_kb = total_size / 1024
    print(f'[{bar} {percentage:.2f}% ( {total_size_kb:.0f}KB )]', end='\r')

def urlretrieve(remote_path, weight_path, progress_print):
    temp_path = weight_path + ".tmp"
    try:
        #raise ssl.SSLError # test
        urllib.request.urlretrieve(
            remote_path,
            temp_path,
            progress_print,
        )
    except ssl.SSLError as e:
        print(f'SSLError detected, so try to download without ssl')
        remote_path = remote_path.replace("https","http")
        urllib.request.urlretrieve(
            remote_path,
            temp_path,
            progress_print,
        )
    shutil.move(temp_path, weight_path)

def check_and_download_file(file_path, remote_path):
    if not os.path.exists(file_path):
        print('Downloading %s...' % file_path)
        urlretrieve(remote_path + os.path.basename(file_path), file_path, progress_print)

# ==============================================================================
# base model class
# ==============================================================================

intermediate_callback_cnt = 0
intermediate_callback_map = {}

def intermediate_callback(handle, text):
    intermediate_callback_map[handle](text.decode())
    return 0

class AiliaSpeechError(RuntimeError):
    def __init__(self, message, code):
        super().__init__(f"{message} code:{code}")
        self.code = code

class AiliaSpeechModel:
    _api_callback = None
    _instance = None
    _c_callback = None

    def __init__(self, env_id = -1, num_thread = 0, memory_mode = 11, task = AILIA_SPEECH_TASK_TRANSCRIBE, flags = AILIA_SPEECH_FLAG_NONE, callback = None):
        """ constructor of ailia Specch model instance.

        Parameters
        ----------
        env_id : int, optional, default:ENVIRONMENT_AUTO(-1)
            environment id of ailia excecution.
            To retrieve env_id value, use
                ailia.get_environment_count() / ailia.get_environment() pair
            or
                ailia.get_gpu_environment_id() .
        num_thread : int, optional, default: MULTITHREAD_AUTO(0)
            number of threads.
            valid values:
                MULTITHREAD_AUTO=0 [means systems's logical processor count],
                1 to 32.
        memory_mode : int, optional, default: 11 (reuse interstage)
            memory management mode of ailia excecution.
            To retrieve memory_mode value, use ailia.get_memory_mode() .
        task : int, optional, default: AILIA_SPEECH_TASK_TRANSCRIBE
            AILIA_SPEECH_TASK_TRANSCRIBE or AILIA_SPEECH_TASK_TRANSLATE
        flags : int, optional, default: AILIA_SPEECH_FLAG_NONE
            Reserved
        callback : func or None, optional, default: None
            Callback for receiving intermediate result text .
            Example
              def f_callback(text):
                print(text)
        """
        self._instance = ctypes.c_void_p(None)
        self._create_callback()
        self._check(dll.ailiaSpeechCreate(cast(pointer(self._instance), POINTER(c_void_p)), ctypes.c_int32(env_id), ctypes.c_int32(num_thread), ctypes.c_int32(memory_mode), ctypes.c_int32(task), ctypes.c_int32(flags), self._api_callback, ctypes.c_int32(AILIA_SPEECH_API_CALLBACK_VERSION)))
        if callback is not None:
            self._c_callback = AILIA_SPEECH_USER_API_INTERMEDIATE_CALLBACK(intermediate_callback)
            global intermediate_callback_cnt
            global intermediate_callback_map
            intermediate_callback_map[intermediate_callback_cnt] = callback
            self._check(dll.ailiaSpeechSetIntermediateCallback(self._instance, self._c_callback, intermediate_callback_cnt))
            intermediate_callback_cnt = intermediate_callback_cnt + 1

    def _check(self, status):
        if status != AILIA_SPEECH_STATUS_SUCCESS:
            raise AiliaSpeechError(f"ailia speech error", status)

    def _string_buffer_aw(self, path):
        if sys.platform == "win32":
            return ctypes.create_unicode_buffer(path)
        else:
            return ctypes.create_string_buffer(path.encode("utf-8"))

    def _string_buffer(self, path):
        return ctypes.create_string_buffer(path.encode("utf-8"))

    def _create_callback(self):
        callback = AILIASpeechApiCallback()
        callback.ailiaAudioGetFrameLen = AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_FRAME_LEN(("ailiaAudioGetFrameLen", ailia.audio.audio_core.dll))
        callback.ailiaAudioGetMelSpectrogram = AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_MEL_SPECTROGRAM(("ailiaAudioGetMelSpectrogram", ailia.audio.audio_core.dll))
        callback.ailiaAudioResample = AILIA_SPEECH_USER_API_AILIA_AUDIO_RESAMPLE(("ailiaAudioResample", ailia.audio.audio_core.dll))
        callback.ailiaAudioGetResampleLen = AILIA_SPEECH_USER_API_AILIA_AUDIO_GET_RESAMPLE_LEN(("ailiaAudioGetResampleLen", ailia.audio.audio_core.dll))

        callback.ailiaTokenizerCreate = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_CREATE(("ailiaTokenizerCreate", ailia_tokenizer.dll))
        callback.ailiaTokenizerOpenModelFileA = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_OPEN_MODEL_FILE_A(("ailiaTokenizerOpenModelFileA", ailia_tokenizer.dll))
        callback.ailiaTokenizerOpenModelFileW = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_OPEN_MODEL_FILE_W(("ailiaTokenizerOpenModelFileW", ailia_tokenizer.dll))
        callback.ailiaTokenizerEncode = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_ENCODE(("ailiaTokenizerEncode", ailia_tokenizer.dll))
        callback.ailiaTokenizerGetTokenCount = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TOKEN_COUNT(("ailiaTokenizerGetTokenCount", ailia_tokenizer.dll))
        callback.ailiaTokenizerGetTokens = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TOKENS(("ailiaTokenizerGetTokens", ailia_tokenizer.dll))
        callback.ailiaTokenizerDecode = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_DECODE(("ailiaTokenizerDecode", ailia_tokenizer.dll))
        callback.ailiaTokenizerGetTextLength = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TEXT_LENGTH(("ailiaTokenizerGetTextLength", ailia_tokenizer.dll))
        callback.ailiaTokenizerGetText = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_GET_TEXT(("ailiaTokenizerGetText", ailia_tokenizer.dll))
        callback.ailiaTokenizerDestroy = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_DESTROY(("ailiaTokenizerDestroy", ailia_tokenizer.dll))
        callback.ailiaTokenizerUtf8ToUtf32 = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_UTF8_TO_UTF32(("ailiaTokenizerUtf8ToUtf32", ailia_tokenizer.dll))
        callback.ailiaTokenizerUtf32ToUtf8 = AILIA_SPEECH_USER_API_AILIA_TOKENIZER_UTF32_TO_UTF8(("ailiaTokenizerUtf32ToUtf8", ailia_tokenizer.dll))

        callback.ailiaCreate = AILIA_SPEECH_USER_API_AILIA_CREATE(("ailiaCreate", ailia.core.dll))
        callback.ailiaOpenWeightFileA = AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_FILE_A(("ailiaOpenWeightFileA", ailia.core.dll))
        callback.ailiaOpenWeightFileW = AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_FILE_W(("ailiaOpenWeightFileW", ailia.core.dll))
        callback.ailiaOpenWeightMem = AILIA_SPEECH_USER_API_AILIA_OPEN_WEIGHT_MEM(("ailiaOpenWeightMem", ailia.core.dll))
        callback.ailiaSetMemoryMode = AILIA_SPEECH_USER_API_AILIA_SET_MEMORY_MODE(("ailiaSetMemoryMode", ailia.core.dll))
        callback.ailiaDestroy = AILIA_SPEECH_USER_API_AILIA_DESTROY(("ailiaDestroy", ailia.core.dll))
        callback.ailiaUpdate = AILIA_SPEECH_USER_API_AILIA_UPDATE(("ailiaUpdate", ailia.core.dll))
        callback.ailiaGetBlobIndexByInputIndex = AILIA_SPEECH_USER_API_AILIA_GET_BLOB_INDEX_BY_INPUT_INDEX(("ailiaGetBlobIndexByInputIndex", ailia.core.dll))
        callback.ailiaGetBlobIndexByOutputIndex = AILIA_SPEECH_USER_API_AILIA_GET_BLOB_INDEX_BY_OUTPUT_INDEX(("ailiaGetBlobIndexByOutputIndex", ailia.core.dll))
        callback.ailiaGetBlobData = AILIA_SPEECH_USER_API_AILIA_GET_BLOB_DATA(("ailiaGetBlobData", ailia.core.dll))
        callback.ailiaSetInputBlobData = AILIA_SPEECH_USER_API_AILIA_SET_INPUT_BLOB_DATA(("ailiaSetInputBlobData", ailia.core.dll))
        callback.ailiaSetInputBlobShape = AILIA_SPEECH_USER_API_AILIA_SET_INPUT_BLOB_SHAPE(("ailiaSetInputBlobShape", ailia.core.dll))
        callback.ailiaGetBlobShape = AILIA_SPEECH_USER_API_AILIA_GET_BLOB_SHAPE(("ailiaGetBlobShape", ailia.core.dll))
        callback.ailiaGetErrorDetail = AILIA_SPEECH_USER_API_AILIA_GET_ERROR_DETAIL(("ailiaGetErrorDetail", ailia.core.dll))
        callback.ailiaCopyBlobData = AILIA_SPEECH_USER_API_AILIA_COPY_BLOB_DATA(("ailiaCopyBlobData", ailia.core.dll))
        callback.ailiaGetEnvironment = AILIA_SPEECH_USER_API_AILIA_GET_ENVIRONMENT(("ailiaGetEnvironment", ailia.core.dll))

        self._api_callback = callback # prevent GC

    def _download_model(self, model_path, encoder_path, decoder_path, encoder_pb_path, decoder_pb_path, vad_type, vad_version, diarization_type, model_type):
        if model_type == AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL:
            REMOTE_PATH = "https://storage.googleapis.com/ailia-models/sensevoice/"
        else:
            REMOTE_PATH = "https://storage.googleapis.com/ailia-models/whisper/"
        os.makedirs(model_path, exist_ok = True)
        check_and_download_file(model_path + encoder_path, REMOTE_PATH)
        check_and_download_file(model_path + decoder_path, REMOTE_PATH)
        if encoder_pb_path is not None:
            check_and_download_file(model_path + encoder_pb_path, REMOTE_PATH)
        if decoder_pb_path is not None:
            check_and_download_file(model_path + decoder_pb_path, REMOTE_PATH)

        if vad_type is not None:
            REMOTE_PATH = "https://storage.googleapis.com/ailia-models/silero-vad/"
            check_and_download_file(model_path + self._vad_model_name(vad_version), REMOTE_PATH)

        if diarization_type is not None:
            REMOTE_PATH = "https://storage.googleapis.com/ailia-models/pyannote-audio/"
            check_and_download_file(model_path + "segmentation.onnx", REMOTE_PATH)
            check_and_download_file(model_path + "speaker-embedding.onnx", REMOTE_PATH)

    def _open_model(self, encoder, decoder, model_type):
        p1 = self._string_buffer_aw(encoder)
        p2 = self._string_buffer_aw(decoder)

        if sys.platform == "win32":
            self._check(dll.ailiaSpeechOpenModelFileW(self._instance, p1, p2, model_type))
        else:
            self._check(dll.ailiaSpeechOpenModelFileA(self._instance, p1, p2, model_type))

    def _open_vad(self, vad, vad_type):
        p1 = self._string_buffer_aw(vad)

        if sys.platform == "win32":
            self._check(dll.ailiaSpeechOpenVadFileW(self._instance, p1, vad_type))
        else:
            self._check(dll.ailiaSpeechOpenVadFileA(self._instance, p1, vad_type))

    def _open_diarization(self, segmentation, embedding, diarization_type):
        p1 = self._string_buffer_aw(segmentation)
        p2 = self._string_buffer_aw(embedding)

        if sys.platform == "win32":
            self._check(dll.ailiaSpeechOpenDiarizationFileW(self._instance, p1, p2, diarization_type))
        else:
            self._check(dll.ailiaSpeechOpenDiarizationFileA(self._instance, p1, p2, diarization_type))

    def set_silent_threshold(self, silent_threshold, speech_sec, no_speech_sec):
        """ Set silent threshold. If there are more than a certain number of sounded sections, and if the silent section lasts for a certain amount of time or more, the remaining buffer is processed without waiting for 30 seconds.

        Parameters
        ----------
        silent_threshold : float
            volume threshold, standard value 0.5
        speech_sec : float
            speech time, standard value 1.0
        no_speech_sec : float
            no_speech time, standard value 1.0
        """
        self._check(dll.ailiaSpeechSetSilentThreshold(self._instance, silent_threshold, speech_sec, no_speech_sec))

    def transcribe(self, audio_waveform, sampling_rate, lang = None):
        """ Perform speech recognition. Processes the entire audio at once.

        Parameters
        ----------
        audio_waveform : np.array
            PCM data  
        sampling_rate : int
            Sampling rate (Hz)
        lang : str, optional, default : None
            Language code (ja, en, etc.) (automatic detection if None)

        Returns
        ----------
        text : Speech recognition result text
        time_stamp_begin : Start Time (seconds)
        time_stamp_end : End Time (seconds)
        speaker_id :Speaker ID (when diarization is enabled)  
        language : Language code  
        confidence : Confidence level
        """
        if len(audio_waveform.shape) == 1:
            channels = 1
        elif len(audio_waveform.shape) == 2:
            channels = audio_waveform.shape[0]
            audio_waveform = numpy.transpose(audio_waveform, (1, 0)).flatten()
        else:
            raise AiliaSpeechError(f"audio_waveform must be 1 channel or 2 channel", -1)

        audio_waveform = numpy.ascontiguousarray(audio_waveform.astype(numpy.float32))

        if lang is not None:
            self._check(dll.ailiaSpeechSetLanguage(self._instance, self._string_buffer(lang)))

        self._check(dll.ailiaSpeechPushInputData(self._instance, audio_waveform, channels, audio_waveform.shape[0] // channels, sampling_rate))
        self._check(dll.ailiaSpeechFinalizeInputData(self._instance))

        while True:
            complete = ctypes.c_uint(0)
            self._check(dll.ailiaSpeechComplete(self._instance, ctypes.byref(complete)))
            if complete.value == 1:
                break

            self._check(dll.ailiaSpeechTranscribe(self._instance))

            count = ctypes.c_uint(0)
            self._check(dll.ailiaSpeechGetTextCount(self._instance, ctypes.byref(count)))
            results = []
            for i in range(count.value):
                text = AILIASpeechText()
                self._check(dll.ailiaSpeechGetText(self._instance, ctypes.byref(text), AILIA_SPEECH_TEXT_VERSION, i))
                yield {"text" : text.text.decode(), "time_stamp_begin" : text.time_stamp_begin, "time_stamp_end" : text.time_stamp_end, "speaker_id" : None if text.speaker_id == AILIA_SPEECH_SPEAKER_ID_UNKNOWN else text.speaker_id, "language" : text.language.decode(), "confidence" : text.confidence}

        self._check(dll.ailiaSpeechResetTranscribeState(self._instance))

    def transcribe_step(self, audio_waveform, sampling_rate, complete, lang = None):
        """ Perform speech recognition. Processes the audio sequentially.

        Parameters
        ----------
        audio_waveform : np.array
            PCM data  
        sampling_rate : int
            Sampling rate (Hz)
        lang : str, optional, default : None
            Language code (ja, en, etc.) (automatic detection if None)
        complete : bool
            True if this is the final audio input. 
            transcribe_step executes a step each time there is microphone input, and by setting complete to True at the end, the buffer can be flushed.

        Returns
        ----------
        text : Speech recognition result text
        time_stamp_begin : Start Time (seconds)
        time_stamp_end : End Time (seconds)
        speaker_id :Speaker ID (when diarization is enabled)  
        language : Language code  
        confidence : Confidence level
        """
        if len(audio_waveform.shape) == 1:
            channels = 1
        elif len(audio_waveform.shape) == 2:
            channels = audio_waveform.shape[0]
            audio_waveform = numpy.transpose(audio_waveform, (1, 0)).flatten()
        else:
            raise AiliaSpeechError(f"audio_waveform must be 1 channel or 2 channel", -1)

        audio_waveform = numpy.ascontiguousarray(audio_waveform.astype(numpy.float32))

        if lang is not None:
            self._check(dll.ailiaSpeechSetLanguage(self._instance, self._string_buffer(lang)))

        self._check(dll.ailiaSpeechPushInputData(self._instance, audio_waveform, channels, audio_waveform.shape[0] // channels, sampling_rate))
        if complete:
            self._check(dll.ailiaSpeechFinalizeInputData(self._instance))

        while True:
            buffered = ctypes.c_uint(0)
            self._check(dll.ailiaSpeechBuffered(self._instance, ctypes.byref(buffered)))
            if buffered.value == 0:
                break

            self._check(dll.ailiaSpeechTranscribe(self._instance))

            count = ctypes.c_uint(0)
            self._check(dll.ailiaSpeechGetTextCount(self._instance, ctypes.byref(count)))
            results = []
            for i in range(count.value):
                text = AILIASpeechText()
                self._check(dll.ailiaSpeechGetText(self._instance, ctypes.byref(text), AILIA_SPEECH_TEXT_VERSION, i))
                yield {"text" : text.text.decode(), "time_stamp_begin" : text.time_stamp_begin, "time_stamp_end" : text.time_stamp_end, "speaker_id" : None if text.speaker_id == AILIA_SPEECH_SPEAKER_ID_UNKNOWN else text.speaker_id, "language" : text.language.decode(), "confidence" : text.confidence}

        if complete:
            self._check(dll.ailiaSpeechResetTranscribeState(self._instance))

    def _vad_model_name(self, vad_version):
        if vad_version == "4":
            vad_path = "silero_vad.onnx"
        elif vad_version == "5" or vad_version == "6" or vad_version == "6_2":
            vad_path = "silero_vad_v" + vad_version + ".onnx"
        else:
            raise Exception("Unknown vad_version")
        return vad_path

    def __del__(self):
        if self._instance:
            dll.ailiaSpeechDestroy(cast(self._instance, c_void_p))

# ==============================================================================
# Public class
# ==============================================================================

class Whisper(AiliaSpeechModel):
    def __init__(self, env_id = -1, num_thread = 0, memory_mode = 11, task = AILIA_SPEECH_TASK_TRANSCRIBE, flags = AILIA_SPEECH_FLAG_NONE, callback = None):
        super().__init__(env_id = env_id, num_thread = num_thread, memory_mode = memory_mode, task = task, flags = flags, callback = callback)

    def initialize_model(self, model_path = "./", model_type = AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_TINY, vad_type = AILIA_SPEECH_VAD_TYPE_SILERO, vad_version = "4", diarization_type = None, is_fp16 = False):
        """ Initialize and download the model.

        Parameters
        ----------
        model_path : string, optional, default : "./"
            Destination for saving the model file
        model_type : int, optional, default : AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_TINY
            Type of model. Can be set to AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_TINY, AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_BASE, AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_SMALL, AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_MEDIUM, AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE, AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3 or AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3_TURBO.
        vad_type : int, optional, default : AILIA_SPEECH_VAD_TYPE_SILERO
            Type of VAD. Can be set to None or AILIA_SPEECH_VAD_TYPE_SILERO.
        vad_version : string, optional, default : "4"
            Versions 4, 5, and 6.2 of SileroVAD can be specified.
        diarization_type : int, optional, default : None
            Type of diarization. Can be set to None or AILIA_SPEECH_DIARIZATION_TYPE_PYANNOTE_AUDIO.
            transcribe_step executes a step each time there is microphone input, and by setting complete to True at the end, the buffer can be flushed.
        is_fp16 : bool, optional, default : False
            Whether to use an FP16 model.
        """
        if "time_license" in ailia.get_version():
            ailia.check_and_download_license()
        if model_type == AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_TINY:
            if is_fp16:
                encoder_path = "encoder_tiny_fp16.opt3.onnx"
                decoder_path = "decoder_tiny_fix_kv_cache_fp16.opt3.onnx"
            else:
                encoder_path = "encoder_tiny.opt3.onnx"
                decoder_path = "decoder_tiny_fix_kv_cache.opt3.onnx"
            encoder_pb_path = None
            decoder_pb_path = None
        elif model_type == AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_BASE:
            if is_fp16:
                encoder_path = "encoder_base_fp16.opt3.onnx"
                decoder_path = "decoder_base_fix_kv_cache_fp16.opt3.onnx"
            else:
                encoder_path = "encoder_base.opt3.onnx"
                decoder_path = "decoder_base_fix_kv_cache.opt3.onnx"
            encoder_pb_path = None
            decoder_pb_path = None
        elif model_type == AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_SMALL:
            if is_fp16:
                encoder_path = "encoder_small_fp16.opt3.onnx"
                decoder_path = "decoder_small_fix_kv_cache_fp16.opt3.onnx"
            else:
                encoder_path = "encoder_small.opt3.onnx"
                decoder_path = "decoder_small_fix_kv_cache.opt3.onnx"
            encoder_pb_path = None
            decoder_pb_path = None
        elif model_type == AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_MEDIUM:
            if is_fp16:
                encoder_path = "encoder_medium_fp16.opt3.onnx"
                decoder_path = "decoder_medium_fix_kv_cache_fp16.opt3.onnx"
            else:
                encoder_path = "encoder_medium.opt3.onnx"
                decoder_path = "decoder_medium_fix_kv_cache.opt3.onnx"
            encoder_pb_path = None
            decoder_pb_path = None
        elif model_type == AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE:
            encoder_path = "encoder_large.onnx"
            decoder_path = "decoder_large_fix_kv_cache.onnx"
            encoder_pb_path = "encoder_large_weights.pb"
            decoder_pb_path = "decoder_large_fix_kv_cache_weights.pb"
        elif model_type == AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3:
            encoder_path = "encoder_large_v3.onnx"
            decoder_path = "decoder_large_v3_fix_kv_cache.onnx"
            encoder_pb_path = "encoder_large_v3_weights.pb"
            decoder_pb_path = "decoder_large_v3_fix_kv_cache_weights.pb"
        elif model_type == AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3_TURBO:
            if is_fp16:
                encoder_path = "encoder_turbo_fp16.opt.onnx"
                decoder_path = "decoder_turbo_fix_kv_cache_fp16.opt.onnx"
                encoder_pb_path = None
            else:
                encoder_path = "encoder_turbo.opt.onnx"
                decoder_path = "decoder_turbo_fix_kv_cache.opt.onnx"
                encoder_pb_path = "encoder_turbo_weights.opt.pb"
            decoder_pb_path = None
            model_type = AILIA_SPEECH_MODEL_TYPE_WHISPER_MULTILINGUAL_LARGE_V3
        else:
            raise Exception("Unknown model type")
        self._download_model(model_path, encoder_path, decoder_path, encoder_pb_path, decoder_pb_path, vad_type, vad_version, diarization_type, model_type)
        self._open_model(model_path + encoder_path, model_path + decoder_path, model_type)
        if vad_type is not None:
            self._open_vad(model_path + self._vad_model_name(vad_version), vad_type)
            self.set_silent_threshold(0.5, 1.0, 1.0)
        if diarization_type is not None:
            self._open_diarization(model_path + "segmentation.onnx", model_path + "speaker-embedding.onnx", diarization_type)

class SenseVoice(AiliaSpeechModel):
    def __init__(self, env_id = -1, num_thread = 0, memory_mode = 11, task = AILIA_SPEECH_TASK_TRANSCRIBE, flags = AILIA_SPEECH_FLAG_NONE, callback = None):
        super().__init__(env_id = env_id, num_thread = num_thread, memory_mode = memory_mode, task = task, flags = flags, callback = callback)

    def initialize_model(self, model_path = "./", model_type = AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL, vad_type = AILIA_SPEECH_VAD_TYPE_SILERO, vad_version = "4", diarization_type = None, is_fp16 = False):
        """ Initialize and download the model.

        Parameters
        ----------
        model_path : string, optional, default : "./"
            Destination for saving the model file
        model_type : int, optional, default : AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL
            Type of model. Can be set to AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL.
        vad_type : int, optional, default : AILIA_SPEECH_VAD_TYPE_SILERO
            Type of VAD. Can be set to None or AILIA_SPEECH_VAD_TYPE_SILERO.
        vad_version : string, optional, default : "4"
            Versions 4, 5, and 6.2 of SileroVAD can be specified.
        diarization_type : int, optional, default : None
            Type of diarization. Can be set to None or AILIA_SPEECH_DIARIZATION_TYPE_PYANNOTE_AUDIO.
            transcribe_step executes a step each time there is microphone input, and by setting complete to True at the end, the buffer can be flushed.
        is_fp16 : bool, optional, default : False
            Whether to use an FP16 model.
        """
        
        if "time_license" in ailia.get_version():
            ailia.check_and_download_license()
        if model_type == AILIA_SPEECH_MODEL_TYPE_SENSEVOICE_SMALL:
            if is_fp16:
                encoder_path = "sensevoice_small_fp16.onnx"
            else:
                encoder_path = "sensevoice_small.onnx"
            decoder_path = "sensevoice_small.model"
            encoder_pb_path = None
            decoder_pb_path = None
        else:
            raise Exception("Unknown model type")
        self._download_model(model_path, encoder_path, decoder_path, encoder_pb_path, decoder_pb_path, vad_type, vad_version, diarization_type, model_type)
        self._open_model(model_path + encoder_path, model_path + decoder_path, model_type)
        if vad_type is not None:
            self._open_vad(model_path + self._vad_model_name(vad_version), vad_type)
            self.set_silent_threshold(0.5, 1.0, 1.0)
        if diarization_type is not None:
            self._open_diarization(model_path + "segmentation.onnx", model_path + "speaker-embedding.onnx", diarization_type)
