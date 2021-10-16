"""
Generate settings for WireGuard.
"""

import logging
import os
import ipaddress
import sys
from typing import Union
import wgconfig
import wgconfig.wgexec
import qrcode

CONFIGURATION_DIR = '/config'
SERVER_CONFIGURATION_FILE = '/config/wg0.conf'


class WireGuard(wgconfig.WGConfig):
    """
    Child class for create WireGuard configuration.

    ...

    Attributes:
    ----------
    configuration_dir : str
        path to dir where saving configurations
    server_configuration_file : str
        WireGuard server configuration file

    Methods
    -------
    _get_interface_name():
        Get default interface name for WireGuard server.
    create_server_configuration():
        Create server configuration file.
    add_client():
        Add configuration file and qr-code for client.

    """
    post_up: str = 'iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT;' \
                   'iptables -t nat -A POSTROUTING -o {0} -j MASQUERADE;' \
                   'ip6tables -A FORWARD -i %i -j ACCEPT; ip6tables -A FORWARD -o %i -j ACCEPT;' \
                   'ip6tables -t nat -A POSTROUTING -o {0} -j MASQUERADE; /app/wgdashboard/wgd.sh start'
    post_down: str = 'iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT;' \
                     'iptables -t nat -D POSTROUTING -o {0} -j MASQUERADE;' \
                     'ip6tables -D FORWARD -i %i -j ACCEPT; ip6tables -D FORWARD -o %i -j ACCEPT;' \
                     'ip6tables -t nat -D POSTROUTING -o {0} -j MASQUERADE; /app/wgdashboard/wgd.sh stop'

    def __init__(self, configuration_dir, server_configuration_file):
        """
        Constructs all the necessary attributes for the person object.

        Parameters
        ----------
        configuration_dir : str
            path to dir where saving configurations
        server_configuration_file : str
            WireGuard server configuration file
        """

        self.configuration_dir: str = configuration_dir
        super().__init__(server_configuration_file)
        self.server_public_key: str = str()
        self.log_gwg: logging.Logger = logging.getLogger('CLASS_GWG')
        logging_configuration(self.log_gwg)

    def _get_interface_name(self) -> Union[str, None]:
        """
        Get default interface name for WireGuard server.

        Returns
        -------
        str
            Interface name.
        None
            Not found interface name.
        """

        interfaces_list: tuple = (
            'eth0',
            'ens3'
        )

        host_interfaces: list = os.listdir('/sys/class/net/')
        for interface_name in interfaces_list:
            if interface_name in host_interfaces:
                self.log_gwg.info('Find %s interface', interface_name)
                result: str = interface_name
                break
        else:
            self.log_gwg.error('Cannot find interface name:\n %s', host_interfaces)
            result: None = None

        return result

    def create_server_configuration(self, server_ip, server_port) -> None:
        """
        Create server configuration file.

        Parameters
        ----------
        server_ip : str
            white ip-address of WireGuard server
        server_port : str
            wireGuard server port

        Returns
        -------
        None
        """

        server_private_key, self.server_public_key, = wgconfig.wgexec.generate_keypair()
        host_interface_name = self._get_interface_name()
        if not host_interface_name:
            raise Exception('Not found server interface')
        init_server_interface: dict = {
            'Address': server_ip,
            'SaveConfig': 'true',
            'ListenPort': server_port,
            'PostUp': self.post_up.format(host_interface_name),
            'PostDown': self.post_down.format(host_interface_name),
            'PrivateKey': server_private_key,
        }

        for attr_name, attr_value in init_server_interface.items():
            self.add_attr(None, attr_name, attr_value)

        self.write_file()

    def add_client(self, client_name: str, client_ips: tuple, dns_server: str,
                   vpn_domain_name: str, allowed_ips: str) -> None:
        """
        Add configuration file and qr-code for client.

        Parameters
        ----------
        client_name : str
            client label
        client_ips : tuple
            client vpn ip
        dns_server : str
            dns-servers for client
        vpn_domain_name : str
            domain name or ip address of WireGuard server
        allowed_ips : str
            allowed ips for routing

        Returns
        -------
        None
        """

        client_configuration_dir: str = os.path.join(self.configuration_dir, client_name)
        os.mkdir(client_configuration_dir)
        wg_client: wgconfig.WGConfig = wgconfig.WGConfig(os.path.join(client_configuration_dir, client_name + '.conf'))
        client_private_key, client_public_key = wgconfig.wgexec.generate_keypair()
        init_client_interface: dict = {
            'Address': client_ips[0],
            'PrivateKey': client_private_key,
            'DNS': dns_server,
        }

        init_client_peer: dict = {
            'Endpoint': vpn_domain_name,
            'AllowedIPs': allowed_ips,
        }

        init_server_peer: dict = {
            'AllowedIPs': client_ips[1]
        }

        for attr_name, attr_value in init_client_interface.items():
            wg_client.add_attr(None, attr_name, attr_value)

        wg_client.add_peer(self.server_public_key)
        for attr_name, attr_value in init_client_peer.items():
            wg_client.add_attr(self.server_public_key, attr_name, attr_value)

        img = qrcode.make("\n".join(wg_client.lines))
        img.save(os.path.join(client_configuration_dir, client_name + '.png'))
        wg_client.write_file()

        self.add_peer(client_public_key)
        for attr_name, attr_value in init_server_peer.items():
            self.add_attr(client_public_key, attr_name, attr_value)


def logging_configuration(logger) -> None:
    """
    Configure logger.

    Parameters
    ----------
    logger : logging.Logger
        logger

    Returns
    -------
    None
    """

    sh_formatter: logging.Formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: %(process)d %(name)s '
                                                            '%(funcName)s %(message)s',
                                                        datefmt='%m-%d-%Y %H:%M:%S', )
    sh: logging.StreamHandler = logging.StreamHandler()
    sh.setLevel(level=logging.INFO)
    sh.setFormatter(sh_formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(sh)


def main() -> None:
    """
    Main function.

    Returns
    -------
    None
    """

    vpn_subnetv4 = ipaddress.ip_network((os.environ.get('INTERNAL_SUBNETv4', '10.13.13.0'), 24))
    vpn_subnetv6 = ipaddress.ip_network((os.environ.get('INTERNAL_SUBNETv6', 'fc00:bfb7:3bdb:ae33::'), 64))
    vpn_port: str = os.environ.get('SERVERPORT', '51820')
    vpn_domain_name: str = os.environ.get('SERVERURL', '')
    allowed_ip = os.environ.get('AllowedIPs', '0.0.0.0/0,::/0')
    dns_server = os.environ.get('PEERDNS', '77.88.8.8,77.88.8.1,2a02:6b8::feed:0ff,2a02:6b8:0:1::feed:0ff')
    peers_count: int = int(os.environ.get('PEERS', 1))
    wg = WireGuard(CONFIGURATION_DIR, SERVER_CONFIGURATION_FILE)
    subnet_ipsv4 = vpn_subnetv4.hosts()
    subnet_ipsv6 = vpn_subnetv6.hosts()
    server_ip = f'{str(next(subnet_ipsv4))}/{str(vpn_subnetv4.prefixlen)},' \
                f'{str(next(subnet_ipsv6))}/{str(vpn_subnetv6.prefixlen)}'
    if not os.path.isfile(SERVER_CONFIGURATION_FILE):
        wg.create_server_configuration(server_ip, vpn_port)

        for peer_number in range(peers_count):
            peer_name: str = 'peer_' + str(peer_number)
            client_ipv4 = str(next(subnet_ipsv4))
            client_ipv6 = str(next(subnet_ipsv6))
            peer_ips: tuple = (f'{client_ipv4}/{str(vpn_subnetv4.prefixlen)},'
                               f'{client_ipv6}/{str(vpn_subnetv6.prefixlen)}',
                               f'{client_ipv4}/32,{client_ipv6}/128')
            vpn_address: str = vpn_domain_name + ':' + vpn_port
            wg.add_client(peer_name, peer_ips, dns_server, vpn_address, allowed_ip)
        wg.write_file()
    else:
        log_mgwg.info('Configuration is exist')
        if len(os.listdir(CONFIGURATION_DIR)) != peers_count:
            log_mgwg.info('We have new peers')


if __name__ == '__main__':
    log_mgwg = logging.getLogger('MAIN_GWG')
    print(type(log_mgwg))
    logging_configuration(log_mgwg)
    sys.exit(main())
