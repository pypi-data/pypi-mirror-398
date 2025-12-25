import os

import logfire
import rabbitpy
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt

from inoopa_utils.utils.exceptions import MissingEnvVariable

load_dotenv()


def _get_queue_name_with_env(queue_name: str) -> str:
    """Helper function to add the env name to the queue name."""
    env_name = os.getenv("ENV")
    if env_name is None:
        raise MissingEnvVariable("Missing env variable: ENV")
    return f"{queue_name}_{env_name}"


@retry(stop=stop_after_attempt(3))
def get_messages_from_queue(
    queue_name: str,
    queue_batch_size: int = 1,
    queue_host: str = os.environ["QUEUE_HOST"],
    queue_username: str = os.environ["QUEUE_USERNAME"],
    queue_password: str = os.environ["QUEUE_PASSWORD"],
) -> list[str | dict[str, str] | list[str] | list[dict[str, str]]]:
    """
    Helper function to get X messages from a rabbitMQ queue.\

    !!! Credentials should NOT be passed as params in this function! This is for development purpose only !!!
    You should use kubernetes secrets to get credentials from env variable (The default values of these params)
    """

    queue_name_with_env = _get_queue_name_with_env(queue_name)
    messages_body = []
    logfire.info(f"Connecting to queue: {queue_name_with_env}...")
    with rabbitpy.Connection(f"amqp://{queue_username}:{queue_password}@{queue_host}/%2f") as conn:
        with conn.channel() as channel:
            queue = rabbitpy.Queue(channel, queue_name_with_env, durable=True)
            queue.declare()
            logfire.info("Connected to queue, reading messages...")
            for i in range(queue_batch_size):
                message = queue.get(acknowledge=True)
                if message:
                    messages_body.append(message.body.decode())
                    # Tell the queue that this message has been read and should be removed from queue
                    message.ack()
                    logfire.info(f"Message {i + 1}/{queue_batch_size} read")
                else:
                    logfire.info("Queue empty, stoping...")
                    break
    return messages_body


@retry(stop=stop_after_attempt(3))
def push_to_queue(
    queue_name: str,
    messages: list[str | dict[str, str]],
    queue_host: str = os.environ["QUEUE_HOST"],
    queue_username: str = os.environ["QUEUE_USERNAME"],
    queue_password: str = os.environ["QUEUE_PASSWORD"],
) -> None:
    """Helper function to push a list of messages to a rabbitMQ queue."""

    queue_name_with_env = _get_queue_name_with_env(queue_name)

    logfire.info(f"Connecting to queue: {queue_name_with_env}...")
    with rabbitpy.Connection(f"amqp://{queue_username}:{queue_password}@{queue_host}/%2f") as conn:
        with conn.channel() as channel:
            queue = rabbitpy.Queue(channel, queue_name_with_env, durable=True)
            queue.declare()
            for i, message in enumerate(messages):
                logfire.debug(f"Pushing message {i + 1}/{len(messages)}")
                # Create a new message
                msg = rabbitpy.Message(channel, message)

                # Publish the message to the specified queue
                msg.publish("", queue_name_with_env)
    logfire.info(f"{len(messages)} Messages pushed to {queue_name_with_env}")


@retry(stop=stop_after_attempt(3))
def empty_queue(
    queue_name: str,
    queue_host: str = os.environ["QUEUE_HOST"],
    queue_username: str = os.environ["QUEUE_USERNAME"],
    queue_password: str = os.environ["QUEUE_PASSWORD"],
) -> None:
    """
    Helper function to remove all messages from a RabbitMQ queue.
    """

    queue_name_with_env = _get_queue_name_with_env(queue_name)
    logfire.info(f"Purging queue: {queue_name_with_env}")
    with rabbitpy.Connection(f"amqp://{queue_username}:{queue_password}@{queue_host}/%2f") as conn:
        with conn.channel() as channel:
            queue = rabbitpy.Queue(channel, queue_name_with_env, durable=True)
            queue.declare()
            message_count = queue.purge()
        logfire.info(f"Removed {message_count} messages from queue: {queue_name_with_env}")
        logfire.info("Queue empty!")
