import collections
import ctypes
import struct

from scapy.all import *
from scapy.fields import *
from scapy.layers.inet import TCP, UDP
from scapy.packet import Packet, Raw

from .constants import SOMEIPMessageType, SOMEIPReturnCode, SOMEIPTPMessageType

SOMEIP_MSGS_TYPES = [i.value for i in SOMEIPMessageType]
SOMEIP_TP_TYPES = [i.value for i in SOMEIPTPMessageType]


class _SOMEIP_MessageId(Packet):
    """MessageId subpacket."""

    name = "MessageId"
    fields_desc = [
        ShortField("service_id", 0),
        BitEnumField("sub_id", 0, 1, {0: "METHOD_ID", 1: "EVENT_ID"}),
        ConditionalField(BitField("method_id", 0, 15), lambda pkt: pkt.sub_id == 0),
        ConditionalField(BitField("event_id", 0, 15), lambda pkt: pkt.sub_id == 1),
    ]

    def extract_padding(self, p):
        return "", p


class _SOMEIP_RequestId(Packet):
    """RequestId subpacket."""

    name = "RequestId"
    fields_desc = [ShortField("client_id", 0), ShortField("session_id", 0)]

    def extract_padding(self, p):
        return "", p


class SOMEIP(Packet):
    """SOME/IP Packet."""

    # Default values
    PROTOCOL_VERSION = 0x01
    INTERFACE_VERSION = 0x01

    # Lenght offset (without payload)
    LEN_OFFSET = 0x08

    SOMEIP_TP_TYPE_BIT_MASK = 0x20

    # SOME/IP-TP More Segments Flag
    SOMEIP_TP_LAST_SEGMENT = 0
    SOMEIP_TP_MORE_SEGMENTS = 1

    _OVERALL_LEN_NOPAYLOAD = 16

    name = "SOME/IP"

    fields_desc = [
        PacketField("message_id", _SOMEIP_MessageId(), _SOMEIP_MessageId),
        IntField("length", None),
        PacketField("request_id", _SOMEIP_RequestId(), _SOMEIP_RequestId),
        ByteField("protocol_version", PROTOCOL_VERSION),
        ByteField("interface_version", INTERFACE_VERSION),
        ByteEnumField(
            "message_type",
            SOMEIPMessageType.REQUEST,
            {
                SOMEIPMessageType.REQUEST: "REQUEST",
                SOMEIPMessageType.REQUEST_NO_RETURN: "REQUEST_NO_RETURN",
                SOMEIPMessageType.NOTIFICATION: "NOTIFICATION",
                SOMEIPMessageType.REQUEST_ACK: "REQUEST_ACK",
                SOMEIPMessageType.REQUEST_NO_RETURN_ACK: "REQUEST_NO_RETURN_ACK",
                SOMEIPMessageType.NOTIFICATION_ACK: "NOTIFICATION_ACK",
                SOMEIPMessageType.RESPONSE: "RESPONSE",
                SOMEIPMessageType.ERROR: "ERROR",
                SOMEIPMessageType.RESPONSE_ACK: "RESPONSE_ACK",
                SOMEIPMessageType.ERROR_ACK: "ERROR_ACK",
                SOMEIPTPMessageType.TYPE_REQUEST_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_REQUEST_NO_RET_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_NOTIFICATION_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_REQUEST_ACK_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_REQUEST_NORET_ACK_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_NOTIFICATION_ACK_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_RESPONSE_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_ERROR_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_RESPONSE_ACK_SEGMENT: "REQUEST-TP",
                SOMEIPTPMessageType.TYPE_ERROR_ACK_SEGMENT: "REQUEST-TP",
            },
        ),
        ByteEnumField(
            "return_code",
            SOMEIPReturnCode.E_OK,
            {
                SOMEIPReturnCode.E_OK: "E_OK",
                SOMEIPReturnCode.E_NOT_OK: "E_NOT_OK",
                SOMEIPReturnCode.E_UNKNOWN_SERVICE: "E_UNKNOWN_SERVICE",
                SOMEIPReturnCode.E_UNKNOWN_METHOD: "E_UNKNOWN_METHOD",
                SOMEIPReturnCode.E_NOT_READY: "E_NOT_READY",
                SOMEIPReturnCode.E_NOT_REACHABLE: "E_NOT_REACHABLE",
                SOMEIPReturnCode.E_TIMEOUT: "E_TIMEOUT",
                SOMEIPReturnCode.E_WRONG_PROTOCOL_VERSION: "E_WRONG_PROTOCOL_VERSION",
                SOMEIPReturnCode.E_WRONG_INTERFACE_VERSION: "E_WRONG_INTERFACE_VERSION",
                SOMEIPReturnCode.E_MALFORMED_MESSAGE: "E_MALFORMED_MESSAGE",
                SOMEIPReturnCode.E_WRONG_MESSAGE_TYPE: "E_WRONG_MESSAGE_TYPE",
            },
        ),
        ConditionalField(
            BitField("offset", 0, 28),
            lambda pkt: pkt.message_type in SOMEIP_TP_TYPES,
        ),
        ConditionalField(
            BitField("reserved", 0, 3),
            lambda pkt: pkt.message_type in SOMEIP_TP_TYPES,
        ),
        ConditionalField(
            BitEnumField(
                "more_segments",
                0,
                1,
                {
                    SOMEIP_TP_LAST_SEGMENT: "Last_Segment",
                    SOMEIP_TP_MORE_SEGMENTS: "More_Segments",
                },
            ),
            lambda pkt: pkt.message_type in SOMEIP_TP_TYPES,
        ),
    ]

    def post_build(self, p, pay):
        length = self.len
        # length computation : RequestID + PROTOVER_IFACEVER_TYPE_RETCODE + PAYLOAD
        if length is None:
            length = self.LEN_OFFSET + len(pay)
            p = p[:4] + struct.pack("!I", length) + p[8:]
        return p + pay

    def guess_payload_class(self, payload):
        if self.message_id.service_id == 0xFFFF:
            return SOMEIP_SD
        return Raw


class _SDPacketBase(Packet):
    """base class to be used among all SD Packet definitions."""

    # use this dictionary to set default values for desired fields (mostly on subclasses
    # where not all fields are defined locally)
    # - key : field_name, value : desired value
    # - it will be used from 'init_fields' function, upon packet initialization
    #
    # example : _defaults = {'field_1_name':field_1_value,'field_2_name':field_2_value}
    _defaults = {}

    def _set_defaults(self):
        """goes through '_defaults' dict setting field default values (for those that have been defined)."""
        for key in self._defaults.keys():
            try:
                self.get_field(key)
            except KeyError:
                pass
            else:
                self.setfieldval(key, self._defaults[key])

    def init_fields(self, for_dissect_only=False):
        super().init_fields(for_dissect_only)
        self._set_defaults()


# SD ENTRY
#  - Service
#  - EventGroup
class _SDEntry(_SDPacketBase):
    """Base class for SDEntry_* packages."""

    TYPE_FMT = ">B"
    TYPE_PAYLOAD_I = 0
    # ENTRY TYPES : SERVICE
    TYPE_SRV_FINDSERVICE = 0x00
    TYPE_SRV_OFFERSERVICE = 0x01
    TYPE_SRV = (TYPE_SRV_FINDSERVICE, TYPE_SRV_OFFERSERVICE)
    # ENTRY TYPES : EVENGROUP
    TYPE_EVTGRP_SUBSCRIBE = 0x06
    TYPE_EVTGRP_SUBSCRIBE_ACK = 0x07
    TYPE_EVTGRP = (TYPE_EVTGRP_SUBSCRIBE, TYPE_EVTGRP_SUBSCRIBE_ACK)
    # overall len (UT usage)
    OVERALL_LEN = 16

    # fields_desc = [
    #     ByteField("type", 0),
    #     ByteField("index_1", 0),
    #     ByteField("index_2", 0),
    #     BitField("n_opt_1", 0, 4),
    #     BitField("n_opt_2", 0, 4),
    #     ShortField("service_id", 0),
    #     ShortField("instance_id", 0),
    #     ByteField("major_version", 0),
    #     X3BytesField("ttl", 0),
    # ]

    def guess_payload_class(self, payload):
        """decode SDEntry depending on its type."""
        pl_type = struct.unpack(
            _SDEntry.TYPE_FMT,
            payload[_SDEntry.TYPE_PAYLOAD_I : _SDEntry.TYPE_PAYLOAD_I + 1],
        )[0]
        if pl_type in _SDEntry.TYPE_SRV:
            return SDEntry_Service
        elif pl_type in _SDEntry.TYPE_EVTGRP:
            return SDEntry_EventGroup


class SDEntry_Service(_SDEntry):
    """Service Entry."""

    _defaults = {"type": _SDEntry.TYPE_SRV_FINDSERVICE}

    name = "Service Entry"
    # fields_desc = [_SDEntry, IntField("minor_version", 0)]
    fields_desc = [
        ByteField("type", 0),
        ByteField("index_1", 0),
        ByteField("index_2", 0),
        BitField("n_opt_1", 0, 4),
        BitField("n_opt_2", 0, 4),
        ShortField("service_id", 0),
        ShortField("instance_id", 0),
        ByteField("major_version", 0),
        X3BytesField("ttl", 0),
        IntField("minor_version", 0),
    ]


class SDEntry_EventGroup(_SDEntry):
    """EventGroup Entry."""

    _defaults = {"type": _SDEntry.TYPE_EVTGRP_SUBSCRIBE}

    name = "Eventgroup Entry"
    # fields_desc = [
    #     _SDEntry,
    #     BitField("reserved", 0, 12),
    #     BitField("cnt", 0, 4),
    #     ShortField("eventgroup_id", 0),
    # ]
    fields_desc = [
        ByteField("type", 0),
        ByteField("index_1", 0),
        ByteField("index_2", 0),
        BitField("n_opt_1", 0, 4),
        BitField("n_opt_2", 0, 4),
        ShortField("service_id", 0),
        ShortField("instance_id", 0),
        ByteField("major_version", 0),
        X3BytesField("ttl", 0),
        BitField("reserved", 0, 12),
        BitField("cnt", 0, 4),
        ShortField("eventgroup_id", 0),
    ]


# SD Option
#  - Configuration
#  - LoadBalancing
#  - IPv4 EndPoint
#  - IPv6 EndPoint
#  - IPv4 MultiCast
#  - IPv6 MultiCast
#  - IPv4 SDEndPoint
#  - IPv6 SDEndPoint
class _SDOption(_SDPacketBase):
    """Base class for SDOption_* packages."""

    TYPE_FMT = ">B"
    TYPE_PAYLOAD_I = 2

    CFG_TYPE = 0x01
    CFG_OVERALL_LEN = (
        4  # overall length of CFG SDOption,empty 'cfg_str' (to be used from UT)
    )
    LOADBALANCE_TYPE = 0x02
    LOADBALANCE_LEN = 0x05
    LOADBALANCE_OVERALL_LEN = 8  # overall length of LB SDOption (to be used from UT)
    IP4_ENDPOINT_TYPE = 0x04
    IP4_ENDPOINT_LEN = 0x0009
    IP4_MCAST_TYPE = 0x14
    IP4_MCAST_LEN = 0x0009
    IP4_SDENDPOINT_TYPE = 0x24
    IP4_SDENDPOINT_LEN = 0x0009
    IP4_OVERALL_LEN = 12  # overall length of IP4 SDOption (to be used from UT)
    IP6_ENDPOINT_TYPE = 0x06
    IP6_ENDPOINT_LEN = 0x0015
    IP6_MCAST_TYPE = 0x16
    IP6_MCAST_LEN = 0x0015
    IP6_SDENDPOINT_TYPE = 0x26
    IP6_SDENDPOINT_LEN = 0x0015
    IP6_OVERALL_LEN = 24  # overall length of IP6 SDOption (to be used from UT)

    def guess_payload_class(self, payload):
        """decode SDOption depending on its type."""
        pl_type = struct.unpack(
            _SDOption.TYPE_FMT,
            payload[_SDOption.TYPE_PAYLOAD_I : _SDOption.TYPE_PAYLOAD_I + 1],
        )[0]

        if pl_type == _SDOption.CFG_TYPE:
            return SDOption_Config
        elif pl_type == self.LOADBALANCE_TYPE:
            return SDOption_LoadBalance
        elif pl_type == self.IP4_ENDPOINT_TYPE:
            return SDOption_IP4_EndPoint
        elif pl_type == self.IP4_MCAST_TYPE:
            return SDOption_IP4_Multicast
        elif pl_type == self.IP4_SDENDPOINT_TYPE:
            return SDOption_IP4_SD_EndPoint
        elif pl_type == self.IP6_ENDPOINT_TYPE:
            return SDOption_IP6_EndPoint
        elif pl_type == self.IP6_MCAST_TYPE:
            return SDOption_IP6_Multicast
        elif pl_type == self.IP6_SDENDPOINT_TYPE:
            return SDOption_IP6_SD_EndPoint


class _SDOption_Header(_SDOption):
    fields_desc = [
        ShortField("len", None),
        ByteField("type", 0),
        ByteField("res_hdr", 0),
    ]


class _SDOption_Tail(_SDOption):
    fields_desc = [
        ByteField("res_tail", 0),
        ByteEnumField("l4_proto", 0x06, {0x06: "TCP", 0x11: "UDP"}),
        ShortField("port", 0),
    ]


class _SDOption_IP4(_SDOption):
    fields_desc = [_SDOption_Header, IPField("addr", "0.0.0.0"), _SDOption_Tail]


class _SDOption_IP6(_SDOption):
    fields_desc = [
        _SDOption_Header,
        IP6Field("addr", "2001:cdba:0000:0000:0000:0000:3257:9652"),
        _SDOption_Tail,
    ]


class SDOption_Config(_SDOption):
    # offset to be added upon length calculation (corresponding to header's "Reserved" field)
    LEN_OFFSET = 0x01

    name = "Config Option"
    # default values specification
    _defaults = {"type": _SDOption.CFG_TYPE}
    # package fields definiton
    fields_desc = [_SDOption_Header, StrField("cfg_str", "")]

    def post_build(self, p, pay):
        # length computation excluding 16b_length and 8b_type
        l = self.len
        if l is None:
            l = len(self.cfg_str) + self.LEN_OFFSET
            p = struct.pack("!H", l) + p[2:]
        return p + pay


class SDOption_LoadBalance(_SDOption):
    name = "LoadBalance Option"
    # default values specification
    _defaults = {"type": _SDOption.LOADBALANCE_TYPE, "len": _SDOption.LOADBALANCE_LEN}
    # package fields definiton
    fields_desc = [_SDOption_Header, ShortField("priority", 0), ShortField("weight", 0)]


# SDOPTIONS : IPv4-specific
class SDOption_IP4_EndPoint(_SDOption_IP4):
    name = "IP4 EndPoint Option"
    # default values specification
    _defaults = {"type": _SDOption.IP4_ENDPOINT_TYPE, "len": _SDOption.IP4_ENDPOINT_LEN}


class SDOption_IP4_Multicast(_SDOption_IP4):
    name = "IP4 Multicast Option"
    # default values specification
    _defaults = {"type": _SDOption.IP4_MCAST_TYPE, "len": _SDOption.IP4_MCAST_LEN}


class SDOption_IP4_SD_EndPoint(_SDOption_IP4):
    name = "IP4 SDEndPoint Option"
    # default values specification
    _defaults = {
        "type": _SDOption.IP4_SDENDPOINT_TYPE,
        "len": _SDOption.IP4_SDENDPOINT_LEN,
    }


# SDOPTIONS : IPv6-specific
class SDOption_IP6_EndPoint(_SDOption_IP6):
    name = "IP6 EndPoint Option"
    # default values specification
    _defaults = {"type": _SDOption.IP6_ENDPOINT_TYPE, "len": _SDOption.IP6_ENDPOINT_LEN}


class SDOption_IP6_Multicast(_SDOption_IP6):
    name = "IP6 Multicast Option"
    # default values specification
    _defaults = {"type": _SDOption.IP6_MCAST_TYPE, "len": _SDOption.IP6_MCAST_LEN}


class SDOption_IP6_SD_EndPoint(_SDOption_IP6):
    name = "IP6 SDEndPoint Option"
    # default values specification
    _defaults = {
        "type": _SDOption.IP6_SDENDPOINT_TYPE,
        "len": _SDOption.IP6_SDENDPOINT_LEN,
    }


class SOMEIP_SD(_SDPacketBase):
    """
    SOME/IP-SD Packet

    NOTE :   when adding 'entries' or 'options', do not use list.append() method but create a new list
    e.g. :  p = SOMEIP_SD()
            p.option_array = [SDOption_Config(),SDOption_IP6_EndPoint()]
    """

    SOMEIP_MSGID_SRVID = 0xFFFF
    SOMEIP_MSGID_SUBID = 0x1
    SOMEIP_MSGID_EVENTID = 0x8100
    SOMEIP_PROTO_VER = 0x01
    SOMEIP_IFACE_VER = 0x01
    SOMEIP_MSG_TYPE = SOMEIPMessageType.NOTIFICATION

    name = "SOME/IP-SD"
    # Flags definition: {"name":(mask,offset)}
    _sdFlag = collections.namedtuple("Flag", "mask offset")
    FLAGSDEF = {
        "REBOOT": _sdFlag(mask=0x80, offset=7),  # ReBoot flag
        "UNICAST": _sdFlag(mask=0x40, offset=6),  # UniCast flag
    }

    fields_desc = [
        ByteField("flags", 0),
        X3BytesField("res", 0),
        FieldLenField(
            name="len_entry_array", default=None, length_of="entry_array", fmt="!I"
        ),
        PacketListField(
            name="entry_array",
            default=None,
            pkt_cls=_SDEntry,
            length_from=lambda pkt: pkt.len_entry_array,
        ),
        FieldLenField(
            name="len_option_array", default=None, length_of="option_array", fmt="!I"
        ),
        PacketListField(
            name="option_array",
            default=None,
            pkt_cls=_SDOption,
            length_from=lambda pkt: pkt.len_option_array,
        ),
    ]

    def __init__(self, *args, **kwargs):
        super(SOMEIP_SD, self).__init__(*args, **kwargs)
        self.explicit = 1

    def getFlag(self, name):
        """get particular flag from bitfield."""
        name = name.upper()
        if name in self.FLAGSDEF:
            return (self.flags & self.FLAGSDEF[name].mask) >> self.FLAGSDEF[name].offset
        else:
            return None

    def setFlag(self, name, value):
        """
        Set particular flag on bitfield.
         :param str name : name of the flag to set (see SD.FLAGSDEF)
         :param int value : either 0x1 or 0x0 (provided int will be ANDed with 0x01)
        """
        name = name.upper()
        if name in self.FLAGSDEF:
            self.flags = (
                self.flags & ctypes.c_ubyte(~self.FLAGSDEF[name].mask).value
            ) | (value & 0x01) << self.FLAGSDEF[name].offset

    def setEntryArray(self, entry_list):
        """
        Add entries to entry_array.
        :param entry_list: list of entries to be added. Single entry object also accepted
        """
        if isinstance(entry_list, list):
            self.entry_array = entry_list
        else:
            self.entry_array = [entry_list]

    def setOptionArray(self, option_list):
        """
        Add options to option_array.
        :param option_list: list of options to be added. Single option object also accepted
        """
        if isinstance(option_list, list):
            self.option_array = option_list
        else:
            self.option_array = [option_list]

    def getSomeip(self, stacked=False):
        """
        return SD-initialized SOME/IP packet
        :param stacked: boolean. Either just SOME/IP packet or stacked over SD-self
        """
        p = SOMEIP()
        p.message_id.service_id = SOMEIP_SD.SOMEIP_MSGID_SRVID
        p.message_id.sub_id = SOMEIP_SD.SOMEIP_MSGID_SUBID
        p.message_id.event_id = SOMEIP_SD.SOMEIP_MSGID_EVENTID
        p.protocol_version = SOMEIP_SD.SOMEIP_PROTO_VER
        p.interface_version = SOMEIP_SD.SOMEIP_IFACE_VER
        p.message_type = SOMEIP_SD.SOMEIP_MSG_TYPE

        if stacked:
            return p / self
        else:
            return p


# ========================
# Heuristic Dissector
# ========================
class CustomUDP(UDP):
    def guess_payload_class(self, payload):
        if is_valid_someip(payload):
            return SOMEIP
        return super().guess_payload_class(payload)


class CustomTCP(TCP):
    def guess_payload_class(self, payload):
        if is_valid_someip(payload):
            return SOMEIP
        return super().guess_payload_class(payload)


def is_valid_someip(payload) -> bool:
    if len(payload) < 16:
        return False

    length = struct.unpack(">I", payload[4:8])[0]
    proto_ver = payload[12]
    msg_type = payload[14]
    return (
        length >= 8
        and proto_ver <= 1
        and (msg_type in SOMEIP_MSGS_TYPES or msg_type in SOMEIP_TP_TYPES)
    )


# UDP.guess_payload_class = CustomUDP.guess_payload_class
# TCP.guess_payload_class = CustomTCP.guess_payload_class
