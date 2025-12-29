import functools
import itertools

import numpy as np

from ..simple import seq2mat
from .utils import one_qubit_clifford_seq

baises = [
    np.array([[1, 0], [0, 1]]),
    np.array([[0, 1], [1, 0]]),
    np.array([[0, -1j], [1j, 0]]),
    np.array([[1, 0], [0, -1]]),
]

baises_labels = "IXYZ"

baises_dict = {
    'I': np.array([[1, 0], [0, 1]]),
    'X': np.array([[0, 1], [1, 0]]),
    'Y': np.array([[0, -1j], [1j, 0]]),
    'Z': np.array([[1, 0], [0, -1]]),
}


def Pauli_group_elements(N):
    """
    Generate the Pauli group elements for a given number of qubits.

    Returns:
    - labels: a list of tuples of the form (sign, label)
    - matrices: a list of numpy arrays
    """
    labels = []
    matrices = []
    for (index, ops) in zip(itertools.product(range(4), repeat=N),
                            itertools.product(baises_labels, repeat=N)):
        P = functools.reduce(np.kron, (baises[i] for i in index))
        label = ''.join(ops)
        labels.extend([(0, label), (2, label)])
        matrices.extend([P, -P])
    return labels, matrices


def Pauli_matrix(sign, string):
    return 1j**sign * functools.reduce(np.kron,
                                       (baises_dict[c] for c in string))


def gen_rules(C):
    """
    Generate the rules for a given Clifford gate.

    The rules are a dictionary of the form:
    {
        label_before: (sign, label_after),
    }
    where:
    - label_before is a string of the form 'IXYZ'
    - label_after is a string of the form 'IXYZ'
    - sign is an integer in {0, 1, 2, 3}
    When the Clifford gate is applied to a Pauli group element labeled by `label_before`,
    the sign and label of the resulting Pauli group element labeled by `label_after` are
    updated accordingly.

    Parameters:
        C: a numpy array representing a Clifford gate

    Returns:
        a dictionary of the form:
        {
            label_before: (sign, label_after),
        }
    """
    N = round(np.log2(C.shape[0]))

    labels, matrices = Pauli_group_elements(N)
    matrices2 = np.einsum("ij,...jk,kl", C, np.asarray(matrices), C.T.conj())

    ret = {}
    for (_, label_in_str), M_out in zip(labels[::2], matrices2[::2]):
        for i, (label, M) in enumerate(zip(labels, matrices)):
            if np.allclose(M, M_out):
                if label != (0, label_in_str):
                    ret[label_in_str] = label
                break
        else:
            raise ValueError(f'C is not a Clifford gate. {C}')
        del labels[i]
        del matrices[i]
    return ret


def apply_rules(sign, P, rules, *index):
    """
    Apply the rules to a Pauli group element.
    """
    key = ''.join(P[i] for i in index)
    if key not in rules:
        return sign, P

    sign += rules[key][0]
    label = list(P)
    for i, p in zip(index, rules[key][1]):
        label[i] = p
    return sign % 4, ''.join(label)


def extend_stablizers(stablizers, N):
    if N <= len(stablizers):
        return stablizers

    M = len(stablizers)

    ret = [(i, s + 'I' * (N - M)) for i, s in stablizers]
    for i in range(M, N):
        ret.append((0, 'I' * i + 'Z' + 'I' * (N - i - 1)))
    return ret


def extend_destablizers(destablizers, N):
    if N <= len(destablizers):
        return destablizers

    M = len(destablizers)

    ret = [(i, s + 'I' * (N - M)) for i, s in destablizers]
    for i in range(M, N):
        ret.append((0, 'I' * i + 'X' + 'I' * (N - i - 1)))
    return ret


def stablizer_state(stablizers):
    """
    Compute the stabilizer state of a given list of stablizers.

    The stabilizer state is computed as follows:
    rho = prod_{s in stablizers} (P_s + I) / 2
    where P_s is the Pauli matrix corresponding to the stabilizer s.

    Parameters:
        stablizers: a list of tuples of the form (sign, string)

    Returns:
        a numpy array representing the stabilizer state
    """
    N = len(stablizers[0][1])

    rho = np.eye(2**N, dtype=complex)
    for sign, string in stablizers:
        rho = Pauli_matrix(sign, string) @ rho / 2 + rho / 2
    i = np.nonzero(np.diag(rho))[0][0]
    return rho[:, i] / np.sqrt(rho[i, i])


def pauli_mul(p1, p2):
    sign_dict = {
        ('X', 'Y'): 3,
        ('Y', 'Z'): 3,
        ('Z', 'X'): 3,
        ('Y', 'X'): 1,
        ('Z', 'Y'): 1,
        ('X', 'Z'): 1
    }
    op_dict = {
        ('I', 'I'): 'I',
        ('I', 'X'): 'X',
        ('I', 'Y'): 'Y',
        ('I', 'Z'): 'Z',
        ('X', 'I'): 'X',
        ('X', 'X'): 'I',
        ('X', 'Y'): 'Z',
        ('X', 'Z'): 'Y',
        ('Y', 'I'): 'Y',
        ('Y', 'X'): 'Z',
        ('Y', 'Y'): 'I',
        ('Y', 'Z'): 'X',
        ('Z', 'I'): 'Z',
        ('Z', 'X'): 'Y',
        ('Z', 'Y'): 'X',
        ('Z', 'Z'): 'I',
    }
    sign = p1[0] + p2[0]
    s = []
    for a, b in zip(p1[1], p2[1]):
        sign += sign_dict.get((a, b), 0)
        s.append(op_dict.get((a, b)))
    return sign & 3, ''.join(s)


def gaussian_elimination(stablizers):
    key = lambda p: (*['IXZY'.index(c) for c in p[1]], p[0])

    stablizers = sorted(stablizers, key=key, reverse=True)
    for i in range(len(stablizers) - 1):
        for j in range(i + 1, len(stablizers)):
            s = pauli_mul(stablizers[j], stablizers[i])
            if key(s) < key(stablizers[j]):
                stablizers[j] = s
        stablizers = sorted(stablizers, key=key, reverse=True)

    stablizers = sorted(stablizers, key=key)
    for i in range(len(stablizers) - 1):
        for j in range(i + 1, len(stablizers)):
            s = pauli_mul(stablizers[j], stablizers[i])
            if key(s) < key(stablizers[j]):
                stablizers[j] = s
        stablizers = sorted(stablizers, key=key)

    stablizers = sorted(stablizers, key=key, reverse=True)
    for i in range(len(stablizers) - 1):
        for j in range(i + 1, len(stablizers)):
            s = pauli_mul(stablizers[j], stablizers[i])
            if key(s) < key(stablizers[j]):
                stablizers[j] = s
        stablizers = sorted(stablizers, key=key, reverse=True)

    return stablizers


class Clifford():

    def __init__(self, verify=False):
        self.rules = {}
        self.alias = {}

        for gate in [
                'I', 'X', 'Y', 'Z', 'S', '-S', 'H', 'X/2', '-X/2', 'Y/2',
                '-Y/2'
        ] + one_qubit_clifford_seq:
            self.add_gate(gate, 1, verify)

        for gate in ['Cnot', 'CZ', 'iSWAP', 'SWAP', 'CR']:
            self.add_gate(gate, 2, verify)

    def add_gate(self, gate, N, verify=False):
        U = seq2mat([(gate, *range(N))])
        self.rules[gate] = gen_rules(U)

        if not verify:
            return

        for k, (s, v) in self.rules[gate].items():
            op1 = functools.reduce(np.kron,
                                   [baises[baises_labels.index(c)] for c in k])
            op2 = functools.reduce(np.kron,
                                   [baises[baises_labels.index(c)] for c in v])
            out = U @ op1 @ U.T.conj()
            assert np.allclose(out, op2 * [1, 1j, -1, -1j][s])

    def get_rule(self, gate, N):
        if gate in self.rules:
            return self.rules[gate]
        elif gate in self.alias:
            return self.rules[self.alias[gate]]
        self.add_gate(gate, N, verify=False)
        return self.rules[gate]

    def simulate(self, circ):
        # destablizers = []
        stablizers = []

        for gate, *qubits in circ:
            # destablizers = extend_destablizers(destablizers, max(qubits) + 1)
            stablizers = extend_stablizers(stablizers, max(qubits) + 1)

            # destablizers = [
            #     apply_rules(s, p, self.get_rule(gate, len(qubits)), *qubits)
            #     for s, p in destablizers
            # ]
            stablizers = [
                apply_rules(s, p, self.get_rule(gate, len(qubits)), *qubits)
                for s, p in stablizers
            ]

        return stablizers

    def inverse(self, circ):
        """
        Inverse a Clifford circuit.
        """
        stablizers = gaussian_elimination(self.simulate(circ))
        return []
