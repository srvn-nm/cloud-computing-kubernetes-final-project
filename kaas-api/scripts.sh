docker build . -t kaas-sarvin-abtin
minikube start
docker-compose up -d
docker-compose logs