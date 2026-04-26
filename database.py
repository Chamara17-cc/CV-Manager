"""
database.py  —  CV Manager
All MySQL operations live here. Update DB_CONFIG with your credentials.
"""

import mysql.connector
from mysql.connector import Error


# ── Configure your MySQL connection here ─────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "chmr@123",
    "database": "cv_manager",
}
# ─────────────────────────────────────────────────────────────────────────────


def get_connection():
    """Return a live MySQL connection or raise a readable error."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"Cannot connect to MySQL: {e}")


# ── CREATE ────────────────────────────────────────────────────────────────────

def add_candidate(data: dict) -> int:
    """
    Insert a new candidate row.
    data keys: full_name, email, phone, role, experience,
               location, skills, status, notes
    Returns the new row id.
    """
    sql = """
        INSERT INTO candidates
            (full_name, email, phone, role, experience, location, skills, status, notes)
        VALUES
            (%(full_name)s, %(email)s, %(phone)s, %(role)s, %(experience)s,
             %(location)s, %(skills)s, %(status)s, %(notes)s)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# ── READ ──────────────────────────────────────────────────────────────────────

def get_all_candidates() -> list[dict]:
    """Return every candidate, newest first."""
    sql = "SELECT * FROM candidates ORDER BY created_at DESC"
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        return cursor.fetchall()
    finally:
        conn.close()


def search_candidates(
    search: str = "",
    status: str = "",
    experience: str = "",
    skills: list[str] | None = None,
) -> list[dict]:
    """
    Filter candidates by:
      - search  : free-text match on name / role / skills column
      - status  : exact match  (e.g. "Active")
      - experience : exact match (e.g. "3-5")
      - skills  : list of skill strings — candidate must have ALL of them
                  (each checked with LIKE against the skills column)
    """
    conditions = []
    params = []

    if search:
        conditions.append(
            "(full_name LIKE %s OR role LIKE %s OR skills LIKE %s)"
        )
        like = f"%{search}%"
        params.extend([like, like, like])

    if status:
        conditions.append("status = %s")
        params.append(status)

    if experience:
        conditions.append("experience = %s")
        params.append(experience)

    # Each selected skill must appear somewhere in the skills column
    for skill in (skills or []):
        skill = skill.strip()
        if skill:
            conditions.append("skills LIKE %s")
            params.append(f"%{skill}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM candidates {where} ORDER BY created_at DESC"

    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def get_all_skills() -> list[str]:
    """
    Return a sorted, deduplicated list of every skill found across
    all candidate rows. Used to populate the skills filter dropdown.
    """
    sql = "SELECT skills FROM candidates WHERE skills IS NOT NULL AND skills != ''"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
    finally:
        conn.close()

    skill_set = set()
    for (raw,) in rows:
        for s in raw.split(","):
            s = s.strip()
            if s:
                skill_set.add(s)
    return sorted(skill_set, key=str.lower)


def get_candidate_by_id(candidate_id: int) -> dict | None:
    """Return a single candidate dict or None."""
    sql = "SELECT * FROM candidates WHERE id = %s"
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, (candidate_id,))
        return cursor.fetchone()
    finally:
        conn.close()


# ── UPDATE ────────────────────────────────────────────────────────────────────

def update_candidate(candidate_id: int, data: dict) -> bool:
    """
    Update an existing candidate.
    data keys same as add_candidate.
    Returns True on success.
    """
    sql = """
        UPDATE candidates SET
            full_name  = %(full_name)s,
            email      = %(email)s,
            phone      = %(phone)s,
            role       = %(role)s,
            experience = %(experience)s,
            location   = %(location)s,
            skills     = %(skills)s,
            status     = %(status)s,
            notes      = %(notes)s
        WHERE id = %(id)s
    """
    data["id"] = candidate_id
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, data)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def update_status(candidate_id: int, new_status: str) -> bool:
    """Quick status-only update (e.g. from the card view)."""
    sql = "UPDATE candidates SET status = %s WHERE id = %s"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (new_status, candidate_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── DELETE ────────────────────────────────────────────────────────────────────

def delete_candidate(candidate_id: int) -> bool:
    """Permanently remove a candidate row. Returns True on success."""
    sql = "DELETE FROM candidates WHERE id = %s"
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, (candidate_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ── STATS ─────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Return counts per status for the dashboard header."""
    sql = "SELECT status, COUNT(*) as cnt FROM candidates GROUP BY status"
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        rows = cursor.fetchall()
        stats = {"total": 0, "Active": 0,
                 "Reviewing": 0, "Hired": 0, "Rejected": 0}
        for r in rows:
            stats[r["status"]] = r["cnt"]
            stats["total"] += r["cnt"]
        return stats
    finally:
        conn.close()


def get_upcoming_interviews():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, full_name, email, role, status,
               interview_date, interview_time, interview_mode
        FROM candidates
        WHERE status = 'Active'
          AND interview_date IS NOT NULL
          AND interview_date != ''
        ORDER BY interview_date ASC
        LIMIT 5
    """)

    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data
