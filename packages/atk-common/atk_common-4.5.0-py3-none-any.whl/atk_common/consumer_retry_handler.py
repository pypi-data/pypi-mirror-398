from kombu import Producer
from atk_common.internal_response_utils import is_response_ok

def create_retry_handler(process_func, connection, exchange, routing_key, should_retry, log, declare=None):
    """
    process_func: your original handler function (body, message)
    retry_queue: kombu.Queue instance to republish to
    should_retry: function(message_status) -> bool
    log: function for logging
    """

    def handler(body, message):
        try:
            process_response = process_func(body, message)
            if is_response_ok(process_response):
                message.ack()
            else:
                if connection is not None:
                    # Use retry queue
                    if should_retry(process_response):
                        log("Retrying after delay...")
                        with connection.Producer() as producer:
                            producer.publish(
                                message.body,
                                exchange=exchange,
                                routing_key=routing_key,
                                retry=True,
                                declare=declare,
                                content_type=message.content_type,
                                content_encoding=message.content_encoding,
                                headers=message.headers,
                                timestamp=message.properties.get("timestamp")
                            )
                        message.ack()
                    else:
                        log("Sending to DLQ...")
                        message.reject(requeue=False)
                else:
                    if should_retry(process_response):
                        log("Requing...")
                        message.requeue()
                    else:
                        log("Sending to DLQ...")
                        message.reject(requeue=False)
        except Exception as e:
            log(f"Error during processing: {e}")
            message.reject(requeue=False)

    return handler
