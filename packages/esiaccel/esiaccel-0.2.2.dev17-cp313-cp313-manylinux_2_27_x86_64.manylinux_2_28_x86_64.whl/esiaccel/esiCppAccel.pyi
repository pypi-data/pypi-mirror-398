from collections.abc import Callable, Sequence
import enum


class Type:
    def __init__(self, id: str) -> None: ...

    @property
    def id(self) -> str: ...

    def __repr__(self) -> str: ...

class ChannelType(Type):
    def __init__(self, id: str, inner: Type) -> None: ...

    @property
    def inner(self) -> Type: ...

class Direction(enum.Enum):
    To = 0

    From = 1

To: Direction = Direction.To

From: Direction = Direction.From

class BundleType(Type):
    def __init__(self, id: str, channels: Sequence["std::tuple<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, esi::BundleType::Direction, esi::Type const*>"]) -> None: ...

    @property
    def channels(self) -> list["std::tuple<std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> >, esi::BundleType::Direction, esi::Type const*>"]: ...

class VoidType(Type):
    def __init__(self, id: str) -> None: ...

class AnyType(Type):
    def __init__(self, id: str) -> None: ...

class BitVectorType(Type):
    def __init__(self, id: str, width: int) -> None: ...

    @property
    def width(self) -> int: ...

class BitsType(BitVectorType):
    def __init__(self, id: str, width: int) -> None: ...

class IntegerType(BitVectorType):
    def __init__(self, id: str, width: int) -> None: ...

class SIntType(IntegerType):
    def __init__(self, id: str, width: int) -> None: ...

class UIntType(IntegerType):
    def __init__(self, id: str, width: int) -> None: ...

class StructType(Type):
    def __init__(self, id: str, fields: Sequence[tuple[str, Type]], reverse: bool = True) -> None: ...

    @property
    def fields(self) -> list[tuple[str, Type]]: ...

    @property
    def reverse(self) -> bool: ...

class ArrayType(Type):
    def __init__(self, id: str, element_type: Type, size: int) -> None: ...

    @property
    def element(self) -> Type: ...

    @property
    def size(self) -> int: ...

class Constant:
    @property
    def value(self) -> object: ...

    @property
    def type(self) -> object: ...

class AppID:
    def __init__(self, name: str, idx: int | None = None) -> None: ...

    @property
    def name(self) -> str: ...

    @property
    def idx(self) -> object: ...

    def __repr__(self) -> str: ...

    def __eq__(self, arg: AppID, /) -> bool: ...

    def __hash__(self) -> int: ...

class AppIDPath:
    def __repr__(self) -> str: ...

class ModuleInfo:
    @property
    def name(self) -> str | None: ...

    @property
    def summary(self) -> str | None: ...

    @property
    def version(self) -> str | None: ...

    @property
    def repo(self) -> str | None: ...

    @property
    def commit_hash(self) -> str | None: ...

    @property
    def constants(self) -> dict[str, Constant]: ...

    def __repr__(self) -> str: ...

class LogLevel(enum.Enum):
    Debug = 1

    Info = 2

    Warning = 3

    Error = 4

Debug: LogLevel = LogLevel.Debug

Info: LogLevel = LogLevel.Info

Warning: LogLevel = LogLevel.Warning

Error: LogLevel = LogLevel.Error

class Logger:
    pass

class Service:
    def get_service_symbol(self) -> str: ...

class SysInfo(Service):
    def esi_version(self) -> int: ...

    def json_manifest(self) -> str: ...

class MMIORegionDescriptor:
    @property
    def base(self) -> int: ...

    @property
    def size(self) -> int: ...

class MMIO(Service):
    def read(self, arg: int, /) -> int: ...

    def write(self, arg0: int, arg1: int, /) -> None: ...

    @property
    def regions(self) -> dict[AppIDPath, MMIORegionDescriptor]: ...

class HostMemRegion:
    @property
    def ptr(self) -> int: ...

    @property
    def size(self) -> int: ...

class HostMemOptions:
    def __init__(self) -> None: ...

    @property
    def writeable(self) -> bool: ...

    @writeable.setter
    def writeable(self, arg: bool, /) -> None: ...

    @property
    def use_large_pages(self) -> bool: ...

    @use_large_pages.setter
    def use_large_pages(self, arg: bool, /) -> None: ...

    def __repr__(self) -> str: ...

class HostMem(Service):
    def allocate(self, size: int, options: HostMemOptions = ...) -> HostMemRegion: ...

    def map_memory(self, ptr: int, size: int, options: HostMemOptions = ...) -> bool: ...

    def unmap_memory(self, ptr: int) -> None: ...

class TelemetryService(Service):
    pass

class MessageDataFuture:
    def valid(self) -> bool: ...

    def wait(self) -> None: ...

    def get(self) -> bytearray: ...

class ConnectOptions:
    def __init__(self) -> None: ...

    @property
    def buffer_size(self) -> int | None: ...

    @buffer_size.setter
    def buffer_size(self, buffer_size: int | None) -> None: ...

    @property
    def translate_message(self) -> bool: ...

    @translate_message.setter
    def translate_message(self, arg: bool, /) -> None: ...

class ChannelPort:
    def connect(self, options: ConnectOptions) -> None:
        """Connect with specified options"""

    def disconnect(self) -> None: ...

    @property
    def type(self) -> Type: ...

class WriteChannelPort(ChannelPort):
    def write(self, arg: bytearray, /) -> None: ...

    def tryWrite(self, arg: bytearray, /) -> bool: ...

class ReadChannelPort(ChannelPort):
    def read(self) -> bytearray:
        """Read data from the channel. Blocking."""

    def read_async(self) -> MessageDataFuture: ...

class BundlePort:
    @property
    def id(self) -> AppID: ...

    @property
    def channels(self) -> dict[str, ChannelPort]: ...

    def getWrite(self, arg: str, /) -> WriteChannelPort: ...

    def getRead(self, arg: str, /) -> ReadChannelPort: ...

class ServicePort(BundlePort):
    pass

class MMIORegion(ServicePort):
    @property
    def descriptor(self) -> MMIORegionDescriptor: ...

    def read(self, arg: int, /) -> int: ...

    def write(self, arg0: int, arg1: int, /) -> None: ...

class Function(ServicePort):
    def call(self, arg: bytearray, /) -> MessageDataFuture: ...

    def connect(self) -> None: ...

class Callback(ServicePort):
    def connect(self, arg: Callable[[object], object], /) -> None: ...

class Metric(ServicePort):
    def connect(self) -> None: ...

    def read(self) -> MessageDataFuture: ...

    def readInt(self) -> int: ...

class HWModule:
    @property
    def info(self) -> ModuleInfo | None: ...

    @property
    def ports(self) -> dict[AppID, BundlePort]: ...

    @property
    def services(self) -> list[Service]: ...

    @property
    def children(self) -> dict[AppID, Instance]: ...

class Instance(HWModule):
    @property
    def id(self) -> AppID: ...

class Accelerator(HWModule):
    pass

class AcceleratorConnection:
    def sysinfo(self) -> SysInfo: ...

    def get_service_mmio(self) -> MMIO: ...

    def get_service_hostmem(self) -> HostMem: ...

    def get_accelerator(self) -> Accelerator: ...

class Context:
    """
    An ESI context owns everything -- types, accelerator connections, and the accelerator facade (aka Accelerator) itself. It MUST NOT be garbage collected while the accelerator is still in use. When it is destroyed, all accelerator connections are disconnected.
    """

    def __init__(self) -> None:
        """Create a context with a default logger."""

    def connect(self, arg0: str, arg1: str, /) -> AcceleratorConnection: ...

    def set_stdio_logger(self, arg: LogLevel, /) -> None: ...

class Manifest:
    def __init__(self, arg0: Context, arg1: str, /) -> None: ...

    @property
    def api_version(self) -> int: ...

    def build_accelerator(self, arg: AcceleratorConnection, /) -> Accelerator: ...

    @property
    def type_table(self) -> list[object]: ...

    @property
    def module_infos(self) -> list[ModuleInfo]: ...
