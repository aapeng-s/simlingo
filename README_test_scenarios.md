# 场景测试工具使用说明

## 🎯 单场景测试

### 基本用法

```bash
# 使用默认场景 (bench2drive_00.xml)
python test_single_scenario.py

# 指定特定场景
python test_single_scenario.py --scenario bench2drive_05.xml

# 查看所有可用场景
python test_single_scenario.py --list-scenarios

# 查看帮助
python test_single_scenario.py --help
```

### 参数说明

- `--scenario` : 指定要测试的场景文件名 (默认: bench2drive_00.xml)
- `--list-scenarios` : 列出所有可用的场景文件

## 🎯 多场景测试

```bash
# 测试预选的4个场景
python test_multiple_scenarios.py
```

## 📋 场景列表示例

当运行 `python test_single_scenario.py --list-scenarios` 时，你会看到类似输出：

```
📋 可用的场景文件:
   1. bench2drive_00.xml    (4.5KB)
   2. bench2drive_01.xml    (4.6KB)
   3. bench2drive_02.xml    (4.2KB)
   ...
  119. bench2drive_118.xml  (2.1KB)

总共 119 个场景

使用方法: python test_single_scenario.py --scenario bench2drive_XX.xml
```

## 🚀 快速测试推荐

### 短时间验证 (选择小文件快速场景)
```bash
python test_single_scenario.py --scenario bench2drive_59.xml
python test_single_scenario.py --scenario bench2drive_97.xml
```

### 中等测试
```bash
python test_single_scenario.py --scenario bench2drive_10.xml
python test_single_scenario.py --scenario bench2drive_20.xml
```

### 复杂场景测试
```bash
python test_single_scenario.py --scenario bench2drive_00.xml
python test_single_scenario.py --scenario bench2drive_63.xml
```

## 🔧 提示

1. **查看场景信息**: 文件大小通常反映场景复杂度，小文件(1-3KB)是短场景，大文件(4-5KB)是复杂场景
2. **快速调试**: 优先选择小场景进行初步测试
3. **GPU内存**: 复杂场景需要更多GPU内存
4. **帧率优化**: 使用提升的60fps配置，评估速度会更快

## 💡 常见用法

```bash
# 验证配置是否正确 (使用最短场景)
python test_single_scenario.py --scenario bench2drive_59.xml

# 测试特定复杂场景
python test_single_scenario.py --scenario bench2drive_00.xml

# 快速浏览所有场景选项
python test_single_scenario.py --list-scenarios | head -20
``` 