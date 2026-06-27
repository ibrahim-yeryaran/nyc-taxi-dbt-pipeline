"""
load_raw.py
-----------
The "EL" part of ELT: pulls NYC Taxi data from public URLs and loads it
raw into the `raw` schema in DuckDB. Transformations (T) are done in dbt.

DuckDB's httpfs extension can read parquet/csv directly from a URL, so no
separate download library is needed.

Run:
    python extract_load/load_raw.py
"""

import logging
from pathlib import Path

import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("load_raw")

# ── Settings ─────────────────────────────────────────────────────────────────
# Warehouse file (gitignored). Path relative to the repo root.
DB_PATH = Path(__file__).resolve().parent.parent / "warehouse" / "nyc_taxi.duckdb"

# Months to load. Kept small; add as many as you like.
MONTHS = ["2023-01"]

# NYC TLC public data sources (no API key required)
TRIP_URL_TEMPLATE = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet"
ZONE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def load_zones(con: duckdb.DuckDBPyConnection) -> None:
    """Load the zone lookup table (dimension source) into the raw schema."""
    log.info("Loading zone table: %s", ZONE_URL)
    con.execute(
        """
        CREATE OR REPLACE TABLE raw.taxi_zones AS
        SELECT * FROM read_csv_auto(?, header = true)
        """,
        [ZONE_URL],
    )
    count = con.sql("SELECT count(*) FROM raw.taxi_zones").fetchone()[0]
    log.info("raw.taxi_zones loaded → %s rows", f"{count:,}")


def load_trips(con: duckdb.DuckDBPyConnection, months: list[str]) -> None:
    """Load trip data for the given months into the raw.yellow_trips table."""
    # Rebuild the table from scratch on every run (idempotent: re-running
    # doesn't create duplicate rows). A larger project would load incrementally.
    first = True
    for month in months:
        url = TRIP_URL_TEMPLATE.format(month=month)
        log.info("Loading trip data (%s): %s", month, url)

        # filename=true → records which source file each row came from (traceability)
        select_sql = f"""
            SELECT *, '{month}' AS source_month
            FROM read_parquet('{url}', filename = true)
        """
        if first:
            con.execute(f"CREATE OR REPLACE TABLE raw.yellow_trips AS {select_sql}")
            first = False
        else:
            con.execute(f"INSERT INTO raw.yellow_trips {select_sql}")

    count = con.sql("SELECT count(*) FROM raw.yellow_trips").fetchone()[0]
    log.info("raw.yellow_trips loaded → %s rows", f"{count:,}")


def run() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.info("Connecting to the DuckDB warehouse: %s", DB_PATH)
    con = duckdb.connect(str(DB_PATH))
    try:
        # httpfs extension to read remote files
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

        load_zones(con)
        load_trips(con, MONTHS)

        log.info("✅ Raw load complete.")
    finally:
        con.close()


if __name__ == "__main__":
    run()
