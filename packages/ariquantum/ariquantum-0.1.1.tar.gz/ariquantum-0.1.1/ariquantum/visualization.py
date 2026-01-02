from math import pi, gcd


def format_angle(angle, tol=1e-10):
    """Formats the angle in radians into a readable string using the symbol π.

    Args:
        angle: The angle in radians for formatting.
        tol: Tolerance for comparison with zero and rational numbers. By
            default, 1e-10.

    Return:
        A string representation of an angle in radians with the symbol π.
    """
    if abs(angle) < tol:
        return "0"

    ratio = angle / pi
    n = ratio

    if abs(n - round(n)) < tol:
        n_int = int(round(n))
        if n_int == 1:
            return "π"
        elif n_int == -1:
            return "-π"
        return f"{n_int}π" if n_int != 0 else "0"

    for denom in range(2, 33):
        num = round(ratio * denom)
        if abs(ratio - num / denom) < tol:
            gcd_val = gcd(abs(int(num)), denom)
            num //= gcd_val
            denom //= gcd_val

            if num == 1 and denom == 1:
                return "π"
            elif num == 1:
                return f"π/{denom}"
            elif num == -1:
                return f"-π/{denom}"
            elif denom == 1:
                return f"{num}π"
            return f"{num}π/{denom}"

    return f"{angle:.4g}".rstrip('0').rstrip('.')

def text_state_vector(state, num_qubits, decimals=4):
    """Return the quantum state representation in Dirac bra-ket notation.

    Formats the quantum state as a linear combination of basis states using
    standard Dirac notation with complex coefficients.

    Args:
        state: The list is the state vector of a quantum circuit.
        num_qubits: The number of qubits in the quantum circuit.
        decimals: Number of decimal places to round coefficients to.

    Returns:
        String representation of the quantum state in bra-ket notation.
   """
    def bracket_elem(amplitude, bin_state):
        bin_state = "0" * (num_qubits - len(bin_state[2:])) + bin_state[2:]

        if amplitude.real == 0:
            if amplitude.imag == 0:
                result = f''
            elif amplitude.imag == 1:
                result = f'i|{bin_state}⟩'
            elif amplitude.imag == -1:
                result = f'-i|{bin_state}⟩'
            else:
                result = f'{round(amplitude.imag, decimals)}i|{bin_state}⟩'
        elif amplitude.imag == 0:
            if amplitude.real == 1:
                result = f'|{bin_state}⟩'
            elif amplitude.real == -1:
                result = f'-|{bin_state}⟩'
            else:
                result = f'{round(amplitude.real, decimals)}|{bin_state}⟩'
        else:
            result = f'{round(amplitude.real, decimals)}{"+" if amplitude.imag > 0 else "-"}{abs(round(amplitude.imag, decimals))}i|{bin_state}⟩'

        return result

    lst_states = state
    result_lst = []

    for i, ampl in enumerate(lst_states, start=0):
        if ampl != 0:
            result_lst.append(bracket_elem(ampl, bin(i)))

    return " + ".join(result_lst)


def draw_circuit(num_qubits, operations, init_states, show_initial=False):
    """Generate a textual representation of the quantum circuit operations.

    Creates an ASCII diagram showing the sequence of quantum operations applied
    to the system, with options to display the initial state.

    Args:
        num_qubits: The number of qubits in the quantum circuit.
        operations: History of applied operations to the quantum circuit.
        show_initial: Whether to show the initial state of the system. Defaults to False.
        init_states: A list of the initial states of each qubit.

    Returns:
        String containing the ASCII diagram of the quantum circuit.
    """
    def replace_char(s, idx, ch):
        return s[:idx] + ch + s[idx + 1:]

    ops = operations
    n = num_qubits

    tops_total = [''] * n
    mids_total = [''] * n
    bots_total = [''] * n

    if n == 1:
        if show_initial:
            start_text = f'q {init_states[0]} : ─'
        else:
            start_text = f'q : ─'
        tops_total[0] += " " * len(start_text)
        mids_total[0] += start_text
        bots_total[0] += " " * len(start_text)
    else:
        for q in range(n):
            if show_initial:
                start_text = f'q{q} {init_states[q]} : ─'
            else:
                start_text = f'q{q} : ─'
            tops_total[q] += " " * len(start_text)
            mids_total[q] += start_text
            bots_total[q] += " " * len(start_text)

    sym_ls1 = ['─' for _ in range(n)]
    sym_ls2 = ['│' for _ in range(n)]

    for op in ops:
        op_str, ctrls, anticontrol, targets = op
        ctrls = sorted(ctrls)

        if op_str == '↗':
            sym_ls1[targets[0]] = '═'
            sym_ls2[targets[0]] = '║'

        if op_str in ['swap', 'cswap']:
            all_used_qubits = ctrls + targets
            all_used_qubits = list(range(min(all_used_qubits), max(all_used_qubits) + 1))

            all_used_qubits_swap = ctrls + targets
            if ctrls:
                a, sr, b = sorted(all_used_qubits_swap)
            else:
                a, b = sorted(targets)
                sr = -1

            max_lline_q = max([len(mids_total[i]) for i in all_used_qubits])

            for i in range(a, b + 1):
                need_lline = max_lline_q - len(mids_total[i])
                tops_total[i] += ' ' * need_lline
                mids_total[i] += sym_ls1[i] * need_lline
                bots_total[i] += ' ' * need_lline

            if op_str == 'cswap' and mids_total[ctrls[0]][-1] == '═':
                per_line = '║'
            else:
                per_line = '│'

            for q in range(a, b + 1):
                if q in ctrls:
                    mids_total[q] += '◯' if anticontrol else '●'
                elif q in targets:
                    mids_total[q] += 'X'

                if q == a:
                    tops_total[q] += ' '
                    bots_total[q] += per_line
                elif q == b:
                    tops_total[q] += per_line
                    bots_total[q] += ' '
                elif q == sr:
                    tops_total[q] += per_line
                    bots_total[q] += per_line
                else:
                    tops_total[q] += per_line
                    if sym_ls1[q] == '─' and per_line == '│':
                        mids_total[q] += '┼'
                    elif sym_ls1[q] == '═' and per_line == '│':
                        mids_total[q] += '╪'
                    elif sym_ls1[q] == '─' and per_line == '║':
                        mids_total[q] += '╫'
                    else:
                        mids_total[q] += '╬'
                    bots_total[q] += per_line

            if op_str == 'swap':
                sym_ls1[targets[0]], sym_ls1[targets[1]] = sym_ls1[targets[1]], sym_ls1[targets[0]]

        else:
            t = targets[0]
            len_line = len(op_str) + 2
            top_seq_op = "┌" + ("─" * len_line) + "┐"
            mid_seq_op = "│ " + op_str + " │"
            bot_seq_op = "└" + ("─" * len_line) + "┘"

            if ctrls:
                center = (len_line + 2) // 2

                all_used_qubits_swap = ctrls + [t]
                all_used_qubits_swap = list(range(min(all_used_qubits_swap), max(all_used_qubits_swap) + 1))
                max_lline_q = max([len(mids_total[i]) for i in all_used_qubits_swap])
                for c in ctrls:
                    a, b = sorted((t, c))
                    for i in range(a, b + 1):
                        need_lline = max_lline_q - len(mids_total[i])
                        if i != t:
                            tops_total[i] += ' ' * (need_lline + len_line + 2)
                            mids_total[i] += sym_ls1[i] * (need_lline + len_line + 2)
                            bots_total[i] += ' ' * (need_lline + len_line + 2)
                        else:
                            tops_total[i] += ' ' * need_lline
                            mids_total[i] += sym_ls1[i] * need_lline
                            bots_total[i] += ' ' * need_lline

                tops_total[t] += top_seq_op
                mids_total[t] += mid_seq_op
                bots_total[t] += bot_seq_op

                idx_center = len(mids_total[t]) - center - 1

                for c in ctrls:
                    a, b = sorted((t, c))
                    mids_total[c] = replace_char(mids_total[c], idx_center, '◯' if anticontrol else '●')
                    for i in range(a, b + 1):
                        if i == t:
                            if c < t:
                                if sym_ls2[c] == '│':
                                    tops_total[i] = replace_char(tops_total[i], idx_center, '┴')
                                else:
                                    tops_total[i] = replace_char(tops_total[i], idx_center, '╨')
                            else:
                                if sym_ls2[c] == '│':
                                    bots_total[i] = replace_char(bots_total[i], idx_center, '┬')
                                else:
                                    bots_total[i] = replace_char(bots_total[i], idx_center, '╥')
                        elif i == a:
                            bots_total[i] = replace_char(bots_total[i], idx_center, sym_ls2[c])
                        elif i == b:
                            tops_total[i] = replace_char(tops_total[i], idx_center, sym_ls2[c])
                        else:
                            tops_total[i] = replace_char(tops_total[i], idx_center, sym_ls2[c])
                            if sym_ls1[i] == '─' and sym_ls2[c] == '│':
                                mids_total[i] = replace_char(mids_total[i], idx_center, '┼')
                            elif sym_ls1[i] == '═' and sym_ls2[c] == '│':
                                mids_total[i] = replace_char(mids_total[i], idx_center, '╪')
                            elif sym_ls1[i] == '─' and sym_ls2[c] == '║':
                                mids_total[i] = replace_char(mids_total[i], idx_center, '╫')
                            else:
                                mids_total[i] = replace_char(mids_total[i], idx_center, '╬')
                            bots_total[i] = replace_char(bots_total[i], idx_center, sym_ls2[c])
            else:
                tops_total[t] += top_seq_op
                mids_total[t] += mid_seq_op
                bots_total[t] += bot_seq_op

        all_used_qubits_swap = ctrls + targets
        all_used_qubits_swap = range(min(all_used_qubits_swap), max(all_used_qubits_swap) + 1)
        for q in all_used_qubits_swap:
            tops_total[q] += ' '
            mids_total[q] += sym_ls1[q]
            bots_total[q] += ' '

    max_lline_q = max([len(mids_total[i]) for i in range(n)])
    for i in range(n):
        need_lline = max_lline_q - len(bots_total[i])
        symbol_line = mids_total[i][-1]
        tops_total[i] += ' ' * need_lline
        mids_total[i] += symbol_line * need_lline + ' :'
        bots_total[i] += ' ' * need_lline

    for i in range(n):
        print(tops_total[i],
              mids_total[i],
              bots_total[i], sep='\n')
