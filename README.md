# 房价预测系统

基于 Kaggle 开源数据集开发的交互式房价预测系统，使用 Flask + sklearn / PyTorch 实现完整的数据科学生命周期：上传 → 清洗 → 训练 → 预测 → 可视化。

## 功能

| 功能 | 说明 |
|------|------|
| 📤 数据上传 | 支持 CSV 和 XLSX 格式，自动去重 |
| 🔧 生成测试数据 | 一键生成带噪声的线性/多项式合成数据集 |
| 🧹 数据清洗 | 缺失值填充（中位数/众数）、IQR 异常值处理、StandardScaler 标准化 |
| 🏋️ 模型训练 | sklearn LinearRegression 或 PyTorch 全连接神经网络，自动划分训练/测试集 |
| 🔮 房价预测 | 选择模型 → 查看指标 → 分类特征下拉选择 → 输入数值特征 → 获取预测 |
| 📊 数据可视化 | 直方图、散点图、相关性热力图（服务端渲染，base64 嵌入） |

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

## 使用流程

```
1. 上传 / 生成测试数据  →  2. 数据清洗  →  3. 模型训练  →  4. 房价预测  →  5. 数据可视化
```

### 1. 数据上传
访问 `/upload`，选择 CSV 或 XLSX 文件上传。文件保存到 `data/datasets/raw/`，不允许重名。

### 2. 生成测试数据（可选）
访问 `/random-gen`，选择线性或多项式模式，设置样本数和噪声水平，一键生成合成数据用于快速验证流程。

### 3. 数据清洗
访问 `/clean`，选择原始数据集，勾选清洗操作（缺失值填充、异常值处理、标准化），执行后保存到 `data/datasets/cleaned/`。

### 4. 模型训练
访问 `/train`，选择已清洗数据集和算法（sklearn / pytorch），设置测试集比例。训练完成后显示 MSE、RMSE、R² 等指标，模型保存到 `data/models/`。

### 5. 房价预测
访问 `/predict`，选择已训练模型 → 查看性能指标 → 分类特征通过下拉框选择 → 输入数值特征 → 获取预测价格。

### 6. 数据可视化
访问 `/visualize`，选择数据集和图表类型（直方图/散点图/热力图），生成服务端渲染图表。

## 项目结构

```
py-exp/
├── src/
│   ├── app.py                    # Flask 应用入口，注册所有 Blueprint
│   ├── api/                      # 路由层（Flask Blueprint）
│   │   ├── upload.py             #   数据上传
│   │   ├── random_gen.py         #   合成测试数据生成
│   │   ├── clean.py              #   数据清洗
│   │   ├── train.py              #   模型训练
│   │   ├── analysis.py           #   房价预测
│   │   └── visualize.py          #   数据可视化
│   ├── services/                 # 业务逻辑层
│   │   ├── dataset_service.py    #   数据集存取
│   │   ├── random_gen_service.py #   合成数据生成
│   │   ├── clean_service.py      #   清洗流水线
│   │   ├── train_service.py      #   训练（sklearn + pytorch）
│   │   ├── predict_service.py    #   预测
│   │   └── visualize_service.py  #   图表生成
│   ├── dao/                      # 数据访问层
│   │   ├── __init__.py           #   DB 连接、路径常量
│   │   ├── dataset_dao.py        #   datasets 表 CRUD
│   │   └── model_dao.py          #   models 表 CRUD
│   └── templates/
│       └── index.html            # 首页导航
├── kaggle/
│   └── house_prices.csv/         # Kaggle 房价数据集（187K 行）
├── data/                         # 运行时数据（自动创建）
│   ├── datasets/raw/             #   原始上传文件
│   ├── datasets/cleaned/         #   清洗后文件
│   ├── models/                   #   训练好的模型 + 特征信息
│   └── database/app.db           #   SQLite 数据库
├── pyproject.toml
└── instruction.md                # 详细需求文档
```

## 数据库

SQLite 数据库自动创建于 `data/database/app.db`，包含两张表：

**datasets** — 数据集记录：`id`, `filename`, `metadata`(JSON: file_type, file_path, is_cleaned, clean_type, columns, row_count 等)

**models** — 模型记录：`id`, `model_name`, `metadata`(JSON: model_type, model_path, train_data_id, mse, rmse, r2, feature_info_path 等)

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
