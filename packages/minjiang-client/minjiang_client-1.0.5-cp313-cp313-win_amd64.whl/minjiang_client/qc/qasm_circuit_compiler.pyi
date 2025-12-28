from _typeshed import Incomplete
from minjiang_client.compiler.gate_compiler import GateCompiler as GateCompiler
from minjiang_client.experiment.experiment import Experiment as Experiment
from minjiang_client.group import Group as Group

class QASMCircuitCompiler:
    group: Incomplete
    gate_compiler: Incomplete
    supported_gates: Incomplete
    qubits: Incomplete
    couplers: Incomplete
    coupler_graph: Incomplete
    def __init__(self, group: Group, gate_compiler: GateCompiler) -> None: ...
    def compile(self, qasm_circuit: str, title: str = 'QASM Circuit', desc: str = 'Compiled from QASM') -> Experiment: ...
