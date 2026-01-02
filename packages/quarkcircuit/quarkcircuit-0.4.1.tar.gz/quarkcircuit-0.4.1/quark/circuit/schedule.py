# Copyright (c) 2024 XX Xiao

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
A toolkit for applying dynamical decoupling (DD) sequences to quantum circuits.
"""
import copy 
import networkx as nx
from quark.circuit.basepasses import TranspilerPass
from quark.circuit.dag import qc2dag, dag2qc
from quark.circuit.quantumcircuit_helpers import (
    one_qubit_gates_available,
    two_qubit_gates_available,
    one_qubit_parameter_gates_available,
    two_qubit_parameter_gates_available,
    )
from typing import Literal

class DynamicalDecoupling(TranspilerPass):
    def __init__(self,t1g,t2g):
        self.t1g = t1g
        self.t2g = t2g
        self._count = 86751 # for new node 

    def counter(self):
        """Increment and return the internal counter."""
        self._count += 1
        return self._count

    def _get_max_idle_time(self,nodes):
        """Determine the maximum idle time for the current layer of nodes."""
        gates = [node.split('_')[0] for node in nodes]
        one_qubit_gates = list(one_qubit_gates_available.keys()) + list(one_qubit_parameter_gates_available.keys())
        two_qubit_gates = list(two_qubit_gates_available.keys()) + list(two_qubit_parameter_gates_available.keys())
        if bool(set(two_qubit_gates) & set(gates)):
            max_idle_time = self.t2g
        elif bool(set(one_qubit_gates) & set(gates)):
            max_idle_time = self.t1g
        else:
            max_idle_time = 0
        return max_idle_time

    def _update_idle_time(self,node,max_idle_time):
        """Update idle time for a qubit after executing a given node."""
        gate = node.split('_')[0]
        if gate in one_qubit_gates_available.keys() or gate in one_qubit_parameter_gates_available.keys():
            return max_idle_time - self.t1g
        elif gate in two_qubit_gates_available.keys():
            return max_idle_time - self.t2g
        else:
            return 0

    def run(self,qc,sequence:Literal['XY4','CPMG']='XY4', align_right:bool = True, insert_before_barrier:bool = False):

        """Insert dynamical decoupling sequences into the given quantum circuit.
           CPMG = (τ/2 - X - τ - X - τ/2) * n_dd
           XY4 = (τ/2 - X - τ - Y - τ - X - τ - Y - τ/2) * n_dd

        Args:
            qc (QuantumCircuit): Input quantum circuit.
            sequence (Literal['XY4', 'CPMG'], optional): Type of DD sequence to apply. Defaults to 'XY4'. 
            align_right (bool, optional): If True, traverse the circuit in reverse topological order to calculate idle regions. Defaults to True.
            insert_before_barrier (bool, optional): If True, allows inserting DD sequences before barriers. Defaults to False.

        Returns:
            QuantumCircuit:  A new quantum circuit with inserted dynamical decoupling sequences.
        """
        if sequence == 'XY4':
            sequence_length = 4
        elif sequence == 'CPMG':
            sequence_length = 2
        else:
            raise ValueError(f'Sequence {sequence} is not support now!')
        
        dag = qc2dag(qc,show_qubits=False)
        qubit_idle_time = {k:{'current_node':None,'idle_time':0} for k in qc.qubits}
        dag_copy = copy.deepcopy(dag)

        if align_right is True:
            topological_generations = []
            rev_dag = dag_copy.reverse()
            for nodes in nx.topological_generations(rev_dag):
                topological_generations.insert(0,nodes)
        else:
            topological_generations = nx.topological_generations(dag_copy)

        for nodes in topological_generations:
            # time
            max_idle_time = self._get_max_idle_time(nodes)
            # calcaulate
            node_qubits_dic = {node:dag_copy.nodes[node]['qubits'] for node in nodes}
            qubit_node_dic = {}
            for k,vv in node_qubits_dic.items():
                for v in vv:
                    qubit_node_dic[v] = k
            for qubit,node in qubit_node_dic.items(): # 其他qubit增加等待时间
                pre_node = qubit_idle_time[qubit]['current_node']
                idle_time = qubit_idle_time[qubit]['idle_time']
                if pre_node ==  None:
                    if idle_time > 0:
                        delay_nodes = [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':idle_time}),]
                        delay_edges = [(delay_nodes[0][0],node,{'qubit':[qubit]}),]
                        dag.add_nodes_from(delay_nodes)
                        dag.add_edges_from(delay_edges)
                    # update idle time
                    qubit_idle_time[qubit]['idle_time'] = self._update_idle_time(node,max_idle_time)
                    qubit_idle_time[qubit]['current_node'] = node
                else:
                    if idle_time >= self.t1g*sequence_length:
                        if node.split('_')[0] == 'barrier' and insert_before_barrier is False:
                            # update idle time
                            qubit_idle_time[qubit]['idle_time'] = self._update_idle_time(node,max_idle_time)
                            qubit_idle_time[qubit]['current_node'] = node                        
                        else:
                            dag.remove_edge(pre_node,node)
                            n_dd = int(idle_time//(self.t1g*sequence_length))
                            GRID_NS = 0.1 #精确到0.1 ns
                            tgap_units = round((idle_time - n_dd*sequence_length*self.t1g)/sequence_length/n_dd/(GRID_NS * 1e-9))
                            tgap = tgap_units*GRID_NS*1e-9
                            tgap_half = tgap/2
                            #print(idle_time,n_dd,tgap)
                            if sequence == 'XY4':
                                dd_nodes = []
                                for idx in range(n_dd):
                                    if idx == 0:
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap_half}),] if tgap > 0 else []
                                    else:
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                    if idx % 2 == 0:
                                        dd_nodes += [(f'x_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                        dd_nodes += [(f'y_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                        dd_nodes += [(f'x_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                        dd_nodes += [(f'y_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                    else:
                                        dd_nodes += [(f'y_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                        dd_nodes += [(f'x_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                        dd_nodes += [(f'y_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                        dd_nodes += [(f'x_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]                                        
                                    if idx == n_dd-1:
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap_half}),] if tgap > 0 else []
                            elif sequence == 'CPMG':
                                dd_nodes = []
                                for idx in range(n_dd):
                                    if idx == 0:
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap_half}),] if tgap > 0 else []
                                    else:
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                    dd_nodes += [(f'x_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                    dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap}),] if tgap > 0 else []
                                    dd_nodes += [(f'x_{self.counter()}_[{qubit}]',{'qubits':[qubit]}),]
                                    if idx == n_dd-1:
                                        dd_nodes += [(f'delay_{self.counter()}_[{qubit}]',{'qubits':[qubit],'duration':tgap_half}),] if tgap > 0 else []
                            dd_edges = [(dd_nodes[i][0],dd_nodes[i+1][0],{'qubit':[qubit]}) for i in range(len(dd_nodes)-1)]
                            dd_edges.append((pre_node,dd_nodes[0][0],{'qubit':[qubit]}))
                            dd_edges.append((dd_nodes[-1][0],node,{'qubit':[qubit]}))
                            dag.add_nodes_from(dd_nodes)
                            dag.add_edges_from(dd_edges)
                            # update idle time
                            qubit_idle_time[qubit]['idle_time'] = self._update_idle_time(node,max_idle_time)
                            qubit_idle_time[qubit]['current_node'] = node
                    else:
                        qubit_idle_time[qubit]['idle_time'] = self._update_idle_time(node,max_idle_time)
                        qubit_idle_time[qubit]['current_node'] = node
            for q in qubit_idle_time.keys():
                if q not in qubit_node_dic.keys():
                    qubit_idle_time[q]['idle_time'] += max_idle_time
            #print(qubit_idle_time)
            #print('=' * 35)
        qc_new = dag2qc(dag)
        return qc_new