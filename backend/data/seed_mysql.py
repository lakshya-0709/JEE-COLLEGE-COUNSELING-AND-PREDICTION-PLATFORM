"""
MySQL Database Setup & Seeding Script
Reads processed JoSAA JSON cutoff data and populates MySQL database.
"""

import json
import os
import sys
import time

# Ensure UTF-8 output encoding for Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import pymysql
except ImportError:
    print("[ERROR] pymysql is not installed. Run 'pip install pymysql sqlalchemy' first.")
    sys.exit(1)

# Add parent directory to path to import config
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BASE_DIR)

from app.config import (
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB,
    CUTOFF_DATA_PATH
)


def get_server_connection():
    """Connect to MySQL server without specifying database."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )


def get_db_connection():
    """Connect directly to the specific MySQL database."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        autocommit=True,
        cursorclass=pymysql.cursors.DictCursor
    )


def create_database_and_table():
    """Create database and normalized 3NF tables with indexes and foreign keys."""
    print(f"[*] Connecting to MySQL server at {MYSQL_HOST}:{MYSQL_PORT}...")
    conn = get_server_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"  [OK] Database `{MYSQL_DB}` is ready.")
    finally:
        conn.close()

    print("[*] Creating 3NF Normalized schema and tables...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Disable foreign key checks for clean recreation
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("DROP TABLE IF EXISTS `cutoffs`;")
            cursor.execute("DROP TABLE IF EXISTS `institute_programs`;")
            cursor.execute("DROP TABLE IF EXISTS `programs`;")
            cursor.execute("DROP TABLE IF EXISTS `institutes`;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            # 1. Institutes Table
            create_institutes_sql = """
            CREATE TABLE `institutes` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `institute` VARCHAR(500) NOT NULL UNIQUE,
                `institute_short` VARCHAR(255) NOT NULL,
                `institute_type` VARCHAR(50) NOT NULL,
                `state` VARCHAR(100) NOT NULL,
                INDEX `idx_inst_type` (`institute_type`),
                INDEX `idx_inst_short` (`institute_short`),
                INDEX `idx_state` (`state`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """

            # 2. Programs Table
            create_programs_sql = """
            CREATE TABLE `programs` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `program` VARCHAR(500) NOT NULL UNIQUE,
                `branch_full` VARCHAR(500) NOT NULL,
                `branch_short` VARCHAR(255) NOT NULL,
                `degree_type` VARCHAR(100) NOT NULL,
                `duration` INT NOT NULL,
                INDEX `idx_branch_short` (`branch_short`),
                INDEX `idx_degree_type` (`degree_type`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """

            # 3. Institute Programs Junction Table
            create_inst_programs_sql = """
            CREATE TABLE `institute_programs` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `institute_id` INT NOT NULL,
                `program_id` INT NOT NULL,
                FOREIGN KEY (`institute_id`) REFERENCES `institutes`(`id`) ON DELETE CASCADE,
                FOREIGN KEY (`program_id`) REFERENCES `programs`(`id`) ON DELETE CASCADE,
                UNIQUE KEY `uk_inst_prog` (`institute_id`, `program_id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """

            # 4. Cutoff Ranks Transactional Fact Table
            create_cutoffs_sql = """
            CREATE TABLE `cutoffs` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `inst_program_id` INT NOT NULL,
                `quota` VARCHAR(50) NOT NULL,
                `seat_type` VARCHAR(50) NOT NULL,
                `gender` VARCHAR(100) NOT NULL,
                `opening_rank` INT NOT NULL,
                `closing_rank` INT NOT NULL,
                `year` INT NOT NULL,
                `round` INT NOT NULL,
                FOREIGN KEY (`inst_program_id`) REFERENCES `institute_programs`(`id`) ON DELETE CASCADE,
                INDEX `idx_year_round` (`year`, `round`),
                INDEX `idx_filters` (`seat_type`, `gender`, `quota`),
                INDEX `idx_lookup` (`inst_program_id`, `seat_type`, `gender`, `quota`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """

            cursor.execute(create_institutes_sql)
            cursor.execute(create_programs_sql)
            cursor.execute(create_inst_programs_sql)
            cursor.execute(create_cutoffs_sql)
            print("  [OK] 4 Normalized 3NF tables (`institutes`, `programs`, `institute_programs`, `cutoffs`) created with indexes & foreign keys.")
    finally:
        conn.close()


def seed_data(batch_size=5000):
    """Seed data from cutoffs_processed.json into normalized MySQL tables."""
    if not os.path.exists(CUTOFF_DATA_PATH):
        print(f"[ERROR] Data file not found at {CUTOFF_DATA_PATH}. Run process_data.py first.")
        return

    print(f"[*] Loading data from {CUTOFF_DATA_PATH}...")
    with open(CUTOFF_DATA_PATH, 'r', encoding='utf-8') as f:
        records = json.load(f)

    total_records = len(records)
    print(f"[*] Loaded {total_records:,} records. Preparing normalized 3NF relational insertion...")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check existing count in cutoffs table
            cursor.execute("SELECT COUNT(*) AS total FROM `cutoffs`;")
            existing_count = cursor.fetchone()["total"]
            
            if existing_count >= total_records:
                print(f"[INFO] MySQL table `cutoffs` already contains {existing_count:,} records.")
                user_choice = input("Do you want to re-seed (truncate & replace)? (y/n): ").strip().lower() if sys.stdin.isatty() else 'y'
                if user_choice != 'y':
                    print("  Skipping data insertion.")
                    return

            print("  [*] Truncating existing normalized tables...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            cursor.execute("TRUNCATE TABLE `cutoffs`;")
            cursor.execute("TRUNCATE TABLE `institute_programs`;")
            cursor.execute("TRUNCATE TABLE `programs`;")
            cursor.execute("TRUNCATE TABLE `institutes`;")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            start_time = time.time()

            # 1. Populate institutes table
            print("  [1/4] Seeding `institutes` table...")
            inst_dict = {}  # institute -> (institute_short, institute_type, state)
            for r in records:
                if r["institute"] not in inst_dict:
                    inst_dict[r["institute"]] = (r["institute_short"], r["institute_type"], r["state"])

            inst_insert_sql = "INSERT INTO `institutes` (institute, institute_short, institute_type, state) VALUES (%s, %s, %s, %s)"
            inst_values = [(inst, v[0], v[1], v[2]) for inst, v in inst_dict.items()]
            cursor.executemany(inst_insert_sql, inst_values)
            print(f"      Inserted {len(inst_values):,} distinct institutes.")

            # Fetch institute_id map
            cursor.execute("SELECT id, institute FROM `institutes`;")
            inst_map = {row["institute"]: row["id"] for row in cursor.fetchall()}

            # 2. Populate programs table
            print("  [2/4] Seeding `programs` table...")
            prog_dict = {}  # program -> (branch_full, branch_short, degree_type, duration)
            for r in records:
                if r["program"] not in prog_dict:
                    prog_dict[r["program"]] = (r["branch_full"], r["branch_short"], r["degree_type"], r["duration"])

            prog_insert_sql = "INSERT INTO `programs` (program, branch_full, branch_short, degree_type, duration) VALUES (%s, %s, %s, %s, %s)"
            prog_values = [(prog, v[0], v[1], v[2], v[3]) for prog, v in prog_dict.items()]
            cursor.executemany(prog_insert_sql, prog_values)
            print(f"      Inserted {len(prog_values):,} distinct academic programs.")

            # Fetch program_id map
            cursor.execute("SELECT id, program FROM `programs`;")
            prog_map = {row["program"]: row["id"] for row in cursor.fetchall()}

            # 3. Populate institute_programs junction table
            print("  [3/4] Seeding `institute_programs` junction table...")
            inst_prog_set = set()
            for r in records:
                i_id = inst_map[r["institute"]]
                p_id = prog_map[r["program"]]
                inst_prog_set.add((i_id, p_id))

            inst_prog_insert_sql = "INSERT INTO `institute_programs` (institute_id, program_id) VALUES (%s, %s)"
            inst_prog_values = list(inst_prog_set)
            cursor.executemany(inst_prog_insert_sql, inst_prog_values)
            print(f"      Inserted {len(inst_prog_values):,} institute-program links.")

            # Fetch inst_program_id map
            cursor.execute("SELECT id, institute_id, program_id FROM `institute_programs`;")
            inst_prog_map = {(row["institute_id"], row["program_id"]): row["id"] for row in cursor.fetchall()}

            # 4. Populate cutoffs transactional fact table
            print("  [4/4] Seeding `cutoffs` fact table...")
            cutoff_insert_sql = """
            INSERT INTO `cutoffs` (
                inst_program_id, quota, seat_type, gender, opening_rank, closing_rank, year, round
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            cutoff_values = [
                (
                    inst_prog_map[(inst_map[r["institute"]], prog_map[r["program"]])],
                    r["quota"], r["seat_type"], r["gender"],
                    r["opening_rank"], r["closing_rank"], r["year"], r["round"]
                )
                for r in records
            ]

            inserted = 0
            for i in range(0, len(cutoff_values), batch_size):
                batch = cutoff_values[i:i + batch_size]
                cursor.executemany(cutoff_insert_sql, batch)
                inserted += len(batch)
                print(f"      [>] Inserted {inserted:,} / {len(cutoff_values):,} cutoff records...")

            elapsed = time.time() - start_time
            print(f"[SUCCESS] Successfully seeded 4-table normalized 3NF schema ({total_records:,} cutoffs) in {elapsed:.2f} seconds!")
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  MySQL 3NF Normalized Setup & Data Seeder")
    print("=" * 60)
    try:
        create_database_and_table()
        seed_data()
        print("\n[OK] MySQL 3NF Normalized Database setup & seeding complete!")
    except Exception as e:
        print(f"\n[ERROR] Error during MySQL database setup: {e}")
        print("\nPlease ensure MySQL Server is running and password matches your .env / config.py settings.")
        print(f"Configured Connection: Host={MYSQL_HOST}, Port={MYSQL_PORT}, User={MYSQL_USER}")

