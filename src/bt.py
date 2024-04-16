# bt.py
#   behavior tree code
# by: Noah Syrkis

# imports
import jax
import jax.numpy as jnp
from jax import jit, vmap
import chex
from jaxmarl import make

import os
from functools import partial
from typing import Any, Callable, List, Tuple, Dict

from src.utils import Status, NodeFunc as NF
import src.atomics as atomics
from .bank import grammar_fn, parse_fn, dict_fn

# constants
ATOMIC_FNS = {fn: getattr(atomics, fn) for fn in dir(atomics) if not fn.startswith("_")}
SUCCESS, FAILURE, RUNNING = Status.SUCCESS, Status.FAILURE, Status.RUNNING
PARENT_DIR = os.path.dirname(os.path.dirname(__file__))


# functions
def tree_fn(children: List[NF], kind: str) -> NF:  # sequence / fallback (selector) node
    def tick(obs: jnp.array, agent, env) -> Status:
        state, action = SUCCESS if kind.startswith("seq") else FAILURE, -1
        for child in children:  # loop through all children
            child_state, child_action = child(obs, agent, env)

            # node conditions
            seq_cond = jnp.logical_and(kind.startswith("s"), child_state != SUCCESS)
            fall_cond = jnp.logical_and(kind.startswith("f"), child_state != FAILURE)
            cond = jnp.logical_and(jnp.logical_or(seq_cond, fall_cond), action == -1)

            # update return values
            state = jnp.where(cond, child_state, state)
            action = jnp.where(cond, child_action, action)
        return state, action

    return tick


def atomic_fn(fn: Callable, dec_fn: Callable = None) -> NF:
    def tick(obs: jnp.array, agent, env) -> Status:
        args = (obs, agent, env)
        response = dec_fn(*fn(*args)) if dec_fn is not None else fn(*args)
        return response if isinstance(response, tuple) else (response, -1)

    return tick


def make_bt(env, tree) -> NF:
    def make_node(node: dict) -> NF:
        if node[0] in ["sequence", "fallback"]:
            children = [make_node(child) for child in node[1]]
            return tree_fn(children, node[0])
        if node[0] in ["condition", "action"]:
            fn = ATOMIC_FNS[node[1]]
            return atomic_fn(fn)
        if node[0] == "decorator":
            dec_fn = ATOMIC_FNS[node[1][0]]
            subtree = make_node(node[1][1])
            return atomic_fn(subtree, dec_fn)
        raise ValueError(f"Invalid node type: {node[0]}")

    return partial(make_node(tree), env=env)  # partial to pass env to all nodes


def main():
    tree = dict_fn(parse_fn(PARENT_DIR + "/bank/default.bt"))
    rng = jax.random.PRNGKey(1)
    env = make("SMAX", num_allies=10, num_enemies=10)
    bt = make_bt(env, tree)
    obs, state = env.reset(rng)
    rngs = jax.random.split(rng, env.num_agents)
    acts = {a: bt(rngs[idx], obs[a], a)[1] for idx, a in enumerate(env.agents)}
    for k, v in acts.items():
        print(f"{k}: {v}")
