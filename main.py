from __future__ import annotations
from austin_heller_repo.certificate_manager import CertificateManagerServer, Certificate
from austin_heller_repo.socket import ServerSocketFactory
from austin_heller_repo.common import HostPointer
import configparser
import time
from datetime import datetime
import os


if "DOCKER_IP" in os.environ:
	docker_ip = os.environ["DOCKER_IP"]
	print(f"Found DOCKER_IP: {docker_ip}")


config = configparser.ConfigParser()
config.read("./settings.ini")

server_socket_factory_config = config["ServerSocketFactory"]
to_client_packet_bytes_length = int(server_socket_factory_config["PacketBytesLength"])
listening_limit_total = int(server_socket_factory_config["ListeningLimitTotal"])
accept_timeout_seconds = float(server_socket_factory_config["AcceptTimeoutSeconds"])
host_address = server_socket_factory_config["HostAddress"]
host_port = int(server_socket_factory_config["HostPort"])
public_certificate_file_path = server_socket_factory_config["PublicCertificateFilePath"]
private_key_file_path = server_socket_factory_config["PrivateKeyFilePath"]

process_config = config["Process"]
sleep_seconds = float(process_config["SleepSeconds"])
is_interval_print = bool(process_config["IsIntervalPrint"])

certificate_config = config["Certificate"]
key_size = int(certificate_config["KeySize"])
certificate_name = certificate_config["Name"]
certificate_valid_days = int(certificate_config["ValidDays"])

if not os.path.exists(private_key_file_path) and not os.path.exists(public_certificate_file_path):
	print("Creating CA certificate...")
	self_signed_certificate = Certificate.create_self_signed_certificate(
		key_size=key_size,
		name=certificate_name,
		valid_days_total=certificate_valid_days
	)
	self_signed_certificate.save_to_file(
		private_key_file_path=private_key_file_path,
		signed_certificate_file_path=public_certificate_file_path
	)
	print("Created CA certificate")
elif os.path.exists(private_key_file_path) and os.path.exists(public_certificate_file_path):
	print("Found CA certificate")
else:
	raise Exception(f"Unexpected mismatch of private key and certificate file paths. One of these files is present while the other is missing.")

certificate_manager_server = CertificateManagerServer(
	server_socket_factory=ServerSocketFactory(
		to_client_packet_bytes_length=to_client_packet_bytes_length,
		listening_limit_total=listening_limit_total,
		accept_timeout_seconds=accept_timeout_seconds
	),
	server_host_pointer=HostPointer(
		host_address=host_address,
		host_port=host_port
	),
	public_certificate_file_path=public_certificate_file_path,
	private_key_file_path=private_key_file_path,
	certificate_valid_days=certificate_valid_days
)

certificate_manager_server.start_accepting_clients()

try:
	print_index = 0
	start_datetime = datetime.utcnow()
	while True:
		time.sleep(sleep_seconds)
		if is_interval_print:
			print(f"{datetime.utcnow()}: {print_index}: {(datetime.utcnow() - start_datetime).total_seconds()} seconds elapsed")
			print_index += 1
finally:
	certificate_manager_server.stop_accepting_clients()
