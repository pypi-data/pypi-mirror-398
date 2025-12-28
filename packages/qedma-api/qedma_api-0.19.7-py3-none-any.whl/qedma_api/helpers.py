"""
This module contains helper functions for the qedma_api module.
"""

import pathlib
import re
from typing import Literal

import numpy as np
import qiskit.converters
import qiskit.providers.backend
import qiskit.transpiler
import qiskit.transpiler.passes
import qiskit.transpiler.preset_passmanagers.builtin_plugins

from qedma_api import models


CONFIG_DIRECTORY = ".qedma"
CONFIG_FILE = "config"


def config_file_path() -> pathlib.Path:
    """path to file containing the api configuration"""
    directory_path = pathlib.Path(pathlib.Path.home().joinpath(CONFIG_DIRECTORY))
    directory_path.mkdir(exist_ok=True)

    return directory_path.joinpath(CONFIG_FILE)


def adapt_to_backend(  # type: ignore[no-any-unimported]
    circ: qiskit.QuantumCircuit,
    observables: list[models.Observable],
    *,
    backend: qiskit.providers.backend.BackendV2,
    optimization_level: Literal[1, 2, 3] = 1,
) -> tuple[qiskit.QuantumCircuit, list[models.Observable]]:
    """
    Adapt a circuit and observables to a backend qubits layout and basis gates.

    Useful for running with QESEM and transpilation level 0.
    """
    transpiled_circ = qiskit.transpile(circ, optimization_level=optimization_level, backend=backend)
    qmap = dict(enumerate(transpiled_circ.layout.final_index_layout()))
    for q in set().union(*(o.qubits for o in observables)):
        qmap.setdefault(q, q)

    transpiled_observables = [_embed_observable(o, qmap) for o in observables]

    return transpiled_circ, transpiled_observables


def parallelize_circuit(  # type: ignore[no-any-unimported]
    circ: qiskit.QuantumCircuit,
    observables: list[models.Observable],
    num_copies: int,
    *,
    backend: qiskit.providers.backend.BackendV2,
    optimization_level: Literal[1, 2, 3] = 3,
    seed: int | None = None,
) -> tuple[qiskit.QuantumCircuit, dict[models.Observable, list[models.Observable]]]:
    """
    This transpiled a circuit to a backend, and then parallelizes it by copying it `num_copies`
    times.

    :param circ: The circuit to parallelize
    :param observables: The observables to parallelize
    :param num_copies: The number of copies to make
    :param backend: The backend to transpile the circuit to
    :param seed: a seed for the random number generator (used in transpilation)
    :raises ValueError: If the circuit can not be fit into the backend with `num_copies` copies
     (after transpilation).
    :return: The parallelized circuit and a dictionary from each original observable to a list of
     observables in the parallelized circuit which measure the same expectation value.
     The returned circuit should be run with transpilation level 0.
    """
    transpiled_circ, transpiled_observables = adapt_to_backend(
        circ, observables, backend=backend, optimization_level=optimization_level
    )

    copied_circ, copied_observables = _copy_circ(
        transpiled_circ,
        num_copies,
        transpiled_qmap=_get_transpiled_qmap(transpiled_circ, transpiled_observables),
        transpiled_observables=transpiled_observables,
        transpiled_observables_dict=dict(zip(transpiled_observables, observables)),
    )

    try:
        routed_circ = (
            qiskit.transpiler.preset_passmanagers.builtin_plugins.SabreLayoutPassManager()
            .pass_manager(
                qiskit.transpiler.PassManagerConfig(
                    coupling_map=backend.coupling_map, seed_transpiler=seed
                ),
                optimization_level=3,
            )
            .run(copied_circ)
        )
    except qiskit.transpiler.TranspilerError:
        raise ValueError(  # pylint: disable=raise-missing-from
            f"Can not fit {num_copies} copies of the given into the backend"
        )

    routing_qmap = dict(enumerate(routed_circ.layout.final_index_layout()))
    routed_observables = {
        orig_o: [_embed_observable(o, routing_qmap) for o in o_copies]
        for orig_o, o_copies in copied_observables.items()
    }

    return routed_circ, routed_observables


def _get_transpiled_qmap(  # type: ignore[no-any-unimported]
    transpiled_circ: qiskit.QuantumCircuit, transpiled_observables: list[models.Observable]
) -> dict[int, int]:
    transpiled_index_layout = transpiled_circ.layout.final_index_layout()
    for q in set().union(*(o.qubits for o in transpiled_observables)):
        if q not in transpiled_index_layout:
            transpiled_index_layout.append(q)
    transpiled_qmap = dict(zip(transpiled_index_layout, _embed_zero_to_n(transpiled_index_layout)))
    return transpiled_qmap


def _copy_circ(  # type: ignore[no-any-unimported]
    transpiled_circ: qiskit.QuantumCircuit,
    num_copies: int,
    *,
    transpiled_qmap: dict[int, int],
    transpiled_observables: list[models.Observable],
    transpiled_observables_dict: dict[models.Observable, models.Observable],
) -> tuple[qiskit.QuantumCircuit, dict[models.Observable, list[models.Observable]]]:
    transpiled_circ = _remove_idle_wires(transpiled_circ, observables=transpiled_observables)
    circ_instruction = qiskit.converters.circuit_to_instruction(transpiled_circ)
    n_qbits = circ_instruction.num_qubits
    n_clbit = circ_instruction.num_clbits

    copied_circ = qiskit.QuantumCircuit(n_qbits * num_copies, n_clbit * num_copies)
    for i in range(num_copies):
        copied_circ.append(
            circ_instruction,
            list(range(i * n_qbits, (i + 1) * n_qbits)),
            list(range(i * n_clbit, (i + 1) * n_clbit)),
        )

    copied_circ = copied_circ.decompose(circ_instruction.name)

    copied_observables: dict[models.Observable, list[models.Observable]] = {}
    for i in range(num_copies):
        copy_qmap = {k: (v + i * n_qbits) for k, v in transpiled_qmap.items()}
        for o in transpiled_observables:
            copied_observables.setdefault(transpiled_observables_dict[o], []).append(
                _embed_observable(o, copy_qmap)
            )

    return copied_circ, copied_observables


def _embed_zero_to_n(l: list[int]) -> list[int]:
    return np.argsort(  # type: ignore[no-any-return]
        np.argsort(np.asarray(l, dtype=np.int_))
    ).tolist()


def _embed_observable(
    observable: models.Observable, qubit_map: dict[int, int]
) -> models.Observable:
    new_observable = {}
    for k, v in observable.root.items():
        old_terms = [(op, int(s)) for op, s in re.findall(r"([XYZ])(\d+)", k)]
        new_observable[",".join([o + str(qubit_map[q]) for o, q in old_terms])] = v
    return models.Observable(new_observable)


def _count_gates(  # type: ignore[no-any-unimported]
    qc: qiskit.QuantumCircuit,
) -> dict[qiskit.circuit.Qubit, int]:
    gate_count = {qubit: 0 for qubit in qc.qubits}
    for gate in qc.data:
        for qubit in gate.qubits:
            gate_count[qubit] += 1
    return gate_count


def _remove_idle_wires(  # type: ignore[no-any-unimported]
    qc: qiskit.QuantumCircuit, *, observables: list[models.Observable]
) -> qiskit.QuantumCircuit:
    observables_qubits = set().union(*(o.qubits for o in observables))
    qc_out = qc.copy()
    gate_count = _count_gates(qc_out)
    non_idle_indexes = set()
    for qubit, count in gate_count.items():
        if count == 0 and qc.qubits.index(qubit) not in observables_qubits:
            qc_out.qubits.remove(qubit)
        else:
            non_idle_indexes.add(qc.qubits.index(qubit))

    new_circ = qiskit.QuantumCircuit(len(qc_out.qubits))
    for instr, qargs, cargs in qc_out.data:
        if len(cargs) > 0:
            raise ValueError("Instructions with classical registers are not supported")
        new_circ.append(
            instr, [qc_out.qubits.index(q) for q in qargs], [qc_out.clbits.index(c) for c in cargs]
        )

    index_layout = _embed_zero_to_n(
        [q for q in qc_out.layout.final_index_layout() if q in non_idle_indexes]
    )

    layout = qiskit.transpiler.TranspileLayout(
        initial_layout=qiskit.transpiler.Layout.from_intlist(index_layout, new_circ.qregs[0]),
        input_qubit_mapping={q: i for i, q in enumerate(new_circ.qubits)},
        _input_qubit_count=len(new_circ.qubits),
        _output_qubit_list=new_circ.qubits,
    )

    new_circ._layout = layout  # pylint: disable=protected-access
    return new_circ


def save_token(api_token: str) -> None:
    """
    Save api token locally for default use in client
    """
    token_file_path = config_file_path()
    qedma_params = models.QEDMAParams(api_token=api_token)
    with open(token_file_path, "w", encoding="utf-8") as f:
        f.write(qedma_params.model_dump_json())
