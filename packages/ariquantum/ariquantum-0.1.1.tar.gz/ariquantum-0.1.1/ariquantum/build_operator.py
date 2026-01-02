import numpy as np


def build_single_qubit_operator(num_qubits, qubit, operator):
    """Construct a full quantum operator for a single-qubit gate applied to a
    multi-qubit system.

    Args:
        num_qubits: Total number of qubits in the quantum system.
        qubit: Index of the target qubit (0-based) to apply the operator to.
        operator: 2x2 matrix representing the single-qubit gate operation.

    Returns:
        A 2 ** num_qubits × 2 ** num_qubits matrix representing the full system operator.
    """
    full_operator = 1

    for i in range(num_qubits):
        if i == qubit:
            full_operator = np.kron(full_operator, operator)
        else:
            full_operator = np.kron(full_operator, np.identity(2))

    return full_operator

def build_two_qubit_operator(num_qubits, controls, targets, operator, anticontrol):
    """Construct a full quantum operator for a  two-qubit gate applied to a
    multi-qubit system.

    Args:
        num_qubits: Total number of qubits in the quantum system.
        controls: List of control qubit indices (0-based).
        targets: List of target qubit indices (0-based) where the operator is applied.
        operator: 2x2 matrix representing the single-qubit gate operation to apply
                 to the target qubit when control conditions are met.
        anticontrol: Boolean flag indicating whether to use anti-control (True)
                    or regular control (False). Anti-control activates when
                    control qubits are in |0⟩ state.

    Returns:
        A 2 ** num_qubits × 2 ** num_qubits matrix representing the controlled
        operation.
    """
    full_operator_control = 1
    full_operator_target = 1

    for i in range(num_qubits):
        if i in controls:
            if anticontrol:
                full_operator_control = np.kron(full_operator_control,
                                                np.array([[0, 0], [0, 1]]))
                full_operator_target = np.kron(full_operator_target,
                                               np.array([[1, 0], [0, 0]]))
            else:
                full_operator_control = np.kron(full_operator_control,
                                                np.array([[1, 0], [0, 0]]))
                full_operator_target = np.kron(full_operator_target,
                                                np.array([[0, 0], [0, 1]]))
        elif i in targets:
            full_operator_control = np.kron(full_operator_control,
                                            np.identity(2))
            full_operator_target = np.kron(full_operator_target,
                                           operator)
        else:
            full_operator_control = np.kron(full_operator_control,
                                            np.identity(2))
            full_operator_target = np.kron(full_operator_target,
                                           np.identity(2))

    return full_operator_control + full_operator_target

def build_three_qubit_operator(num_qubits, controls, targets, operator, anticontrol):
    """Construct a full quantum operator for a  three-qubit gate applied to a
    multi-qubit system.

    Args:
        num_qubits: Total number of qubits in the quantum system.
        controls: List of control qubit indices (0-based).
        targets: List of target qubit indices (0-based) where the operator is applied.
        operator: 2x2 matrix representing the single-qubit gate operation to apply
                 to the target qubit when control conditions are met.
        anticontrol: Boolean flag indicating whether to use anti-control (True)
                    or regular control (False). Anti-control activates when
                    control qubits are in |0⟩ state.

    Returns:
        A 2 ** num_qubits × 2 ** num_qubits matrix representing the multi-controlled
        operation.
    """
    full_operator_control = 1
    full_operator_target = 1

    for i in range(num_qubits):
        if i in controls:
            if anticontrol:
                full_operator_control = np.kron(full_operator_control,
                                                np.array([[1, 0], [0, 0]]))
                full_operator_target = np.kron(full_operator_target,
                                               np.array([[1, 0], [0, 0]]))
            else:
                full_operator_control = np.kron(full_operator_control,
                                                np.array([[0, 0], [0, 1]]))
                full_operator_target = np.kron(full_operator_target,
                                               np.array([[0, 0], [0, 1]]))
        elif i in targets:
            full_operator_control = np.kron(full_operator_control,
                                            np.identity(2))
            full_operator_target = np.kron(full_operator_target,
                                           operator)
        else:
            full_operator_control = np.kron(full_operator_control,
                                            np.identity(2))
            full_operator_target = np.kron(full_operator_target,
                                           np.identity(2))

    return np.identity(2 ** num_qubits) - full_operator_control + full_operator_target
