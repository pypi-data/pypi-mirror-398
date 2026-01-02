from math import cos, sin, pi, e, log2
import numpy as np

from .build_operator import build_single_qubit_operator, build_two_qubit_operator, build_three_qubit_operator
from .visualization import draw_circuit, format_angle, text_state_vector
from .qubit import Qubit
from .exceptions import QuantumMeasurementError, GateAngleError, InitializStateError, QubitIndexError
from .helpers import validate_qubit_index


class QuantumRegister:
    """The quantum circuit.

    Review
    ======

    :class:`QuantumRegister` is a quantum circuit, a system of several qubits
    that can be in entangled states. This class provides a basic set of
    operations for working with multi-qubit systems, including single-qubit and
    multi-qubit gates, measurements, and visualization

    Register attributes
    ===================

    :class:`QuantumRegister` has a two public attributes. They are immutable.

    * :attr:`num_qubits`: The number of qubits in the circuit.

    * :attr:`state`: The state vector of a quantum system consisting of
      :attr:`num_qubits` of qubits. It has a dimension of 2 ** :attr:`num_qubits`.

    Main features
    =============

    Single-Qubit Operations
    -----------------------

    * * :meth:`i(qubit)` - Identity gate.

    * :meth:`x(qubit, angle=1)` - Pauli-X gate.

    * :meth:`y(qubit, angle=1)` - Pauli-Y gate.

    * :meth:`z(qubit, angle=1)` - Pauli-Z gate.

    * :meth:`s(qubit, angle=1)` - Square-root of Pauli-Z gate.

    * :meth:`t(qubit, angle=1)` - pi/8 gate.

    * :meth:`h(qubit)` - Hadamard gate.

    * :meth:`u(qubit, theta, phi, lam)` - Generic single-qubit gate.

    * :meth:`p(qubit, angle)` - Phase gate.

    * :meth:`rx(qubit, angle)` - Rotation around the X-axis.

    * :meth:`ry(qubit, angle)` - Rotation around the Y-axis.

    * :meth:`rz(qubit, angle)` - Rotation around the Z-axis.

    Two-Qubit Operations
    --------------------

    * :meth:`cx(control, target, angle=1, anticontrol=False)` - Controlled-X gate.

    * :meth:`cy(control, target, angle=1, anticontrol=False)` - Controlled-Y gate.

    * :meth:`cz(control, target, angle=1, anticontrol=False)` - Controlled-Z gate.

    * :meth:`cs(control, target, angle=1, anticontrol=False)` - Controlled-S gate.

    * :meth:`ch(control, target, anticontrol=False)` - Controlled-Hadamard gate.

    * :meth:`cu(control, target, theta, phi, lam, gamma, anticontrol=False)` -
      Controlled-U gate (4-parameter two-qubit gate).

    * :meth:`cp(control, target, angle, anticontrol=False)` - Controlled-Phase gate.

    * :meth:`crx(control, target, angle, anticontrol=False)` - Controlled-RX gate.

    * :meth:`cry(control, target, angle, anticontrol=False)` - Controlled-RY gate.

    * :meth:`crz(control, target, angle, anticontrol=False)` - Controlled-RZ gate.

    * :meth:`swap(qubit1, qubit2)` - SWAP gate.

    Three-Qubit Operations
    ----------------------

    * :meth:`ccx(control1, control2, target, angle=1, anticontrol=False)` - Toffoli
      gate (CCNOT).

    * :meth:`ccz(control1, control2, target, angle=1, anticontrol=False)` - CCZ gate.

    * :meth:`cswap(control, target1, target2, anticontrol=False)` - Fredkin gate
      (Controlled-SWAP).

    Measurement Operations
    ----------------------

    * :meth:`measure(qubits=None)` - Measurement of specified qubits.

    * :meth:`get_counts(shots)` - Statistics of measurement results.

    Visualization Methods
    ---------------------

    * :meth:`as_bracket_string(decimals=4)` - The state vector in bracket notation.

    * :meth:`draw_circuit(show_initial=False)` - Visualization of the operation scheme.

    Implementation features
    =======================

    * All operations include checking the validity of qubit indexes and their states.

    * Many gates support fractional powers (for example, X^0.5).

    * Support for regular and anti-control gates.

    * After measuring a qubit, some quantum operations cannot be applied to it.

    Example:

    .. code-block:: python

      from ariquantum import QuantumRegister

      # Creating a circuit with 2 qubits
      qr = QuantumRegister(2, "0")

      # Apply Hadamard gate to the first qubit
      qr.h(0)

      # Apply a controlled-X gate on qubit 1б controlled by qubit 0
      qr.cx(0, 1)

      # Visualization of the scheme
      qr.draw_circuit()

    Output:

    .. code-block:: text

            ┌───┐
      q0 : ─│ H │───●─── :
            └───┘   │
                  ┌─┴─┐
      q1 : ───────│ X │─ :
                  └───┘
    """

    def __init__(self,
                 num_qubits: int,
                 state: str | list[str] | list[Qubit] = "0"):
        """Initializer of the quantum circuit.

        Args:
            num_qubits: Number of qubits in the circuit. Must be a positive integer.

            state: Initial state of the register. Defaults to "0".

                * Single string: One of '0', '1', '+', '-', 'i', or '-i'. Applied to all qubits.

                  For example:

                  * ``QuantumRegister(3, '1') # 3-qubit circuit in state |111⟩``
                  * ``QuantumRegister(2, '+') # 2-qubit circuit in state 0.5|00⟩ + 0.5|01⟩ +
                    0.5|10⟩ + 0.5|11⟩``

                * List of strings: Length must equal num_qubits. Each string must be a valid state.

                  For example:

                  * ``QuantumRegister(3, ['1', '1', '0']) # 3-qubit circuit in state |110⟩``
                  * ``QuantumRegister(2, ['0', '-']) # 2-qubit circuit: (|00⟩ - |01⟩)/√2``

                * List of Qubit objects: Length must equal num_qubits. Uses provided qubit instances.

                  For example:

                  * ``QuantumRegister(3, [Qubit('0'), Qubit('1'), Qubit('0')]) # State |110⟩``
                  * ``QuantumRegister(2, [Qubit([0.5, 0.866]), Qubit('1')]) # Custom state``
        Raises:
            InitializStateError: If the state parameter is invalid (wrong type, length, or values).
        """

        self.__num_qubits = num_qubits

        if isinstance(state, str):
            self.__qubits = [Qubit(state) for _ in range(num_qubits)]
            self.__init_states = ['|' + state + '⟩'] * self.__num_qubits
        elif isinstance(state, list) and len(state) == num_qubits:
            if all(isinstance(state[i], str) for i in range(num_qubits)):
                self.__qubits = [Qubit(state_q) for state_q in state]
                self.__init_states = ['|' + s + '⟩' for s in state]
            elif all(isinstance(state[i], Qubit) for i in range(num_qubits)):
                self.__qubits = state
                self.__init_states = [q.as_bracket_string() for q in state]
            else:
                raise InitializStateError(
                    f"Invalid initial state for QuantumRegister with {self.__num_qubits} qubits.\n"
                    f"The state must be one of the following:\n"
                    f"- A single string: '0', '1', '+', '-', 'i', '-i' (applied to all qubits);\n"
                    f"- A list of strings with length equal to num_qubits. "
                    f"Each string must be one of: '0', '1', '+', '-', 'i', '-i';\n"
                    f"- A list of Qubit objects with length equal to num_qubits;\n"
                    f"(defaults to all qubits in |0⟩ state)."
                )
        else:
            raise InitializStateError(
                f"Invalid initial state for QuantumRegister with {self.__num_qubits} qubits.\n"
                f"The state must be one of the following:\n"
                f"- A single string: '0', '1', '+', '-', 'i', '-i' (applied to all qubits);\n"
                f"- A list of strings with length equal to num_qubits. "
                f"Each string must be one of: '0', '1', '+', '-', 'i', '-i';\n"
                f"- A list of Qubit objects with length equal to num_qubits;\n"
                f"(defaults to all qubits in |0⟩ state)."
            )

        self.__state = self.__qubits[0].state
        for i in range(1, self.__num_qubits):
            self.__state = np.kron(self.__state, self.__qubits[i].state)

        self.__all_operations = []

        self.__is_measured = [False for _ in range(self.__num_qubits)]
        self.__measured_probabilities = None

    @property
    def num_qubits(self):
        """The number of qubits in the circuit.
        """
        return self.__num_qubits

    @property
    def state(self):
        """The state vector of a quantum system consisting of
        :attr:`num_qubits` of qubits. It has a dimension of 2 ** :attr:`num_qubits`."""
        return self.__state

    def __check_measured(self, ctrls, targ, op_str, gate):
        """Validate if gate can be applied to qubits based on their measurement status.

        This internal method checks whether a quantum gate can be safely applied to the
        specified qubits, considering which qubits have already been measured.

        Checks target qubits and control qubits. The measurement validation logic follows
        specific rules for different gate types.

        Args:
            ctrls: List of control qubit indices or empty list.
            targ: Target qubit index or list of target indices (for multi-target gates).
            op_str: String identifying the gate type.
            gate: Full gate name for error messages.

        Raises:
            QuantumMeasurementError: If gate cannot be applied due to measurement constraints.
        """
        if op_str in ['swap', 'cswap']:
            for i in range(2):
                if self.__is_measured[targ[i]]:
                    targ[i] = True
                else:
                    targ[i] = False
            if ctrls:
                ctrls[0] = True if self.__is_measured[ctrls[0]] else False

            if len(ctrls) == 0 and any(targ) or \
                all(ctrls) and len(set(targ)) == 1 or \
                not any(ctrls) and not any(targ):
                return
            else:
                raise QuantumMeasurementError(
                    f"Quantum gate {gate} cannot be applied to measured qubits."
                )
        else:
            for i in range(len(ctrls)):
                if self.__is_measured[ctrls[i]]:
                    ctrls[i] = True
                else:
                    ctrls[i] = False
            targ = True if self.__is_measured[targ] else False

            op_str1 = ['I', 'X', 'Y', 'Z', 'S', 'T', 'Rz', 'P']
            op_str2 = ['I', 'Z', 'S', 'T', 'Rz', 'P']

            if all(ctrls) and targ and op_str in op_str1 or \
                any(ctrls) and not targ or \
                not all(ctrls) and targ and op_str in op_str2 or \
                not any(ctrls) and not targ:
                return
            else:
                raise QuantumMeasurementError(
                    f"Quantum gate {gate} cannot be applied to measured qubits."
                )

    def measure(self, qubits=None):
        """Perform deferred measurement on one or more qubits in the quantum register.

        Implements the principle of deferred measurement, where qubits are marked as measured
        without immediately collapsing the wavefunction. This allows for continued quantum
        operations on unmeasured qubits while preventing specified operations on measured qubits.

        Args:
            qubits: Qubit indices to measure. Can be:

                * None: Measure all qubits in the register (default).
                * list[int]: Measure specific qubits.

        Returns:
            Binary string of measurement results (For example, "010" for three qubits).

        Raises:
            QubitIndexError: If any qubit index is out of range.
        """
        if qubits is None:
            qubits = list(range(self.__num_qubits))
        else:
            if len(qubits) != len(set(qubits)):
                raise QubitIndexError(
                    "Duplicate qubit indices are not allowed."
                )
            if any(q >= self.__num_qubits or q < 0 for q in qubits):
                raise QubitIndexError(
                    "Qubit index out of range."
                )
        for i in qubits:
            self.__all_operations.append(['↗', [], False, [i]])

        k = len(qubits)
        num_states = 2 ** self.__num_qubits
        outcome_probabilities = np.zeros(2 ** k, dtype=float)

        for i in range(num_states):
            outcome_index = 0
            for q in qubits:
                bit = (i >> (self.__num_qubits - 1 - q)) & 1
                outcome_index = (outcome_index << 1) | bit
            outcome_probabilities[outcome_index] += abs(self.__state[i]) ** 2

        total_prob = np.sum(outcome_probabilities)
        outcome_probabilities /= total_prob
        possible_outcomes = np.arange(2 ** k)
        chosen_outcome = np.random.choice(possible_outcomes, p=outcome_probabilities)

        self.__measured_probabilities = outcome_probabilities
        for q in qubits:
            self.__is_measured[q] = True

        bin_state = bin(chosen_outcome)
        bin_state = "0" * (k - len(bin_state[2:])) + bin_state[2:]
        return bin_state

    def get_counts(self, shots):
        """Obtain measurement statistics by repeatedly simulating the quantum circuit.

        Runs multiple simulations (shots) of the circuit to collect statistics about
        measurement outcomes. This is useful for estimating probabilities of different
        quantum states without collapsing the actual state vector.

        Args:
            shots: Number of simulation runs to perform. Must be a positive integer.

        Returns:
            Dictionary mapping measurement outcomes to their frequencies.
            Keys are binary strings representing qubit states (For example, "0101"),
            values are integers counting how many times that outcome occurred.

        Raises:
            QuantumMeasurementError: If called before any measurements have been performed.
        """
        if not all(self.__is_measured):
            raise QuantumMeasurementError(
                "Measurement is required before accessing results. "
            )

        probabilities = self.__measured_probabilities
        num_measure_qubits = int(log2(len(probabilities)))
        states = ["0" * (num_measure_qubits - len(bin(i)[2:])) + bin(i)[2:]
                  for i in range(2 ** num_measure_qubits)]

        result = {}

        for _ in range(shots):
            m = str(np.random.choice(states, p=probabilities))

            if m not in result:
                result[m] = 1
            else:
                result[m] += 1

        return result

    def i(self, qubit: int):
        """Apply I gate to the specified qubit.

        This gate does not perform any actions on the qubit. It leaves the state
        of the qubit completely unchanged.

        Visualization using the :meth:`draw_circuit()` method:

        .. code-block:: text

                ┌───┐
          q0 : ─│ I │─ :
                └───┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        self.__check_measured([], qubit, 'I', 'I')
        self.__all_operations.append(['I', [], False, [qubit]])
        self.__state = self.__state

    def x(self, qubit: int, angle=1):
        """Apply X gate to the specified qubit.

        Pauli-X gate. 180° rotation around the X-axis. An analog of the
        classical logic element NOT.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───┐
          q0 : ─│ X │─ :
                └───┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([], qubit, f'X^{angle}', f'X^{angle}')
            self.__all_operations.append([f'X^{angle}', [], False, [qubit]])
            angle = pi * angle
            x = np.array([
                [cos(angle / 2), complex(0, -sin(angle / 2))],
                [complex(0, -sin(angle / 2)), cos(angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([], qubit, 'X', 'X')
            self.__all_operations.append(['X', [], False, [qubit]])
            x = np.array([
                [0, 1],
                [1, 0]
            ])
        else:
            raise GateAngleError('x')

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, x)
        self.__state = np.dot(full_operator, self.__state)

    def y(self, qubit: int, angle=1):
        """Apply Y gate to the specified qubit.

        Pauli-Y gate. 180° rotation around the Y-axis. Adds phase and inverts.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───┐
          q0 : ─│ Y │─ :
                └───┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([], qubit, f'Y^{angle}', f'Y^{angle}')
            self.__all_operations.append([f'Y^{angle}', [], False, [qubit]])
            angle = pi * angle
            y = np.array([
                [cos(angle / 2), -sin(angle / 2)],
                [sin(angle / 2), cos(angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([], qubit, 'Y' ,'Y')
            self.__all_operations.append(['Y', [], False, [qubit]])
            y = np.array([
                [0, complex(0, -1)],
                [complex(0, 1), 0]
            ])
        else:
            raise GateAngleError('y')

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, y)
        self.__state = np.dot(full_operator, self.__state)

    def z(self, qubit: int, angle=1):
        """Apply Z gate to the specified qubit.

        Pauli-Z gate. 180° rotation around the Z-axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───┐
          q0 : ─│ Z │─ :
                └───┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([], qubit, 'Z', f'Z^{angle}')
            self.__all_operations.append([f'Z^{angle}', [], False, [qubit]])
            angle = pi * angle
            z = np.array([
                [e ** complex(0, -angle / 2), 0],
                [0, e ** complex(0, angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([], qubit, 'Z', 'Z')
            self.__all_operations.append(['Z', [], False, [qubit]])
            z = np.array([
                [1, 0],
                [0, -1]
            ])
        else:
            raise GateAngleError('z')

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, z)
        self.__state = np.dot(full_operator, self.__state)

    def s(self, qubit: int, angle=1):
        """Apply S gate to the specified qubit.

        Square-root of Pauli-Z gate. 90° rotation around the Z-axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───┐
          q0 : ─│ S │─ :
                └───┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a quarter
                rotation (90° or π/2 radians). Supported values:

                * 1: 90° rotation (π/2 radians).
                * -1: -90° rotation (-π/2 radians).

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        self.__check_measured([], qubit, 'S', 'S' + ("^-1" if angle == -1 else ''))
        self.__all_operations.append(['S' + ("^-1" if angle == -1 else ''), [], False, [qubit]])

        if abs(angle) != 1:
            raise GateAngleError('s')
        s = np.array([
            [1, 0],
            [0, 1j * angle]
        ])

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, s)
        self.__state = np.dot(full_operator, self.__state)

    def t(self, qubit: int, angle=1):
        """Apply T gate to the specified qubit.

        pi/8 gate. 45° rotation around the Z-axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───┐
          q0 : ─│ T │─ :
                └───┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a 1/8
                rotation (45° or π/4 radians). Supported values:

                * 1: 45° rotation (π/4 radians) - fourth root of gate.
                * -1: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        self.__check_measured([], qubit, 'T', 'T' + ("^-1" if angle == -1 else ''))
        self.__all_operations.append(['T' + ("^-1" if angle == -1 else ''), [], False, [qubit]])

        if abs(angle) != 1:
            raise GateAngleError('t')
        t = np.array([
            [1, 0],
            [0, e ** complex(0, pi / 4 * angle)]
        ])

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, t)
        self.__state = np.dot(full_operator, self.__state)

    def h(self, qubit: int):
        """Apply H gate to the specified qubit.

        Hadamard gate. 180° rotation around the X+Z axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───┐
          q0 : ─│ H │─ :
                └───┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        self.__check_measured([], qubit, 'H', 'H')
        self.__all_operations.append(['H', [], False, [qubit]])

        h = np.array([[1, 1], [1, -1]], dtype=complex) * (1 / np.sqrt(2))

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, h)
        self.__state = np.dot(full_operator, self.__state)

    def u(self, qubit: int, theta, phi, lam):
        """Apply U gate to the specified qubit.

        Generic single-qubit gate. Arbitrary rotation on the Bloch sphere.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌────────────┐
          q0 : ─│ U(ϴ, φ, λ) │─ :
                └────────────┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            theta: Polar angle in radians. Controls the population of |0⟩ and |1⟩ states.
            phi: Phase angle in radians. Controls the phase of the |1⟩ component.
            lam: Phase angle in radians. Controls the phase of the |0⟩ component.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        theta_str, phi_str, lam_str = format_angle(theta), format_angle(phi), format_angle(lam)
        self.__check_measured([], qubit, 'U', f'U({theta_str}, {phi_str}, {lam_str})')
        self.__all_operations.append([f'U({theta_str}, {phi_str}, {lam_str})', [], False, [qubit]])

        u = np.array([
            [cos(theta / 2), -e ** complex(0, lam) * sin(theta / 2)],
            [e ** complex(0, phi) * sin(theta / 2), e ** complex(0, phi + lam) * cos(theta / 2)]
        ])

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, u)
        self.__state = np.dot(full_operator, self.__state)

    def p(self, qubit: int, theta):
        """Apply P gate to the specified qubit.

        Phase gate. Generalization of gates Z, S, T. Rotation by an angle ϴ
        around the Z axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌──────┐
          q0 : ─│ P(ϴ) │─ :
                └──────┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            theta: Phase shift angle in radians. Can be any real number. Applies a
                phase shift of e^(iθ) to the |1⟩ component while leaving |0⟩ unchanged.
                Example: theta=π/2 applies a 90° phase shift.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        angle_str = format_angle(theta)
        self.__check_measured([], qubit, 'P', f'P({angle_str})')
        self.__all_operations.append([f'P({angle_str})', [], False, [qubit]])

        p = np.array([
            [1, 0],
            [0, e ** (1j * theta)]
        ])
        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, p)
        self.__state = np.dot(full_operator, self.__state)

    def rx(self, qubit: int, theta):
        """Apply Rx gate to the specified qubit.

        Rotation around the X-axis by an arbitrary angle θ.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───────┐
          q0 : ─│ Rx(ϴ) │─ :
                └───────┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            theta: Rotation angle in radians. Can be any real number. Positive
                values rotate counterclockwise around the X-axis of the Bloch sphere.
                Example: theta=π/2 performs a 90° rotation around X-axis.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        angle_str = format_angle(theta)
        self.__check_measured([], qubit, 'Rx', f'Rx({angle_str})')
        self.__all_operations.append([f'Rx({angle_str})', [], False, [qubit]])

        rx = np.array([
            [cos(theta / 2), complex(0, -sin(theta / 2))],
            [complex(0, -sin(theta / 2)), cos(theta / 2)]
        ])
        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, rx)
        self.__state = np.dot(full_operator, self.__state)

    def ry(self, qubit: int, theta):
        """Apply Ry gate to the specified qubit.

        Rotation around the Y-axis by an arbitrary angle θ.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───────┐
          q0 : ─│ Ry(ϴ) │─ :
                └───────┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            theta: Rotation angle in radians. Can be any real number. Positive
                values rotate counterclockwise around the Y-axis of the Bloch sphere.
                Example: theta=π/2 performs a 90° rotation around Y-axis.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        angle_str = format_angle(theta)
        self.__check_measured([], qubit, 'Ry', f'Ry({angle_str})')
        self.__all_operations.append([f'Ry({angle_str})', [], False, [qubit]])

        ry = np.array([
            [cos(theta / 2), -sin(theta / 2)],
            [sin(theta / 2), cos(theta / 2)]
        ])
        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, ry)
        self.__state = np.dot(full_operator, self.__state)

    def rz(self, qubit: int, theta):
        """Apply Rz gate to the specified qubit.

        Rotation around the Z-axis by an arbitrary angle θ.

        Visualization using the draw_circuit() method:

        .. code-block:: text

                ┌───────┐
          q0 : ─│ Rz(ϴ) │─ :
                └───────┘

        Args:
            qubit: Index of the target qubit (indexing starts from 0).
            theta: Rotation angle in radians. Can be any real number. Positive
                values rotate counterclockwise around the Z-axis of the Bloch sphere.
                Example: theta=π/2 performs a 90° rotation around Z-axis.


        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [], [qubit])
        angle_str = format_angle(theta)
        self.__check_measured([], qubit, 'Rz', f'Rz({angle_str})')
        self.__all_operations.append([f'Rz({angle_str})', [], False, [qubit]])

        rz = np.array([
            [e ** (-1j * theta / 2), 0],
            [0, e ** (1j * theta / 2)]
        ])

        full_operator = build_single_qubit_operator(self.__num_qubits, qubit, rz)
        self.__state = np.dot(full_operator, self.__state)

    def cx(self, control: int, target: int, angle=1, anticontrol: bool = False):
        """Apply controlled-X gate.

        If the control qubit is |1⟩, then an X gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ───●─── :
                  │
                ┌─┴─┐
          q0 : ─│ X │─ :
                └───┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([control], target, f'X^{angle}', f'CX^{angle}')
            self.__all_operations.append([f'X^{angle}', [control], anticontrol, [target]])
            angle = pi * angle
            x = np.array([
                [cos(angle / 2), complex(0, -sin(angle / 2))],
                [complex(0, -sin(angle / 2)), cos(angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([control], target, 'X', 'CX')
            self.__all_operations.append([f'X', [control], anticontrol, [target]])
            x = np.array([
                [0, 1],
                [1, 0]
            ])
        else:
            raise GateAngleError('x')

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], x, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def cy(self, control: int, target: int, angle=1, anticontrol: bool = False):
        """Apply controlled-Y gate.

        If the control qubit is |1⟩, then an Y gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ───●─── :
                  │
                ┌─┴─┐
          q1 : ─│ Y │─ :
                └───┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([control], target, f'Y^{angle}', f'CY^{angle}')
            self.__all_operations.append([f'Y^{angle}', [control], anticontrol, [target]])
            angle = pi * angle
            y = np.array([
                [cos(angle / 2), -sin(angle / 2)],
                [sin(angle / 2), cos(angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([control], target, 'Y', 'CY')
            self.__all_operations.append([f'Y', [control], anticontrol, [target]])
            y = np.array([
                [0, complex(0, -1)],
                [complex(0, 1), 0]
            ])
        else:
            raise GateAngleError('y')

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], y, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def cz(self, control: int, target: int, angle=1, anticontrol: bool = False):
        """Apply controlled-Z gate.

        If the control qubit is |1⟩, then an Z gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ───●─── :
                  │
                ┌─┴─┐
          q1 : ─│ Z │─ :
                └───┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([control], target, 'Z', f'CZ^{angle}')
            self.__all_operations.append([f'Z^{angle}', [control], anticontrol, [target]])
            angle = pi * angle
            z = np.array([
                [e ** complex(0, -angle / 2), 0],
                [0, e ** complex(0, angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([control], target, 'Z', 'CZ')
            self.__all_operations.append([f'Z', [control], anticontrol, [target]])
            z = np.array([
                [1, 0],
                [0, -1]
            ])
        else:
            raise GateAngleError('z')

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], z, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def cs(self, control: int, target: int, angle=1, anticontrol: bool = False):
        """Apply controlled-S gate.

        If the control qubit is |1⟩, then an S gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ───●─── :
                  │
                ┌─┴─┐
          q1 : ─│ S │─ :
                └───┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a quarter
                rotation (90° or π/2 radians). Supported values:

                * 1: 90° rotation (π/2 radians) - square root of gate.
                * -1: -90° rotation (-π/2 radians) - inverse square root of gate.

            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        self.__check_measured([control], target, 'S', 'CS' + ("^-1" if angle == -1 else ''))

        if abs(angle) != 1:
            raise GateAngleError('s')
        self.__all_operations.append(['S' + ("^-1" if angle == -1 else ''), [control], anticontrol, [target]])
        s = np.array([
            [1, 0],
            [0, 1j * angle]
        ])

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], s, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def ch(self, control: int, target: int, anticontrol: bool = False):
        """Apply Controlled-Hadamard gate.

        If the control qubit is |1⟩, then an H gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ───●─── :
                  │
                ┌─┴─┐
          q1 : ─│ H │─ :
                └───┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        self.__check_measured([control], target, 'H', 'CH')
        self.__all_operations.append(['H', [control], anticontrol, [target]])

        h = np.array([[1, 1], [1, -1]], dtype=complex) * (1 / np.sqrt(2))

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], h, anticontrol)
        self.__state = np.dot(full_operator, self.__state)


    def cu(self, control: int, target: int, theta, phi, lam, gamma, anticontrol: bool = False):
        """Apply Controlled-U gate (4-parameter two-qubit gate).

        If the control qubit is |1⟩, then an H gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ─────────●──────── :
                        │
                ┌───────┴───────┐
          q1 : ─│ U(ϴ, φ, λ, γ) │─ :
                └───────────────┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            theta: Polar angle in radians for the U gate. Controls the population of |0⟩ and |1⟩ states.
            phi: Phase angle in radians for the U gate. Controls the phase of the |1⟩ component.
            lam: Phase angle in radians for the U gate. Controls the phase of the |0⟩ component.
            gamma: Global phase angle in radians. Applies an additional global phase factor e^(iγ).
            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        theta_str, phi_str, lam_str, gam_str = format_angle(theta), format_angle(phi), \
            format_angle(lam), format_angle(gamma)
        self.__check_measured([control], target, 'U', f'CU({theta_str}, {phi_str}, {lam_str}, {gam_str})')
        self.__all_operations.append([f'U({theta_str}, {phi_str}, {lam_str}, {gam_str})', [control], anticontrol, [target]])

        u = np.e ** (1j * gamma) * np.array([
            [cos(theta / 2), -e ** complex(0, lam) * sin(theta / 2)],
            [e ** complex(0, phi) * sin(theta / 2), e ** complex(0, phi + lam) * cos(theta / 2)]
        ])

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], u, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def cp(self, control: int, target: int, theta, anticontrol: bool = False):
        """Apply Controlled-Phase gate.

        If the control qubit is |1⟩, then an P gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ────●───── :
                   │
                ┌──┴───┐
          q1 : ─│ P(ϴ) │─ :
                └──────┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            theta: Phase shift angle in radians. Can be any real number. Applies a
                phase shift of e^(iθ) to the |1⟩ component while leaving |0⟩ unchanged.
                Example: theta=π/2 applies a 90° phase shift.
            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        angle_str = format_angle(theta)
        self.__check_measured([control], target, 'P', f'P({angle_str})')
        self.__all_operations.append([f'P({angle_str})', [control], anticontrol, [target]])

        p = np.array([
            [1, 0],
            [0, e ** (1j * theta)]
        ])

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], p, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def crx(self, control: int, target: int, theta, anticontrol: bool = False):
        """Apply Controlled-Rx gate.

        If the control qubit is |1⟩, then an Rx(ϴ) gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ─────●───── :
                    │
                ┌───┴───┐
          q1 : ─│ Rx(ϴ) │─ :
                └───────┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            theta: Rotation angle in radians. Can be any real number. Positive
                 values rotate counterclockwise around the X-axis of the Bloch sphere.
                 Example: theta=π/2 performs a 90° rotation around X-axis.
            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        angle_str = format_angle(theta)
        self.__check_measured([control], target, 'Rx', f'Rx({angle_str})')
        self.__all_operations.append([f'Rx({angle_str})', [control], anticontrol, [target]])

        rx = np.array([
            [cos(theta / 2), complex(0, -sin(theta / 2))],
            [complex(0, -sin(theta / 2)), cos(theta / 2)]
        ])

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], rx, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def cry(self, control: int, target: int, theta, anticontrol: bool = False):
        """Apply Controlled-Ry gate.

        If the control qubit is |1⟩, then an Ry(ϴ) gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ─────●───── :
                    │
                ┌───┴───┐
          q1 : ─│ Ry(ϴ) │─ :
                └───────┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            theta: Rotation angle in radians. Can be any real number. Positive
                 values rotate counterclockwise around the Y-axis of the Bloch sphere.
                 Example: theta=π/2 performs a 90° rotation around Y-axis.
            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        angle_str = format_angle(theta)
        self.__check_measured([control], target, 'Ry', f'CRy({angle_str})')
        self.__all_operations.append([f'Ry({angle_str})', [control], anticontrol, [target]])

        ry = np.array([
            [cos(theta / 2), -sin(theta / 2)],
            [sin(theta / 2), cos(theta / 2)]
        ])

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], ry, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def crz(self, control: int, target: int, theta, anticontrol: bool = False):
        """Apply Controlled-Rz gate.

        If the control qubit is |1⟩, then an Rz(ϴ) gate is applied to the
        target qubit. If at |0⟩, nothing happens.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ─────●───── :
                    │
                ┌───┴───┐
          q1 : ─│ Rz(ϴ) │─ :
                └───────┘

        Args:
            control: Index of the control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            theta: Rotation angle in radians. Can be any real number. Positive
                 values rotate counterclockwise around the Z-axis of the Bloch sphere.
                 Example: theta=π/2 performs a 90° rotation around Z-axis.
            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [control], [target])
        angle_str = format_angle(theta)
        self.__check_measured([control], target, 'Rz', f'Rz({angle_str})')
        self.__all_operations.append([f'Rz({angle_str})', [control], anticontrol, [target]])

        rz = np.array([
            [e ** (-1j * theta / 2), 0],
            [0, e ** (1j * theta / 2)]
        ])

        full_operator = build_two_qubit_operator(self.__num_qubits, [control], [target], rz, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def swap(self, qubit1: int, qubit2: int):
        """Apply SWAP gate.

        The SWAP gate exchanges the quantum states between two qubits.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ─X─ :
                │
                │
          q1 : ─X─ :

        Args:
            qubit1: Index of the first qubit (indexing starts from 0).
            qubit2: Index of the second qubit (indexing starts from 0).

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [qubit1], [qubit2])
        self.__check_measured([], [qubit1, qubit2], 'swap', 'Swap')
        self.__is_measured[qubit1], self.__is_measured[qubit2] = \
            self.__is_measured[qubit2], self.__is_measured[qubit1]
        self.__all_operations.append([f'swap', [], False, [qubit1, qubit2]])

        swap_i = 0.5
        swap_x = 0.5
        swap_y = 0.5
        swap_z = 0.5

        for i in range(self.__num_qubits):
            if i == qubit1 or i == qubit2:
                swap_i = np.kron(swap_i, np.identity(2))
                swap_x = np.kron(swap_x, np.array([[0, 1], [1, 0]]))
                swap_y = np.kron(swap_y, np.array([[0, -1j], [1j, 0]]))
                swap_z = np.kron(swap_z, np.array([[1, 0], [0, -1]]))
            else:
                swap_i = np.kron(swap_i, np.identity(2))
                swap_x = np.kron(swap_x, np.identity(2))
                swap_y = np.kron(swap_y, np.identity(2))
                swap_z = np.kron(swap_z, np.identity(2))
        swap = swap_i + swap_x + swap_y + swap_z

        self.__state = np.dot(swap, self.__state)

    def ccx(self, control1: int, control2: int, target: int, angle=1, anticontrol: bool = False):
        """Apply Toffoli (CCNOT) gate.

        The Toffoli gate flips the target qubit if both control qubits are in |1⟩
        state (or |0⟩ state if anticontrol=True). It is a universal reversible logic gate.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ───●─── :
                  │
                  │
          q1 : ───●─── :
                  │
                ┌─┴─┐
          q2 : ─│ X │─ :
                └───┘

        Args:
            control1: Index of the first control qubit (indexing starts from 0).
            control2: Index of the second control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [control1, control2], [target])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([control1, control2], target, f'X^{angle}', f'CCX^{angle}')
            self.__all_operations.append([f'X^{angle}', [control1, control2], anticontrol, [target]])
            angle = pi * angle
            x = np.array([
                [cos(angle / 2), complex(0, -sin(angle / 2))],
                [complex(0, -sin(angle / 2)), cos(angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([control1, control2], target, 'X', 'CCX')
            self.__all_operations.append([f'X', [control1, control2], anticontrol, [target]])
            x = np.array([
                [0, 1],
                [1, 0]
            ])
        else:
            raise GateAngleError('x')

        full_operator = build_three_qubit_operator(self.__num_qubits, [control1, control2], [target], x, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def ccz(self, control1: int, control2: int, target: int, angle=1, anticontrol: bool = False):
        """Apply CCZ gate.

        The CCZ gate flips the target qubit if both control qubits are in |1⟩ state
        (or |0⟩ state if anticontrol=True). It is a universal reversible logic gate.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ───●─── :
                  │
                  │
          q1 : ───●─── :
                  │
                ┌─┴─┐
          q2 : ─│ Z │─ :
                └───┘

        Args:
            control1: Index of the first control qubit (indexing starts from 0).
            control2: Index of the second control qubit (indexing starts from 0).
            target: Index of the target qubit (indexing starts from 0).
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        validate_qubit_index(self.__num_qubits, [control1, control2], [target])
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([control1, control2], target, 'Z', f'CCZ^{angle}')
            self.__all_operations.append([f'Z^{angle}', [control1, control2], anticontrol, [target]])
            angle = pi * angle
            z = np.array([
                [e ** complex(0, -angle / 2), 0],
                [0, e ** complex(0, angle / 2)]
            ])
        elif angle == 1:
            self.__check_measured([control1, control2], target, 'Z', 'CCZ')
            self.__all_operations.append([f'Z', [control1, control2], anticontrol, [target]])
            z = np.array([
                [1, 0],
                [0, -1]
            ])
        else:
            raise GateAngleError('z')

        full_operator = build_three_qubit_operator(self.__num_qubits, [control1, control2], [target], z, anticontrol)
        self.__state = np.dot(full_operator, self.__state)

    def cswap(self, control: int, target1: int, target2: int, anticontrol: bool = False):
        """Apply Fredkin (Controlled-SWAP). gate.

        The Fredkin gate exchanges the states of two target qubits if the control qubit is
        in |1⟩ state (or |0⟩ state if anticontrol=True). It is a universal reversible logic gate.

        Visualization using the draw_circuit() method:

        .. code-block:: text

          q0 : ─●─ :
                │
                │
          q1 : ─X─ :
                │
                │
          q2 : ─X─ :

        Args:
            control: Index of the control qubit (0-based indexing).
            target1: Index of the first target qubit (0-based indexing).
            target2: Index of the second target qubit (0-based indexing).
            anticontrol: If True, gate is activated when control qubit is |0⟩ instead of |1⟩.

        Raises:
            QubitIndexError: If any qubit index is out of range.
            QuantumMeasurementError: If any qubit has been measured.
        """
        validate_qubit_index(self.__num_qubits, [control], [target1, target2])
        self.__check_measured([control], [target1, target2], 'cswap', 'CSwap')
        self.__all_operations.append([f'cswap', [control], anticontrol, [target1, target2]])

        swap_control = 1

        swap_i = 0.5
        swap_x = 0.5
        swap_y = 0.5
        swap_z = 0.5

        for i in range(self.__num_qubits):
            if i == target1 or i == target2:
                swap_control = np.kron(swap_control, np.identity(2))
                swap_i = np.kron(swap_i, np.identity(2))
                swap_x = np.kron(swap_x, np.array([[0, 1], [1, 0]]))
                swap_y = np.kron(swap_y, np.array([[0, -1j], [1j, 0]]))
                swap_z = np.kron(swap_z, np.array([[1, 0], [0, -1]]))
            elif i == control:
                if anticontrol:
                    swap_control = np.kron(swap_control, np.array([[0, 0], [0, 1]]))
                    swap_i = np.kron(swap_i, np.array([[1, 0], [0, 0]]))
                    swap_x = np.kron(swap_x, np.array([[1, 0], [0, 0]]))
                    swap_y = np.kron(swap_y, np.array([[1, 0], [0, 0]]))
                    swap_z = np.kron(swap_z, np.array([[1, 0], [0, 0]]))
                else:
                    swap_control = np.kron(swap_control, np.array([[1, 0], [0, 0]]))
                    swap_i = np.kron(swap_i, np.array([[0, 0], [0, 1]]))
                    swap_x = np.kron(swap_x, np.array([[0, 0], [0, 1]]))
                    swap_y = np.kron(swap_y, np.array([[0, 0], [0, 1]]))
                    swap_z = np.kron(swap_z, np.array([[0, 0], [0, 1]]))
            else:
                swap_control = np.kron(swap_control, np.identity(2))
                swap_i = np.kron(swap_i, np.identity(2))
                swap_x = np.kron(swap_x, np.identity(2))
                swap_y = np.kron(swap_y, np.identity(2))
                swap_z = np.kron(swap_z, np.identity(2))
        swap = swap_i + swap_x + swap_y + swap_z
        swap += swap_control

        self.__state = np.dot(swap, self.__state)

    def as_bracket_string(self, decimals=4):
        """Return the quantum state representation in Dirac bra-ket notation.

        Formats the quantum state as a linear combination of basis states using
        standard Dirac notation with complex coefficients.

        Args:
            decimals: Number of decimal places to round coefficients to.

        Returns:
            String representation of the quantum state in bra-ket notation.
        """
        return text_state_vector(
            state=self.__state,
            num_qubits=self.__num_qubits,
            decimals=decimals
        )

    def draw_circuit(self, show_initial: bool = False):
        """Generate a textual representation of the quantum circuit operations.

        Creates an ASCII diagram showing the sequence of quantum operations applied
        to the system, with options to display the initial state.

        Args:
            show_initial: Whether to show the initial state of the system. Defaults to False.

        Returns:
            String containing the ASCII diagram of the quantum circuit.
        """
        draw_circuit(
            num_qubits=self.__num_qubits,
            operations=self.__all_operations,
            show_initial=show_initial,
            init_states=self.__init_states
        )

    def __str__(self):
        return self.as_bracket_string()

