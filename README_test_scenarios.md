# 场景测试工具使用说明

## 🎯 预训练模型下载
```bash
pip install -U "huggingface_hub[cli]"
export HF_ENDPOINT="https://hf-mirror.com"
hf download RenzKa/simlingo --local-dir ./output
```
### 基本用法

```bash
# 使用默认场景 (bench2drive_00.xml)
python test_single_scenario.py

# 指定特定场景
python test_single_scenario.py --scenario bench2drive_13.xml

```