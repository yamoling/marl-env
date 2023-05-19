from typing import TypeVar
from rlenv.models import ActionSpace
from .rlenv_wrapper import RLEnvWrapper, RLEnv

A = TypeVar("A", bound=ActionSpace)


class TimeLimitWrapper(RLEnvWrapper[A]):
    def __init__(self, env: RLEnv[A], step_limit: int) -> None:
        super().__init__(env)
        self._step_limit = step_limit
        self._current_step = 0

    def reset(self):
        self._current_step = 0
        return super().reset()

    def step(self, actions):
        self._current_step += 1
        obs_, reward, done, truncated, info = super().step(actions)
        truncated = truncated or (self._current_step >= self._step_limit)
        return obs_, reward, done, truncated, info

    def kwargs(self) -> dict[str,]:
        return {"step_limit": self._step_limit}
