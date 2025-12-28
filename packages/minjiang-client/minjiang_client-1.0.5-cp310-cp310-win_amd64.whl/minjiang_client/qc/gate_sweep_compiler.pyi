from minjiang_client.experiment.experiment import Experiment as Experiment
from minjiang_client.qc.qc_utils.quantum_gate import QuantumGate as QuantumGate
from minjiang_client.waveform import WavePackage as WavePackage
from minjiang_client.waveform.waveform_register import waveform_register as waveform_register

def gate_sweep_compile(exp: Experiment, process_list: list[str] | list[QuantumGate], layer: int, qubit: str): ...
