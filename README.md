# 房价预测系统

基于 Kaggle 开源数据集开发的交互式房价预测系统，使用 Flask + sklearn / PyTorch 实现完整的数据科学生命周期：上传 → 清洗 → 训练 → 预测 → 可视化 → 导出。

## 功能

| 功能 | 说明 |
|------|------|
| 📤 数据上传 | 支持 CSV 和 XLSX 格式，自动去重 |
| 🔧 生成测试数据 | 三种模式：线性回归 / 多项式 / 正态分布，可调噪声和样本数 |
| 🧹 数据清洗 | 缺失值填充（中位数/众数）、IQR 异常值处理、StandardScaler 标准化 |
| 🏋️ 模型训练 | sklearn LinearRegression 或 PyTorch 全连接神经网络，自动划分训练/测试集 |
| 🔮 房价预测 | 选择模型 → 查看指标 → 分类特征下拉选择 → 输入数值特征 → 获取预测 |
| 🎲 随机抽查 | 从清洗数据中随机抽取一行，对比真值与预测值 |
| 📈 预测测试 | 生成随机测试点，绘制原始数据散点 + 模型预测曲线 |
| 📊 数据可视化 | 直方图、散点图、相关性热力图（服务端渲染） |
| 📦 数据导出 | 下载原始/清洗数据集、模型文件、特征 JSON、预处理器，支持 zip 打包 |

## 技术栈

- **后端**: Flask (Jinja2 模板)
- **机器学习**: scikit-learn (LinearRegression), PyTorch (全连接 NN)
- **数据处理**: pandas, numpy
- **可视化**: matplotlib
- **数据库**: SQLite (内建 sqlite3)
- **包管理**: uv

## 快速开始

```bash
# 安装依赖
uv sync

# 启动开发服务器
flask run
# → http://127.0.0.1:5000
```

## 路由总览

| 路由 | 功能 |
|------|------|
| `/` | 首页导航 |
| `/upload` | 数据上传 |
| `/random-gen` | 生成合成测试数据 |
| `/clean` | 数据清洗 |
| `/train` | 模型训练 |
| `/predict` | 房价预测 + 随机抽查 |
| `/predict-test` | 预测测试（散点 + 曲线图） |
| `/visualize` | 数据可视化 |
| `/export` | 数据与模型导出 |

## 使用流程

### 1. 数据上传
访问 `/upload`，选择 CSV 或 XLSX 文件上传。文件保存到 `data/datasets/raw/`，不允许重名。

### 2. 生成测试数据（可选）
访问 `/random-gen`，选择生成模式：
- **线性** — y = 3.5x₁ + 2.0x₂ − 1.2x₃ + 0.5x₄ + noise，全数值特征
- **多项式** — y = 0.01x₁² + 0.5x₂ + 10 + noise，含分类特征和冗余特征
- **正态分布** — y = 2.0x₁ + 1.5x₂ − 0.8x₃ + noise，特征从正态分布采样

可配置样本数（100-10000）和噪声水平（0-1）。

### 3. 数据清洗
访问 `/clean`，选择原始数据集，勾选清洗操作（缺失值填充、异常值处理、标准化），执行后保存到 `data/datasets/cleaned/`。

### 4. 模型训练
访问 `/train`，选择已清洗数据集和算法（sklearn / pytorch），设置测试集比例。训练完成后显示 MSE、RMSE、R² 等指标，模型保存到 `data/models/`。

### 5. 房价预测
访问 `/predict`，选择已训练模型 → 查看性能指标 → 分类特征通过下拉框选择（选项来自训练数据） → 输入数值特征 → 获取预测价格。点击「随机抽查」可从数据集中随机抽取一行对比真值与预测值。

### 6. 预测测试
访问 `/predict-test`，选择模型和数值特征 → 生成图表：蓝色散点为原始训练数据，橙色曲线为模型预测线（其他特征固定为均值/众数）。

### 7. 数据可视化
访问 `/visualize`，选择数据集和图表类型（直方图/散点图/热力图），生成服务端渲染图表。

### 8. 数据导出
访问 `/export`，按类别展示所有可下载项：
- 原始数据集 — 下载 CSV/XLSX
- 已清洗数据集 — 下载 CSV/XLSX
- 已训练模型 — 下载模型文件 / 特征 JSON / 预处理器 / zip 打包

## 项目结构

```
py-exp/
├── src/
│   ├── app.py                      # Flask 应用入口
│   ├── api/                        # 路由层（Flask Blueprint）
│   │   ├── upload.py               #   数据上传
│   │   ├── random_gen.py           #   合成测试数据生成
│   │   ├── clean.py                #   数据清洗
│   │   ├── train.py                #   模型训练
│   │   ├── analysis.py             #   房价预测 + 随机抽查
│   │   ├── predict_test.py         #   预测测试（曲线图）
│   │   ├── visualize.py            #   数据可视化
│   │   └── export.py               #   数据与模型导出
│   ├── services/                   # 业务逻辑层
│   │   ├── dataset_service.py      #   数据集存取
│   │   ├── random_gen_service.py   #   合成数据生成
│   │   ├── clean_service.py        #   清洗流水线
│   │   ├── train_service.py        #   训练（sklearn + pytorch）
│   │   ├── predict_service.py      #   预测
│   │   ├── predict_test_service.py #   预测测试 + 随机抽查
│   │   └── visualize_service.py    #   图表生成
│   ├── dao/                        # 数据访问层
│   │   ├── __init__.py             #   DB 连接、路径常量
│   │   ├── dataset_dao.py          #   datasets 表 CRUD
│   │   └── model_dao.py            #   models 表 CRUD
│   └── templates/                  # Jinja2 模板
│       ├── base.html               #   基础布局
│       ├── index.html              #   首页
│       ├── upload.html             #   数据上传
│       ├── random_gen.html         #   测试数据生成
│       ├── clean.html              #   数据清洗
│       ├── train.html              #   模型训练
│       ├── analysis.html           #   房价预测 + 抽查
│       ├── predict_test.html       #   预测测试
│       ├── visualize.html          #   数据可视化
│       ├── export.html             #   数据导出
│       └── macros/                 #   可复用 Jinja2 宏
├── kaggle/
│   └── house_prices.csv/           # Kaggle 房价数据集（187K 行）
├── data/                           # 运行时数据（自动创建）
│   ├── datasets/raw/               #   原始上传文件
│   ├── datasets/cleaned/           #   清洗后文件
│   ├── models/                     #   训练好的模型 + 特征信息
│   └── database/app.db             #   SQLite 数据库
├── pyproject.toml
└── instruction.md                  # 详细需求文档
```

## 数据库

SQLite 数据库自动创建于 `data/database/app.db`，包含两张表：

**datasets** — `id`, `filename`, `metadata`(JSON: file_type, file_path, is_cleaned, clean_type, columns, row_count 等)

**models** — `id`, `model_name`, `metadata`(JSON: model_type, model_path, train_data_id, mse, rmse, r2, feature_info_path 等)

## 数据集

[Kaggle House Prices Dataset](https://www.kaggle.com/datasets/juhibhojani/house-price)

- 187,531 行，21 列
- 目标变量：`Price (in rupees)`
- 混合数值和分类特征

## 依赖

```
Flask, pandas, numpy, scikit-learn, matplotlib, python-dotenv
```

PyTorch 为可选依赖（选择 pytorch 训练时提示安装：`uv add torch && uv sync`）。
