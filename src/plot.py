# plot.py
#   plot code
# by: Noah Syrkis

# imports
import imageio
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import darkdetect
from matplotlib import rcParams
import numpy as np
from jax import numpy as jnp, vmap
from tqdm import tqdm
from src.smax import bullet_fn

# +
# globals
rcParams["font.family"] = "monospace"
rcParams["font.monospace"] = "Fira Code"
bg = "black" if darkdetect.isDark() else "white"
ink = "white" if bg == "black" else "black"
markers = {0: "o", 1: "s", 2: "D", 3: "^", 4: "<", 5: ">", 6: "+"}


action2txt_base = {
    -2: " ",
    -1: " ",
    0: "↑",
    1: "→",
    2: "↓",
    3: "←",
    4: "∅",
}
def action2txt(a): 
    return action2txt_base[a] if a in action2txt_base else f"{int(a-5)}"


# -

# params
tick_params = {
    "colors": ink,
    "direction": "in",
    "length": 6,
    "width": 1,
    "which": "both",
    "top": True,
    "bottom": True,
    "left": True,
    "right": True,
    "labelleft": False,
    "labelbottom": False,
}


# functions
def plot_fn(env, state_seq, reward_seq, expand=False, path=None):
    n_steps = len(state_seq)
    bullet_seq = bullet_fn(env, state_seq) if expand else None
    state_seq = state_seq if not expand else vmap(env.expand_state_seq)(state_seq)
    frames, returns = [], return_fn(reward_seq)
    unit_types = np.unique(np.array(state_seq[0][1].unit_types))
    unit_sight_range = [
        env.unit_type_sight_ranges[unit_type] for unit_type in unit_types
    ]
    unit_attack_range = [
        env.unit_type_attack_ranges[unit_type] for unit_type in unit_types
    ]
    fills = np.where(np.array(state_seq[0][1].unit_teams) == 1, ink, "None")
    for i, (_, state, actions) in tqdm(enumerate(state_seq), total=len(state_seq)):
        fig, axes = plt.subplots(2, 3, figsize=(18.08, 12), facecolor=bg, dpi=50)
        bullets = bullet_seq[i // 8] if expand and i < (len(bullet_seq) * 8) else None
        args = (
            returns,
            state,
            bullets,
            i,
            unit_types,
            unit_sight_range,
            unit_attack_range,
            fills,
            actions,
        )
        seq = [(ax, j, *args) for j, ax in enumerate(axes.flatten())]
        for ax, j, *args in seq:
            axis_fn(ax, j, *args)
        frames.append(frame_fn(n_steps, fig, i // 8 if expand else i, path))
    fname = (
        "docs/figs" if path is None else path
    ) + f"/worlds_{bg}{'_laggy' if not expand else ''}.mp4"
    imageio.mimsave(fname, frames, fps=24 if expand else 3)


def return_fn(reward_seq):
    reward = [reward_fn(reward) for reward in reward_seq]
    ally = jnp.stack([v[0] for v in reward]).cumsum(axis=0)
    enemy = jnp.stack([v[1] for v in reward]).cumsum(axis=0)
    return {"ally": ally, "enemy": enemy}


def reward_fn(reward):
    ally_rewards = jnp.stack([v for k, v in reward.items() if k.startswith("ally")])
    enemy_rewards = jnp.stack([v for k, v in reward.items() if k.startswith("enemy")])
    return ally_rewards.sum(axis=0), enemy_rewards.sum(axis=0)


def frame_fn(n_steps, fig, idx, path=None):
    title = f"step : {str(idx).zfill(len(str(n_steps - 1)))} | model : random"
    fig.text(0.01, 0.5, title, va="center", rotation="vertical", fontsize=20, color=ink)
    sublot_params = {"hspace": 0.3, "wspace": 0.3, "left": 0.05, "right": 0.95}
    plt.subplots_adjust(**sublot_params)
    fig.canvas.draw()
    fig.tight_layout()
    width, height = fig.get_size_inches() * fig.get_dpi()
    shape = (int(height), int(width), 4)
    frame = np.frombuffer(fig.canvas.buffer_rgba(), np.uint8).reshape(shape)[..., :3]
    if idx == n_steps - 1:
        plt.savefig(
            ("docs/figs" if path is None else path) + f"/worlds_{bg}.jpg", dpi=200
        )
    plt.close()  # close fig
    return frame


# +
#sdebug_colors = ["red", "green", "blue", "pink", "orange", "purple", "cyan", "yellow"]  # for knowing who is who during isual debugging
debug_colors = [ink]

def axis_fn(
    ax,
    j,
    returns,
    state,
    bullets,
    i,
    unit_types,
    unit_sight_range,
    unit_attack_range,
    fills,
    actions,
):
    aux_ax_fn(ax, bullets, returns, i, j, actions)
    for unit_idx, unit_type in enumerate(unit_types):
        idx = state.unit_types[j, :] == unit_type
        x = state.unit_positions[j, idx, 0]
        y = state.unit_positions[j, idx, 1]
        c = fills[j, idx]
        s = state.unit_health[j, idx] ** 1.5 * 0.1
        ec = [debug_colors[k%len(debug_colors)] for k in range(len(x))]
        ax.scatter(x, y, s=s, c=c, edgecolor=ec, marker=markers[unit_type])
        for i in range(len(x)):
            if state.unit_health[j, idx][i] > 0:
                circle = plt.Circle(
                    (x[i], y[i]),
                    unit_sight_range[unit_idx],
                    color=ink,
                    ls=(0, (1, 10)),
                    fill=False,
                )
                ax.add_patch(circle)
                circle = plt.Circle(
                    (x[i], y[i]),
                    unit_attack_range[unit_idx],
                    color=ink,
                    fill=True,
                    alpha=0.05,
                )
                ax.add_patch(circle)


# -

def aux_ax_fn(ax, bullets, returns, i, j, actions):
    if bullets is not None:
        idx = bullets[:, 0] == j
        alpha = i % 8 / 8
        pos = (1 - alpha) * bullets[idx, 3:5] + alpha * bullets[idx, 5:]
        ax.scatter(pos[:, 0], pos[:, 1], s=10, c=ink, marker=",")
    ally_actions = [actions[a][j].item() for a in actions if a[0] == "a"]
    enemy_actions = [actions[a][j].item() for a in actions if a[0] == "e"]
    ally_return = returns["ally"][i, j]
    enemy_return = returns["enemy"][i, j]
    ax.set_xlabel("\n{:.3f} | {:.3f}".format(ally_return, enemy_return), color=ink)
    ax.set_title(f"{' '.join([action2txt(a) for a in ally_actions])} | {' '.join([action2txt(a) for a in enemy_actions])}\n", color=ink)
    ax.set_facecolor(bg)
    ticks = np.arange(2, 31, 4)  # Assuming your grid goes from 0 to 32
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)
    ax.tick_params(**tick_params)
    ax.set_aspect("equal")
    ax.set_xlim(-2, 34)
    ax.set_ylim(-2, 34)
