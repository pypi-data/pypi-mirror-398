from __future__ import annotations

import abc
import dataclasses
import enum
import ipaddress
import socket
import struct
import typing

try:
    from functools import cached_property
except ImportError:
    cached_property = property

from .constants import SOMEIPMessageType, SOMEIPReturnCode, SOMEIPSDEntryType

T = typing.TypeVar("T", ipaddress.IPv4Address, ipaddress.IPv6Address)


class SOMEIPFrame:
    """SOME/IP Frame controller

    It allows us to easily separate messages as follows::

        [                                            Header                                          ][ payload ]
        [    message ID    ][ length ][  Request ID  ][ proto ver ][ iface ver ][ msg type ][ r code ]
        [ svc ID ][ med ID ]          [ c ID ][ s ID ]
            2b        2b        4b       2b      2b        1b           1b           1b         1b
    """

    def __init__(
        self,
        service_id: int = None,
        method_id: int = None,
        client_id: int = 1,
        session_id: int = 1,
        protocol_version: int = 1,
        interface_version: int = 1,
        message_type: typing.Optional[SOMEIPMessageType] = None,
        return_code: typing.Optional[SOMEIPReturnCode] = None,
        payload: bytes = b"",
        structures: typing.Optional[dict] = None,
    ):
        """
        Initializes a new instance of the framer

        Args:
            service_id (int): SOME/IP header service id.
            method_id (int): SOME/IP header method id.
            client_id (int): SOME/IP header client id.
            session_id (int): SOME/IP header session id.
            protocol_version (int): SOME/IP header protocol version.
            interface_version (int): SOME/IP header service interface version.
            message_type (int): SOME/IP header message type.
            return_code (int): SOME/IP header return code.
            payload (bytes): SOME/IP payload.
            structures (dict): SOME/IP structures.
        """
        self.service_id = service_id
        self.method_id = method_id
        self.client_id = client_id
        self.session_id = session_id
        self.protocol_version = protocol_version
        self.interface_version = interface_version
        self.message_type = message_type
        self.return_code = return_code
        self.payload = payload
        self.structures = structures

    def __repr__(self):
        args = [
            f"service_id=0x{self.service_id:04x}",
            f"method_id=0x{self.method_id:04x}",
            f"client_id=0x{self.client_id:04x}",
            f"session_id=0x{self.session_id:04x}",
            f"protocol_version={self.protocol_version}",
            f"interface_version=0x{self.interface_version:02x}",
            f"message_type={SOMEIPMessageType(self.message_type).name}",
            f"return_code={SOMEIPReturnCode(self.return_code).name}",
            f"payload={self.payload}",
            f"structures={self.structures}",
        ]
        return f"SOMEIP.Frame({', '.join(args)})"

    def encode(self) -> bytes:
        return (
            struct.pack(
                "!HHIHHBBBB",
                self.service_id,
                self.method_id | 0x8000
                if self.message_type == SOMEIPMessageType.NOTIFICATION
                else self.method_id & 0x7FFF,
                len(self.payload) + 8,
                self.client_id,
                self.session_id,
                self.protocol_version,
                self.interface_version,
                self.message_type,
                self.return_code,
            )
            + self.payload
        )

    @classmethod
    def decode(
        cls, data: bytes, decode_all: bool = False
    ) -> typing.Union[SOMEIPFrame, typing.List[SOMEIPFrame]]:
        """decode from SOME/IP response.

        Args:
            data (bytes): SOME/IP response.

        Returns:
            SOMEIPFrame: Decoded SOME/IP frame.
        """
        someip_frames = []
        if len(data) < 16:
            raise TypeError(f"response SOME/IP frame format error, response: {data}")
        (
            service_id,
            method_id,
            length,
            client_id,
            session_id,
            protocol_version,
            interface_version,
            message_type,
            return_code,
        ) = struct.unpack("!HHIHHBBBB", data[:16])
        remaining = data[length + 8 :]
        if len(remaining) < 16 or not decode_all:
            return cls(
                service_id=service_id,
                method_id=method_id & 0x7FFF,
                client_id=client_id,
                session_id=session_id,
                protocol_version=protocol_version,
                interface_version=interface_version,
                message_type=message_type,
                return_code=return_code,
                payload=data[16 : 16 + length - 8],
            )
        else:
            someip_frames.append(
                cls(
                    service_id=service_id,
                    method_id=method_id & 0x7FFF,
                    client_id=client_id,
                    session_id=session_id,
                    protocol_version=protocol_version,
                    interface_version=interface_version,
                    message_type=message_type,
                    return_code=return_code,
                    payload=data[16 : 16 + length - 8],
                )
            )
            while len(remaining) >= 16:
                (
                    service_id,
                    method_id,
                    length,
                    client_id,
                    session_id,
                    protocol_version,
                    interface_version,
                    message_type,
                    return_code,
                ) = struct.unpack("!HHIHHBBBB", remaining[:16])
                someip_frames.append(
                    cls(
                        service_id=service_id,
                        method_id=method_id & 0x7FFF,
                        client_id=client_id,
                        session_id=session_id,
                        protocol_version=protocol_version,
                        interface_version=interface_version,
                        message_type=message_type,
                        return_code=return_code,
                        payload=remaining[16 : 16 + length - 8],
                    )
                )
                remaining = remaining[length + 8 :]
            return someip_frames


class ParseError(RuntimeError):
    pass


class IncompleteReadError(ParseError):
    pass


def _unpack(fmt, buf):
    if len(buf) < fmt.size:
        raise IncompleteReadError(
            f"can not parse {fmt.format!r}, got only {len(buf)} bytes"
        )
    return fmt.unpack(buf[: fmt.size]), buf[fmt.size :]


def _find(haystack, needle):
    """Return the index at which the sequence needle appears in the sequence haystack,
    or -1 if it is not found, using the Boyer-Moore-Horspool algorithm. The elements of
    needle and haystack must be hashable.

    >>> find([1, 1, 2], [1, 2])
    1

    from https://codereview.stackexchange.com/a/19629
    """
    h = len(haystack)
    n = len(needle)
    skip = {needle[i]: n - i - 1 for i in range(n - 1)}
    i = n - 1
    while i < h:
        for j in range(n):
            if haystack[i - j] != needle[-j - 1]:
                i += skip.get(haystack[i], n)
                break
        else:
            return i - n + 1
    return None


@dataclasses.dataclass(frozen=True)
class SOMEIPSDEntry:
    """
    Represents an Entry in SOMEIP SD packets.

    :param sd_type:
    :param service_id:
    :param instance_id:
    :param major_version:
    :param ttl:
    :param minver_or_counter: service minor version or eventgroup id and counter value
    :param options_1: resolved options that apply to this entry (run 1)
    :param options_2: resolved options that apply to this entry (run 2)
    :param option_index_1: option index (for unresolved options, run 1)
    :param option_index_2: option index (for unresolved options, run 2)
    :param num_options_1: number of option (for unresolved options, run 1)
    :param num_options_2: number of option (for unresolved options, run 2)
    """

    __format: typing.ClassVar[struct.Struct] = struct.Struct("!BBBBHHBBHI")
    sd_type: SOMEIPSDEntryType
    service_id: int
    instance_id: int
    major_version: int
    ttl: int
    minver_or_counter: int

    options_1: typing.Tuple[SOMEIPSDOption, ...] = ()
    options_2: typing.Tuple[SOMEIPSDOption, ...] = ()

    option_index_1: typing.Optional[int] = None
    option_index_2: typing.Optional[int] = None
    num_options_1: typing.Optional[int] = None
    num_options_2: typing.Optional[int] = None

    def __str__(self) -> str:  # pragma: nocover
        if self.sd_type in (
            SOMEIPSDEntryType.FindService,
            SOMEIPSDEntryType.OfferService,
        ):
            version = f"{self.major_version}.{self.service_minor_version}"
        elif self.sd_type in (
            SOMEIPSDEntryType.Subscribe,
            SOMEIPSDEntryType.SubscribeAck,
        ):
            version = (
                f"{self.major_version}, eventgroup_counter={self.eventgroup_counter},"
                f" eventgroup_id={self.eventgroup_id}"
            )

        if self.options_resolved:
            s_options_1 = ", ".join(str(o) for o in self.options_1)
            s_options_2 = ", ".join(str(o) for o in self.options_2)
        else:
            oi1 = typing.cast(int, self.option_index_1)
            oi2 = typing.cast(int, self.option_index_2)
            no1 = typing.cast(int, self.num_options_1)
            no2 = typing.cast(int, self.num_options_2)
            s_options_1 = repr(range(oi1, oi1 + no1))
            s_options_2 = repr(range(oi2, oi2 + no2))

        return (
            f"type={self.sd_type.name}, service=0x{self.service_id:04x},"
            f" instance=0x{self.instance_id:04x}, version={version}, ttl={self.ttl}, "
            f" options_1=[{s_options_1}], options_2=[{s_options_2}]"
        )

    @cached_property
    def options(self) -> typing.Tuple[SOMEIPSDOption, ...]:
        """
        convenience wrapper contains merged :attr:`options_1` and :attr:`options_2`
        """
        return self.options_1 + self.options_2

    @property
    def options_resolved(self) -> bool:
        """
        indicates if the options on this instance are resolved
        """
        return (
            self.option_index_1 is None
            or self.option_index_2 is None
            or self.num_options_1 is None
            or self.num_options_2 is None
        )

    def resolve_options(
        self, options: typing.Tuple[SOMEIPSDOption, ...]
    ) -> SOMEIPSDEntry:
        """
        resolves this entry's options with option list from containing
        :class:`SOMEIPSDHeader`.

        :return: a new :class:`SOMEIPSDEntry` instance with resolved options
        """
        if self.options_resolved:
            raise ValueError("options already resolved")

        oi1 = typing.cast(int, self.option_index_1)
        oi2 = typing.cast(int, self.option_index_2)
        no1 = typing.cast(int, self.num_options_1)
        no2 = typing.cast(int, self.num_options_2)

        return dataclasses.replace(
            self,
            options_1=options[oi1 : oi1 + no1],
            options_2=options[oi2 : oi2 + no2],
            option_index_1=None,
            option_index_2=None,
            num_options_1=None,
            num_options_2=None,
        )

    @staticmethod
    def _assign_option(entry_options, hdr_options) -> typing.Tuple[int, int]:
        if not entry_options:
            return (0, 0)

        no = len(entry_options)
        oi = _find(hdr_options, entry_options)
        if oi is None:
            oi = len(hdr_options)
            hdr_options.extend(entry_options)
        return oi, no

    def assign_option_index(
        self, options: typing.List[SOMEIPSDOption]
    ) -> SOMEIPSDEntry:
        """
        assigns option indexes, optionally inserting new options to the given option
        list. Index assignment is done in a simple manner by searching if a slice exists
        in `options` that matches the option runs (:attr:`options_1` and
        :attr:`options_2`).

        :return: a new :class:`SOMEIPSDEntry` instance with assigned options indexes
        """
        if not self.options_resolved:
            return dataclasses.replace(self)  # pragma: nocover

        oi1, no1 = self._assign_option(self.options_1, options)
        oi2, no2 = self._assign_option(self.options_2, options)
        return dataclasses.replace(
            self,
            option_index_1=oi1,
            option_index_2=oi2,
            num_options_1=no1,
            num_options_2=no2,
            options_1=(),
            options_2=(),
        )

    @property
    def service_minor_version(self) -> int:
        """
        the service minor version

        :raises TypeError: if this entry is not a FindService or OfferService
        """
        if self.sd_type not in (
            SOMEIPSDEntryType.FindService,
            SOMEIPSDEntryType.OfferService,
        ):
            raise TypeError(
                f"SD entry is type {self.sd_type},"
                " does not have service_minor_version"
            )
        return self.minver_or_counter

    @property
    def eventgroup_counter(self) -> int:
        """
        the eventgroup counter

        :raises TypeError: if this entry is not a Subscribe or SubscribeAck
        """
        if self.sd_type not in (
            SOMEIPSDEntryType.Subscribe,
            SOMEIPSDEntryType.SubscribeAck,
        ):
            raise TypeError(
                f"SD entry is type {self.sd_type}, does not have eventgroup_counter"
            )
        return (self.minver_or_counter >> 16) & 0x0F

    @property
    def eventgroup_id(self) -> int:
        """
        the eventgroup id

        :raises TypeError: if this entry is not a Subscribe or SubscribeAck
        """
        if self.sd_type not in (
            SOMEIPSDEntryType.Subscribe,
            SOMEIPSDEntryType.SubscribeAck,
        ):
            raise TypeError(
                f"SD entry is type {self.sd_type}, does not have eventgroup_id"
            )
        return self.minver_or_counter & 0xFFFF

    @classmethod
    def parse(cls, buf: bytes, num_options: int) -> typing.Tuple[SOMEIPSDEntry, bytes]:
        """
        parses SOMEIP SD entry in `buf`

        :param buf: buffer containing SOMEIP SD entry
        :param num_options: number of known options in containing
            :class:`SOMEIPSDHeader`
        :raises ParseError: if the buffer did not parse as a SOMEIP SD entry, e.g., due
            to an unknown entry type or out-of-bounds option indexes
        :return: tuple (S, B) where S is the parsed :class:`SOMEIPSDEntry` instance and
            B is the unparsed rest of `buf`
        """
        (
            (sd_type_b, oi1, oi2, numopt, sid, iid, majv, ttl_hi, ttl_lo, val),
            buf_rest,
        ) = _unpack(cls.__format, buf)
        try:
            sd_type = SOMEIPSDEntryType(sd_type_b)
        except ValueError as exc:
            raise ParseError("bad someip sd entry type {sd_type_b:#x}") from exc

        no1 = numopt >> 4
        no2 = numopt & 0x0F
        ttl = (ttl_hi << 16) | ttl_lo

        if oi1 + no1 > num_options:
            raise ParseError(
                f"SD entry options_1 ({oi1}:{oi1+no1}) out of range ({num_options})"
            )

        if oi2 + no2 > num_options:
            raise ParseError(
                f"SD entry options_2 ({oi2}:{oi2+no2}) out of range ({num_options})"
            )

        if sd_type in (SOMEIPSDEntryType.Subscribe, SOMEIPSDEntryType.SubscribeAck):
            if val & 0xFFF00000:
                raise ParseError(
                    "expected counter and eventgroup_id to be 4 + 16-bit"
                    " with 12 upper bits zeros"
                )

        parsed = cls(
            sd_type=sd_type,
            option_index_1=oi1,
            option_index_2=oi2,
            num_options_1=no1,
            num_options_2=no2,
            service_id=sid,
            instance_id=iid,
            major_version=majv,
            ttl=ttl,
            minver_or_counter=val,
        )

        return parsed, buf_rest

    def build(self) -> bytes:
        """
        build the byte representation of this entry.

        :raises ValueError: if the option indexes on this entry were not resolved.
            see :meth:`assign_option_index`
        :raises struct.error: if any attribute was out of range for serialization
        :return: the byte representation
        """
        if self.options_resolved:
            raise ValueError("option indexes must be assigned before building")
        oi1 = typing.cast(int, self.option_index_1)
        oi2 = typing.cast(int, self.option_index_2)
        no1 = typing.cast(int, self.num_options_1)
        no2 = typing.cast(int, self.num_options_2)
        return self.__format.pack(
            self.sd_type.value,
            oi1,
            oi2,
            (no1 << 4) | no2,
            self.service_id,
            self.instance_id,
            self.major_version,
            self.ttl >> 16,
            self.ttl & 0xFFFF,
            self.minver_or_counter,
        )


class SOMEIPSDOption(metaclass=abc.ABCMeta):
    """
    Abstract base class representing SD options
    """

    __format: typing.ClassVar[struct.Struct] = struct.Struct("!HB")
    _options: typing.ClassVar[
        typing.Dict[int, typing.Type[SOMEIPSDAbstractOption]]
    ] = {}

    @classmethod
    def register(
        cls, option_cls: typing.Type[SOMEIPSDAbstractOption]
    ) -> typing.Type[SOMEIPSDAbstractOption]:
        """
        Decorator for SD option classes, to register them for option parsing, identified
        by their :attr:`SOMEIPSDAbstractOption.type` members.
        """
        cls._options[option_cls.type] = option_cls
        return option_cls

    @classmethod
    def parse(cls, buf: bytes) -> typing.Tuple[SOMEIPSDOption, bytes]:
        """
        parses SOMEIP SD option in `buf`. Options with unknown types will be parsed as
        :class:`SOMEIPSDUnknownOption`, known types will be parsed to their registered
        types.

        :param buf: buffer containing SOMEIP SD option
        :raises ParseError: if the buffer did not parse as a SOMEIP SD option, e.g., due
            to out-of-bounds lengths or the specific
            :meth:`SOMEIPSDAbstractOption.parse_option` failed
        :return: tuple (S, B) where S is the parsed :class:`SOMEIPSDOption` instance and
            B is the unparsed rest of `buf`
        """
        (len_b, type_b), buf_rest = _unpack(cls.__format, buf)
        if len(buf_rest) < len_b:
            raise ParseError(
                f"option data too short, expected {len_b}, got {buf_rest!r}"
            )
        opt_b, buf_rest = buf_rest[:len_b], buf_rest[len_b:]

        opt_cls = cls._options.get(type_b)
        if not opt_cls:
            return SOMEIPSDUnknownOption(type=type_b, payload=opt_b), buf_rest

        return opt_cls.parse_option(opt_b), buf_rest

    def build_option(self, type_b: int, buf: bytes) -> bytes:
        """
        Helper for SD option classes to build the byte representation of their option.

        :param type_b: option type identifier
        :param buf: buffer SD option data
        :raises struct.error: if the buffer is too big to be represented, or `type_b` is
            out of range
        :return: the byte representation
        """
        return self.__format.pack(len(buf), type_b) + buf

    @abc.abstractmethod
    def build(self) -> bytes:
        """
        build the byte representation of this option, must be implemented by actual
        options. Should use :meth:`build_option` to build the option header.

        :raises struct.error: if any attribute was out of range for serialization
        :return: the byte representation
        """
        ...


@dataclasses.dataclass(frozen=True)
class SOMEIPSDUnknownOption(SOMEIPSDOption):
    """
    Received options with unknown option types are parsed as this generic class.

    :param type: the type identifier for this unknown option
    :param payload: the option payload
    """

    type: int
    payload: bytes

    def build(self) -> bytes:
        """
        build the byte representation of this option.

        :raises struct.error: if :attr:`payload` is too big to be represented, or
            :attr:`type` is out of range
        :return: the byte representation
        """
        return self.build_option(self.type, self.payload)


class SOMEIPSDAbstractOption(SOMEIPSDOption):
    """
    Base class for specific option implementations.
    """

    type: typing.ClassVar[int]
    """
    Class variable. Used to differentiate SD option types when parsing. See
    :meth:`SOMEIPSDOption.register` and :meth:`SOMEIPSDOption.parse`
    """

    @classmethod
    @abc.abstractmethod
    def parse_option(cls, buf: bytes) -> SOMEIPSDAbstractOption:
        """
        parses SD option payload in `buf`.

        :param buf: buffer containing SOMEIP SD option data
        :raises ParseError: if this option type fails to parse `buf`
        :return: the parsed instance
        """
        ...


@SOMEIPSDOption.register
@dataclasses.dataclass(frozen=True)
class SOMEIPSDLoadBalancingOption(SOMEIPSDAbstractOption):
    type: typing.ClassVar[int] = 2
    priority: int
    weight: int

    @classmethod
    def parse_option(cls, buf: bytes) -> SOMEIPSDLoadBalancingOption:
        if len(buf) != 5:
            raise ParseError(
                f"SD load balancing option with wrong payload length {len(buf)} != 5"
            )

        prio, weight = struct.unpack("!HH", buf[1:])
        return cls(priority=prio, weight=weight)

    def build(self) -> bytes:
        """
        build the byte representation of this option.

        :raises struct.error: if :attr:`payload` is too big to be represented, or
            :attr:`type` is out of range
        :return: the byte representation
        """
        return self.build_option(
            self.type, struct.pack("!BHH", 0, self.priority, self.weight)
        )


@SOMEIPSDOption.register
@dataclasses.dataclass(frozen=True)
class SOMEIPSDConfigOption(SOMEIPSDAbstractOption):
    type: typing.ClassVar[int] = 1
    configs: typing.Tuple[typing.Tuple[str, typing.Optional[str]], ...]

    @classmethod
    def parse_option(cls, buf: bytes) -> SOMEIPSDConfigOption:
        if len(buf) < 2:
            raise ParseError(
                f"SD config option with wrong payload length {len(buf)} < 2"
            )

        b = buf[1:]
        nextlen, b = b[0], b[1:]

        configs: typing.List[typing.Tuple[str, typing.Optional[str]]] = []

        while nextlen != 0:
            if len(b) < nextlen + 1:
                raise ParseError(
                    f"SD config option length {nextlen} too big for remaining"
                    f" option buffer {b!r}"
                )

            cfg_str, b = b[:nextlen], b[nextlen:]

            split = cfg_str.find(b"=")
            if split == -1:
                configs.append((cfg_str.decode("ascii"), None))
            else:
                key, value = cfg_str[:split], cfg_str[split + 1 :]
                configs.append((key.decode("ascii"), value.decode("ascii")))
            nextlen, b = b[0], b[1:]
        return cls(configs=tuple(configs))

    def build(self) -> bytes:
        """
        build the byte representation of this option.

        :raises struct.error: if :attr:`payload` is too big to be represented, or
            :attr:`type` is out of range
        :return: the byte representation
        """
        buf = bytearray([0])
        for k, v in self.configs:
            if v is not None:
                buf.append(len(k) + len(v) + 1)
                buf += k.encode("ascii")
                buf += b"="
                buf += v.encode("ascii")
            else:
                buf.append(len(k))
                buf += k.encode("ascii")
        buf.append(0)
        return self.build_option(self.type, buf)


class L4Protocols(enum.IntEnum):
    """
    Enum for valid layer 4 protocol identifiers.
    """

    TCP = socket.IPPROTO_TCP
    UDP = socket.IPPROTO_UDP


@dataclasses.dataclass(frozen=True)
class AbstractIPOption(SOMEIPSDAbstractOption, typing.Generic[T]):
    """
    Abstract base class for options with IP payloads. Generalizes parsing and building
    based on :attr:`_format`, :attr:`_address_type` and :attr:`_family`.
    """

    _format: typing.ClassVar[struct.Struct]
    _address_type: typing.ClassVar[typing.Type[typing.Any]]
    _family: typing.ClassVar[socket.AddressFamily]
    address: T
    l4proto: typing.Union[L4Protocols, int]
    port: int

    @classmethod
    def parse_option(cls, buf: bytes) -> AbstractIPOption[T]:
        if len(buf) != cls._format.size:
            raise ParseError(
                f"{cls.__name__} with wrong payload length {len(buf)} != 9"
            )

        r1, addr_b, r2, l4proto_b, port = cls._format.unpack(buf)

        addr = cls._address_type(addr_b)
        try:
            l4proto = L4Protocols(l4proto_b)
        except ValueError:
            l4proto = l4proto_b

        return cls(address=addr, l4proto=l4proto, port=port)

    def build(self) -> bytes:
        """
        build the byte representation of this option.

        :raises struct.error: if :attr:`payload` is too big to be represented, or
            :attr:`type` is out of range
        :return: the byte representation
        """
        payload = self._format.pack(0, self.address.packed, 0, self.l4proto, self.port)
        return self.build_option(self.type, payload)


class EndpointOption(AbstractIPOption[T]):
    """
    Abstract base class for endpoint options (IPv4 or IPv6).
    """

    pass


class MulticastOption(AbstractIPOption[T]):
    """
    Abstract base class for multicast options (IPv4 or IPv6).
    """

    pass


class SDEndpointOption(AbstractIPOption[T]):
    """
    Abstract base class for SD Endpoint options (IPv4 or IPv6).
    """

    pass


class AbstractIPv4Option(AbstractIPOption[ipaddress.IPv4Address]):
    """
    Abstract base class for IPv4 options.
    """

    _format: typing.ClassVar[struct.Struct] = struct.Struct("!B4sBBH")
    _address_type = ipaddress.IPv4Address
    _family = socket.AF_INET

    def __str__(self) -> str:  # pragma: nocover
        if isinstance(self.l4proto, L4Protocols):
            return f"{self.address}:{self.port} ({self.l4proto.name})"
        else:
            return f"{self.address}:{self.port} (protocol={self.l4proto:#x})"


class AbstractIPv6Option(AbstractIPOption[ipaddress.IPv6Address]):
    """
    Abstract base class for IPv6 options.
    """

    _format: typing.ClassVar[struct.Struct] = struct.Struct("!B16sBBH")
    _address_type = ipaddress.IPv6Address
    _family = socket.AF_INET6

    def __str__(self) -> str:  # pragma: nocover
        if isinstance(self.l4proto, L4Protocols):
            return f"{self.address}:{self.port} ({self.l4proto.name})"
        else:
            return f"{self.address}:{self.port} (protocol={self.l4proto:#x})"


@SOMEIPSDOption.register
class IPv4EndpointOption(AbstractIPv4Option, EndpointOption[ipaddress.IPv4Address]):
    type: typing.ClassVar[int] = 0x04


@SOMEIPSDOption.register
class IPv4MulticastOption(AbstractIPv4Option, MulticastOption[ipaddress.IPv4Address]):
    type: typing.ClassVar[int] = 0x14


@SOMEIPSDOption.register
@dataclasses.dataclass(frozen=True)
class IPv4SDEndpointOption(AbstractIPv4Option, SDEndpointOption[ipaddress.IPv4Address]):
    type: typing.ClassVar[int] = 0x24


@SOMEIPSDOption.register
class IPv6EndpointOption(AbstractIPv6Option, EndpointOption[ipaddress.IPv6Address]):
    type: typing.ClassVar[int] = 0x06


@SOMEIPSDOption.register
class IPv6MulticastOption(AbstractIPv6Option, MulticastOption[ipaddress.IPv6Address]):
    type: typing.ClassVar[int] = 0x16


@SOMEIPSDOption.register
@dataclasses.dataclass(frozen=True)
class IPv6SDEndpointOption(AbstractIPv6Option, SDEndpointOption[ipaddress.IPv6Address]):
    type: typing.ClassVar[int] = 0x26


@dataclasses.dataclass(frozen=True)
class SOMEIPSDHeader:
    """
    Represents a SOMEIP SD packet.
    """

    entries: typing.Tuple[SOMEIPSDEntry, ...]
    options: typing.Tuple[SOMEIPSDOption, ...] = ()
    flag_reboot: bool = False
    flag_unicast: bool = True
    flags_unknown: int = 0

    def resolve_options(self):
        """
        resolves all `entries`' options from `options` list.

        :return: a new :class:`SOMEIPSDHeader` instance with entries with resolved
            options
        """
        entries = [e.resolve_options(self.options) for e in self.entries]
        return dataclasses.replace(self, entries=tuple(entries))

    def assign_option_indexes(self):
        """
        assigns option indexes to all `entries` and builds the `options` list.

        :return: a new :class:`SOMEIPSDHeader` instance with entries with assigned
            options indexes
        """
        options = list(self.options)
        entries = [e.assign_option_index(options) for e in self.entries]
        return dataclasses.replace(self, entries=tuple(entries), options=tuple(options))

    def __str__(self):  # pragma: nocover
        entries = "\n".join(str(e) for e in self.entries)
        return f"""reboot={self.flag_reboot}, unicast={self.flag_unicast}, entries:
{entries}"""

    @classmethod
    def parse(cls, buf: bytes) -> typing.Tuple[SOMEIPSDHeader, bytes]:
        """
        parses SOMEIP SD packet in `buf`

        :param buf: buffer containing SOMEIP packet
        :raises ParseError: if the packet contained invalid data, such as out-of-bounds
            lengths or failing :meth:`SOMEIPSDEntry.parse` and
            :meth:`SOMEIPSDOption.parse`
        :return: tuple (S, B) where S is the parsed :class:`SOMEIPSDHeader` instance and
            B is the unparsed rest of `buf`
        """
        if len(buf) < 12:
            raise ParseError(f"can not parse SOMEIPSDHeader, got only {len(buf)} bytes")

        flags = buf[0]

        entries_length = struct.unpack("!I", buf[4:8])[0]
        rest_buf = buf[8:]
        if len(rest_buf) < entries_length + 4:
            raise ParseError(
                f"can not parse SOMEIPSDHeader, entries length too big"
                f" ({entries_length})"
            )
        entries_buffer, rest_buf = rest_buf[:entries_length], rest_buf[entries_length:]

        options_length = struct.unpack("!I", rest_buf[:4])[0]
        rest_buf = rest_buf[4:]
        if len(rest_buf) < options_length:
            raise ParseError(
                f"can not parse SOMEIPSDHeader, options length too big"
                f" ({options_length}"
            )
        options_buffer, rest_buf = rest_buf[:options_length], rest_buf[options_length:]

        options = []
        while options_buffer:
            option, options_buffer = SOMEIPSDOption.parse(options_buffer)
            options.append(option)

        entries = []
        while entries_buffer:
            entry, entries_buffer = SOMEIPSDEntry.parse(entries_buffer, len(options))
            entries.append(entry)

        flag_reboot = bool(flags & 0x80)
        flags &= ~0x80

        flag_unicast = bool(flags & 0x40)
        flags &= ~0x40

        parsed = cls(
            flag_reboot=flag_reboot,
            flag_unicast=flag_unicast,
            flags_unknown=flags,
            entries=tuple(entries),
            options=tuple(options),
        )
        return parsed, rest_buf

    def build(self) -> bytes:
        """
        builds the byte representation of this SOMEIP SD packet.

        :raises struct.error: if any attribute was out of range for serialization
        :raises ValueError: from :meth:`SOMEIPSDEntry.build`
        :return: the byte representation
        """
        flags = self.flags_unknown

        if self.flag_reboot:
            flags |= 0x80

        if self.flag_unicast:
            flags |= 0x40

        buf = bytearray([flags, 0, 0, 0])

        entries_buf = b"".join(e.build() for e in self.entries)
        options_buf = b"".join(e.build() for e in self.options)

        buf += struct.pack("!I", len(entries_buf))
        buf += entries_buf
        buf += struct.pack("!I", len(options_buf))
        buf += options_buf

        return buf


class SOMEIPSDFrame(SOMEIPFrame):
    """SOME/IP-SD Frame controller

    It allows us to easily separate messages as follows::

        [                                            Header                                          ]
        [...]
        [ Flags ][ Reserved ][ Entries Len ][ Entries Array ][ Options Len ][ Options Array ]
            1b        3b            4b             el                4b             ol
    """

    SD_SERVICE_ID = 0xFFFF
    SD_METHOD_ID = 0x8100
    SD_CLIENT_ID = 0x0000
    SD_PROTOCOL_VERSION = 1
    SD_INTERFACE_VERSION = 1
    SD_MESSAGE_TYPE = SOMEIPMessageType.NOTIFICATION
    SD_RETURN_CODE = SOMEIPReturnCode.E_OK

    def __init__(
        self,
        session_id: int = 1,
        flag_reboot: bool = False,
        flag_unicast: bool = True,
        flags_unknown: int = 0,
        entries: typing.Tuple[SOMEIPSDEntry, ...] = (),
        options: typing.Tuple[SOMEIPSDOption, ...] = (),
    ):
        self.flag_reboot = flag_reboot
        self.flag_unicast = flag_unicast
        self.flag_unknown = flags_unknown
        self.entries = entries
        self.options = options
        super().__init__(
            service_id=self.SD_SERVICE_ID,
            method_id=self.SD_METHOD_ID,
            client_id=self.SD_CLIENT_ID,
            session_id=session_id,
            protocol_version=self.SD_PROTOCOL_VERSION,
            interface_version=self.SD_INTERFACE_VERSION,
            message_type=self.SD_MESSAGE_TYPE,
            return_code=self.SD_RETURN_CODE,
            payload=self.encode_sd(),
        )

    def encode_sd(self):
        msg = SOMEIPSDHeader(
            flag_reboot=self.flag_reboot,
            flag_unicast=self.flag_unicast,
            entries=tuple(self.entries),
        )
        msg_assigned = msg.assign_option_indexes()
        return msg_assigned.build()

    def decode_sd(self, data: bytes) -> typing.Tuple[SOMEIPSDHeader, bytes]:
        sd_hdr, remaining = SOMEIPSDHeader.parse(data)
        self.flag_reboot = sd_hdr.flag_reboot
        self.flag_unicast = sd_hdr.flag_unicast
        self.flag_unknown = sd_hdr.flags_unknown
        self.entries = sd_hdr.entries
        self.optionss = sd_hdr.options
        return sd_hdr, remaining

    @classmethod
    def check_ack(cls, data: bytes):
        parsed, _ = cls.decode_sd(cls, data)
        assert parsed.entries[0].sd_type == SOMEIPSDEntryType.SubscribeAck
