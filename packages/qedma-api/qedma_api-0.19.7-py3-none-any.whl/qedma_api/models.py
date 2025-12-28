# pylint: disable=too-many-lines
"""Qedma Public API"""

# pylint: disable=missing-function-docstring,missing-class-docstring,missing-module-docstring
import contextlib
import datetime
import enum
import re
from collections.abc import Generator, Sequence
from typing import Annotated, Any, Literal, TypeAlias

import pydantic
import qiskit.qasm3
import qiskit.quantum_info
from typing_extensions import NotRequired, Self, TypedDict

from qedma_api import pauli_utils


class QEDMAParams(pydantic.BaseModel):
    api_token: str


class BaseProvider(pydantic.BaseModel):
    token_ref: str | None = None


class RequestBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )


class ResponseBase(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        extra="ignore",
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )


class JobStatus(str, enum.Enum):
    """The status of a job."""

    ESTIMATING = "ESTIMATING"
    """Job was created and QESEM is currently estimating it."""
    ESTIMATED = "ESTIMATED"
    """Job was estimated. Issue the `qedma_client.start_job()` api request to initiate the execution."""  # pylint: disable=line-too-long
    RUNNING = "RUNNING"
    """Job started running. Monitor its progress using the `qedma_client.wait_for_job_complete()`
    method."""
    SUCCEEDED = "SUCCEEDED"
    """Job finished successfully. The user can now get the results via the `qedma_client.get_job()`
    API with the include_results = True flag."""
    FAILED = "FAILED"
    "Job failed. Review the error message in the `job.errors` field." ""
    CANCELLED = "CANCELLED"
    "The job was cancelled by the user."

    def __str__(self) -> str:
        return self.value


class TranspilationLevel(str, enum.Enum):
    MINIMAL = "minimal"
    """
    Minimal transpilation: the mitigated circuit will closely resemble the input
    circuit structurally.
    """

    MINIMAL_WITH_LAYOUT_OPT = "minimal_with_layout_opt"
    """
    Minimal transpilation: the mitigated circuit will closely resemble the input
    circuit structurally. Additionally, the qubit layout will be optimized.
    """

    STANDARD = "standard"
    """ Prepares several alternative transpilations and chooses the one that minimizes QPU time."""

    # Aliases for backward compatibility
    LEVEL_0 = MINIMAL_WITH_LAYOUT_OPT
    LEVEL_1 = STANDARD

    @classmethod
    def _missing_(cls, value: object) -> Any:
        # aliases for backward compatibility
        match value:
            case 0:
                return cls.MINIMAL_WITH_LAYOUT_OPT
            case 1:
                return cls.STANDARD
        return super()._missing_(value)


def _unique_qubit_indices(value: str) -> str:
    """
    Ensure that every qubit index is referenced at most once.
    The Pauli string syntax is restricted by ``_PAULI_STRING_REGEX_STR`` to
    be a comma-separated list of terms such as ``"X_0"`` or ``"r_15"``.
    Extract the trailing integer of each term and verify uniqueness.
    """
    if value == "I":
        return value

    ops_groups_pattern = re.compile(_TERM_GROUP_REGEX)
    ops_groups = sorted(
        ((op_match, q_match) for op_match, q_match in ops_groups_pattern.findall(value)),
        key=lambda x: x[1],
    )
    all_qubits = [q for _, q in ops_groups]

    if not len(set(all_qubits)) == len(all_qubits):
        raise ValueError(
            f"Observable term contains multiple operations for the same qubit: {value}"
        )

    return ",".join("".join(g) for g in ops_groups)


_TERM_GROUP_REGEX = r"([XYZ01rl+\-])_*(\d+)"
_TERM_STRING_REGEX = rf"^{_TERM_GROUP_REGEX}(,{_TERM_GROUP_REGEX})*$"
_TERM_STRING_OR_I_REGEX = rf"({_TERM_STRING_REGEX})|(^I$)"

ObsTerm = Annotated[
    str,
    pydantic.Field(pattern=_TERM_STRING_OR_I_REGEX),
    pydantic.AfterValidator(_unique_qubit_indices),
    pydantic.BeforeValidator(lambda s: s.replace("_", "")),
]


class ObservableMetadata(pydantic.BaseModel):
    """Metadata for a quantum observable."""

    description: str
    "Description of the observable"


def _term_to_repr(term: ObsTerm) -> ObsTerm:
    term = term.replace("_", "")
    return ",".join(f"{q_term[0]}_{q_term[1:]}" for q_term in term.split(","))


class Observable(pydantic.RootModel[dict[ObsTerm, float]]):
    """A quantum observable represented as a mapping of ObsTerm strings to their coefficients."""

    @pydantic.model_validator(mode="after")
    def validate_not_all_terms_are_i(self) -> Self:
        if all(p == "I" for p in self):
            raise ValueError("At least one Term must be non-identity")
        return self

    def __iter__(self) -> Generator[ObsTerm, None, None]:  # type: ignore[override]
        # pydantic suggests to override __iter__ method (
        # https://docs.pydantic.dev/latest/concepts/models/#rootmodel-and-custom-root-types)
        # but __iter__ method is already implemented in pydantic.BaseModel, so we just ignore the
        # warning and hope that it works as expected (tests covers dump/load methods and iter)
        yield from iter(self.root)

    def __getitem__(self, key: ObsTerm) -> float:
        return self.root[pydantic.TypeAdapter(ObsTerm).validate_python(key)]

    def __contains__(self, key: ObsTerm) -> bool:
        return pydantic.TypeAdapter(ObsTerm).validate_python(key) in self.root

    def __len__(self) -> int:
        return len(self.root)

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return (
            "Observable({"
            + ", ".join(f"'{_term_to_repr(t)}': {c}" for t, c in self.root.items())
            + "})"
        )

    def __hash__(self) -> int:
        return hash(tuple(self.root.items()))

    @property
    def qubits(self) -> set[int]:
        """
        Returns a set of qubits that are used in the observable.
        """
        qubit_idx_pattern = re.compile(_TERM_GROUP_REGEX)
        return set().union(
            *((int(q) for _, q in qubit_idx_pattern.findall(s)) for s in self.root if s != "I")
        )

    @staticmethod
    def observables_to_qubits(observables: list["Observable"]) -> set[int]:
        """
        Returns a set of qubits that are used in the observables.
        """
        return set().union(*(o.qubits for o in observables))

    @classmethod
    def from_sparse_pauli_op(  # type: ignore[no-any-unimported]
        cls, pauli_op: qiskit.quantum_info.SparsePauliOp
    ) -> "Observable":
        """Convert a qiskit.quantum_info.SparsePauliOp to an Observable.

        SparsePauliOp, like all of qiskit, uses little-endian convention.
        This means that the operator Pauli("XY") or SparsePauliOp(["XY"],[1])
        have the "X" acting on qubit 1 and "Y" acting on qubit 0.

        :param pauli_op: The SparsePauliOp to convert
        :return: An Observable instance representing the same operator
        :raises ValueError: If the SparsePauliOp contains phases or complex coefficients,
            or if it contains only identity Paulis with zero coefficients
        """
        if any(p.phase != 0 for p in pauli_op.paulis):
            raise ValueError("The `PauliList` of the `SparsePauliOp` must not contain phases")

        if any(c.imag != 0 for c in pauli_op.coeffs):
            raise ValueError("The `coeffs` of the `SparsePauliOp` must be real")

        pauli_op = pauli_op.simplify()

        observable_dict = {
            pauli_utils.qiskit_pauli_to_pauli(p.to_label()): float(c.real)
            for p, c in zip(pauli_op.paulis, pauli_op.coeffs, strict=True)
        }

        return cls(root=observable_dict)

    def to_sparse_pauli_op(  # type: ignore[no-any-unimported]
        self, num_qubits: int | None = None
    ) -> qiskit.quantum_info.SparsePauliOp:
        """
        Convert this Observable to a qiskit.quantum_info.SparsePauliOp.

        SparsePauliOp, like all of qiskit, uses little-endian convention.
        This means that the operator Pauli("XY") or SparsePauliOp(["XY"],[1])
        have the "X" acting on qubit 1 and "Y" acting on qubit 0.

        :param num_qubits: The number of qubits in the resulting SparsePauliOp. If None,
         it will be determined from the highest qubit index in the observable
        """
        if len(self.root) == 0:
            return qiskit.quantum_info.SparsePauliOp(["I"], [0.0])

        if num_qubits is None:
            num_qubits = max(self.qubits, default=0) + 1

        paulis, coeffs = zip(*self.root.items())
        return qiskit.quantum_info.SparsePauliOp(
            [pauli_utils.pauli_to_qiskit_pauli(p, num_qubits) for p in paulis], coeffs
        )

    @classmethod
    def from_sparse_observable(  # type: ignore[no-any-unimported]
        cls, sparse_obs: qiskit.quantum_info.SparseObservable
    ) -> "Observable":
        """
        Convert a qiskit.quantum_info.SparseObservable to an Observable.

        SparseObservable, like all of qiskit, uses little-endian convention.
        This means that the operator SparseObservable("XY")
        have the "X" acting on qubit 1 and "Y" acting on qubit 0.

        :param sparse_obs: The qiskit.quantum_info.SparseObservable to convert
        :return: An Observable instance representing the same operator
        :raises ValueError: If the SparseObservable contains phases or complex coefficients,
            or if it contains only identity Paulis with zero coefficients
        """
        if any(c.imag != 0 for c in sparse_obs.coeffs):
            raise ValueError("The `coeffs` of the `SparsePauliOp` must be real")

        sparse_obs = sparse_obs.simplify()

        def _build_term_string(  # type: ignore[no-any-unimported]
            ops: tuple[qiskit.quantum_info.SparseObservable.BitTerm, ...],
            qubits: tuple[int, ...],
        ) -> ObsTerm:
            if len(ops) == len(qubits) == 0:
                return "I"
            return ",".join(f"{q_op}{q}" for q_op, q in zip(ops, qubits, strict=True))

        observable_dict = {
            _build_term_string(ops, qs): float(c.real)
            for (ops, qs, c) in sparse_obs.to_sparse_list()
        }

        return cls(root=observable_dict)

    def to_sparse_observable(  # type: ignore[no-any-unimported]
        self, num_qubits: int | None = None
    ) -> qiskit.quantum_info.SparseObservable:
        """
        Convert this Observable to a qiskit.quantum_info.SparseObservable.

        SparseObservable, like all of qiskit, uses little-endian convention.
        This means that the operator SparseObservable("XY")
        have the "X" acting on qubit 1 and "Y" acting on qubit 0.

        :param num_qubits: The number of qubits in the resulting SparseObservable. If None,
         it will be determined from the highest qubit index in the observable
        """

        if num_qubits is None:
            num_qubits = max(self.qubits, default=0) + 1

        if len(self.root) == 0:
            return qiskit.quantum_info.SparseObservable.from_terms([], num_qubits)

        return qiskit.quantum_info.SparseObservable.from_terms(
            [
                qiskit.quantum_info.SparseObservable.Term(
                    num_qubits, c, *_term_string_to_qiskit_term(t)
                )
                for t, c in self.root.items()
            ],
            num_qubits,
        )


def _term_string_to_qiskit_term(  # type: ignore[no-any-unimported]
    term: ObsTerm,
) -> tuple[tuple[qiskit.quantum_info.SparseObservable.BitTerm, ...], tuple[int, ...]]:
    if term == "I":
        return (), ()

    ops_groups_pattern = re.compile(_TERM_GROUP_REGEX)
    ops_groups = [
        (qiskit.quantum_info.SparseObservable.BitTerm[q_op], int(q))
        for q_op, q in ops_groups_pattern.findall(term)
    ]
    return tuple(zip(*ops_groups))  # type: ignore[return-value]


SparseObservable: TypeAlias = Observable


class ExpectationValue(ResponseBase):
    """Result of a quantum measurement, containing both the measured value and its uncertainty."""

    value: float
    "The expected value of the quantum measurement"

    error_bar: float
    "The standard error associated with the measurement"

    def __str__(self) -> str:
        return f"{{ev: {self.value} ± {self.error_bar}}}"


class ScaleExpectationValue(ExpectationValue):
    """Result of a quantum measurement, containing both the measured value and its uncertainty."""

    scale: float
    "The quantum error tuning scale (error amplification or reduction scale)"

    def __str__(self) -> str:
        return f"{{scale: {self.scale}, ev: {self.value} ± {self.error_bar}}}"


class NoiseScalingResult(ResponseBase):
    scaling_method: Literal["QESEM"] = "QESEM"
    results_with_REM: list[ScaleExpectationValue]

    def __str__(self) -> str:
        return (
            f'{{scaling_method="{self.scaling_method}", scale_factors= {self.scale_factors}, '
            f"results_with_REM= [{','.join(str(r) for r in self.results_with_REM)})]}}"
        )

    @property
    def scale_factors(self) -> list[float]:
        """List of scale factors used in the noise scaling results"""
        return [r.scale for r in self.results_with_REM]


class ZNEResult(ExpectationValue):
    """Result of an extrapolation to zero noise"""

    extrapolation: str
    """The extrapolation method used (e.g., 'exponential', 'linear', 'quadratic')"""

    scale_factors: list[float]
    """The scale factors used in the extrapolation"""

    def __str__(self) -> str:
        return (
            super().__str__()
            + f", extrapolation: {self.extrapolation}, scale_factors: {self.scale_factors}"
        )


class QesemObservableResult(ResponseBase):
    """Collection of quantum measurement results for a single observable"""

    unmitigated: ExpectationValue | None
    noise_scaling: NoiseScalingResult
    qesem_zne: list[ZNEResult] | None = None

    def __str__(self) -> str:
        return (
            f"{{QESEM: {self.qesem}, unmitigated: {self.unmitigated}, "
            f"noise_scaling: {self.noise_scaling}}}, "
            f"QESEM-SingleZNE: {self.qesem_zne}}}"
        )

    @property
    def qesem(self) -> ExpectationValue | None:
        """Alias for QESEM field"""
        if self.noise_scaling.scaling_method != "QESEM":
            return None

        zero_scale = [v for v in self.noise_scaling.results_with_REM if v.scale == 0.0]

        if len(zero_scale) == 1:
            return ExpectationValue(value=zero_scale[0].value, error_bar=zero_scale[0].error_bar)

        return None


class CircuitQesemResults(pydantic.RootModel[list[tuple[Observable, QesemObservableResult]]]):
    """Collection of quantum measurement results for a single circuit, pairing observables
    and quantum error tuning factor (error amplification or reduction factor) with their
    measured expectation values."""

    def __iter__(self) -> Generator[tuple[Observable, QesemObservableResult], None, None]:  # type: ignore[override] # pylint: disable=line-too-long
        # pydantic suggests to override __iter__ method (
        # https://docs.pydantic.dev/latest/concepts/#rootmodel-and-custom-root-types)
        # but __iter__ method is already implemented in pydantic.BaseModel, so we just ignore the
        # warning and hope that it works as expected (tests covers dump/load methods and iter)
        yield from iter(self.root)

    def __getitem__(self, key: int) -> tuple[Observable, QesemObservableResult]:
        return self.root[key]

    def __len__(self) -> int:
        return len(self.root)

    def __str__(self) -> str:
        return f"{{{','.join([f'    {obs}: {res}' for obs, res in self.root])}}}"


class QesemResults(pydantic.RootModel[list[CircuitQesemResults]]):
    """Collection of quantum measurement results for multiple circuits."""

    def __iter__(self) -> Generator[CircuitQesemResults, None, None]:  # type: ignore[override] # pylint: disable=line-too-long
        # pydantic suggests to override __iter__ method (
        # https://docs.pydantic.dev/latest/concepts/#rootmodel-and-custom-root-types)
        # but __iter__ method is already implemented in pydantic.BaseModel, so we just ignore the
        # warning and hope that it works as expected (tests covers dump/load methods and iter)
        yield from iter(self.root)

    def __getitem__(self, key: int) -> CircuitQesemResults:
        return self.root[key]

    def __len__(self) -> int:
        return len(self.root)

    def __str__(self) -> str:
        return f"[{','.join([f'  Circuit {i}: {res}' for i, res in enumerate(self.root)])}]"


class CircuitQiskitResults(
    list[tuple[qiskit.quantum_info.SparseObservable, QesemObservableResult]]  # type: ignore[no-any-unimported]  # pylint: disable=line-too-long
):
    """Collection of quantum measurement results for a single circuit, pairing observables
    and quantum error tuning factor (error amplification or reduction factor) with their
    measured expectation values."""

    @classmethod
    def from_circuit_result(cls, circ_r: CircuitQesemResults) -> "CircuitQiskitResults":
        qiskit_results = []
        for obs, res in circ_r:
            sparse_obs = obs.to_sparse_observable()
            qiskit_results.append((sparse_obs, res))
        return cls(qiskit_results)


class QiskitResults(list[CircuitQiskitResults]):
    @classmethod
    def from_result(cls, result: QesemResults) -> "QiskitResults":
        return cls([CircuitQiskitResults.from_circuit_result(circ_r) for circ_r in result])


class QesResults(ResponseBase):
    """Quantum Error suppression results"""

    noisy_results: list[dict[int, int]] | None
    results: list[dict[int, int]] | None


class PrecisionMode(str, enum.Enum):
    """
    Precision mode types when executing a parameterized circuit.
    """

    JOB = "JOB"
    """ QESEM will treat the `precision` as a precision for the sum of the expectation values."""
    CIRCUIT = "CIRCUIT"
    """ QESEM will target the specified `precision` for each circuit."""

    def __str__(self) -> str:
        return self.value


class ExecutionMode(str, enum.Enum):
    """The mode of execution."""

    SESSION = "SESSION"
    """ QESEM will execute the job in a single IBM dedicated session."""
    BATCH = "BATCH"
    """ QESEM will execute the job in multiple IBM batches."""

    def __str__(self) -> str:
        return self.value


class JobOptions(RequestBase):
    """Additional options for a job request"""

    execution_mode: ExecutionMode = pydantic.Field(default=ExecutionMode.BATCH)
    """ Execution mode type. Default is BATCH"""


class CircuitOptions(RequestBase):
    """Qesem circuits circuit_options"""

    error_suppression_only: bool = False
    """ No error mitigation. This results in a much shorter but biased run. When True, the `shots`
    parameter becomes mandatory, while precision and observables will be ignored!"""

    twirl: bool | None = None
    """ Use twirls during transpilation. Only relevant when error_suppression_only is True
    (Otherwise it is always on)."""

    transpilation_level: TranspilationLevel = pydantic.Field(default=TranspilationLevel.STANDARD)
    """ Transpilation level type"""

    parallel_execution: bool = False
    """
    Whether to parallel the circuit over multiple copies (if possible).
    Useful for small circuits over large QPUs.
    """

    @pydantic.model_validator(mode="after")
    def twirl_default(self) -> "CircuitOptions":
        if self.twirl is None:
            self.twirl = not self.error_suppression_only
        return self


def _check_circuit(  # type: ignore[no-any-unimported]
    value: qiskit.QuantumCircuit | str,
) -> qiskit.QuantumCircuit:
    if isinstance(value, str):
        with contextlib.suppress(Exception):
            value = qiskit.qasm3.loads(value)

    if isinstance(value, str):
        with contextlib.suppress(Exception):
            value = qiskit.QuantumCircuit.from_qasm_str(value)

    if not isinstance(value, qiskit.QuantumCircuit):
        raise ValueError("Circuit must be a valid Qiskit QuantumCircuit or QASM string")

    return value


def _serialize_circuit(value: qiskit.QuantumCircuit) -> str:  # type: ignore[no-any-unimported]
    result = qiskit.qasm3.dumps(value)
    if not isinstance(result, str):
        raise ValueError("Failed to serialize the circuit")

    return result


class BareCircuit(RequestBase):  # type: ignore[no-any-unimported]
    circuit: qiskit.QuantumCircuit  # type: ignore[no-any-unimported]
    "The quantum circuit to be executed."

    @pydantic.field_validator("circuit", mode="plain", json_schema_input_type=str)
    @classmethod
    def check_circuit(cls, value: qiskit.QuantumCircuit | str) -> qiskit.QuantumCircuit:  # type: ignore[no-any-unimported] # pylint: disable=line-too-long
        return _check_circuit(value)

    @pydantic.field_serializer("circuit", mode="plain", return_type=str)
    def serialize_circuit(self, value: qiskit.QuantumCircuit) -> str:  # type: ignore[no-any-unimported] # pylint: disable=line-too-long
        return _serialize_circuit(value)


class ParameterizedCircuit(BareCircuit):  # type: ignore[no-any-unimported]
    parameters: dict[str, tuple[float, ...]] | None = None
    "Optional dictionary mapping parameter names to their values for parameterized circuits. "

    @pydantic.model_validator(mode="after")
    def check_parameters(self) -> "ParameterizedCircuit":
        if self.parameters is None:
            if len(set(map(str, self.circuit.parameters))) > 0:
                raise ValueError("Parameters must match the circuit parameters")
            return self

        if set(map(str, self.parameters.keys())) != set(map(str, self.circuit.parameters)):
            raise ValueError("Parameters must match the circuit parameters")

        if len(self.parameters) > 0:
            if any(
                re.search(r"[^\w\d]", p, flags=re.U)
                for p in self.parameters  # pylint: disable=not-an-iterable
            ):
                raise ValueError(
                    "Parameter names must contain only alphanumeric characters, got: "
                    f"{list(self.parameters.keys())}"
                )

            # check all parameters are of the same length
            parameter_value_lengths = set(len(v) for v in self.parameters.values())
            if len(parameter_value_lengths) > 1:
                raise ValueError("All parameter values must have the same length")

        return self


class PrecisionPerFactor(pydantic.RootModel[dict[float, float]]):
    """A dictionary mapping quantum error tuning factors (error amplification or reduction
    factors) to desired precisions (for all observables)."""

    @pydantic.model_validator(mode="after")
    def check_positive_keys_and_values(self) -> "PrecisionPerFactor":
        for factor, precision in self.root.items():
            if factor < 0.0:
                raise ValueError("Quantum error tuning factors must be non-negative")
            if precision <= 0.0:
                raise ValueError("Precision values must be positive")
        return self

    @pydantic.model_validator(mode="after")
    def check_non_empty(self) -> "PrecisionPerFactor":
        if len(self.root) == 0:
            raise ValueError("Precision per factor cannot be empty")
        return self


class Circuit(ParameterizedCircuit):  # type: ignore[no-any-unimported]
    """A quantum circuit configuration including the circuit itself,
    observables to measure, and execution parameters."""

    observables: tuple[Observable, ...]
    """Tuple of observables to be measured. Each observable represents a measurement
    configuration."""

    observables_metadata: tuple[ObservableMetadata, ...] | None = None
    """Tuple of metadata for the observables.
    Each metadata corresponds to the observable at the same index."""

    precision: float | PrecisionPerFactor
    """Target precision for the error mitigated expectation value measurements (a.k.a, 0.0
    error reduction factor).
    If a `PrecisionPerFactor` is provided, it should be a map from a quantum error tuning factor 
    (error amplification or reduction factor) to the desired precision at that factor 
    (for all observables).
    """

    options: CircuitOptions
    "Additional options for circuit execution"

    @pydantic.model_validator(mode="after")
    def _precision_per_factor_to_float(self) -> "Circuit":
        """
        Transform a precision per factor with single key 0.0 to a float for backward compatibility
        and convenience.
        """
        if isinstance(self.precision, PrecisionPerFactor) and set(self.precision.root.keys()) == {
            0.0
        }:
            self.precision = self.precision.root[0.0]

        return self

    @pydantic.model_validator(mode="after")
    def check_parameters_and_observables(self) -> "Circuit":
        if self.parameters and len(self.parameters) > 0:
            # check that the number of observables is equal to the number of parameters values
            parameter_value_lengths = set(len(v) for v in self.parameters.values())
            if len(self.observables) != list(parameter_value_lengths)[0]:
                raise ValueError(
                    "Number of observables must be equal to the number of parameter values"
                )

        if self.observables_metadata is not None and len(self.observables_metadata) != len(
            self.observables
        ):
            raise ValueError(
                "The number of observable metadata items must match the number of observables"
            )

        return self

    @pydantic.field_validator("options")
    @classmethod
    def validate_error_suppression_only(cls, value: CircuitOptions) -> CircuitOptions:
        if value.error_suppression_only:
            raise ValueError("Wrong circuit type!")
        if not value.twirl:
            raise ValueError("Twirling cannot be disabled for circuits with error mitigation!")
        return value


class ErrorSuppressionCircuit(ParameterizedCircuit):  # type: ignore[no-any-unimported]
    shots: int
    """Amount of shots to run this circuit. Only viable when error-suppression only is True!"""

    options: CircuitOptions
    "Additional options for circuit execution"

    @pydantic.field_validator("options")
    @classmethod
    def validate_error_suppression_only(cls, value: CircuitOptions) -> CircuitOptions:
        if not value.error_suppression_only:
            raise ValueError("Wrong circuit type!")
        return value


class QPUTime(TypedDict):
    """Time metrics for quantum processing unit (QPU) usage."""

    execution: datetime.timedelta
    "Actual time spent executing the quantum circuit on the QPU"

    estimation: NotRequired[datetime.timedelta]
    "Estimated time required for QPU execution, may not be present"


class TranspiledCircuit(pydantic.BaseModel):  # type: ignore[no-any-unimported]
    """Circuit to be executed on QPU"""

    circuit: qiskit.QuantumCircuit  # type: ignore[no-any-unimported]
    """The quantum circuit after optimization, ready for execution."""

    qubit_maps: list[dict[int, int]] = pydantic.Field(
        validation_alias=pydantic.AliasChoices("qubit_maps", "qubit_map")
    )
    """
    A list of mapping between logical qubits in the original circuit and physical qubits on the
    QPU, one for each copy of the original circuit (if parallel execution is not used, will
    contain only one mapping).
    """

    num_measurement_bases: int
    "Number of different measurement bases required for this circuit"

    @pydantic.field_validator("qubit_maps", mode="before")
    @classmethod
    def qubit_map_backward_compatibility(
        cls, value: list[dict[int, int]] | dict[int, int]
    ) -> list[dict[int, int]]:
        # qubit map was a dict in the past
        if isinstance(value, dict):
            return [value]

        return value

    @pydantic.field_validator("circuit", mode="plain", json_schema_input_type=str)
    @classmethod
    def check_circuit(  # type: ignore[no-any-unimported]
        cls,
        value: qiskit.QuantumCircuit | str,
    ) -> qiskit.QuantumCircuit:
        return _check_circuit(value)

    @pydantic.field_serializer("circuit", mode="plain", return_type=str)
    def serialize_circuit(  # type: ignore[no-any-unimported]
        self,
        value: qiskit.QuantumCircuit,
    ) -> str:
        return _serialize_circuit(value)


class ExecutionDetails(ResponseBase):
    """Detailed statistics about the quantum circuit execution."""

    total_shots: int
    "Total number of times the quantum circuit was executed"

    mitigation_shots: int
    "Number of shots used for error mitigation"

    gate_fidelities: dict[str, float]
    "Dictionary mapping gate names to their measured fidelities on the QPU"

    transpiled_circuits: list[TranspiledCircuit] | None = None
    """List of circuits after optimization and mapping to the QPU architecture."""


class JobStep(pydantic.BaseModel):
    """Represents a single step in a job progress"""

    name: Annotated[str, pydantic.Field(description="The name of the step")]


class JobProgress(pydantic.BaseModel):
    """Represents job progress, i.e. a list of sequential steps"""

    steps: Annotated[
        list[JobStep],
        pydantic.Field(
            description="List of steps corresponding to JobStep values",
            default_factory=list,
        ),
    ]


class JobDetails(ResponseBase):
    """Detailed information about a quantum job, including its status, execution details,
    and results."""

    account_id: str
    "The unique identifier of the user account"

    account_email: str
    "The email address associated with the user account"

    job_id: str
    "The unique identifier of the job"

    description: str = ""
    "Optional description of the job"

    masked_account_token: str
    "Partially hidden account authentication token"

    masked_qpu_token: str
    "Partially hidden QPU access token"

    qpu_name: str
    "Name of the quantum processing unit (or simulator) being used"

    circuit: Circuit | ErrorSuppressionCircuit | None = None
    "The quantum circuit to be executed. Returns only if `include_circuit` is True"

    precision_mode: PrecisionMode | None = None
    "The precision mode used for execution. Can only be used when parameters are set."

    status: JobStatus
    "Current status of the job"

    analytical_qpu_time_estimation: datetime.timedelta | None
    "Theoretical estimation of QPU execution time"

    empirical_qpu_time_estimation: datetime.timedelta | None = None
    "Measured estimation of QPU execution time based on actual runs"

    total_execution_time: datetime.timedelta
    "Total time taken for the job execution. Includes QPU and classical processing time."

    created_at: datetime.datetime
    "Timestamp when the job was created"

    updated_at: datetime.datetime
    "Timestamp when the job was last updated"

    qpu_time: QPUTime | None
    "Actual QPU time used for execution and estimation."

    qpu_time_limit: datetime.timedelta | None = None
    "Maximum allowed QPU execution time"

    warnings: list[str] | None = None
    "List of warning messages generated during job execution"

    errors: list[str] | None = None
    "List of error messages generated during job execution"

    empirical_estimation_mitigation_results: QesemResults | None = None
    "Mitigation results obtained during empirical time estimation."

    intermediate_results: QesemResults | None = None
    "Partial results obtained during job execution."

    results: QesResults | QesemResults | None = None
    "Final results of the quantum computation. Returns only if `include_results` is True"

    execution_details: ExecutionDetails | None = None
    "Information about the execution process. Includes total shots, mitigation shots, and gate fidelities."  # pylint: disable=line-too-long

    empirical_estimation_execution_details: ExecutionDetails | None = None
    "Information about the empirical time estimation execution process. Includes total shots, mitigation shots, and gate fidelities."  # pylint: disable=line-too-long

    progress: JobProgress | None = None
    "Current progress information of the job. Printed automatically when calling `qedma_client.wait_for_job_complete()`."  # pylint: disable=line-too-long

    execution_mode: ExecutionMode
    "The mode of execution."

    enable_notifications: bool = True
    "Whether to enable email notifications for this job."

    def __str__(self) -> str:
        return self.model_dump_json(indent=4)


class CharacterizationJobStatus(str, enum.Enum):
    """The status of a job."""

    RUNNING = "RUNNING"
    """Job started running. Monitor its progress using the `qedma_client.wait_for_job_complete()`
    method."""
    SUCCEEDED = "SUCCEEDED"
    """Job finished successfully. The user can now get the results via the `qedma_client.get_job()`
    API with the include_results = True flag."""
    FAILED = "FAILED"
    "Job failed. Review the error message in the `job.errors` field." ""
    CANCELLED = "CANCELLED"
    "The job was cancelled by the user."

    def __str__(self) -> str:
        return self.value


class GateInfidelity(ResponseBase):
    name: str
    qubits: tuple[int, ...]
    infidelity: float


class CharacterizationJobDetails(ResponseBase):
    """Detailed information about a quantum job, including its status, execution details,
    and results."""

    account_id: str
    "The unique identifier of the user account"

    account_email: str
    "The email address associated with the user account"

    job_id: str
    "The unique identifier of the job"

    masked_account_token: str
    "Partially hidden account authentication token"

    masked_qpu_token: str
    "Partially hidden QPU access token"

    qpu_name: str
    "Name of the quantum processing unit (or simulator) being used"

    circuit: BareCircuit | None
    "The quantum circuit to choose the layout for"

    status: CharacterizationJobStatus
    "Current status of the job"

    created_at: datetime.datetime
    "Timestamp when the job was created"

    updated_at: datetime.datetime
    "Timestamp when the job was last updated"

    warnings: list[str] | None = None
    "List of warning messages generated during job execution"

    errors: list[str] | None = None
    "List of error messages generated during job execution"

    measurement_errors: dict[int, float] | None = None
    "qubits measurement errors"

    gate_infidelities: list[GateInfidelity] | None = None
    "Gate infidelities per gate type and qubits"

    layout_optimized_circuit: BareCircuit | None = None
    "The quantum circuit after layout optimization"

    qubit_map: dict[int, int] | None = None
    "The chosen mapping of the layout optimization process"

    enable_notifications: bool = True
    "Whether to enable email notifications for this job."

    def __str__(self) -> str:
        return self.model_dump_json(indent=4)


ObservablesGroups: TypeAlias = (  # type: ignore[no-any-unimported]
    Observable
    | qiskit.quantum_info.SparseObservable
    | qiskit.quantum_info.SparsePauliOp
    | Sequence[
        Observable | qiskit.quantum_info.SparsePauliOp | qiskit.quantum_info.SparseObservable
    ]
)


class JobRequestBase(RequestBase):
    """Request to create a new job"""

    circuit: Circuit | ErrorSuppressionCircuit
    backend: str
    empirical_time_estimation: bool
    precision_mode: PrecisionMode | None = None
    description: str = ""
    enable_notifications: bool = True
    provider: BaseProvider
    single_mitigation_step: bool = False

    @pydantic.model_validator(mode="after")
    def validate_precision_mode(self) -> Self:
        """Validates the precision mode."""
        if isinstance(self.circuit, ErrorSuppressionCircuit):
            return self

        if (self.circuit.parameters is None) != (self.precision_mode is None):
            raise ValueError("Parameters and precision mode must be both set or unset")
        return self


class CharacterizationJobRequestBase(RequestBase):
    """Request to create a new job"""

    circuit: BareCircuit
    backend: str
    description: str = ""
    enable_notifications: bool = True
    provider: BaseProvider

    @pydantic.model_validator(mode="after")
    def validate_circuit_type(self) -> Self:
        """Validates the circuit type."""
        if type(self.circuit) is not BareCircuit:  # pylint: disable=unidiomatic-typecheck
            raise TypeError("circuit must be exactly of type BareCircuit")

        return self


class StartJobRequest(RequestBase):
    """Start a job."""

    max_qpu_time: datetime.timedelta
    options: JobOptions
    force_start: bool = False


class GetJobsDetailsResponse(ResponseBase):
    """An internal object."""

    jobs: list[JobDetails]


class GetCharJobsDetailsResponse(ResponseBase):
    """An internal object."""

    jobs: list[CharacterizationJobDetails]


class RegisterQpuTokenRequest(RequestBase):
    """Store qpu token request model"""

    qpu_token: str


class DecomposeResponse(ResponseBase):
    """Decompose response model"""

    parametrized_circ: str
    meas_params: dict[str, list[float]]
    obs_per_basis: list[Observable]
    relative_l2_trunc_err: float


class QedmaServerError(Exception):
    """An exception raised when the server returns an error."""

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details is None:
            return super().__str__()
        return f"{super().__str__()}. Details: {self.details}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message}, details={self.details})"


class QedmaBadGatewayError(QedmaServerError):
    pass


class ResultNotReadyError(QedmaServerError):
    """An exception raised when the server returns an error."""

    def __init__(self) -> None:
        super().__init__("Result is not ready yet")


def model_dump_fallback(value: Any) -> Any:
    if isinstance(value, qiskit.quantum_info.SparseObservable):
        return Observable.from_sparse_observable(value).model_dump()

    return value


class ClientJobDetails(pydantic.BaseModel):
    """Detailed information about a quantum job, including its status, execution details,
    and results.
    Same as JobDetails, but meant to be returned to the client."""

    model_config = pydantic.ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=True,
    )

    account_id: str
    "The unique identifier of the user account"

    account_email: str
    "The email address associated with the user account"

    job_id: str
    "The unique identifier of the job"

    description: str = ""
    "Optional description of the job"

    masked_account_token: str
    "Partially hidden account authentication token"

    masked_qpu_token: str
    "Partially hidden QPU access token"

    qpu_name: str
    "Name of the quantum processing unit (or simulator) being used"

    circuit: Circuit | ErrorSuppressionCircuit | None = None
    "The quantum circuit to be executed. Returns only if `include_circuit` is True"

    precision_mode: PrecisionMode | None = None
    "The precision mode used for execution. Can only be used when parameters are set."

    status: JobStatus
    "Current status of the job"

    analytical_qpu_time_estimation: datetime.timedelta | None
    "Theoretical estimation of QPU execution time"

    empirical_qpu_time_estimation: datetime.timedelta | None = None
    "Measured estimation of QPU execution time based on actual runs"

    total_execution_time: datetime.timedelta
    "Total time taken for the job execution. Includes QPU and classical processing time."

    created_at: datetime.datetime
    "Timestamp when the job was created"

    updated_at: datetime.datetime
    "Timestamp when the job was last updated"

    qpu_time: QPUTime | None
    "Actual QPU time used for execution and estimation."

    qpu_time_limit: datetime.timedelta | None = None
    "Maximum allowed QPU execution time"

    warnings: list[str] | None = None
    "List of warning messages generated during job execution"

    errors: list[str] | None = None
    "List of error messages generated during job execution"

    empirical_estimation_mitigation_results: QiskitResults | QesemResults | None = None
    "Mitigation results obtained during empirical time estimation."

    intermediate_results: QiskitResults | QesemResults | None = None
    "Partial results obtained during job execution."

    results: QiskitResults | QesemResults | QesResults | None = None
    "Final results of the quantum computation. Returns only if `include_results` is True"

    execution_details: ExecutionDetails | None = None
    "Information about the execution process. Includes total shots, mitigation shots, and gate fidelities."  # pylint: disable=line-too-long

    empirical_estimation_execution_details: ExecutionDetails | None = None
    "Information about the empirical time estimation execution process. Includes total shots, mitigation shots, and gate fidelities."  # pylint: disable=line-too-long

    progress: JobProgress | None = None
    "Current progress information of the job. Printed automatically when calling `qedma_client.wait_for_job_complete()`."  # pylint: disable=line-too-long

    execution_mode: ExecutionMode
    "The mode of execution."

    enable_notifications: bool = True
    "Whether to enable email notifications for this job."

    def __str__(self) -> str:
        return self.model_dump_json(indent=4, fallback=model_dump_fallback)

    @classmethod
    def from_job_details(
        cls, job_details: JobDetails, qedma_observable_model: bool = False
    ) -> "ClientJobDetails":
        """
        Convert a JobDetails object to a ClientJobDetails object.
        :param job_details: The JobDetails object to convert.
        :param qedma_observable_model: Whether to return the results with Qedma's observable model,
         or Qiskit SparsePauliOp.
        :return: The converted ClientJobDetails object.
        """
        job = cls(**job_details.model_dump())

        if qedma_observable_model:
            return job

        if isinstance(job.empirical_estimation_mitigation_results, QesemResults):
            job.empirical_estimation_mitigation_results = (  # pylint: disable=invalid-name
                QiskitResults.from_result(job.empirical_estimation_mitigation_results)
            )
        if job_details.intermediate_results is not None:
            job.intermediate_results = (
                QiskitResults.from_result(job.intermediate_results)
                if isinstance(job.intermediate_results, QesemResults)
                else job.intermediate_results
            )
        if job_details.results is not None and isinstance(job.results, QesemResults):
            job.results = QiskitResults.from_result(job.results)

        return job
