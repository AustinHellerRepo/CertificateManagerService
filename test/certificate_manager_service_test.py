import unittest
from austin_heller_repo.certificate_manager import CertificateManagerClient, Certificate
from austin_heller_repo.socket import ClientSocketFactory, ClientSocket, ServerSocket
from austin_heller_repo.common import HostPointer
import tempfile
import time
import uuid


def get_default_certificate_manager_client() -> CertificateManagerClient:

	return CertificateManagerClient(
		client_socket_factory=ClientSocketFactory(
			to_server_packet_bytes_length=4096
		),
		server_host_pointer=HostPointer(
			host_address="172.17.0.1",
			host_port=35123
		)
	)


class CertificateManagerServiceTest(unittest.TestCase):

	def test_initialize(self):

		certificate_manager_client = get_default_certificate_manager_client()

		self.assertIsNotNone(certificate_manager_client)

	def test_get_root_certificate(self):

		certificate_manager_client = get_default_certificate_manager_client()

		root_certificate_tempfile = tempfile.NamedTemporaryFile(
			delete=False
		)

		with open(root_certificate_tempfile.name, "rb") as file_handle:
			root_certificate_bytes = file_handle.read()

		self.assertEqual(0, len(root_certificate_bytes))

		certificate_manager_client.get_root_certificate(
			save_to_file_path=root_certificate_tempfile.name
		)

		with open(root_certificate_tempfile.name, "rb") as file_handle:
			root_certificate_bytes = file_handle.read()

		self.assertNotEqual(0, len(root_certificate_bytes))

		root_certificate_tempfile.close()

	def test_create_certificate(self):

		certificate_manager_client = get_default_certificate_manager_client()

		certificate = certificate_manager_client.request_certificate(
			name="test"
		)

		self.assertIsNotNone(certificate)

	def test_socket_connection(self):

		certificate_manager_client = get_default_certificate_manager_client()

		client_certificate = certificate_manager_client.request_certificate(
			name="0.0.0.0"
		)

		print(client_certificate.get_signed_certificate().subject)
		print(client_certificate.get_signed_certificate().issuer)
		print(client_certificate.get_private_key())

		# NOTE localhost is the only thing that seems to work
		# 	these fail: "192.168.0.1", "127.0.0.1", "0.0.0.0", and empty string
		server_address = "localhost"  # works
		#server_address = "0.0.0.0"  # does not work, IP not valid
		#server_address = "192.168.0.1"  # does not work, connection times out
		#server_address = "127.0.0.1"  # does not work, IP not valid
		#server_address = "cert_test"  # works, temporary addition to /etc/hosts file that maps to 127.0.0.1

		server_certificate = certificate_manager_client.request_certificate(
			name=server_address
		)

		print(server_certificate.get_signed_certificate().subject)
		print(server_certificate.get_signed_certificate().issuer)
		print(server_certificate.get_private_key())

		root_certificate_tempfile = tempfile.NamedTemporaryFile(
			delete=False
		)

		certificate_manager_client.get_root_certificate(
			save_to_file_path=root_certificate_tempfile.name
		)

		with open(root_certificate_tempfile.name, "rb") as file_handle:
			print(file_handle.read())

		time.sleep(1)

		client_private_key_tempfile = tempfile.NamedTemporaryFile(
			delete=False
		)

		client_signed_certificate_tempfile = tempfile.NamedTemporaryFile(
			delete=False
		)

		client_certificate.save_to_file(
			private_key_file_path=client_private_key_tempfile.name,
			signed_certificate_file_path=client_signed_certificate_tempfile.name
		)

		server_private_key_tempfile = tempfile.NamedTemporaryFile(
			delete=False
		)

		server_signed_certificate_tempfile = tempfile.NamedTemporaryFile(
			delete=False
		)

		server_certificate.save_to_file(
			private_key_file_path=server_private_key_tempfile.name,
			signed_certificate_file_path=server_signed_certificate_tempfile.name
		)

		server_socket = ServerSocket(
			to_client_packet_bytes_length=4096,
			listening_limit_total=10,
			accept_timeout_seconds=1.0,
			ssl_private_key_file_path=server_private_key_tempfile.name,
			ssl_certificate_file_path=server_signed_certificate_tempfile.name,
			root_ssl_certificate_file_path=root_certificate_tempfile.name
		)

		expected_message = str(uuid.uuid4())

		def on_accepted_client_method(client_socket: ClientSocket):
			nonlocal expected_message
			print(f"Client connected!")
			actual_message = client_socket.read()
			self.assertEqual(expected_message, actual_message)
			client_socket.close()

		server_socket.start_accepting_clients(
			host_ip_address="0.0.0.0",
			host_port=36451,
			on_accepted_client_method=on_accepted_client_method
		)

		time.sleep(1)

		client_socket = ClientSocket(
			packet_bytes_length=4096,
			ssl_private_key_file_path=client_private_key_tempfile.name,
			ssl_certificate_file_path=client_signed_certificate_tempfile.name,
			root_ssl_certificate_file_path=root_certificate_tempfile.name
		)

		client_socket.connect_to_server(
			ip_address=server_address,
			port=36451
		)

		client_socket.write(expected_message)

		time.sleep(1)

		client_socket.close()

		server_socket.stop_accepting_clients()

		server_socket.close()

		time.sleep(1)

		root_certificate_tempfile.close()
		client_private_key_tempfile.close()
		client_signed_certificate_tempfile.close()
		server_private_key_tempfile.close()
		server_signed_certificate_tempfile.close()
