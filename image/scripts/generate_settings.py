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


def main():
    vpn_subnet = ipaddress.ip_network((os.environ.get('INTERNAL_SUBNET', '10.13.13.0'), 24))
    vpn_port: str = os.environ.get('SERVERPORT', '51820')
    vpn_domain_name: str = os.environ.get('SERVERURL', '')
    allowed_ip = ipaddress.ip_network(os.environ.get('AllowedIPs', '0.0.0.0/0'))
    dns_server = ipaddress.ip_address(os.environ.get('PEERDNS', '77.88.8.8'))
    peers_count: int = int(os.environ.get('PEERS', 1))
    wg = WireGuard(CONFIGURATION_DIR, SERVER_CONFIGURATION_FILE)
    subnets_ips = vpn_subnet.hosts()
    server_ip = str(next(subnets_ips)) + '/' + str(vpn_subnet.prefixlen)
    if not os.path.isfile(SERVER_CONFIGURATION_FILE):
        wg.create_server_configuration(server_ip, vpn_port)

        for peer_number in range(peers_count):
            peer_name: str = 'peer_' + str(peer_number)
            client_ip = str(next(subnets_ips))
            peer_ips: tuple = (client_ip + '/' + str(vpn_subnet.prefixlen), client_ip + '/32')
            vpn_address: str = vpn_domain_name + ':' + vpn_port
            wg.add_client(peer_name, peer_ips, dns_server, vpn_address, str(allowed_ip))
        wg.write_file()
    else:
        wg.read_file()


if __name__ == '__main__':
    main()
