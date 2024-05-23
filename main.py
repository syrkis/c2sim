# main.py
#   c2sim main
# by: Noah Syrkis

# imports
import yaml
from jax import random, vmap, jit
from jax import numpy as jnp
from jaxmarl import make
from jaxmarl.environments.smax import map_name_to_scenario
from tqdm import tqdm
from functools import partial
from src import parse_args, scripts, make_bt, plot_fn, grammar_fn, dict_fn, load_trees
from src.utils import Status, STAND, scenarios


# constants
with open("config.yaml", "r") as f:
    conf = yaml.safe_load(f)
n_envs = conf["n_envs"]
n_trees = conf["n_trees"]
n_steps = conf["n_steps"]
n_allies = conf["n_allies"]
n_enemies = conf["n_enemies"]


# trajectory functions
def step_fn(bts, rng, old_state_v, obs_v, env):  # take a step in the env
    rng, step_rng = random.split(rng)
    step_keys = random.split(step_rng, n_envs * n_trees)
    idxs = jnp.arange(n_envs * n_trees) % n_envs
    acts = {a: bts(old_state_v, idxs, obs_v[a], a) for i, a in enumerate(env.agents)}
    obs_v, state_v, reward_v, done, info = vmap(env.step)(step_keys, old_state_v, acts)
    return obs_v, (bts, rng, state_v), (step_keys, old_state_v, acts), reward_v


def traj_fn(btv, rng, env, state_seq, reward_seq):  # take n_steps in m env
    rng, reset_rng = random.split(rng)  # split rng for reset and step
    reset_keys = random.split(reset_rng, n_envs * n_trees)  # split reset rng for n_envs
    obs_v, state_v = vmap(env.reset)(reset_keys)  # initiate envs
    traj_state = (btv, rng, state_v)  # initial state for step_fn
    for _ in tqdm(range(n_steps)):  # take n steps in env and append to lists
        obs_v, traj_state, state_v, reward_v = step_fn(*traj_state, obs_v, env)
        state_seq.append(state_v)
        reward_seq.append(reward_v)
    return state_seq, reward_seq


def trees_fn(bts):
    def bts_fn(state, idx, obs, agent):
        state, action = STAND, STAND
        i = 0
        for bt in bts:
            tree_state, tree_action = bt["tree"](state, obs, agent)
            state = jnp.where(idx == i, tree_state, state)
            action = jnp.where(idx == i, tree_action, action)
            i += 1
        return action

    bts_fn = jit(bts_fn, static_argnums=(3))
    return bts_fn


def main():
    args = parse_args()

    if args.script in scripts:
        scripts[args.script]()

    else:
        env = make("SMAX", scenario=map_name_to_scenario(scenarios[-3]))
        bts = vmap(trees_fn(load_trees(env)), in_axes=(0, 0, 0, None))
        rng = random.PRNGKey(0)
        seq = traj_fn(bts, rng, env, [], [])  # seq[0][0][2] is the first action dict
        # plot_fn(env, seq[0], seq[1], expand=True)


if __name__ == "__main__":
    main()
