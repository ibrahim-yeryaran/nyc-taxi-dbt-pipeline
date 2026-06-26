"""
load_raw.py
-----------
ELT'in "EL" kısmı: NYC Taxi verisini public URL'lerden çekip DuckDB
içindeki `raw` şemaya ham haliyle yükler. Dönüşümler (T) dbt'de yapılır.

DuckDB'nin httpfs eklentisi parquet/csv'yi doğrudan URL'den okuyabildiği
için ayrı bir indirme kütüphanesine gerek yoktur.

Çalıştırma:
    python extract_load/load_raw.py
"""

import logging
from pathlib import Path

import duckdb

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("load_raw")

# ── Ayarlar ────────────────────────────────────────────────────────────────
# Ambar dosyası (gitignore'lu). Repo kökünden göreceli yol.
DB_PATH = Path(__file__).resolve().parent.parent / "warehouse" / "nyc_taxi.duckdb"

# Yüklenecek aylar. Küçük tutuyoruz; istediğin kadar ay ekleyebilirsin.
MONTHS = ["2023-01"]

# NYC TLC public veri kaynakları (API key gerektirmez)
TRIP_URL_TEMPLATE = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{month}.parquet"
ZONE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"


def load_zones(con: duckdb.DuckDBPyConnection) -> None:
    """Bölge arama tablosunu (dimension kaynağı) raw şemaya yükler."""
    log.info("Bölge tablosu yükleniyor: %s", ZONE_URL)
    con.execute(
        """
        CREATE OR REPLACE TABLE raw.taxi_zones AS
        SELECT * FROM read_csv_auto(?, header = true)
        """,
        [ZONE_URL],
    )
    count = con.sql("SELECT count(*) FROM raw.taxi_zones").fetchone()[0]
    log.info("raw.taxi_zones yüklendi → %s satır", f"{count:,}")


def load_trips(con: duckdb.DuckDBPyConnection, months: list[str]) -> None:
    """Belirtilen aylara ait yolculuk verisini raw.yellow_trips tablosuna yükler."""
    # Tabloyu her çalıştırmada sıfırdan kuruyoruz (idempotent: tekrar çalışınca
    # mükerrer satır oluşmaz). Büyük projede artımlı (incremental) yüklenir.
    first = True
    for month in months:
        url = TRIP_URL_TEMPLATE.format(month=month)
        log.info("Yolculuk verisi yükleniyor (%s): %s", month, url)

        # filename=true → her satırın hangi kaynak dosyadan geldiğini saklar (izlenebilirlik)
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
    log.info("raw.yellow_trips yüklendi → %s satır", f"{count:,}")


def run() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.info("DuckDB ambarına bağlanılıyor: %s", DB_PATH)
    con = duckdb.connect(str(DB_PATH))
    try:
        # Uzaktaki dosyaları okumak için httpfs eklentisi
        con.execute("INSTALL httpfs; LOAD httpfs;")
        con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

        load_zones(con)
        load_trips(con, MONTHS)

        log.info("✅ Ham yükleme tamamlandı.")
    finally:
        con.close()


if __name__ == "__main__":
    run()
