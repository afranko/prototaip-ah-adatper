from __future__ import annotations

import requests

from arrowhead_client.consumer.base import BaseConsumer
from arrowhead_client.response import Response
from arrowhead_client.rules import OrchestrationRule
from arrowhead_client import constants
from arrowhead_client.types import M


class RequestsConsumer(BaseConsumer, protocol=constants.Protocol.HTTP):
    """
    Consumer based on requests.
    """

    def __init__(
            self,
            keyfile: str,
            certfile: str,
            cafile: str,
    ):
        super().__init__(keyfile, certfile, cafile)
        self.session = requests.Session()
        self.session.verify = True
        self.session.cert = (certfile, keyfile)
        self.cafile = cafile

    def consume_service(
            self,
            rule: OrchestrationRule,
            data_model: type[M] | None = None,
            **kwargs,
    ) -> Response:
        """ Consume registered provided_service """

        # RMID MOD
        rmid = str(kwargs.pop("rmid")) if "rmid" in kwargs else ""

        print(f'{http(rule.secure)}{rule.endpoint}/{rmid}')

        service_response = self.session.request(
                rule.method,
                url=f'{http(rule.secure)}{rule.endpoint + "/" + rmid}',
                auth=ArrowheadTokenAuth(rule.authorization_token),
                verify=self.cafile,
                **kwargs
        )

        return Response(service_response.content, rule.payload_type, service_response.status_code)


def http(secure: str) -> str:
    if secure == constants.Security.INSECURE:
        return 'http://'
    return 'https://'


class ArrowheadTokenAuth(requests.auth.AuthBase):
    def __init__(self, token: str):
        self.token = token

    def __call__(self, r: requests.PreparedRequest):
        if self.token:
            r.headers['Authorization'] = f'Bearer {self.token}'

        return r
