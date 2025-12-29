import logging

from django.utils import timezone

try:
    from firebase_admin import messaging
except ImportError as e:
    raise RuntimeError(
        "idtinc.firebase requires 'firebase-admin'. "
        "Install with: pip install idtinc[firebase]"
    ) from e


logger = logging.getLogger("exception")


class FirebaseMessage:

    @classmethod
    def send_to_device(cls, device_id, title, body, data=None):
        if not device_id:
            return

        if not data:
            data = {}

        if isinstance(data, dict):
            if "message" not in data:
                data["message"] = body

            for key, value in data.items():
                data[key] = str(value) if value is not None else ""

        data["created_at"] = timezone.now().isoformat()

        notification = messaging.Notification(
            title=title,
            body=body,
        )

        message = messaging.Message(
            data=data,
            notification=notification,
            token=device_id,
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        content_available=True,
                    )
                )
            ),
        )

        try:
            messaging.send(message)
        except messaging.UnregisteredError:
            logger.error(f"Token {device_id} is invalid or not registered")
        except Exception as e:
            logger.error(f"Failed to send FCM message: {e}")

    @classmethod
    def send_each_for_multicast(cls, device_ids: list, title, body, data=None):
        if not device_ids:
            return

        try:
            if not data:
                data = {}

            if isinstance(data, dict):
                if "message" not in data:
                    data["message"] = body

                for key, value in data.items():
                    data[key] = str(value) if value is not None else ""

            data["created_at"] = timezone.now().isoformat()

            registration_tokens = device_ids

            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                tokens=registration_tokens,
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            content_available=True,
                        )
                    )
                ),
                data=data,
            )

            response = messaging.send_each_for_multicast(message)
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        logger.error(
                            f"{idx}/{len(registration_tokens) - 1}: "
                            f"Error sending message to {registration_tokens[idx]}: {resp.exception}"
                        )

        except messaging.UnregisteredError:
            logger.error(f"Token {device_ids} is invalid or not registered")
        except Exception as e:
            logger.error(f"Failed to send FCM message: {e}")

    @classmethod
    def subscribe_to_topic(cls, device_ids, topic):
        try:
            response = messaging.subscribe_to_topic(device_ids, topic)

            result = {
                "failure_count": response.failure_count,
                "success_count": response.success_count,
                "errors": [],
            }

            if response.failure_count > 0:
                for error in response.errors:
                    token = device_ids[error.index]
                    result["errors"].append(
                        {
                            "index": error.index,
                            "reason": error.reason,
                            "token": token,
                        },
                    )

            return result
        except Exception as e:
            logger.error(f"Failed to subscribe devices to topic {topic}: {e}")
            return {
                "failure_count": len(device_ids),
                "success_count": 0,
                "error": str(e),
            }

    @classmethod
    def unsubscribe_from_topic(cls, device_ids, topic):
        try:
            response = messaging.unsubscribe_from_topic(device_ids, topic)

            result = {
                "failure_count": response.failure_count,
                "success_count": response.success_count,
                "errors": [],
            }

            if response.failure_count > 0:
                for error in response.errors:
                    token = device_ids[error.index]
                    result["errors"].append(
                        {
                            "index": error.index,
                            "reason": error.reason,
                            "token": token,
                        }
                    )

            return result
        except Exception as e:
            logger.error(f"Failed to unsubscribe devices from topic {topic}: {e}")
            return {
                "failure_count": len(device_ids),
                "success_count": 0,
                "error": str(e),
            }

    @classmethod
    def send_to_topic(cls, topic, title, body, data=None):
        try:
            if isinstance(data, dict):
                if "message" not in data:
                    data["message"] = body

                for key, value in data.items():
                    data[key] = str(value) if value is not None else ""

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                topic=topic,
                data=data or {},
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            content_available=True,
                        )
                    )
                ),
            )

            messaging.send(message)
        except Exception as e:
            logger.error(f"Failed to send message to topic {topic}: {e}")
            raise e
