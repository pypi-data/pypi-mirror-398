from kombu import Connection, Queue, Consumer
from kombu.exceptions import ConnectionError, ChannelError # Import relevant exceptions
import socket
import time
from atk_common.interfaces import ILogger
CONNECTION_ERRORS = (
    ConnectionError,
    ChannelError,
    OSError,
)

class RabbitMQConsumer:
    def __init__(self, queue_name, user, pwd, host, vhost, prefetch_count, dlx, dlq, content_type, message_handler, logger: ILogger):
        self.logger = logger

        rabbit_url = 'amqp://' + user + ':' + pwd + '@' + host + '/' + vhost
        self.logger.info(f"Initializing connection to RabbitMQ {queue_name} at {host}")

        self.connection = Connection(rabbit_url, heartbeat=10)
        if dlx is not None and dlq is not None:
            queue = Queue(name=queue_name,
                        queue_arguments={
                            'x-dead-letter-exchange': dlx, 
                            'x-dead-letter-routing-key': dlq},
                        )
        else:
            queue = Queue(name=queue_name)
        self.queue = queue
        self.content_type = content_type
        self.message_handler = message_handler
        self.prefetch_count = prefetch_count
    
    def _consume(self):
        conn = self._establish_connection()
        self.logger.info("Begin consuming messages...")

        while True:
            try:
                conn.drain_events(timeout=2)
                self.logger.debug("Drained event or heartbeat.")
            except socket.timeout:
                self.logger.debug("Socket timeout, checking heartbeat...")
                conn.heartbeat_check()
            except CONNECTION_ERRORS as e:
                self.logger.error(f"Connection lost: {e}. Reconnecting...")
                return  # break loop and re-establish connection
            except Exception as e:
                self.logger.error(f"Top-level exception in consume loop: {e}. Restarting after delay...")
                return

    def _establish_connection(self):
        revived_connection = self.connection.clone()
        revived_connection.ensure_connection(max_retries=3)
        channel = revived_connection.channel()

        consumer = Consumer(
            revived_connection, 
            queues=self.queue, 
            callbacks=[self.message_handler], 
            accept=[self.content_type] if self.content_type else None)
        consumer.revive(channel)
        consumer.consume()
        consumer.qos(prefetch_count=self.prefetch_count, apply_global=False)
        self.logger.info("Connection revived!")
        return revived_connection
        
    def run(self):
        self.logger.info("Starting RabbitMQ consumer run loop...")
        while True:
            try:
                self._consume()
            except Exception as e:
                self.logger.error(f"Top-level exception in run loop: {e}. Restarting after delay...")
                time.sleep(5)
