import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.message import Message
from framework.message import BaseMessageHandler

class TestMessageHandler(BaseMessageHandler):
    def initialize(self, **kwargs):
        ip = kwargs.get('ip')
        connection_string = kwargs.get('connection', 'default_connection')
        print(f"Initializing with ip: {ip}, connection: {connection_string}")

    def _generate_channel_from_target(self, target_name: str):
        return f"channel_for_{target_name}"

    def send(self, message: Message, target_name: str):
        target_channel = self.target_map.get(target_name)
        if target_channel:
            print(f"Sending message '{message.service_name}' to {target_channel}")
        else:
            print(f"Error: target '{target_name}' not found.")

    def recv(self):
        print(f"Receiving message")
        return Message(id=1, service_name=f"Message Service", msg_type="event")

    def close(self):
        pass

if __name__ == "__main__":
    handler = TestMessageHandler()
    handler.initialize(ip = "192.0.0.1", connection="topic1")

    handler.add_target_mapping("TargetA")
    handler.add_target_mappings(["TargetB", "TargetC"])

    print("Target map:", handler.target_map)

    message_a = Message(id=0, service_name="ServiceA", msg_type="event")
    handler.send(message_a, "TargetA")

    received_message = handler.recv()
    if received_message:
        print("Received message:", received_message.get_service_name())

    handler.send(message_a, "NonExistentTarget1")
    print("ending")