"""A1 负责：JSON 数据文件读写。

默认文件路径：data/records.json（运行时生成，不提交）。
可在启动前设置 CODEMIND_RECORDS_PATH 环境变量；支持绝对路径、~ 和相对项目根目录的路径。
PowerShell 示例：$env:CODEMIND_RECORDS_PATH = 'D:/ledger/records.json'
配置在模块导入时读取，修改后需重启；不会自动搬迁旧数据。
备份与账本同目录，名称为账本完整文件名加 .bak。
与 B1/B2/B3 的接口已经约定，请勿擅自更名。
"""

import json
import os
from pathlib import Path
import tempfile


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_CONFIGURED_PATH = Path(os.environ.get("CODEMIND_RECORDS_PATH") or "data/records.json").expanduser()
RECORDS_PATH = (_PROJECT_ROOT / _CONFIGURED_PATH).resolve()


def _read_records(path):
    """校验文件并返回记录与原文；缺失文件仍抛出 FileNotFoundError。"""
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise FileNotFoundError(f"账本文件不存在：{path}") from error
    except PermissionError as error:
        raise PermissionError(f"读取账本失败：无读取权限（{path}）：{error}") from error
    except UnicodeDecodeError as error:
        raise ValueError(f"账本文件不是有效的 UTF-8 编码：{path}") from error
    except OSError as error:
        raise OSError(f"读取账本失败（{path}）：{error}") from error
    try:
        records = json.loads(content)
    except json.JSONDecodeError as error:
        raise ValueError(f"账本 JSON 已损坏（{path}），请检查文件或显式恢复备份") from error
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError(f"记录数据必须是字典组成的列表：{path}")
    return records, content


def load_records():
    """读取所有记录；首次文件不存在时返回 []，损坏时不自动恢复。"""
    try:
        records, _ = _read_records(RECORDS_PATH)
        return records
    except FileNotFoundError:
        return []


def _atomic_write(path, content, before_replace=None):
    """写完并关闭临时文件后替换；可在替换前执行备份。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix="records-", suffix=".tmp", delete=False,
        ) as file:
            temp_path = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        # 同目录保证位于同一文件系统；Windows 下须先关闭文件再替换。
        if before_replace is not None:
            before_replace()
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                # 清理失败不能掩盖原始写入异常；残留临时文件不会作为账本读取。
                pass


def save_records(records):
    """完整覆盖保存并保留上一版有效账本到 <账本完整文件名>.bak。

    首次保存不生成备份；旧账本损坏或备份失败时停止保存。
    仅检查存储结构，业务字段由 A2 校验；不提供并发读改写控制。
    """
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ValueError("记录数据必须是字典组成的列表")
    try:
        content = json.dumps(records, ensure_ascii=False, indent=2, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise type(error)(f"保存账本失败：记录包含无法转换为 JSON 的内容：{error}") from error

    try:
        _, previous = _read_records(RECORDS_PATH)
    except FileNotFoundError:
        previous = None

    def backup_previous():
        if previous is not None:
            _atomic_write(RECORDS_PATH.with_name(RECORDS_PATH.name + ".bak"), previous)

    try:
        _atomic_write(RECORDS_PATH, content, before_replace=backup_previous)
    except PermissionError as error:
        raise PermissionError(f"保存账本失败：无写入权限或文件被占用：{error}") from error
    except OSError as error:
        raise OSError(f"保存账本失败，请检查磁盘空间和文件系统：{error}") from error


def restore_records():
    """显式用上一版备份覆盖当前账本，成功返回 None，保留备份不变。

    可用于恢复损坏或缺失的账本；备份缺失、损坏时不修改当前文件。
    此操作会丢弃当前账本的更新，调用前应停止其他记账操作。
    """
    _, content = _read_records(RECORDS_PATH.with_name(RECORDS_PATH.name + ".bak"))
    try:
        _atomic_write(RECORDS_PATH, content)
    except PermissionError as error:
        raise PermissionError(f"恢复账本失败：无写入权限或文件被占用：{error}") from error
    except OSError as error:
        raise OSError(f"恢复账本失败，请检查磁盘空间和文件系统：{error}") from error
