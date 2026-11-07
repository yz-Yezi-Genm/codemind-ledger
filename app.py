"""D1 负责模块：Flask 路由及服务集成。

目前只提供可启动的项目基础设施和 501 占位 API。
D1 需要独立完成实际接口参数解析、服务调用和错误处理。
请先阅读 docs/CONTRACT.md。
"""
from flask import Flask, jsonify, render_template
from core.categories import get_categories

app = Flask(__name__)


@app.get("/")
def index():
    """基础页面入口；D2/D3 后续完善页面与交互。"""
    return render_template("index.html")


@app.get("/api/health")
def health():
    """启动检查，不代表业务功能已完成。"""
    return jsonify({"success": True, "data": {"status": "scaffold"}})


def not_implemented():
    """占位响应：禁止将 501 误认为已经实现的业务功能。"""
    return jsonify({"success": False, "error": "接口尚未实现，请对应成员完成模块"}), 501


@app.get("/api/records")
def list_records():
    # TODO(D1): 调用 B3/C1 的模块，根据查询参数返回记录。
    return not_implemented()


@app.post("/api/records")
def create_record():
    # TODO(D1): 读取 JSON 请求体并调用 B1 添加记录。
    return not_implemented()


@app.put("/api/records/<record_id>")
def edit_record(record_id):
    # TODO(D1): 调用 B2 修改记录，处理记录不存在/参数无效。
    return not_implemented()


@app.delete("/api/records/<record_id>")
def remove_record(record_id):
    # TODO(D1): 调用 B2 删除记录。
    return not_implemented()


@app.get("/api/statistics")
def statistics_api():
    # TODO(D1): 调用 C1/C2，返回筛选后的统计结果。
    return not_implemented()


@app.get("/api/charts")
def charts_api():
    # TODO(D1): 调用 C3，返回图表数据。
    return not_implemented()


@app.get("/api/categories")
def categories_api():
    categories = get_categories()
    return jsonify({
        "success": True,
        "data": categories
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
