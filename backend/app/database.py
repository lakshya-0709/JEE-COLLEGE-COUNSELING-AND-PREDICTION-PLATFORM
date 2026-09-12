"""
Data layer — manages data access using MySQL database with JSON fallback.
Provides unified query interface for both MySQL DB and in-memory DataStore.
"""

import json
import os
from app.config import (
    CUTOFF_DATA_PATH, METADATA_PATH,
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, USE_MYSQL
)

# Try importing pymysql
try:
    import pymysql
    HAS_PYMYSQL = True
except ImportError:
    HAS_PYMYSQL = False


# Last round number per year (JoSAA uses 6 rounds for 2021-2023, 5 for 2024)
LAST_ROUNDS = {2021: 6, 2022: 6, 2023: 6, 2024: 5}


class DataStore:
    """Unified Data store with MySQL support and JSON fallback."""

    def __init__(self):
        self.cutoffs: list[dict] = []
        self.metadata: dict = {}
        self._loaded = False
        self.use_mysql = False
        self.mysql_status = "Not initialized"

    def _get_db_connection(self):
        """Helper to create a MySQL database connection."""
        return pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor
        )

    def load(self):
        """Load data from MySQL or fallback to JSON files."""
        if self._loaded:
            return

        # Always load JSON into memory as reliable backup
        if os.path.exists(CUTOFF_DATA_PATH):
            with open(CUTOFF_DATA_PATH, 'r', encoding='utf-8') as f:
                self.cutoffs = json.load(f)

        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)

        # Try connecting to MySQL if enabled
        if USE_MYSQL and HAS_PYMYSQL:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) AS total FROM `cutoffs`;")
                    count = cursor.fetchone()["total"]
                    if count > 0:
                        self.use_mysql = True
                        self.mysql_status = f"Connected (MySQL: {count:,} records)"
                        print(f"[OK] DataStore initialized with MySQL Database ({count:,} records).")
                    else:
                        self.mysql_status = "Table empty (using JSON fallback)"
                        print("[WARNING] MySQL `cutoffs` table is empty. Falling back to in-memory JSON data.")
                conn.close()
            except Exception as e:
                self.use_mysql = False
                self.mysql_status = f"Disconnected/Offline: {e}"
                print(f"[WARNING] MySQL connection unverified ({e}). Using in-memory JSON fallback.")

        else:
            self.use_mysql = False
            self.mysql_status = "Disabled (using JSON fallback)"

        self._loaded = True
        print(f"Loaded {len(self.cutoffs):,} cutoff records into memory backup.")

    def get_last_round_data(self) -> list[dict]:
        """Get only the last round data per year (for predictions) using 3NF JOINs."""
        if self.use_mysql:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    # Construct round filter
                    conditions = [f"(c.year = {y} AND c.round = {r})" for y, r in LAST_ROUNDS.items()]
                    where_clause = " OR ".join(conditions)
                    sql = f"""
                    SELECT 
                        c.id, i.institute, i.institute_short, i.institute_type, i.state,
                        p.program, p.branch_full, p.branch_short, p.degree_type, p.duration,
                        c.quota, c.seat_type, c.gender, c.opening_rank, c.closing_rank, c.year, c.round
                    FROM `cutoffs` c
                    JOIN `institute_programs` ip ON c.inst_program_id = ip.id
                    JOIN `institutes` i ON ip.institute_id = i.id
                    JOIN `programs` p ON ip.program_id = p.id
                    WHERE {where_clause};
                    """
                    cursor.execute(sql)
                    results = cursor.fetchall()
                conn.close()
                return results
            except Exception as e:
                print(f"MySQL query error in get_last_round_data: {e}. Falling back to JSON.")

        # JSON Fallback
        return [r for r in self.cutoffs if r["round"] == LAST_ROUNDS.get(r["year"], 6)]

    def query(self, **filters) -> list[dict]:
        """Query cutoff data with filters across normalized 3NF tables."""
        if self.use_mysql:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    inst_cols = {"institute", "institute_short", "institute_type", "state"}
                    prog_cols = {"program", "branch_full", "branch_short", "degree_type", "duration"}

                    conditions = []
                    params = []
                    for key, val in filters.items():
                        if val is None:
                            continue
                        prefix = "i." if key in inst_cols else ("p." if key in prog_cols else "c.")
                        col_ref = f"{prefix}`{key}`"

                        if isinstance(val, list):
                            if len(val) > 0:
                                placeholders = ", ".join(["%s"] * len(val))
                                conditions.append(f"{col_ref} IN ({placeholders})")
                                params.extend(val)
                        else:
                            conditions.append(f"{col_ref} = %s")
                            params.append(val)

                    where_sql = (" WHERE " + " AND ".join(conditions)) if conditions else ""
                    sql = f"""
                    SELECT 
                        c.id, i.institute, i.institute_short, i.institute_type, i.state,
                        p.program, p.branch_full, p.branch_short, p.degree_type, p.duration,
                        c.quota, c.seat_type, c.gender, c.opening_rank, c.closing_rank, c.year, c.round
                    FROM `cutoffs` c
                    JOIN `institute_programs` ip ON c.inst_program_id = ip.id
                    JOIN `institutes` i ON ip.institute_id = i.id
                    JOIN `programs` p ON ip.program_id = p.id
                    {where_sql};
                    """
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
                conn.close()
                return results
            except Exception as e:
                print(f"MySQL query error in query(): {e}. Falling back to JSON.")

        # JSON Fallback
        results = self.cutoffs
        for key, value in filters.items():
            if value is None:
                continue
            if isinstance(value, list):
                if len(value) > 0:
                    results = [r for r in results if r.get(key) in value]
            else:
                results = [r for r in results if r.get(key) == value]
        return results

    def get_institutes(self, institute_type: str = None) -> list[dict]:
        """Get unique institutes with metadata from normalized `institutes` table."""
        if self.use_mysql:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    if institute_type:
                        sql = """
                        SELECT DISTINCT institute, institute_short, institute_type, state
                        FROM `institutes` WHERE institute_type = %s
                        ORDER BY institute_short;
                        """
                        cursor.execute(sql, (institute_type,))
                    else:
                        sql = """
                        SELECT DISTINCT institute, institute_short, institute_type, state
                        FROM `institutes` ORDER BY institute_short;
                        """
                        cursor.execute(sql)
                    results = cursor.fetchall()
                conn.close()
                return results
            except Exception as e:
                print(f"MySQL query error in get_institutes: {e}. Falling back to JSON.")

        # JSON Fallback
        seen = set()
        institutes = []
        for r in self.cutoffs:
            if r["institute"] not in seen:
                if institute_type and r["institute_type"] != institute_type:
                    continue
                seen.add(r["institute"])
                institutes.append({
                    "institute": r["institute"],
                    "institute_short": r["institute_short"],
                    "institute_type": r["institute_type"],
                    "state": r["state"],
                })
        return sorted(institutes, key=lambda x: x["institute_short"])

    def get_branches(self, institute_types: list[str] = None) -> list[str]:
        """Get unique normalized branch names from normalized `programs` table."""
        if self.use_mysql:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    if institute_types:
                        placeholders = ", ".join(["%s"] * len(institute_types))
                        sql = f"""
                        SELECT DISTINCT p.branch_short 
                        FROM `programs` p
                        JOIN `institute_programs` ip ON p.id = ip.program_id
                        JOIN `institutes` i ON ip.institute_id = i.id
                        WHERE i.institute_type IN ({placeholders}) 
                        ORDER BY p.branch_short;
                        """
                        cursor.execute(sql, institute_types)
                    else:
                        sql = "SELECT DISTINCT branch_short FROM `programs` ORDER BY branch_short;"
                        cursor.execute(sql)
                    rows = cursor.fetchall()
                conn.close()
                return [r["branch_short"] for r in rows]
            except Exception as e:
                print(f"MySQL query error in get_branches: {e}. Falling back to JSON.")

        # JSON Fallback
        if institute_types:
            return sorted(set(r["branch_short"] for r in self.cutoffs if r["institute_type"] in institute_types))
        return sorted(set(r["branch_short"] for r in self.cutoffs))

    def get_programs_for_institute(self, institute: str) -> list[dict]:
        """Get all programs offered by an institute."""
        if self.use_mysql:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    sql = """
                    SELECT DISTINCT p.program, p.branch_full, p.branch_short, p.degree_type
                    FROM `programs` p
                    JOIN `institute_programs` ip ON p.id = ip.program_id
                    JOIN `institutes` i ON ip.institute_id = i.id
                    WHERE i.institute = %s 
                    ORDER BY p.branch_short;
                    """
                    cursor.execute(sql, (institute,))
                    results = cursor.fetchall()
                conn.close()
                return results
            except Exception as e:
                print(f"MySQL query error in get_programs_for_institute: {e}. Falling back to JSON.")

        # JSON Fallback
        seen = set()
        programs = []
        for r in self.cutoffs:
            if r["institute"] == institute and r["program"] not in seen:
                seen.add(r["program"])
                programs.append({
                    "program": r["program"],
                    "branch_full": r["branch_full"],
                    "branch_short": r["branch_short"],
                    "degree_type": r["degree_type"],
                })
        return sorted(programs, key=lambda x: x["branch_short"])

    def get_trend(self, institute: str, program: str,
                  seat_type: str = "OPEN", gender: str = "Gender-Neutral",
                  quota: str = "AI") -> list[dict]:
        """Get year-wise cutoff trend for a specific combo from normalized 3NF schema."""
        if self.use_mysql:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    round_conditions = [f"(c.year = {y} AND c.round = {r})" for y, r in LAST_ROUNDS.items()]
                    round_clause = " OR ".join(round_conditions)
                    sql = f"""
                    SELECT c.year, c.opening_rank, c.closing_rank, c.round
                    FROM `cutoffs` c
                    JOIN `institute_programs` ip ON c.inst_program_id = ip.id
                    JOIN `institutes` i ON ip.institute_id = i.id
                    JOIN `programs` p ON ip.program_id = p.id
                    WHERE i.institute = %s AND p.program = %s AND c.seat_type = %s
                      AND c.gender = %s AND c.quota = %s AND ({round_clause})
                    ORDER BY c.year;
                    """
                    cursor.execute(sql, (institute, program, seat_type, gender, quota))
                    results = cursor.fetchall()
                conn.close()
                return results
            except Exception as e:
                print(f"MySQL query error in get_trend: {e}. Falling back to JSON.")

        # JSON Fallback
        results = [
            {"year": r["year"], "opening_rank": r["opening_rank"],
             "closing_rank": r["closing_rank"], "round": r["round"]}
            for r in self.cutoffs
            if (r["institute"] == institute and r["program"] == program and
                r["seat_type"] == seat_type and r["gender"] == gender and
                r["quota"] == quota and r["round"] == LAST_ROUNDS.get(r["year"], 6))
        ]
        return sorted(results, key=lambda x: x["year"])

    def search_institutes(self, query: str) -> list[dict]:
        """Search institutes by name (for autocomplete) from normalized `institutes` table."""
        if self.use_mysql:
            try:
                conn = self._get_db_connection()
                with conn.cursor() as cursor:
                    search_pattern = f"%{query.lower()}%"
                    sql = """
                    SELECT DISTINCT institute, institute_short, institute_type, state
                    FROM `institutes`
                    WHERE LOWER(institute) LIKE %s OR LOWER(institute_short) LIKE %s
                    ORDER BY institute_short LIMIT 20;
                    """
                    cursor.execute(sql, (search_pattern, search_pattern))
                    results = cursor.fetchall()
                conn.close()
                return results
            except Exception as e:
                print(f"MySQL query error in search_institutes: {e}. Falling back to JSON.")

        # JSON Fallback
        query_lower = query.lower()
        seen = set()
        results = []
        for r in self.cutoffs:
            if r["institute"] not in seen:
                if (query_lower in r["institute"].lower() or
                    query_lower in r["institute_short"].lower()):
                    seen.add(r["institute"])
                    results.append({
                        "institute": r["institute"],
                        "institute_short": r["institute_short"],
                        "institute_type": r["institute_type"],
                        "state": r["state"],
                    })
        return sorted(results, key=lambda x: x["institute_short"])[:20]


# Global singleton
data_store = DataStore()

