import socket
import unittest
from unittest.mock import patch, MagicMock
from update_route53 import (
    Route53Updater,
    get_localhost,
    request_address,
    get_public_ip,
    get_domain_from_fqdn,
    register_ip,
    main_func
)

class TestRoute53Updater(unittest.TestCase):
    @patch('update_route53.boto3')
    def test_init_creates_client(self, mock_boto3):
        rup = Route53Updater()
        mock_boto3.client.assert_called_once_with('route53')
        self.assertEqual(rup.client, mock_boto3.client.return_value)

    @patch('update_route53.boto3')
    def test_get_hosted_zone_id_for_domain(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_response = {
            'HostedZones': [{
                'Name': 'example.com.',
                'Id': 'zone1'
            }]
        }
        mock_client.list_hosted_zones_by_name.return_value = mock_response
        rup = Route53Updater()
        ret = rup.get_hosted_zone_id_for_domain('example.com')
        self.assertEqual(ret, 'zone1')

    @patch('update_route53.boto3')
    def test_upsert_name_with_ip(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        mock_client.change_resource_record_sets.return_value = 'fake_return'
        rup = Route53Updater()
        ret = rup.upsert_name_with_ip('zone1', 'test.example.com', '10.10.1.1')
        self.assertEqual(ret, 'fake_return')

    @patch('update_route53.socketcontext')
    def test_get_localhost(self, mock_socketcontext):
        mock_context = MagicMock()
        mock_socketcontext.return_value = mock_context
        mock_socket = MagicMock()
        mock_context.__enter__.return_value = mock_socket
        mock_socket.getsockname.return_value = ['mocked_socket_name']
        ret = get_localhost()
        mock_socketcontext.assert_called_once_with(socket.AF_INET, socket.SOCK_DGRAM)
        mock_socket.connect.assert_called_once_with(('8.8.8.8', 80))
        mock_socket.getsockname.assert_called_once_with()
        self.assertEqual(ret, 'mocked_socket_name')

    @patch('update_route53.urlopen')
    @patch('update_route53.Request')
    def test_request_address(self, mock_request, mock_urlopen):
        mock_response = MagicMock()
        mock_urlopen.return_value = mock_response
        url = 'https://ifconfig.co/ip'
        headers = { 'User-Agent' : 'update-route53/1.0' }
        ret = request_address()
        mock_request.assert_called_once_with(url, headers=headers)
        mock_urlopen.assert_called_once_with(mock_request.return_value)
        self.assertEqual(ret, mock_response.read.return_value.decode.return_value.strip.return_value)

    @patch('update_route53.request_address')
    @patch('update_route53.get_localhost')
    def test_get_public_ip__uses_public_localhost(self, mock_get_localhost, mock_request_address):
        public_ip = '8.8.8.8'
        mock_get_localhost.return_value = public_ip
        ret = get_public_ip()
        self.assertEqual(ret, public_ip)
        mock_get_localhost.assert_called_once_with()
        mock_request_address.assert_not_called()

    @patch('update_route53.request_address')
    @patch('update_route53.get_localhost')
    def test_get_public_ip__queries_private_localhost(self, mock_get_localhost, mock_request_address):
        private_ip = '10.10.10.10'
        mock_get_localhost.return_value = private_ip
        public_ip = 'public_address'
        mock_request_address.return_value = public_ip
        ret = get_public_ip()
        self.assertEqual(ret, public_ip)
        mock_get_localhost.assert_called_once_with()
        mock_request_address.assert_called_once_with()

    def test_get_domain_from_fqdn(self):
        test_domains = {
            'subdomain.subdomain.domain.com.': 'domain.com',
            'foo.bar.co.uk.': 'bar.co.uk',
            'myhome.mydomain.com': 'mydomain.com',
            'foo.bar.baz.com.mx': 'baz.com.mx',
            'domain.org': 'domain.org'
        }
        for test_fqdn, expected in test_domains.items():
            with self.subTest(test_fqdn=test_fqdn):
                self.assertEqual(get_domain_from_fqdn(test_fqdn), expected)

    @patch('update_route53.print')
    @patch('update_route53.Route53Updater')
    def test_register_ip__updates_for_always(self, mock_route53_updater, mock_print):
        mock_rup = MagicMock()
        mock_route53_updater.return_value = mock_rup
        mock_rup.get_hosted_zone_id_for_domain.return_value = 'zone1'
        mock_rup.check_dns.return_value = False
        mock_rup.upsert_name_with_ip.return_value = 'upsert_return'
        register_ip('test.example.com', 'fake_ip_address', True)
        mock_print.assert_called_once_with('upsert_return')
        mock_rup.upsert_name_with_ip.assert_called_once_with('zone1', 'test.example.com', 'fake_ip_address')
        mock_rup.check_dns.assert_not_called()
        mock_rup.get_hosted_zone_id_for_domain.assert_called_once_with('example.com')

    @patch('update_route53.print')
    @patch('update_route53.Route53Updater')
    def test_register_ip__skips_unnecessary_update_when_not_always(self, mock_route53_updater, mock_print):
        mock_rup = MagicMock()
        mock_route53_updater.return_value = mock_rup
        mock_rup.get_hosted_zone_id_for_domain.return_value = 'zone1'
        mock_rup.check_dns.return_value = True
        register_ip('test.example.com', 'fake_ip_address', False)
        mock_print.assert_called_once_with('Not updating, no change detected.')
        mock_rup.upsert_name_with_ip.assert_not_called()
        mock_rup.check_dns.assert_called_once_with('test.example.com', 'fake_ip_address')
        mock_rup.get_hosted_zone_id_for_domain.assert_called_once_with('example.com')

    @patch('update_route53.print')
    @patch('update_route53.Route53Updater')
    def test_register_ip__update_change_when_not_always(self, mock_route53_updater, mock_print):
        mock_rup = MagicMock()
        mock_route53_updater.return_value = mock_rup
        mock_rup.get_hosted_zone_id_for_domain.return_value = 'zone1'
        mock_rup.check_dns.return_value = False
        mock_rup.upsert_name_with_ip.return_value = 'upsert_return'
        register_ip('test.example.com', 'fake_ip_address', False)
        mock_print.assert_called_once_with('upsert_return')
        mock_rup.upsert_name_with_ip.assert_called_once_with('zone1', 'test.example.com', 'fake_ip_address')
        mock_rup.check_dns.assert_called_once_with('test.example.com', 'fake_ip_address')
        mock_rup.get_hosted_zone_id_for_domain.assert_called_once_with('example.com')

    @patch('update_route53.get_public_ip')
    @patch('update_route53.register_ip')
    @patch('update_route53.argparse.ArgumentParser')
    def test_main_func__uses_args(self, mock_argparser, mock_register_ip, mock_get_public_ip):
        mock_get_public_ip.return_value = '10.1.1.1'
        mock_args = MagicMock()
        mock_argparser.return_value.parse_args.return_value = mock_args
        mock_args.ip = '10.1.2.3'
        mock_args.name = 'test.example.com'
        mock_args.always = False
        main_func()
        mock_register_ip.assert_called_once_with('test.example.com', '10.1.2.3', False)
        mock_get_public_ip.assert_not_called()

    @patch('update_route53.get_public_ip')
    @patch('update_route53.register_ip')
    @patch('update_route53.argparse.ArgumentParser')
    def test_main_func__uses_get_public_ip_by_default(self, mock_argparser, mock_register_ip, mock_get_public_ip):
        mock_get_public_ip.return_value = '10.1.1.1'
        mock_args = MagicMock()
        mock_argparser.return_value.parse_args.return_value = mock_args
        mock_args.ip = None
        mock_args.name = 'test.example.com'
        mock_args.always = True
        main_func()
        mock_register_ip.assert_called_once_with('test.example.com', '10.1.1.1', True)
        mock_get_public_ip.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
