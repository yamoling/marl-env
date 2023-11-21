import numpy as np
from typing import Literal
from smac.env import StarCraft2Env

from rlenv.models import RLEnv, Observation, DiscreteActionSpace


class SMAC(RLEnv[DiscreteActionSpace]):
    """Wrapper for the SMAC environment to work with this framework"""

    def __init__(self, map_name: str) -> None:
        self._env = StarCraft2Env(map_name=map_name)
        action_space = DiscreteActionSpace(self._env.n_agents, self._env.n_actions)
        super().__init__(action_space)
        self._env_info = self._env.get_env_info()
        self._seed = self._env.seed()
        self.name = f"smac-{self._env.map_name}"

    @property
    def state_shape(self):
        return (self._env_info["state_shape"],)

    @property
    def observation_shape(self):
        return (self._env_info["obs_shape"],)

    def reset(self):
        obs, state = self._env.reset()
        obs = Observation(np.array(obs), self.available_actions(), state)
        return obs

    def get_state(self):
        return self._env.get_state()

    def step(self, actions):
        reward, done, info = self._env.step(actions)
        obs = Observation(
            np.array(self._env.get_obs()), self.available_actions(), self.get_state()
        )
        return obs, reward, done, False, info

    def available_actions(self):
        return np.array(self._env.get_avail_actions())

    def render(self, mode: Literal["human", "rgb_array"] = "human"):
        return self._env.render(mode)

    def seed(self, seed_value: int):
        self._env = StarCraft2Env(map_name=self._env.map_name, seed=seed_value)
