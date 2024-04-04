# atomics.py
#   atomic c2sim bt functions
# by: Noah Syrkis

# imports
import jax
import jax.numpy as jnp
from jax import random, lax
from jaxmarl import make

from functools import partial

from .utils import Status

# constants
SUCCESS, FAILURE, RUNNING = Status.SUCCESS, Status.FAILURE, Status.RUNNING


# functions
def see_fn(obs, agent, env):
    other_obs = obs[: -len(env.own_features)].reshape(env.num_agents - 1, -1)
    split_idx = env.num_allies - (jnp.where(agent.startswith("ally"), 1, 0))
    mask = jnp.arange(env.num_agents - 1) < split_idx
    bool_ = jnp.where(agent.startswith("ally"), 0, 1)
    mask = mask
    return other_obs, mask


# atomics
def enemy_found(_, obs, agent, env):  # see's for a given AGENT
    other_obs, mask = see_fn(obs, agent, env)
    cond = other_obs[mask].any()
    return jnp.where(cond, SUCCESS, FAILURE)


def find_enemy(rng, _, __, ___):  # walk around randomly to find enemy
    # just chose a random direction to move in for now
    return RUNNING, random.randint(rng, (1,), 0, 5)[0]


def attack_enemy(rng, obs, agent, env):  # attack random enemy in range
    other_obs, mask = see_fn(obs, agent, env)
    mask = jnp.where(agent.startswith("ally"), ~mask, mask[::-1])
    in_sight = other_obs[mask].any(axis=1)
    idxs = jnp.where(in_sight, size=mask.size)[0]
    one_hot = jnp.put(jnp.zeros(in_sight.size), idxs, 1, inplace=False)
    probs = jnp.where(one_hot.sum() > 0, one_hot / one_hot.sum(), one_hot)
    probs = jnp.concatenate((probs, (1 - probs.sum()).reshape(1)))
    actions = jnp.arange(probs.size).at[-1].set(-1)
    action = random.choice(rng, actions, p=probs)
    return SUCCESS, action


def main():
    env = make("SMAX", num_allies=2, num_enemies=5)
    rng, key = jax.random.split(jax.random.PRNGKey(0))
    obs, state = env.reset(key)
    # out = attack_enemy(rng, obs["ally_0"], "ally_0", env)
    # out = find_enemy(rng, obs["ally_0"], "ally_0", env)
    out = enemy_found(rng, obs["ally_0"], "ally_0", env)
    print(out)
