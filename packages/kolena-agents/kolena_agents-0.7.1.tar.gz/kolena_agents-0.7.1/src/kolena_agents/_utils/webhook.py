import hashlib
import hmac
import json
import random
import string
import time
import uuid
from typing import Any
from typing import Mapping
from typing import Union

import urllib3

from kolena_agents._generated.openapi_client import AgentRun  # type: ignore
from kolena_agents._generated.openapi_client import ClientApi  # type: ignore
from kolena_agents._utils.client import _get_client

X_KOLENA_SIGNATURE = "X-Kolena-Signature"
X_KOLENA_DELIVERY_ID = "X-Kolena-Delivery-ID"
X_KOLENA_TIMESTAMP = "X-Kolena-Timestamp"


class VerificationError(Exception): ...


def _construct_signature_content(timestamp: str, delivery_id: str, payload: str) -> str:
    return f"{timestamp}.{delivery_id}.{payload}"


def _generate_signature(
    secret: str, timestamp: str, delivery_id: str, payload: str
) -> str:
    signature_content = _construct_signature_content(timestamp, delivery_id, payload)
    signature = hmac.new(
        secret.encode("UTF-8"), signature_content.encode("UTF-8"), hashlib.sha256
    ).hexdigest()
    return signature


def verify_signature(
    secret: str, signature: str, timestamp: str, delivery_id: str, payload: str
) -> bool:
    expected_signature = _generate_signature(secret, timestamp, delivery_id, payload)
    return hmac.compare_digest(signature, expected_signature)


def construct_event(
    request_body: Union[str, bytes],
    secret: str,
    request_headers: Mapping[str, Any],
    valid_time_seconds: int = 300,
) -> AgentRun:
    body = (
        request_body.decode("UTF-8")
        if isinstance(request_body, bytes)
        else request_body
    )
    timestamp = request_headers.get(X_KOLENA_TIMESTAMP)
    delivery_id = request_headers.get(X_KOLENA_DELIVERY_ID)
    signature = request_headers.get(X_KOLENA_SIGNATURE)
    if not timestamp or not delivery_id or not signature:
        raise VerificationError("Missing required header(s)")

    ts = int(timestamp)
    current = int(time.time())
    # prevent request with timestamp older than allowed window
    if current - ts > valid_time_seconds:
        raise VerificationError(
            f"Request timestamp outside valid time range {valid_time_seconds}"
        )

    if not verify_signature(secret, signature, timestamp, delivery_id, body):
        raise VerificationError("Invalid signature")

    return AgentRun.model_validate(json.loads(request_body))


def _generate_secret() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=24))


class Proxy:
    """Listen to agent run results and forward to another destination when provided"""

    def __init__(
        self,
        *,
        agent_id: int,
        secret: Union[str, None] = None,
        target: Union[str, None] = None,
    ) -> None:
        self.secret = secret or _generate_secret()
        self.target = target
        self.agent_id = agent_id
        self._client = ClientApi(_get_client())
        print(f"Using webhook secret '{self.secret}'")

    @staticmethod
    def _forward_result(secret: str, target: str, data: str) -> None:
        timestamp = str(int(time.time()))
        delivery_id = str(uuid.uuid4())
        signature = _generate_signature(secret, timestamp, delivery_id, data)
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain",
            X_KOLENA_SIGNATURE: signature,
            X_KOLENA_TIMESTAMP: timestamp,
            X_KOLENA_DELIVERY_ID: delivery_id,
        }
        try:
            urllib3.request("POST", target, body=data, headers=headers)
        except Exception as e:
            print(f"Failed to forward result: {e}")
            pass

    def listen(self, tail: int = -1) -> None:
        import sseclient

        response = self._client.client_stream_results_api_v1_client_agents_agent_id_stream_get_without_preload_content(
            agent_id=self.agent_id, tail=tail
        )
        if response.status >= 400:
            raise Exception(f"HTTP Error: {response.status} - {response.reason}")

        client = sseclient.SSEClient(response)

        for event in client.events():
            try:
                json_payload = json.loads(event.data)
                run_result = AgentRun.model_validate(json_payload)
                print(run_result.model_dump_json(indent=2))
                if self.target:
                    self._forward_result(self.secret, self.target, event.data)
            except Exception as e:
                print(e)
                pass

        print("Session ended")

    def sample(self) -> None:
        response = (
            self._client.client_sample_results_api_v1_client_agents_agent_id_sample_get(
                agent_id=self.agent_id
            )
        )

        print(response.model_dump_json(indent=2))
        if self.target:
            self._forward_result(self.secret, self.target, response.model_dump_json())
