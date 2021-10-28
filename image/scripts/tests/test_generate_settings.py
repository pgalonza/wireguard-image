"""
Testing generate_settings
"""

import logging
import unittest
import unittest.mock
import generate_settings


class TestWireGuard(unittest.TestCase):
    """
    Class for testing WireGuard.
    """

    def setUp(self) -> None:
        generate_settings.logging.disable(logging.INFO)
        generate_settings.logging.disable(logging.ERROR)

    def test_interface_name_eth(self):
        """
        Testing to find eth0 interface
        """

        with unittest.mock.patch('generate_settings.os.listdir') as ld_mock:
            ld_mock.return_value = ('lo', 'eth0', 'eth')
            wg_interface = generate_settings.WireGuard('', '')
            result = wg_interface._get_interface_name()
            self.assertEqual(result, 'eth0')

    def test_interface_name_ens(self):
        """
        Testing to find ens0 interface
        """

        with unittest.mock.patch('generate_settings.os.listdir') as ld_mock:
            ld_mock.return_value = ('lo', 'ens3', 'ens')
            wg_interface = generate_settings.WireGuard('', '')
            result = wg_interface._get_interface_name()
            self.assertEqual(result, 'ens3')

    def test_interface_name_error(self):
        """
        Testing if does not find interface.
        """

        with unittest.mock.patch('generate_settings.os.listdir') as ld_mock:
            ld_mock.return_value = ('lo', 'ens', 'enh', 'ens4', 'eth1')
            wg_interface = generate_settings.WireGuard('', '')
            result = wg_interface._get_interface_name()
            self.assertIsNone(result)

    def test_server_configuration(self):
        """
        Testing create configuration for  server.
        """

        with unittest.mock.patch('generate_settings.wgconfig.wgexec.generate_keypair') as gk_mock:
            gk_mock.return_value = ('private_key', 'public_key')
            with unittest.mock.patch('generate_settings.wgconfig.WGConfig.write_file'):
                mock_gin = unittest.mock.Mock()
                mock_gin.return_value = 'eth0'
                wg_interface = generate_settings.WireGuard('', '')
                wg_interface._get_interface_name = mock_gin
                wg_interface.create_server_configuration('127.0.0.1', '51820')
                self.assertEqual(len(wg_interface.lines), 7)

    @staticmethod
    def test_client_configuration() -> None:
        """
        Testing add new client.
        """

        with unittest.mock.patch('generate_settings.wgconfig.wgexec.generate_keypair') as gk_mock:
            gk_mock.return_value = ('private_key', 'public_key')
            with unittest.mock.patch('generate_settings.wgconfig.WGConfig.write_file'):
                with unittest.mock.patch('generate_settings.os.mkdir'):
                    with unittest.mock.patch('generate_settings.qrcode.make'):
                        with unittest.mock.patch('generate_settings.tinydb'):
                            wg_interface = generate_settings.WireGuard('', '')
                            wg_interface.server_public_key = 'public_key'
                            wg_interface.add_client('peer_test', ('192.168.0.2/24', '192.168.0.2/32',),
                                                    '8.8.8.8', 'test.local', '0.0.0.0, ::/0')


if __name__ == "__main__":
    unittest.main()
