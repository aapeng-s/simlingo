#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import argparse
import time
import ujson
import shutil
from pathlib import Path

def get_available_port(start_port=10000, end_port=20000):
    """获取可用端口"""
    import socket
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    raise RuntimeError("无法找到可用端口")

def run_single_evaluation(config):
    """运行单个场景评估"""
    
    # 创建输出目录
    output_dir = Path(config['output_dir'])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    viz_path = output_dir / "viz"
    if viz_path.exists():
        shutil.rmtree(viz_path)
    viz_path.mkdir(parents=True, exist_ok=True)
    
    result_file = output_dir / "result.json"
    log_file = output_dir / "output.log"
    err_file = output_dir / "error.log"
    
    # 获取可用端口
    world_port = get_available_port(10000, 20000)
    tm_port = get_available_port(30000, 40000)
    
    print(f"使用端口: World={world_port}, TM={tm_port}")
    
    # 设置环境变量
    env = os.environ.copy()
    env.update({
        'CARLA_ROOT': config['carla_root'],
        'PYTHONPATH': f"{config['carla_root']}/PythonAPI/carla:{config['carla_root']}/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg:{config['repo_root']}/Bench2Drive/leaderboard:{config['repo_root']}/Bench2Drive/scenario_runner",
        'SCENARIO_RUNNER_ROOT': f"{config['repo_root']}/Bench2Drive/scenario_runner",
        'SAVE_PATH': str(viz_path)
    })
    
    # 构建命令
    cmd = [
        'python', '-u', f"{config['repo_root']}/Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py",
        f"--routes={config['route_file']}",
        "--repetitions=1",
        "--track=SENSORS",
        f"--checkpoint={result_file}",
        f"--timeout={config.get('timeout', 600)}",
        f"--agent={config['agent_file']}",
        f"--agent-config={config['checkpoint']}",
        f"--traffic-manager-seed={config.get('seed', 1)}",
        f"--port={world_port}",
        f"--traffic-manager-port={tm_port}"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print(f"输出目录: {output_dir}")
    print(f"路由文件: {config['route_file']}")
    
    # 运行评估
    start_time = time.time()
    with open(log_file, 'w') as log_f, open(err_file, 'w') as err_f:
        process = subprocess.Popen(cmd, stdout=log_f, stderr=err_f, env=env, cwd=config['repo_root'])
        
        try:
            return_code = process.wait()
            end_time = time.time()
            
            print(f"评估完成，耗时: {end_time - start_time:.2f}秒")
            print(f"返回码: {return_code}")
            
            if return_code == 0:
                print("✅ 评估成功完成")
                if result_file.exists():
                    try:
                        with open(result_file, 'r') as f:
                            result_data = ujson.load(f)
                        print(f"结果文件已生成: {result_file}")
                        if '_checkpoint' in result_data and 'progress' in result_data['_checkpoint']:
                            progress = result_data['_checkpoint']['progress']
                            print(f"进度: {progress}")
                    except Exception as e:
                        print(f"读取结果文件失败: {e}")
            else:
                print("❌ 评估失败")
                print(f"查看错误日志: {err_file}")
                
        except KeyboardInterrupt:
            print("用户中断评估")
            process.terminate()
            process.wait()
            return_code = -1
            
    return return_code

def main():
    # 默认配置 - 根据项目结构调整路径
    default_config = {
        'route_file': './Bench2Drive/leaderboard/data/routes_devtest.xml',  # 更常见的路由文件
        'agent_file': './team_code/agent_simlingo.py',
        'checkpoint': './outputs/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt',
        'output_dir': './single_eval_results',
        'carla_root': os.path.expanduser('~/software/carla0915'),
        'repo_root': os.path.abspath('./'),
        'seed': 1,
        'timeout': 600
    }
    
    # 尝试找到存在的路由文件
    possible_routes = [
        './Bench2Drive/leaderboard/data/routes_devtest.xml',
        './leaderboard/data/routes_devtest.xml', 
        './Bench2Drive/leaderboard/data/bench2drive_split/route_001.xml',
        './leaderboard/data/bench2drive_split/route_001.xml',
        './leaderboard/data/routes_training.xml',
        './Bench2Drive/leaderboard/data/routes_training.xml'
    ]
    
    # 查找第一个存在的路由文件作为默认值
    for route_path in possible_routes:
        if Path(route_path).exists():
            default_config['route_file'] = route_path
            break
    
    parser = argparse.ArgumentParser(description='评估单个CARLA场景')
    parser.add_argument('--route', default=default_config['route_file'], help='路由XML文件路径')
    parser.add_argument('--agent', default=default_config['agent_file'], help='智能体文件路径')
    parser.add_argument('--checkpoint', default=default_config['checkpoint'], help='模型检查点路径')
    parser.add_argument('--output', default=default_config['output_dir'], help='输出目录')
    parser.add_argument('--carla-root', default=default_config['carla_root'], help='CARLA根目录')
    parser.add_argument('--repo-root', default=default_config['repo_root'], help='代码仓库根目录')
    parser.add_argument('--seed', type=int, default=default_config['seed'], help='随机种子')
    parser.add_argument('--timeout', type=int, default=default_config['timeout'], help='超时时间(秒)')
    
    args = parser.parse_args()
    
    # 验证文件存在
    route_file = Path(args.route)
    if not route_file.exists():
        print(f"❌ 路由文件不存在: {route_file}")
        print("可能的路由文件位置:")
        for route_path in possible_routes:
            if Path(route_path).exists():
                print(f"  ✅ {route_path}")
            else:
                print(f"  ❌ {route_path}")
        print(f"请使用 --route 参数指定正确的路由文件路径")
        return 1
        
    agent_file = Path(args.agent)
    if not agent_file.exists():
        print(f"❌ 智能体文件不存在: {agent_file}")
        return 1
        
    checkpoint_file = Path(args.checkpoint)
    if not checkpoint_file.exists():
        print(f"❌ 检查点文件不存在: {checkpoint_file}")
        return 1
    
    config = {
        'route_file': str(route_file.absolute()),
        'agent_file': str(agent_file.absolute()),
        'checkpoint': str(checkpoint_file.absolute()),
        'output_dir': args.output,
        'carla_root': os.path.expanduser(args.carla_root),
        'repo_root': os.path.abspath(args.repo_root),
        'seed': args.seed,
        'timeout': args.timeout
    }
    
    print("=== 单场景评估配置 ===")
    for key, value in config.items():
        print(f"{key}: {value}")
    print("=" * 30)
    
    return run_single_evaluation(config)

if __name__ == "__main__":
    exit(main())
