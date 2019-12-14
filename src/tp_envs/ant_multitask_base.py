import numpy as np
from typing import List

from src.tp_envs.ant import AntEnv
# from gym.envs.mujoco.ant import AntEnv

class MultitaskAntEnv(AntEnv):
    def __init__(self, tasks: List[dict], task_idx, **kwargs):
        self.tasks = tasks
        self._task = tasks[task_idx]
        self._goal = self.tasks[task_idx]['goal']
        super(MultitaskAntEnv, self).__init__(**kwargs)

    """
    def step(self, action):
        xposbefore = self.sim.data.qpos[0]
        self.do_simulation(action, self.frame_skip)
        xposafter = self.sim.data.qpos[0]

        forward_vel = (xposafter - xposbefore) / self.dt
        forward_reward = -1.0 * abs(forward_vel - self._goal_vel)
        ctrl_cost = 0.5 * 1e-1 * np.sum(np.square(action))

        observation = self._get_obs()
        reward = forward_reward - ctrl_cost
        done = False
        infos = dict(reward_forward=forward_reward,
                     reward_ctrl=-ctrl_cost, task=self._task)
        return (observation, reward, done, infos)
    """

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._task_idx = idx
        self._goal = self._task['goal']

    def set_task(self, task):
        self._task = task
        self._goal = self._task['goal']
