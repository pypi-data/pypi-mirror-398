from enum import Enum
import importlib
import json
import logging
import signal
import sys
import time
import zipfile
from contextlib import contextmanager
from functools import partial
from pathlib import Path
import traceback
from tempfile import TemporaryDirectory
from typing import List, Optional
import numpy as np
import gymnasium as gym
import torch
from bbrl.agents.gymnasium import ParallelGymAgent, make_env
from bbrl.workspace import Workspace
from gymnasium import spec
from gymnasium.envs.registration import load_env_creator
from master_mind.rld.stk_graph import STKLivePlotServer
from pystk2_gymnasium import AgentSpec, MonoAgentWrapperAdapter, AgentException


class InteractionMode(Enum):
    NONE = 0
    INTERACTIVE = 1
    MAP = 2


class TimeoutError(Exception):
    """Exception raised when an agent action times out."""

    pass


@contextmanager
def timeout(seconds: float):
    """Context manager that raises TimeoutError if code takes too long.

    Args:
        seconds: Maximum time in seconds to allow the code to run.
    """

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)

    try:
        yield
    finally:
        # Disable the alarm and restore the old handler
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)


def fail(message: str):
    logging.error(message)
    sys.exit(1)


@contextmanager
def sys_path(dir: Path):
    sys.path.insert(0, str(dir.absolute()))
    yield
    sys.path.pop(0)


def load_player_from_module(
    key: str, module_name: str, error_handling=False, name_opt: str = None
):
    # Get the module
    try:
        mod_actor = importlib.import_module(f"{module_name}.pystk_actor")
    except Exception as e:
        if error_handling:
            raise AgentException("Exception when loading module", key) from e
        raise e

    # Get the path
    py_dir = Path(mod_actor.__file__).parent

    # Get the environment
    env_name = getattr(mod_actor, "env_name", None) or fail(
        "No env_name in pystk_actor.py"
    )
    assert isinstance(env_name, str), "env_name is not as string in pystk_actor.py"

    # Get the player name
    player_name = getattr(mod_actor, "player_name", None) or fail(
        "No player_name in pystk_actor.py"
    )
    if name_opt:
        player_name = name_opt[0]
        logging.info("Overriding player name: %s", player_name)
    assert isinstance(
        player_name, str
    ), "player_name is not as string in pystk_actor.py"

    env_spec = spec(env_name)
    assert (
        env_spec.entry_point == "pystk2_gymnasium.envs:STKRaceEnv"
    ), f"Not a standard STK race environment (got {env_spec.entry_point})"

    def wrappers_factory(env):
        # Apply environment wrappers
        for wrapper_spec in env_spec.additional_wrappers:
            logging.info("Adding wrapper %s", wrapper_spec)
            env = load_env_creator(wrapper_spec.entry_point)(
                env=env, **wrapper_spec.kwargs
            )

        # Apply the wrappers (if they exist)
        get_wrappers = getattr(mod_actor, "get_wrappers", lambda: [])
        for wrapper in get_wrappers():
            logging.info("Adding wrapper %s", wrapper)
            env = wrapper(env)
        return env

    # Load the actor
    get_actor = getattr(mod_actor, "get_actor", None) or fail(
        "No get_actor function in pystk_actor.py"
    )

    def actor_factory(env: gym.Env):
        pth_path = py_dir / "pystk_actor.pth"
        params = None
        if pth_path.is_file():
            params = torch.load(
                pth_path,
                map_location=torch.device("cpu"),
                weights_only=True,
            )
        else:
            logging.warning("No pystk_actor.pth file for actor %s", player_name)
        actor = get_actor(
            params,
            env.observation_space[key],
            env.action_space[key],
        )
        return actor

    logging.info("Loaded player %s", player_name)
    return player_name, wrappers_factory, actor_factory


def load_player(dir: Path, key: str, file_or_module: str, error_handling=False):
    """Check that the BBRL agent is valid and load the agent

    The zip file or folder should contain a:

    - a `pystk_actor.py` file
    - a `pystk_actor.pth` file
    """

    file_or_module, *name_opt = file_or_module.rsplit("@:", -1)

    path = Path(file_or_module)
    py_dir = dir / f"player_{key}"

    # Directory
    if path.is_dir() and (path / "stk_actor" / "pystk_actor.py").is_file():
        py_dir.symlink_to((path / "stk_actor").resolve())
        with sys_path(py_dir.parent):
            return load_player_from_module(
                key,
                f"player_{key}",
                name_opt=name_opt,
                error_handling=error_handling,
            )

    # Module name: use as is
    if not path.is_file():
        return load_player_from_module(
            key, file_or_module, error_handling=error_handling, name_opt=name_opt
        )

    # Extract ZIP and load the module
    with zipfile.ZipFile(path.absolute(), "r") as zip_ref:
        zip_path = zipfile.Path(zip_ref)
        assert (
            zip_path / "pystk_actor.py"
        ).is_file, "Could not find an pystk_actor.py file"
        assert (
            zip_path / "pystk_actor.pth"
        ).is_file, "Could not find an pystk_actor.pth file"
        logging.info("Extracting %s into %s", path, dir)

        # Extract and set path
        zip_ref.extractall(py_dir)

    (py_dir / "__init__.py").touch()

    with sys_path(dir):
        return load_player_from_module(
            key, f"player_{key}", name_opt=name_opt, error_handling=error_handling
        )


def get_action(workspace: Workspace, t: int):
    name = "action"

    if name in workspace.variables:
        # Action is a tensor
        action = workspace.get(name, t)
    else:
        # Action is a dictionary
        action = {}
        prefix = f"{name}/"
        len_prefix = len(prefix)
        for varname in workspace.variables:
            if not varname.startswith(prefix):
                continue
            keys = varname[len_prefix:].split("/")
            current = action
            for key in keys[:-1]:
                current = current.setdefault(key, {})
            current[keys[-1]] = workspace.get(varname, t)

    return action


def dict_slice(k: int, object):
    if isinstance(object, dict):
        return {key: dict_slice(k, value) for key, value in object.items()}
    return object[k]


def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


@torch.no_grad()
def race(
    hide: bool,
    num_karts: Optional[int],
    zip_files: List[Path],
    interaction=InteractionMode.NONE,
    output: Optional[Path] = None,
    error_handling=False,
    action_timeout: Optional[float] = None,
    max_paths: Optional[int] = None,
):
    try:
        server = None
        num_karts = num_karts or len(zip_files)
        assert num_karts >= len(zip_files), "Not enough karts"

        with TemporaryDirectory() as dir:
            dir = Path(dir)
            logging.info("Loading the agents")
            agent_factories = {}
            wrapper_factories = {}
            agents_spec = []
            player_names = []
            for agent_ix, zip_file in enumerate(zip_files):
                key = str(agent_ix)
                player_name, wrappers_factory, agent_factory = load_player(
                    dir, key, zip_file, error_handling=error_handling
                )
                player_names.append(player_name)
                agent_factories[key] = agent_factory
                wrapper_factories[key] = wrappers_factory
                agents_spec.append(AgentSpec(name=player_name))

            # Create the environment
            n_agents = len(agents_spec)
            env = make_env(
                "supertuxkart/multi-full-v0",
                render_mode=None if hide else "human",
                num_kart=num_karts,
                max_paths=max_paths,
                agents=agents_spec,
                wrappers=[
                    partial(
                        MonoAgentWrapperAdapter,
                        keep_original=interaction != InteractionMode.NONE,
                        wrapper_factories=wrapper_factories,
                    )
                ],
            )

            # Get the actors and put them in eval mode
            assert isinstance(env, MonoAgentWrapperAdapter)

            agents = []
            for key, agent_factory in agent_factories.items():
                try:
                    agents.append(agent_factory(env))
                except Exception as e:
                    if error_handling:
                        raise AgentException(
                            "Exception when initializing the actor", key
                        ) from e
                    raise e

            for agent in agents:
                agent.eval()

            workspaces = [Workspace() for _ in range(n_agents)]

            # Track action times for each agent
            action_times = [[] for _ in range(n_agents)]

            logging.info("Starting a race")

            done = False
            obs, _ = env.reset()
            choice = ""

            # List possible keys
            keys = []
            for key, item in obs.items():
                if isinstance(item, dict):
                    for subkey in item.keys():
                        keys.append((key, subkey))
            keys.sort()

            # Start plotly server if needed
            if interaction == InteractionMode.MAP:
                port = 8050
                server = STKLivePlotServer(env.unwrapped, port=port)
                url = server.start(block=False)
                print(f"Started track display server on {url}")  # noqa: T201

            # Main loop
            t = 0
            while not done:
                if interaction != InteractionMode.NONE:
                    if server is not None:
                        server.update_plot(obs["original/0"])
                    while True:
                        for s in choice.split(","):
                            if is_integer(s):
                                try:
                                    ix = int(s)
                                except Exception:
                                    pass

                                value = obs[keys[ix][0]][keys[ix][1]]
                                if isinstance(value, (tuple, list)):
                                    value = np.stack(value)
                                print(  # noqa: T201
                                    f"{keys[ix][0]}.{keys[ix][1]}", ": ", value
                                )

                        print()  # noqa: T201
                        print("(q) Quitter")  # noqa: T201
                        print(  # noqa: T201
                            "\n".join(
                                f"({ix}) {key[0]}.{key[1]}"
                                for ix, key in enumerate(keys)
                            )
                        )
                        print()  # noqa: T201
                        print()  # noqa: T201

                        old_choice = choice
                        choice = input("Choice (q: quit, p: print): ").lower().strip()

                        if choice == "":
                            choice = old_choice
                            break

                        if choice == "q":
                            sys.exit()

                actions = {}
                for ix in range(n_agents):
                    key = str(ix)
                    obs_agent = ParallelGymAgent._format_frame(obs[key])
                    for var_key, var_value in obs_agent.items():
                        workspaces[ix].set(f"env/{var_key}", t, var_value)

                    # Run the agent and measure time
                    start_time = time.perf_counter()
                    try:
                        if action_timeout is not None:
                            with timeout(action_timeout):
                                agents[ix](workspaces[ix], t=t)
                                action = get_action(workspaces[ix], t=t)
                        else:
                            agents[ix](workspaces[ix], t=t)
                            action = get_action(workspaces[ix], t=t)

                        # Record successful action time
                        elapsed_time = time.perf_counter() - start_time
                        action_times[ix].append(elapsed_time)
                    except TimeoutError as e:
                        if error_handling:
                            raise AgentException(
                                f"Agent action timed out after {action_timeout}s", key
                            ) from e
                        raise e
                    except Exception as e:
                        if error_handling:
                            raise AgentException(
                                "Exception when choosing action", key
                            ) from e
                        raise e

                    # Takes the first action
                    if isinstance(action, dict):
                        action = dict_slice(0, action)
                    else:
                        action = action[0]
                    # print(t, key, action)

                    actions[key] = action

                obs, reward, terminated, truncated, info = env.step(actions)
                done = terminated or truncated
                t += 1

            rewards = info["reward"]
            payload = []
            message = {
                "type": "results",
                "track": env.unwrapped.current_track,
                "results": payload,
            }
            for ix in range(n_agents):
                key = str(ix)
                # Calculate average action time
                avg_action_time = (
                    float(np.mean(action_times[ix])) if action_times[ix] else 0.0
                )
                payload.append(
                    {
                        "key": ix,
                        "reward": rewards[key],
                        "position": info["infos"][key]["position"],
                        "name": player_names[ix],
                        "avg_action_time": avg_action_time,
                    }
                )
                logging.info(
                    "Agent %s (%s): avg action time = %.4fs",
                    ix,
                    player_names[ix],
                    avg_action_time,
                )

    except AgentException as e:
        cause = e if e.__cause__ is None else e.__cause__
        tb = traceback.extract_tb(cause.__traceback__)
        message = {
            "key": int(e.key),
            "name": player_names[int(e.key)] if len(player_names) > int(e.key) else "?",
            "when": str(e),
            "message": str(cause),
            "traceback": traceback.format_list(tb),
        }

    finally:
        if server is not None:
            server.close()

    if output:
        with output.open("wt") as fp:
            json.dump(message, fp)
    else:
        print(json.dumps(message))  # noqa: T201
