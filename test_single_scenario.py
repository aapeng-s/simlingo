#!/usr/bin/env python3
"""
测试单个场景的脚本，用于调试段错误问题
"""
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
import subprocess
import sys
import time

def find_conda_path():
    """查找conda路径"""
    possible_paths = [
        os.path.expanduser("~/anaconda3/etc/profile.d/conda.sh"),
        os.path.expanduser("~/miniconda3/etc/profile.d/conda.sh"),
        "/opt/anaconda3/etc/profile.d/conda.sh",
        "/opt/miniconda3/etc/profile.d/conda.sh",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def create_test_script():
    """创建测试脚本"""
    conda_path = find_conda_path()
    
    if conda_path:
        conda_init = f". {conda_path}"
    else:
        conda_init = "# 使用系统conda命令"
    
    # 选择指定的RouteScenario_1711场景进行测试
    route_path = "./leaderboard/data/bench2drive_split"
    target_scenario = "bench2drive_00.xml"  # RouteScenario_1711, Town12, ParkingCutIn
    
    test_route_full_path = os.path.join(route_path, target_scenario)
    if not os.path.exists(test_route_full_path):
        print(f"❌ 目标场景文件不存在: {target_scenario}")
        return None
    
    test_route = target_scenario
    route_id = test_route.split("_")[-1][:-4].zfill(3)
    
    print(f"选择测试场景: {test_route} (RouteScenario_1711, Town12, 停车切入场景)")
    print(f"场景ID: {route_id}")
    
    # 创建输出目录
    base_dir = "./eval_results/Bench2Drive/simlingo/bench2drive/1"
    os.makedirs(os.path.join(base_dir, "run"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "res"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "out"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "err"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "viz", route_id), exist_ok=True)
    
    # 配置文件
    cfg = {
        "agent": "simlingo",
        "checkpoint": "./outputs/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt",
        "benchmark": "bench2drive",
        "carla_root": "~/software/carla0915",
        "repo_root": "./",
        "agent_file": "./team_code/agent_simlingo.py",
    }
    
    # 文件路径
    route = os.path.join(route_path, test_route)
    viz_path = os.path.join(base_dir, "viz", route_id)
    result_file = os.path.join(base_dir, "res", f"{route_id}_res.json")
    log_file = os.path.join(base_dir, "out", f"{route_id}_out.log")
    err_file = os.path.join(base_dir, "err", f"{route_id}_err.log")
    job_file = os.path.join(base_dir, "run", f'eval_{route_id}.sh')
    
    # 创建bash脚本
    with open(job_file, 'w', encoding='utf-8') as f:
        f.write(f'''#!/bin/bash

# 设置退出时的清理函数
cleanup() {{
    echo "正在清理资源..."
    rm -f /tmp/leaderboard_evaluator_display.py
    pkill -f CarlaUE4 || true
    exit 1
}}

# 捕获退出信号
trap cleanup SIGINT SIGTERM EXIT

echo "=== 开始测试场景 {route_id} (RouteScenario_1711) ==="
echo "场景: {test_route} - Town12 停车切入场景"
echo "开始时间: $(date)"
echo "JOB ID $$"

# 直接使用simlingo环境的Python
CONDA_PYTHON="/home/aapeng/anaconda3/envs/simlingo/bin/python"

if [ ! -f "$CONDA_PYTHON" ]; then
    echo "❌ simlingo环境的Python不存在: $CONDA_PYTHON"
    exit 1
fi

echo "使用Python: $CONDA_PYTHON"
echo "Python版本: $($CONDA_PYTHON --version)"

# 切换到项目目录
cd {cfg["repo_root"]}

# 设置CARLA环境变量
export CARLA_ROOT={cfg["carla_root"]}
# 确保项目根目录和team_code目录都在PYTHONPATH中
export PYTHONPATH={cfg["repo_root"]}:{cfg["repo_root"]}/team_code:{cfg["carla_root"]}/PythonAPI/carla:{cfg["carla_root"]}/PythonAPI/carla/dist/carla-0.9.15-py3.7-linux-x86_64.egg:{cfg["repo_root"]}/Bench2Drive/leaderboard:{cfg["repo_root"]}/Bench2Drive/scenario_runner
export SCENARIO_RUNNER_ROOT={cfg["repo_root"]}/Bench2Drive/scenario_runner

export SAVE_PATH={viz_path}

# 调试信息
echo "=== 环境信息 ==="
echo "Python路径: $(which python)"
echo "Python版本: $(python --version)"
echo "CARLA_ROOT: $CARLA_ROOT"
echo "当前目录: $(pwd)"

# 检查关键文件
echo "=== 检查关键文件 ==="
if [ -f "{cfg['agent_file']}" ]; then
    echo "✅ Agent文件存在: {cfg['agent_file']}"
else
    echo "❌ Agent文件不存在: {cfg['agent_file']}"
    exit 1
fi

if [ -f "{cfg['checkpoint']}" ]; then
    echo "✅ 模型文件存在: {cfg['checkpoint']}"
else
    echo "❌ 模型文件不存在: {cfg['checkpoint']}"
    exit 1
fi

if [ -f "{route}" ]; then
    echo "✅ 场景文件存在: {route}"
else
    echo "❌ 场景文件不存在: {route}"
    exit 1
fi

# 测试Python导入
echo "=== 测试Python导入 ==="
python -c "
import sys
print('Python路径:', sys.executable)
print('Python版本:', sys.version)

try:
    import carla
    print('✅ CARLA导入成功')
    try:
        print('CARLA版本:', carla.__version__)
    except AttributeError:
        print('CARLA版本: 0.9.15 (推测)')
except Exception as e:
    print('❌ CARLA导入失败:', e)
    sys.exit(1)

try:
    sys.path.insert(0, './') # 项目根目录优先
    sys.path.append('./team_code') # 添加team_code目录让scenario_logger能被找到
    sys.path.append('./Bench2Drive/leaderboard')
    from leaderboard.leaderboard_evaluator import main
    print('✅ Leaderboard导入成功')
except Exception as e:
    print('❌ Leaderboard导入失败:', e)
    sys.exit(1)

try:
    # 现在team_code目录在sys.path中，scenario_logger应该能被找到
    import team_code.agent_simlingo
    print('✅ Agent导入成功')
except Exception as e:
    print('❌ Agent导入失败:', e)
    sys.exit(1)

try:
    import pygame
    print('✅ Pygame导入成功 - 支持实时可视化')
except ImportError as e:
    print('⚠️ Pygame导入失败 - 将使用文件保存模式')
except Exception as e:
    print('⚠️ Pygame测试出错:', str(e))

try:
    import team_code.pygame_visualizer
    print('✅ Pygame可视化器导入成功')
except Exception as e:
    print('⚠️ Pygame可视化器导入失败:', str(e))

print('✅ 所有导入测试通过')
"

if [ $? -ne 0 ]; then
    echo "❌ Python导入测试失败"
    exit 1
fi

# 创建临时的leaderboard_evaluator.py，移除-RenderOffScreen参数启用图形界面
echo "=== 创建带图形界面的leaderboard_evaluator.py ==="
cp {cfg["repo_root"]}/Bench2Drive/leaderboard/leaderboard/leaderboard_evaluator.py /tmp/leaderboard_evaluator_display.py

# 修改CARLA启动命令，移除-RenderOffScreen
sed -i 's/-RenderOffScreen//g' /tmp/leaderboard_evaluator_display.py

echo "✅ 已创建带图形界面的评估器"
echo "🎮 注意：Agent可视化将实时显示在pygame窗口中，包括："
echo "   - 车辆前视图 (默认原始大小，不缩放)"
echo "   - 预测的路径点(红色、蓝色、绿色)"
echo "   - 语言提示和回答"
echo "   - 按键控制：3=原始大小 1=适应窗口 2=填充 4=自定义缩放 +/-=缩放"

echo "=== 开始运行评估（带CARLA图形界面） ==="
echo "场景: {route}"
echo "端口: 2000"
echo "交通管理器端口: 8000"

# 运行评估（使用修改后的评估器）
python -u /tmp/leaderboard_evaluator_display.py \\
--routes={route} \\
--repetitions=1 \\
--track=SENSORS \\
--checkpoint={result_file} \\
--timeout=600 \\
--agent={cfg["agent_file"]} \\
--agent-config={cfg["checkpoint"]} \\
--traffic-manager-seed=1 \\
--port=2000 \\
--traffic-manager-port=8000

exit_code=$?
echo "评估完成，退出码: $exit_code"
echo "结束时间: $(date)"

if [ $exit_code -eq 0 ]; then
    echo "✅ 场景 {route_id} (RouteScenario_1711 停车切入) 评估成功"
else
    echo "❌ 场景 {route_id} (RouteScenario_1711 停车切入) 评估失败"
fi

# 取消trap，手动清理
trap - SIGINT SIGTERM EXIT

# 清理临时文件和CARLA进程
echo "清理临时文件和CARLA进程..."
rm -f /tmp/leaderboard_evaluator_display.py
pkill -f CarlaUE4 || true

exit $exit_code
''')
    
    # 使脚本可执行
    os.chmod(job_file, 0o755)
    
    return job_file

def run_test():
    """运行测试"""
    print("=== 创建测试脚本 ===")
    job_file = create_test_script()
    
    if not job_file:
        return False
    
    print(f"测试脚本已创建: {job_file}")
    
    print("\n=== 运行测试 ===")
    print("注意：如果出现段错误，请检查上面的调试信息")
    print("按 Ctrl+C 可以停止测试")
    
    try:
        # 直接运行脚本（不是后台运行）
        result = subprocess.run(f'bash {job_file}', shell=True)
        
        if result.returncode == 0:
            print("✅ 测试成功完成")
            return True
        else:
            print(f"❌ 测试失败，退出码: {result.returncode}")
            return False
            
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return False
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False

def main():
    print("=== 单场景测试脚本 ===")
    print("测试场景: RouteScenario_1711 (bench2drive_00.xml)")
    print("场景描述: Town12 - 停车切入场景 (ParkingCutIn)")
    print("特性: CARLA图形界面 + Pygame实时可视化 (默认原始大小不缩放)")
    print("控制: 按3=原始大小 1=适应窗口 2=填充 4=自定义 +/-=缩放")
    print()
    
    # 检查必要文件
    if not os.path.exists("./leaderboard/data/bench2drive_split/bench2drive_00.xml"):
        print("❌ 目标场景文件不存在: bench2drive_00.xml")
        return
    
    if not os.path.exists("./team_code/agent_simlingo.py"):
        print("❌ Agent文件不存在")
        return
    
    if not os.path.exists("./outputs/simlingo/checkpoints/epoch=013.ckpt/pytorch_model.pt"):
        print("❌ 模型文件不存在")
        return
    
    print("✅ 必要文件检查通过")
    print()
    
    # 运行测试
    success = run_test()
    
    if success:
        print("\n🎉 测试成功！您可以继续运行完整的评估脚本")
    else:
        print("\n�� 测试失败，请检查上面的错误信息")
        print("常见解决方案：")
        print("1. 检查CARLA是否正确安装")
        print("2. 检查Python环境和依赖库")
        print("3. 检查GPU内存是否足够")
        print("4. 尝试在CPU模式下运行")

if __name__ == "__main__":
    main()
