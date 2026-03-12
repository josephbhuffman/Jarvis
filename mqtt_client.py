import paho.mqtt.client as mqtt
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisMQTT:
    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client(client_id="jarvis_brain", clean_session=False)
        self.client.reconnect_delay_set(min_delay=1, max_delay=120)
        self.broker = broker
        self.port = port
        self.callbacks = {}
        self.subscribed_topics = {}
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
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
    
    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnect (rc={rc}), will reconnect automatically")
    
    def connect(self):
        self.client.connect(self.broker, self.port, keepalive=3600)
        self.client.loop_start()
        
    def subscribe(self, topic, callback):
        self.callbacks[topic] = callback
        self.subscribed_topics[topic] = True
        self.client.subscribe(topic)
        logger.info(f"Subscribed to: {topic}")
        
    def publish(self, topic, payload):
        result = self.client.publish(topic, str(payload), qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Published: {topic} = {payload}")
        else:
            logger.error(f"Publish failed: {topic} (rc={result.rc})")
