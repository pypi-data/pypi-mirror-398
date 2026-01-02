# ins_pricing

本目录为可复用的生产级工具与训练框架集合，重点是 BayesOpt 系列组件。

核心内容：
- `bayesopt/`：拆分后的核心子包（数据预处理、训练器、模型、绘图、解释封装等）
- `plotting/`：独立绘图库（lift/roc/importance/geo 等）
- `explain/`：独立解释模块（Permutation/Integrated Gradients/SHAP）
- `BayesOpt.py`：兼容入口，保留旧 import 路径
- `BayesOpt_entry.py`：批量训练 CLI
- `BayesOpt_incremental.py`：增量训练 CLI
- `cli_common.py` / `notebook_utils.py`：CLI 与 Notebook 公共工具
- `demo/config_template.json` / `demo/config_incremental_template.json`：配置模板
- `Explain_entry.py` / `Explain_Run.py`：解释性分析入口（加载已训练模型）
- `demo/config_explain_template.json` / `demo/Explain_Run.ipynb`：解释流程示例

说明：`modelling/demo/` 仅在仓库中保留，PyPI 包不包含该目录。

常见使用方式：
- CLI：`python ins_pricing/modelling/BayesOpt_entry.py --config-json ...`
- Notebook：`from ins_pricing.bayesopt import BayesOptModel`

解释调用（加载 Results/model 中已训练模型，对指定验证集解释）：
- CLI：`python ins_pricing/modelling/Explain_entry.py --config-json ins_pricing/modelling/demo/config_explain_template.json`
- Notebook：打开 `ins_pricing/modelling/demo/Explain_Run.ipynb` 并执行

说明：
- 模型默认从 `output_dir/model` 读取（可通过 `explain.model_dir` 覆盖）
- 验证集可通过 `explain.validation_path` 指定

注意事项：
- 训练输出默认写入 `plot/`、`Results/`、`model/`
- 大数据与密钥请放在仓库外，并通过环境变量或 `.env` 加载
