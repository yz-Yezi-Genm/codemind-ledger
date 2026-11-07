# CodeMind Ledger · 个人记账本

福州大学 H202601《软件工程与软件工程实践》课程现场编程作业（2026-11-07）

**CodeMind Ledger** 是一个面向个人日常收支记录的轻量记账应用。项目采用 Flask 提供后端 API，使用原生 HTML、CSS 和 JavaScript 实现交互界面，并将记录保存在本地 JSON 文件中。

<kbd>v1.0.0</kbd> · 正式版本已发布

- **GitHub 仓库：** https://github.com/yz-Yezi-Genm/codemind-ledger
- **GitHub Release：** https://github.com/yz-Yezi-Genm/codemind-ledger/releases/tag/v1.0.0

## 项目功能

### 记账与记录管理
- 新增收入和支出记录。
- 记录日期、金额、类别和备注。
- 根据收入/支出类型切换可选类别。
- 首页查看最近记账记录。
- 后端 API 支持按记录 ID 修改和删除记录。

### 查询与统计
- 按日期范围筛选记录。
- 按收入/支出类型筛选。
- 按类别筛选。
- 按金额下限和上限筛选。
- 支持多个筛选条件组合使用。
- 统计收入、支出、结余和记录数量。

### 图表展示
- 按支出类别汇总金额。
- 以分类气泡图展示支出分布。
- 支持在气泡图与分类排行榜之间切换。

### 数据校验与持久化
- 对记录类型、日期、金额和类别进行校验。
- 对非法日期范围、非法金额范围等筛选条件进行提示。
- 使用 JSON 文件保存记录；服务重启或浏览器刷新后，已保存的数据仍可读取。
- 运行时数据文件不提交到 GitHub，避免把个人记账数据上传到仓库。

## 技术栈

| 部分 | 技术 |
| --- | --- |
| 后端 | Python 3.10+、Flask |
| 前端 | HTML5、CSS3、原生 JavaScript |
| 数据存储 | JSON 本地文件 |
| 自动化测试 | pytest |
| 协作与版本管理 | Git、GitHub、Pull Request |

## 运行环境与启动

建议使用 Python 3.10 或更高版本。以下命令以 Windows PowerShell 为例。

### 1. 克隆仓库

```powershell
git clone https://github.com/yz-Yezi-Genm/codemind-ledger.git
cd codemind-ledger
```

### 2. 创建虚拟环境

```powershell
py -3.10 -m venv .venv
```

### 3. 安装依赖

不需要先激活虚拟环境，可以直接运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. 启动应用

```powershell
.\.venv\Scripts\python.exe app.py
```

启动后，在浏览器访问：

http://127.0.0.1:5000/

停止服务时，在运行 Flask 的终端按 `Ctrl + C`。

> 当前项目使用 Flask 开发服务器，适用于本地运行和课程演示，不应直接作为生产环境服务器部署。

## 自动化测试

在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

**2026-11-07 最终集成验收记录：179 passed。**

测试覆盖类别管理、JSON 存储、记录校验、记录新增与编辑、最近记录、组合筛选、收支统计、图表数据以及 Flask API 等模块。以上为团队在最终集成版本上的本地测试结果。

## API 接口

所有业务接口均返回 JSON。成功响应采用：

```json
{
  "success": true,
  "data": {}
}
```

失败响应采用：

```json
{
  "success": false,
  "error": "中文错误信息"
}
```

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/` | 记账本 Web 页面 |
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/categories` | 获取收入和支出类别 |
| GET | `/api/records` | 查询最近记录，支持筛选参数和 `limit` |
| POST | `/api/records` | 新增记录 |
| PUT | `/api/records/<record_id>` | 修改指定记录 |
| DELETE | `/api/records/<record_id>` | 删除指定记录 |
| GET | `/api/statistics` | 获取收支汇总，支持组合筛选 |
| GET | `/api/charts` | 获取支出分类汇总数据 |

`/api/records` 和 `/api/statistics` 支持以下筛选参数：

- `start_date`：开始日期，格式为 `YYYY-MM-DD`
- `end_date`：结束日期，格式为 `YYYY-MM-DD`
- `record_type`：`income` 或 `expense`
- `category`：类别名称
- `min_amount`：金额下限
- `max_amount`：金额上限

其中 `/api/records` 还支持正整数参数 `limit`，默认查询最近 5 笔记录。多个筛选条件同时提供时，记录需要同时满足所有条件。

更多数据结构和接口约定见 [docs/CONTRACT.md](docs/CONTRACT.md)。

## 数据保存位置

应用运行时使用：

`data/records.json`

首次运行时，如果该文件不存在，程序会按空记录列表初始化。该文件已加入 `.gitignore`，不会随普通 Git 提交上传。仓库中的 `data/sample_records.json` 是示例数据，不是用户实际运行数据。

## 项目结构

```text
codemind-ledger/
├── app.py                  # Flask 路由与 API 集成（D1）
├── core/
│   ├── storage.py          # JSON 数据存储（A1）
│   ├── validators.py       # 记录数据校验（A2）
│   └── categories.py       # 收支类别管理（A3）
├── services/
│   ├── record_add.py       # 新增记录（B1）
│   ├── record_edit.py      # 修改与删除记录（B2）
│   ├── record_list.py      # 最近记录查询（B3）
│   ├── filters.py          # 组合筛选（C1）
│   ├── statistics.py       # 收支统计（C2）
│   └── charts.py           # 分类图表数据（C3）
├── templates/
│   └── index.html          # 页面结构（D2）
├── static/
│   ├── style.css           # 页面样式（D2）
│   └── app.js              # 前端交互与 API 调用（D3）
├── data/
│   └── sample_records.json # 示例数据
├── docs/
│   ├── CONTRACT.md         # 数据结构与 API 契约
│   ├── TEAM_TASKS.md       # 团队分工说明
│   └── WORKFLOW.md         # GitHub 协作流程
├── tests/                  # 自动化测试
├── requirements.txt
└── README.md
```

## 团队分工

| 编号 | 模块 | 主要负责人 |
| --- | --- | --- |
| A1 | JSON 存储 | 王智洋 |
| A2 | 记录校验 | 颜俊宇 |
| A3 | 类别管理 | 薛锦荣 |
| B1 | 添加记录 | 洪添军 |
| B2 | 修改/删除 | 赵紫龙 |
| B3 | 最近记录 | 林彦翔 |
| C1 | 组合筛选 | 雷葭雨 |
| C2 | 收支汇总 | 吴欣键 |
| C3 | 分类图表数据 | 林世颖 |
| D1 | Flask API 整合 | 罗宇泽 |
| D2 | 前端页面 | 吴诗莹 |
| D3 | 前端交互 | 丁晓炜 |

详细分工和协作规范见 [docs/TEAM_TASKS.md](docs/TEAM_TASKS.md) 与 [docs/WORKFLOW.md](docs/WORKFLOW.md)。

## 版本信息

- 当前正式版本：**v1.0.0**
- Release 页面：[CodeMind Ledger v1.0.0](https://github.com/yz-Yezi-Genm/codemind-ledger/releases/tag/v1.0.0)
- 发布目标：`main` 分支
- 课程现场编程日期：2026-11-07

## 当前版本说明

本项目面向课程现场编程任务，采用本地 JSON 文件保存数据，适合单机运行与课程演示。当前版本不包含账号登录、云端同步或多用户数据隔离功能。
