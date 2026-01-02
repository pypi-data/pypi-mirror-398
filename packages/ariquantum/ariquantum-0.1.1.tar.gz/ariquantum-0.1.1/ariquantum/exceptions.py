class QuantumError(Exception):
    """Base exception class for all quantum computing related errors.

    This exception serves as the parent class for all specific quantum
    computing errors in the ariquantum framework.

    Args:
        message: Custom error message. Defaults to generic quantum error message.
    """
    def __init__(self, message='An error related to quantum computing'):
        self.message = message
        super().__init__(self.message)

class InitializStateError(QuantumError):
    """Exception raised for invalid quantum state initialization.

    This error occurs when attempting to initialize a quantum system
    with an invalid state configuration.

    Args:
        message: Custom error message describing the specific initialization error.
    """
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

class QuantumMeasurementError(QuantumError):
    """Exception raised for invalid quantum measurement operations.

    This error occurs when attempting to perform measurements or operations
    that violate quantum measurement principles (e.g., applying certain gates
    to already measured qubits).

    Args:
        message: Custom error message describing the specific measurement error.
    """
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

class GateAngleError(QuantumError):
    """Exception raised for invalid gate angle parameters.

    This error occurs when providing invalid angle values for parameterized
    quantum gates. Different gates have different valid angle ranges.

    Args:
        gate_name: Name of the gate that received the invalid angle.
        message: Custom error message. If not provided, generates a default
                 message with allowed angle values for the specific gate.
    """
    def __init__(self, gate_name, message=None):
        if not message:
            if gate_name in ['x', 'y', 'z']:
                allowed = '1, 0.5, -0.5, 0.25, -0.25.'
            else:
                allowed = '1, -1.'
            message = f'Invalid angle value for {gate_name} gate. ' \
                      f'Allowed values: ' + allowed
        self.message = message
        super().__init__(self.message)

class QubitIndexError(QuantumError):
    """Exception raised for invalid qubit indices.

    This error occurs when attempting to access or manipulate qubits using
    indices that are out of range, negative, or duplicated in operations
    that require unique qubit indices.

    Args:
        message: Custom error message describing the specific index error.
    """
    def __init__(self, message=None):
        self.message = message
        super().__init__(self.message)

