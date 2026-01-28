# savetodatabase.py
import hashlib
import os
from typing import Optional

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()


# ------------------ DB CONNECT ------------------
def get_pg_conn():
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "5433"))
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    if not all([dbname, user, password]):
        raise ValueError("DB_NAME, DB_USER, DB_PASSWORD .env ichida bo‘lishi shart")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
    )


# ------------------ TABLE (PostgreSQL) ------------------
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS job_listings (
    id BIGSERIAL PRIMARY KEY,
    posted_date TEXT,
    job_title_from_list TEXT,
    job_title TEXT,
    company TEXT,
    company_logo_url TEXT,
    country TEXT,
    location TEXT,
    skills TEXT,
    salary_info TEXT,
    source TEXT,
    row_hash TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
"""

# indexlar tezlik uchun (optional, lekin yaxshi)
CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_job_listings_company ON job_listings (company);
CREATE INDEX IF NOT EXISTS idx_job_listings_country ON job_listings (country);
CREATE INDEX IF NOT EXISTS idx_job_listings_source ON job_listings (source);
"""


def _safe_str(x) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, float) and pd.isna(x):
        return None
    s = str(x)
    # illegal chars ni olib tashlash
    s = "".join(c for c in s if ord(c) >= 32)
    return s.strip() if s.strip() != "" else None


def _make_row_hash(row: dict) -> str:
    """
    Dublikatni oldini olish uchun barqaror hash.
    Eng ko‘p uchraydigan fields asosida.
    """
    parts = [
        row.get("posted_date") or "",
        row.get("job_title_from_list") or "",
        row.get("job_title") or "",
        row.get("company") or "",
        row.get("country") or "",
        row.get("location") or "",
        row.get("source") or "",
    ]
    raw = "|".join(p.lower().strip() for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
        cur.execute(CREATE_INDEXES_SQL)
    conn.commit()


def save_to_postgres(df: pd.DataFrame, table_name: str = "job_listings") -> dict:
    """
    final_df ni Postgresga yozadi.
    - table create: bor bo‘lmasa yaratadi
    - bulk insert: tez
    - duplicate: row_hash UNIQUE + ON CONFLICT DO NOTHING
    """
    if df is None or df.empty:
        print("⚠️ DB ga yozilmadi — DataFrame bo‘sh")
        return {"inserted": 0, "skipped": 0, "total": 0}

    # Kutiladigan column mapping (seniki bilan mos)
    col_map = {
        "Posted_date": "posted_date",
        "Job Title from List": "job_title_from_list",
        "Job Title": "job_title",
        "Company": "company",
        "Company Logo URL": "company_logo_url",
        "Country": "country",
        "Location": "location",
        "Skills": "skills",
        "Salary Info": "salary_info",
        "Source": "source",
    }

    # df ichida qaysi columnlar borligini tekshirib, rename qilamiz
    work = df.copy()
    work = work.rename(columns={k: v for k, v in col_map.items() if k in work.columns})

    required = [
        "posted_date",
        "job_title_from_list",
        "job_title",
        "company",
        "company_logo_url",
        "country",
        "location",
        "skills",
        "salary_info",
        "source",
    ]

    # yo‘q columnlar bo‘lsa, None qilib yaratib qo‘yamiz (krasivo ishlasin)
    for c in required:
        if c not in work.columns:
            work[c] = None

    # faqat kerakli columnlarni olamiz
    work = work[required]

    # data tozalash + row_hash
    rows = []
    for _, r in work.iterrows():
        row = {c: _safe_str(r[c]) for c in required}
        row_hash = _make_row_hash(row)

        rows.append(
            (
                row["posted_date"],
                row["job_title_from_list"],
                row["job_title"],
                row["company"],
                row["company_logo_url"],
                row["country"],
                row["location"],
                row["skills"],
                row["salary_info"],
                row["source"],
                row_hash,
            )
        )

    conn = get_pg_conn()
    try:
        ensure_table(conn)

        insert_sql = f"""
        INSERT INTO {table_name} (
            posted_date, job_title_from_list, job_title, company, company_logo_url,
            country, location, skills, salary_info, source, row_hash
        ) VALUES %s
        ON CONFLICT (row_hash) DO NOTHING;
        """

        before = None
        after = None

        with conn.cursor() as cur:
            # count uchun inserted ni taxminiy hisoblaymiz:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            before = cur.fetchone()[0]

            execute_values(cur, insert_sql, rows, page_size=1000)

            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            after = cur.fetchone()[0]

        conn.commit()

        inserted = max(0, after - before)
        total = len(rows)
        skipped = total - inserted

        print(f"✅ Postgresga yozildi: inserted={inserted}, skipped(duplicate)={skipped}, total={total}")
        return {"inserted": inserted, "skipped": skipped, "total": total}

    finally:
        try:
            conn.close()
        except Exception:
            pass


def savetodb(job_data, conn):
    try:
        cursor = conn.cursor()

        create_table_query = """
        IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'JobListings')
        BEGIN
            CREATE TABLE JobListings (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    Posted_date NVARCHAR(100),
    Job_Title_from_List NVARCHAR(255),
    Job_Title NVARCHAR(255),
    Company NVARCHAR(255),
    Company_Logo_URL NVARCHAR(MAX),
    Country NVARCHAR(50),
    Location NVARCHAR(255),
    Skills NVARCHAR(MAX),
    Salary_Info NVARCHAR(255),
    Source NVARCHAR(255)
)

        END
        """
        cursor.execute(create_table_query)
        conn.commit()

        # Insert data into the table
        insert_query = """
        INSERT INTO JobListings (Posted_date, Job_Title_from_List, Job_Title, 
                         Company, Company_Logo_URL, Country, Location, 
                         Skills, Salary_Info, Source)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """

        for idx, job in job_data.iterrows():
            try:
                cursor.execute(insert_query,
                               job['Posted_date'],
                               job['Job Title from List'],
                               job['Job Title'],
                               job['Company'],
                               job['Company Logo URL'],
                               job['Country'],
                               job['Location'],
                               job['Skills'],
                               job['Salary Info'],
                               job['Source'])
            except Exception as row_error:
                print(f"Failed to insert row {idx}: {row_error}")

        conn.commit()
        print("Data saved to SQL Server")

    except Exception as e:
        print(f"Failed to save data to SQL Server: {e}")

    finally:
        cursor.close()
        conn.close()


def save_to_csv(df, filename="job_results.csv"):
    if df.empty:
        print("⚠️ CSV saqlanmadi — DataFrame bo‘sh")
        return
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"📁 CSV saqlandi → {filename}")
