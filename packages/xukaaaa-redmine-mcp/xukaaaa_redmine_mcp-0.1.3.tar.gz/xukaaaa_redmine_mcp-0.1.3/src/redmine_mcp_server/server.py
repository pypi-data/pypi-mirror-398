#!/usr/bin/env python3
import os
import json
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
import ssl

# Khởi tạo MCP Server
mcp = FastMCP("Redmine Helper")

# === CONFIG ===
API_KEY = os.environ.get("REDMINE_API_KEY")
BASE_URL = os.environ.get("REDMINE_URL", "").rstrip("/")
CACHE_FILE = Path.home() / ".cache" / "redmine_mcp" / "cache.json"

SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

def get_headers():
    if not API_KEY:
        raise ValueError("❌ Missing REDMINE_API_KEY environment variable")
    return {
        "X-Redmine-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

def api_request(method, endpoint, data=None):
    """Helper gọi API, return dict hoặc raise Exception"""
    if not BASE_URL:
        raise ValueError("❌ Missing REDMINE_URL environment variable")

    url = f"{BASE_URL}{endpoint}"
    body = json.dumps(data).encode() if data else None
    
    req = urllib.request.Request(url, data=body, headers=get_headers(), method=method)

    try:
        with urllib.request.urlopen(req, context=SSL_CONTEXT) as resp:
            if resp.status == 204:
                return {}
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        raise RuntimeError(f"Redmine API Error {e.code}: {err_msg}")

# === CACHE UTILS ===

def _load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return None

def _get_custom_field_ids(issue_id: int, cache: dict) -> dict:
    """Get custom field IDs từ cache hoặc fetch từ issue"""
    if cache and "custom_fields" in cache and cache["custom_fields"]:
        return cache["custom_fields"]
    
    try:
        data = api_request("GET", f"/issues/{issue_id}.json")
        cf_ids = {}
        for cf in data["issue"].get("custom_fields", []):
            name_normalized = cf["name"].lower().replace(" ", "").replace("_", "").replace(".", "")
            if "actstart" in name_normalized:
                cf_ids["act.start"] = cf["id"]
            elif "actfinish" in name_normalized:
                cf_ids["act.finish"] = cf["id"]
        
        if cf_ids and cache:
            cache["custom_fields"] = cf_ids
            _save_cache(cache)
        return cf_ids
    except Exception:
        return {}

def _save_cache(data):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))

def _ensure_metadata():
    """Đảm bảo đã có cache status/activities, nếu chưa thì fetch"""
    if _load_cache():
        return

    statuses_data = api_request("GET", "/issue_statuses.json")
    statuses = {
        s["name"].lower().replace(" ", "_"): s["id"]
        for s in statuses_data["issue_statuses"]
    }

    activities_data = api_request("GET", "/enumerations/time_entry_activities.json")
    activities = {
        a["name"].lower(): a["id"]
        for a in activities_data["time_entry_activities"]
        if a.get("active", True)
    }

    default_activity = activities.get("development") or list(activities.values())[0]

    cache = {
        "statuses": statuses,
        "activities": activities,
        "default_activity_id": default_activity
    }
    _save_cache(cache)
    return cache

# === MCP TOOLS ===

@mcp.tool()
def list_my_tasks(status_filter: str = "open") -> str:
    """
    Lấy danh sách task được assign cho tôi.
    Args:
        status_filter: Trạng thái task (open, closed, hoặc tên status cụ thể like 'in_progress'). Default: open.
    """
    _ensure_metadata()
    endpoint = "/issues.json?assigned_to_id=me&limit=25"
    cache = _load_cache()

    if status_filter in ["open", "closed"]:
         endpoint += f"&status_id={status_filter}"
    elif cache and status_filter in cache["statuses"]:
        endpoint += f"&status_id={cache['statuses'][status_filter]}"
    else:
        endpoint += "&status_id=open"

    try:
        data = api_request("GET", endpoint)
    except Exception as e:
        return f"Error fetching tasks: {str(e)}"

    issues = data.get("issues", [])
    if not issues:
        return "📭 Không có task nào phù hợp."

    result = [f"📋 Tasks ({len(issues)}):\n"]
    for issue in issues:
        status = issue["status"]["name"]
        progress = issue.get("done_ratio", 0)
        due = issue.get("due_date", "N/A")
        project = issue['project']['name']
        result.append(f"- #{issue['id']} [{status}] {progress}%: {issue['subject']}")
        result.append(f"  (Due: {due} | Project: {project})")
    
    return "\n".join(result)

@mcp.tool()
def get_issue_details(issue_id: int) -> str:
    """Xem chi tiết một task cụ thể bằng ID."""
    try:
        data = api_request("GET", f"/issues/{issue_id}.json?include=journals,children")
        issue = data["issue"]
    except Exception as e:
        return f"Không tìm thấy issue #{issue_id}. Error: {str(e)}"

    lines = [
        f"#{issue['id']} - {issue['subject']}",
        f"Project:    {issue['project']['name']}",
        f"Status:     {issue['status']['name']}",
        f"Progress:   {issue.get('done_ratio', 0)}%",
        f"Assigned:   {issue.get('assigned_to', {}).get('name', 'N/A')}",
        f"Start date: {issue.get('start_date', 'N/A')}",
        f"Due date:   {issue.get('due_date', 'N/A')}",
        f"Spent:      {issue.get('spent_hours', 0)}h / Est: {issue.get('estimated_hours', 'N/A')}h"
    ]

    if issue.get("parent"):
        lines.append(f"Parent:     #{issue['parent']['id']}")

    if issue.get("children"):
        lines.append(f"\nSubtasks ({len(issue['children'])}):")
        for child in issue['children']:
            lines.append(f"  - #{child['id']}: {child.get('subject', 'N/A')}")

    if issue.get("description"):
        lines.append(f"\nDescription:\n{issue['description'][:500]}...")

    journals = issue.get("journals", [])
    notes = [j for j in journals if j.get("notes")]
    if notes:
        lines.append(f"\nRecent notes:")
        for note in notes[-3:]:
            author = note["user"]["name"]
            created = note["created_on"][:10]
            lines.append(f"- [{created}] {author}: {note['notes'][:100]}...")

    return "\n".join(lines)

@mcp.tool()
def log_time(issue_id: int, hours: float, comment: str) -> str:
    """
    Log thời gian làm việc vào task.
    Args:
        issue_id: ID của task
        hours: Số giờ (ví dụ 1.5)
        comment: Mô tả công việc đã làm
    """
    _ensure_metadata()
    cache = _load_cache()
    
    data = {
        "time_entry": {
            "issue_id": int(issue_id),
            "hours": float(hours),
            "comments": comment,
            "activity_id": cache["default_activity_id"]
        }
    }

    try:
        api_request("POST", "/time_entries.json", data)
        return f"✅ Đã log {hours}h vào task #{issue_id}. Comment: {comment}"
    except Exception as e:
        return f"Lỗi log time: {str(e)}"

@mcp.tool()
def update_issue_status(
    issue_id: int, 
    status_name: str,
    act_start: Optional[str] = None,
    act_finish: Optional[str] = None
) -> str:
    """
    Cập nhật trạng thái của task.
    Args:
        issue_id: ID của task
        status_name: Tên trạng thái (ví dụ: 'resolved', 'in progress', 'completed')
        act_start: Ngày bắt đầu thực tế (YYYY-MM-DD). Bắt buộc khi status=completed. Default: today
        act_finish: Ngày kết thúc thực tế (YYYY-MM-DD). Bắt buộc khi status=completed. Default: today
    """
    _ensure_metadata()
    cache = _load_cache()
    
    status_lower = status_name.lower().replace(" ", "_")
    if status_lower not in cache["statuses"]:
        valid_statuses = ", ".join(cache['statuses'].keys())
        return f"❌ Status '{status_name}' không hợp lệ. Các status khả dụng: {valid_statuses}"

    status_id = cache["statuses"][status_lower]
    issue_data = {"status_id": status_id}
    
    if status_lower == "completed":
        today = date.today().isoformat()
        act_start = act_start or today
        act_finish = act_finish or today
        
        cf_ids = _get_custom_field_ids(issue_id, cache)
        custom_fields = []
        
        if "act.start" in cf_ids:
            custom_fields.append({"id": cf_ids["act.start"], "value": act_start})
        if "act.finish" in cf_ids:
            custom_fields.append({"id": cf_ids["act.finish"], "value": act_finish})
        
        if custom_fields:
            issue_data["custom_fields"] = custom_fields
            issue_data["done_ratio"] = 100
    
    try:
        api_request("PUT", f"/issues/{issue_id}.json", {"issue": issue_data})
        msg = f"✅ Đã đổi trạng thái task #{issue_id} sang '{status_name}'"
        if status_lower == "completed":
            msg += f"\n   Act.Start: {act_start}, Act.Finish: {act_finish}"
        return msg
    except Exception as e:
        return f"Lỗi update status: {str(e)}"

@mcp.tool()
def update_progress(issue_id: int, percent: int) -> str:
    """Cập nhật % hoàn thành (0-100)"""
    if not (0 <= percent <= 100):
        return "❌ Percent phải từ 0 đến 100"
        
    data = {"issue": {"done_ratio": int(percent)}}
    try:
        api_request("PUT", f"/issues/{issue_id}.json", data)
        return f"✅ Đã cập nhật task #{issue_id} lên {percent}%"
    except Exception as e:
        return f"Lỗi update progress: {str(e)}"

@mcp.tool()
def add_note(issue_id: int, note: str) -> str:
    """Thêm comment (note) vào task"""
    data = {"issue": {"notes": note}}
    try:
        api_request("PUT", f"/issues/{issue_id}.json", data)
        return f"✅ Đã thêm note vào task #{issue_id}"
    except Exception as e:
        return f"Lỗi thêm note: {str(e)}"

@mcp.tool()
def get_today_logs() -> str:
    """Kiểm tra tổng giờ đã log trong hôm nay"""
    today = date.today().isoformat()
    try:
        data = api_request("GET", f"/time_entries.json?user_id=me&from={today}&to={today}&limit=100")
        entries = data.get("time_entries", [])
    except Exception as e:
        return f"Lỗi lấy log: {str(e)}"

    total = sum(e["hours"] for e in entries)
    lines = [f"📅 Time log hôm nay ({today}):"]
    
    for e in entries:
        issue_id = e.get("issue", {}).get("id", "N/A")
        lines.append(f"- #{issue_id}: {e['hours']}h ({e.get('comments', 'No comment')})")

    lines.append(f"\n⏱️  Tổng cộng: {total}h")
    if total < 8:
        lines.append(f"⚠️  Còn thiếu {8 - total}h nữa mới đủ 8h.")
    else:
        lines.append("✅ Đã log đủ giờ!")
        
    return "\n".join(lines)

@mcp.tool()
def get_time_logs_range(from_date: str, to_date: str) -> str:
    """
    Xem tổng giờ đã log trong khoảng thời gian.
    Args:
        from_date: Ngày bắt đầu (YYYY-MM-DD)
        to_date: Ngày kết thúc (YYYY-MM-DD)
    """
    try:
        data = api_request("GET", f"/time_entries.json?user_id=me&from={from_date}&to={to_date}&limit=100")
        entries = data.get("time_entries", [])
    except Exception as e:
        return f"Lỗi lấy log: {str(e)}"

    if not entries:
        return f"📭 Không có time log nào từ {from_date} đến {to_date}."

    total = sum(e["hours"] for e in entries)
    lines = [f"📅 Time log từ {from_date} đến {to_date}:\n"]
    
    by_date = {}
    for e in entries:
        spent_on = e.get("spent_on", "N/A")
        if spent_on not in by_date:
            by_date[spent_on] = []
        by_date[spent_on].append(e)
    
    for day in sorted(by_date.keys()):
        day_entries = by_date[day]
        day_total = sum(e["hours"] for e in day_entries)
        lines.append(f"\n[{day}] - {day_total}h:")
        for e in day_entries:
            issue_id = e.get("issue", {}).get("id", "N/A")
            lines.append(f"  - #{issue_id}: {e['hours']}h ({e.get('comments', 'No comment')})")
    
    lines.append(f"\n⏱️  Tổng cộng: {total}h")
    return "\n".join(lines)

@mcp.tool()
def clear_cache() -> str:
    """Xóa cache để reload metadata từ Redmine"""
    try:
        if CACHE_FILE.exists():
            CACHE_FILE.unlink()
        return "✅ Đã xóa cache. Metadata sẽ được reload ở lần gọi tiếp theo."
    except Exception as e:
        return f"Lỗi xóa cache: {str(e)}"

def main():
    """Entry point cho CLI"""
    mcp.run()

if __name__ == "__main__":
    main()
