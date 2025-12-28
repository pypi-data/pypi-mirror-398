from _typeshed import Incomplete
from minjiang_client.qc.gates import HX as HX, HY as HY, I as I, X as X, Y as Y, dHX as dHX, dHY as dHY

clifford_gates: Incomplete
clifford_gates_decom_1q: Incomplete

class TwoQubitClifford:
    SINGLE_QUBIT_CLIFFORDS: Incomplete
    TWO_QUBIT_GATE: str
    gates_db: Incomplete
    def __init__(self) -> None: ...
    def get_decomposition(self, clifford_idx: int): ...
    def generate_sequence(self, length: int): ...
