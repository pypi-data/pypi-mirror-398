# topdogalerts/publisher/sqs.py
"""
SQS message publisher for topdogalerts.

Publishes JSON messages to an AWS SQS queue.
"""
import json
import os
from typing import Any, Mapping, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class SqsPublisher:
    """
    Publish JSON messages to an SQS queue.

    Configuration via environment variables:
        EVENT_QUEUE_URL  (required) - The SQS queue URL
        AWS_REGION       (optional) - AWS region (can also come from AWS config)

    Example:
        publisher = SqsPublisher()
        message_id = publisher.publish({"trigger_id": 123, "attributes": {...}})
    """

    def __init__(
        self,
        queue_url: Optional[str] = None,
        region_name: Optional[str] = None,
    ) -> None:
        """
        Initialize the SQS publisher.

        Args:
            queue_url: The SQS queue URL. If not provided, uses EVENT_QUEUE_URL env var.
            region_name: AWS region. If not provided, uses AWS_REGION env var or AWS config.

        Raises:
            ValueError: If queue_url is not provided and EVENT_QUEUE_URL is not set.
        """
        self.queue_url = queue_url or os.getenv("EVENT_QUEUE_URL")
        if not self.queue_url:
            raise ValueError(
                "EVENT_QUEUE_URL env var is required or queue_url must be passed to SqsPublisher()."
            )

        self.region_name = region_name or os.getenv("AWS_REGION")

        session = boto3.Session(region_name=self.region_name)
        self.sqs = session.client("sqs")

    def publish(
        self,
        message: Mapping[str, Any],
        *,
        message_group_id: Optional[str] = None,
        message_deduplication_id: Optional[str] = None,
    ) -> str:
        """
        Publish a JSON message to SQS.

        Args:
            message: A JSON-serializable mapping to publish.
            message_group_id: Optional message group ID for FIFO queues.
            message_deduplication_id: Optional deduplication ID for FIFO queues.

        Returns:
            The SQS MessageId of the published message.

        Raises:
            ValueError: If the message is not JSON-serializable.
            RuntimeError: If the SQS publish fails.
        """
        try:
            body = json.dumps(
                message,
                separators=(",", ":"),
                default=str,
            )
        except (TypeError, ValueError) as e:
            raise ValueError(f"Message is not JSON-serializable: {e}") from e

        params = {
            "QueueUrl": self.queue_url,
            "MessageBody": body,
        }

        if message_group_id:
            params["MessageGroupId"] = message_group_id
        if message_deduplication_id:
            params["MessageDeduplicationId"] = message_deduplication_id

        try:
            resp = self.sqs.send_message(**params)
        except (BotoCoreError, ClientError) as e:
            raise RuntimeError(f"Failed to publish message to SQS: {e}") from e

        return resp.get("MessageId", "")
