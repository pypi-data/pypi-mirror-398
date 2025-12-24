from __future__ import annotations

import operator as op
from dataclasses import dataclass
from typing import FrozenSet, Mapping, Optional, Tuple

import funcy as fn
from pyrsistent import pmap
from pyrsistent.typing import PMap

from aiger import common as cmn
from aiger.aig import AIG, AndGate, ConstFalse, Input, Inverter, LatchIn, to_aig


@dataclass(frozen=True)
class NodeDef:
    kind: str
    children: Tuple[str, ...] = ()
    name: Optional[str] = None
    value: Optional[bool] = None


NodeMap = PMap[str, NodeDef]


@dataclass(frozen=True)
class ImmutableAIG:
    inputs: FrozenSet[str]
    output_map: PMap[str, str]
    latch_map: PMap[str, str]
    latch2init: PMap[str, bool]
    nodes: NodeMap
    node_order: Tuple[str, ...]
    comments: Tuple[str, ...] = ()

    @property
    def outputs(self) -> FrozenSet[str]:
        return frozenset(self.output_map.keys())

    @property
    def latches(self) -> FrozenSet[str]:
        return frozenset(self.latch_map.keys())

    def __call__(
        self,
        inputs: Mapping[str, bool],
        latches=None,
        *,
        lift=None,
    ):
        if latches is None:
            latches = {}
        else:
            latches = dict(latches)

        if lift is None:
            lift = fn.identity
            and_, neg = op.and_, op.not_
        else:
            and_, neg = op.__and__, op.__invert__

        latch_inputs = fn.merge(dict(self.latch2init), latches)
        latch_inputs = fn.project(latch_inputs, self.latches)

        mem = {}
        for node_id in self.node_order:
            node_def = self.nodes[node_id]
            kind = node_def.kind

            if kind == 'input':
                mem[node_id] = lift(inputs[node_def.name])
            elif kind == 'latch_in':
                mem[node_id] = lift(latch_inputs[node_def.name])
            elif kind == 'const':
                mem[node_id] = lift(node_def.value)
            elif kind == 'and':
                left, right = node_def.children
                mem[node_id] = and_(mem[left], mem[right])
            elif kind == 'not':
                (child,) = node_def.children
                mem[node_id] = neg(mem[child])
            else:
                raise ValueError(f'Unexpected node kind {kind!r}')

        outs = {name: mem[nid] for name, nid in self.output_map.items()}
        louts = {name: mem[nid] for name, nid in self.latch_map.items()}
        return outs, louts

    @classmethod
    def from_aig(cls, circ: AIG) -> 'ImmutableAIG':
        node_defs: dict[str, NodeDef] = {}
        node_to_id: dict[object, str] = {}
        gate_counter = 0

        def _next_gate(kind: str) -> str:
            nonlocal gate_counter
            node_id = f'node:{kind}:{gate_counter}'
            gate_counter += 1
            return node_id

        for node in cmn.dfs(circ):
            if isinstance(node, Input):
                node_id = f'input:{node.name}'
                node_def = NodeDef(kind='input', name=node.name)
            elif isinstance(node, LatchIn):
                node_id = f'latch:{node.name}'
                node_def = NodeDef(kind='latch_in', name=node.name)
            elif isinstance(node, ConstFalse):
                node_id = _next_gate('const')
                node_def = NodeDef(kind='const', value=False)
            elif isinstance(node, Inverter):
                node_id = _next_gate('not')
                child = node_to_id[node.input]
                node_def = NodeDef(kind='not', children=(child,))
            elif isinstance(node, AndGate):
                node_id = _next_gate('and')
                left = node_to_id[node.left]
                right = node_to_id[node.right]
                node_def = NodeDef(kind='and', children=(left, right))
            else:
                raise TypeError(f'Unsupported node type {type(node)}')

            node_defs[node_id] = node_def
            node_to_id[node] = node_id

        node_order = tuple(node_defs.keys())
        output_map = pmap({name: node_to_id[node] for name, node in circ.node_map.items()})
        latch_map = pmap({name: node_to_id[node] for name, node in circ.latch_map.items()})
        nodes = pmap(node_defs)

        return cls(
            inputs=frozenset(circ.inputs),
            output_map=output_map,
            latch_map=latch_map,
            latch2init=pmap(circ.latch2init),
            nodes=nodes,
            node_order=node_order,
            comments=tuple(circ.comments),
        )

    def to_aig(self) -> AIG:
        node_instances: dict[str, object] = {}
        for node_id in self.node_order:
            node_def = self.nodes[node_id]
            kind = node_def.kind

            if kind == 'input':
                node_instances[node_id] = Input(node_def.name)
            elif kind == 'latch_in':
                node_instances[node_id] = LatchIn(node_def.name)
            elif kind == 'const':
                if node_def.value:
                    node_instances[node_id] = Inverter(ConstFalse())
                else:
                    node_instances[node_id] = ConstFalse()
            elif kind == 'not':
                (child,) = node_def.children
                node_instances[node_id] = Inverter(node_instances[child])
            elif kind == 'and':
                left, right = node_def.children
                node_instances[node_id] = AndGate(node_instances[left], node_instances[right])
            else:
                raise ValueError(f'Unexpected node kind {kind!r}')

        node_map = {name: node_instances[nid] for name, nid in self.output_map.items()}
        latch_map = {name: node_instances[nid] for name, nid in self.latch_map.items()}
        return AIG(
            inputs=self.inputs,
            node_map=node_map,
            latch_map=latch_map,
            latch2init=self.latch2init,
            comments=self.comments,
        )


def to_immutable(circ) -> ImmutableAIG:
    return ImmutableAIG.from_aig(to_aig(circ))


__all__ = ['ImmutableAIG', 'NodeDef', 'to_immutable']
