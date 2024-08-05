# agent.py
#  functions for agents
# by: Noah Syrkis

# imports
import jax.numpy as jnp
from jax import random, vmap, jit
import c2sim


# functions
def env_info_fn(env):
    return c2sim.types.EnvInfo(
        num_agents=env.num_agents,
        num_allies=env.num_allies,
        num_enemies=env.num_enemies,

        num_types=jnp.array(len(env.unit_type_names)),
        num_own_features=jnp.array(len(env.own_features)),

        world_steps_per_env_step=env.world_steps_per_env_step,
        time_per_step=env.time_per_step,

        # map info
        map_width=env.map_width,
        map_height=env.map_height,
        terrain_raster = env.terrain_raster, # 2D array of terrain types
    )

def agent_info_fn(env, agent):  # <- this is the function that is called in ludens.py. It passes agent info to each cope of the agent in the environment
    agent_info = c2sim.types.AgentInfo(
        agent_id=jnp.array(env.agent_ids[agent]),
        velocity=jnp.array(env.agent_ids[agent]),
        sight_range=jnp.array(env.agent_ids[agent]),
        attack_range=jnp.array(env.agent_ids[agent]),
        is_ally=jnp.array(agent.startswith('ally'))
    )
    return agent_info
