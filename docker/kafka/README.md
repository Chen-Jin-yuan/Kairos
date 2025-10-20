# env
python3
* `pip install kafka-python`

# run
* start: `docker-compose up -d`
* stop: `docker-compose down`

# check
* `docker exec -it {container id} /bin/bash`
* `kafka-topics.sh --describe --bootstrap-server {kafka_ip}:{kafka_port}`