# pylint: disable=too-many-lines
"""Qedma Public API"""

import abc
import datetime
import importlib.metadata
import json
import math
import os
import sys
import threading
import time
from collections.abc import Mapping, Sequence
from typing import Any, overload

import loguru
import pydantic
import qiskit
import qiskit.circuit
import qiskit.quantum_info
import requests
import tenacity

from qedma_api import helpers, models
from qedma_api.exceptions import APITokenNotFound


STATUS_POLLING_INTERVAL = datetime.timedelta(seconds=10)
PROGRESS_POLLING_INTERVAL = datetime.timedelta(seconds=10)


class BaseClient(abc.ABC):  # pylint: disable=missing-class-docstring

    def __init__(
        self, *, api_token: str | None = None, uri: str, timeout: int = 60, logger_scope: str
    ) -> None:
        self._logger_scope = logger_scope
        self.logger = loguru.logger.bind(scope=self._logger_scope)
        self.api_token = api_token if api_token else self._load_stored_api_token()
        self.provider: Any = None
        self.uri = uri
        self.timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {self.api_token}",
            "X-Qedma-Client-Version": importlib.metadata.version("qedma_api"),
        }
        self._config_loguru()

    @overload  # QESEM without parameters
    def create_job(  # type: ignore[no-any-unimported]  # pylint: disable=too-many-arguments
        self,
        *,
        circuit: qiskit.QuantumCircuit,
        observables: models.ObservablesGroups,
        observables_metadata: Sequence[models.ObservableMetadata] | None = None,
        parameters: None = None,
        precision: float | models.PrecisionPerFactor,
        backend: str,
        empirical_time_estimation: bool = False,
        description: str = "",
        circuit_options: models.CircuitOptions | None = None,
        precision_mode: None = None,
    ) -> models.ClientJobDetails: ...

    @overload  # QESEM with parameters
    def create_job(  # type: ignore[no-any-unimported]  # pylint: disable=too-many-arguments
        self,
        *,
        circuit: qiskit.QuantumCircuit,
        observables: models.ObservablesGroups,
        observables_metadata: Sequence[models.ObservableMetadata] | None = None,
        parameters: Mapping[str | qiskit.circuit.Parameter, Sequence[float]],
        precision: float | models.PrecisionPerFactor,
        backend: str,
        empirical_time_estimation: bool = False,
        description: str = "",
        circuit_options: models.CircuitOptions | None = None,
        precision_mode: models.PrecisionMode,
    ) -> models.ClientJobDetails: ...

    @overload  # QES
    def create_job(  # type: ignore[no-any-unimported]  # pylint: disable=too-many-arguments
        self,
        *,
        circuit: qiskit.QuantumCircuit,
        shots: int,
        parameters: Mapping[str | qiskit.circuit.Parameter, Sequence[float]] | None = None,
        backend: str,
        description: str = "",
        circuit_options: models.CircuitOptions | None = None,
    ) -> models.ClientJobDetails: ...

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def create_job(  # type: ignore[no-any-unimported]  # pylint: disable=too-many-arguments,too-many-branches,too-many-locals
        self,
        *,
        circuit: qiskit.QuantumCircuit,
        observables: models.ObservablesGroups | None = None,
        observables_metadata: Sequence[models.ObservableMetadata] | None = None,
        parameters: Mapping[str | qiskit.circuit.Parameter, Sequence[float]] | None = None,
        precision: float | models.PrecisionPerFactor | None = None,
        backend: str,
        empirical_time_estimation: bool = False,
        description: str = "",
        circuit_options: models.CircuitOptions | None = None,
        precision_mode: models.PrecisionMode | None = None,
        shots: int | None = None,
        enable_notifications: bool = True,
        single_mitigation_step: bool = False,
    ) -> models.ClientJobDetails:
        """
        Submit a new job to the API Gateway.
        :param circuit: The circuit to run.
        :param observables: The observables to measure.
         Can be either models.Observable, Sequence[models.Observable],
         or qiskit.quantum_info.SparsePauliOp.
        :param precision: The target absolute precision to achieve for each input observable.
         If a `PrecisionPerFactor` is provided, it should be a map from a quantum error tuning
         factor (error amplification or reduction factor) to the desired precision at that factor
         (for all observables).
        :param backend: The backend (QPU) to run on. (e.g., `ibm_fez`)
        :param parameters: Used when a parameterized circuit is provided. The parameters to run the
         circuit with (mapping from parameter to sequence of values, all parameters must have the
         same number of values) If given, the number of observables must be equal to the number
         of values.
        :param empirical_time_estimation: Whether to use empirical time estimation.
        :param description: A description for the job.
        :param circuit_options: Additional options for a circuit.
        :param precision_mode: The precision mode to use. Can only be used when parameters are set.
        :param shots: The number of shots to execute. Only used when error_suppression_only=True.
        :param enable_notifications: Whether to enable email notifications for this job.
        :param single_mitigation_step: Whether to run mitigation in a single step. Default is False.
        :return: The job's details including its ID.
        """

        if circuit_options is None:
            circuit_options = models.CircuitOptions()

        if self.provider is None:
            raise ValueError("Provider is not set")

        if observables is not None:

            if isinstance(
                observables,
                (
                    models.Observable,
                    qiskit.quantum_info.SparsePauliOp,
                    qiskit.quantum_info.SparseObservable,
                ),
            ):
                observables = (observables,)

            new_observables = []
            for obs in observables:

                if isinstance(obs, qiskit.quantum_info.SparsePauliOp):
                    obs = models.Observable.from_sparse_pauli_op(obs)

                if isinstance(obs, qiskit.quantum_info.SparseObservable):
                    obs = models.Observable.from_sparse_observable(obs)

                new_observables.append(obs)

            observables = tuple(new_observables)

        if observables_metadata is not None:
            if observables is None or len(observables_metadata) != len(observables):
                raise ValueError(
                    "Observables metadata provided but did not match the number of observables"
                )

        circ: models.Circuit | models.ErrorSuppressionCircuit
        if not circuit_options.error_suppression_only:
            if not observables:
                raise ValueError("Observables are mandatory!")
            if not precision:
                raise ValueError("Precision is mandatory!")
            if shots:
                raise ValueError("Shots are not supported when error_suppression_only is disabled")

            circ = models.Circuit(
                circuit=circuit,
                parameters=(
                    {str(k): tuple(v) for k, v in parameters.items()}
                    if parameters is not None
                    else None
                ),
                observables=tuple(observables),
                observables_metadata=(
                    tuple(observables_metadata) if observables_metadata is not None else None
                ),
                precision=precision,
                options=circuit_options,
            )
        else:
            if observables:
                raise ValueError(
                    "Observables are not supported when error_suppression_only is enabled"
                )
            if precision:
                raise ValueError(
                    "Precision is not supported when error_suppression_only is enabled"
                )
            if empirical_time_estimation:
                raise ValueError(
                    "Time estimation is not supported when error_suppression_only is enabled"
                )
            if not shots:
                raise ValueError("shots is mandatory when error_suppression_only is enabled")

            circ = models.ErrorSuppressionCircuit(
                circuit=circuit,
                shots=shots,
                parameters=(
                    {str(k): tuple(v) for k, v in parameters.items()}
                    if parameters is not None
                    else None
                ),
                options=circuit_options,
            )

        job_request = self._build_job_request(
            circuit=circ,
            empirical_time_estimation=empirical_time_estimation,
            backend=backend,
            description=description,
            precision_mode=precision_mode,
            enable_notifications=enable_notifications,
            single_mitigation_step=single_mitigation_step,
        )
        self.logger.info("Submitting new job")
        response = requests.post(
            url=f"{self.uri}/job",
            data=job_request.model_dump_json(),
            headers=self._headers,
            timeout=self.timeout,
        )

        self._raise_for_status(response)

        resp = models.JobDetails.model_validate_json(response.content)
        client_job_details = models.ClientJobDetails.from_job_details(resp)

        self.logger.info("[{job_id}] New job created", job_id=resp.job_id)

        self._print_warnings_and_errors(client_job_details)

        return client_job_details

    @abc.abstractmethod
    def _build_job_request(  # pylint: disable=too-many-positional-arguments
        self,
        circuit: models.ErrorSuppressionCircuit | models.Circuit,
        empirical_time_estimation: bool,
        backend: str,
        description: str,
        precision_mode: models.PrecisionMode | None,
        enable_notifications: bool,
        single_mitigation_step: bool,
    ) -> models.JobRequestBase:
        pass

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def start_job(
        self,
        job_id: str,
        max_qpu_time: datetime.timedelta,
        options: models.JobOptions | None = None,
        force_start: bool = False,
    ) -> None:
        """
        Start running an estimation job.
        :param job_id: The ID of the job.
        :param max_qpu_time: The maximum allowed QPU time.
        :param options: Additional options for the job (see `JobOptions`).
        :param force_start: If True, the job will automatically start once the estimation completes.
        """
        if options is None:
            options = models.JobOptions()

        job = self._get_jobs([job_id])[0]
        if (not force_start) and job.status == models.JobStatus.ESTIMATING:
            self.logger.error(
                "[{job_id}] It is not allowed to issue start_job until it is in status ESTIMATED. Please wait for the estimation to complete.",  # pylint: disable=line-too-long
                job_id=job_id,
            )
            return
        if job.status not in {
            models.JobStatus.ESTIMATING,
            models.JobStatus.ESTIMATED,
        }:
            self.logger.error(
                "[{job_id}] It is not allowed to issue start_job after the job has started or completed. ",  # pylint: disable=line-too-long
                job_id=job_id,
            )
            return

        self.logger.info("[{job_id}] Starting job", job_id=job_id)

        response = requests.post(
            url=f"{self.uri}/job/{job_id}/start",
            data=models.StartJobRequest(
                max_qpu_time=max_qpu_time, options=options, force_start=force_start
            ).model_dump_json(),
            headers=self._headers,
            timeout=self.timeout,
        )

        self._raise_for_status(response)

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def _create_decompose_task(
        self,
        mpo_file: str,
        *,
        max_bases: int,
        l2_truncation_err: float,
        op_l2_norm: float,
        k: int,
        pauli_coeff_th: float,
    ) -> str:
        self.logger.info("Requesting decomposition of MPO")
        if not os.path.exists(mpo_file):
            raise FileNotFoundError(f"File {mpo_file} not found")
        if not os.path.isfile(mpo_file):
            raise FileNotFoundError(f"File {mpo_file} is not a file")

        with open(mpo_file, "rb") as data_file:
            response = requests.post(
                url=f"{self.uri}/hpc/decompose",
                params=[
                    ("max_bases", max_bases),
                    ("l2_truncation_err", l2_truncation_err),
                    ("op_l2_norm", op_l2_norm),
                    ("k", k),
                    ("pauli_coeff_th", pauli_coeff_th),
                ],
                files={"data_file": data_file},
                headers=self._headers,
                timeout=datetime.timedelta(minutes=5).total_seconds(),
            )

        if response.status_code == 404:
            raise models.QedmaServerError("API endpoint not enabled")

        self._raise_for_status(response)

        resp_json = response.json()
        if "task_id" not in resp_json:
            raise models.QedmaServerError("Task ID not found in response", details=resp_json)

        task_id = resp_json["task_id"]
        if not isinstance(task_id, str):
            raise models.QedmaServerError("Invalid task ID in response", details=resp_json)

        return task_id

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def _get_decompose_task_result(
        self, task_id: str, *, max_retries: int = 5
    ) -> models.DecomposeResponse:
        response = None
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    url=f"{self.uri}/hpc/decompose/{task_id}",
                    headers=self._headers,
                    timeout=60 * 10,
                )
            except requests.Timeout:
                if attempt == max_retries - 1:
                    self.logger.error(
                        "[{task_id}] Timeout while waiting for decomposition task result. ",
                        task_id=task_id,
                    )
                    raise
                self.logger.error(
                    "[{task_id}] Timeout while waiting for decomposition task result. "
                    "Retrying...",
                    task_id=task_id,
                )
                time.sleep(0.3)
                continue

            if response.status_code == 200:
                return models.DecomposeResponse.model_validate_json(response.content)

            if response.status_code == 202:
                raise models.ResultNotReadyError()

            self.logger.error(
                "[{task_id}] Failed to get decomposition task result ({status_code}). "
                "Retrying...",
                task_id=task_id,
                status_code=response.status_code,
            )
            time.sleep(0.3)

        if response is not None:
            self._raise_for_status(response)
        raise models.QedmaServerError("Failed to get decomposition task result after max retries")

    def decompose(  # type: ignore[no-any-unimported]  # pylint: disable=missing-function-docstring
        self,
        mpo_file: str,
        *,
        max_bases: int,
        l2_truncation_err: float = 1e-12,
        observable: models.Observable | qiskit.quantum_info.SparsePauliOp,
        k: int = 1000,
        pauli_coeff_th: float = 1e-8,
        timeout: datetime.timedelta = datetime.timedelta(minutes=60),
    ) -> models.DecomposeResponse:
        if isinstance(observable, qiskit.quantum_info.SparsePauliOp):
            observable = models.Observable.from_sparse_pauli_op(observable)

        op_l2_norm = math.sqrt(sum(coeff**2 for p, coeff in observable.root.items()))

        task_id = self._create_decompose_task(
            mpo_file,
            max_bases=max_bases,
            l2_truncation_err=l2_truncation_err,
            op_l2_norm=op_l2_norm,
            k=k,
            pauli_coeff_th=pauli_coeff_th,
        )
        self.logger.info("Decomposition task created. task_id: [{task_id}]", task_id=task_id)

        start = datetime.datetime.now()
        while datetime.datetime.now() - start < timeout:
            time.sleep(0.5)
            try:
                return self._get_decompose_task_result(task_id)
            except models.ResultNotReadyError:
                pass

        raise TimeoutError("Decomposition task timed out")

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def run_device_characterization(  # type: ignore[no-any-unimported]
        self,
        *,
        circuit: qiskit.QuantumCircuit,
        backend: str,
        enable_notifications: bool = True,
    ) -> models.CharacterizationJobDetails:
        """
        Submit a new job to the API Gateway.
        :param circuit: The circuit to choose the best layout for (acccording to the infidelities).
        :param backend: The backend (QPU) to run on. (e.g., `ibm_fez`)
        :param enable_notifications: Whether to enable email notifications for this job.
        :return: The layout selected circuit and a dict containing the device characterization:
         - a dictionary from qubit index to measurement error (`dict[int, float]`)
         - a dictionary of gate infidelities per gate type and qubits
           (`dict[tuple[str, tuple[int, int]]]`)
        """

        if self.provider is None:
            raise ValueError("Provider is not set")

        characterization_job_request = self._build_characterization_job_request(
            circuit=models.BareCircuit(circuit=circuit),
            backend=backend,
            enable_notifications=enable_notifications,
        )

        self.logger.info("Submitting new characterization job")
        response = requests.post(
            url=f"{self.uri}/daas_job",
            data=characterization_job_request.model_dump_json(),
            headers=self._headers,
            timeout=self.timeout,
        )

        self._raise_for_status(response)

        resp = models.CharacterizationJobDetails.model_validate_json(response.content)

        self.logger.info("[{job_id}] New characterization job created", job_id=resp.job_id)

        self._print_warnings_and_errors(resp)

        return resp

    @abc.abstractmethod
    def _build_characterization_job_request(
        self, circuit: models.BareCircuit, backend: str, enable_notifications: bool
    ) -> models.CharacterizationJobRequestBase:
        pass

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def cancel_job(self, job_id: str) -> None:
        """
        Cancel a job. Please note that the `cancel_job` API will prevent QESEM from sending
        new circuits to the QPU. Circuits which are already running on the QPU cannot be cancelled.

        :param job_id: The job_id to cancel
        """
        self.logger.info("[{job_id}] Canceling job", job_id=job_id)
        response = requests.post(
            url=f"{self.uri}/job/{job_id}/cancel",
            headers=self._headers,
            timeout=self.timeout,
        )

        self._raise_for_status(response)

    def get_job(
        self,
        job_id: str,
        *,
        include_circuits: bool = False,
        include_results: bool = False,
        qedma_observable_model: bool = False,
    ) -> models.ClientJobDetails:
        """
        Get a job's details.
        :param job_id: The ID of the job.
        :param include_circuits: Whether to include the input circuit.
        :param include_results: Whether to include the result of the job (if it is ready).
        :param qedma_observable_model: Whether to return the results with Qedma's observable model,
         or Qiskit SparsePauliOp.
        :return: Details about the job, with the data from the flags.
        """
        client_job_details = self.get_jobs(
            [job_id],
            include_circuits=include_circuits,
            include_results=include_results,
            qedma_observable_model=qedma_observable_model,
        )[0]

        self._print_warnings_and_errors(client_job_details)

        return client_job_details

    def get_jobs(
        self,
        jobs_ids: list[str],
        *,
        include_circuits: bool = False,
        include_results: bool = False,
        qedma_observable_model: bool = False,
    ) -> list[models.ClientJobDetails]:
        """
        Get multiple jobs' details.
        :param jobs_ids: The IDs of the jobs.
        :param include_circuits: Whether to include the input circuits.
        :param include_results: Whether to include the results of the jobs (if they are ready).
        :param qedma_observable_model: Whether to return the results with Qedma's observable model,
         or Qiskit SparsePauliOp.
        :return: Details about the jobs, with the data from the flags.
        """
        self.logger.info("Querying jobs details. jobs_ids: {jobs_ids}", jobs_ids=jobs_ids)
        return [
            models.ClientJobDetails.from_job_details(job, qedma_observable_model)
            for job in self._get_jobs(
                jobs_ids, include_circuits=include_circuits, include_results=include_results
            )
        ]

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def list_jobs(self, skip: int = 0, limit: int = 50) -> list[models.JobDetails]:
        """
        Paginate jobs.
        :param skip: How many jobs to skip.
        :param limit: Maximum amount of jobs to return.
        :return: The list of requested jobs.
        """
        self.logger.info(
            "Listing jobs details. skip: [{skip}], limit: [{limit}]", skip=skip, limit=limit
        )

        response = requests.get(
            url=f"{self.uri}/jobs/list",
            params=[("skip", skip), ("limit", limit)],
            headers=self._headers,
            timeout=self.timeout,
        )

        self._raise_for_status(response)

        return models.GetJobsDetailsResponse.model_validate_json(response.content).jobs

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def _get_jobs(
        self,
        jobs_ids: list[str],
        *,
        include_circuits: bool = False,
        include_results: bool = False,
    ) -> list[models.JobDetails]:
        response = requests.get(
            url=f"{self.uri}/jobs",
            params=[
                ("ids", ",".join(jobs_ids)),
                ("include_circuits", include_circuits),
                ("include_results", include_results),
            ],
            headers=self._headers,
            timeout=self.timeout,
        )

        self._raise_for_status(response)

        jobs = models.GetJobsDetailsResponse.model_validate_json(response.content).jobs
        if not jobs:
            raise models.QedmaServerError("No jobs found")

        return jobs

    @tenacity.retry(
        retry=tenacity.retry_if_exception_type(models.QedmaBadGatewayError),
        reraise=True,
        wait=tenacity.wait_exponential(min=3, max=10),
        stop=tenacity.stop_after_attempt(5),
    )
    def get_characterization_jobs(
        self, jobs_ids: list[str]
    ) -> list[models.CharacterizationJobDetails]:
        """
        Get multiple jobs' details.
        :param jobs_ids: The IDs of the jobs.
        :return: the characterization jobs details.
        """
        response = requests.get(
            url=f"{self.uri}/daas_jobs",
            params=[("ids", ",".join(jobs_ids))],
            headers=self._headers,
            timeout=self.timeout,
        )

        self._raise_for_status(response)

        jobs = models.GetCharJobsDetailsResponse.model_validate_json(response.content).jobs
        if not jobs:
            raise models.QedmaServerError("No jobs found")

        return jobs

    def _wait_for_status(  # pylint: disable=too-many-arguments
        self,
        job_id: str,
        statuses: set[models.JobStatus],
        interval: datetime.timedelta,
        timeout: datetime.timedelta | None,
        *,
        include_circuits: bool = False,
        include_results: bool = False,
        log_intermediate_results: bool = False,
    ) -> models.JobDetails:
        job = self._get_jobs(
            [job_id], include_circuits=include_circuits, include_results=include_results
        )[0]

        start = datetime.datetime.now()
        intermediate_results = None
        while job.status not in statuses:
            if timeout is not None and datetime.datetime.now() - start > timeout:
                raise TimeoutError("The given time out passed!")

            time.sleep(interval.total_seconds())
            job = self._get_jobs(
                [job_id], include_circuits=include_circuits, include_results=include_results
            )[0]

            if log_intermediate_results and job.intermediate_results:
                if job.intermediate_results != intermediate_results:
                    intermediate_results = job.intermediate_results
                    self.logger.info(
                        "[{job_id}] Intermediate results: [{results}]",
                        job_id=job_id,
                        results=job.intermediate_results,
                    )

        return job

    def _wait_for_char_status(  # pylint: disable=too-many-arguments
        self,
        job_id: str,
        statuses: set[models.CharacterizationJobStatus],
        interval: datetime.timedelta,
        timeout: datetime.timedelta | None,
    ) -> models.CharacterizationJobDetails:
        job = self.get_characterization_jobs([job_id])[0]

        start = datetime.datetime.now()
        while job.status not in statuses:
            if timeout is not None and datetime.datetime.now() - start < timeout:
                raise TimeoutError("The given time out passed!")

            time.sleep(interval.total_seconds())
            job = self.get_characterization_jobs([job_id])[0]

        return job

    def wait_for_time_estimation(
        self,
        job_id: str,
        *,
        interval: datetime.timedelta = STATUS_POLLING_INTERVAL,
        max_poll_time: datetime.timedelta | None = None,
    ) -> datetime.timedelta | None:
        """
        Wait until a job reaches the time-estimation part, and get the estimation.

        :param job_id: The ID of the job.
        :param interval: The interval between two polls. Defaults to 10 seconds.
        :param max_poll_time: Max time until a timeout. If left empty, the method
        will return only when the job finishes.
        :return: The time estimation of the job.
        :raises: `TimeoutError` if max_poll_time passed.
        """
        job = self._wait_for_status(
            job_id,
            {
                models.JobStatus.ESTIMATED,
                models.JobStatus.RUNNING,
                models.JobStatus.SUCCEEDED,
                models.JobStatus.FAILED,
                models.JobStatus.CANCELLED,
            },
            interval,
            max_poll_time,
        )
        client_job = models.ClientJobDetails.from_job_details(job)

        self._print_warnings_and_errors(client_job)

        time_est = client_job.empirical_qpu_time_estimation
        time_est_desc = "Empirical"
        if time_est is None:
            time_est = client_job.analytical_qpu_time_estimation
            time_est_desc = "Analytical"

        if time_est is not None:
            self.logger.info(
                "[{job_id}] {time_est_desc} time estimation: [{time_est} minutes]",
                job_id=job_id,
                time_est=time_est.total_seconds() // 60,
                time_est_desc=time_est_desc,
            )

        return time_est

    def wait_for_job_complete(
        self,
        job_id: str,
        *,
        interval: datetime.timedelta = STATUS_POLLING_INTERVAL,
        max_poll_time: datetime.timedelta | None = None,
        qedma_observable_model: bool = False,
    ) -> models.ClientJobDetails:
        """
        Wait until the job finishes, and get the results. While the job is running,
        this function also prints the job's current step and intermediate results

        :param job_id: The ID of the job.
        :param interval: The interval between two polls. Defaults to 10 seconds.
        :param max_poll_time: Max time until a timeout. If left empty, the method
        will return only when the job finishes.
        :param qedma_observable_model: Whether to return the results with Qedma's observable model,
         or Qiskit SparsePauliOp.
        :return: The details of the job, including its results.
        :raises: `TimeoutError` if max_poll_time passed.
        """
        stop_event = threading.Event()
        progress_polling_thread = threading.Thread(
            target=self._progress_listener,
            kwargs={
                "sampling_interval": PROGRESS_POLLING_INTERVAL.total_seconds(),
                "print_interval": interval.total_seconds(),
                "job_id": job_id,
                "stop_event": stop_event,
            },
            daemon=True,
        )
        progress_polling_thread.start()

        try:
            job = self._wait_for_status(
                job_id,
                {
                    models.JobStatus.SUCCEEDED,
                    models.JobStatus.FAILED,
                    models.JobStatus.CANCELLED,
                },
                interval,
                max_poll_time,
                include_results=True,
                log_intermediate_results=True,
            )
            client_job = models.ClientJobDetails.from_job_details(job, qedma_observable_model)
        finally:
            stop_event.set()
            progress_polling_thread.join()

        self._print_warnings_and_errors(client_job)

        results = client_job.results
        self.logger.info(
            "[{job_id}] Final results: [{results}]",
            job_id=job_id,
            results=results,
        )

        return client_job

    def wait_for_characterization_job_complete(
        self,
        job_id: str,
        *,
        interval: datetime.timedelta = STATUS_POLLING_INTERVAL,
        max_poll_time: datetime.timedelta | None = None,
    ) -> models.CharacterizationJobDetails:
        """
        Wait until the job finishes, and get the results. While the job is running,
        this function also prints the job's current step and intermediate results

        :param job_id: The ID of the job.
        :param interval: The interval between two polls. Defaults to 10 seconds.
        :param max_poll_time: Max time until a timeout. If left empty, the method
        will return only when the job finishes.
        :return: The job results
        :raises: `TimeoutError` if max_poll_time passed.
        """
        job = self._wait_for_char_status(
            job_id,
            {
                models.CharacterizationJobStatus.SUCCEEDED,
                models.CharacterizationJobStatus.FAILED,
                models.CharacterizationJobStatus.CANCELLED,
            },
            interval,
            max_poll_time,
        )

        self._print_warnings_and_errors(job)

        self.logger.info(
            "[{job_id}] characterization and layout optimization results are ready", job_id=job_id
        )

        return job

    def _progress_listener(
        self,
        sampling_interval: float,
        print_interval: float,
        job_id: str,
        stop_event: threading.Event,
    ) -> None:
        last_time = time.monotonic()
        next_step_idx = 0

        while True:
            job = self._get_jobs([job_id], include_circuits=False, include_results=False)[0]

            if job.progress and job.progress.steps:
                new_steps_count = len(job.progress.steps)

                if time.monotonic() - last_time > print_interval or new_steps_count > next_step_idx:
                    last_time = time.monotonic()

                    if new_steps_count > next_step_idx:
                        new_steps = job.progress.steps[next_step_idx:]
                        next_step_idx = new_steps_count
                        for step in new_steps:
                            self.logger.info(f"[{job.job_id}] step: [{step.name}]")

            # We break here instead in the while loop because we want to print any steps
            # that may have been added during the last sampling interval
            if stop_event.is_set():
                break
            time.sleep(sampling_interval)

    def _raise_for_status(self, response: requests.Response) -> None:
        http_error_msg = ""
        if isinstance(response.reason, bytes):
            # We attempt to decode utf-8 first because some servers choose to
            # localize their reason strings. If the string isn't utf-8, we fall
            # back to iso-8859-1 for all other encodings. (See PR #3538)
            try:
                reason = response.reason.decode("utf-8")
            except UnicodeDecodeError:
                reason = response.reason.decode("iso-8859-1")
        else:
            reason = response.reason

        if 400 <= response.status_code < 500:
            http_error_msg = (
                f"{response.status_code} Client Error: {reason} for url: {response.url}"
            )

        elif 500 <= response.status_code < 600:
            http_error_msg = (
                f"{response.status_code} Server Error: {reason} for url: {response.url}"
            )

        if http_error_msg:
            if not response.content:
                raise models.QedmaServerError(http_error_msg)

            try:
                details = response.json().get("detail")
            except json.JSONDecodeError:
                raise models.QedmaServerError(http_error_msg)  # pylint: disable=raise-missing-from

            self.logger.error(
                "Qedma server error: {http_error_msg}. Details: {details}",
                http_error_msg=http_error_msg,
                details=details,
            )
            if response.status_code == 502:
                raise models.QedmaBadGatewayError(http_error_msg, details=details)
            raise models.QedmaServerError(http_error_msg, details=details)

    def _print_warnings_and_errors(
        self,
        job_details: models.ClientJobDetails | models.CharacterizationJobDetails,
    ) -> None:
        if job_details.warnings:
            for w in job_details.warnings:
                self.logger.warning(w)

        if job_details.errors:
            if len(job_details.errors) == 1:
                self.logger.error(
                    "Job creation encountered an error: {err}.", err=job_details.errors[0]
                )
            else:
                self.logger.error(
                    "Job creation encountered multiple errors: {errs}.", errs=job_details.errors
                )

    def _config_loguru(self) -> None:
        if sys.stderr or sys.stdout:
            self.logger.remove()  # Note that this affects anyone using loguru.logger
            if sys.stdout:
                self.logger.add(
                    sys.stdout,
                    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}",
                    filter=lambda record: record["extra"].get("scope") == self._logger_scope
                    and record["level"].no <= self.logger.level("INFO").no,
                )
            if sys.stderr:
                self.logger.add(
                    sys.stderr,
                    filter=lambda record: record["extra"].get("scope") != self._logger_scope,
                )
                self.logger.add(
                    sys.stderr,
                    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {message}",
                    filter=lambda record: record["extra"].get("scope") == self._logger_scope
                    and record["level"].no > self.logger.level("INFO").no,
                )

    def _load_stored_api_token(self) -> str:
        token_file_path = helpers.config_file_path()
        try:
            with open(token_file_path, "r", encoding="utf-8") as f:
                qedma_params = models.QEDMAParams.model_validate_json(f.read())
                return qedma_params.api_token
        except (FileNotFoundError, pydantic.ValidationError) as exc:
            raise APITokenNotFound() from exc
