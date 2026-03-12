import paho.mqtt.client as mqtt
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisMQTT:
    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client(client_id="jarvis_brain", clean_session=False)
        self.broker = broker
        self.port = port
        self.callbacks = {}
        self.subscribed_topics = {}
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
    def _on_connect(self, client, userdata, flags, rc):
        logger.info(f"Connected to MQTT broker (rc={rc})")
        
        # Re-subscribe to all topics on reconnect
        for topic in self.subscribed_topics:
            self.client.subscribe(topic)
            logger.info(f"Re-subscribed to: {topic}")
        
    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode()
        logger.info(f"Received: {topic} = {payload}")
        
        if topic in self.callbacks:
            self.callbacks[topic](topic, payload)
    
    def connect(self):
        self.client.connect(self.broker, self.port, keepalive=3600)  # 1 hour keepalive
        self.client.loop_start()
        
    def subscribe(self, topic, callback):
        self.callbacks[topic] = callback
        self.subscribed_topics[topic] = True
        self.client.subscribe(topic)
        logger.info(f"Subscribed to: {topic}")
        
    def publish(self, topic, payload):
        self.client.publish(topic, str(payload))
        logger.info(f"Published: {topic} = {payload}")
