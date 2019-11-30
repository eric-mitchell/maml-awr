import argparse
import gym
import numpy as np
from multiprocessing import Process
import random
import torch

from src.envs import PointMass1DEnv, HalfCheetahDirEnv, HalfCheetahVelEnv
from src.maml_rawr import MAMLRAWR


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--random', action='store_true')
    parser.add_argument('--explore', action='store_true')
    parser.add_argument('--cvae', action='store_true')
    parser.add_argument('--latent_dim', type=int, default=32)
    parser.add_argument('--n_adaptations', type=int, default=1)
    parser.add_argument('--pre_adapted', action='store_true')
    parser.add_argument('--train_steps', type=int, default=100000)
    parser.add_argument('--batch_size', type=int, default=256)
    parser.add_argument('--inner_batch_size', type=int, default=256)
    parser.add_argument('--inner_policy_lr', type=float, default=0.015)
    parser.add_argument('--inner_value_lr', type=float, default=0.1)
    parser.add_argument('--outer_policy_lr', type=float, default=1e-4)
    parser.add_argument('--outer_value_lr', type=float, default=1e-4)
    parser.add_argument('--exploration_lr', type=float, default=1e-4)
    parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--vis_interval', type=int, default=200)
    parser.add_argument('--log_dir', type=str, default='log')
    parser.add_argument('--task_idx', type=int, default=None)
    parser.add_argument('--instances', type=int, default=1)
    parser.add_argument('--name', type=str, default=None)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--env', type=str, default='point_mass')
    parser.add_argument('--gym_env', type=str, default=None)
    parser.add_argument('--gradient_steps_per_iteration', type=int, default=10)
    parser.add_argument('--replay_buffer_size', type=int, default=1000)
    parser.add_argument('--discount_factor', type=float, default=0.99)
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--vf_archive', type=str, default=None)
    parser.add_argument('--ap_archive', type=str, default=None)
    parser.add_argument('--ep_archive', type=str, default=None)
    parser.add_argument('--initial_rollouts', type=int, default=40)
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--offline_outer', action='store_true')
    parser.add_argument('--offline_inner', action='store_true')
    parser.add_argument('--grad_clip', type=float, default=None)
    parser.add_argument('--exp_advantage_clip', type=float, default=10.0)
    parser.add_argument('--maml_steps', type=int, default=1)
    parser.add_argument('--adaptation_temp', type=float, default=0.05)
    parser.add_argument('--exploration_temp', type=float, default=0.2)
    parser.add_argument('--bias_linear', action='store_true')
    parser.add_argument('--advantage_head_coef', type=float, default=None)
    parser.add_argument('--eval', action='store_true')
    parser.add_argument('--target_reward', type=float, default=None)
    parser.add_argument('--save_buffers', action='store_true')
    parser.add_argument('--ratio_clip', type=float, default=0.5)
    parser.add_argument('--buffer_paths', type=str, nargs='+', default=None)
    parser.add_argument('--load_inner_buffer', action='store_true')
    parser.add_argument('--load_outer_buffer', action='store_true')
    return parser.parse_args()


def run(args: argparse.Namespace, instance_idx: int = 0):
    if args.explore:
        assert args.n_adaptations > 1, "Cannot explore without n_adaptation > 1"
    if args.gym_env is None:
        if args.task_idx is None:
            if args.env == 'point_mass':
                envs = [PointMass1DEnv(0), PointMass1DEnv(-1)]
            elif args.env == 'cheetah_dir':
                envs = [HalfCheetahDirEnv(0), HalfCheetahDirEnv(1)]
            elif args.env == 'cheetah_vel':
                envs = [HalfCheetahVelEnv(i) for i in range(4)]
        else:
            if args.env == 'point_mass':
                envs = [PointMass1DEnv(args.task_idx)]
            elif args.env == 'cheetah_dir':
                envs = [HalfCheetahDirEnv(args.task_idx)]
            elif args.env == 'cheetah_vel':
                envs = [HalfCheetahVelEnv(args.task_idx)]
    else:
        envs = [gym.make(args.gym_env)]

    if args.name is None:
        args.name = 'throwaway_test_run'
    if instance_idx == 0:
        name = args.name
    else:
        name = f'{args.name}_{instance_idx}'

    if args.gym_env is None and args.env == 'point_mass':
        network_shape = [32, 32]
    else:
        network_shape = [64, 64, 32, 32]

    seed = args.seed if args.seed is not None else instance_idx
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)

    maml_rawr = MAMLRAWR(args, envs, args.log_dir, name, network_shape, network_shape, batch_size=args.batch_size, training_iterations=args.train_steps,
                         device=args.device, visualization_interval=args.vis_interval, silent=args.instances > 1,
                         gradient_steps_per_iteration=args.gradient_steps_per_iteration,
                         replay_buffer_length=args.replay_buffer_size, discount_factor=args.discount_factor,
                         initial_trajectories=args.initial_rollouts, grad_clip=args.grad_clip,
                         inner_batch_size=args.inner_batch_size, maml_steps=args.maml_steps, bias_linear=args.bias_linear)

    maml_rawr.train()


if __name__ == '__main__':
    args = get_args()
    if args.instances == 1:
        if args.profile:
            import cProfile
            cProfile.runctx('run(args)', sort='cumtime', locals=locals(), globals=globals())
        else:
            run(args)
    else:
        for instance_idx in range(args.instances):
            subprocess = Process(target=run, args=(args, instance_idx))
            subprocess.start()
