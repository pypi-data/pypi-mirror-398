import json
import time

import click

from someip_py import SOMEIPService, __version__


@click.version_option(version=__version__)
@click.group(
    context_settings=dict(help_option_names=["-h", "--help"]),
)
def main():
    pass


@main.command(name="gen")
@click.option(
    "-p",
    "--platform",
    help="the project platform",
    default=SOMEIPService.Platform.P_30T,
)
@click.option("-f", "--file", help="communicate matrix file path", required=True)
@click.option("-o", "--output", help="output dir", default="services")
def gen(platform, file, output):
    """generate someip service python module"""
    s = SOMEIPService(platform=platform)
    s.generate_services(file, output=output)


@main.command(name="decode")
@click.option(
    "-p",
    "--platform",
    help="the project platform",
    default=SOMEIPService.Platform.P_30T,
)
@click.option("-i", "--idl", help="someip service matrix path", default=None)
@click.option("-P", "--proto_path", help="someip proto path", default=None)
@click.option("-s", "--service_id", help="service id", required=True)
@click.option("-m", "--method_id", help="method id", required=True)
@click.option("-t", "--message_type", type=int, help="method id", default=2)
@click.option("-P", "--payload", help="method id", required=True)
def decode(platform, idl, proto_path, service_id, method_id, message_type, payload):
    """decode some/ip message"""
    s = SOMEIPService(platform=platform, arxml_path=idl, proto_path=proto_path)
    click.echo(
        click.style(
            json.dumps(
                s.decode_payload(
                    service_id, method_id, message_type=message_type, payload=payload
                ),
                indent=4,
            ),
            fg="cyan",
            bold=True,
        )
    )


@main.command(name="parse")
@click.option(
    "-p",
    "--platform",
    help="the project platform",
    default=SOMEIPService.Platform.P_30T,
)
@click.option("-i", "--idl", help="someip service matrix path", default=None)
@click.option("-P", "--proto_path", help="someip proto path", default=None)
@click.option("-f", "--file", help="pcap file path", required=True)
@click.option("-o", "--output", help="output dir", default=None)
@click.option("-s", "--service_id", help="filter by someip serviceid", default=None)
@click.option("-m", "--method_id", help="filter by someip methodid", default=None)
def parse(platform, idl, proto_path, file, output, service_id, method_id):
    """parse pcap/pcapng file"""
    s = SOMEIPService(platform=platform, arxml_path=idl, proto_path=proto_path)
    filters = {}
    if service_id:
        filters["service_id"] = service_id
    if method_id:
        filters["method_id"] = method_id
    s.parse_pcap(file, output=output, filters=filters)


@main.command(name="sub")
@click.option(
    "-p",
    "--platform",
    help="the project platform",
    default=SOMEIPService.Platform.P_30T,
)
@click.option("-s", "--service", help="someip service name", required=True)
@click.option("-i", "--interface", help="someip service interface name", required=True)
@click.option("-r", "--remote_address", help="remote addr", default="10.206.0.5")
@click.option("-l", "--local_address", help="local addr", default="10.206.0.1")
@click.option("-m", "--mcast_address", help="multicast addr", default="227.100.206.1")
@click.option("-t", "--timeout", help="recv timeout", type=int, default=5)
@click.option("-T", "--ttl", help="subscribe ttl", type=int, default=3)
def sub(
    platform,
    service,
    interface,
    remote_address,
    local_address,
    mcast_address,
    timeout,
    ttl,
):
    """subscribe a some/ip eventgroup"""
    s = SOMEIPService(platform=platform)

    def cb(frame):
        try:
            frame.structures = s.decode_payload(
                frame.service_id,
                frame.method_id,
                payload=frame.payload,
            )
        except Exception as e:
            frame.structures = str(e)

        print(frame)

    s.as_client(
        service=service,
        interface=interface,
        remote_address=remote_address,
        local_address=local_address,
        mcast_address=mcast_address,
        ttl=ttl,
        cb=cb,
        timeout=timeout,
    )


@main.command(name="inject")
@click.option(
    "-p",
    "--platform",
    help="the project platform",
    default=SOMEIPService.Platform.P_30T,
)
@click.option("-i", "--idl", help="someip service matrix path", default=None)
@click.option("-P", "--proto_path", help="someip proto path", default=None)
@click.option("-f", "--file", help="someip json config file", required=True)
def inject(platform, idl, proto_path, file):
    """update internal someip json config file"""
    s = SOMEIPService(platform=platform, arxml_path=idl, proto_path=proto_path)
    s.inject_config(platform, file)


@click.group(
    context_settings=dict(help_option_names=["-h", "--help"]),
)
def server():
    """SOME/IP simulation server"""
    pass


main.add_command(server)


@server.command(name="start")
@click.option(
    "-p",
    "--platform",
    help="the project platform",
    default=SOMEIPService.Platform.P_30T,
)
@click.option("-s", "--service", help="someip service name", required=True)
@click.option("-i", "--interface", help="someip service interface name", required=True)
@click.option("-l", "--local_address", help="local addr", default="10.206.0.1")
@click.option("-m", "--mcast_address", help="multicast addr", default="227.100.206.1")
@click.option("-p", "--port", help="multicast port", default=30490)
@click.option("-t", "--timeout", help="recv timeout", type=int, default=5)
def start_server(
    platform, service, interface, local_address, mcast_address, port, timeout
):
    """start SOME/IP simulation server"""
    s = SOMEIPService(platform=platform)
    s.as_server(
        service=service,
        interfaces=[interface],
        local_bind_address=local_address,
        mcast_address=mcast_address,
        mcast_port=port,
    )
    t = time.time()
    while time.time() - t < timeout:
        time.sleep(1)


@server.command(name="stop")
@click.option(
    "-p",
    "--platform",
    help="the project platform",
    default=SOMEIPService.Platform.P_30T,
)
def stop_server():
    """stop SOME/IP simulation server"""
    pass
