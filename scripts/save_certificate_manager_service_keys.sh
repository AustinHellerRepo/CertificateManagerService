# pulls the saved private key and public certificate from the running container so that it can be pulled by the container the next time it is started

docker cp certificate_manager_service:/app/ssl/cert.pem ../ssl/cert.pem
docker cp certificate_manager_service:/app/ssl/cert.key ../ssl/cert.key
