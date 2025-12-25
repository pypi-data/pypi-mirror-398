import enum
import types
from typing import Annotated

import numpy
from numpy.typing import NDArray


class SampleFormat(enum.Enum):
    FLOAT32 = 0

    INT32 = 1

    INT24 = 2

    INT16 = 3

    INT8 = 4

    UINT8 = 5

class ErrorCode(enum.Enum):
    NoError = 0

    NotInitialized = -10000

    UnanticipatedHostError = -9999

    InvalidChannelCount = -9998

    InvalidSampleRate = -9997

    InvalidDevice = -9996

    InvalidFlag = -9995

    SampleFormatNotSupported = -9994

    BadIODeviceCombination = -9993

    InsufficientMemory = -9992

    BufferTooBig = -9991

    BufferTooSmall = -9990

    NullCallback = -9989

    BadStreamPtr = -9988

    TimedOut = -9987

    InternalError = -9986

    DeviceUnavailable = -9985

    IncompatibleHostApiSpecificStreamInfo = -9984

    StreamIsStopped = -9983

    StreamIsNotStopped = -9982

    InputOverflowed = -9981

    OutputUnderflowed = -9980

    HostApiNotFound = -9979

    InvalidHostApi = -9978

    CanNotReadFromACallbackStream = -9977

    CanNotWriteToACallbackStream = -9976

    CanNotReadFromAnOutputOnlyStream = -9975

    CanNotWriteToAnInputOnlyStream = -9974

    IncompatibleStreamHostApi = -9973

    BadBufferPtr = -9972

    CanNotInitializeRecursively = -9971

NoError: ErrorCode = ErrorCode.NoError

NotInitialized: ErrorCode = ErrorCode.NotInitialized

UnanticipatedHostError: ErrorCode = ErrorCode.UnanticipatedHostError

InvalidChannelCount: ErrorCode = ErrorCode.InvalidChannelCount

InvalidSampleRate: ErrorCode = ErrorCode.InvalidSampleRate

InvalidDevice: ErrorCode = ErrorCode.InvalidDevice

InvalidFlag: ErrorCode = ErrorCode.InvalidFlag

SampleFormatNotSupported: ErrorCode = ErrorCode.SampleFormatNotSupported

BadIODeviceCombination: ErrorCode = ErrorCode.BadIODeviceCombination

InsufficientMemory: ErrorCode = ErrorCode.InsufficientMemory

BufferTooBig: ErrorCode = ErrorCode.BufferTooBig

BufferTooSmall: ErrorCode = ErrorCode.BufferTooSmall

NullCallback: ErrorCode = ErrorCode.NullCallback

BadStreamPtr: ErrorCode = ErrorCode.BadStreamPtr

TimedOut: ErrorCode = ErrorCode.TimedOut

InternalError: ErrorCode = ErrorCode.InternalError

DeviceUnavailable: ErrorCode = ErrorCode.DeviceUnavailable

IncompatibleHostApiSpecificStreamInfo: ErrorCode = ErrorCode.IncompatibleHostApiSpecificStreamInfo

StreamIsStopped: ErrorCode = ErrorCode.StreamIsStopped

StreamIsNotStopped: ErrorCode = ErrorCode.StreamIsNotStopped

InputOverflowed: ErrorCode = ErrorCode.InputOverflowed

OutputUnderflowed: ErrorCode = ErrorCode.OutputUnderflowed

HostApiNotFound: ErrorCode = ErrorCode.HostApiNotFound

InvalidHostApi: ErrorCode = ErrorCode.InvalidHostApi

CanNotReadFromACallbackStream: ErrorCode = ErrorCode.CanNotReadFromACallbackStream

CanNotWriteToACallbackStream: ErrorCode = ErrorCode.CanNotWriteToACallbackStream

CanNotReadFromAnOutputOnlyStream: ErrorCode = ErrorCode.CanNotReadFromAnOutputOnlyStream

CanNotWriteToAnInputOnlyStream: ErrorCode = ErrorCode.CanNotWriteToAnInputOnlyStream

IncompatibleStreamHostApi: ErrorCode = ErrorCode.IncompatibleStreamHostApi

BadBufferPtr: ErrorCode = ErrorCode.BadBufferPtr

CanNotInitializeRecursively: ErrorCode = ErrorCode.CanNotInitializeRecursively

class HostApiTypeId(enum.Enum):
    InDevelopment = 0

    DirectSound = 1

    MME = 2

    ASIO = 3

    SoundManager = 4

    CoreAudio = 5

    OSS = 7

    ALSA = 8

    AL = 9

    BeOS = 10

    WDMKS = 11

    JACK = 12

    WASAPI = 13

    AudioScienceHPI = 14

    AudioIO = 15

    PulseAudio = 16

    Sndio = 17

InDevelopment: HostApiTypeId = HostApiTypeId.InDevelopment

DirectSound: HostApiTypeId = HostApiTypeId.DirectSound

MME: HostApiTypeId = HostApiTypeId.MME

ASIO: HostApiTypeId = HostApiTypeId.ASIO

SoundManager: HostApiTypeId = HostApiTypeId.SoundManager

CoreAudio: HostApiTypeId = HostApiTypeId.CoreAudio

OSS: HostApiTypeId = HostApiTypeId.OSS

ALSA: HostApiTypeId = HostApiTypeId.ALSA

AL: HostApiTypeId = HostApiTypeId.AL

BeOS: HostApiTypeId = HostApiTypeId.BeOS

WDMKS: HostApiTypeId = HostApiTypeId.WDMKS

JACK: HostApiTypeId = HostApiTypeId.JACK

WASAPI: HostApiTypeId = HostApiTypeId.WASAPI

AudioScienceHPI: HostApiTypeId = HostApiTypeId.AudioScienceHPI

AudioIO: HostApiTypeId = HostApiTypeId.AudioIO

PulseAudio: HostApiTypeId = HostApiTypeId.PulseAudio

Sndio: HostApiTypeId = HostApiTypeId.Sndio

class StreamCallbackResult(enum.Enum):
    Continue = 0

    Complete = 1

    Abort = 2

Continue: StreamCallbackResult = StreamCallbackResult.Continue

Complete: StreamCallbackResult = StreamCallbackResult.Complete

Abort: StreamCallbackResult = StreamCallbackResult.Abort

FLOAT32: int = 1

INT32: int = 2

INT24: int = 4

INT16: int = 8

INT8: int = 16

UINT8: int = 32

CUSTOM_FORMAT: int = 65536

NON_INTERLEAVED: int = 2147483648

NO_FLAG: int = 0

CLIP_OFF: int = 1

DITHER_OFF: int = 2

NEVER_DROP_INPUT: int = 4

PRIME_OUTPUT_BUFFERS_USING_STREAM_CALLBACK: int = 8

INPUT_UNDERFLOW: int = 1

INPUT_OVERFLOW: int = 2

OUTPUT_UNDERFLOW: int = 4

OUTPUT_OVERFLOW: int = 8

PRIMING_OUTPUT: int = 16

NO_DEVICE: int = -1

FRAMES_PER_BUFFER_UNSPECIFIED: int = 0

class DeviceInfo:
    @property
    def index(self) -> int: ...

    @property
    def name(self) -> str: ...

    @property
    def host_api(self) -> int: ...

    @property
    def max_input_channels(self) -> int: ...

    @property
    def max_output_channels(self) -> int: ...

    @property
    def default_low_input_latency(self) -> float: ...

    @property
    def default_low_output_latency(self) -> float: ...

    @property
    def default_high_input_latency(self) -> float: ...

    @property
    def default_high_output_latency(self) -> float: ...

    @property
    def default_sample_rate(self) -> float: ...

    def __repr__(self) -> str: ...

class VersionInfo:
    @property
    def version_major(self) -> int: ...

    @property
    def version_minor(self) -> int: ...

    @property
    def version_sub_minor(self) -> int: ...

    @property
    def version_control_revision(self) -> str | None: ...

    @property
    def version_text(self) -> str | None: ...

class HostApiInfo:
    @property
    def struct_version(self) -> int: ...

    @property
    def type(self) -> HostApiTypeId: ...

    @property
    def name(self) -> str | None: ...

    @property
    def device_count(self) -> int: ...

    @property
    def default_input_device(self) -> int: ...

    @property
    def default_output_device(self) -> int: ...

class StreamInfo:
    @property
    def struct_version(self) -> int: ...

    @property
    def input_latency(self) -> float: ...

    @property
    def output_latency(self) -> float: ...

    @property
    def sample_rate(self) -> float: ...

class HostErrorInfo:
    @property
    def host_api_type(self) -> HostApiTypeId: ...

    @property
    def error_code(self) -> int: ...

    @property
    def error_text(self) -> str | None: ...

class StreamCallbackTimeInfo:
    @property
    def input_buffer_adc_time(self) -> float: ...

    @property
    def current_time(self) -> float: ...

    @property
    def output_buffer_dac_time(self) -> float: ...

class StreamParameters:
    def __init__(self, device: int, channel_count: int, sample_format: int = 1, suggested_latency: float = 0.0) -> None: ...

    @property
    def device(self) -> int: ...

    @device.setter
    def device(self, arg: int, /) -> None: ...

    @property
    def channel_count(self) -> int: ...

    @channel_count.setter
    def channel_count(self, arg: int, /) -> None: ...

    @property
    def sample_format(self) -> int: ...

    @sample_format.setter
    def sample_format(self, arg: int, /) -> None: ...

    @property
    def suggested_latency(self) -> float: ...

    @suggested_latency.setter
    def suggested_latency(self, arg: float, /) -> None: ...

class Stream:
    def __init__(self, input_parameters: StreamParameters | None = None, output_parameters: StreamParameters | None = None, sample_rate: float = 44100.0, frames_per_buffer: int = 0, stream_flags: int = 0) -> None: ...

    def start(self) -> None: ...

    def stop(self) -> None: ...

    def abort(self) -> None: ...

    def close(self) -> None: ...

    def is_stopped(self) -> bool: ...

    def is_active(self) -> bool: ...

    def get_time(self) -> float: ...

    def get_cpu_load(self) -> float: ...

    def get_info(self) -> StreamInfo | None: ...

    def get_read_available(self) -> int: ...

    def get_write_available(self) -> int: ...

    def read(self, frames: int) -> object: ...

    def write(self, buffer: NDArray) -> None: ...

    def read_float32(self, frames: int) -> Annotated[NDArray[numpy.float32], dict(shape=(None, None))]: ...

    def read_int16(self, frames: int) -> Annotated[NDArray[numpy.int16], dict(shape=(None, None))]: ...

    def read_int32(self, frames: int) -> Annotated[NDArray[numpy.int32], dict(shape=(None, None))]: ...

    def read_uint8(self, frames: int) -> Annotated[NDArray[numpy.uint8], dict(shape=(None, None))]: ...

    def write_float32(self, buffer: Annotated[NDArray[numpy.float32], dict(shape=(None, None), writable=False)]) -> None: ...

    def write_int16(self, buffer: Annotated[NDArray[numpy.int16], dict(shape=(None, None), writable=False)]) -> None: ...

    def write_int32(self, buffer: Annotated[NDArray[numpy.int32], dict(shape=(None, None), writable=False)]) -> None: ...

    def write_uint8(self, buffer: Annotated[NDArray[numpy.uint8], dict(shape=(None, None), writable=False)]) -> None: ...

    @property
    def sample_rate(self) -> float: ...

    @property
    def input_channels(self) -> int: ...

    @property
    def output_channels(self) -> int: ...

    @property
    def format(self) -> SampleFormat: ...

    def __enter__(self) -> Stream: ...

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: types.TracebackType | None) -> None: ...

def is_format_supported(input_parameters: StreamParameters | None = None, output_parameters: StreamParameters | None = None, sample_rate: float = 44100.0) -> bool: ...

def list_devices() -> list[DeviceInfo]: ...

def list_input_devices() -> list[DeviceInfo]: ...

def list_output_devices() -> list[DeviceInfo]: ...

def open_input(device: object | None = None, sample_rate: float = 44100.0, channels: int = 1, format: SampleFormat = SampleFormat.FLOAT32, frames_per_buffer: int = 1024) -> Stream: ...

def open_output(device: object | None = None, sample_rate: float = 44100.0, channels: int = 1, format: SampleFormat = SampleFormat.FLOAT32, frames_per_buffer: int = 1024) -> Stream: ...

def get_version() -> int: ...

def get_version_text() -> str: ...

def get_version_info() -> VersionInfo: ...

def get_error_text(error_code: int) -> str: ...

def get_last_host_error_info() -> HostErrorInfo: ...

def get_host_api_count() -> int: ...

def get_default_host_api() -> int: ...

def get_host_api_info(host_api: int) -> HostApiInfo: ...

def host_api_type_id_to_host_api_index(type: HostApiTypeId) -> int: ...

def host_api_device_index_to_device_index(host_api: int, host_api_device_index: int) -> int: ...

def get_device_count() -> int: ...

def get_default_input_device() -> int: ...

def get_default_output_device() -> int: ...

def get_device_info(device: int) -> DeviceInfo | None: ...

def get_sample_size(format: int) -> int: ...

def sleep(msec: int) -> None: ...

def get_all_devices() -> list[tuple[int, DeviceInfo]]: ...

def get_input_devices() -> list[tuple[int, DeviceInfo]]: ...

def get_output_devices() -> list[tuple[int, DeviceInfo]]: ...

def get_all_host_apis() -> list[tuple[int, HostApiInfo]]: ...
