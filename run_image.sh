docker run --name certificate_manager_service -p 35123:35123 -e "DOCKER_IP=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+')" --rm certificate_manager_service
