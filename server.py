import sqlite3
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

# 1. MCP 및 FastAPI 초기화
mcp = FastMCP("YukA-Log-Server")
app = FastAPI(title="YukA-Log-Server-Wrapper")

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

# [MCP Tools 정의]
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
    return f"[육아로그] 아기({baby_id}) 성장 이벤트 '{event}' 기록 완료 (체중: {weight_kg}kg)"

@mcp.tool()
def record_vaccination(baby_id: str, vaccine_type: str, status: str = "완료", next_schedule: str = "") -> str:
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vaccination (baby_id, vaccine_type, status, next_schedule) VALUES (?, ?, ?, ?)", (baby_id, vaccine_type, status, next_schedule))
    conn.commit()
    conn.close()
    return f"[육아로그] {vaccine_type} 접종 완료 (다음 예정일: {next_schedule})"

@mcp.tool()
def get_co_parenting_summary(baby_id: str) -> str:
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM feeding WHERE baby_id = ?", (baby_id,))
    feed_count, total_feed = cursor.fetchone()
    total_feed = total_feed if total_feed else 0
    conn.close()
    return f"[공동 육아 브리핑] 오늘 수유: {feed_count}회 / 총 {total_feed}ml"

# 3. 카카오 시스템 연동을 위한 라우팅 강제 설정
@app.get("/")
@app.get("/health")
def health_check():
    """카카오의 서버 생존 확인(Health Check)에 응답하는 경로"""
    return {"status": "healthy", "mcp_server": "active"}

# FastMCP의 HTTP 통신 진입점을 FastAPI 웹 주소에 강제로 이식
from mcp.server.fastmcp.transport.sse import ASMGSSETransport
sse_transport = ASMGSSETransport(mcp)

@app.get("/sse")
async def handle_sse_connect(request: Request):
    return await sse_transport.handle_connect(request)

@app.post("/sse")
async def handle_sse_message(request: Request):
    return await sse_transport.handle_message(request)

if __name__ == "__main__":
    import uvicorn
    # 카카오가 요구하는 0.0.0.0 주소와 8000 포트로 웹 서버 구동
    uvicorn.run(app, host="0.0.0.0", port=8000)
