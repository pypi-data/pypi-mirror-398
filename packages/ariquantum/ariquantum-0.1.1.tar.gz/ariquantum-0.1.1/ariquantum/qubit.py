from .exceptions import InitializStateError, QuantumMeasurementError, GateAngleError
from .visualization import draw_circuit, format_angle, text_state_vector

from math import acos, atan2, degrees, cos, sin, pi, e
import numpy as np


class Qubit:
    """A single quantum bit (qubit).

    Review
    ======

    The :class:`Qubit` class represents a single quantum bit that can exist in
    superposition states. This class provides a comprehensive set of quantum
    operations for working with individual qubits, including state initialization,
    quantum gates, measurements, and visualization.

    Qubit attributes
    ================

    :class:`Qubit` has one public attribute that is immutable.

    * :attr:`state`: The state vector of the qubit represented as a complex numpy
      array of dimension 2. The first element corresponds to the |0⟩ component,
      and the second element to the |1⟩ component.

    Main features
    =============

    Single-Qubit Operations
    -----------------------

    * :meth:`i()` - Identity gate.

    * :meth:`x(angle=1)` - Pauli-X gate.

    * :meth:`y(angle=1)` - Pauli-Y gate.

    * :meth:`z(angle=1)` - Pauli-Z gate.

    * :meth:`s(angle=1)` - Square-root of Pauli-Z gate.

    * :meth:`t(angle=1)` - pi/8 gate.

    * :meth:`h()` - Hadamard gate.

    * :meth:`u(theta, phi, lam)` - Generic single-qubit gate.

    * :meth:`p(theta)` - Phase gate.

    * :meth:`rx(theta)` - Rotation around the X-axis.

    * :meth:`ry(theta)` - Rotation around the Y-axis.

    * :meth:`rz(theta)` - Rotation around the Z-axis.

    Measurement Operations
    ----------------------

    * :meth:`measure()` - Measure the qubit in the computational basis.

    * :meth:`get_counts(shots)` - Get measurement statistics over multiple shots.

    * :meth:`measure_probabilities(decimals=5)` - Get probabilities of |0⟩ and |1⟩
      states.

    Visualization Methods
    ---------------------

    * :meth:`as_bracket_string(decimals=4)` - The state vector in bracket notation.

    * :meth:`draw_circuit(show_initial=False)` - Visualization of the operation scheme.

    Additional Methods
    ------------------

    * :meth:`bloch_coordinates(decimals=4)` - Get Bloch sphere coordinates (x, y, z)

    * :meth:`bloch_sphere_angles(decimals=2, degree=False)` - Get Bloch sphere angles (φ, θ)

    Implementation features
    =======================

    * The state is always normalized during initialization

    * All operations include checking the validity of qubit indexes and their states.

    * Many gates support fractional powers (for example, X^0.5).

    * After measuring a qubit, some quantum operations cannot be applied to it.

    Example:

    .. code-block:: python

        from ariquantum import Qubit

        # Create a qubit in the |0⟩ state
        q = Qubit('0')

        # Apply a Hadamard gate to create superposition
        q.h()

        # Apply a Pauli-Z gate
        q.z()

        # Draw the circuit
        q.draw_circuit(show_initial=True)

    Output:

    .. code-block:: text

                 ┌───┐ ┌───┐
        q |0⟩ : ─│ H │─│ Z │─ :
                 └───┘ └───┘
    """
    def __init__(self, state: str | list | tuple | np.ndarray = '0'):
        """Initializer of a single qubit.

        Args:
            state: Initial state of the qubit. Defaults to "0".

                * String: One of the standard basis states:

                  * '0': Ground state |0⟩.
                  * '1': Excited state |1⟩.
                  * '+': Superposition state |+⟩ = (|0⟩ + |1⟩)/√2.
                  * '-': Superposition state |-⟩ = (|0⟩ - |1⟩)/√2.
                  * 'i': Superposition state |i⟩ = (|0⟩ + i|1⟩)/√2.
                  * '-i': Superposition state |-i⟩ = (|0⟩ - i|1⟩)/√2.

                  For example:

                  * ``q = Qubit('0')  # Ground state |0⟩``
                  * ``q = Qubit('+')  # Superposition state |+⟩``


                * List, tuple or numpy array: Custom state vector [α, β] where:

                  * α: Complex amplitude for |0⟩ state
                  * β: Complex amplitude for |1⟩ state

                  The state will be automatically normalized.

                  For example:

                  * ``q = Qubit([1, 0])  # Equivalent to '0' state``
                  * ``q = Qubit([1, 1])  # Will be normalized to |+⟩ state``
                  * ``q = Qubit([0.6, 0.8j])  # Custom complex amplitudes``

        Raises:
            InitializStateError: If the state parameter is invalid (wrong type,
                incorrect dimension, or non-normalizable values).
        """
        STANDARD_STATES = {
            '0': [1, 0],
            '1': [0, 1],
            '+': [1 / np.sqrt(2), 1 / np.sqrt(2)],
            '-': [1 / np.sqrt(2), -1 / np.sqrt(2)],
            'i': [1 / np.sqrt(2), 1j / np.sqrt(2)],
            '-i': [1 / np.sqrt(2), -1j / np.sqrt(2)]
        }

        if isinstance(state, str) and state in STANDARD_STATES:
            self.__state = np.array(STANDARD_STATES[state], dtype=complex)
            self.__init_states = ['|' + state + '⟩']
        elif (isinstance(state, list) or isinstance(state, tuple)) and len(state) == 2:
            stard_view_qubit = np.array(state) / np.linalg.norm(np.array(state))
            self.__state = stard_view_qubit
            self.__init_states = [self.as_bracket_string()]
        elif isinstance(state, np.ndarray) and len(state) == 2:
            stard_view_qubit = state / np.linalg.norm(state)
            self.__state = stard_view_qubit
            self.__init_states = [self.as_bracket_string()]
        else:
            self.__state = state
            raise InitializStateError(
                f"Invalid initial state for Qubit: {self.__state}.\n"
                f"The state must be one of the following:\n"
                f"- A string: '0', '1', '+', '-', 'i', '-i';\n"
                f"- List/tuple or array of the type: [alpha, beta].\n"
            )

        self.__all_operations = []
        self.__is_measured = [False]

        self.__measured_probabilities = None

    @property
    def state(self):
        """The state vector of the qubit represented as a complex numpy
        array of dimension 2. The first element corresponds to the |0⟩ component,
        and the second element to the |1⟩ component.
        """
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

    def measure(self):
        """Perform deferred measurement on one or more qubits in the quantum register.

        Implements the principle of deferred measurement, where qubits are marked as measured
        without immediately collapsing the wavefunction. This allows for continued quantum
        operations on unmeasured qubits while preventing specified operations on measured qubits.

        Returns:
            String '0' or '1', depending on the measurement result of the qubit.
        """
        qubits = [0]
        for i in qubits:
            self.__all_operations.append(['↗', [], False, [i]])

        k = len(qubits)
        num_states = 2
        outcome_probabilities = np.zeros(2 ** k, dtype=float)

        for i in range(num_states):
            outcome_index = 0
            for q in qubits:
                bit = (i >> (-q)) & 1
                outcome_index = (outcome_index << 1) | bit
            outcome_probabilities[outcome_index] += abs(self.__state[i]) ** 2

        total_prob = np.sum(outcome_probabilities)
        if total_prob == 0:
            raise ValueError("Total probability is zero.")
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
            Keys are '0' and '1' representing qubit states (For example, "0101"),
            values are integers counting how many times that outcome occurred.

        Raises:
            QuantumMeasurementError: If called before any measurements have been performed.
        """
        if not all(self.__is_measured):
            raise QuantumMeasurementError(
                "Measurement is required before accessing results. "
            )

        prob0, prob1 = self.__measured_probabilities

        result = {'0': 0, '1': 0}
        for _ in range(shots):
            m = np.random.choice(['0', '1'], p=[prob0, prob1])
            result[m] += 1

        return result

    def measure_probabilities(self, decimals=5):
        """
        Calculate the measurement probabilities for the qubit in computational basis.

        Computes the probabilities of measuring the qubit in |0⟩ and |1⟩ states,
        returned as percentages with specified precision.

        Args:
            decimals: Number of decimal places for probability values.
                      Defaults to 5.

        Returns:
            Dictionary with measurement probabilities:
            - Key '0': Probability of measuring |0⟩ state (as percentage).
            - Key '1': Probability of measuring |1⟩ state (as percentage).
        """
        probability_0 = float(round(abs(abs(self.__state[0] ** 2) * 100), decimals))
        probability_1 = float(round(abs(abs(self.__state[1] ** 2) * 100), decimals))
        return {'0': probability_0, '1': probability_1}

    def bloch_coordinates(self, decimals=4):
        """
        Calculate the coordinates of the qubit state on the Bloch sphere.

        Returns the (x, y, z) coordinates representing the qubit's state
        on the surface of the Bloch sphere.

        Args:
            decimals: Number of decimal places for coordinate values.  Use -1 to disable
                rounding and get exact values. Defaults to 4.

        Returns:
            Tuple (x, y, z) representing coordinates on the Bloch sphere.
        """
        if decimals == -1:
            z = float(abs(self.__state[0]) ** 2 - abs(self.__state[1]) ** 2)
            x = float(2 * (self.__state[0].conjugate() * self.__state[1]).real)
            y = float(2 * (self.__state[0].conjugate() * self.__state[1]).imag)
        else:
            z = round(float(abs(self.__state[0]) ** 2 - abs(self.__state[1]) ** 2), decimals)
            x = round(float(2 * (self.__state[0].conjugate() * self.__state[1]).real), decimals)
            y = round(float(2 * (self.__state[0].conjugate() * self.__state[1]).imag), decimals)
        return x, y, z

    def bloch_sphere_angles(self, decimals=2, degree=False):
        """
        Calculate the angular coordinates (φ, θ) of the qubit state on Bloch sphere.

        Returns the azimuthal (φ) and polar (θ) angles representing the qubit's state
        in spherical coordinates on the Bloch sphere.

        Args:
            decimals: Number of decimal places for angle values.
                      Use -1 to disable rounding and get exact values.
                      Defaults to 2.
            degree: If True, return angles in degrees instead of radians.
                    Defaults to False (radians).

        Returns:
            Tuple (φ, θ) representing angular coordinates on Bloch sphere. Azimuthal (φ)
                angle (longitude) in range [-π, π] or [-180°, 180°]. Polar (θ) angle
                (colatitude) in range [0, π] or [0°, 180°].
        """
        x, y, z = self.bloch_coordinates(decimals=-1)
        teta = acos(z)
        fi = atan2(y, x)

        if degree:
            teta = degrees(teta)
            fi = degrees(fi)
        if decimals != -1:
            teta = round(teta, decimals)
            fi = round(fi, decimals)
        return fi, teta

    def i(self):
        """Apply I gate to the qubit.

        This gate does not perform any actions on the qubit. It leaves the state
        of the qubit completely unchanged.

        Visualization using the :meth:`draw_circuit()` method:

        .. code-block:: text

               ┌───┐
          q : ─│ I │─ :
               └───┘

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
        """
        self.__check_measured([], 0, 'I', 'I')
        self.__all_operations.append(['I', [], False, [0]])

    def x(self, angle=1):
        """Apply X gate to the qubit.

        Pauli-X gate. 180° rotation around the X-axis. An analog of the
        classical logic element NOT.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───┐
          q : ─│ X │─ :
               └───┘

        Args:
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([], 0, f'X^{angle}', f'X^{angle}')
            self.__all_operations.append([f'X^{angle}', [], False, [0]])
            angle = pi * angle

            x_matrix = np.array([
                [cos(angle / 2), complex(0, -sin(angle / 2))],
                [complex(0, -sin(angle / 2)), cos(angle / 2)]
            ])
            self.__state = np.dot(x_matrix, self.__state)

        elif angle == 1:
            self.__check_measured([], 0, 'X', 'X')
            self.__all_operations.append(['X', [], False, [0]])
            self.__state[0], self.__state[1] = self.__state[1], self.__state[0]
        else:
            raise GateAngleError('x')

    def y(self, angle=1):
        """Apply Y gate to the qubit.

        Pauli-Y gate. 180° rotation around the Z-axis. An analog of the
        classical logic element NOT.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───┐
          q : ─│ Y │─ :
               └───┘

        Args:
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([], 0, f'Y^{angle}', f'Y^{angle}')
            self.__all_operations.append([f'Y^{angle}', [], False, [0]])
            angle = pi * angle

            y_matrix = np.array([
                [cos(angle / 2), -sin(angle / 2)],
                [sin(angle / 2), cos(angle / 2)]
            ])
            self.__state = np.dot(y_matrix, self.__state)

        elif angle == 1:
            self.__check_measured([], 0, 'Y' ,'Y')
            self.__all_operations.append(['Y', [], False, [0]])
            self.__state[0], self.__state[1] = self.__state[1] * -1j, self.__state[0] * 1j
        else:
            raise GateAngleError('y')

    def z(self, angle=1):
        """Apply Z gate to the qubit.

        Pauli-Z gate. 180° rotation around the Z-axis. An analog of the
        classical logic element NOT.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───┐
          q : ─│ Z │─ :
               └───┘

        Args:
            angle: Rotation angle specified as a fraction of a half
                rotation (180° or π radians). Supported values:

                * 1: 180° rotation (π radians) - full gate application.
                * 0.5: 90° rotation (π/2 radians) - square root of gate.
                * -0.5: -90° rotation (-π/2 radians) - inverse square root of gate.
                * 0.25: 45° rotation (π/4 radians) - fourth root of gate.
                * -0.25: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        if angle in [0.5, -0.5, 0.25, -0.25]:
            self.__check_measured([], 0, 'Z', f'Z^{angle}')
            self.__all_operations.append([f'Z^{angle}', [], False, [0]])
            angle = pi * angle

            z_matrix = np.array([
                [e ** complex(0, -angle / 2), 0],
                [0, e ** complex(0, angle / 2)]
            ])
            self.__state = np.dot(z_matrix, self.__state)
        elif angle == 1:
            self.__check_measured([], 0, 'Z', 'Z')
            self.__all_operations.append(['Z', [], False, [0]])
            self.__state[1] = -self.__state[1]
        else:
            raise GateAngleError('z')

    def s(self, angle=1):
        """Apply S gate to the qubit.

        Square-root of Pauli-Z gate. 90° rotation around the Z-axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───┐
          q : ─│ S │─ :
               └───┘

        Args:
            angle: Rotation angle specified as a fraction of a quarter
                rotation (90° or π/2 radians). Supported values:

                * 1: 90° rotation (π/2 radians).
                * -1: -90° rotation (-π/2 radians).

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """
        self.__check_measured([], 0, 'S', 'S' + ("^-1" if angle == -1 else ''))
        self.__all_operations.append(['S' + ("^-1" if angle == -1 else ''), [], False, [0]])
        if abs(angle) != 1:
            raise GateAngleError('s')
        angle = pi / 2 * angle
        self.__state[0] *= e ** (-1j * angle / 2)
        self.__state[1] *= e ** (1j * angle / 2)

    def t(self, angle=1):
        """Apply T gate to the qubit.

        pi/8 gate. 45° rotation around the Z-axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───┐
          q : ─│ T │─ :
               └───┘

        Args:
            angle: Rotation angle specified as a fraction of a 1/8
                rotation (45° or π/4 radians). Supported values:

                * 1: 45° rotation (π/4 radians) - fourth root of gate.
                * -1: -45° rotation (-π/4 radians) - inverse fourth root of gate.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
            GateAngleError: If an invalid angle value is provided.
        """

        self.__check_measured([], 0, 'T', 'T' + ("^-1" if angle == -1 else ''))
        self.__all_operations.append(['T' + ("^-1" if angle == -1 else ''), [], False, [0]])
        if abs(angle) != 1:
            raise GateAngleError('t')
        angle = pi / 4 * angle
        self.__state[0] *= e ** (-1j * angle / 2)
        self.__state[1] *= e ** (1j * angle / 2)

    __H_MATRIX = np.array([[1, 1], [1, -1]], dtype=complex) * (1 / np.sqrt(2))
    def h(self):
        """Apply H gate to the qubit.

        Hadamard gate. 180° rotation around the X+Z axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───┐
          q : ─│ H │─ :
               └───┘

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
        """
        self.__check_measured([], 0, 'H', 'H')
        self.__all_operations.append(['H', [], False, [0]])
        self.__state = np.dot(self.__H_MATRIX, self.__state)

    def u(self, theta, phi, lam):
        """Apply U gate to the qubit.

        Generic single-qubit gate. Arbitrary rotation on the Bloch sphere.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌────────────┐
          q : ─│ U(ϴ, φ, λ) │─ :
               └────────────┘

        Args:
            theta: Polar angle in radians. Controls the population of |0⟩ and |1⟩ states.
            phi: Phase angle in radians. Controls the phase of the |1⟩ component.
            lam: Phase angle in radians. Controls the phase of the |0⟩ component.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
        """

        theta_str, phi_str, lam_str = format_angle(theta), format_angle(phi), format_angle(lam)
        self.__check_measured([], 0, 'U', f'U({theta_str}, {phi_str}, {lam_str})')
        self.__all_operations.append([f'U({theta_str}, {phi_str}, {lam_str})', [], False, [0]])
        u_matrix = np.array([
            [cos(theta / 2), -e ** complex(0, lam) * sin(theta / 2)],
            [e ** complex(0, phi) * sin(theta / 2), e ** complex(0, phi + lam) * cos(theta / 2)]
        ])
        self.__state = np.dot(u_matrix, self.__state)

    def p(self, theta):
        """Apply P gate to the qubit.

        Phase gate. Generalization of gates Z, S, T. Rotation by an angle ϴ
        around the Z axis.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌──────┐
          q : ─│ P(ϴ) │─ :
               └──────┘

        Args:
            theta: Phase shift angle in radians. Can be any real number. Applies a
                phase shift of e^(iθ) to the |1⟩ component while leaving |0⟩ unchanged.
                Example: theta=π/2 applies a 90° phase shift.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
        """
        angle_str = format_angle(theta)
        self.__check_measured([], 0, 'P', f'P({angle_str})')
        self.__all_operations.append([f'P({angle_str})', [], False, [0]])

        self.__state[1] *= e ** (1j * theta)

    def rx(self, theta):
        """Apply Ry gate to the qubit.

        Rotation around the Y-axis by an arbitrary angle θ.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───────┐
          q : ─│ Ry(ϴ) │─ :
               └───────┘

        Args:
            theta: Rotation angle in radians. Can be any real number. Positive
                values rotate counterclockwise around the Y-axis of the Bloch sphere.
                Example: theta=π/2 performs a 90° rotation around Y-axis.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
        """
        angle_str = format_angle(theta)
        self.__check_measured([], 0, 'Rx', f'Rx({angle_str})')
        self.__all_operations.append([f'Rx({angle_str})', [], False, [0]])
        x_matrix = np.array([
            [cos(theta / 2), complex(0, -sin(theta / 2))],
            [complex(0, -sin(theta / 2)), cos(theta / 2)]
        ])
        self.__state = np.dot(x_matrix, self.__state)

    def ry(self, theta):
        """Apply Ry gate to the qubit.

        Rotation around the Y-axis by an arbitrary angle θ.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───────┐
          q : ─│ Ry(ϴ) │─ :
               └───────┘

        Args:
            theta: Rotation angle in radians. Can be any real number. Positive
                values rotate counterclockwise around the Y-axis of the Bloch sphere.
                Example: theta=π/2 performs a 90° rotation around Y-axis.

        Raises:
            QuantumMeasurementError: If the qubit has been measured.
        """
        angle_str = format_angle(theta)
        self.__check_measured([], 0, 'Ry', f'Ry({angle_str})')
        self.__all_operations.append([f'Ry({angle_str})', [], False, [0]])
        y_matrix = np.array([
            [cos(theta / 2), -sin(theta / 2)],
            [sin(theta / 2), cos(theta / 2)]
        ])
        self.__state = np.dot(y_matrix, self.__state)

    def rz(self, theta):
        """Apply Rz gate to the qubit.

        Rotation around the Z-axis by an arbitrary angle θ.

        Visualization using the draw_circuit() method:

        .. code-block:: text

               ┌───────┐
          q : ─│ Rz(ϴ) │─ :
               └───────┘

        Args:
            theta: Rotation angle in radians. Can be any real number. Positive
                values rotate counterclockwise around the Z-axis of the Bloch sphere.
                Example: theta=π/2 performs a 90° rotation around Z-axis.

        Raises:
            QubitIndexError: If the qubit index is out of range.
            QuantumMeasurementError: If the qubit has been measured.
        """
        angle_str = format_angle(theta)
        self.__check_measured([], 0, 'Rz', f'Rz({angle_str})')
        self.__all_operations.append([f'Rz({angle_str})', [], False, [0]])
        self.__state[0] *= e ** (-1j * theta / 2)
        self.__state[1] *= e ** (1j * theta / 2)

    def as_bracket_string(self, decimals=5):
        """
        Return the quantum state representation in Dirac bra-ket notation.

        Formats the quantum state as a linear combination of basis states using
        standard Dirac notation with complex coefficients.

        Args:
            decimals: Number of decimal places to round coefficients to.

        Returns:
            String representation of the quantum state in bra-ket notation.
        """
        return text_state_vector(
            state=self.__state,
            num_qubits=1,
            decimals=decimals
        )

    def draw_circuit(self, show_initial=False):
        """
        Generate a textual representation of the quantum circuit operations.

        Creates an ASCII diagram showing the sequence of quantum operations applied
        to the system, with options to display the initial state.

        Args:
            show_initial: Whether to show the initial state of the system.
                          Defaults to False.

        Returns:
            String containing the ASCII diagram of the quantum circuit.
        """
        draw_circuit(
            num_qubits=1,
            operations=self.__all_operations,
            show_initial=show_initial,
            init_states=self.__init_states
        )


    def __str__(self):
        return self.as_bracket_string()


