import asyncio
import logging

from amqtt.client import MQTTClient, ConnectException
from readings import NFCReading
from amqtt.mqtt.constants import QOS_2

logger = logging.getLogger(__name__)


class Publisher:
    """
    An asynchronous class to forward any readings in the provided queue to a configured broker.

    The Publisher class takes an asynchronous queue that gets populated by NFCReading objects, publishing the readings
    to a mqtt broker.
    """

    def __init__(self, queue: asyncio.Queue[NFCReading]):
        self._queue = queue
        self._publish_topic = ""
        self._broker_address = ""
        self._OldPayload = ""

        try:
            with open("payload.txt", "r") as file:
                self._OldPayload = file.read()

        except FileNotFoundError:
            logger.error("Error, payload.txt not found")

        except OSError as e:
            logger.error("Error with opening payload.txt file")

        try:
            with open('config.txt', 'r') as file:
                lines = file.readlines()  # Returns a list where each element is a line
                self._broker_address = lines[0].strip()
                self._publish_topic = lines[1].strip()
                logger.debug(f"Broker IP {self._broker_address}, and Topic {self._publish_topic}")

        except FileNotFoundError:
            logger.error("Error, config.txt not found")
            raise

        except OSError as e:
            logger.error("Error with opening config.txt file")
            raise

    async def publish(self, readings: list[NFCReading]) -> bool:
        """
        Publish the given readings to the broker address

        The sample format of the payload to be sent and received by the broker (tentative):
        QUESTg107af419hb41414
        USER14f8971da4984B5
        USER1414fa1441d555
        USER148arf9714faf9845
        QUESTg152181hkdf9814
        USER14f8971drFrt3145
        USER1414BdD2145e14
        USER148arf9714faf9845

        ... and so on

        :param readings: The readings to publish to the broker
        :return: True if successful
        """

        current_quest = ""
        # Open the file in read mode and read the string
        payload = self._OldPayload

        for s in readings:
            if s.quest_id != current_quest:
                current_quest = s.quest_id
            payload += s.quest_string() + "\n"
            payload += s.user_string() + "\n"

            # print(f"Generated NFCReading: user_id={s.user_id}")
        # print(payload)
        logger.debug(payload)
        battah = await self.publish_with_qos_2(self._broker_address, self._publish_topic, payload)
        return battah

    # TODO Publish every 30 seconds
    # TODO Handle cases where publishing fails due to connection errors
    async def publish_forever(self) -> None:
        """
        Loops forever waiting for readings and publishing to the mqtt broker
        :return: None
        """
        while True:
            readings = []
            await asyncio.sleep(8)
            if self._queue.empty():
                logger.debug("No readings to publish")
                continue
            while not self._queue.empty():
                readings.append(await self._queue.get())
            await self.publish(readings)

    async def publish_with_qos_2(self, broker_url, topic, payload):
        mqtt_config = {
            "keep_alive": 20,
            "ping_delay": 1,
            "reconnect_retries": 5,
            "reconnect_max_interval": 3,
        }

        client = None

        try:
            # Initialize MQTTClient
            client = MQTTClient()
            # print("MQTTClient initialized.")

            # Connect to the broker
            # print("Attempting to connect...")
            await client.connect(broker_url)
            # print(f"Connected to broker: {broker_url}")
            logger.debug(f"Connected to broker: {broker_url}")

            # Validate and encode the payload
            if not payload or not isinstance(payload, str):
                raise ValueError("Payload must be a non-empty string.")
            encoded_payload = payload.encode()
            # print(f"Payload encoded: {encoded_payload}")

            # Publish the message
            await client.publish(topic, encoded_payload, qos=QOS_2)
            # print(f"Message published to topic '{topic}' with QoS 2.")
            # f"Message published to topic"
            logger.info(f"Message published to topic {topic}")
            logger.debug(f"{encoded_payload} sent to {topic}")
            self._OldPayload = ""
            with open("Payload.txt", "w") as file:
                # Write the desired string to the file
                file.write("")
            return True

        except ConnectException as e:
            # print(f"ConnectException occurred: {e}")
            logger.error("Error connecting to Broker")
            self._OldPayload = payload
            with open("Payload.txt", "w") as file:
                # Write the desired string to the file
                file.write(payload)
            return False

        except AttributeError as e:
            # print(f"AttributeError: {e}. Possible uninitialized or invalid client.")
            logger.error(f"Error {e}")
            self._OldPayload = payload
            with open("Payload.txt", "w") as file:
                # Write the desired string to the file
                file.write(payload)
            return False

        except Exception as e:
            # print(f"Unexpected error: {e}")
            logger.error(f"Error {e}")
            self._OldPayload = payload
            with open("Payload.txt", "w") as file:
                # Write the desired string to the file
                file.write(payload)
            return False

        finally:
            if client is not None:
                try:
                    await client.disconnect()
                    # print("Disconnected from broker.")
                    logger.debug(f"Disconnected From Broker")
                except Exception as e:
                    # print(f"Error during disconnection: {e}")
                    logger.debug(f"Error during disconnection: {e}")
            # else:
            #     print("Client was not initialized properly.")