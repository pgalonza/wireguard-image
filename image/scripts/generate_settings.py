import logging
import os
import ipaddress
import wgconfig
import wgconfig.wgexec
import qrcode

CONFIGURATION_DIR = '/config'
SERVER_CONFIGURATION_FILE = '/config/wg0.conf'


class WireGuard(wgconfig.WGConfig):
    post_up: str = 'iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A ' \
              'POSTROUTING -o eth0 -j MASQUERADE'
    post_down: str = 'iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D ' \
                     'POSTROUTING -o eth0 -j MASQUERADE'

    def __init__(self, configuration_dir, server_configuration_file):
        self.configuration_dir: str = configuration_dir
        super().__init__(server_configuration_file)
        self.server_public_key: str = str()

    def create_server_configuration(self, server_ip, server_port):
        server_private_key, self.server_public_key, = wgconfig.wgexec.generate_keypair()
        init_server_interface: dict = {
            'Address': server_ip,
            'SaveConfig': 'true',
            'ListenPort': server_port,
            'PostUp': self.post_up,
            'PostDown': self.post_down,
            'PrivateKey': server_private_key,
        }

        for attr_name, attr_value in init_server_interface.items():
            self.add_attr(None, attr_name, attr_value)

        self.write_file()

    def add_client(self, client_name, client_ip, dns_server, vpn_domain_name, allowed_ips):
        client_configuration_dir: str = os.path.join(self.configuration_dir, client_name)
        os.mkdir(client_configuration_dir)
        wg_client = wgconfig.WGConfig(os.path.join(client_configuration_dir, client_name + '.conf'))
        client_private_key, client_public_key = wgconfig.wgexec.generate_keypair()
        init_client_interface: dict = {
            'Address': client_ip[0],
            'PrivateKey': client_private_key,
            'DNS': dns_server,
        }

        init_client_peer: dict = {
            'Endpoint': vpn_domain_name,
            'AllowedIPs': allowed_ips,
        }

        init_server_peer: dict = {
            'AllowedIPs': client_ip[1]
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


def logging_configuration(logger):
    sh_formatter = logging.Formatter(fmt='%(asctime)s %(levelname)s: %(process)d %(name)s %(funcName)s %(message)s',
                                     datefmt='%m-%d-%Y %H:%M:%S', )
    sh = logging.StreamHandler()
    sh.setLevel(level=logging.INFO)
    sh.setFormatter(sh_formatter)

    logger.addHandler(sh)


def main():
    vpn_subnetv4 = ipaddress.ip_network((os.environ.get('INTERNAL_SUBNETv4', '10.13.13.0'), 24))
    vpn_subnetv6 = ipaddress.ip_network((os.environ.get('INTERNAL_SUBNETv6', 'fc00:bfb7:3bdb:ae33::'), 120))
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
            peer_ips: tuple = (f'{client_ipv4}/{str(vpn_subnetv4.prefixlen)},{client_ipv6}/{str(vpn_subnetv6.prefixlen)}',
                               f'{client_ipv4}/32,{client_ipv6}/128')
            vpn_address: str = vpn_domain_name + ':' + vpn_port
            wg.add_client(peer_name, peer_ips, dns_server, vpn_address, allowed_ip)
        wg.write_file()
    else:
        log_gwg.info('Configuration is exist')
        if len(os.listdir(CONFIGURATION_DIR)) != peers_count:
            log_gwg.info('We have new peers')


if __name__ == '__main__':
    log_gwg = logging.getLogger('G_WG')
    logging_configuration(log_gwg)
    main()
