import sqlite3
from mcp.server.fastmcp import FastMCP

# 1. MCP 서버 초기화
mcp = FastMCP("YukA-Log-Server")

# 2. 고도화된 파일 기반 데이터베이스(SQLite) 초기화
def init_db():
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    
    # ① 수유 기록 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feeding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id TEXT,
            time TEXT,
            amount INTEGER
        )
    """)
    
    # ② 수면 기록 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sleep (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id TEXT,
            start_time TEXT,
            duration_hours REAL
        )
    """)
    
    # ③ 성장 기록 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS growth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id TEXT,
            event TEXT,
            weight REAL
        )
    """)
    
    # ④ 예방접종 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vaccination (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            baby_id TEXT,
            vaccine_type TEXT,
            status TEXT,
            next_schedule TEXT
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

# =====================================================================
# [Tool ①] AI 수유 기록 기능
# =====================================================================
@mcp.tool()
def record_feeding(baby_id: str, time: str, amount_ml: int) -> str:
    """아기의 수유 시간과 수유량(ml)을 기록합니다."""
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feeding (baby_id, time, amount) VALUES (?, ?, ?)", (baby_id, time, amount_ml))
    conn.commit()
    conn.close()
    return f"[육아로그] 아기({baby_id})의 {time} 수유 기록 완료: {amount_ml}ml"

# =====================================================================
# [Tool ②] AI 수면 기록 기능
# =====================================================================
@mcp.tool()
def record_sleep(baby_id: str, start_time: str, duration_hours: float) -> str:
    """아기의 수면 시작 시간과 수면 시간(시간 단위, 예: 1.5)을 기록합니다."""
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO sleep (baby_id, start_time, duration_hours) VALUES (?, ?, ?)", (baby_id, start_time, duration_hours))
    conn.commit()
    conn.close()
    return f"[육아로그] 아기({baby_id})의 {start_time} 낮잠/수면 기록 완료: {duration_hours}시간"

# =====================================================================
# [Tool ③] AI 성장 과정 및 체중 기록 기능
# =====================================================================
@mcp.tool()
def record_growth(baby_id: str, event: str, weight_kg: float = 0.0) -> str:
    """아기의 성장 이벤트(예: 첫 뒤집기 성공) 및 체중(kg)을 기록합니다."""
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO growth (baby_id, event, weight) VALUES (?, ?, ?)", (baby_id, event, weight_kg))
    conn.commit()
    conn.close()
    
    msg = f"성장 이벤트 '{event}' 기록 완료"
    if weight_kg > 0:
        msg += f" (체중: {weight_kg}kg)"
    return f"[육아로그] 아기({baby_id}) {msg}"

# =====================================================================
# [Tool ④] AI 예방접종 일정 관리 기능
# =====================================================================
@mcp.tool()
def record_vaccination(baby_id: str, vaccine_type: str, status: str = "완료", next_schedule: str = "") -> str:
    """접종한 백신 종류와 상태(완료), 그리고 다음 접종 예정일을 기록합니다."""
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vaccination (baby_id, vaccine_type, status, next_schedule) VALUES (?, ?, ?, ?)", 
                   (baby_id, vaccine_type, status, next_schedule))
    conn.commit()
    conn.close()
    
    reply = f"[육아로그] {vaccine_type} 접종 {status} 처리되었습니다."
    if next_schedule:
        reply += f" (다음 접종 예정일: {next_schedule})"
    return reply

# =====================================================================
# [Tool ⑤] AI 통합 브리핑 및 부모 교대 육아 지원 기능
# =====================================================================
@mcp.tool()
def get_co_parenting_summary(baby_id: str) -> str:
    """엄마/아빠 교대 시 오늘 누적된 수유, 수면, 성장 및 접종 현황을 종합 브리핑합니다."""
    conn = sqlite3.connect("yukalog.db")
    cursor = conn.cursor()
    
    # 1. 누적 수유량 계산
    cursor.execute("SELECT COUNT(*), SUM(amount), MAX(time) FROM feeding WHERE baby_id = ?", (baby_id,))
    feed_count, total_feed, last_feed_time = cursor.fetchone()
    total_feed = total_feed if total_feed else 0
    last_feed_str = f" (마지막 수유: {last_feed_time})" if last_feed_time else ""
    
    # 2. 누적 수면 시간 계산
    cursor.execute("SELECT SUM(duration_hours) FROM sleep WHERE baby_id = ?", (baby_id,))
    total_sleep = cursor.fetchone()[0]
    total_sleep = total_sleep if total_sleep else 0.0
    
    # 3. 성장 이벤트 및 최근 체중 조회
    cursor.execute("SELECT event, weight FROM growth WHERE baby_id = ? ORDER BY id DESC", (baby_id,))
    growth_rows = cursor.fetchall()
    events = [row[0] for row in growth_rows if row[0] != ""]
    latest_weight = next((row[1] for row in growth_rows if row[1] > 0), "기록 없음")
    
    # 4. 다음 예방접종 일정 조회
    cursor.execute("SELECT vaccine_type, next_schedule FROM vaccination WHERE baby_id = ? AND next_schedule != '' ORDER BY id DESC LIMIT 1", (baby_id,))
    vac_row = cursor.fetchone()
    next_vac_str = f"{vac_row[0]} ({vac_row[1]})" if vac_row else "예정된 일정 없음"
    
    conn.close()
    
    event_str = ", ".join(events[:3]) if events else "특이사항 없음"
    
    # 부모 간 완벽한 인수인계를 위한 요약 포맷팅
    return (
        f"[공동 육아 실시간 브리핑]\n"
        f"🍼 수유 현황: 총 {feed_count}회 / {total_feed}ml{last_feed_str}\n"
        f"😴 낮잠 시간: 총 {total_sleep}시간\n"
        f"⚖️ 최근 체중: {latest_weight}kg\n"
        f"✨ 성장 이벤트: {event_str}\n"
        f"📅 다음 예방접종: {next_vac_str}"
    )

if __name__ == "__main__":
    mcp.run()
