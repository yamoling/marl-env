from typing import Any, Optional, TypeVar, Generic
from abc import abstractmethod, ABC
import numpy as np
import numpy.typing as npt
import math
from serde import serde
from dataclasses import dataclass

S = TypeVar("S", bound="Space")


@serde
@dataclass
class Space(ABC):
    shape: tuple[int, ...]
    n_dims: int
    labels: list[str]

    def __init__(self, shape: tuple[int, ...], labels: Optional[list[str]] = None):
        self.shape = shape
        self.n_dims = len(shape)
        if labels is None:
            labels = [f"Dim {i}" for i in range(self.n_dims)]
        self.labels = labels

    @abstractmethod
    def sample(self, mask: Optional[npt.NDArray[np.bool_]] = None) -> Any:
        """Sample a value from the space."""


@serde
@dataclass
class DiscreteSpace(Space):
    size: int
    """Number of categories"""

    def __init__(self, size: int, labels: Optional[list[str]] = None):
        super().__init__((size,), labels)
        self.size = size
        self.space = np.arange(size)

    def sample(self, mask: Optional[npt.NDArray[np.bool_]] = None) -> int:
        space = self.space
        if mask is not None:
            space = space[mask]
        return int(np.random.choice(space))


@serde
@dataclass
class MultiDiscreteSpace(Space):
    n_dims: int
    spaces: tuple[DiscreteSpace, ...]

    def __init__(self, *spaces: DiscreteSpace, labels: Optional[list[str]] = None):
        if labels is None:
            labels = [f"Discrete space {i}" for i in range(len(spaces))]
        Space.__init__(self, tuple(space.size for space in spaces), labels)
        self.spaces = spaces
        self.n_dims = len(spaces)

    @classmethod
    def from_sizes(cls, *sizes: int):
        return cls(*(DiscreteSpace(size) for size in sizes))

    def sample(self, masks: Optional[npt.NDArray[np.bool_] | list[npt.NDArray[np.bool_]]] = None):
        if masks is None:
            return np.array([space.sample() for space in self.spaces], dtype=np.int32)
        return np.array([space.sample(mask) for mask, space in zip(masks, self.spaces)], dtype=np.int32)


@serde
@dataclass
class ContinuousSpace(Space):
    """A continuous space (box) in R^n."""

    low: npt.NDArray[np.float32]
    """Lower bound of the space for each dimension."""
    high: npt.NDArray[np.float32]
    """Upper bound of the space for each dimension."""

    def __init__(
        self,
        low: list | npt.NDArray[np.float32],
        high: list | npt.NDArray[np.float32],
        labels: Optional[list[str]] = None,
    ):
        if isinstance(low, list):
            low = np.array(low, dtype=np.float32)
        if isinstance(high, list):
            high = np.array(high, dtype=np.float32)
        assert low.shape == high.shape, "Low and high must have the same shape."
        assert np.all(low <= high), "All elements in low must be less than the corresponding elements in high."
        Space.__init__(self, low.shape, labels)
        self.low = low
        self.high = high

    def sample(self, *_):
        return np.random.random(self.shape) * (self.high - self.low) + self.low


@serde
@dataclass
class ActionSpace(Space, Generic[S]):
    n_agents: int
    """Number of agents."""
    action_names: list[str]
    """The meaning of each action."""
    n_actions: int
    individual_action_space: S

    def __init__(self, n_agents: int, individual_action_space: S, action_names: Optional[list] = None):
        Space.__init__(self, (n_agents, *individual_action_space.shape), action_names)
        self.n_agents = n_agents
        self.individual_action_space = individual_action_space
        self.n_actions = math.prod(individual_action_space.shape)
        self.action_names = action_names or [f"Action {i}" for i in range(self.n_actions)]

    def sample(self, mask: np.ndarray | None = None):
        res = []
        for i in range(self.n_agents):
            if mask is not None:
                m = mask[i]
            else:
                m = None
            res.append(self.individual_action_space.sample(m))
        return np.array(res, dtype=np.int64)


class DiscreteActionSpace(ActionSpace[DiscreteSpace]):
    def __init__(self, n_agents: int, n_actions: int, action_names: Optional[list[str]] = None):
        individual_action_space = DiscreteSpace(n_actions, action_names)
        super().__init__(n_agents, individual_action_space, action_names)


class MultiDiscreteActionSpace(ActionSpace[MultiDiscreteSpace]):
    pass


class ContinuousActionSpace(ActionSpace[ContinuousSpace]):
    def __init__(self, n_agents: int, low: np.ndarray | list, high: np.ndarray | list, action_names: list | None = None):
        space = ContinuousSpace(low, high, action_names)
        super().__init__(n_agents, space, action_names)
