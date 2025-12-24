import pickle
import random
import struct
from itertools import chain, count, product
from pathlib import Path

import numpy as np
from cycles.clifford import cliffordOrder
from numpy import pi
from qlisp import U, seq2mat, synchronize_global_phase

from .cache import cache

one_qubit_clifford_seq = [
    # Paulis
    ("u3", 0   ,  0   ,  0   ), # I
    ("u3", pi  , -pi  ,  0   ), # X
    ("u3", pi  ,  0   ,  0   ), # Y
    ("u3", 0   ,  pi/2,  pi/2), # Z

    # 2 pi / 3 rotations
    ("u3", pi/2, -pi/2,  0   ),
    ("u3", pi/2, -pi/2,  pi  ),
    ("u3", pi/2,  pi/2,  0   ),
    ("u3", pi/2,  pi/2, -pi  ),
    ("u3", pi/2,  0   ,  pi/2),
    ("u3", pi/2,  0   , -pi/2),
    ("u3", pi/2, -pi  ,  pi/2),
    ("u3", pi/2,  pi  , -pi/2),

    # pi / 2 rotations
    ("u3", pi/2, -pi/2,  pi/2), #  X/2
    ("u3", pi/2,  pi/2, -pi/2), # -X/2
    ("u3", pi/2,  0   ,  0   ), #  Y/2
    ("u3", pi/2,  pi  , -pi  ), # -Y/2
    ("u3", 0   ,  0   ,  pi/2), #  Z/2
    ("u3", 0   ,  0   , -pi/2), # -Z/2

    # Hadamard-like
    ("u3", pi/2, -pi  ,  0   ),
    ("u3", pi/2,  0   ,  pi  ), # Hadamard
    ("u3", pi/2,  pi/2,  pi/2),
    ("u3", pi/2, -pi/2, -pi/2),
    ("u3", pi  , -pi/2,  0   ),
    ("u3", pi  ,  pi/2,  0   )
] #yapf: disable

one_qubit_clifford_seq2 = [
    # Paulis
    [],                              # I
    ['H', 'S', 'S', 'H'],            # X
    ['H', 'S', 'S', 'H', 'S', 'S'],  # Y
    ['S', 'S'],                      # Z

    # 2 pi / 3 rotations
    ['S', 'S', 'H', 'S', 'S', 'S'],
    ['H', 'S', 'S', 'S'],
    ['S', 'S', 'H', 'S'],
    ['H', 'S'],
    ['S', 'S', 'S', 'H'],
    ['S', 'H'],
    ['S', 'S', 'S', 'H', 'S', 'S'],
    ['S', 'H', 'S', 'S'],

    # pi / 2 rotations
    ['S', 'S', 'S', 'H', 'S', 'S', 'S'], #  X/2
    ['S', 'H', 'S'],                     # -X/2
    ['S', 'S', 'H'],                     #  Y/2
    ['H', 'S', 'S'],                     # -Y/2
    ['S'],                               #  Z/2
    ['S', 'S', 'S'],                     # -Z/2

    # Hadamard-like
    ['S', 'S', 'H', 'S', 'S'],
    ['H'],
    ['S', 'S', 'S', 'H', 'S'],
    ['S', 'H', 'S', 'S', 'S'],
    ['H', 'S', 'S', 'H', 'S'],
    ['H', 'S', 'S', 'H', 'S', 'S', 'S']
] #yapf: disable

one_qubit_clifford_seq3 = [
    # Paulis
    ('I', ),
    ('X', ),
    ('Y', ),
    ('Y', 'X'),

    # 2 pi / 3 rotations
    ('X/2', 'Y/2'),
    ('X/2', '-Y/2'),
    ('-X/2', 'Y/2'),
    ('-X/2', '-Y/2'),
    ('Y/2', 'X/2'),
    ('Y/2', '-X/2'),
    ('-Y/2', 'X/2'),
    ('-Y/2', '-X/2'),

    # pi / 2 rotations
    ('X/2', ),
    ('-X/2', ),
    ('Y/2', ),
    ('-Y/2', ),
    ('-X/2', 'Y/2', 'X/2'),
    ('-X/2', '-Y/2', 'X/2'),

    # Hadamard-like
    ('X', 'Y/2'),
    ('X', '-Y/2'), # Hadamard
    ('Y', 'X/2'),
    ('Y', '-X/2'),
    ('X/2', 'Y/2', 'X/2'),
    ('-X/2', 'Y/2', '-X/2')
] #yapf: disable

one_qubit_clifford_seq_inv = {
    g: i
    for i, g in enumerate(one_qubit_clifford_seq)
}
one_qubit_clifford_seq_inv['H'] = 19
one_qubit_clifford_seq_inv['S'] = 16
one_qubit_clifford_seq_inv['I'] = 0
one_qubit_clifford_seq_inv['X'] = 1
one_qubit_clifford_seq_inv['Y'] = 2
one_qubit_clifford_seq_inv['Z'] = 3
one_qubit_clifford_seq_inv['X/2'] = 12
one_qubit_clifford_seq_inv['-X/2'] = 13
one_qubit_clifford_seq_inv['Y/2'] = 14
one_qubit_clifford_seq_inv['-Y/2'] = 15
one_qubit_clifford_seq_inv['-S'] = 17
one_qubit_clifford_seq_inv.update({f'C1_{i}': i for i in range(24)})

one_qubit_clifford_mul_table = np.array([
    [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23],
    [1,0,3,2,6,7,4,5,11,10,9,8,13,12,18,19,22,23,14,15,21,20,16,17],
    [2,3,0,1,7,6,5,4,10,11,8,9,20,21,15,14,23,22,19,18,12,13,17,16],
    [3,2,1,0,5,4,7,6,9,8,11,10,21,20,19,18,17,16,15,14,13,12,23,22],
    [4,7,5,6,11,8,9,10,2,3,1,0,22,17,21,12,14,18,13,20,23,16,15,19],
    [5,6,4,7,10,9,8,11,1,0,2,3,23,16,12,21,19,15,20,13,22,17,18,14],
    [6,5,7,4,8,11,10,9,3,2,0,1,16,23,20,13,18,14,12,21,17,22,19,15],
    [7,4,6,5,9,10,11,8,0,1,3,2,17,22,13,20,15,19,21,12,16,23,14,18],
    [8,9,11,10,1,3,2,0,7,4,5,6,19,14,22,16,20,12,23,17,15,18,13,21],
    [9,8,10,11,2,0,1,3,6,5,4,7,14,19,23,17,13,21,22,16,18,15,20,12],
    [10,11,9,8,3,1,0,2,4,7,6,5,18,15,17,23,12,20,16,22,14,19,21,13],
    [11,10,8,9,0,2,3,1,5,6,7,4,15,18,16,22,21,13,17,23,19,14,12,20],
    [12,13,21,20,18,19,14,15,22,17,23,16,1,0,4,5,8,10,6,7,2,3,11,9],
    [13,12,20,21,14,15,18,19,16,23,17,22,0,1,6,7,11,9,4,5,3,2,8,10],
    [14,19,15,18,22,16,23,17,20,21,12,13,8,9,2,0,6,4,1,3,10,11,7,5],
    [15,18,14,19,17,23,16,22,12,13,20,21,10,11,0,2,5,7,3,1,8,9,4,6],
    [16,23,22,17,12,21,20,13,19,14,15,18,5,6,8,11,3,0,10,9,7,4,1,2],
    [17,22,23,16,21,12,13,20,14,19,18,15,4,7,9,10,0,3,11,8,6,5,2,1],
    [18,15,19,14,16,22,17,23,21,20,13,12,11,10,3,1,4,6,0,2,9,8,5,7],
    [19,14,18,15,23,17,22,16,13,12,21,20,9,8,1,3,7,5,2,0,11,10,6,4],
    [20,21,13,12,19,18,15,14,17,22,16,23,3,2,7,6,10,8,5,4,0,1,9,11],
    [21,20,12,13,15,14,19,18,23,16,22,17,2,3,5,4,9,11,7,6,1,0,10,8],
    [22,17,16,23,13,20,21,12,15,18,19,14,7,4,11,8,2,1,9,10,5,6,0,3],
    [23,16,17,22,20,13,12,21,18,15,14,19,6,5,10,9,1,2,8,11,4,7,3,0],
], dtype=np.int8) #yapf: disable


_one_qubit_clifford_index = {
    (0, 0, 0): 0,
    (0, 0, 1): 16,
    (0, 0, 2): 3,
    (0, 0, 3): 17,
    (0, 1, 0): 16,
    (0, 1, 1): 3,
    (0, 1, 2): 17,
    (0, 1, 3): 0,
    (0, 2, 0): 3,
    (0, 2, 1): 17,
    (0, 2, 2): 0,
    (0, 2, 3): 16,
    (0, 3, 0): 17,
    (0, 3, 1): 0,
    (0, 3, 2): 16,
    (0, 3, 3): 3,
    (1, 0, 0): 14,
    (1, 0, 1): 8,
    (1, 0, 2): 19,
    (1, 0, 3): 9,
    (1, 1, 0): 6,
    (1, 1, 1): 20,
    (1, 1, 2): 7,
    (1, 1, 3): 13,
    (1, 2, 0): 18,
    (1, 2, 1): 10,
    (1, 2, 2): 15,
    (1, 2, 3): 11,
    (1, 3, 0): 4,
    (1, 3, 1): 12,
    (1, 3, 2): 5,
    (1, 3, 3): 21,
    (2, 0, 0): 2,
    (2, 0, 1): 22,
    (2, 0, 2): 1,
    (2, 0, 3): 23,
    (2, 1, 0): 23,
    (2, 1, 1): 2,
    (2, 1, 2): 22,
    (2, 1, 3): 1,
    (2, 2, 0): 1,
    (2, 2, 1): 23,
    (2, 2, 2): 2,
    (2, 2, 3): 22,
    (2, 3, 0): 22,
    (2, 3, 1): 1,
    (2, 3, 2): 23,
    (2, 3, 3): 2,
}


def one_qubit_clifford_index(gate):
    if gate in one_qubit_clifford_seq_inv:
        return one_qubit_clifford_seq_inv[gate]
    else:
        match gate:
            case ('R', phi):
                return one_qubit_clifford_index(
                    ('U', pi / 2, phi - pi / 2, pi / 2 - phi))
            case ('rfUnitary', theta, phi):
                return one_qubit_clifford_index(
                    ('U', theta, phi - pi / 2, pi / 2 - phi))
            case ('u3', theta, phi, lam) | ('U', theta, phi, lam):
                theta_i = round(4 * np.mod(theta / (2 * pi), 1), 12)
                if np.mod(theta_i, 1) > 1e-9:
                    return -1
                theta_i = round(theta_i)
                if theta_i == 1:
                    pass
                elif theta_i == 0:
                    phi, lam = phi + lam, 0
                elif theta_i == 2:
                    phi, lam = phi - lam, 0
                elif theta_i == 3:
                    theta_i = 1
                    phi, lam = phi + pi, lam + pi
                else:
                    return -1
                phi_i = round(4 * np.mod(phi / (2 * pi), 1), 12)
                lam_i = round(4 * np.mod(lam / (2 * pi), 1), 12)
                if np.mod(phi_i, 1) < 1e-9 and np.mod(lam_i, 1) < 1e-9:
                    return _one_qubit_clifford_index[theta_i,
                                                     round(phi_i),
                                                     round(lam_i)]
                else:
                    return -1
            case ('u2', phi, lam):
                return one_qubit_clifford_index(('U', pi / 2, phi, lam))
            case ('u1', lam) | ('Rz', lam) | ('P', lam):
                return one_qubit_clifford_index(('U', 0, 0, lam))
            case 'P':
                return 16
            case ('Rx', theta):
                return one_qubit_clifford_index(('U', theta, -pi / 2, pi / 2))
            case ('Ry', theta):
                return one_qubit_clifford_index(('U', theta, 0, 0))
            case _:
                return -1


def twoQubitCliffordSequence(n):
    """
    生成第 n 个群元对应的操作序列
    """
    S1 = [0, 8, 7]  #  I, Rot(2/3 pi, (1,1,1)), Rot(2/3 pi, (1,-1,-1))
    if n < 576:
        i, j = np.unravel_index(n, (24, 24))
        return ((i, ), (j, ))
    elif n < 5760:
        n -= 576
        i, j, k, l = np.unravel_index(n, (24, 24, 3, 3))
        return ((i, 'CX', S1[k]), (j, 'CX', S1[l]))
    elif n < 10944:
        n -= 5760
        i, j, k, l = np.unravel_index(n, (24, 24, 3, 3))
        return ((i, 'iSWAP', S1[k]), (j, 'iSWAP', S1[l]))
    else:
        n -= 10944
        i, j = np.unravel_index(n, (24, 24))
        return ((i, 'SWAP'), (j, 'SWAP'))


@cache()
def _matricies():
    one_qubit_clifford_matricies = [U(*g[1:]) for g in one_qubit_clifford_seq]
    two_qubit_clifford_matricies = []
    for n in range(11520):
        seq = twoQubitCliffordSequence(n)
        mat = np.eye(4, dtype=complex)
        for a, b in zip(*seq):
            if isinstance(a, str):
                mat = {
                    'CX':
                    np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1],
                              [0, 0, 1, 0]]),
                    'iSWAP':
                    np.array([[1, 0, 0, 0], [0, 0, 1j, 0], [0, 1j, 0, 0],
                              [0, 0, 0, 1]]),
                    'SWAP':
                    np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0],
                              [0, 0, 0, 1]])
                }[a] @ mat
            else:
                mat = np.kron(one_qubit_clifford_matricies[a],
                              one_qubit_clifford_matricies[b]) @ mat

        two_qubit_clifford_matricies.append(mat)
    return one_qubit_clifford_matricies, two_qubit_clifford_matricies


one_qubit_clifford_matricies, two_qubit_clifford_matricies = _matricies()

# 相位规范化后，2 比特 Clifford 群元的矩阵元仅可能取以下值
elms = [
    0, 0, 0, 0, 1, 1j, -1, -1j, 1 / np.sqrt(2), 1j / np.sqrt(2),
    -1 / np.sqrt(2), -1j / np.sqrt(2), 0.5, 0.5j, -0.5, -0.5j
]

# 速查表，key 为模与相位组成的元组
# 对于模，0,1,2,3 分别对应 0, 1, 1/sqrt(2), 1/2
# 对于相位， 0,1,2,3 分别对应 0, pi/2, pi, 3pi/2
elms_map = {k: v for k, v in zip(product(range(4), repeat=2), elms)}


def mat2num(mat, norm=True):
    """
    将一个 2 比特 Clifford 群元对应的矩阵转换为 64 位的整数
    
    由于规范化后矩阵元只有 13 种可能取值，故每个矩阵元可用 4 位二进制整数表示，
    4 x 4 的矩阵可以用不超过 64 位的整数表示
    """

    # 仅相隔一个全局相位的操作等价，故令第一个非零的矩阵元相位为 0，保证操作与矩阵一一对应
    if norm:
        mat = synchronize_global_phase(mat)

    absData, phaseData = 0, 0
    for index, (i, j) in zip(count(start=0, step=2), product(range(4),
                                                             repeat=2)):
        for k, v in elms_map.items():
            if abs(v - mat[i, j]) < 1e-3:
                a, phase = k
                break
        else:
            raise ValueError(f"Element {mat[i, j]} not allowed.")
        absData |= a << index
        phaseData |= phase << index
    return absData | (phaseData << 32)


def num2mat(num):
    """
    将 64 位整数还原成矩阵
    """
    absData, phaseData = num & 0xffffffff, num >> 32
    mat = np.zeros((4, 4), dtype=complex)

    for index, (i, j) in zip(count(start=0, step=2), product(range(4),
                                                             repeat=2)):
        a, phase = (absData >> index) & 0x3, (phaseData >> index) & 0x3
        mat[i, j] = elms_map[(a, phase)]
    return mat


NUMBEROFELEMENTS = 11520  # cliffordOrder(2)


def _fill_seq_pair(A, B):
    """
    填充必要的 I 作为占位符
    """
    if len(A) > len(B):
        B = ('I', ) * (len(A) - len(B)) + B
    elif len(B) > len(A):
        A = ('I', ) * (len(B) - len(A)) + A
    return A, B


def _short_seq_pair(A, B):
    """
    去掉多余的 I
    """
    C, D = [], []
    for x, y in zip(A, B):
        if x == 'I' and y == 'I':
            continue
        else:
            C.append(x)
            D.append(y)
    if len(C) == 0:
        return ('I', ), ('I', )
    else:
        return tuple(C), tuple(D)


def two_qubit_clifford_num():
    return [
        mat2num(seq2mat(twoQubitCliffordSequence(i)))
        for i in range(NUMBEROFELEMENTS)
    ]


__base = cache_dir.parent / "clifford"
__mul_table_file = __base / "clifford_2qb_mul_table_unsigned_short.dat"
__index_file = __base / "clifford_2qb_index.pickle"
__seq_lib_file = __base / "clifford_2qb_seq_lib.db"
__mul_table_packer = struct.Struct('<H')

if not __base.exists():
    __base.mkdir(parents=True)

if not __mul_table_file.exists():
    __mul_table = bytearray(NUMBEROFELEMENTS * NUMBEROFELEMENTS * 2)
    for offset in range(0, len(__mul_table), 2):
        __mul_table_packer.pack_into(__mul_table, offset, 0x8000)
    __mul_table_file.write_bytes(__mul_table)
else:
    __mul_table = bytearray(__mul_table_file.read_bytes())

if not __index_file.exists():
    __index2num = two_qubit_clifford_num()
    __num2index = {n: i for i, n in enumerate(__index2num)}
    __index2mat = [num2mat(n) for n in __index2num]

    with open(__index_file, 'wb') as f:
        pickle.dump((__index2num, __num2index, __index2mat), f)

else:
    with open(__index_file, 'rb') as f:
        (__index2num, __num2index, __index2mat) = pickle.load(f)


def mat2index(mat: np.ndarray) -> int:
    """
    convert matrix to index

    Args:
        mat ([type]): unitary matrix

    Returns:
        int: index of Clifford gate
    """
    return num2index(mat2num(mat))


def index2mat(i: int) -> np.ndarray:
    """
    convert index to matrix

    Args:
        i (int): index of Clifford gate

    Returns:
        np.ndarray: matrix
    """
    return __index2mat[i]


def index2num(i: int) -> int:
    return __index2num[i]


def num2index(num: int) -> int:
    return __num2index[num]


def seq2num(seq):
    return mat2num(seq2mat(seq))


def seq2index(seq):
    # if seq in __seq2index:
    #     return __seq2index[seq]
    i = mat2index(seq2mat(seq))
    # _updateSeqLib(i, seq)
    return i


# def index2seq(i, base=None):
#     if base is None:
#         return __index2seq[i]
#     ret = []
#     for seq in __index2seq[i]:
#         if _elms(seq) <= set(base) | {'I'}:
#             ret.append(seq)
#     return ret


def mul(i1: int, i2: int) -> int:
    offset = 2 * (NUMBEROFELEMENTS * i1 + i2)
    ret = __mul_table_packer.unpack_from(__mul_table, offset)[0]

    if ret & 0x8000:
        ret = mat2index(index2mat(i1) @ index2mat(i2))
        __mul_table_packer.pack_into(__mul_table, offset, ret)
        with open(__mul_table_file, 'r+b') as f:
            f.seek(offset)
            f.write(__mul_table_packer.pack(ret))
    return ret


def inv(i: int) -> int:
    return mat2index(index2mat(i).T.conj())


def _genSeq(i, gate=('CZ', 'CZ')):
    pulses = ['I', 'X', 'Y', 'X/2', 'Y/2', '-X/2', '-Y/2']
    phases = ['I', 'Z', 'S', '-S']

    for k in [2, 4, 6, 8]:
        num = len(pulses)**k * len(phases)**2
        if i >= num:
            i -= num
            continue
        index = np.unravel_index(i, (len(pulses), ) * k + (len(phases), ) * 2)
        a = [pulses[n] for n in index[:-2]]
        p = [phases[n] for n in index[-2:]]
        return _short_seq_pair(
            tuple(
                chain(*[[a[j], gate[0]] for j in range(0, k - 3, 2)],
                      [a[-2], p[0]])),
            tuple(
                chain(*[[a[j], gate[1]] for j in range(1, k - 2, 2)],
                      [a[-1], p[1]])))
    else:
        raise IndexError(f'i={i} should be less than 94158400.')


def _countTwoQubitGate(seq, gate):
    count = 0
    for a, b in zip(*seq):
        if (a, b) == gate:
            count += 1
    return count


def genSeqForGate(db, gate=('CZ', 'CZ')):
    db = Path(db)
    if db.exists():
        with open(db, 'rb') as f:
            start, index2seq = pickle.load(f)
    else:
        start, index2seq = 0, [list() for i in range(NUMBEROFELEMENTS)]
    try:
        while True:
            try:
                seq = _genSeq(start, gate)
            except IndexError:
                break
            i = seq2index(seq)
            if len(index2seq[i]) == 0:
                index2seq[i].append(seq)
            else:
                s = index2seq[i].pop()
                if (len(s[0]) == len(seq[0])
                        and _countTwoQubitGate(s, gate) == _countTwoQubitGate(
                            seq, gate)):
                    index2seq[i].append(seq)
                    index2seq[i].append(s)
                elif (len(s[0]) > len(seq[0])
                      or _countTwoQubitGate(s, gate) > _countTwoQubitGate(
                          seq, gate)):
                    index2seq[i] = [seq]
                else:
                    index2seq[i].append(s)
            start += 1
            if start % 10000 == 0:
                with open(db, 'wb') as f:
                    pickle.dump((start, index2seq), f)
    finally:
        with open(db, 'wb') as f:
            pickle.dump((start, index2seq), f)


_index2seq = [twoQubitCliffordSequence(i) for i in range(cliffordOrder(2))]


def mapping_qubits(circuit, mapping):
    """
    Remap qubits in a circuit.

    Args:
        circuit: [(gate, target), ...]
        mapping: {old: new}
    """
    ret = []
    for gate, target in circuit:
        if isinstance(target, tuple):
            ret.append((gate, tuple(mapping.get(i, i) for i in target)))
        else:
            ret.append((gate, mapping.get(target, target)))
    return ret


def twoQubitGate(gates):
    return {
        ('CZ', 'CZ'): ('CZ', (0, 1)),
        ('C', 'Z'): ('CZ', (0, 1)),
        ('Z', 'C'): ('CZ', (0, 1)),
        ('CX', 'CX'): ('Cnot', (0, 1)),
        ('XC', 'XC'): ('Cnot', (1, 0)),
        ('CR', 'CR'): ('CR', (0, 1)),
        ('RC', 'RC'): ('CR', (1, 0)),
        ('C', 'X'): ('Cnot', (0, 1)),
        ('X', 'C'): ('Cnot', (1, 0)),
        ('C', 'R'): ('CR', (0, 1)),
        ('R', 'C'): ('CR', (1, 0)),
        ('iSWAP', 'iSWAP'): ('iSWAP', (0, 1)),
        ('SWAP', 'SWAP'): ('SWAP', (0, 1)),
        ('SQiSWAP', 'SQiSWAP'): ('SQiSWAP', (0, 1)),
    }[gates]


def seq2qlisp(seq, qubits):
    if len(seq) > 2:
        raise ValueError("Only support 1 or 2 bits.")
    if len(seq) != len(qubits):
        raise ValueError("seq size and qubit num mismatched.")

    qlisp = []
    for gates in zip(*seq):
        try:
            qlisp.append(twoQubitGate(gates))
        except:
            for gate, i in zip(gates, qubits):
                qlisp.append((gate, i))
    return qlisp


def circuit_to_index(circuit: list) -> int:
    if not circuit:
        return 0
    mat = seq2mat(circuit)
    if mat.shape[0] == 2:
        mat = np.kron(np.eye(2), mat)
    return mat2index(mat)


def index_to_circuit(index: int, qubits=(0, ), base=None, rng=None) -> list:
    if len(qubits) > 2:
        raise ValueError('Only support 1 or 2 qubits')
    if rng is None:
        rng = random.Random()
    if base is None:
        base = _index2seq
    seq = rng.choice(base[index])
    if len(qubits) == 1:
        seq = (seq[1], )
    return seq2qlisp(seq, range(len(qubits)))


def generateRBCircuit(qubits, cycle, seed=None, interleaves=[], base=None):
    """Generate a random Clifford RB circuit.

    Args:
        qubits (list): The qubits to use.
        cycle (int): The cycles of clifford sequence.
        seed (int): The seed for the random number generator.
        interleaves (list): The interleaves to use.
        base (list): The basic two-qubit Clifford sequence.

    Returns:
        list: The RB circuit.
    """
    if isinstance(qubits, (str, int)):
        qubits = {0: qubits}
    else:
        qubits = {i: q for i, q in enumerate(qubits)}

    MAX = cliffordOrder(len(qubits))

    interleaves_index = circuit_to_index(interleaves)

    ret = []
    index = 0
    rng = random.Random(seed)

    for _ in range(cycle):
        i = rng.randrange(MAX)
        index = mul(i, index)
        ret.extend(index_to_circuit(i, qubits, base, rng))
        index = mul(interleaves_index, index)
        ret.extend(interleaves)

    ret.extend(index_to_circuit(inv(index), qubits, base, rng))

    return mapping_qubits(ret, qubits)
