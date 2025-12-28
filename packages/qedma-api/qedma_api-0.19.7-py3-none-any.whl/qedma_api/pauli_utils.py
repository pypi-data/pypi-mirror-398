"""
Utility functions for working with Pauli operators and observables.
"""


def pauli_to_qiskit_pauli(pauli_str: str, num_qubits: int) -> str:
    """Convert a Pauli string to Qiskit format.

    :param pauli_str: The Pauli string in our format (e.g., "X0,Y1")
    :param num_qubits: The total number of qubits in the system
    :return: The Pauli string in Qiskit format (e.g., "XYI")
    :raises ValueError: If any qubit index is out of range
    """
    if not pauli_str or pauli_str == "I":
        return "I" * num_qubits

    pauli_label = ["I"] * num_qubits
    for term in pauli_str.split(","):
        op = term[0]  # X, Y, or Z
        qubit = int(term[1:])
        if qubit >= num_qubits:
            raise ValueError(f"Qubit index {qubit} is out of range for num_qubits={num_qubits}")
        pauli_label[qubit] = op
    return "".join(pauli_label[::-1])


def qiskit_pauli_to_pauli(pauli_str: str) -> str:
    """Convert a Qiskit Pauli string to our format.

    :param pauli_str: The Pauli string in Qiskit format (e.g., "XYI")
    :return: The Pauli string in our format (e.g., "X0,Y1")
    """
    terms = []
    for i, op in enumerate(pauli_str[::-1]):
        if op != "I":
            terms.append(f"{op}{i}")

    if not terms:
        return "I"

    return ",".join(terms)
