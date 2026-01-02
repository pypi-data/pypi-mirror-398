from .exceptions import QubitIndexError


def validate_qubit_index(num_qubits, ctrls, targs):
    """Validate qubit indices for quantum operations.

    This function checks if the provided control and target qubit indices
    are valid for a quantum system with the specified number of qubits.

    Args:
        num_qubits: Total number of qubits in the quantum system.
                    Must be a positive integer.
        ctrls: List of control qubit indices. Can be empty if no controls.
        targs: List of target qubit indices. Must contain at least one index.

    Raises:
        QubitIndexError: If any of the following conditions are violated:

            * Duplicate qubit indices found in controls and targets.
            * Any qubit index is out of range [0, num_qubits-1].

    """
    qubits = ctrls + targs

    if len(qubits) != len(set(qubits)):
        raise QubitIndexError(
            "Duplicate qubit indices are not allowed."
        )
    if any(q >= num_qubits or q < 0 for q in qubits):
        raise QubitIndexError(
            "Qubit index out of range."
        )