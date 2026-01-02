from kombu import Producer
from atk_common.interfaces import ILogger
from atk_common.utils.internal_response_utils import is_response_ok

"""
process_func: your original handler function (body, message)
connection: kombu.Connection instance to use for retrying (nullable)
exchange: kombu.Exchange instance to publish to (nullable)
routing_key: routing key for the exchange (nullable)
should_retry: function(message_status) -> bool
bo_logger: BoLogger instance for logging
declare: optional kombu.DeclarativeExchange or Queue to declare before publishing
"""
def create_retry_handler(process_func, connection, exchange, routing_key, should_retry, logger: ILogger, declare=None):

    def handler(body, message):
        try:
            retry_policy = {
                "max_retries": 5,
                "interval_start": 0.2,
                "interval_step": 0.5,
                "interval_max": 5,
            }
            process_response = process_func(body, message)
            if is_response_ok(process_response):
                message.ack()
            else:
                if connection is not None:
                    # Use retry queue
                    if should_retry(process_response):
                        logger.info("Retrying after delay...")
                        with connection.Producer() as producer:
                            producer.publish(
                                message.body,
                                exchange=exchange,
                                routing_key=routing_key,
                                retry=True,
                                retry_policy=retry_policy,
                                declare=declare,
                                content_type=message.content_type,
                                content_encoding=message.content_encoding,
                                headers=message.headers,
                                timestamp=message.properties.get("timestamp"),
                                mandatory=True,
                                delivery_mode=2
                            )
                        message.ack()
                    else:
                        logger.error("Sending to DLQ...")
                        message.reject(requeue=False)
                else:
                    if should_retry(process_response):
                        logger.error("Sending to DLQ...")
                        message.reject(requeue=False)
                    else:
                        logger.error("Discarding message...")
                        message.ack()
        except Exception as e:
            logger.error(f"Error during processing: {e}, sending to DLQ...")
            message.reject(requeue=False)

    return handler
