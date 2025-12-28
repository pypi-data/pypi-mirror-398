"""Qedma Public API"""

# pylint: disable=[duplicate-code]
from typing import Literal

import requests

from qedma_api import models
from qedma_api.clients import base_client


class IBMQProvider(models.RequestBase, models.BaseProvider):
    """IBM Quantum Provider params"""

    name: Literal["ibmq"] = "ibmq"
    token_ref: str | None = None
    instance: str
    channel: Literal["ibm_quantum_platform", "ibm_cloud"] = "ibm_quantum_platform"


class IBMJobRequest(models.JobRequestBase):
    """IBM job request"""

    provider: IBMQProvider


class IBMCharacterizationJobRequest(models.CharacterizationJobRequestBase):
    """IBM characterization job request"""

    provider: IBMQProvider


class Client(base_client.BaseClient):  # pylint: disable=missing-class-docstring
    ENDPOINT_URI = "https://api.qedma.io/v2/qesem"

    def __init__(
        self,
        *,
        api_token: str | None = None,
        provider: IBMQProvider | None = None,
        uri: str = ENDPOINT_URI,
        timeout: int = 60,
    ) -> None:
        super().__init__(
            api_token=api_token, uri=uri, timeout=timeout, logger_scope="qedma-api/client"
        )
        self.provider = provider

    def set_provider(self, provider: IBMQProvider) -> None:
        """Set the provider of the client. (e.g. IBMQProvider)"""
        self.provider = provider

    def _build_characterization_job_request(
        self, circuit: models.BareCircuit, backend: str, enable_notifications: bool
    ) -> IBMCharacterizationJobRequest:
        return IBMCharacterizationJobRequest(
            circuit=circuit,
            provider=self.provider,
            backend=backend,
            enable_notifications=enable_notifications,
        )

    def _build_job_request(  # pylint: disable=too-many-positional-arguments
        self,
        circuit: models.ErrorSuppressionCircuit | models.Circuit,
        empirical_time_estimation: bool,
        backend: str,
        description: str,
        precision_mode: models.PrecisionMode | None,
        enable_notifications: bool,
        single_mitigation_step: bool = False,
    ) -> IBMJobRequest:

        return IBMJobRequest(
            provider=self.provider,
            circuit=circuit,
            backend=backend,
            empirical_time_estimation=empirical_time_estimation,
            precision_mode=precision_mode,
            description=description,
            enable_notifications=enable_notifications,
            single_mitigation_step=single_mitigation_step,
        )

    def register_qpu_token(self, token: str) -> None:
        """
        registers the QPU vendor token.
        :param token: The vendor token.
        """

        response = requests.post(
            url=f"{self.uri}/qpu-token",
            data=models.RegisterQpuTokenRequest(qpu_token=token).model_dump_json(),
            headers=self._headers,
            timeout=30,
        )

        self._raise_for_status(response)

    def unregister_qpu_token(self) -> None:
        """
        Unregisters a vendor token for an account.
        """

        response = requests.delete(
            url=f"{self.uri}/qpu-token",
            headers=self._headers,
            timeout=30,
        )

        self._raise_for_status(response)
