#
# Toy environments for testing maml-rawr
#
import gym
from gym.spaces import Box
from gym.envs.mujoco import mujoco_env
from gym import utils

import imageio
import numpy as np
from typing import Optional, Tuple, List
from gym.envs.mujoco import HalfCheetahEnv as HalfCheetahEnv_

from src.utils import Experience


class Env(object):
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, dict]:
        raise NotImplementedError()

    def reset(self) -> np.ndarray:
        raise NotImplementedError()

    def n_tasks() -> int:
        raise NotImplementedError()


class PointMass1DEnv(Env):
    targets = np.linspace(-1,1,4)
    def __init__(self, task_idx: Optional[int] = 0, fix_random_task: bool = False):
        self.action_space = Box(
            np.array([-1.]),
            np.array([1.])
        )
        self.observation_space = Box(
            np.array([-1., -1.]),
            np.array([1., 1.])
        )

        self._mass = 10
        self._dt = 0.1
        self._t = 0
        self._x = 0
        self._v = 0

        if task_idx is None and fix_random_task:
            task_idx = np.random.choice(PointMass1DEnv.n_tasks())

        self._task_idx = task_idx
        if task_idx is not None:
            self._task_target = PointMass1DEnv.targets[self._task_idx]
            
        self._this_task_idx = self._task_idx            
        self._max_episode_steps = 50

    @staticmethod
    def n_tasks() -> int:
        return len(PointMass1DEnv.targets)
        
    def render_rollout(self, rollout: List[Experience], path: Optional[str] = None) -> np.ndarray:
        RED, GREEN, BLUE = np.array([1., 0., 0.]), np.array([0., 1., 0.]), np.array([0., 0., 1.])
        resolution = 300
        padding = self._max_episode_steps
        image = np.zeros((self._max_episode_steps, resolution * 2, 3))
        for idx, experience in enumerate(rollout):
            path_column = resolution + int((experience.state[0]) * (resolution - 1))
            image[idx, path_column] = GREEN
            if idx % 2 == 0:
                column = resolution + int(resolution * np.tanh(self._task_target))
                image[idx, column] /= 2
                image[idx, column] += BLUE / 2

        padding_image = np.zeros((padding, resolution * 2, 3))
        image = np.concatenate((padding_image, image, padding_image), 0)

        if path is not None:
            imageio.imwrite(path, (image * 255).astype(np.uint8))
        
        return image

    def _compute_state(self) -> np.ndarray:
        # return np.array([np.tanh(self._x), self._v, self._t/float(self._max_episode_steps)], dtype=np.float32)
        # return np.array([(self._x), self._v, self._t/float(self._max_episode_steps)], dtype=np.float32)
        return np.array([np.tanh(self._x), self._v], dtype=np.float32)

    def reset(self) -> np.ndarray:
        if self._task_idx is None:
            self._this_task_idx = np.random.choice(PointMass1DEnv.n_tasks())
            self._task_target = PointMass1DEnv.targets[self._this_task_idx]

        self._x = np.random.normal() * 0.
        self._v = np.random.normal() * 0.
        self._t = 0

        return self._compute_state()

    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, dict]:
        action = action.clip(self.action_space.low, self.action_space.high)
        assert action.shape == (1,)
        # Move time forward
        self._t += 1

        # Update velocity with action and compute new position
        self._v += action[0] / self._mass
        self._x += self._dt * self._v
        
        done = self._t == self._max_episode_steps

        effort_penalty = -0.01 * np.abs(action[0])
        proximity_reward = -0.1 * np.abs(self._x - self._task_target) ** 2
        reward = proximity_reward + effort_penalty

        return self._compute_state(), reward, done, {'task_idx': self._this_task_idx}


class HalfCheetahEnv(HalfCheetahEnv_):
    def _get_obs(self):
        return np.concatenate([
            self.sim.data.qpos.flat[1:],
            self.sim.data.qvel.flat,
            self.get_body_com("torso").flat,
        ]).astype(np.float32).flatten()

    def viewer_setup(self):
        camera_id = self.model.camera_name2id('track')
        self.viewer.cam.type = 2
        self.viewer.cam.fixedcamid = camera_id
        self.viewer.cam.distance = self.model.stat.extent * 0.35
        # [Don't] Hide the overlay
        # self.viewer._hide_overlay = True

    def render(self, mode='human'):
        if mode == 'rgb_array':
            self._get_viewer().render()
            # window size used for old mujoco-py:
            width, height = 500, 500
            data = self._get_viewer(mode).read_pixels(width, height, depth=False)
            return data
        elif mode == 'human':
            self._get_viewer(mode).render()

class HalfCheetahVelEnv(HalfCheetahEnv):
    """Half-cheetah environment with target velocity, as described in [1]. The 
    code is adapted from
    https://github.com/cbfinn/maml_rl/blob/9c8e2ebd741cb0c7b8bf2d040c4caeeb8e06cc95/rllab/envs/mujoco/half_cheetah_env_rand.py
    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each 
    time step a reward composed of a control cost and a penalty equal to the 
    difference between its current velocity and the target velocity. The tasks 
    are generated by sampling the target velocities from the uniform 
    distribution on [0, 2].
    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic 
        Meta-Learning for Fast Adaptation of Deep Networks", 2017 
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for 
        model-based control", 2012 
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)
    """
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, include_target: bool = False, single_task: bool = False):
        
        self.include_target = include_target
        if tasks is None:
            tasks = [{'velocity': v} for v in np.linspace(0,3,41)[1:]]
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._velocity = self._task['velocity']
        super(HalfCheetahVelEnv, self).__init__()
        self._max_episode_steps = 200
        self.info_dim = 1
    
    def _get_obs(self):
        if self.include_target:
            return np.concatenate([
                self.sim.data.qpos.flat[1:],
                self.sim.data.qvel.flat,
                self.get_body_com("torso").flat,
                np.array([self._velocity]),
                ]).astype(np.float32).flatten()
        else:
            return np.concatenate([
                self.sim.data.qpos.flat[1:],
                self.sim.data.qvel.flat,
                self.get_body_com("torso").flat,
                ]).astype(np.float32).flatten()

    def compute_reward(self, observation: np.ndarray, action: np.ndarray, next_observation: np.ndarray, info: np.ndarray, next_info: np.ndarray):
        batch_shape = observation.shape[:-1]

        observation = observation.reshape((-1, observation.shape[-1]))
        action = action.reshape((-1, action.shape[-1]))
        next_observation = next_observation.reshape((-1, next_observation.shape[-1]))
        info = info.reshape((-1, info.shape[-1]))
        next_info = next_info.reshape((-1, next_info.shape[-1]))

        xpos_idx = 0
        xposbefore = info[:,0]
        xposafter = next_info[:,0]
        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = -1.0 * abs(forward_vel - self._velocity)
        ctrl_cost = 0.5 * 1e-1 * np.square(action).sum(-1)

        rewards = forward_reward - ctrl_cost

        return rewards.reshape(batch_shape)

    def step(self, action):
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]

        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = -1.0 * abs(forward_vel - self._velocity)
        ctrl_cost = 0.5 * 1e-1 * np.sum(np.square(action))

        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward,
                     reward_ctrl=-ctrl_cost, task=self._velocity,
                     info=xposbefore, next_info=xposafter)
        return (observation, reward, done, infos)

    def sample_tasks(self, num_tasks):
        velocities = self.np_random.uniform(0.0, 2.0, size=(num_tasks,))
        tasks = [{'velocity': velocity} for velocity in velocities]
        return tasks

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._velocity = self._task['velocity']
    
    def set_task(self, task):
        self._task = task
        self._velocity = task['velocity']

    def task_description_dim(self, one_hot: bool = True):
        return len(self.tasks) if one_hot else 1

    def task_description(self, task: dict = None, batch: Optional[int] = None, one_hot: bool = True):
        if task is None:
            task = self._task

        idx = self.tasks.index(task)
        one_hot = np.zeros((self.task_description_dim(),), dtype=np.float32)
        one_hot[idx] = 1
        if batch:
            one_hot = one_hot[None,:].repeat(batch, 0)
        return one_hot
        

class HalfCheetahDirEnv(HalfCheetahEnv):
    """Half-cheetah environment with target direction, as described in [1]. The 
    code is adapted from
    https://github.com/cbfinn/maml_rl/blob/9c8e2ebd741cb0c7b8bf2d040c4caeeb8e06cc95/rllab/envs/mujoco/half_cheetah_env_rand_direc.py
    The half-cheetah follows the dynamics from MuJoCo [2], and receives at each 
    time step a reward composed of a control cost and a reward equal to its 
    velocity in the target direction. The tasks are generated by sampling the 
    target directions from a Bernoulli distribution on {-1, 1} with parameter 
    0.5 (-1: backward, +1: forward).
    [1] Chelsea Finn, Pieter Abbeel, Sergey Levine, "Model-Agnostic 
        Meta-Learning for Fast Adaptation of Deep Networks", 2017 
        (https://arxiv.org/abs/1703.03400)
    [2] Emanuel Todorov, Tom Erez, Yuval Tassa, "MuJoCo: A physics engine for 
        model-based control", 2012 
        (https://homes.cs.washington.edu/~todorov/papers/TodorovIROS12.pdf)
    """
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, single_task: bool = False):
        if tasks is None:
            tasks = [{'direction': 1}, {'direction': -1}]
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._direction = self._task['direction']

        super(HalfCheetahDirEnv, self).__init__()
        self._max_episode_steps = 200
        self.info_dim = 1

    def step(self, action):
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]

        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = self._direction * forward_vel
        ctrl_cost = 0.5 * 1e-1 * np.sum(np.square(action))

        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward,
                     reward_ctrl=-ctrl_cost, task=self._task,
                     info=xposbefore, next_info=xposafter)
        return (observation, reward, done, infos)

    def set_task(self, task):
        self._task = task
        self._direction = task['direction']

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._direction = self._task['direction']

    def task_description_dim(self, one_hot: bool = True):
        return len(self.tasks) if one_hot else 1

    def task_description(self, task: dict = None, batch: Optional[int] = None, one_hot: bool = True):
        if task is None:
            task = self._task

        idx = self.tasks.index(task)
        one_hot = np.zeros((self.task_description_dim(),), dtype=np.float32)
        one_hot[idx] = 1
        if batch:
            one_hot = one_hot[None,:].repeat(batch, 0)
        return one_hot


class AntEnv((mujoco_env.MujocoEnv, utils.EzPickle):
    def __init__(self, use_low_gear_ratio=False):
        # self.init_serialization(locals())
        if use_low_gear_ratio:
            xml_path = 'low_gear_ratio_ant.xml'
        else:
            xml_path = 'ant.xml'
        super().__init__(
            xml_path,
            frame_skip=5,
            automatically_set_obs_and_action_space=True,
        )

    def step(self, a):
        torso_xyz_before = self.get_body_com("torso")
        self.do_simulation(a, self.frame_skip)
        torso_xyz_after = self.get_body_com("torso")
        torso_velocity = torso_xyz_after - torso_xyz_before
        forward_reward = torso_velocity[0]/self.dt
        ctrl_cost = 0. # .5 * np.square(a).sum()
        contact_cost = 0.5 * 1e-3 * np.sum(
            np.square(np.clip(self.sim.data.cfrc_ext, -1, 1)))
        survive_reward = 0. # 1.0
        reward = forward_reward - ctrl_cost - contact_cost + survive_reward
        state = self.state_vector()
        notdone = np.isfinite(state).all() \
                  and state[2] >= 0.2 and state[2] <= 1.0
        done = not notdone
        ob = self._get_obs()
        return ob, reward, done, dict(
            reward_forward=forward_reward,
            reward_ctrl=-ctrl_cost,
            reward_contact=-contact_cost,
            reward_survive=survive_reward,
            torso_velocity=torso_velocity,
        )

    def _get_obs(self):
        # this is gym ant obs, should use rllab?
        # if position is needed, override this in subclasses
        return np.concatenate([
            self.sim.data.qpos.flat[2:],
            self.sim.data.qvel.flat,
        ])

    def reset_model(self):
        qpos = self.init_qpos + self.np_random.uniform(size=self.model.nq, low=-.1, high=.1)
        qvel = self.init_qvel + self.np_random.randn(self.model.nv) * .1
        self.set_state(qpos, qvel)
        return self._get_obs()

    def viewer_setup(self):
        self.viewer.cam.distance = self.model.stat.extent * 0.5


