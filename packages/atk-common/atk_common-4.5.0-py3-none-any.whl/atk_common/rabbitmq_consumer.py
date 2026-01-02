from kombu import Connection, Exchange, Queue, Consumer
import socket
import time

class RabbitMQConsumer:
    def __init__(self, queue_name, user, pwd, host, vhost, dlx, dlq, content_type, message_handler, log):

        rabbit_url = 'amqp://' + user + ':' + pwd + '@' + host + '/' + vhost

        self.connection = Connection(rabbit_url, heartbeat=10)
        if dlx is not None and dlq is not None:
            queue = Queue(name=queue_name,
                        queue_arguments={
                            'x-dead-letter-exchange': dlx, 
                            'x-dead-letter-routing-key': dlq},
                        )
        else:
            queue = Queue(name=queue_name)
        if content_type is not None:
            self.consumer = Consumer(self.connection, queues=queue, callbacks=[message_handler], accept=[content_type])
        else:
            self.consumer = Consumer(self.connection, queues=queue, callbacks=[message_handler], accept=None)
        self.consumer.consume()

        self.message_handler = message_handler  # Custom message handler
        self.log = log
    
    def consume(self):
        new_conn = self.establish_connection()
        while True:
            try:
                new_conn.drain_events(timeout=2)
            except socket.timeout:
                new_conn.heartbeat_check()

    def establish_connection(self):
        revived_connection = self.connection.clone()
        revived_connection.ensure_connection(max_retries=3)
        channel = revived_connection.channel()
        self.consumer.revive(channel)
        self.consumer.consume()
        self.log("Connection revived!")
        return revived_connection
        
    def run(self):
        while True:
            try:
                self.consume()
            except self.connection.connection_errors:
                pass

