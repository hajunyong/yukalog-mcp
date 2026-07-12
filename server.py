import sqlite3
from mcp.server.fastmcp import FastMCP

# 1. MCP 서버 초기화
mcp = FastMCP("YukA-Log-Server")

# 2. SQLite DB 초기화
def init_db():
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS feeding (id INTEGER PRIMARY KEY AUTOINCREMENT, baby_id TEXT, time TEXT, amount INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS sleep (id INTEGER PRIMARY KEY AUTOINCREMENT, baby_id TEXT, start_time TEXT, duration_hours REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS growth (id INTEGER PRIMARY KEY AUTOINCREMENT, baby_id TEXT, event TEXT, weight REAL)")
    cursor.execute("CREATE TABLE IF NOT EXISTS vaccination (id INTEGER PRIMARY KEY AUTOINCREMENT, baby_id TEXT, vaccine_type TEXT, status TEXT, next_schedule TEXT)")
    conn.commit()
    conn.close()

init_db()

# [MCP 도구들 정의]
@mcp.tool()
def record_feeding(baby_id: str, time: str, amount_ml: int) -> str:
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feeding (baby_id, time, amount) VALUES (?, ?, ?)", (baby_id, time, amount_ml))
    conn.commit()
    conn.close()
    return f"[육아로그] 아기({baby_id})의 {time} 수유 기록 완료: {amount_ml}ml"

@mcp.tool()
def record_sleep(baby_id: str, start_time: str, duration_hours: float) -> str:
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sleep (baby_id, start_time, duration_hours) VALUES (?, ?, ?)", (baby_id, start_time, duration_hours))
    conn.commit()
    conn.close()
    return f"[육아로그] 아기({baby_id})의 {start_time} 수면 기록 완료: {duration_hours}시간"

@mcp.tool()
def record_growth(baby_id: str, event: str, weight_kg: float = 0.0) -> str:
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO growth (baby_id, event, weight) VALUES (?, ?, ?)", (baby_id, event, weight_kg))
    conn.commit()
    conn.close()
    return f"[육아로그] 아기({baby_id}) 성장 이벤트 '{event}' 기록 완료"

@mcp.tool()
def record_vaccination(baby_id: str, vaccine_type: str, status: str = "완료", next_schedule: str = "") -> str:
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vaccination (baby_id, vaccine_type, status, next_schedule) VALUES (?, ?, ?, ?)", (baby_id, vaccine_type, status, next_schedule))
    conn.commit()
    conn.close()
    return f"[육아로그] {vaccine_type} 접종 완료"

@mcp.tool()
def get_co_parenting_summary(baby_id: str) -> str:
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM feeding WHERE baby_id = ?", (baby_id,))
    feed_count, total_feed = cursor.fetchone()
    total_feed = total_feed if total_feed else 0
    conn.close()
    return f"[공동 육아 브리핑] 오늘 수유: {feed_count}회 / 총 {total_feed}ml"

if __name__ == "__main__":
    # FastMCP 가 제공하는 순정 내장 HTTP 서버를 활용하여 8000포트로 구동합니다.
    # 이렇게 하면 카카오의 / 및 /sse 요청을 표준 규격대로 깔끔하게 처리합니다.
    mcp.run(transport="http", host="0.0.0.0", port=8000)
