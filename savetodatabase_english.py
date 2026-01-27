# savetodatabase_english.py
import hashlib
import os
from typing import Optional, Dict

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

load_dotenv()


# =========================
# COUNTRY -> COUNTRY_CODE (faqat shu list bo‘yicha)
# =========================
COUNTRY_CODE_MAP: Dict[str, str] = {
    "Japan": "JP",
    "UK": "GB",
    "Germany": "DE",
    "Poland": "PL",
    "France": "FR",
    "Switzerland": "CH",
    "London": "GB",
    "Philippines": "PH",
    "United States": "US",
    "China": "CN",
    "Dubai": "AE",
    "Abu Dhabi": "AE",
    "Uzbekistan": "UZB",
    "Kazakhstan": "KZ",
}

ALLOWED_COUNTRIES = set(COUNTRY_CODE_MAP.keys())


def normalize_country_name(x: Optional[str]) -> Optional[str]:
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None

    # case-insensitive match
    for k in COUNTRY_CODE_MAP.keys():
        if s.lower() == k.lower():
            return k

    return s


def get_country_code(country: Optional[str]) -> Optional[str]:
    c = normalize_country_name(country)
    if c is None:
        return None
    return COUNTRY_CODE_MAP.get(c)


# =========================
# DB CONNECT
# =========================
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


# =========================
# TABLE
# =========================
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS job_lisntings (
    id BIGSERIAL PRIMARY KEY,
    posted_date TEXT,
    job_title_from_list TEXT,
    job_title TEXT,
    company TEXT,
    company_logo_url TEXT,
    country TEXT,
    country_code TEXT,
    location TEXT,
    skills TEXT,
    salary_info TEXT,
    source TEXT,
    row_hash TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT now()
);
"""

# agar table oldin yaratilgan bo‘lsa, country_code yo‘q bo‘lishi mumkin
ALTER_TABLE_SQL = """
ALTER TABLE job_listings
ADD COLUMN IF NOT EXISTS country_code TEXT;
"""

CREATE_INDEXES_SQL = """
CREATE INDEX IF NOT EXISTS idx_job_listings_company ON job_listings (company);
CREATE INDEX IF NOT EXISTS idx_job_listings_country ON job_listings (country);
CREATE INDEX IF NOT EXISTS idx_job_listings_country_code ON job_listings (country_code);
CREATE INDEX IF NOT EXISTS idx_job_listings_source ON job_listings (source);
"""


def _safe_str(x) -> Optional[str]:
    if x is None:
        return None
    if isinstance(x, float) and pd.isna(x):
        return None
    s = str(x)
    s = "".join(c for c in s if ord(c) >= 32)
    s = s.strip()
    return s if s else None


def _make_row_hash(row: dict) -> str:
    parts = [
        row.get("posted_date") or "",
        row.get("job_title_from_list") or "",
        row.get("job_title") or "",
        row.get("company") or "",
        row.get("country") or "",
        row.get("country_code") or "",
        row.get("location") or "",
        row.get("source") or "",
    ]
    raw = "|".join(p.lower().strip() for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
        cur.execute(ALTER_TABLE_SQL)
        cur.execute(CREATE_INDEXES_SQL)
    conn.commit()


def save_to_postgres(df: pd.DataFrame, table_name: str = "job_listings") -> dict:
    """
    DataFrame -> Postgres
    - faqat ALLOWED_COUNTRIES bo‘yicha filter
    - country_code qo‘shadi
    - row_hash UNIQUE + ON CONFLICT DO NOTHING
    """
    if df is None or df.empty:
        print("⚠️ DB ga yozilmadi — DataFrame bo‘sh")
        return {"inserted": 0, "skipped": 0, "total": 0}

    # sen result.csv ichida shu nomlar bo‘ladi:
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

    work = df.copy()
    work = work.rename(columns={k: v for k, v in col_map.items() if k in work.columns})

    required = [
        "posted_date",
        "job_title_from_list",
        "job_title",
        "company",
        "company_logo_url",
        "country",
        "country_code",
        "location",
        "skills",
        "salary_info",
        "source",
    ]

    for c in required:
        if c not in work.columns:
            work[c] = None

    # ✅ country normalize + filter
    work["country"] = work["country"].apply(normalize_country_name)
    work = work[work["country"].isin(ALLOWED_COUNTRIES)].copy()

    if work.empty:
        print("⚠️ Filterdan keyin data qolmadi (country allowed emas).")
        return {"inserted": 0, "skipped": 0, "total": 0}

    # ✅ country_code yaratish
    work["country_code"] = work["country"].apply(get_country_code)

    work = work[required]

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
                row["country_code"],
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
            country, country_code, location, skills, salary_info, source, row_hash
        ) VALUES %s
        ON CONFLICT (row_hash) DO NOTHING;
        """

        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            before = cur.fetchone()[0]

            execute_values(cur, insert_sql, rows, page_size=1000)

            cur.execute(f"SELECT COUNT(*) FROM {table_name};")
            after = cur.fetchone()[0]

        conn.commit()

        inserted = max(0, after - before)
        total = len(rows)
        skipped = total - inserted

        print(f"✅ Postgresga yozildi: inserted={inserted}, skipped={skipped}, total={total}")
        return {"inserted": inserted, "skipped": skipped, "total": total}

    finally:
        try:
            conn.close()
        except Exception:
            pass


def save_to_csv(df: pd.DataFrame, filename: str = "job_results.csv"):
    if df is None or df.empty:
        print("⚠️ CSV saqlanmadi — DataFrame bo‘sh")
        return
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"📁 CSV saqlandi → {filename}")
