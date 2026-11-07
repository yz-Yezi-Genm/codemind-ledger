"""D1 负责模块：Flask 路由及服务集成。

目前只提供可启动的项目基础设施和 501 占位 API。
D1 需要独立完成实际接口参数解析、服务调用和错误处理。
请先阅读 docs/CONTRACT.md。
"""

from flask import request
from services.record_add import add_record

from flask import Flask, jsonify, render_template
from core.categories import get_categories

from core.storage import load_records
from services.charts import category_statistics

from services.record_edit import delete_record

from services.record_list import get_recent_records
from services.filters import filter_records

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
    """查询记账记录，支持组合筛选和数量限制。"""
    try:
        # 获取 limit，默认返回最近 5 条
        limit_text = request.args.get("limit", "5")

        if not limit_text.isdecimal() or int(limit_text) <= 0:
            raise ValueError("limit 必须是正整数")

        limit = int(limit_text)

        # 读取六个可选筛选参数
        filter_keys = (
            "start_date", "end_date", "record_type",
            "category", "min_amount", "max_amount"
        )

        filters = {
            key: request.args.get(key)
            for key in filter_keys
        }

        has_filters = any(
            value not in (None, "")
            for value in filters.values()
        )

        if has_filters:
            # 有筛选条件：A1 读取全部记录，C1 负责筛选
            records = load_records()
            records = filter_records(records, **filters)

            # 按日期倒序，同一天后添加的排在前面
            records = [
                record
                for _, record in sorted(
                    enumerate(records),
                    key=lambda item: (
                        item[1]["date"], item[0]
                    ),
                    reverse=True
                )
            ][:limit]
        else:
            # 无筛选条件：直接调用 B3
            records = get_recent_records(limit=limit)

        return jsonify({
            "success": True,
            "data": records
        }), 200

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("查询记账记录时发生错误")
        return jsonify({
            "success": False,
            "error": "服务器查询记账记录时发生错误"
        }), 500


@app.post("/api/records")
def create_record():
    """新增一笔收入或支出记录。"""

    # 1. 获取客户端发送的 JSON 数据
    data = request.get_json(silent=True)

    # 2. 检查请求体是否为 JSON 对象
    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "请求体必须是 JSON 对象"
        }), 400

    try:
        # 3. 调用 B1 模块新增记录
        new_record = add_record(data)

        # 4. 新增成功，返回记录和 HTTP 201
        return jsonify({
            "success": True,
            "data": new_record
        }), 201

    except ValueError as error:
        # 5. 业务数据不合法，返回 HTTP 400
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except NotImplementedError:
        # 6. 依赖模块尚未实现
        return jsonify({
            "success": False,
            "error": "新增记录依赖的模块尚未完成"
        }), 501

    except Exception:
        # 7. 其他服务器异常，记录日志并返回 HTTP 500
        app.logger.exception("新增记录时发生服务器异常")
        return jsonify({
            "success": False,
            "error": "服务器处理新增记录时发生错误"
        }), 500


@app.put("/api/records/<record_id>")
def edit_record(record_id):
    # TODO(D1): 调用 B2 修改记录，处理记录不存在/参数无效。
    return not_implemented()


@app.delete("/api/records/<record_id>")
def remove_record(record_id):
    """删除指定 ID 的记账记录。"""
    try:
        deleted = delete_record(record_id)

        if not deleted:
            return jsonify({
                "success": False,
                "error": "指定的记账记录不存在"
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "id": record_id,
                "deleted": True
            }
        }), 200

    except Exception:
        app.logger.exception("删除记账记录时发生错误")
        return jsonify({
            "success": False,
            "error": "服务器删除记录时发生错误"
        }), 500

@app.get("/api/statistics")
def statistics_api():
    # TODO(D1): 调用 C1/C2，返回筛选后的统计结果。
    return not_implemented()


@app.get("/api/charts")
def charts_api():
    """返回各支出类别的统计数据。"""
    try:
        records = load_records()
        chart_data = category_statistics(records)

        return jsonify({
            "success": True,
            "data": chart_data
        }), 200

    except Exception:
        app.logger.exception("获取图表数据失败")
        return jsonify({
            "success": False,
            "error": "获取图表数据失败"
        }), 500


@app.get("/api/categories")
def categories_api():
    categories = get_categories()
    return jsonify({
        "success": True,
        "data": categories
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
