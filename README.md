# CodeMind Ledger · 个人记账本

福州大学 H202601 软件工程与软件工程实践 · 2026-11-07 现场编程

> 当前状态：**协作开发骨架**。仓库中的函数占位符尚未实现，**不是已完成的软件**。
> 所有成员必须独立编写自己负责的真实功能并使用本人账号提交，禁止伪造提交记录或代写。

## 技术约定

- Python 3.10+、Flask、原生 HTML/CSS/JavaScript
- JSON 本地文件保存（`data/records.json`，不纳入版本控制）
- 唯一数据契约和 API 约定请看 [docs/CONTRACT.md](docs/CONTRACT.md)
- 12 人模块归属请看 [docs/TEAM_TASKS.md](docs/TEAM_TASKS.md)
- 分支、PR、合并流程请看 [docs/WORKFLOW.md](docs/WORKFLOW.md)

## 团队成员分工（请认领）

请每位成员认领**一个且仅一个主负责模块**，把本行“待填写”改为自己的姓名（可加学号）；填写后应实际独立编写该模块并保留本人 GitHub 提交记录。详细要求见 [12 人分工说明](docs/TEAM_TASKS.md)。

| 编号 | 模块 | 主要文件 | 交付标准 | 负责人姓名 |
| --- | --- | --- | --- | --- |
| A1 | JSON 存储 | `core/storage.py` | 首次读取、读写持久化、中文内容 | 王智洋 |
| A2 | 记录校验 | `core/validators.py` | 合法/非法类型、金额、日期、类别 | 颜俊宇 |
| A3 | 类别管理 | `core/categories.py` | 类别列表、类型与类别规则 | 薛锦荣 |
| B1 | 添加记录 | `services/record_add.py` | 创建唯一 ID、保存、异常处理 | 洪添军 |
| B2 | 修改/删除 | `services/record_edit.py` | ID 查询、更新、删除、找不到 | 赵紫龙 |
| B3 | 最近记录 | `services/record_list.py` | 按日期排序、limit | 林彦翔 |
| C1 | 组合筛选 | `services/filters.py` | 日期、类别、类型、金额上下限 | 雷葭雨 |
| C2 | 收支汇总 | `services/statistics.py` | 收入、支出、结余、笔数 | 吴欣键 |
| C3 | 分类图表数据 | `services/charts.py` | 支出分组、汇总结果 | 林世颖 |
| D1 | Flask API 整合 | `app.py` | 路由调用各模块、HTTP 错误处理 | 罗宇泽 |
| D2 | 前端页面 | `templates/index.html`、`static/style.css` | 表单、列表、统计区、自适应 | 吴诗莹 |
| D3 | 前端交互 | `static/app.js` | 请求接口、提示信息、图表 | 丁晓炜 |

> 编辑提醒：GitHub 网页可点击文件右上角铅笔图标编辑；多人同时改同一文件可能产生冲突。请逐人保存，或通过个人分支发起 PR，经审核后合并。

## Windows 本地启动（当前仅有骨架页面）

```powershell
git clone https://github.com/yz-Yezi-Genm/codemind-ledger.git
cd codemind-ledger
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

浏览器打开 http://127.0.0.1:5000 。当前主页与 `/api/health` 可访问，
业务 API 暂时统一返回 HTTP 501，**等模块负责同学自行完成后才能真正记账**。

如 PowerShell 禁止激活，可以不激活环境，直接：
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## 运行基础检查

```powershell
python -m pytest -q
```

注意：现有测试只检查项目骨架的 HTTP 响应，并不代表记账功能完成；
成员应自行为负责模块编写真实单元测试与边界用例。

## 推荐协作节奏

1. 组长确认数据格式和接口，不再任意更改（如需变更，先群内同步）。
2. 每人克隆仓库，从 `main` 新建自己的 `feat/xxx` 分支。
3. 只修改负责的模块和自己的测试文件；跨文件改动先沟通。
4. 本人运行测试、提交 commit、推送分支、创建 Pull Request。
5. 组长/同伴 Review 后分批合并，集成测试，再在 17:00 前发布 GitHub Release。
6. 演示后收集真实开发记录、截图、视频，23:00 前完成团队博客。

### 截止节点
- 17:00：提交仓库链接并发布可演示版本 Release
- 17:00–17:15：现场演示
- 23:00：团队博客与要求的链接

## 当前模块进度
- [x] 仓库基础骨架、接口文档与协作规范
- [ ] A1~A3 数据层
- [ ] B1~B3 记账功能
- [ ] C1~C3 查询统计
- [ ] D1~D3 Web 界面及路由
- [ ] 全流程联调、演示与 Release

## 说明
`data/sample_records.json` 是可提交的模拟数据；
`data/records.json` 为运行时用户数据，不应提交到 GitHub。
