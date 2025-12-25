# avispy

A Python package for psychology statistics and psychometrics.

**包名**: `avispy` (PyPI 安装名)  
**导入名**: `avis` (使用时 `from avis import ...`)

## 开发状态

这个包正在开发中，用于封装论文研究过程中的心理学统计函数。

## 在 research 项目中使用

由于 `avispy` 是 workspace 成员，可以直接在 `research` 项目中导入：

```python
from avis import xls, fix_parens, make_unique

# 或者导入具体模块（待实现）
# from avis.stats import calculate_effect_size
# from avis.psychometrics import reliability_analysis
```

## 项目结构

```
avispy/
├── src/
│   └── avis/                # 导入时使用 avis
│       ├── __init__.py      # 包入口
│       ├── utils.py         # 工具函数
│       └── py.typed         # 类型提示标记
├── pyproject.toml           # 包配置（name = "avispy"）
└── README.md                # 本文件
```

## 未来功能

- 统计分析函数（效应量、置信区间等）
- 心理测量工具（信度、效度分析）
- SEM 辅助函数
- 贝叶斯网络工具
- 数据预处理函数
