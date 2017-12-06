# MQTT

import ssl
import paho.mqtt.client as mqtt
import logging


class MqttConnection(object):

    def __init__(self, settings, topics=list()):
        self._ip = settings["brokeraddress"]
        self._port = settings["brokerport"]
        self._topics = dict()
        self._parseTopics(topics)

        self._mqttc = mqtt.Client()

        if "brokerusername" in settings:
            self._mqttc.username_pw_set(settings["brokerusername"], settings["brokerpassword"])

        if settings["brokerssl"]:
            self._mqttc.tls_set(ca_certs=settings["cafilepath"],certfile=settings["certfilepath"],
                                keyfile=settings["keyfilepath"], cert_reqs=ssl.CERT_NONE)
            self._mqttc.tls_insecure_set(True)

        self._mqttc.on_message = self._onmessage
        self._mqttc.on_disconnect = self._ondisconnect
        logging.debug('MQTTClient initialized')

    def _parseTopics(self, topics):
        for topic in topics:
            self._topics[topic] = ''

    def connect(self):
        self._mqttc.connect(self._ip, self._port)
        for topic in self._topics:
            self._mqttc.subscribe(topic, 0)
        self._mqttc.loop_start()
        logging.debug('MQTTClient connected')

    def disconnect(self):
        self._mqttc.loop_stop(True)
        logging.debug('MQTTClient disconnected')

    def publish(self, topic, payload=None, retain=False):
        a, b = self._mqttc.publish(topic, payload, retain=retain)
        if a != mqtt.MQTT_ERR_SUCCESS:
            try:
                self.connect()
            except Exception:
                pass
        return a == mqtt.MQTT_ERR_SUCCESS

    def raw_publish(self, topic, payload=None, retain=False):
        a, b = self._mqttc.publish(topic, payload, retain=retain)
        return a == mqtt.MQTT_ERR_SUCCESS

    def getMessage(self, topic):
        return self._topics[topic] if topic in self._topics else None

    def _onmessage(self, mqttc, obj, msg):
        logging.debug('onMessage() %s %s' % (str(msg.topic), str(msg.payload)))
        # print('onMessage %s' % str(isinstance(msg.payload, str))) # TODO
        # bytes
        if isinstance(msg.payload, bytes):
            # we want strings !
            msg.payload = msg.payload.decode('utf-8')

        if msg.topic in self._topics:
            self._topics[msg.topic] = msg.payload

    def _ondisconnect(self, mqttc, userdata, rc):
        self._connected = False
        if rc != 0:
            logging.debug('onDisconnected() -> error! Reconnecting...')
            self.connect()
