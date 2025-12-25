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

""" A toolkit for the SABRE algorithm."""

from collections import OrderedDict
import copy, random
from functools import partial
import networkx as nx
from networkx import floyd_warshall_numpy
from typing import Literal
from quark.circuit.quantumcircuit_helpers import (
    one_qubit_gates_available,
    two_qubit_gates_available,
    one_qubit_parameter_gates_available,
    two_qubit_parameter_gates_available,
    three_qubit_gates_available,
    functional_gates_available,
    )
from quark.circuit.quantumcircuit import QuantumCircuit
from quark.circuit.dag import qc2dag, split_qubits
from quark.circuit.basepasses import TranspilerPass
import re

def extract_qubits(node_name:str):
    """
    Extracts qubit indices from the node name string.

    This function parses the node name to find all qubit indices specified 
    within square brackets (e.g., "[0,1]"), using regular expressions.
    It provides a faster alternative to accessing the 'qubits' attribute 
    from a DAG node (e.g., dag.nodes[node]['qubits']).

    Args:
        node_name (str): The name of the node, expected to contain qubit 
            information in square brackets.

    Returns:
        List[int]: A list of qubit indices as integers, extracted in order 
        of appearance. Returns an empty list if no qubit information is found.
    """
    #qubit0 = dag.nodes[node]['qubits'][0] is too time-consuming
    bracket_content = re.search(r'\[([^\]]*)\]', node_name)
    if not bracket_content:
        return []
    return list(map(int, re.findall(r'\d+', bracket_content.group(1))))

# 这个函数没放到类里的原因，1，多次调用，2，临时或者永久改变v2p
def update_v2p_and_p2v_mapping(v2p:dict,swap_gate_info:tuple) -> tuple[dict,dict]:
    """Update v2p and p2v mappings based on the given SWAP gate.

    Args:
        v2p (dict): A dictionary mapping virtual qubits to physical qubits.
        swap_gate_info (tuple): A tuple containing gate information. The format is
            (gate_name, vq1, vq2), where vq1 and vq2 are the virtual qubits being swapped.

    Returns:
        tuple[dict, dict]: 
            - Updated v2p mapping after applying the SWAP.
            - Updated p2v mapping.
    """
    v2p = copy.deepcopy(v2p)
    vq1,vq2 = swap_gate_info[1:]
    v2p[vq1],v2p[vq2] = v2p[vq2],v2p[vq1]
    p2v = {p:v for v,p in v2p.items()}
    return v2p,p2v

class SabreRouting(TranspilerPass):
    """SABRE-based routing pass for quantum circuit transpilation.

    Args:
        TranspilerPass (class): The base class that provides the infrastructure for
            the transpiler pass functionality.
    """
    def __init__(self,
                 subgraph:nx.Graph,
                 initial_mapping:Literal['random','trivial']|list = 'trivial',
                 do_random_choice:bool = False,
                 iterations: int = 5,
                 heuristic: Literal['basic','lookahead','basic_decay','lookahead_decay']='lookahead_decay',
                 max_extended_set_weight:float = 0.5, # validate when heuristic='lookahead'|'lookahead' 
                 ):
        """Initializes the SabreRouting class with the specified settings.

        Args:
            subgraph (nx.Graph): A subgraph of the hardware's coupling graph, containing 
                only the physical qubits relevant for the current circuit.
            initial_mapping (Literal['random','trivial'], optional): Strategy for initializing 
                the virtual-to-physical qubit mapping. Options:
                - 'trivial': Maps virtual qubits to physical qubits sequentially.
                - 'random': Maps virtual qubits to physical qubits randomly.
                Defaults to 'trivial'.
            do_random_choice (bool, optional): If True, randomly chooses a SWAP when 
                multiple options have the same score. Defaults to False.
            iterations (int, optional): The number of iterations for the SABRE routing process. Defaults to 5.
            heuristic (Literal['basic', 'lookahead', 'basic_decay', 'lookahead_decay'], optional):
                The heuristic strategy used to evaluate candidate SWAP gates.Defaults to 'lookahead_decay'.
    
            max_extended_set_weight (float, optional): The max weight of extended set. Defaults to 0.5.
        """
        super().__init__()
        self.coupling_graph = subgraph
        self.distance_matrix = floyd_warshall_numpy(subgraph)
        if 'normal_order' not in subgraph.graph:
            subgraph.graph['normal_order'] = list(subgraph.nodes())
        self.physical_qubits = subgraph.graph['normal_order'] # list(sorted(subgraph.nodes()))
        self.physical_qubits_index = dict(zip(list(subgraph.nodes),range(len(subgraph.nodes))))
        self.initial_mapping = initial_mapping
        self.do_random_choice = do_random_choice
        self.iterations = iterations
        self.heuristic = heuristic
        self.extended_successor_set = []
        self.max_extended_set_weight = max_extended_set_weight
        self.decay_parameter = {}
        
        self._cache = OrderedDict()

    def _distance_matrix_element(self,pq1:int,pq2:int):
        """ Obtain the distance matrix element between two physical qubits.
        """
        idx1 = self.physical_qubits_index[pq1]
        idx2 = self.physical_qubits_index[pq2]
        return self.distance_matrix[idx1][idx2]

    def _dag_successors(self, node:str):
        """ Obtain the successor nodes of the given node."""
        return self._get_nodes(node, 'successors')
    
    def _dag_predecessors(self, node:str):
        """ Obtain the predecessor nodes of the given node."""
        return self._get_nodes(node, 'predecessors')
    
    def _get_nodes(self, node:str, query_type:Literal['successors','predecessors']):
        """Retrieve the successors or predecessors of a given node in the DAG, with LRU caching.

         This method queries the directed acyclic graph (DAG) to obtain either the 
         successor nodes or predecessor nodes of the specified node. To improve 
         performance on repeated queries, results are cached using an LRU (Least 
         Recently Used) policy with a maximum cache size of 10,000 entries.
     
         Args:
             node (str): The name or identifier of the node in the DAG.
             query_type (Literal['successors', 'predecessors']): Type of query to perform.
                 - 'successors': Returns nodes that immediately follow the given node.
                 - 'predecessors': Returns nodes that immediately precede the given node.
     
         Returns:
             List[str]: A list of node names that are either successors or predecessors
             of the given node, depending on `query_type`.
     
         Note:
             The function uses a combination of `dag_id`, `id(node)`, and `query_type`
             as the cache key. When the cache exceeds 10,000 entries, the least
             recently used item is removed.
        """
        key = (self.dag_id, id(node), query_type)  # 使用 dag_id, node id 和 query_type 作为键
        
        if key in self._cache:
            self._cache.move_to_end(key)  # LRU 更新
            return self._cache[key]
        
        if query_type == 'successors':
            nodes = list(self.dag.successors(node))
        else:  # query_type == 'predecessors'
            nodes = list(self.dag.predecessors(node))
        
        self._cache[key] = nodes
        
        if len(self._cache) > 10000:
            self._cache.popitem(last=False)  # 移除最旧条目
        return nodes

    def _initialize_v2p_p2v(self,virtual_qubits:list):
        """
        Initialize the virtual-to-physical and physical-to-virtual qubit mappings.
    
        The mapping is determined based on the `initial_mapping` attribute:
        - If it is a list, it is used directly as the physical qubit assignment.
        - If it is 'trivial', virtual qubits are mapped to physical qubits in order.
        - If it is 'random', a random mapping is generated.
        
        Args:
            virtual_qubits (list): A list of virtual qubit identifiers to be mapped.
    
        Returns:
            Tuple[dict, dict]: A tuple containing:
                - v2p (dict): Mapping from virtual qubits to physical qubits.
                - p2v (dict): Mapping from physical qubits to virtual qubits.
        """
        if isinstance(self.initial_mapping,list):
            if len(set(self.initial_mapping)) != len(set(self.physical_qubits)):
                raise(ValueError(f'The number of initial_mapping does not match the number of physical qubits.{self.initial_mapping} {self.physical_qubits}'))
            v2p = dict(zip(virtual_qubits,self.initial_mapping))
        elif isinstance(self.initial_mapping,str):
            if len(set(virtual_qubits)) != len(set(self.physical_qubits)):
                raise(ValueError(f'The number of virtual qubits does not match the number of physical qubits.{virtual_qubits} {self.physical_qubits}'))
            if self.initial_mapping == 'trivial':
                v2p = dict(zip(virtual_qubits,self.physical_qubits))
            elif self.initial_mapping == 'random':
                shuffle_physical_qubits = random.sample(self.physical_qubits,len(self.physical_qubits))
                v2p = dict(zip(virtual_qubits,shuffle_physical_qubits))
            else:
                raise(ValueError(f"There is a spelling error in the input of initial_mapping {self.initial_mapping}."))
        else:
            raise(ValueError(f"Invalid input type for initial_mapping — only str and list are supported."))
        p2v = {p:v for v,p in v2p.items()}
        return v2p, p2v

    def _mapping_node_to_gate_info(self, node:str) -> tuple:
        """Map a DAG node to its corresponding gate information. 
    
        Args:
            node (str): The identifier of the node in the DAG.

        Returns:
            tuple: A tuple containing gate information.
        """
        gate = node.split('_')[0]
        if gate in one_qubit_gates_available.keys():
            qubit0 = extract_qubits(node)[0]
            gate_info = (gate,self.v2p[qubit0])
        elif gate in two_qubit_gates_available.keys():
            qubit1,qubit2 = extract_qubits(node)
            gate_info = (gate, self.v2p[qubit1], self.v2p[qubit2])
        elif gate in three_qubit_gates_available.keys():
            raise(ValueError(f'Please first decompose the {gate} gate into a combination of single- and two-qubit gates.'))
        elif gate in one_qubit_parameter_gates_available.keys():
            qubit0 = extract_qubits(node)[0]
            paramslst = self.dag.nodes[node]['params']
            gate_info = (gate,*paramslst,self.v2p[qubit0])
        elif gate in two_qubit_parameter_gates_available.keys():
            paramslst = self.dag.nodes[node]['params']
            qubit1,qubit2 = extract_qubits(node)
            gate_info = (gate, *paramslst, self.v2p[qubit1], self.v2p[qubit2])
        elif gate in functional_gates_available.keys():
            if gate == 'measure':
                qubitlst = self.dag.nodes[node]['qubits']
                cbitlst = self.dag.nodes[node]['cbits']
                gate_info = (gate,[self.v2p[qubit] for qubit in qubitlst], cbitlst)
            elif gate == 'barrier':
                qubitlst = extract_qubits(node)
                phy_qubitlst = [self.v2p[qubit] for qubit in qubitlst]
                gate_info = (gate,tuple(phy_qubitlst))
            elif gate == 'delay':
                qubitlst = self.dag.nodes[node]['qubits']
                phy_qubitlst = [self.v2p[qubit] for qubit in qubitlst]
                duration = self.dag.nodes[node]['duration']
                gate_info = (gate,duration,tuple(phy_qubitlst))
            elif gate == 'reset':
                qubit0 = self.dag.nodes[node]['qubits'][0]
                gate_info = (gate,self.v2p[qubit0])      
        return gate_info 

    def _get_extended_successor_set(self, front_layer: list) -> list:
        """Create an extended set for the front layer.
    
        Args:
            front_layer (list): A list of node identifiers representing the front layer.
            dag (nx.DiGraph): The directed acyclic graph (DAG) representing the quantum circuit.
    
        Returns:
            list: A list of node identifiers representing the extended set of the front layer.
        """
        if 'lookahead' in self.heuristic:
            two_qubit_gates = list(two_qubit_gates_available.keys()) + list(two_qubit_parameter_gates_available.keys())
            E = set()
            for node in front_layer:
                for node_successor in self._dag_successors(node):
                    gate = node_successor.split('_')[0]
                    if gate in two_qubit_gates and len(E) <= len(self.v2p):
                        E.update([node_successor])
            self.extended_successor_set = list(E)
        else:
            pass

    def _get_execute_node_list(self,front_layer:list):
        """Extract the list of executable nodes from the given front layer.
    
        Args:
            front_layer (list): A list of node names representing the current front layer
                of the circuit DAG. 
    
        Returns:
            list: A list of node names from the front layer that are ready for execution
            based on the current virtual-to-physical qubit mapping.
        """
        execute_node_list = []
        for node in front_layer:
            gate = node.split('_')[0]
            if gate not in two_qubit_gates_available.keys() and gate not in two_qubit_parameter_gates_available.keys():
                execute_node_list.append(node)
            else:
                #vq1, vq2 = self.dag.nodes[node]['qubits']
                vq1, vq2 = extract_qubits(node)
                pq1, pq2 = self.v2p[vq1], self.v2p[vq2]
                dis = self._distance_matrix_element(pq1, pq2)
                if dis == 1:
                    execute_node_list.append(node)  
        return execute_node_list

    def _has_no_correlation_on_front_layer(self, node:str, front_layer:list) -> bool:
        """Check if the given node in the DAG is correlated with any node in the front layer.
    
        Args:
            node (str): The identifier of the node in the DAG.
            front_layer (list): A list of node identifiers representing the front layer.
            dag (nx.DiGraph): The directed acyclic graph (DAG) representing the quantum circuit.
    
        Returns:
            bool: True if the node is no correlated with any node in the front layer, otherwise False.
        """
        qubitlst = []
        for fnode in front_layer:
            qubits = extract_qubits(fnode) #self.dag.nodes[fnode]['qubits']
            qubitlst += qubits
        qubitlst = set(qubitlst)
        
        node_qubits = set(extract_qubits(node))
        if qubitlst.intersection(node_qubits):
            return False
        else:
            return True
    
    def _get_swap_candidate_list(self,front_layer:list):
        """Generate a list of candidate SWAP operations based on the current front layer.
    
        Args:
            front_layer (list): A list of node names from the circuit DAG that are currently 
                in the front layer. 
    
        Returns:
            list: A list of SWAP candidates in the format:
                  [('swap', virtual_qubit_1, virtual_qubit_2), ...]
        """
        swap_candidate_list = []
        for hard_node in front_layer:
            vq1, vq2 = extract_qubits(hard_node) #self.dag.nodes[hard_node]['qubits']
            pq1_neighbours = self.coupling_graph.neighbors(self.v2p[vq1])
            pq2_neighbours = self.coupling_graph.neighbors(self.v2p[vq2])
            vq1_neighbours = [self.p2v[pq] for pq in pq1_neighbours]
            vq2_neighbours = [self.p2v[pq] for pq in pq2_neighbours]
            for vq in vq1_neighbours:
                poss = [vq,vq1]
                if ('swap',min(poss),max(poss)) not in swap_candidate_list:
                    swap_candidate_list.append(('swap',min(poss),max(poss)))
            for vq in vq2_neighbours:
                poss = [vq,vq2]
                if ('swap',min(poss),max(poss)) not in swap_candidate_list:
                    swap_candidate_list.append(('swap',min(poss),max(poss)))
        return swap_candidate_list
    
    def _reset_decay_parameter(self):
        if 'decay' in self.heuristic:
            self.decay_parameter = {k:1 for k in self.physical_qubits}
        else:
            pass

    def _update_decay_parameter(self, min_score_swap_gate_info: tuple,) -> list:
        """Update the decay parameter after applying the SWAP gate with the minimum score.
    
        Args:
            min_score_swap_gate_info (tuple): A tuple representing the SWAP gate with the minimum score.
            decay_parameter (list):  A list of decay parameters, where each index corresponds to a physical qubit.
            v2p (dict): A dictionary mapping virtual qubits to physical qubits.
    
        Returns:
            list: The updated list of decay parameters.
        """
        if 'decay' in self.heuristic:
            min_score_swap_qubits = list(min_score_swap_gate_info[1:])
            pq1 = self.v2p[min_score_swap_qubits[0]]
            pq2 = self.v2p[min_score_swap_qubits[1]]
            self.decay_parameter[pq1] = self.decay_parameter[pq1] + 0.01
            self.decay_parameter[pq2] = self.decay_parameter[pq2] + 0.01
        else:
            pass

    def _heuristic_score_basic(self,
                         swap_gate_info: tuple,
                         front_layer: list, 
                         ) -> float:
        r""" The decay function is defined as follows:

        $$
        H = \frac{1}{|F|}\sum_{gate\in F}D[\pi(gate.q1)][\pi(gate.q2)]
        $$

        """
        v2p,_ = update_v2p_and_p2v_mapping(self.v2p,swap_gate_info)
    
        F = front_layer
        size_F = len(F)
        f_distance = 0
        for node in F:
            vq1, vq2 = extract_qubits(node)
            f_distance += self._distance_matrix_element(v2p[vq1],v2p[vq2])
        return  f_distance / size_F

    def _heuristic_score_lookahead(self,
                         swap_gate_info: tuple,
                         front_layer: list, 
                         ) -> float:
        r""" The lookahead function is defined as follows:

        $$
        H = \frac{1}{|F|}\sum_{gate\in F}D[\pi(gate.q1)][\pi(gate.q2)] + W*\frac{1}{|E|}\sum_{gate\in E}D[\pi(gate.q1)][\pi(gate.q2)]
        $$

        """
        v2p,_ = update_v2p_and_p2v_mapping(self.v2p,swap_gate_info)
    
        F = front_layer
        E = self.extended_successor_set
        size_E = len(E)
        if size_E == 0:
            size_E = 1
        size_F = len(F)
        W = min(self.max_extended_set_weight, size_E/size_F)
        f_distance = 0
        e_distance = 0
        for node in F:
            vq1, vq2 = extract_qubits(node)
            f_distance += self._distance_matrix_element(v2p[vq1],v2p[vq2])
        for node in E:
            vq1, vq2 = extract_qubits(node)
            e_distance += self._distance_matrix_element(v2p[vq1],v2p[vq2])
        f_distance = f_distance / size_F
        e_distance = (e_distance / size_E)
        H = f_distance + W * e_distance
        return H

    def _heuristic_score_basic_decay(self,
                         swap_gate_info: tuple,
                         front_layer: list, 
                         ) -> float:
        r"""The baisc_decay function is defined as follows:

        $$
        H = (\frac{1}{|F|}\sum_{gate\in F}D[\pi(gate.q1)][\pi(gate.q2)])\times \min(\max(decay(SWAP.q1),decay(SWAP.q2)),\frac{|E|}{|F|})
        $$

        """
        v2p,_ = update_v2p_and_p2v_mapping(self.v2p,swap_gate_info)
    
        F = front_layer
        size_F = len(F)
        max_decay = max(self.decay_parameter[v2p[swap_gate_info[1]]], self.decay_parameter[v2p[swap_gate_info[2]]])
        f_distance = 0
        for node in F:
            vq1, vq2 = extract_qubits(node)
            f_distance += self._distance_matrix_element(v2p[vq1],v2p[vq2])
        f_distance = f_distance / size_F
        H = max_decay * f_distance 
        return H
    
    def _heuristic_score_lookahead_decay(self,
                         swap_gate_info: tuple,
                         front_layer: list, 
                         ) -> float:
        r"""Computes a heuristic cost function that is used to rate a candidate SWAP to determine whether the SWAP gate can be inserted in a program to resolve qubit dependencies. 
        ref:https://github.com/Kaustuvi/quantum-qubit-mapping/blob/master/quantum_qubit_mapping/sabre_tools/heuristic_function.py

        The lookahead_decay function is defined as follows:
        
        $$
        H = (\frac{1}{|F|}\sum_{gate\in F}D[\pi(gate.q1)][\pi(gate.q2)] + W*\frac{1}{|E|}\sum_{gate\in E}D[\pi(gate.q1)][\pi(gate.q2)]) \times \min(\max(decay(SWAP.q1),decay(SWAP.q2)),\frac{|E|}{|F|})
        $$
    
        Args:
            swap_gate_info (tuple): Candidate SWAP gate of virtual circuit.
            front_layer (list): A list of gates that have no unexecuted predecessors in dag.
    
        Returns:
            float: The heuristic score for the candidate SWAP gate
        """
        v2p,_ = update_v2p_and_p2v_mapping(self.v2p,swap_gate_info)
    
        F = front_layer
        E = self.extended_successor_set
        size_E = len(E)
        if size_E == 0:
            size_E = 1
        size_F = len(F)
        W = min(self.max_extended_set_weight, size_E/size_F)
        max_decay = max(self.decay_parameter[v2p[swap_gate_info[1]]], self.decay_parameter[v2p[swap_gate_info[2]]])
        f_distance = 0
        e_distance = 0
        for node in F:
            vq1, vq2 = extract_qubits(node)
            f_distance += self._distance_matrix_element(v2p[vq1],v2p[vq2])
        for node in E:
            vq1, vq2 = extract_qubits(node)
            e_distance += self._distance_matrix_element(v2p[vq1],v2p[vq2])
        f_distance = f_distance / size_F
        e_distance = (e_distance / size_E)
        H = max_decay * (f_distance + W * e_distance)
        return H
    
    def _heuristic_score(self,
                         swap_gate_info: tuple,
                         front_layer: list, 
                         ) -> float:
        if self.heuristic == 'basic':
            H = self._heuristic_score_basic(swap_gate_info,front_layer)
        elif self.heuristic == 'lookahead':
            H = self._heuristic_score_lookahead(swap_gate_info,front_layer)
        elif self.heuristic == 'basic_decay':
            H = self._heuristic_score_basic_decay(swap_gate_info,front_layer)
        elif self.heuristic == 'lookahead_decay':
            H = self._heuristic_score_lookahead_decay(swap_gate_info,front_layer)
        return H
    
    def _single_sabre_routing(self) -> tuple[list,dict]:
        """Perform a single iteration of SABRE routing to generate gates and update v2p.
    
        Args:
            map_node_to_gate (bool): Whether to map nodes in the DAG to corresponding gate operations.
            do_random_choice (bool, optional): Whether to randomly choose a SWAP when multiple options 
                have the same heuristic score. Defaults to False.
    
        Returns:
            tuple[list, dict]: 
                - list: The list of gates generated after applying the SWAP sequence.
                - dict: The updated v2p mapping after the SWAP operations.
        """
    
        front_layer = list(nx.topological_generations(self.dag))
        if front_layer != []:
            front_layer = front_layer[0] 
        self._reset_decay_parameter()
        self._get_extended_successor_set(front_layer)
    
        nswap = 0
        ncycle = 0 
        nrepeat = 0
        front_layer_repeat = copy.deepcopy(front_layer)
        new = []
        collect_execute = []
        while len(front_layer) != 0:
            #time00 = time.time()
            #print('+++', ncycle, front_layer)
            ncycle += 1
            if front_layer_repeat == front_layer:
                nrepeat += 1
            else:
                front_layer_repeat = copy.deepcopy(front_layer)
                self._get_extended_successor_set(front_layer)
                nrepeat = 0
    
            execute_node_list = self._get_execute_node_list(front_layer)
            if execute_node_list:
                for execute_node in execute_node_list:
                    collect_execute.append(execute_node)
                    front_layer.remove(execute_node)
                    if self.do_map_node_to_gate:
                        gate_info = self._mapping_node_to_gate_info(execute_node)
                        new.append(gate_info)
                    for successor_node in self._dag_successors(execute_node):
                        if self._has_no_correlation_on_front_layer(successor_node,front_layer):
                            predecessors = self._dag_predecessors(successor_node)
                            if all(x in (front_layer + collect_execute) for x in predecessors):
                                front_layer.append(successor_node)
                self._reset_decay_parameter()
                #print('AAA', front_layer, execute_node_list)
            else:
                swap_candidate_list = self._get_swap_candidate_list(front_layer)
                swap_heuristic_score = {}
                for swap_gate_info in swap_candidate_list:
                    score = self._heuristic_score(swap_gate_info,front_layer)
                    swap_heuristic_score[swap_gate_info] = score

                min_score = min(swap_heuristic_score.values())
                best_swap = [swap for swap,score in swap_heuristic_score.items() if score == min_score]
                if len(best_swap)>1:
                    if self.do_random_choice:
                        min_score_swap_gate_info = random.choice(best_swap)
                    else:
                        min_score_swap_gate_info = best_swap[0]
                else:
                    min_score_swap_gate_info = best_swap[0]
                    
                if self.do_map_node_to_gate:
                    vq1 = min_score_swap_gate_info[1]
                    vq2 = min_score_swap_gate_info[2]
                    pq1 = self.v2p[vq1]
                    pq2 = self.v2p[vq2]
                    new.append(('swap',pq1,pq2))
                    nswap += 1
    
                if nrepeat==10*len(self.v2p):
                    exit(1)
                    raise(ValueError("A conflict occurred during the Sabre algorithm computation. Please contact the developer for assistance."))
                    
                
                # update decay parameter
                self._update_decay_parameter(min_score_swap_gate_info)

                # update v2p and p2v mapping
                self.v2p, self.p2v = update_v2p_and_p2v_mapping(self.v2p,min_score_swap_gate_info,)

        return new, nswap

    def run(self,qc:QuantumCircuit,):
        """Routing based on the Sabre algorithm.
        Args:
            iterations (int, optional): The number of iterations. Defaults to 1.
        Returns:
            Transpiler: Update self information.
        """

        all_qubits = split_qubits(qc)
        virtual_qubits = [x for sub in all_qubits for x in sub]

        self.v2p, self.p2v = self._initialize_v2p_p2v(virtual_qubits)
        init_p2v = {p:v for v,p in self.v2p.items()}

        dag = qc2dag(qc,show_qubits=False)
        rev_qc = qc.deepcopy()
        rev_qc.gates.reverse()
        rev_dag = qc2dag(rev_qc,show_qubits=False)
        self.do_map_node_to_gate = False
        for idx in range(self.iterations):
            if idx == self.iterations-1:
                self.do_map_node_to_gate = True
            if idx%2 == 0:
                self.dag_id = 'forward'
                self.dag = dag
            else:
                self.dag_id = 'reverse'
                self.dag = rev_dag

            new,nswap = self._single_sabre_routing()

            if self.iterations == 1:
                best_p2v = init_p2v
            else:
                if idx == self.iterations-2:
                    best_p2v = {p:v for v,p in self.v2p.items()}
                
        final_p2v = {p:v for v,p in self.v2p.items()}
        print('{:^21} -----> {:^21} -----> {:^21}'.format('initial mapping','best mapping','final mapping'))
        print('{:^10}:{:^10} -----> {:^10}:{:^10} -----> {:^10}:{:^10}'.format('P','V','P','V','P','V'))
        for p in sorted(init_p2v.keys()):
            print('{:^10}:{:^10} -----> {:^10}:{:^10} -----> {:^10}:{:^10}'.format(p,init_p2v[p],p,best_p2v[p],p,final_p2v[p]))
        print('A total of {} swap gates have been added to the circuit.'.format(nswap))
        new_qc = QuantumCircuit(max(self.physical_qubits)+1,qc.ncbits)
        new_qc.gates = new
        new_qc.params_value = qc.params_value
        new_qc.qubits = self.physical_qubits
        return new_qc 