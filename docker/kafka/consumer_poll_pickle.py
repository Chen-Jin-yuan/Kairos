from kafka import KafkaConsumer
import time
import pickle
from msg import Msg

consumer = KafkaConsumer(
    'test_topic',
    bootstrap_servers='[kafka_ip]:[kafka_port]',
    group_id='my_group',
    key_deserializer=lambda k: k.decode('utf-8'),
    value_deserializer=lambda v: pickle.loads(v)
)


while True:
    messages = consumer.poll(timeout_ms=10)
    if not messages:
        print("No message, doing other tasks...")
        time.sleep(1)
        continue

    for topic_partition, records in messages.items():
        for message in records:
            key = message.key
            value = message.value
            print(value)
            text_message = value.input_data['text']
            print(f'Received text: {text_message} with key: {key}')
            print(value.key)

    consumer.commit()
