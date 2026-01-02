# AriQuantum 🌌

**A simple quantum computing simulation library with an intuitive interface.**  
Perfect for students and beginners in quantum computing — no complex dependencies or noise models, just core operations and visualization.

---

## 🚀 Installation

Requires Python 3.9+ and `numpy`:
```bash
pip install ariquantum
```

---

## 🧪 Quick Start

### 1. Working with individual qubits
```python
from ariquantum.qubit import Qubit

# Create qubits in different initial states
q0 = Qubit('0')
q_plus = Qubit('+')

# Display states in Dirac bra-ket notation
print(q0.as_bracket_string())     # |0⟩
print(q_plus.as_bracket_string()) # 0.70711|0⟩ + 0.70711|1⟩
```

### 2. Quantum circuits and visualization
```python
from ariquantum.quantum_register import QuantumRegister

qr = QuantumRegister(2)  # 2-qubit register

# Apply gates: H on qubit 0, CX between 0 and 1
qr.h(0)
qr.cx(0, 1)

# Display state and circuit diagram
print(qr.as_bracket_string())
# 0.7071|00⟩ + 0.7071|11⟩

qr.draw_circuit()
#       ┌───┐       
# q0 : ─│ H │───●─── :
#       └───┘   │
#             ┌─┴─┐
# q1 : ───────│ X │─ :
#             └───┘
```

### 3. Measurements
```python
qr.measure(qubits=[0, 1])  # Deferred measurement
print(qr.get_counts(shots=100))
# Example output: {'11': 53, '00': 47}
```

---

## ✨ Key Features
- **Flexible control**: Manage individual qubits or full quantum registers.
- **Circuit visualization**: Auto-generated ASCII diagrams of quantum circuits.
- **Bra-ket notation**: Human-readable state representation (e.g., `0.7|00⟩ + 0.7|11⟩`).
- **Measurements**: Support for deferred execution with customizable shot counts.

---

## 📂 Project Structure
```
ariquantum/
├── __init__.py
├── build_operator.py    # Building operators for multi-qubit systems
├── exceptions.py        # Quantum-specific error handling
├── helpers.py           # Utility functions
├── quantum_register.py  # Core: QuantumRegister class for state management
├── qubit.py             # Single-qubit operations and state handling
└── visualization.py     # State/circuit visualization tools
```

---

## ⚖️ License
Distributed under the **[MIT License](https://opensource.org/licenses/MIT)**.

---

## ❓ Support
For questions or feedback:
- 🐞 [GitHub Issues](https://github.com/ariquantum)
- ✉️ Email: arimshcherbakov@gmail.com
- 💬 Telegram: [@ArimShcherbakov](https://t.me/ArimShcherbakov)

🇷🇺 Русская версия: [README_RU.md](README_RU.md)
