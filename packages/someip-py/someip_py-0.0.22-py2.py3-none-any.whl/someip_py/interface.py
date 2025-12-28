# -*- coding: utf-8 -*-
import atexit
import csv
import importlib
import json
import os
import threading
import time
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from logging import getLogger
from typing import Any, Callable, List, Optional, Tuple

import pandas as pd
from google.protobuf.json_format import MessageToDict, ParseDict
from jinja2 import BaseLoader, Environment
from scapy.all import rdpcap
from scapy.layers.inet import IP, TCP, UDP
from scapy.packet import Raw

from .client import SOMEIPClient
from .codec import SomeIpPayload
from .constants import MULTICAST_ADDRESS, MULTICAST_PORT, SOMEIPMessageType
from .frame import SOMEIPFrame
from .scapy_extention import SOMEIP, SOMEIP_SD, CustomTCP, CustomUDP
from .server import SOMEIPServer
from .utils import convert_proto, import_class

logger = getLogger(name="someip.interface")

base_dir = os.path.dirname(__file__)


class PlatformNotFoundError(Exception):
    pass


class ServiceNotFoundError(Exception):
    pass


class MethodNotFoundError(Exception):
    pass


class InterfaceNotFoundError(Exception):
    pass


class NoNotificationFoundError(Exception):
    pass


class SOMEIPService:
    class Platform:
        P_2X = "p_2x"
        P_30T = "p_30t"
        P_L946 = "p_l946"
        P_Smart = "p_smart"

    def __init__(
        self,
        platform: Platform = Platform.P_2X,
        proto_path: Optional[str] = None,
        arxml_path: Optional[str] = None,
        config_file: Optional[str] = None,
    ):
        self.platform = platform
        self.proto_path = proto_path
        self.config_file = config_file
        if self.proto_path:
            convert_proto(self.proto_path)

        if arxml_path:
            self._generate_services(arxml_path)

        self.origin, self.services = self._init_services()

    def _init_services(self) -> Tuple[dict, dict]:
        origin = {}
        services = {}
        config_file = self.config_file or os.path.join(
            base_dir, "service_interface", "config.json"
        )
        if not os.path.exists(config_file):
            return origin, services

        with open(config_file, "r") as fp:
            cfg = json.load(fp)

        if not self.config_file and not cfg.get(self.platform):
            raise PlatformNotFoundError("you must provide available platform")

        origin = cfg[self.platform] if not self.config_file else cfg
        for k, v in origin.items():
            services[v["service_id"]] = {}
            for ik, iv in v["interface"].items():
                try:
                    if not services[v["service_id"]].get(iv["method_id"]):
                        services[v["service_id"]][iv["method_id"]] = {}

                    if iv.get("getter_id") and not services[v["service_id"]].get(
                        iv["getter_id"]
                    ):
                        services[v["service_id"]][iv["getter_id"]] = {}

                    if iv.get("setter_id") and not services[v["service_id"]].get(
                        iv["setter_id"]
                    ):
                        services[v["service_id"]][iv["setter_id"]] = {}

                    if iv["structures"].get("request"):
                        services[v["service_id"]][iv["method_id"]][
                            SOMEIPMessageType.REQUEST
                        ] = import_class(
                            f"someip_py.service_interface.{self.platform}.{k}.{ik}:{iv['structures']['request']}"
                        )
                        if iv.get("getter_id"):
                            services[v["service_id"]][iv["getter_id"]][
                                SOMEIPMessageType.REQUEST
                            ] = import_class(
                                f"someip_py.service_interface.{self.platform}.{k}.{ik}:{iv['structures']['request']}"
                            )
                        if iv.get("setter_id"):
                            services[v["service_id"]][iv["setter_id"]][
                                SOMEIPMessageType.REQUEST
                            ] = import_class(
                                f"someip_py.service_interface.{self.platform}.{k}.{ik}:{iv['structures']['request']}"
                            )

                    if iv["structures"].get("response"):
                        services[v["service_id"]][iv["method_id"]][
                            SOMEIPMessageType.RESPONSE
                        ] = import_class(
                            f"someip_py.service_interface.{self.platform}.{k}.{ik}:{iv['structures']['response']}"
                        )
                        if iv.get("getter_id"):
                            services[v["service_id"]][iv["getter_id"]][
                                SOMEIPMessageType.RESPONSE
                            ] = import_class(
                                f"someip_py.service_interface.{self.platform}.{k}.{ik}:{iv['structures']['response']}"
                            )
                        if iv.get("setter_id"):
                            services[v["service_id"]][iv["setter_id"]][
                                SOMEIPMessageType.RESPONSE
                            ] = import_class(
                                f"someip_py.service_interface.{self.platform}.{k}.{ik}:{iv['structures']['response']}"
                            )

                    if iv["structures"].get("notification"):
                        services[v["service_id"]][iv["method_id"]][
                            SOMEIPMessageType.NOTIFICATION
                        ] = import_class(
                            f"someip_py.service_interface.{self.platform}.{k}.{ik}:{iv['structures']['notification']}"
                        )

                    services[v["service_id"]][iv["method_id"]][
                        "pb"
                    ] = importlib.import_module(
                        f"someip_py.service_interface.pb.Adcu.{k}_pb2"
                    )
                    if iv.get("getter_id"):
                        services[v["service_id"]][iv["getter_id"]][
                            "pb"
                        ] = importlib.import_module(
                            f"someip_py.service_interface.pb.Adcu.{k}_pb2"
                        )
                    if iv.get("setter_id"):
                        services[v["service_id"]][iv["setter_id"]][
                            "pb"
                        ] = importlib.import_module(
                            f"someip_py.service_interface.pb.Adcu.{k}_pb2"
                        )
                except ModuleNotFoundError as e:
                    logger.debug(e)

        return origin, services

    @classmethod
    def inject_config(cls, platform, config):
        config_file = os.path.join(base_dir, "service_interface", "config.json")
        with open(config_file, "r") as fp:
            cfg = json.load(fp)

        if not cfg.get(platform):
            raise TypeError(f"can not found platform {platform}")

        with open(config, "r") as nfp:
            new_cfg = json.load(nfp)

        cfg[platform].update(new_cfg)
        with open(config_file, "w") as f:
            json.dump(cfg, f, indent=4)

    def _generate_services(self, arxml_path: str, output: Optional[str] = None):
        # TODO
        # read from provide .xlsx and generate service code under service_interface folder
        # === Jinja2 Template ===
        template = """
class {{ name }}(SomeIpPayload):
    {% if has_dynamic_size %}_has_dynamic_size = True{% endif %}
    {% if include_struct_len %}_include_struct_len = True{% endif %}
    {% for field in fields %}
    {{ field.name }}: {{ field.type }}
    {% endfor %}

    def __init__(self):
        {% for field in fields %}
        self.{{ field.name }} = {{ field.init }}
        {% endfor %}
"""
        env = Environment(loader=BaseLoader())
        class_template = env.from_string(template)
        # === Type Mappings ===
        primitive_map = {
            "uint8": "Uint8",
            "uint8_t": "Uint8",
            "uint16": "Uint16",
            "uint32": "Uint32",
            "uint64": "Uint64",
            "int8": "Int8",
            "int16": "Int16",
            "int32": "Int32",
            "int64": "Int64",
            "bool": "Bool",
            "float": "Float32",
            "double": "Float64",
            "DynamicArray": "SomeIpDynamicSizeArray",
            "FixedArray": "SomeIpFixedSizeArray",
            "string": "SomeIpDynamicSizeString",
            "String": "SomeIpDynamicSizeString",
        }

        # === Alias resolution for type reference ===
        type_aliases = {}
        # === Type structure ===
        type_tree = defaultdict(list)

        generated = {}

        # Resolve deep aliases
        def resolve_primitive(base_type):
            while base_type in type_aliases:
                base_type = type_aliases[base_type]
            return primitive_map.get(base_type, base_type)

        def generate_class(name, rename=None, first_kls=False):
            class_name = rename or name
            fields = []
            has_dynamic_array = False
            include_struct_len = self.platform in (
                SOMEIPService.Platform.P_30T,
                SOMEIPService.Platform.P_L946,
            )
            is_primitive_only = True

            if name not in type_tree:
                return fields, has_dynamic_array

            for entry in type_tree[name]:
                idt_type = entry["idt_type"]
                field_name = entry["part_name"]
                ref_type = entry["ref_type"]
                base_type = entry["base_type"]
                array_size = entry["array_size"]

                if idt_type == "Struct":
                    is_primitive_only = False
                    sub_fields, dynamic_array = generate_class(ref_type)
                    if dynamic_array:
                        has_dynamic_array = True
                    if sub_fields:
                        sub_fields[0]["name"] = field_name
                        fields.extend(sub_fields)
                    else:
                        fields.append(
                            {
                                "name": field_name,
                                "type": ref_type,
                                "init": f"{ref_type}()",
                            }
                        )

                elif idt_type == "type reference":
                    py_type = resolve_primitive(base_type)
                    fields.append(
                        {"name": name, "type": py_type, "init": f"{py_type}()"}
                    )

                elif idt_type == "FixedArray":
                    elem_type = resolve_primitive(ref_type)
                    if ref_type not in primitive_map and ref_type not in type_aliases:
                        generate_class(ref_type)
                        is_primitive_only = True

                    init = f"SomeIpFixedSizeArray({elem_type}, size={int(array_size)})"
                    if self.platform == SOMEIPService.Platform.P_30T:
                        init = f"SomeIpFixedSizeArray({elem_type}, size={int(array_size)}, include_array_len=True)"

                    fields.append(
                        {
                            "name": field_name if field_name != "/" else class_name,
                            "type": f"SomeIpFixedSizeArray[{elem_type}]",
                            "init": init,
                        }
                    )

                elif idt_type == "DynamicArray":
                    has_dynamic_array = True
                    elem_type = resolve_primitive(ref_type)
                    if ref_type not in primitive_map and ref_type not in type_aliases:
                        generate_class(ref_type)
                        is_primitive_only = True
                    fields.append(
                        {
                            "name": field_name if field_name != "/" else class_name,
                            "type": f"SomeIpDynamicSizeArray[{elem_type}]",
                            "init": f"SomeIpDynamicSizeArray({elem_type})",
                        }
                    )
                elif idt_type == "string":
                    py_type = resolve_primitive(idt_type)
                    fields.append(
                        {"name": name, "type": py_type, "init": f"{py_type}()"}
                    )

            # Don't generate class for purely primitive type references
            if is_primitive_only and not rename:
                return fields, has_dynamic_array

            if first_kls:
                has_dynamic_array = False
                include_struct_len = False

            code = class_template.render(
                name=class_name,
                fields=fields,
                has_dynamic_size=has_dynamic_array,
                include_struct_len=include_struct_len,
            )
            generated[class_name] = code
            return [], has_dynamic_array

        def parse_xlsx(path, cfg):
            type_aliases.clear()
            type_tree.clear()
            all_sheet = pd.read_excel(path, header=0, sheet_name=None)
            service_df = all_sheet["ServiceInfo"]
            instance_df = all_sheet["ServiceInstanceDefinition"]
            interfaces_df = all_sheet["ServiceInterfaceDesign"]

            for _, row in service_df.iterrows():
                service_name = row["Service Name"]
                service_id = row.get("Service ID（0x）") or row.get("Service ID（Dec）")
                major_version = row.get("Major Version") or row.get(
                    "Major Version（Dec）"
                )
                minor_version = row.get("Minor Version") or row.get(
                    "Minor Version（Dec）"
                )
                if minor_version is None:
                    minor_version = 0

                if not isinstance(service_id, str):
                    service_id = f"0x{service_id:04x}"

            for _, row in instance_df.iterrows():
                instance_id = row.get("Instance ID （0x）") or row["Instance ID （Dec）"]

            cfg[service_name] = {
                "service_id": service_id,
                "instance_id": instance_id,
                "major_version": major_version,
                "minor_version": minor_version,
                "tcp_port": cfg.get(service_name, {}).get("tcp_port"),
                "udp_port": cfg.get(service_name, {}).get("udp_port"),
                "interface": {},
            }

            types_df = all_sheet["Parameter"]
            for _, row in types_df.iterrows():
                field = row["IDT Name"]
                type_tree[field].append(
                    {
                        "idt_type": row["IDT Type"],
                        "base_type": row["Base Type"],
                        "part_name": row["Sub Element Name （Part Name）"],
                        "ref_type": row["Sub Element Ref Type"],
                        "array_size": row["Array Size (if necessary)"],
                    }
                )
                if row["IDT Type"] == "type reference":
                    base_type = row["Base Type"]
                    if base_type in primitive_map:
                        type_aliases[field] = primitive_map[base_type]
                    elif base_type in type_aliases:
                        type_aliases[field] = type_aliases[base_type]
                    else:
                        type_aliases[field] = base_type

            # === Process interfaces ===
            latest_file = None
            for _, row in interfaces_df.iterrows():
                generated.clear()
                top_struct = row["IDT Name"]
                if not isinstance(top_struct, str):
                    continue

                if top_struct not in type_tree:
                    continue

                interface_name = row["Interface Name"]
                interface_type = row["Interface Type"].lower()
                interface_protocol = row["Protocol"].lower()

                eventgroup_id = (
                    row.get("Event Group ID") or row.get("Event Group ID （Dec）")
                    if interface_type != "method"
                    else None
                )
                if eventgroup_id == "/":
                    eventgroup_id = None
                if (
                    eventgroup_id
                    and not isinstance(eventgroup_id, int)
                    and not isinstance(eventgroup_id, float)
                ):
                    if eventgroup_id.startswith("0x"):
                        eventgroup_id = int(eventgroup_id, base=16)
                    else:
                        eventgroup_id = int(eventgroup_id)

                if interface_type == "method":
                    method_id = row.get("Method ID/Event ID") or row.get(
                        "Method ID （Dec）"
                    )
                elif interface_type == "event":
                    method_id = row.get("Method ID/Event ID") or row.get(
                        "Event ID （Dec）"
                    )
                elif interface_type == "field":
                    method_id = row.get("Notifier ID") or row.get("Notifier ID （Dec）")

                if pd.isna(method_id):
                    method_id = (
                        cfg[service_name]["interface"]
                        .get(interface_name, {})
                        .get("method_id", 0)
                    )

                if isinstance(method_id, float) or (
                    isinstance(method_id, str)
                    and not method_id.startswith("0x")
                    and method_id != "/"
                ):
                    method_id = int(method_id)

                if isinstance(method_id, str) and method_id.startswith("0x"):
                    if eventgroup_id:
                        method_id = int(method_id, base=16) | 0x8000
                    else:
                        method_id = int(method_id, base=16)
                    method_id = f"0x{method_id:04x}"
                elif isinstance(method_id, int):
                    if eventgroup_id:
                        method_id |= 0x8000
                    method_id = f"0x{method_id:04x}"

                cfg[service_name]["interface"][interface_name] = {
                    "type": interface_type,
                    "protocol": interface_protocol,
                    "method_id": method_id,
                    "structures": cfg[service_name]["interface"]
                    .get(interface_name, {})
                    .get("structures", {}),
                }

                if eventgroup_id:
                    cfg[service_name]["interface"][interface_name][
                        "eventgroup_id"
                    ] = eventgroup_id
                    cfg[service_name]["interface"][interface_name]["structures"][
                        "notification"
                    ] = top_struct

                if interface_type == "method":
                    if not cfg[service_name]["interface"][interface_name][
                        "structures"
                    ].get("request"):
                        cfg[service_name]["interface"][interface_name]["structures"][
                            "request"
                        ] = top_struct
                    else:
                        if (
                            cfg[service_name]["interface"][interface_name][
                                "structures"
                            ]["request"]
                            != top_struct
                        ):
                            cfg[service_name]["interface"][interface_name][
                                "structures"
                            ]["response"] = top_struct
                elif interface_type == "event":
                    cfg[service_name]["interface"][interface_name]["structures"][
                        "notification"
                    ] = top_struct
                elif interface_type == "field":
                    getter_id = row.get("Getter ID") or row.get("Getter ID （Dec）")
                    setter_id = row.get("Setter ID") or row.get("Setter ID （Dec）")
                    if isinstance(getter_id, int):
                        getter_id = f"0x{int(getter_id):04x}"

                    if getter_id and getter_id != "/":
                        if not getter_id.startswith("0x"):
                            getter_id = f"0x{int(getter_id):04x}"
                        else:
                            getter_id = f"0x{int(getter_id, base=16):04x}"
                        cfg[service_name]["interface"][interface_name][
                            "getter_id"
                        ] = getter_id

                    if isinstance(setter_id, int):
                        setter_id = f"0x{int(setter_id):04x}"

                    if setter_id and setter_id != "/":
                        if not setter_id.startswith("0x"):
                            setter_id = f"0x{int(setter_id):04x}"
                        else:
                            setter_id = f"0x{int(setter_id, base=16):04x}"
                        cfg[service_name]["interface"][interface_name][
                            "setter_id"
                        ] = setter_id

                    cfg[service_name]["interface"][interface_name]["structures"][
                        "request"
                    ] = top_struct
                    cfg[service_name]["interface"][interface_name]["structures"][
                        "response"
                    ] = top_struct

                parts = type_tree[top_struct]
                if parts[0]["idt_type"] == "Struct":
                    kls_name = top_struct + "Kls"
                    generate_class(top_struct, rename=kls_name)
                    generated[top_struct] = class_template.render(
                        name=top_struct,
                        fields=[
                            {
                                "name": top_struct,
                                "type": kls_name,
                                "init": f"{kls_name}()",
                            }
                        ],
                        has_dynamic_size=False,
                        include_struct_len=False,
                    )
                else:
                    generate_class(top_struct, rename=top_struct, first_kls=True)

                # === Output code ===
                output_dir = os.path.join(
                    base_dir, "service_interface", self.platform, service_name
                )
                if output:
                    output_dir = os.path.join(output, service_name)

                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                output_file = os.path.join(output_dir, f"{interface_name}.py")
                if latest_file == output_file:
                    with open(output_file, "a") as f:
                        for code in generated.values():
                            f.write(code.strip() + "\n\n\n")
                else:
                    with open(output_file, "w") as f:
                        f.write("from someip_py.codec import *")
                        f.write("\n\n\n")
                        for code in generated.values():
                            f.write(code.strip() + "\n\n\n")
                latest_file = output_file

        config_file = os.path.join(base_dir, "service_interface", "config.json")
        if not os.path.exists(config_file):
            with open(config_file, "w") as f:
                json.dump({self.platform: {}}, f, indent=4)

        with open(config_file, "r") as fp:
            cfg: dict = json.load(fp)
            if not cfg.get(self.platform):
                cfg[self.platform] = {}

        if os.path.isfile(arxml_path):
            parse_xlsx(arxml_path, cfg[self.platform])
        elif os.path.isdir(arxml_path):
            for path in os.listdir(arxml_path):
                parse_xlsx(os.path.join(arxml_path, path), cfg[self.platform])

        if not output:
            with open(config_file, "w") as fp:
                json.dump(cfg, fp, indent=4)
        else:
            output_config_file = os.path.join(output, "config.json")
            with open(output_config_file, "w") as fp:
                json.dump(cfg[self.platform], fp, indent=4)

    def generate_services(self, arxml_path: str, output: Optional[str] = None):
        """generate SOME/IP service python module based on xlsx or arxml file

        Args:
            arxml_path (str): The arxml or xlsx path, can be a file path or directory path.
            output (Optional[str]): The output directory of generated python file in.
        """
        self._generate_services(arxml_path, output=output)

    def parse_pcap(
        self,
        pcap_file: str,
        output: Optional[str] = None,
        filters: Optional[dict] = None,
    ):
        """parse .pcap/.pcapng file.

        Args:
            pcap_file (str): The arxml or xlsx path, can be a file path or directory path.
            output (Optional[str]): The output directory of parsed .txt or .csv file.
        """
        UDP.guess_payload_class = CustomUDP.guess_payload_class
        TCP.guess_payload_class = CustomTCP.guess_payload_class
        packets = rdpcap(pcap_file)
        recorder = print
        if not output:
            recorder(
                f"{'No.':<5} {'Time':<28} {'Source':<21} {'Destination':<21} {'Protocol':<10} {'Len':<5} Info"
            )
            recorder("-" * 100)
        else:
            f = open(output, "w", newline="")
            atexit.register(f.close)
            if output.endswith(".txt"):
                recorder = f.write
                recorder(
                    f"{'No.':<5} {'Time':<28} {'Source':<21} {'Destination':<21} {'Protocol':<10} {'Len':<5} Info\n"
                )
            elif output.endswith(".csv"):
                writer = csv.writer(f)
                recorder = writer.writerow
                recorder(
                    ["No.", "Time", "Source", "Destination", "Protocol", "Len", "Info"]
                )
            else:
                raise TypeError("The output type only support .txt or .csv")

        for i, pkt in enumerate(packets, 1):
            # Timestamp in ISO format
            time = datetime.fromtimestamp(float(pkt.time)).isoformat()

            # Defaults
            src = dst = sport = dport = proto = info = "-"
            length = len(pkt)

            if IP in pkt:
                ip = pkt[IP]
                src = ip.src
                dst = ip.dst
                proto = ip.proto
                if TCP in pkt:
                    tcp = pkt[TCP]
                    sport = tcp.sport
                    dport = tcp.dport
                    src = f"{src}:{sport}"
                    dst = f"{dst}:{dport}"
                    proto = "TCP"
                    info = f"{sport} → {dport} [Flags: {tcp.flags}]"
                elif UDP in pkt:
                    udp = pkt[UDP]
                    sport = udp.sport
                    dport = udp.dport
                    src = f"{src}:{sport}"
                    dst = f"{dst}:{dport}"
                    proto = "UDP"
                    info = f"{sport} → {dport} [UDP]"
                else:
                    proto = "IP"
                    info = f"{src} → {dst} [IP]"

                if pkt.haslayer(SOMEIP):
                    proto = "SOME/IP"
                    service_id = f"0x{pkt[SOMEIP].message_id.service_id:04x}"
                    sub_id = pkt[SOMEIP].message_id.sub_id
                    method_id = (
                        f"0x{pkt[SOMEIP].message_id.method_id:04x}"
                        if sub_id == 0
                        else f"0x{pkt[SOMEIP].message_id.event_id|0x8000:04x}"
                    )
                    if filters:
                        if (
                            filters.get("service_id")
                            and filters["service_id"] != service_id
                        ):
                            continue
                        if (
                            filters.get("method_id")
                            and filters["method_id"] != method_id
                        ):
                            continue

                    info = (
                        f"service_id: {service_id}, method_id: {method_id}, "
                        f"msg_type: {pkt[SOMEIP].get_field('message_type').i2s[pkt[SOMEIP].message_type]}"
                    )
                    if (
                        self.services.get(service_id)
                        and self.services[service_id].get(method_id)
                        and self.services[service_id][method_id].get(
                            pkt[SOMEIP].message_type
                        )
                    ):
                        try:
                            msg = self.decode_payload(
                                service_id,
                                method_id,
                                message_type=pkt[SOMEIP].message_type,
                                payload=pkt[Raw].load,
                            )
                            s = json.dumps(msg)
                            info += f", structures: {s}"
                        except Exception as e:
                            info += f", decoder error: {e}"
                            logger.debug(e)

                if pkt.haslayer(SOMEIP_SD):
                    proto = "SOME/IP-SD"
            elif pkt.name == "Ethernet":
                proto = pkt.payload.name

            line = (
                f"{i:<5} {time:<28} {src:<21} {dst:<21} {proto:<10} {length:<5} {info}"
            )
            if output and output.endswith(".csv"):
                line = [i, time, src, dst, proto, length, info]
            elif output and output.endswith(".txt"):
                line = line + "\n"
            recorder(line)

    def _get_interface(
        self,
        service_id: Any,
        method_id: Any,
        message_type: SOMEIPMessageType = SOMEIPMessageType.NOTIFICATION,
    ) -> dict:
        if isinstance(service_id, int):
            service_id = f"0x{service_id:04x}"

        if isinstance(method_id, int):
            if message_type == SOMEIPMessageType.NOTIFICATION:
                method_id |= 0x8000
            method_id = f"0x{method_id:04x}"
        else:
            if message_type == SOMEIPMessageType.NOTIFICATION:
                method_id = int(method_id, base=16) | 0x8000
                method_id = f"0x{method_id:04x}"

        if not self.services.get(service_id):
            raise ServiceNotFoundError(
                f"service {service_id} not found, available services: {self.services.keys()}"
            )

        if not self.services[service_id].get(method_id):
            raise MethodNotFoundError(
                f"method {method_id} not found in service {service_id}, "
                f"availalbe methods {self.services[service_id].keys()}"
            )
        return self.services[service_id][method_id]

    def view(
        self,
        service_id: Any,
        method_id: Any,
        message_type: SOMEIPMessageType = SOMEIPMessageType.NOTIFICATION,
    ) -> SomeIpPayload:
        interface = self._get_interface(
            service_id, method_id, message_type=message_type
        )
        if not interface.get(message_type):
            raise InterfaceNotFoundError(
                f"The messagetype not found for interface {interface}"
            )
        obj = interface[message_type]()
        logger.debug(f"some/ip service {service_id}-{method_id}'s structures is {obj}")
        return obj

    def _get_pb_attr(
        self,
        service_id: Any,
        method_id: Any,
        message_type: SOMEIPMessageType,
        field_id: int,
    ):
        interface = self._get_interface(
            service_id, method_id, message_type=message_type
        )
        if interface.get("pb"):
            msg_enum = getattr(
                interface["pb"],
                "MessageId",
            )
            msg_name = msg_enum.DESCRIPTOR.values_by_number[field_id].name.replace(
                "MsgId", ""
            )
            attr = getattr(interface["pb"], msg_name)()
            attr.ParseFromString(b"")
            logger.debug(
                f"some/ip service {service_id}-{method_id}'s protobuf structures is"
                f" {MessageToDict(attr, including_default_value_fields=True)}"
            )
            return attr

    def _get_pb_version(
        self,
        service_id: Any,
        method_id: Any,
        message_type: SOMEIPMessageType,
    ):
        interface = self._get_interface(
            service_id, method_id, message_type=message_type
        )
        if interface.get("pb"):
            version_enum = getattr(
                interface["pb"],
                "Version",
            )
            major_version = version_enum.DESCRIPTOR.values_by_name[
                "MAJOR_VERSION"
            ].number
            minor_version = version_enum.DESCRIPTOR.values_by_name[
                "MINOR_VERSION"
            ].number
            return major_version << 4 | minor_version

    def encode_pb(
        self,
        service_id: Any,
        method_id: Any,
        message_type: SOMEIPMessageType,
        field_id: int,
        structures: Optional[dict] = None,
    ) -> List:
        """encode protobuf structures"""
        attr = self._get_pb_attr(service_id, method_id, message_type, field_id)
        if attr:
            ParseDict(structures, attr)
            return list(attr.SerializeToString())
        return []

    def decode_payload(
        self,
        service_id: Any,
        method_id: Any,
        message_type: SOMEIPMessageType = SOMEIPMessageType.NOTIFICATION,
        payload: bytes = b"",
    ) -> dict:
        """decode SOME/IP structures.

        Args:
            service_id (int): The service id of SOME/IP service.
            method_id (int]): The method id of SOME/IP service.
            message_type: (SOMEIPMessageType): The message type of SOME/IP service.
            payload (bytes): The payload of SOME/IP service.

        Returns:
            dict: SOME/IP structures.
        """
        interface = self._get_interface(service_id, method_id, message_type)
        if not interface.get(message_type):
            raise InterfaceNotFoundError(
                f"The messagetype not found for interface {interface}"
            )

        if isinstance(payload, str):
            payload = bytes.fromhex(payload)

        s = interface[message_type]().deserialize(payload)
        if interface.get("pb"):
            msg: dict = s.messagetoDict()
            pb = list(msg.values())[0]
            if isinstance(pb, dict) and pb.get("ProtoHeader"):
                field_id = pb["ProtoHeader"]["FieldId"]
                msg_enum = getattr(
                    interface["pb"],
                    "MessageId",
                )
                msg_name = msg_enum.DESCRIPTOR.values_by_number[field_id].name.replace(
                    "MsgId", ""
                )
                attr = getattr(interface["pb"], msg_name)()
                attr.ParseFromString(bytes(pb["ProtoPayload"]))
                msg["pbData"] = MessageToDict(attr, including_default_value_fields=True)
                return msg
        return s.messagetoDict()

    def encode_payload(
        self,
        service_id: Any,
        method_id: Any,
        message_type: SOMEIPMessageType = SOMEIPMessageType.NOTIFICATION,
        structures: Optional[dict] = None,
    ) -> bytes:
        """encode SOME/IP structures.

        Args:
            service_id (int): The service id of SOME/IP service.
            method_id (int]): The method id of SOME/IP service.
            message_type: (SOMEIPMessageType): The message type of SOME/IP service.
            structures (Optional[dict]): The SOME/IP structures to be encoded.

        Returns:
            bytes: SOME/IP payload.
        """
        obj = self.view(service_id, method_id, message_type=message_type)
        if structures:
            if structures.get("FieldId") and structures.get("ProtoPayload") is not None:
                structures["ProtoPayload"] = self.encode_pb(
                    service_id,
                    method_id,
                    message_type,
                    structures["FieldId"],
                    structures=structures["ProtoPayload"],
                )
                structures["Length"] = len(structures["ProtoPayload"])
                if not structures.get("ProtoVertion"):
                    version = self._get_pb_version(service_id, method_id, message_type)
                    if version:
                        structures["ProtoVertion"] = version
            obj.setValues(structures)

        return obj.serialize()

    def as_client(
        self,
        service: str,
        interface: str,
        typ: str = "sub",
        remote_address: str = "198.99.36.3",
        remote_port: str = None,
        local_address: str = "",
        local_port: int = 0,
        mcast_address: str = MULTICAST_ADDRESS,
        mcast_port: int = MULTICAST_PORT,
        interface_version: Optional[int] = None,
        structures: Optional[dict] = None,
        ttl: int = 3,
        cb: Optional[Callable] = None,
        timeout: float = 3.0,
        loop_time: Optional[float] = None,
        interval: float = 0.01,
    ) -> SOMEIPFrame:
        """send SOME/IP message as a client"""
        if not self.origin.get(service):
            raise ServiceNotFoundError(
                f"service {service} not found, available services: {self.origin.keys()}"
            )

        if not self.origin[service]["interface"].get(interface):
            raise InterfaceNotFoundError(
                f"interface {interface} not found in service {service}, "
                f"availalbe interface {self.origin[service]['interface'].keys()}"
            )

        protocol = self.origin[service]["interface"][interface]["protocol"]
        transport_type = SOMEIPClient.TransportType.TCP
        remote_port = remote_port or self.origin[service]["tcp_port"]
        if protocol == "udp":
            transport_type = SOMEIPClient.TransportType.UDP
            remote_port = remote_port or self.origin[service]["udp_port"]

        iversion = interface_version or self.origin[service]["major_version"]

        if loop_time:

            def loop():
                with SOMEIPClient(
                    remote_address=remote_address,
                    remote_port=remote_port,
                    local_address=local_address,
                    local_port=local_port,
                    mcast_address=mcast_address,
                    mcast_port=mcast_port,
                    transport_type=transport_type,
                ) as client:
                    service_id = int(self.origin[service]["service_id"], base=16)
                    method_id = int(
                        self.origin[service]["interface"][interface]["method_id"],
                        base=16,
                    )
                    payload = self.encode_payload(
                        service_id,
                        method_id,
                        message_type=SOMEIPMessageType.REQUEST,
                        structures=structures,
                    )
                    curr = time.time()
                    while time.time() - curr < loop_time:
                        frame = client.rr_method(
                            service_id,
                            method_id,
                            interface_version=iversion,
                            payload=payload,
                        )
                        try:
                            frame.structures = self.decode_payload(
                                service_id,
                                method_id,
                                message_type=SOMEIPMessageType.RESPONSE,
                                payload=frame.payload,
                            )
                        except Exception as e:
                            logger.debug(e)

                        print(frame)
                        time.sleep(interval)

            l = threading.Thread(
                target=loop,
                name=f"request_{service}_{interface}",
            )
            l.daemon = True
            l.start()
            return

        with SOMEIPClient(
            remote_address=remote_address,
            remote_port=remote_port,
            local_address=local_address,
            local_port=local_port,
            mcast_address=mcast_address,
            mcast_port=mcast_port,
            transport_type=transport_type,
        ) as client:
            service_id = int(self.origin[service]["service_id"], base=16)
            method_id = int(
                self.origin[service]["interface"][interface]["method_id"], base=16
            )

            if self.origin[service]["interface"][interface]["type"] == "method":
                payload = self.encode_payload(
                    service_id,
                    method_id,
                    message_type=SOMEIPMessageType.REQUEST,
                    structures=structures,
                )
                frame = client.rr_method(
                    service_id,
                    method_id,
                    interface_version=iversion,
                    payload=payload,
                )
                try:
                    frame.structures = self.decode_payload(
                        service_id,
                        method_id,
                        message_type=SOMEIPMessageType.RESPONSE,
                        payload=frame.payload,
                    )
                except Exception as e:
                    logger.debug(e)

                return frame
            elif self.origin[service]["interface"][interface]["type"] == "event":
                frame = client.subscribe(
                    service_id,
                    method_id,
                    self.origin[service]["instance_id"],
                    self.origin[service]["interface"][interface]["eventgroup_id"],
                    major_version=self.origin[service]["major_version"],
                    ttl=ttl,
                    callback=cb,
                )
                if not frame:
                    raise NoNotificationFoundError(
                        "can not get notification after subscribe"
                    )

                if isinstance(frame, SOMEIPFrame):
                    try:
                        frame.structures = self.decode_payload(
                            service_id,
                            method_id,
                            message_type=SOMEIPMessageType.NOTIFICATION,
                            payload=frame.payload,
                        )
                    except Exception as e:
                        logger.debug(e)
                    return frame
                time.sleep(timeout)
            elif self.origin[service]["interface"][interface]["type"] == "field":
                if typ == "sub":
                    frame = client.subscribe(
                        service_id,
                        method_id,
                        self.origin[service]["instance_id"],
                        self.origin[service]["interface"][interface]["eventgroup_id"],
                        major_version=self.origin[service]["major_version"],
                        ttl=ttl,
                        callback=cb,
                    )
                    if not frame:
                        raise NoNotificationFoundError(
                            "can not get notification after subscribe"
                        )

                    if isinstance(frame, SOMEIPFrame):
                        try:
                            frame.structures = self.decode_payload(
                                service_id,
                                method_id,
                                message_type=SOMEIPMessageType.NOTIFICATION,
                                payload=frame.payload,
                            )
                        except Exception as e:
                            logger.debug(e)
                        return frame
                    time.sleep(timeout)
                elif typ == "getter":
                    method_id = int(
                        self.origin[service]["interface"][interface]["getter_id"],
                        base=16,
                    )
                    frame = client.rr_method(
                        service_id,
                        method_id,
                        interface_version=iversion,
                    )
                    try:
                        frame.structures = self.decode_payload(
                            service_id,
                            method_id,
                            message_type=SOMEIPMessageType.RESPONSE,
                            payload=frame.payload,
                        )
                    except Exception as e:
                        logger.debug(e)
                    return frame
                elif typ == "setter":
                    method_id = int(
                        self.origin[service]["interface"][interface]["setter_id"],
                        base=16,
                    )
                    payload = self.encode_payload(
                        service_id,
                        method_id,
                        message_type=SOMEIPMessageType.REQUEST,
                        structures=structures,
                    )
                    frame = client.rr_method(
                        service_id,
                        method_id,
                        interface_version=iversion,
                        payload=payload,
                    )
                    try:
                        frame.structures = self.decode_payload(
                            service_id,
                            method_id,
                            message_type=SOMEIPMessageType.RESPONSE,
                            payload=frame.payload,
                        )
                    except Exception as e:
                        logger.debug(e)
                    return frame

    def register_service(
        self,
        server: SOMEIPServer,
        service: str,
        interfaces: List[str],
        service_params: Optional[dict] = None,
    ):
        if not self.origin.get(service):
            raise ServiceNotFoundError(
                f"service {service} not found, available services: {self.origin.keys()}"
            )

        svc = {
            "service_id": self.origin[service]["service_id"],
            "instance_id": self.origin[service]["instance_id"],
            "major_version": self.origin[service]["major_version"],
            "minor_version": self.origin[service]["minor_version"],
            "tcp_port": self.origin[service]["tcp_port"],
            "udp_port": self.origin[service]["udp_port"],
            "interface": [],
        }

        for interface in interfaces:
            if not self.origin[service]["interface"].get(interface):
                raise InterfaceNotFoundError(
                    f"interface {interface} not found in service {service}, "
                    f"availalbe interface {self.origin[service]['interface'].keys()}"
                )
            iface = deepcopy(self.origin[service]["interface"][interface])
            iface["payload"] = {}
            if iface["structures"].get("notification"):
                iface["payload"]["notification"] = self.encode_payload(
                    self.origin[service]["service_id"],
                    iface["method_id"],
                    message_type=SOMEIPMessageType.NOTIFICATION,
                )
            if iface["type"] == "method":
                iface["payload"]["response"] = self.encode_payload(
                    self.origin[service]["service_id"],
                    iface["method_id"],
                    message_type=SOMEIPMessageType.RESPONSE,
                )
            elif iface["type"] == "field" and (
                iface.get("getter_id") or iface.get("setter_id")
            ):
                iface["payload"]["response"] = self.encode_payload(
                    self.origin[service]["service_id"],
                    iface.get("getter_id") or iface.get("setter_id"),
                    message_type=SOMEIPMessageType.RESPONSE,
                )

            iface.pop("structures", None)
            svc["interface"].append(iface)

        if service_params:
            svc.update(service_params)

        server.register_service(svc)

    def update_response(
        self, server: SOMEIPServer, service: str, interface: str, structures: dict
    ):
        if not self.origin.get(service):
            raise ServiceNotFoundError(
                f"service {service} not found, available services: {self.origin.keys()}"
            )

        if not self.origin[service]["interface"].get(interface):
            raise InterfaceNotFoundError(
                f"interface {interface} not found in service {service}, "
                f"availalbe interface {self.origin[service]['interface'].keys()}"
            )

        service_id = self.origin[service]["service_id"]
        method_id = self.origin[service]["interface"][interface]["method_id"]
        if method_id != "/" and method_id != "":
            server.update_response(
                service_id,
                method_id,
                self.encode_payload(
                    service_id,
                    method_id,
                    SOMEIPMessageType.RESPONSE,
                    structures=structures,
                ),
            )
        if self.origin[service]["interface"][interface].get("getter_id"):
            server.update_response(
                service_id,
                self.origin[service]["interface"][interface]["getter_id"],
                self.encode_payload(
                    service_id,
                    method_id,
                    SOMEIPMessageType.RESPONSE,
                    structures=structures,
                ),
            )
        if self.origin[service]["interface"][interface].get("setter_id"):
            server.update_response(
                service_id,
                self.origin[service]["interface"][interface]["setter_id"],
                self.encode_payload(
                    service_id,
                    method_id,
                    SOMEIPMessageType.RESPONSE,
                    structures=structures,
                ),
            )

    def update_notification(
        self, server: SOMEIPServer, service: str, interface: str, structures: dict
    ):
        if not self.origin.get(service):
            raise ServiceNotFoundError(
                f"service {service} not found, available services: {self.origin.keys()}"
            )

        if not self.origin[service]["interface"].get(interface):
            raise InterfaceNotFoundError(
                f"interface {interface} not found in service {service}, "
                f"availalbe interface {self.origin[service]['interface'].keys()}"
            )

        service_id = self.origin[service]["service_id"]
        method_id = self.origin[service]["interface"][interface]["method_id"]
        eventgroup_id = self.origin[service]["interface"][interface]["eventgroup_id"]
        server.update_notification(
            service_id,
            eventgroup_id,
            method_id,
            self.encode_payload(
                service_id,
                method_id,
                SOMEIPMessageType.NOTIFICATION,
                structures=structures,
            ),
        )

    def as_server(
        self,
        service: Optional[str] = None,
        interfaces: Optional[List[str]] = None,
        service_params: Optional[dict] = None,
        local_bind_address: str = "",
        mcast_address: str = MULTICAST_ADDRESS,
        mcast_port: int = MULTICAST_PORT,
    ) -> SOMEIPServer:
        """act as SOME/IP server"""
        server = SOMEIPServer(
            local_bind_address=local_bind_address,
            mcast_address=mcast_address,
            mcast_port=mcast_port,
        )
        if service and interfaces:
            self.register_service(
                server, service, interfaces, service_params=service_params
            )
        return server

    def get_request(
        self, server: SOMEIPServer, e2e: bool = False, timeout: float = 0.5
    ):
        frame = server.get_request(timeout=timeout)
        if frame:
            pl = frame.payload
            if e2e:
                pl = frame.payload[2:]

            try:
                frame.structures = self.decode_payload(
                    frame.service_id,
                    frame.method_id,
                    message_type=SOMEIPMessageType.REQUEST,
                    payload=pl,
                )
            except Exception as e:
                logger.debug(e)
        return frame
