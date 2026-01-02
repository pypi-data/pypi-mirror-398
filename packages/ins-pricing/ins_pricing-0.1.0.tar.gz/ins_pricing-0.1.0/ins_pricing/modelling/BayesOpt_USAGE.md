# BayesOpt 使用说明（框架 + 使用指南）

本文档说明 `ins_pricing/modelling/` 目录下这套训练/调参与堆叠流程的整体框架、配置字段与推荐用法，主要面向：

- 通过 `ins_pricing/modelling/BayesOpt_entry.py` 按 JSON 配置批量训练（可配合 `torchrun`）
- 在 notebook/脚本中直接调用 `ins_pricing.BayesOpt` 或 `ins_pricing.bayesopt` 的 Python API

---

## 1. 你应该运行哪个文件？

`ins_pricing/modelling/` 中与本流程相关的文件：

- `ins_pricing/modelling/bayesopt/`：核心库子包，包含数据预处理、Trainer、Optuna 调参、FT 的 embedding/自监督预训练、绘图与 SHAP 等
- `ins_pricing/modelling/BayesOpt.py`：兼容入口，保留旧有 import 路径，内部 re-export 新子包
- `ins_pricing/modelling/BayesOpt_entry.py`：CLI 批处理入口（按 config 批量读取多个 CSV，训练/调参/保存/绘图；支持 DDP）
- `ins_pricing/modelling/BayesOpt_incremental.py`：增量训练入口（在已有训练结果基础上追加数据并复用参数/模型；用于生产增量场景）
- `ins_pricing/modelling/cli_common.py`：CLI 复用工具（路径解析、模型名生成、绘图选择等公共逻辑）
- `ins_pricing/__init__.py`：将 `ins_pricing/` 变为可导入的包（便于 `from ins_pricing import BayesOptModel` 或 `from ins_pricing import bayesopt`）
- `ins_pricing/modelling/notebook_utils.py`：Notebook 复用工具（统一构造/运行 BayesOpt_entry 与 watchdog 命令）
- `ins_pricing/modelling/Pricing_Run.py`：通用运行入口（Notebook/脚本只需指向 config；由 `runner` 字段决定 entry/incremental/DDP/watchdog）
- `ins_pricing/modelling/demo/config_template.json`：通用 config 模板（推荐复制后修改）
- `ins_pricing/modelling/demo/config_incremental_template.json`：示例增量训练配置（供 `Pricing_incremental.ipynb` 使用）
- `ins_pricing/modelling/demo/config_explain_template.json`：解释流程配置模板
- `user_packages legacy/Try/config_Pricing_FT_Stack.json`：历史“FT 堆叠”配置示例
- Notebook（demo）：`ins_pricing/modelling/demo/Pricing_Run.ipynb`、`ins_pricing/modelling/demo/PricingSingle.ipynb`、`ins_pricing/modelling/demo/Explain_Run.ipynb`
- 已废弃/历史样例：见 `user_packages legacy/Try/*_deprecate.ipynb`

说明：`ins_pricing/modelling/demo/` 仅在仓库中保留，PyPI 包不包含该目录。

---

## 2. 总体框架（从数据到模型的流水线）

### 2.1 一次训练任务的典型流程（BayesOpt_entry）

`BayesOpt_entry.py` 的核心逻辑（每个数据集 `model_name.csv` 都会跑一遍）：

1. 读取 `config.json`，根据 `model_list × model_categories` 拼出数据集名（如 `od_bc`）
2. 从 `data_dir/<model_name>.csv` 读入数据
3. `train_test_split` 切分训练/测试
4. 构造 `BayesOptModel(train_df, test_df, ...)`
5. 根据 FT 角色与模型选择执行：
   - 若 `ft_role != "model"`：先跑 FT（调参/训练/导出 embedding 列），再跑基座模型（XGB/ResNet/GLM 等）
   - 若 `ft_role == "model"`：FT 自己就是一个预测模型，可与其他模型并行调参/训练
6. 保存模型与参数快照，并可选绘图

补充：`BayesOpt_entry.py` / `BayesOpt_incremental.py` 会将配置中的相对路径按“相对于 config.json 所在目录”进行解析（例如 config 在 `ins_pricing/modelling/demo/`，则 `./Data` 表示 `ins_pricing/modelling/demo/Data`）。当前支持的路径字段包括：`data_dir` / `output_dir` / `optuna_storage` / `gnn_graph_cache` / `best_params_files`。

如果你希望 notebook 也“只改 config 文件，不改代码”，推荐使用 `ins_pricing/modelling/demo/Pricing_Run.ipynb`（其内部调用 `ins_pricing/modelling/Pricing_Run.py`）：在 config 中新增 `runner` 字段即可控制运行方式（entry/incremental、DDP、watchdog 等）。

### 2.2 BayesOpt 子包的核心组件分工

以 `ins_pricing/modelling/bayesopt/` 为主：

- `BayesOptConfig`：统一配置（训练轮数、特征列表、FT role、DDP/DP 等）
- `DatasetPreprocessor`：在 `BayesOptModel` 初始化时执行一次预处理：
  - 生成 `w_act`（加权实际值）、可选 `w_binary_act`
  - 类别列转 `category`
  - 生成 `train_oht_data/test_oht_data`（one-hot 版本）
  - 生成 `train_oht_scl_data/test_oht_scl_data`（数值列标准化后的 one-hot 版本）
- `TrainerBase`：训练器基类，封装 `tune()`（Optuna）、`train()`、`save()/load()`、DDP 下的分布式 Optuna 协作
- 具体训练器（`BayesOptModel.trainers`）：
  - `GLMTrainer`：statsmodels GLM
  - `XGBTrainer`：xgboost
  - `ResNetTrainer`：PyTorch MLP/ResNet 风格
  - `FTTrainer`：FT-Transformer（支持 3 种 role）
  - `GNNTrainer`：图神经网络（可作为独立模型 `gnn`，也可用于生成 geo token 注入 FT）
- `OutputManager`：统一输出路径（`plot/`、`Results/`、`model/`）
- `VersionManager`：保存/读取快照（`Results/versions/*_ft_best.json` 等）

### 2.3 BayesOpt 子包结构（按代码顺序理解）

`BayesOpt` 已拆分为子包（`ins_pricing/modelling/bayesopt/`），推荐按下列模块顺序理解：

1) **工具与通用函数**

- `IOUtils / TrainingUtils / PlotUtils`：I/O、通用训练工具（batch size、tweedie loss、free_cuda）、绘图辅助
- `DistributedUtils`：DDP 初始化、rank/world_size 辅助

2) **TorchTrainerMixin（Torch 表格训练的通用部件）**

- DataLoader：`_build_dataloader()` / `_build_val_dataloader()`（会打印 batch/accum/workers）
- Loss：`_compute_losses()` / `_compute_weighted_loss()`（回归默认 tweedie；分类 BCEWithLogits）
- Early stop：`_early_stop_update()`

3) **Sklearn 风格模型类（核心训练对象）**

- `ResNetSklearn`：`fit/predict/set_params`，内部持有 `ResNetSequential`，支持 DP/DDP
- `FTTransformerSklearn`：`fit/predict/fit_unsupervised`，支持 embedding 输出、DP/DDP
- `GraphNeuralNetSklearn`：`fit/predict/set_params`，用于 geo token（可 CPU/GPU 构图，支持邻接矩阵缓存）

4) **配置与预处理/输出管理**

- `BayesOptConfig`：聚合任务、训练、并行与 FT role 等配置字段（由 `BayesOptModel` 构造）
- `OutputManager`：输出根目录下的 `plot/Results/model` 目录管理
- `VersionManager`：写入快照到 `Results/versions/`；并支持读取最新快照（用于复用 best_params）
- `DatasetPreprocessor`：在 `BayesOptModel.__init__` 中运行，生成多种数据视图与派生列

5) **Trainer 系统（Optuna + 训练 + 缓存预测）**

- `TrainerBase`：`tune()`（Optuna）、`save()/load()`、DDP 下分布式 Optuna 协作
- `cross_val_generic()`：通用交叉验证/holdout 评估逻辑（trainer 只需提供 model_builder/metric_fn/fit_predict_fn）
- `_fit_predict_cache()` / `_predict_and_cache()`：训练后把预测写回 `BayesOptModel.train_data/test_data`

6) **总调度器 BayesOptModel**

- `BayesOptModel.optimize_model(model_key, max_evals)`：统一入口，负责：
  - 选择 objective（例如 `ft_role=unsupervised_embedding` 时用自监督 objective）
  - “FT 作为特征”模式：训练后导出 `pred_<prefix>_*` 并自动注入下游特征集合
  - 保存版本快照（便于回溯/复用参数）
- `save_model/load_model`、`plot_*`、`compute_shap_*` 等

### 2.4 关键调用链（从入口到落盘）

以 `BayesOpt_entry.py` 为例，核心调用链是：

1. `BayesOpt_entry.train_from_config()` 读取 CSV，构造 `BayesOptModel(...)`
2. `BayesOptModel.optimize_model(model_key)`
3. `TrainerBase.tune()`（若未开启 `reuse_best_params` 或找不到历史参数）
   - 调用 `Trainer.cross_val()` 或 FT 自监督的 `Trainer.cross_val_unsupervised()`
   - 通过 `cross_val_generic()`：
     - 采样一组 Optuna 参数
     - 构造模型 `model_builder(params)`
     - 训练并在验证集评估 `metric_fn(...)`
4. `Trainer.train()`（用 `best_params` 训练最终模型并缓存预测列）
5. `Trainer.save()` 保存模型文件；`BayesOptModel.optimize_model()` 保存参数快照

**DDP 下的 Optuna（分布式协作）**：

- 只有 rank0 负责 Optuna 采样与驱动 trial；每个 trial 的参数会广播给其他 rank
- 非 rank0 进程不做“采样”，只接收参数并跑同一个 objective（用于多卡训练/同步）

### 2.5 数据视图与缓存列（训练/绘图会用到）

`DatasetPreprocessor` 会在 `train_data/test_data` 上生成一些通用列：

- `w_act`：`target * weight`
-（若提供 `binary_resp_nme`）`w_binary_act`：`binary_target * weight`

训练器完成训练后，`TrainerBase._predict_and_cache()` 会把预测写回：

- **标量预测模型**：生成
  - `pred_<prefix>`（例如 `pred_xgb/pred_resn/pred_ft`）
  - `w_pred_<prefix>`（对应列名是 `w_pred_xgb` 这种形式；实现为 `w_pred_<prefix> = pred_<prefix> * weight`）
- **多维输出（embedding）**：生成
  - `pred_<prefix>_0 .. pred_<prefix>_{k-1}`（例如 `pred_ft_emb_0..`）
  - 这类多维列不会生成 `w_` 前缀加权列（它们不是直接预测值）

这些预测列会被用于 lift/dlift/oneway 等绘图与后续堆叠训练。

### 2.6 Sklearn 风格模型类：细节与调用方法

下面是 `bayesopt` 子包中三个“sklearn 风格”模型类的接口与关键点（它们通常由 Trainer 创建；你也可以手工创建调用）。

#### 2.6.1 ResNetSklearn（`class ResNetSklearn`）

用途：对 one-hot/标准化后的高维表格特征训练一个残差 MLP（回归默认 Softplus 输出，分类输出 logits）。

关键构造参数（常用）：

- `input_dim`：输入维度（通常是 one-hot 后的列数）
- `hidden_dim`、`block_num`：网络宽度与残差块数
- `learning_rate`、`epochs`、`patience`
- `use_data_parallel` / `use_ddp`

关键方法：

- `fit(X_train, y_train, w_train, X_val, y_val, w_val, trial=...)`
- `predict(X_test)`：分类会 sigmoid；回归会 clip 到正数
- `set_params(params: dict)`：训练器会用它把 `best_params` 写回模型

最小手工示例：

```python
from ins_pricing.BayesOpt import ResNetSklearn

# X_train/X_val 建议使用 DatasetPreprocessor 的 one-hot 标准化版本
resn = ResNetSklearn(model_nme="od_bc", input_dim=X_train.shape[1], task_type="regression", epochs=50)
resn.set_params({"hidden_dim": 32, "block_num": 4, "learning_rate": 1e-3})
resn.fit(X_train, y_train, w_train, X_val, y_val, w_val)
y_pred = resn.predict(X_val)
```

#### 2.6.2 FTTransformerSklearn（`class FTTransformerSklearn`）

用途：对数值/类别特征做 Transformer 表征学习；支持三种输出模式：

- 监督预测：`predict()` 返回标量预测
- embedding 输出：`predict(return_embedding=True)` 返回 `(N, d_model)` embedding
- 自监督 masked 重建：`fit_unsupervised()`（用于 `ft_role=unsupervised_embedding`）

关键点（实现细节）：

- 数值列在 `_tensorize_split()` 中会做 `nan_to_num` 并按训练集均值/方差标准化（减少 amp 溢出风险）
- 类别列会在首次构建模型时记录训练集的 `categories`，推理/验证时按同一套 categories 编码；未知/缺失会映射到 “unknown index”（`len(categories)`）
- DDP 训练使用 `DistributedSampler`；自监督重建头在 forward 内部计算，避免 DDP “ready twice” 报错

关键方法：

- `fit(X_train, y_train, w_train, X_val, y_val, w_val, trial=..., geo_train=..., geo_val=...)`
- `predict(X_test, geo_tokens=None, return_embedding=False)`
- `fit_unsupervised(X_train, X_val=None, mask_prob_num=..., mask_prob_cat=..., ...) -> float`

最小手工示例（自监督预训练 + 导出 embedding）：

```python
from ins_pricing.BayesOpt import FTTransformerSklearn

ft = FTTransformerSklearn(
    model_nme="od_bc",
    num_cols=num_cols,
    cat_cols=cat_cols,
    d_model=64,
    n_heads=4,
    n_layers=4,
    dropout=0.1,
    epochs=30,
    use_ddp=False,
)

val_loss = ft.fit_unsupervised(train_df, X_val=test_df, mask_prob_num=0.2, mask_prob_cat=0.2)
emb = ft.predict(test_df, return_embedding=True)   # shape: (N, d_model)
```

#### 2.6.3 GraphNeuralNetSklearn（`class GraphNeuralNetSklearn`）

用途：对指定的 `geo_feature_nmes` 构图并训练一个小型 GNN，用于生成“geo token”注入 FT。

关键点：

- 构图方式：kNN（可近似 pynndescent；若 PyG 可用且满足显存预算可在 GPU 构图）
- 可缓存邻接矩阵：`graph_cache_path`
- 训练方式：整图训练（每 epoch 前向一次），适合维度不高的 geo 特征

关键方法：

- `fit(X_train, y_train, w_train, X_val, y_val, w_val, trial=...)`
- `predict(X)`：回归 clip 正数；分类 sigmoid 概率
- `set_params(params: dict)`：修改结构参数后会重建骨架

> 实际堆叠流程中通常不需要手工调用它：当你在 config 中提供 `geo_feature_nmes` 时，`BayesOptModel` 会在初始化阶段尝试构建并缓存 geo token。

### 2.7 Trainer 与 Sklearn 模型的对应关系（谁在什么时候被调用）

为了把“调参”和“最终训练/落盘”统一起来，`bayesopt` 采用了两层结构：

- **Trainer（调参/调度层）**：负责 Optuna、CV/holdout、选择特征视图、保存/加载、写回预测列
- **Sklearn 风格模型（训练执行层）**：只负责 fit/predict（以及少量辅助方法），不直接处理 Optuna 与输出路径

对应关系概览：

- `GLMTrainer` → statsmodels GLM（非 `*Sklearn` 类；训练器会构造 design matrix 并缓存 `pred_glm/w_pred_glm`）
- `XGBTrainer` → `xgb.XGBRegressor`（启用 `enable_categorical=True`，并根据 `use_gpu` 选择 `gpu_hist/hist`）
- `ResNetTrainer` → `ResNetSklearn`
  - 特征视图：通常使用 `train_oht_scl_data/test_oht_scl_data` 的 `var_nmes`（one-hot + 标准化）
  - 训练后缓存：`pred_resn/w_pred_resn`
- `FTTrainer` → `FTTransformerSklearn`
  - 特征视图：使用原始 `train_data/test_data` 的 `factor_nmes`（包含数值列 + category 列；category 需在 `cate_list` 中声明）
  - `ft_role=model`：训练后缓存 `pred_ft/w_pred_ft`
  - `ft_role=embedding/unsupervised_embedding`：训练后缓存 `pred_<prefix>_0..`，并注入下游 `factor_nmes`
- `GraphNeuralNetSklearn`：当前主要被 `BayesOptModel` 用于 geo token 生成（当配置了 `geo_feature_nmes`）

---

## 3. FT 的三种角色（决定是不是“堆叠”）

FT 的角色由 `ft_role` 控制（来自 config 或 CLI `--ft-role`）：

### 3.1 `ft_role="model"`（FT 作为预测模型）

- 目标：用 `X -> y` 直接训练 FT，并生成 `pred_ft` / `w_pred_ft`
- FT 会参与 lift/dlift/SHAP 等评估

### 3.2 `ft_role="embedding"`（监督学习，但只导出 embedding 给下游）

- 目标：仍用 `X -> y` 监督训练（embedding 质量受监督信号影响）
- 训练后导出 pooling embedding 特征列：`pred_<ft_feature_prefix>_0..`
- 这些列会自动注入到 `factor_nmes`，供下游基座模型训练（堆叠）
- FT 自身不作为独立模型参与 lift/SHAP

### 3.3 `ft_role="unsupervised_embedding"`（masked 自监督预训练 + 导出 embedding）

- 目标：不使用 `y`，仅对输入 `X` 做 masked reconstruction（数值重建 + 类别重建）
- 训练后同样导出 `pred_<ft_feature_prefix>_0..`，并注入下游特征
- 更适合“先学表征，再让基座模型决策”的两阶段方案

---

## 4. Optuna 在优化什么？

### 4.1 监督模型（GLM/XGB/ResNet/FT-as-model）

- `TrainerBase.tune()` 内部会调用各 Trainer 的 `cross_val()`，并最小化验证指标（默认方向 `minimize`）
- 回归任务通常使用 Tweedie deviance / 相关损失；分类任务使用 logloss

### 4.2 FT 自监督（`unsupervised_embedding`）

当 `ft_role="unsupervised_embedding"` 时，`BayesOptModel.optimize_model("ft")` 会调用：

- `FTTrainer.cross_val_unsupervised()`（Optuna objective）
- 目标值：masked reconstruction 的验证集 loss（越小越好）
  - 数值部分：只在被 mask 的位置计算 MSE（乘 `num_loss_weight`）
  - 类别部分：只在被 mask 的位置计算 cross-entropy（乘 `cat_loss_weight`）

备注：
- 当前默认不搜索 `n_heads`，而是由 `d_model` 自动推导并保证可整除（见 `FTTrainer._resolve_adaptive_heads()`）。

---

## 5. 输出目录与文件（约定）

输出根目录来自 `output_dir`（config）或 CLI `--output-dir`，其下会生成：

- `plot/`：各种图（loss 曲线、lift/dlift/oneway 等）
- `Results/`：参数结果、指标、版本快照
  - `Results/<model>_bestparams_<trainer>.csv`：每个 trainer 的最佳参数（tune 后落盘）
  - `Results/versions/<timestamp>_<model_key>_best.json`：快照（含 `best_params` 与 config）
- `model/`：模型文件
  - GLM/XGB：`pkl`
  - PyTorch：`pth`（ResNet 通常保存 state_dict；FT 通常保存整个对象）

---

## 6. 配置文件（JSON）字段说明（常用）

建议从 `ins_pricing/modelling/demo/config_template.json` 复制一份开始改；示例可参考 `ins_pricing/modelling/demo/config_template.json`、`ins_pricing/modelling/demo/config_incremental_template.json`、`user_packages legacy/Try/config_Pricing_FT_Stack.json`。

### 6.1 路径解析规则（非常重要）

- `BayesOpt_entry.py` / `BayesOpt_incremental.py` 会将 config 中的相对路径按“相对于 config.json 所在目录”进行解析。
  - 例如 config 放在 `ins_pricing/modelling/demo/`，则 `data_dir: "./Data"` 表示 `ins_pricing/modelling/demo/Data`。
  - 当前会被解析的字段包括：`data_dir` / `output_dir` / `optuna_storage` / `gnn_graph_cache` / `best_params_files`。
- `optuna_storage` 若形如 URL（包含 `://`），则按 URL 原样传给 Optuna；否则按文件路径解析并转为绝对路径。

**数据与任务**

- `data_dir`（str）：CSV 所在目录（每个数据集一个 `<model_name>.csv`）
- `model_list`（list[str]）/ `model_categories`（list[str]）：用于拼接数据集名（笛卡尔积）
- `target`（str）：目标列名
- `weight`（str）：权重列名
- `feature_list`（list[str]）：特征列名列表（建议显式给出；不填则在 `BayesOptModel` 内推断）
- `categorical_features`（list[str]）：类别列名列表（不填则在 `BayesOptModel` 内推断）
- `binary_resp_nme`（str|null，可选）：二分类目标列名（用于画成交率曲线等）
- `task_type`（str，可选）：`"regression"` / `"classification"`，默认 `"regression"`

**训练与切分**

- `prop_test`（float）：训练/测试切分比例（entry 会先切 train/test；训练器内部还会做 CV/holdout），常用范围 `(0, 0.5]`，默认 `0.25`
- `rand_seed`（int）：随机种子，默认 `13`
- `epochs`（int）：神经网络训练轮数（ResNet/FT/GNN 会用到），默认 `50`
- `use_gpu`（bool，可选）：是否优先使用 GPU（实际仍以 `torch.cuda.is_available()` 为准）
- `resn_weight_decay`（float，可选）：ResNet 的权重衰减系数（L2 正则），默认 `1e-4`
- `final_ensemble`（bool，可选）：是否在最终训练阶段启用 k 折模型平均，默认 `false`
- `final_ensemble_k`（int，可选）：k 折模型平均的折数，默认 `3`
- `final_refit`（bool，可选）：是否在最终训练阶段启用 refit（早停后用全量数据重训），默认 `true`

**FT 堆叠相关**

- `ft_role`（str）：`"model"` / `"embedding"` / `"unsupervised_embedding"`
  - `"model"`：FT 自身作为预测模型输出 `pred_ft`
  - `"embedding"`：FT 仍是监督训练，但只导出 embedding 特征列 `pred_<prefix>_*`，不作为最终模型评估
  - `"unsupervised_embedding"`：FT 用 masked 重建做自监督预训练，再导出 embedding 特征列 `pred_<prefix>_*`
- `ft_feature_prefix`（str）：导出的特征前缀（会生成 `pred_<prefix>_0..`）
- `ft_num_numeric_tokens`（int|null）：FT 数值特征拆分的 token 数；默认等于数值变量数
- `stack_model_keys`（list[str]）：当 `ft_role != "model"` 且希望 FT 后继续训练基座模型时，指定要跑的 trainer，例如 `["xgb","resn"]` 或 `["all"]`

**并行与 DDP**

- `use_resn_ddp` / `use_ft_ddp` / `use_gnn_ddp`（bool）：是否使用 DDP（需要 `torchrun`/`nproc_per_node>1`）
- `use_resn_data_parallel` / `use_ft_data_parallel` / `use_gnn_data_parallel`（bool）：是否允许 DataParallel（多卡单进程兜底）

**复用历史最优参数（跳过 Optuna）**

- `reuse_best_params`（bool）：`true/false`
  - `true`：优先从 `Results/versions/*_<model_key>_best.json` 读取 `best_params`，否则回退读取 `Results/<model>_bestparams_*.csv`
  - 找不到历史参数时会正常执行 Optuna
- `best_params_files`（dict，可选）：显式指定最优参数文件，格式 `{"xgb":"./Results/xxx.csv","ft":"./Results/xxx.json"}`
  - 支持 `.csv/.tsv`（读取第一行）与 `.json`（支持 `{"best_params": {...}}` 或直接 dict）
  - 指定后会直接读取并跳过 Optuna

**Optuna 断点与续跑（推荐配置）**

- `optuna_storage`（str|null）：Optuna storage（推荐 sqlite）
  - 例：`"./Results/optuna/bayesopt.sqlite3"`（会被自动解析为绝对路径）
  - 或：`"sqlite:///E:/path/to/bayesopt.sqlite3"`（URL，原样传入）
- `optuna_study_prefix`（str）：study 名称前缀；建议固定，便于断点续跑

**XGBoost 搜索空间限制（防止某些 trial 极慢）**

- `xgb_max_depth_max`（int）：XGB 最大深度上限（默认 `25`）
- `xgb_n_estimators_max`（int）：XGB 树数量上限（默认 `500`）

**GNN 与 geo token（可选）**

- `gnn_use_approx_knn`（bool）：是否在大样本下优先使用近似 kNN
- `gnn_approx_knn_threshold`（int）：触发近似 kNN 的行数阈值
- `gnn_graph_cache`（str|null）：邻接/图缓存路径（可选）
- `gnn_max_gpu_knn_nodes`（int）：超过该节点数强制 CPU kNN（避免 GPU OOM）
- `gnn_knn_gpu_mem_ratio`（float）：GPU kNN 允许使用的可用显存比例
- `gnn_knn_gpu_mem_overhead`（float）：kNN 临时显存放大倍数估计
- `geo_feature_nmes`（list[str]）：用于生成 geo token 的原始列名（为空则不生成）
- `region_province_col` / `region_city_col`（str|null）：省/市列名（用于 region_effect 特征，可选）
- `region_effect_alpha`（float）：部分池化强度（>=0）

**绘图（可选）**

- `plot_curves`（bool）：是否在任务结束后绘图
- `plot`（dict）：推荐用该结构统一控制绘图
  - `plot.enable`（bool）
  - `plot.n_bins`（int）：分箱数量
  - `plot.oneway`（bool）
  - `plot.lift_models`（list[str]）：要画 lift 的模型 key（如 `["xgb","resn"]`），为空则默认已训练模型
  - `plot.double_lift`（bool）
  - `plot.double_lift_pairs`（list）：支持 `["xgb,resn"]` 或 `[["xgb","resn"]]`

**独立绘图库（推荐）**

`ins_pricing.plotting` 提供与训练过程解耦的绘图工具，可直接使用 DataFrame 或数组进行模型对比与可视化：

- `plotting.curves`：lift/double lift/ROC/PR/KS/校准曲线/成交率 lift
- `plotting.diagnostics`：loss 曲线、单因素 oneway
- `plotting.importance`：因子重要度（支持 SHAP 汇总）
- `plotting.geo`：地理热力图/等高线（含地图底图的热力图/等高线）

示例（独立使用）：

```python
from ins_pricing.plotting import curves, importance, geo

# Lift / Double Lift
curves.plot_lift_curve(pred, w_act, weight, n_bins=10, save_path="plot/lift.png")
curves.plot_double_lift_curve(pred1, pred2, w_act, weight, n_bins=10, save_path="plot/dlift.png")

# ROC / PR（多模型对比）
curves.plot_roc_curves(y_true, {"xgb": pred_xgb, "resn": pred_resn}, save_path="plot/roc.png")
curves.plot_pr_curves(y_true, {"xgb": pred_xgb, "resn": pred_resn}, save_path="plot/pr.png")

# 因子重要度
importance.plot_feature_importance({"x1": 0.32, "x2": 0.18}, save_path="plot/importance.png")

# 地理热力/等高线
geo.plot_geo_heatmap(df, x_col="lon", y_col="lat", value_col="loss", bins=50, save_path="plot/geo_heat.png")
geo.plot_geo_contour(df, x_col="lon", y_col="lat", value_col="loss", levels=12, save_path="plot/geo_contour.png")

# 地图热力图（需安装 contextily）
geo.plot_geo_heatmap_on_map(df, lon_col="lon", lat_col="lat", value_col="loss", bins=80, save_path="plot/map_heat.png")
```

地图类函数默认使用经纬度（EPSG:4326），并基于数据范围自动缩放视图。

训练过程内也会调用该绘图库（`plot_oneway`/`plot_lift`/`plot_dlift`/`plot_conversion_lift`/loss 曲线），便于统一维护与扩展。

**模型解释（独立模块，轻量 + 深度）**

`ins_pricing.explain` 提供与训练解耦的模型解释方法：

- 轻量：Permutation Importance（适合 XGB/ResNet/FT 等模型，全局解释）
- 深度：Integrated Gradients（适合 ResNet/FT，数值特征为主）
- 传统：SHAP（KernelExplainer，适合 GLM/XGB/ResNet/FT，需安装 `shap`）

SHAP 为可选依赖，未安装时会提示安装。

示例：

```python
from ins_pricing.explain import (
    permutation_importance,
    resnet_integrated_gradients,
    ft_integrated_gradients,
    compute_shap_xgb,
)

# permutation importance
imp = permutation_importance(
    predict_fn=model.predict,
    X=X_valid,
    y=y_valid,
    sample_weight=w_valid,
    metric="rmse",
    n_repeats=5,
)

# ResNet integrated gradients
ig_resn = resnet_integrated_gradients(resn_model, X_valid_scl, steps=50)

# FT integrated gradients (categorical 固定，numeric/geo 参与梯度)
ig_ft = ft_integrated_gradients(ft_model, X_valid, geo_tokens=geo_tokens, steps=50)

# SHAP for XGB (BayesOptModel 作为上下文)
shap_xgb = compute_shap_xgb(model, n_background=500, n_samples=200, on_train=False)
```

BayesOptModel 内也提供便捷封装：

```python
model.compute_permutation_importance("resn", on_train=False, metric="rmse")
model.compute_integrated_gradients_resn(on_train=False, steps=50)
model.compute_integrated_gradients_ft(on_train=False, steps=50)
model.compute_shap_xgb(on_train=False)
model.compute_shap_glm(on_train=False)
```

**解释性批量调用（基于 config）**

使用 `Explain_entry.py` 读取 config，加载 `output_dir/model` 中已训练模型，对指定验证集做解释：

```bash
python ins_pricing/modelling/Explain_entry.py --config-json ins_pricing/modelling/demo/config_explain_template.json
```

Notebook 方式可直接运行 `ins_pricing/modelling/demo/Explain_Run.ipynb`。

**环境变量注入（可选）**

- `env`：会通过 `os.environ.setdefault()` 写入（例如限制线程数、调试 CUDA）

### 6.2 Notebook 统一运行：runner 字段（推荐）

所有 `Pricing_*.ipynb` 已精简为薄封装：只调用 `Pricing_Run.run("<config.json>")`，具体运行方式由 config 内 `runner` 字段决定。

Notebook 调用方式（推荐）：

```python
from ins_pricing.Pricing_Run import run
run("modelling/demo/config_template.json")
```

命令行调用方式（可选）：

```bash
python ins_pricing/modelling/Pricing_Run.py --config-json ins_pricing/modelling/demo/config_template.json
```

`runner` 支持三种模式：

- `runner.mode="entry"`：运行 `BayesOpt_entry.py`
  - `runner.model_keys`（list[str]）：`["glm","xgb","resn","ft","gnn"]` 或包含 `"all"`
  - `runner.nproc_per_node`（int）：`1`（单进程）或 `>=2`（torchrun/DDP）
  - `runner.max_evals`（int）：每个模型的 Optuna trial 数（默认 `50`）
  - `runner.plot_curves`（bool）：是否加 `--plot-curves`
  - `runner.ft_role`（str|null）：若非空，则覆盖 config 的 `ft_role`

- `runner.mode="incremental"`：运行 `BayesOpt_incremental.py`
  - `runner.incremental_args`（list[str]）：等价于直接传给增量脚本的 CLI 参数
    - 常用：`--incremental-dir/--incremental-file`、`--merge-keys`、`--timestamp-col`、`--model-keys`、`--max-evals`、`--update-base-data`、`--summary-json` 等

- `runner.mode="explain"`：运行 `Explain_entry.py`
  - `runner.explain_args`（list[str]）：等价于直接传给解释脚本的 CLI 参数

watchdog（两种模式都可用）：

- `runner.use_watchdog`（bool）：是否启用 watchdog
- `runner.idle_seconds`（int）：无输出判定“卡住”的秒数
- `runner.max_restarts`（int）：最多重启次数
- `runner.restart_delay_seconds`（int）：重启间隔秒数

---

## 7. CLI：BayesOpt_entry.py 使用示例

### 7.0 参数速查（BayesOpt_entry.py）

`BayesOpt_entry.py` 的 CLI 参数（常用）如下（`--config-json` 必填，其余可选）：

- `--config-json`（必填，str）：配置文件路径（推荐填 `ins_pricing/modelling/demo/xxx.json` 或绝对路径）
- `--model-keys`（list[str]）：`glm` / `xgb` / `resn` / `ft` / `gnn` / `all`
- `--stack-model-keys`（list[str]）：仅当 `ft_role != model` 时生效；取值同 `--model-keys`
- `--max-evals`（int）：每个数据集每个模型的 Optuna trial 数
- `--plot-curves`（flag）：开启绘图（也可在 config 用 `plot_curves`/`plot.enable` 控制）
- `--output-dir`（str）：覆盖 config 的 `output_dir`
- `--reuse-best-params`（flag）：覆盖 config，尽量复用历史最优参数跳过 Optuna

DDP/DP（覆盖 config）：

- `--use-resn-ddp` / `--use-ft-ddp` / `--use-gnn-ddp`（flag）：强制开启对应 Trainer 的 DDP
- `--use-resn-dp` / `--use-ft-dp` / `--use-gnn-dp`（flag）：开启 DataParallel 兜底

GNN 图构建相关（覆盖 config）：

- `--gnn-no-ann`（flag）：禁用近似 kNN（改用精确搜索）
- `--gnn-ann-threshold`（int）：覆盖 `gnn_approx_knn_threshold`
- `--gnn-graph-cache`（str）：覆盖 `gnn_graph_cache`
- `--gnn-max-gpu-nodes`（int）：覆盖 `gnn_max_gpu_knn_nodes`
- `--gnn-gpu-mem-ratio`（float）：覆盖 `gnn_knn_gpu_mem_ratio`
- `--gnn-gpu-mem-overhead`（float）：覆盖 `gnn_knn_gpu_mem_overhead`

FT 特征模式：

- `--ft-role`（str）：`model` / `embedding` / `unsupervised_embedding`
- `--ft-feature-prefix`（str）：生成特征列的 prefix（如 `ft_emb`）
- `--ft-as-feature`（flag）：兼容别名（仅在 config 未设置非默认 ft_role 时，将 ft_role 置为 `embedding`）

### 7.1 直接训练/调参（单机）

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json ins_pricing/modelling/demo/config_template.json ^
  --model-keys xgb resn ^
  --max-evals 50
```

### 7.2 FT 堆叠：先自监督 FT，再训练基座（单机或 torchrun）

若 config 已经写了 `ft_role=unsupervised_embedding`，CLI 可以不写 `--ft-role`。

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json "user_packages legacy/Try/config_Pricing_FT_Stack.json" ^
  --model-keys xgb resn ^
  --max-evals 50
```

DDP（多卡）示例：

```bash
torchrun --standalone --nproc_per_node=2 ^
  ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json "user_packages legacy/Try/config_Pricing_FT_Stack.json" ^
  --model-keys xgb resn ^
  --use-ft-ddp ^
  --max-evals 50
```

### 7.3 只想复用历史最优参数，不再调参

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json "user_packages legacy/Try/config_Pricing_FT_Stack.json" ^
  --model-keys xgb resn ^
  --reuse-best-params
```

### 7.4 参数速查（BayesOpt_incremental.py）

增量训练脚本 `BayesOpt_incremental.py` 的参数较多，但常用组合通常是：指定增量数据来源 + 合并去重方式 + 需要重训的模型。

常用参数：

- `--config-json`（必填，str）：复用同一份 config（至少需要包含 `data_dir/model_list/model_categories/target/weight/feature_list/categorical_features`）
- `--model-names`（list[str]，可选）：只更新某些数据集（默认跑 `model_list × model_categories`）
- `--model-keys`（list[str]）：`glm` / `xgb` / `resn` / `ft` / `gnn` / `all`
- `--incremental-dir`（Path）或 `--incremental-file`（Path）：增量 CSV 来源（二选一）
- `--incremental-template`（str）：当使用 `--incremental-dir` 时的文件名模板（默认 `{model_name}_incremental.csv`）
- `--merge-keys`（list[str]）：合并后的去重主键列
- `--dedupe-keep`（str）：`first` / `last`
- `--timestamp-col`（str|null）：去重前排序用的时间戳列
- `--timestamp-descending`（flag）：时间戳降序（默认升序）
- `--max-evals`（int）：需要重新调参时的 trial 数
- `--force-retune`（flag）：即使存在历史参数也强制重新调参
- `--skip-retune-missing`（flag）：若缺少历史参数则跳过（默认会补调）
- `--update-base-data`（flag）：训练成功后用合并后的数据覆盖 base CSV
- `--persist-merged-dir`（Path|null）：可选，把合并后的快照另存一份
- `--summary-json`（Path|null）：输出执行摘要
- `--plot-curves`（flag）：绘图
- `--dry-run`（flag）：只做合并与统计，不训练

---

## 8. Python API：最小可运行示例（推荐先跑通）

下面示例演示“先 FT 自监督学 embedding，再训练 XGB”的最小流程（只展示关键调用）：

```python
import pandas as pd
from sklearn.model_selection import train_test_split

import ins_pricing.BayesOpt as ropt

df = pd.read_csv("./Data/od_bc.csv")
train_df, test_df = train_test_split(df, test_size=0.25, random_state=13)

model = ropt.BayesOptModel(
    train_df=train_df,
    test_df=test_df,
    model_nme="od_bc",
    resp_nme="reponse",
    weight_nme="weights",
    factor_nmes=[...],          # 等价于 config 的 feature_list
    cate_list=[...],            # 等价于 config 的 categorical_features
    epochs=50,
    use_ft_ddp=False,
    ft_role="unsupervised_embedding",
    ft_feature_prefix="ft_emb",
    output_dir="./Results",
)

# 1) FT masked 自监督预训练 + 导出 embedding 列 + 注入 factor_nmes
model.optimize_model("ft", max_evals=30)

# 2) 基座模型继续调参/训练（使用已注入的 pred_ft_emb_* 作为新特征）
model.optimize_model("xgb", max_evals=50)

# 3) 保存（也可以只保存某一个）
model.save_model()
```

### 8.x 调参卡住/断点续跑（推荐）
如果某个 trial 卡住很久（例如第 17 次调参跑了几小时），建议先中断本次运行，然后在 `config.json` 增加 Optuna 的持久化存储配置；再次运行会自动从已完成的 trials 继续（并保证总 trial 数仍然等于 `max_evals`）。

同时，XGBoost 某些参数组合会非常慢，可以通过上限字段收窄搜索空间，避免出现单个 trial 极端耗时。

**config.json 示例：**
```json
{
  "optuna_storage": "./Results/optuna/pricing.sqlite3",
  "optuna_study_prefix": "pricing",
  "xgb_max_depth_max": 12,
  "xgb_n_estimators_max": 300
}
```

**只用当前最优参数继续训练（不再调参）**
- 在 `config.json` 加 `"reuse_best_params": true`：会优先读取 `Results/versions/*_xgb_best.json` 或 `Results/<model>_bestparams_xgboost.csv` 等文件直接训练。
- 或者显式指定参数文件 `"best_params_files"`（按 `model_key` 映射），直接从文件读取并跳过 Optuna：

```json
{
  "best_params_files": {
    "xgb": "./Results/od_bc_bestparams_xgboost.csv",
    "ft": "./Results/od_bc_bestparams_fttransformer.csv"
  }
}
```

**自动识别“卡住”并重启继续（Watchdog）**
如果你遇到“某次 trial 卡住几小时没有任何输出”，可以用 `ins_pricing/modelling/watchdog_run.py` 监控输出：超过 `idle_seconds` 没有任何 stdout/stderr 就会自动杀掉 `torchrun` 进程树并重启。配合 `optuna_storage`，重启后会自动续跑剩余 trials。

```bash
python ins_pricing/modelling/watchdog_run.py --idle-seconds 7200 --max-restarts 50 -- ^
  python -m torch.distributed.run --standalone --nproc_per_node=2 ^
  ins_pricing/modelling/BayesOpt_entry.py --config-json config.json --model-keys xgb resn --max-evals 50
```

---

## 9. 各模型使用范例（CLI 与 Python）

下面按“模型/Trainer”给出更细的使用范例。所有示例都基于同一套数据约定：CSV 至少包含 `target/weight/feature_list` 对应列，类别列在 `categorical_features` 中声明。

> 说明：这里的 `model_key` 以 `BayesOpt_entry.py` 的参数为准：`glm` / `xgb` / `resn` / `ft` / `gnn`。

### 9.1 GLM（`model_key="glm"`）

**CLI**

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json ins_pricing/modelling/demo/config_template.json ^
  --model-keys glm ^
  --max-evals 50
```

**Python**

```python
model.optimize_model("glm", max_evals=50)
model.trainers["glm"].save()
```

适用：线性可解释基线；通常速度快，便于 sanity check。

### 9.2 XGBoost（`model_key="xgb"`）

**CLI**

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json ins_pricing/modelling/demo/config_template.json ^
  --model-keys xgb ^
  --max-evals 100
```

**Python**

```python
model.optimize_model("xgb", max_evals=100)
model.trainers["xgb"].save()
```

适用：强基线、对特征工程/堆叠特征友好（包括 FT 导出的 embedding 特征列）。

### 9.3 ResNet（`model_key="resn"`）

ResNetTrainer 使用 PyTorch，内部会使用 one-hot/标准化后的视图进行训练与交叉验证（适合处理类别特征 one-hot 后的大维度输入）。

**CLI（单机）**

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json ins_pricing/modelling/demo/config_template.json ^
  --model-keys resn ^
  --max-evals 50
```

**CLI（DDP，多卡）**

```bash
torchrun --standalone --nproc_per_node=2 ^
  ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json ins_pricing/modelling/demo/config_template.json ^
  --model-keys resn ^
  --use-resn-ddp ^
  --max-evals 50
```

**Python**

```python
model.optimize_model("resn", max_evals=50)
model.trainers["resn"].save()
```

### 9.4 FT-Transformer：作为预测模型（`ft_role="model"`）

FT 会像其他模型一样输出 `pred_ft`，并参与 lift/SHAP（如果你启用绘图/SHAP）。

**CLI**

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json ins_pricing/modelling/demo/config_template.json ^
  --model-keys ft ^
  --ft-role model ^
  --max-evals 50
```

**Python**

```python
model.config.ft_role = "model"
model.optimize_model("ft", max_evals=50)
```

### 9.5 FT-Transformer：监督训练但只导出 embedding（`ft_role="embedding"`）

这时 FT 不作为独立预测模型参与评估，而是把 embedding 写成新特征列（`pred_<prefix>_0..`），并自动注入下游训练特征。

**CLI（先 FT 生成特征，再训练基座）**

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json "user_packages legacy/Try/config_Pricing_FT_Stack.json" ^
  --model-keys xgb resn ^
  --ft-role embedding ^
  --max-evals 50
```

**Python**

```python
model.config.ft_role = "embedding"
model.config.ft_feature_prefix = "ft_emb"
model.optimize_model("ft", max_evals=50)      # 生成 pred_ft_emb_* 并注入 factor_nmes
model.optimize_model("xgb", max_evals=100)    # 用注入后的特征继续调参/训练
```

### 9.6 FT-Transformer：masked 自监督预训练 + embedding（`ft_role="unsupervised_embedding"`）

这是“先表征学习，再基座模型决策”的两阶段堆叠模式。Optuna 目标是 masked reconstruction 的验证集 loss（不是 `tw_power`）。

**CLI（推荐：使用示例配置）**

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json "user_packages legacy/Try/config_Pricing_FT_Stack.json" ^
  --model-keys xgb resn ^
  --max-evals 50
```

**CLI（DDP，多卡）**

```bash
torchrun --standalone --nproc_per_node=2 ^
  ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json "user_packages legacy/Try/config_Pricing_FT_Stack.json" ^
  --model-keys xgb resn ^
  --use-ft-ddp ^
  --max-evals 50
```

**Python**

```python
model.config.ft_role = "unsupervised_embedding"
model.config.ft_feature_prefix = "ft_emb"
model.optimize_model("ft", max_evals=50)      # 自监督预训练并导出 pred_ft_emb_*
model.optimize_model("xgb", max_evals=100)
model.optimize_model("resn", max_evals=50)
```

### 9.7 GNN（`model_key="gnn"`）与 geo token

现在已支持将 GNN 作为独立模型进行 Optuna 调参/训练：会基于 one-hot/标准化后的特征训练，并在 `train_data/test_data` 写入 `pred_gnn` / `w_pred_gnn`。

**CLI**

```bash
python ins_pricing/modelling/BayesOpt_entry.py ^
  --config-json ins_pricing/modelling/demo/config_template.json ^
  --model-keys gnn ^
  --max-evals 50
```

同时，GNN 仍可用于 geo token：当 config 提供 `geo_feature_nmes` 时，会先训练地理 GNN 编码器生成 `geo_token_*`，作为额外 token 注入 FT。

实现方式：geo token 的生成由 `GNNTrainer.prepare_geo_tokens()` 统一负责，生成后会注入 `BayesOptModel.train_geo_tokens/test_geo_tokens`，并在 FT 训练/预测时作为输入。

---

## 9. 常见问题（快速排查）

### 9.1 torchrun 的 OMP_NUM_THREADS warning

这是 torchrun 的常见提示，表示默认把每个进程的线程数设为 1，避免 CPU 过载。可通过 config 的 `env` 覆盖。

### 9.2 Optuna 过程中 loss 显示为 inf

通常意味着训练/验证过程中出现了 NaN/inf（数值溢出、数据异常等），
