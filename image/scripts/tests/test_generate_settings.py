import sys
import unittest
import unittest.mock
import generate_settings


class TestGS(unittest.TestCase):

    def test_interface_name_eth(self):
        with unittest.mock.patch('generate_settings.os.listdir') as ld_mock:
            ld_mock.return_value = ('lo', 'eth0', 'eth')
            wg_interface = generate_settings.WireGuard('', '')
            result = wg_interface._get_interface_name()
            self.assertEqual(result, 'eth0')

    def test_interface_name_ens(self):
        with unittest.mock.patch('generate_settings.os.listdir') as ld_mock:
            ld_mock.return_value = ('lo', 'ens3', 'ens')
            wg_interface = generate_settings.WireGuard('', '')
            result = wg_interface._get_interface_name()
            self.assertEqual(result, 'ens3')

    def test_interface_name_error(self):
        with unittest.mock.patch('generate_settings.os.listdir') as ld_mock:
            ld_mock.return_value = ('lo', 'ens', 'enh', 'ens4', 'eth1')
            wg_interface = generate_settings.WireGuard('', '')
            result = wg_interface._get_interface_name()
            self.assertIsNone(result)

    def test_server_configuration(self):
        with unittest.mock.patch('generate_settings.wgconfig.wgexec.generate_keypair') as gk_mock:
            with unittest.mock.patch('generate_settings.wgconfig.WGConfig.write_file'):
                mock_gin = unittest.mock.Mock()
                mock_gin.return_value = 'eth0'
                gk_mock.return_value = ('private_key', 'public_key')
                wg_interface = generate_settings.WireGuard('', '')
                wg_interface._get_interface_name = mock_gin
                wg_interface.create_server_configuration('127.0.0.1', 51820)
                print(wg_interface.lines)
                self.assertEqual(len(wg_interface.lines), 7)

    def test_client_configuration(self):
        with unittest.mock.patch('generate_settings.wgconfig.WGConfig.write_file'):
            with unittest.mock.patch('generate_settings.os.mkdir'):
                with unittest.mock.patch('qrcode.make'):
                    wg_interface = generate_settings.WireGuard('', '')
                    wg_interface.server_public_key = 'public_key'
                    wg_interface.add_client('peer_test', '127.0.0.1', '8.8.8.8', 'test.local', '0.0.0.0, ::/0')


if __name__ == "__main__":
    unittest.main()
