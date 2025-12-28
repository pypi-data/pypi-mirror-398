import ipaddress
import select
import socket
import struct
import threading
import time
import typing
from enum import IntEnum
from functools import partial
from logging import getLogger
from queue import Empty, Queue

from .config import Eventgroup, SDService
from .constants import (
    A_PROCESSING_TIME,
    CYCLIC_OFFER_DELAY,
    MULTICAST_ADDRESS,
    MULTICAST_PORT,
    REPETITION_BASE_DELAY,
    REPETITION_MAX,
)
from .frame import (
    SOMEIPFrame,
    SOMEIPMessageType,
    SOMEIPReturnCode,
    SOMEIPSDEntry,
    SOMEIPSDEntryType,
    SOMEIPSDFrame,
    SOMEIPSDOption,
)
from .utils import hex2int

logger = getLogger(name="someip.server")


class SimpleEventgroup:
    def __init__(
        self,
        eventgroup_id: int,
        event: int,
        interval: typing.Optional[float] = None,
        payload: bytes = b"",
    ):
        self.id = eventgroup_id
        self.events = {event: payload}
        self.interval = interval
        self.running = False

    def update_payload(self, event_id, payloay=b""):
        self.events[event_id] = payloay


class Service:
    def __init__(
        self,
        service_id: typing.Optional[int] = None,
        instance_id: typing.Optional[int] = None,
        major_version: typing.Optional[int] = None,
        minor_version: typing.Optional[int] = None,
        tcp_port: typing.Optional[int] = None,
        udp_port: typing.Optional[int] = None,
        cb: typing.Optional[typing.Callable] = None,
    ):
        self.service_id = service_id
        self.instance_id = instance_id
        self.major_version = major_version
        self.minor_version = minor_version
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.methods: typing.Dict[int, dict] = {}
        self.eventgroups: typing.Dict[int, SimpleEventgroup] = {}
        self.sockets: dict = {}
        self.cb = cb

    def register_method(self, id: int, payload: bytes = b"") -> None:
        if not self.methods.get(id):
            self.methods[id] = {}
        self.methods[id]["payload"] = payload

    def register_eventgroup(self, eventgroup: SimpleEventgroup) -> None:
        if not self.eventgroups.get(eventgroup.id):
            self.eventgroups[eventgroup.id] = eventgroup
        else:
            self.eventgroups[eventgroup.id].events.update(eventgroup.events)


class SOMEIPServer:
    """SOME/IP server."""

    class TransportType(IntEnum):
        TCP = socket.IPPROTO_TCP
        UDP = socket.IPPROTO_UDP

    def __init__(
        self,
        local_bind_address="",
        mcast_address=MULTICAST_ADDRESS,
        mcast_port=MULTICAST_PORT,
        times_cfg=None,
    ):
        """Init SOME/IP server.

        Args:
            local_bind_address (str): local address that communicate to SOME/IP service.
            mcast_address (str): multicast dst ip address.
            mcast_port (int): multicast port.
        """
        self._local_bind_address = local_bind_address
        self._mcast_address = mcast_address
        self._mcast_port = mcast_port
        self._address_family = socket.AF_INET
        if self._local_bind_address and isinstance(
            ipaddress.ip_address(self._local_bind_address), ipaddress.IPv6Address
        ):
            self._address_family = socket.AF_INET6

        self._times_cfg = times_cfg or {}
        self._session_counter = 0x0001
        self._services: typing.Dict[int, Service] = {}
        self._offers: dict = {"entries": {}}
        self._tcps: typing.Dict[int, dict] = {}
        self._udps: typing.Dict[int, dict] = {}
        self._requests = Queue(maxsize=1000)
        self._unicast_udp_sock = self._create_unicast_udp_sock(self._mcast_port)
        self._mcast_udp_sock = self._create_multicast_udp_sock()
        self._start_eventgroup_listener()

    def _start_eventgroup_listener(self):
        thread = threading.Thread(
            target=self._on_rx,
            args=("eventgroup_listener", "udp"),
            name="eventgroup_listener",
        )
        self._udps[self._mcast_port]["thread"] = thread
        self._services["eventgroup_listener"] = Service()
        self._services["eventgroup_listener"].sockets["udp"] = self._udps[
            self._mcast_port
        ]
        thread.daemon = True
        thread.start()

    def _create_tcp_sock_server(self, port: int):
        sock = socket.socket(self._address_family, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, True)
        sock.settimeout(A_PROCESSING_TIME)
        sock.bind((self._local_bind_address, port))
        sock.listen(10)

        self._tcps[port] = {}
        self._tcps[port]["socket"] = sock
        self._tcps[port]["port"] = port
        self._tcps[port]["connection"] = {}
        self._tcps[port]["running"] = True

        def listen():
            while self._tcps[port]["running"]:
                try:
                    conn, addr = sock.accept()
                except (socket.timeout, OSError):
                    continue
                else:
                    try:
                        self._tcps[port]["connection"][addr] = conn
                    except KeyError:
                        conn.close()
                    except Exception as e:
                        logger.debug(e)

        listener = threading.Thread(
            target=listen,
            name=f"tcp_listener_{port}",
        )
        listener.daemon = True
        listener.start()
        self._tcps[port]["thread"] = listener

    def _create_unicast_udp_sock(self, bind_port: int) -> socket.socket:
        sock = socket.socket(self._address_family, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(A_PROCESSING_TIME)
        sock.bind((self._local_bind_address, bind_port))
        self._udps[bind_port] = {}
        self._udps[bind_port]["socket"] = sock
        self._udps[bind_port]["port"] = bind_port
        self._udps[bind_port]["running"] = True
        return sock

    def _create_multicast_udp_sock(self) -> socket.socket:
        mcast_udp_sock = socket.socket(self._address_family, socket.SOCK_DGRAM)
        mcast_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        mcast_udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        mcast_udp_sock.settimeout(A_PROCESSING_TIME)
        mcast_udp_sock.bind((self._mcast_address, self._mcast_port))
        mreq = struct.pack(
            "4s4s",
            socket.inet_aton(self._mcast_address),
            socket.inet_aton(self._local_bind_address),
        )
        mcast_udp_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        return mcast_udp_sock

    def _send(self, frame, sock: socket.socket, addr=None):
        remaining = len(frame)
        while remaining > 0:
            if sock.type == socket.SocketKind.SOCK_STREAM:
                remaining -= sock.send(frame[-remaining:])
            else:
                remaining -= sock.sendto(frame[-remaining:], addr)

    def _on_subscribe_ack(
        self, frame: SOMEIPFrame, entry: SOMEIPSDEntry, sock: socket.socket, addr
    ):
        entries = SOMEIPSDEntry(
            sd_type=SOMEIPSDEntryType.SubscribeAck,
            service_id=entry.service_id,
            instance_id=entry.instance_id,
            major_version=entry.major_version,
            ttl=entry.ttl,
            minver_or_counter=entry.minver_or_counter,
        )

        frame.session_id = self._session_counter
        self._session_counter += 1

        frame.payload = SOMEIPSDFrame(
            entries=(entries,),
        ).encode_sd()

        self._send(frame.encode(), sock, addr=addr)

    def _on_subscribe_nack(
        self, frame: SOMEIPFrame, entry: SOMEIPSDEntry, sock: socket.socket, addr
    ):
        entries = SOMEIPSDEntry(
            sd_type=SOMEIPSDEntryType.SubscribeAck,
            service_id=entry.service_id,
            instance_id=entry.instance_id,
            major_version=entry.major_version,
            ttl=0,
            minver_or_counter=entry.minver_or_counter,
        )

        frame.session_id = self._session_counter
        self._session_counter += 1

        frame.payload = SOMEIPSDFrame(
            entries=[entries],
        ).encode()

        self._send(frame.encode(), sock, addr=addr)

    def _offer(self):
        self._offers["running"] = True
        repetitions_max = self._times_cfg.get("REPETITION_MAX") or REPETITION_MAX
        repetition_base_delay = (
            self._times_cfg.get("REPETITION_BASE_DELAY") or REPETITION_BASE_DELAY
        )
        cyclic_offer_delay = (
            self._times_cfg.get("CYCLIC_OFFER_DELAY") or CYCLIC_OFFER_DELAY
        )

        def send():
            self._send_offer()

            for i in range(repetitions_max):
                time.sleep((2**i) * repetition_base_delay)
                self._send_offer()

            if not cyclic_offer_delay:
                return

            while self._offers["running"]:
                time.sleep(cyclic_offer_delay)
                self._send_offer()

        offer = threading.Thread(
            target=send,
            name="offer",
        )
        self._offers["thread"] = offer
        offer.daemon = True
        offer.start()

    def _send_offer(self):
        frame = SOMEIPSDFrame(
            session_id=self._session_counter,
            entries=[
                e.create_offer_entry(ttl=0xFFFFFF)
                for e in self._offers["entries"].values()
            ],
        )
        self._session_counter += 1
        self._send(
            frame.encode(),
            sock=self._unicast_udp_sock,
            addr=(self._mcast_address, self._mcast_port),
        )

    def _notify(
        self, eventgroup: SimpleEventgroup, entry: SOMEIPSDEntry, option: SOMEIPSDOption
    ):
        addr = (option.address.compressed, option.port)
        protocol = option.l4proto
        if eventgroup.interval:
            self._notify_cycle(
                entry.service_id,
                entry.major_version,
                eventgroup,
                protocol,
                addr=addr,
            )
        else:
            self._notify_onchange(
                entry.service_id,
                entry.major_version,
                eventgroup,
                protocol,
                addr=addr,
            )

    def _stop_notify(self, eventgroup: SimpleEventgroup):
        eventgroup.running = False

    def _on_notify(
        self,
        service_id: int,
        event_id: int,
        major_version: int,
        payload: bytes,
        sock: socket.socket,
        addr=None,
    ):
        frame = SOMEIPFrame(
            service_id=service_id,
            method_id=event_id,
            interface_version=major_version,
            message_type=SOMEIPMessageType.NOTIFICATION,
            return_code=SOMEIPReturnCode.E_OK,
            payload=payload,
        )
        self._send(frame.encode(), sock, addr=addr)

    def _notify_onchange(
        self,
        service_id: int,
        major_version: int,
        eventgroup: SimpleEventgroup,
        protocol: str,
        addr=None,
    ):
        if protocol == SOMEIPServer.TransportType.TCP:
            sock = self._services[service_id].sockets["tcp"]["connection"][addr]
        elif protocol == SOMEIPServer.TransportType.UDP:
            sock = self._services[service_id].sockets["udp"]["socket"]

        for event_id, payload in eventgroup.events.items():
            try:
                self._on_notify(
                    service_id, event_id, major_version, payload, sock, addr=addr
                )
            except Exception as e:
                logger.debug(e)

    def _notify_cycle(
        self,
        service_id: int,
        major_version: int,
        eventgroup: SimpleEventgroup,
        protocol: str,
        addr=None,
    ):
        if eventgroup.running:
            return

        def _loop():
            if protocol == SOMEIPServer.TransportType.TCP:
                sock = self._services[service_id].sockets["tcp"]["connection"][addr]
            elif protocol == SOMEIPServer.TransportType.UDP:
                sock = self._services[service_id].sockets["udp"]["socket"]

            eventgroup.running = True

            try:
                while eventgroup.running:
                    for event_id, payload in eventgroup.events.items():
                        try:
                            self._on_notify(
                                service_id,
                                event_id,
                                major_version,
                                payload,
                                sock,
                                addr=addr,
                            )
                        except Exception as e:
                            logger.debug(e)

                    time.sleep(eventgroup.interval / 1000)
            except Exception:
                pass

        loop = threading.Thread(
            target=_loop,
            name="notification",
        )
        eventgroup.thread = loop
        loop.daemon = True
        loop.start()

    def _on_error_response(
        self,
        frame: SOMEIPFrame,
        r_code: SOMEIPReturnCode,
        sock: socket.socket,
        addr=None,
    ):
        frame.message_type = SOMEIPMessageType.ERROR
        frame.return_code = r_code
        self._send(frame.encode(), sock, addr=addr)

    def _handle_method(
        self,
        frames: typing.List[SOMEIPFrame],
        sock: socket.socket,
        addr=None,
    ):
        for frame in frames:
            if not self._services.get(frame.service_id):
                self._on_error_response(
                    frame, SOMEIPReturnCode.E_UNKNOWN_SERVICE, sock, addr=addr
                )
            elif frame.method_id not in self._services[frame.service_id].methods:
                self._on_error_response(
                    frame, SOMEIPReturnCode.E_UNKNOWN_METHOD, sock, addr=addr
                )
            else:
                if frame.message_type == SOMEIPMessageType.REQUEST:
                    self._requests.put(frame)
                    logger.debug(f"received R&R method, SOMEIPFrame: {frame}")
                    response = SOMEIPFrame(
                        service_id=frame.service_id,
                        method_id=frame.method_id,
                        client_id=frame.client_id,
                        session_id=frame.session_id,
                        protocol_version=frame.protocol_version,
                        interface_version=frame.interface_version,
                        message_type=SOMEIPMessageType.RESPONSE,
                        return_code=frame.return_code,
                        payload=self._services[frame.service_id].methods[
                            frame.method_id
                        ]["payload"],
                    )
                    self._send(response.encode(), sock, addr=addr)
                    if self._services[frame.service_id].cb:
                        try:
                            self._services[frame.service_id].cb(
                                frame, func=partial(self._send, sock, addr=addr)
                            )
                        except Exception as e:
                            logger.debug(e)

    def _handler_event(
        self,
        frames: typing.List[SOMEIPFrame],
        sock: socket.socket,
        addr=None,
    ):
        for frame in frames:
            sd_frame, _ = SOMEIPSDFrame().decode_sd(frame.payload)
            option = sd_frame.options[0]
            for entry in sd_frame.entries:
                if (
                    not self._services.get(entry.service_id)
                    or self._services[entry.service_id].instance_id != entry.instance_id
                ):
                    self._on_subscribe_nack(frame, entry, sock, addr)
                else:
                    if entry.ttl:
                        logger.debug(
                            f"received subscribe, SOMEIP-Frame: {frame}, SOMEIP-SD-Frame: {sd_frame}"
                        )
                        self._on_subscribe_ack(frame, entry, sock, addr)
                        if self._services[entry.service_id].eventgroups.get(
                            entry.eventgroup_id
                        ):
                            self._notify(
                                self._services[entry.service_id].eventgroups[
                                    entry.eventgroup_id
                                ],
                                entry,
                                option,
                            )
                    else:
                        logger.debug(
                            f"received stop subscribe, SOMEIP-SD-Frame: {sd_frame}"
                        )
                        self._stop_notify(
                            self._services[entry.service_id].eventgroups[
                                entry.eventgroup_id
                            ],
                        )

    def _handle_request(
        self,
        request: bytes,
        sock: socket.socket,
        addr=None,
    ):
        try:
            incoming_frame = SOMEIPFrame.decode(request, decode_all=True)
            if not isinstance(incoming_frame, list):
                incoming_frame = [incoming_frame]
            if incoming_frame[0].service_id == SOMEIPSDFrame.SD_SERVICE_ID:
                self._handler_event(incoming_frame, sock, addr=addr)
            else:
                self._handle_method(incoming_frame, sock, addr=addr)
        except Exception as e:
            logger.debug(e)

    def _on_rx(self, service_id: int, protocol: str):
        """SOME/IP server listener."""
        request = None
        addr = None
        while self._services[service_id].sockets[protocol]["running"]:
            try:
                if (
                    self._services[service_id].sockets[protocol]["socket"].type
                    == socket.SocketKind.SOCK_STREAM
                ):
                    if self._services[service_id].sockets[protocol].get("connection"):
                        for k, conn in (
                            self._services[service_id]
                            .sockets[protocol]["connection"]
                            .items()
                        ):
                            r, _, _ = select.select([conn], [], [], A_PROCESSING_TIME)

                            if r:
                                request = conn.recv(4096)
                                if request:
                                    self._handle_request(
                                        request,
                                        conn,
                                        addr=addr,
                                    )
                                else:
                                    conn.close()
                                    self._services[service_id].sockets[protocol][
                                        "connection"
                                    ].pop(k, None)
                else:
                    r, _, _ = select.select(
                        [self._services[service_id].sockets[protocol]["socket"]],
                        [],
                        [],
                        A_PROCESSING_TIME,
                    )
                    if r:
                        request, addr = (
                            self._services[service_id]
                            .sockets[protocol]["socket"]
                            .recvfrom(4096)
                        )
                        if request:
                            self._handle_request(
                                request,
                                self._services[service_id].sockets[protocol]["socket"],
                                addr=addr,
                            )
            except (BlockingIOError, socket.timeout):
                pass
            except Exception as e:
                logger.debug(e)

            # sleep 1us to give up cpu time
            time.sleep(0.000001)

    def _create_method(self, svc: Service, interface: dict):
        thread = threading.Thread(
            target=self._on_rx,
            args=(svc.service_id, interface["protocol"]),
            name=f"service_listener_{svc.service_id}",
        )

        if interface["protocol"] == "tcp":
            if self._tcps.get(svc.tcp_port):
                if not svc.sockets.get(interface["protocol"]):
                    svc.sockets[interface["protocol"]] = self._tcps[svc.tcp_port]
                return
            self._create_tcp_sock_server(svc.tcp_port)
            self._tcps[svc.tcp_port]["thread"] = thread
            svc.sockets[interface["protocol"]] = self._tcps[svc.tcp_port]
        else:
            if self._udps.get(svc.udp_port):
                if not svc.sockets.get(interface["protocol"]):
                    svc.sockets[interface["protocol"]] = self._udps[svc.tcp_port]
                return
            self._create_unicast_udp_sock(svc.udp_port)
            self._udps[svc.udp_port]["thread"] = thread
            svc.sockets[interface["protocol"]] = self._udps[svc.tcp_port]

        thread.daemon = True
        thread.start()

    def _create_event(self, svc: Service, interface: dict):
        service_id = svc.service_id
        instance_id = svc.instance_id
        if not self._offers["entries"].get(f"{service_id}-{instance_id}"):
            if interface["protocol"] == "tcp":
                options_1_list = (
                    Eventgroup._sockaddr_to_endpoint(
                        (self._local_bind_address, svc.tcp_port),
                        SOMEIPServer.TransportType.TCP,
                    ),
                    # Eventgroup._sockaddr_to_endpoint(
                    #     (self._local_bind_address, svc.udp_port),
                    #     SOMEIPServer.TransportType.UDP,
                    # ),
                )
            else:
                options_1_list = (
                    Eventgroup._sockaddr_to_endpoint(
                        (self._local_bind_address, svc.tcp_port),
                        SOMEIPServer.TransportType.UDP,
                    ),
                    # Eventgroup._sockaddr_to_endpoint(
                    #     (self._local_bind_address, svc.udp_port),
                    #     SOMEIPServer.TransportType.TCP,
                    # ),
                )
            self._offers["entries"][f"{service_id}-{instance_id}"] = SDService(
                service_id,
                instance_id,
                svc.major_version,
                svc.minor_version,
                options_1=options_1_list,
            )

        self._create_method(svc, interface)

    def register_service(self, service: dict):
        """
        register a service for SOME/IP server.

        Args:
            service (dict): service template.

        template example::

            {
                "service_id": "0x405f",
                "instance_id": 1,
                "major_version": 6,
                "minor_version": 0,
                "tcp_port": 54001,
                "udp_port": 54001,
                "interface": [
                    {
                        "type": "method",
                        "protocol": "tcp",
                        "method_id": "0x001",
                        "structures": {}
                    },
                    {
                        "type": "event",
                        "protocol": "udp",
                        "method_id": "0x002",
                        "eventgroup_id": 1,
                        "structures": {}
                    },
                    {
                        "type": "field",
                        "protocol": "udp",
                        "method_id": "0x002",
                        "eventgroup_id": 1,
                        "getter_id": "0x003",
                        "setter_id": "0x004",
                        "structures": {}
                    }
                ]
        """
        service_id = hex2int(service["service_id"])
        if not self._services.get(service_id):
            self._services[service_id] = Service(
                service_id=service_id,
                instance_id=service["instance_id"],
                major_version=service["major_version"],
                minor_version=service["minor_version"],
                tcp_port=service["tcp_port"],
                udp_port=service["udp_port"],
                cb=service.get("cb"),
            )
        for interface in service["interface"]:
            if interface["type"] == "method":
                self._services[service_id].register_method(
                    hex2int(interface["method_id"]),
                    payload=interface["payload"]["response"],
                )
                self._create_method(self._services[service_id], interface)
            elif interface["type"] == "event":
                self._services[service_id].register_eventgroup(
                    SimpleEventgroup(
                        interface["eventgroup_id"],
                        hex2int(interface["method_id"]),
                        payload=interface["payload"]["notification"],
                        interval=10,
                    ),
                )
                self._create_event(self._services[service_id], interface)
            elif interface["type"] == "field":
                if interface.get("eventgroup_id"):
                    interval = None
                    if interface.get("interval"):
                        interval = interface["interval"]
                    self._services[service_id].register_eventgroup(
                        SimpleEventgroup(
                            interface["eventgroup_id"],
                            hex2int(interface["method_id"]),
                            payload=interface["payload"]["notification"],
                            interval=interval,
                        ),
                    )
                    self._create_event(self._services[service_id], interface)

                if interface.get("getter_id"):
                    self._services[service_id].register_method(
                        hex2int(interface["getter_id"]),
                        payload=interface["payload"]["response"],
                    )
                if interface.get("setter_id"):
                    self._services[service_id].register_method(
                        hex2int(interface["setter_id"]),
                        payload=interface["payload"]["response"],
                    )
                if interface.get("getter_id") or interface.get("setter_id"):
                    self._create_method(self._services[service_id], interface)

        if not self._offers.get("running"):
            self._offer()

    def update_response(self, service_id: int, method_id: int, payload: bytes):
        self._services[hex2int(service_id)].register_method(hex2int(method_id), payload)

    def update_notification(
        self, service_id: int, eventgroup_id: int, event_id: int, payload: bytes
    ):
        self._services[hex2int(service_id)].eventgroups[eventgroup_id].update_payload(
            hex2int(event_id), payload
        )

    def get_request(self, timeout: float = 0.5) -> SOMEIPFrame:
        try:
            return self._requests.get(block=True, timeout=timeout)
        except Empty:
            return None

    def _unregister_service(self, service_id):
        if not self._services.get(service_id):
            logger.warning(f"service {service_id} not found")
            return

        self._services.pop(service_id, None)

    def unregister_services(self):
        if self._offers:
            self._offers["running"] = False
            if self._offers.get("thread") and self._offers["thread"].is_alive():
                self._offers["thread"].join(A_PROCESSING_TIME + 1.0)

        # self._unregister_service("eventgroup_listener")
        # services = copy.deepcopy(list(self._services.keys()))
        # for service in services:
        #     if service != "eventgroup_listener":
        #         self._unregister_service(service)

        # del services
        self._offers = {}
        self._events = {}

    def close(self):
        """close socket"""
        self.unregister_services()
        for port, _ in self._tcps.items():
            self._tcps[port]["running"] = False
            if self._tcps[port]["thread"].is_alive():
                self._tcps[port]["thread"].join(A_PROCESSING_TIME + 1.0)

            for conn in self._tcps[port]["connection"].values():
                conn.close()

            self._tcps[port]["socket"].close()

        for udp_sock in self._udps.values():
            udp_sock["running"] = False
            udp_sock["socket"].close()

        time.sleep(A_PROCESSING_TIME)
        self._tcps = {}
        self._udps = {}
        self._mcast_udp_sock.close()
        self._mcast_udp_sock = None
        self._unicast_udp_sock.close()
        self._unicast_udp_sock = None
        self._session_counter = 0x0001
