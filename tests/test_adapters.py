import rlenv
from pettingzoo.sisl import pursuit_v4, waterworld_v4
from rlenv.adapters import SMAC, PymarlAdapter
from rlenv import MockEnv


def test_gym_adapter():
    # Discrete action space
    env = rlenv.make("CartPole-v1")
    env.reset()
    assert env.n_actions == 2
    assert env.n_agents == 1
    assert env.reward_size == 1

    # Continuous action space
    env = rlenv.make("Pendulum-v1")
    env.reset()


def test_pettingzoo_adapter_discrete_action():
    # https://pettingzoo.farama.org/environments/sisl/pursuit/#pursuit
    env = rlenv.make(pursuit_v4.parallel_env())
    env.reset()
    _, r, *_ = env.step(env.action_space.sample())
    assert len(r) == 1
    assert env.n_agents == 8
    assert env.n_actions == 5
    assert isinstance(env.action_space, rlenv.DiscreteActionSpace)


def test_pettingzoo_adapter_continuous_action():
    # https://pettingzoo.farama.org/environments/sisl/waterworld/
    env = rlenv.make(waterworld_v4.parallel_env())
    env.reset()
    env.step(env.action_space.sample())
    assert env.n_actions == 2
    assert env.n_agents == 2
    assert isinstance(env.action_space, rlenv.ContinuousActionSpace)


# Only perform the tests if SMAC is installed.
if SMAC is not None:

    def test_smac_adapter():
        from rlenv.models import DiscreteActionSpace

        env = SMAC("3m")
        env.reset()
        assert env.n_agents == 3
        assert isinstance(env.action_space, DiscreteActionSpace)

    def test_smac_render():
        env = SMAC("3m")
        env.reset()
        env.render("human")


def test_pymarl():
    LIMIT = 20
    N_AGENTS = 2
    env = PymarlAdapter(MockEnv(N_AGENTS), LIMIT)

    info = env.get_env_info()
    assert info["n_agents"] == N_AGENTS
    assert info["n_actions"] == MockEnv.N_ACTIONS
    assert env.get_total_actions() == MockEnv.N_ACTIONS
    assert info["state_shape"] == MockEnv.UNIT_STATE_SIZE * N_AGENTS
    assert env.get_state_size() == MockEnv.UNIT_STATE_SIZE * N_AGENTS
    assert info["obs_shape"] == MockEnv.OBS_SIZE
    assert env.get_obs_size() == MockEnv.OBS_SIZE
    assert env.episode_limit == LIMIT

    try:
        env.get_obs()
        assert False, "Should raise ValueError because the environment has not yet been reset"
    except ValueError:
        pass

    env.reset()
    obs = env.get_obs()
    assert obs.shape == (N_AGENTS, MockEnv.OBS_SIZE)
    state = env.get_state()
    assert len(state.shape) == 1 and state.shape[0] == env.get_state_size()

    for _ in range(LIMIT - 1):
        reward, done, _ = env.step([0] * N_AGENTS)
        assert reward == MockEnv.REWARD_STEP
        assert not done
    reward, done, _ = env.step([0] * N_AGENTS)
    assert reward == MockEnv.REWARD_STEP
    assert done
