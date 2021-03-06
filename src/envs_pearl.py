import numpy as np
from typing import Optional, Tuple, List
from oyster.rlkit.envs.half_cheetah_vel import HalfCheetahVelEnv as HalfCheetahVelEnv_
from oyster.rlkit.envs.half_cheetah_dir import HalfCheetahDirEnv as HalfCheetahDirEnv_
from oyster.rlkit.envs.ant_dir import AntDirEnv as AntDirEnv_
from oyster.rlkit.envs.ant_goal import AntGoalEnv as AntGoalEnv_
from oyster.rlkit.envs.humanoid_dir import HumanoidDirEnv as HumanoidDirEnv_
from oyster.rlkit.envs.walker_rand_params_wrapper import WalkerRandParamsWrappedEnv as WalkerRandParamsWrappedEnv_


class HalfCheetahDirEnv(HalfCheetahDirEnv_):
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, single_task: bool = False):
        super(HalfCheetahDirEnv, self).__init__()
        if tasks is None:
            tasks = [{'direction': 1}, {'direction': -1}]
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._goal_dir = self._task['direction']
        self._goal = self._goal_dir
        self._max_episode_steps = 200
        self.info_dim = 1
    
    def step(self, action):
        obs, rew, done, info = super().step(action)
        info['info'] = self._goal_dir
        return (obs, rew, done, info)

    def set_task(self, task):
        self._task = task
        self._goal_dir = self._task['direction']
        self._goal = self._goal_dir
        self.reset()

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._goal_dir = self._task['direction']
        self._goal = self._goal_dir
        self.reset()
        
class HalfCheetahVelEnv(HalfCheetahVelEnv_):
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, single_task: bool = False):
        super(HalfCheetahVelEnv, self).__init__()        
        if tasks is None:
            #tasks = [{'velocity': v} for v in np.linspace(0,3,41)[1:]]
            tasks = self.sample_tasks(130)
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._goal_vel = self._task['velocity']
        self._goal = self._goal_vel
        self._max_episode_steps = 200
        self.info_dim = 1
        
    def step(self, action):
        obs, rew, done, info = super().step(action)
        info['info'] = self._goal_vel
        return (obs, rew, done, info)
    
    def set_task(self, task):
        self._task = task
        self._goal_vel = self._task['velocity']
        self._goal = self._goal_vel
        self.reset()

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._goal_vel = self._task['velocity']
        self._goal = self._goal_vel
        self.reset()

class AntDirEnv(AntDirEnv_):
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, single_task: bool = False):
        super(AntDirEnv, self).__init__(forward_backward=True)
        if tasks is None:
            tasks = self.sample_tasks(2) #Only backward-forward tasks
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._goal = self._task['goal']
        self._max_episode_steps = 200
        self.info_dim = 1
        
    def step(self, action):
        obs, rew, done, info = super().step(action)
        info['info'] = self._goal
        return (obs, rew, done, info)
    
    def set_task(self, task):
        self._task = task
        self._goal = task['goal']
        self.reset()

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._goal = self._task['goal']
        self.reset()
        
class AntGoalEnv(AntGoalEnv_):
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, single_task: bool = False):
        super(AntGoalEnv, self).__init__()
        if tasks is None:
            tasks = self.sample_tasks(130) #Only backward-forward tasks
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._goal = self._task['goal']
        self._max_episode_steps = 200
        self.info_dim = 2

    def step(self, action):
        obs, rew, done, info = super().step(action)
        info['info'] = self._goal
        return (obs, rew, done, info)
    
    def set_task(self, task):
        self._task = task
        self._goal = task['goal']
        self.reset()

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._goal = self._task['goal']        
        self.reset()
        
class HumanoidDirEnv(HumanoidDirEnv_):
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, single_task: bool = False):
        super(HumanoidDirEnv, self).__init__()
        if tasks is None:
            tasks = self.sample_tasks(130) #Only backward-forward tasks
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._goal = self._task['goal']
        self._max_episode_steps = 200
        self.info_dim = 1
        
    def step(self, action):
        obs, rew, done, info = super().step(action)
        info['info'] = self._goal
        return (obs, rew, done, info)
    
    def set_task(self, task):
        self._task = task
        self._goal = task['goal']
        self.reset()

    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._goal = self._task['goal']    
        self.reset()
    
class WalkerRandParamsWrappedEnv(WalkerRandParamsWrappedEnv_):
    def __init__(self, tasks: List[dict] = None, task_idx: int = 0, single_task: bool = False):
        super(WalkerRandParamsWrappedEnv, self).__init__()
        if tasks is None:
            tasks = self.sample_tasks(50) #Only backward-forward tasks
        self.tasks = tasks
        self._task = tasks[task_idx]
        if single_task:
            self.tasks = self.tasks[task_idx:task_idx+1]
        self._max_episode_steps = 200
        
    def step(self, action):
        obs, rew, done, info = super().step(action)
        info['info'] = self._goal
        return (obs, rew, done, info)
    
    def set_task_idx(self, idx):
        self._task = self.tasks[idx]
        self._goal = idx
        self.set_task(self._task)
        self.reset()
   
     
