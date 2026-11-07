
"""D1 Flask API 集成测试。使用临时文件，避免修改真实记账数据。"""

import pytest
import core.storage as storage
from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # 将数据文件切换到 pytest 创建的临时目录
    monkeypatch.setattr(
        storage, "RECORDS_PATH", tmp_path / "records.json"
    )
    return app.test_client()


def test_categories_and_empty_data(client):
    """类别、空记录、空统计、空图表。"""
    categories = client.get("/api/categories")
    assert categories.status_code == 200
    assert "餐饮" in categories.get_json()["data"]["expense"]

    records = client.get("/api/records")
    assert records.status_code == 200
    assert records.get_json()["data"] == []

    stats = client.get("/api/statistics")
    assert stats.status_code == 200
    assert stats.get_json()["data"]["count"] == 0

    charts = client.get("/api/charts")
    assert charts.status_code == 200
    assert charts.get_json()["data"] == []


def test_invalid_query_parameters(client):
    """非法查询条件必须返回 HTTP 400。"""
    assert client.get("/api/records?limit=0").status_code == 400
    assert client.get("/api/records?min_amount=nan").status_code == 400
    assert client.get("/api/statistics?min_amount=nan").status_code == 400


def test_invalid_create_request(client):
    """新增记录缺少必填字段时应被拒绝。"""
    response = client.post(
        "/api/records",
        json={"type": "expense", "amount": -10}
    )
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_create_update_delete_flow(client):
    """真实测试新增、查询、修改、统计、图表和删除。"""
    record_data = {
        "type": "expense",
        "date": "2026-11-07",
        "amount": 25.5,
        "category": "餐饮",
        "note": "D1自动化测试"
    }

    # 新增
    created = client.post("/api/records", json=record_data)
    assert created.status_code == 201

    record_id = created.get_json()["data"]["id"]
    assert record_id.startswith("rec_")

    # 查询
    records = client.get("/api/records")
    assert records.status_code == 200
    assert len(records.get_json()["data"]) == 1

    # 修改
    updated = client.put(
        f"/api/records/{record_id}",
        json={"amount": 30.8}
    )
    assert updated.status_code == 200
    assert updated.get_json()["data"]["amount"] == 30.8

    # 汇总统计
    stats = client.get("/api/statistics")
    assert stats.get_json()["data"]["expense"] == 30.8
    assert stats.get_json()["data"]["count"] == 1

    # 分类图表
    charts = client.get("/api/charts")
    assert charts.get_json()["data"] == [
        {"category": "餐饮", "amount": 30.8}
    ]

    # 删除
    deleted = client.delete(f"/api/records/{record_id}")
    assert deleted.status_code == 200

    # 删除后检查
    assert client.get("/api/records").get_json()["data"] == []
    assert client.get("/api/statistics").get_json()["data"]["count"] == 0


def test_nonexistent_record(client):
    """修改或删除不存在的记录，必须返回 404。"""
    missing_id = "rec_not_exists"

    response = client.put(
        f"/api/records/{missing_id}",
        json={"amount": 20}
    )
    assert response.status_code == 404

    response = client.delete(f"/api/records/{missing_id}")
    assert response.status_code == 404
