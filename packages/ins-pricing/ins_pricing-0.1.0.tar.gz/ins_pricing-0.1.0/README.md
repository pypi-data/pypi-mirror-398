# Ins-Pricing 项目概览

本仓库包含风险建模与优化相关的 Notebook、脚本与可复用训练框架，重点模块为 `ins_pricing/modelling/bayesopt`。

## 目录结构（顶层）

- `Auto Info/`：车辆信息相关的爬取、预处理与词向量实验
- `GLM and LGB/`：GLM/LightGBM 及业务建模实验
- `OpenAI/`：OpenAI 相关 Notebook 原型
- `Python Code/`：可直接运行的脚本工具
- `others/`：临时或杂项 Notebook
- `ins_pricing/`：可复用训练框架与 CLI 工具（含 BayesOpt 子包）
- `user_packages legacy/`：历史版本快照

说明：`ins_pricing/modelling/demo/` 仅在仓库中保留，PyPI 包不包含该目录。

## 快速开始

建议在仓库根目录运行以下命令：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\\.venv\\Scripts\\activate
pip install pandas scikit-learn lightgbm seaborn matplotlib
```

启动 Notebook：

```bash
jupyter lab
```

## BayesOpt 使用入口

- CLI 批量训练：`python ins_pricing/modelling/BayesOpt_entry.py --config-json <path>`
- 增量训练：`python ins_pricing/modelling/BayesOpt_incremental.py --config-json <path>`
- Python API：`from ins_pricing.modelling import BayesOptModel`

## 测试

```bash
pytest -q
```

## 数据与输出

- 建议将共享数据放在 `data/`（如不存在可自行创建）
- 训练输出默认写入 `plot/`、`Results/`、`model/`
- 密钥与大文件请放在仓库外，并使用环境变量或 `.env` 管理
