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
    """Create database and table with indexes if they do not exist."""
    print(f"[*] Connecting to MySQL server at {MYSQL_HOST}:{MYSQL_PORT}...")
    conn = get_server_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"  [OK] Database `{MYSQL_DB}` is ready.")
    finally:
        conn.close()

    print("[*] Creating schema and table `cutoffs`...")
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS `cutoffs`;")
            create_table_sql = """

            CREATE TABLE IF NOT EXISTS `cutoffs` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `institute` VARCHAR(500) NOT NULL,
                `institute_short` VARCHAR(255) NOT NULL,
                `institute_type` VARCHAR(50) NOT NULL,
                `state` VARCHAR(100) NOT NULL,
                `program` VARCHAR(500) NOT NULL,
                `branch_full` VARCHAR(500) NOT NULL,
                `branch_short` VARCHAR(255) NOT NULL,
                `degree_type` VARCHAR(100) NOT NULL,
                `duration` INT NOT NULL,
                `quota` VARCHAR(50) NOT NULL,
                `seat_type` VARCHAR(50) NOT NULL,
                `gender` VARCHAR(100) NOT NULL,
                `opening_rank` INT NOT NULL,
                `closing_rank` INT NOT NULL,
                `year` INT NOT NULL,
                `round` INT NOT NULL,
                INDEX `idx_inst_type` (`institute_type`),
                INDEX `idx_inst_short` (`institute_short`),
                INDEX `idx_branch_short` (`branch_short`),
                INDEX `idx_seat_gender` (`seat_type`, `gender`),
                INDEX `idx_year_round` (`year`, `round`),
                INDEX `idx_lookup` (`institute_short`, `branch_short`, `seat_type`, `gender`, `quota`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """

            cursor.execute(create_table_sql)
            print("  [OK] Table `cutoffs` schema and indexes verified.")
    finally:
        conn.close()


def seed_data(batch_size=5000):
    """Seed data from cutoffs_processed.json into MySQL."""
    if not os.path.exists(CUTOFF_DATA_PATH):
        print(f"[ERROR] Data file not found at {CUTOFF_DATA_PATH}. Run process_data.py first.")
        return

    print(f"[*] Loading data from {CUTOFF_DATA_PATH}...")
    with open(CUTOFF_DATA_PATH, 'r', encoding='utf-8') as f:
        records = json.load(f)

    total_records = len(records)
    print(f"[*] Loaded {total_records:,} records. Preparing insertion into MySQL...")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check existing count
            cursor.execute("SELECT COUNT(*) AS total FROM `cutoffs`;")
            existing_count = cursor.fetchone()["total"]
            
            if existing_count >= total_records:
                print(f"[INFO] MySQL table `cutoffs` already contains {existing_count:,} records.")
                user_choice = input("Do you want to re-seed (truncate & replace)? (y/n): ").strip().lower() if sys.stdin.isatty() else 'y'
                if user_choice != 'y':
                    print("  Skipping data insertion.")
                    return

            print("  [*] Truncating existing `cutoffs` table...")
            cursor.execute("TRUNCATE TABLE `cutoffs`;")

            insert_sql = """
            INSERT INTO `cutoffs` (
                institute, institute_short, institute_type, state, program,
                branch_full, branch_short, degree_type, duration, quota,
                seat_type, gender, opening_rank, closing_rank, year, round
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """

            start_time = time.time()
            inserted = 0

            for i in range(0, total_records, batch_size):
                batch = records[i:i + batch_size]
                values = [
                    (
                        r["institute"], r["institute_short"], r["institute_type"], r["state"], r["program"],
                        r["branch_full"], r["branch_short"], r["degree_type"], r["duration"], r["quota"],
                        r["seat_type"], r["gender"], r["opening_rank"], r["closing_rank"], r["year"], r["round"]
                    )
                    for r in batch
                ]
                cursor.executemany(insert_sql, values)
                inserted += len(batch)
                print(f"  [>] Inserted {inserted:,} / {total_records:,} records...")

            elapsed = time.time() - start_time
            print(f"[SUCCESS] Successfully seeded {inserted:,} records into MySQL database in {elapsed:.2f} seconds!")
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  MySQL Setup & Data Seeder")
    print("=" * 60)
    try:
        create_database_and_table()
        seed_data()
        print("\n[OK] MySQL Database setup & seeding complete!")
    except Exception as e:
        print(f"\n[ERROR] Error during MySQL database setup: {e}")
        print("\nPlease ensure MySQL Server is running and password matches your .env / config.py settings.")
        print(f"Configured Connection: Host={MYSQL_HOST}, Port={MYSQL_PORT}, User={MYSQL_USER}")
