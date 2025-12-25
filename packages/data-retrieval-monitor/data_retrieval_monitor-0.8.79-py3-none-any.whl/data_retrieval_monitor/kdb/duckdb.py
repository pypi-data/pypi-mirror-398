import os
import math
import duckdb
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.utils.validation import check_X_y
from gplearn.genetic import SymbolicClassifier
import gplearn.genetic as gp


# -----------------------------
# DuckDB helpers
# -----------------------------
def connect_duckdb(db_path: str,
                   memory_limit: str = "8GB",
                   temp_dir: str = "./duckdb_tmp",
                   threads: int = 8) -> duckdb.DuckDBPyConnection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    con = duckdb.connect(db_path)  # persistent DB helps with spilling/out-of-core
    con.execute(f"SET memory_limit='{memory_limit}';")   # controls RAM use  [oai_citation:1‡DuckDB](https://duckdb.org/2024/07/09/memory-management.html?utm_source=chatgpt.com)
    con.execute(f"SET temp_directory='{temp_dir}';")     # where spill files go  [oai_citation:2‡DuckDB](https://duckdb.org/docs/stable/configuration/pragmas.html?utm_source=chatgpt.com)
    con.execute(f"SET threads={threads};")
    con.execute("PRAGMA enable_progress_bar=true;")
    return con


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


# -----------------------------
# 1) Synthetic data generation (chunked, on-disk)
# -----------------------------
def generate_trades_parquet(con,
                           out_dir: str,
                           n_rows: int = 300_000_000,
                           n_symbols: int = 10_000,
                           n_buckets: int = 128,
                           chunk_rows: int = 10_000_000,
                           start_ts: str = "2025-01-02 09:30:00"):
    """
    Trades schema:
      trade_id BIGINT
      sym      INTEGER
      ts       TIMESTAMP
      trade_date DATE
      bucket   INTEGER
      is_buy   UTINYINT (0/1)
      size     INTEGER
      price    DOUBLE
    """
    _ensure_dir(out_dir)
    n_chunks = math.ceil(n_rows / chunk_rows)

    for k in range(n_chunks):
        start = k * chunk_rows
        end = min((k + 1) * chunk_rows, n_rows)
        # Each chunk writes into hive-style partitions bucket=.../trade_date=...
        sql = f"""
        COPY (
          SELECT
            i::BIGINT AS trade_id,
            (i % {n_symbols})::INTEGER AS sym,
            -- spread trades across a "day" worth of milliseconds (6.5h = 23,400,000ms)
            (TIMESTAMP '{start_ts}' + ((i % 23400000)::BIGINT) * INTERVAL 1 MILLISECOND) AS ts,
            CAST((TIMESTAMP '{start_ts}' + ((i % 23400000)::BIGINT) * INTERVAL 1 MILLISECOND) AS DATE) AS trade_date,
            ((i % {n_symbols}) % {n_buckets})::INTEGER AS bucket,

            -- deterministic-ish pseudo randomness from hash(i)  [oai_citation:3‡DuckDB](https://duckdb.org/docs/stable/sql/functions/utility.html?utm_source=chatgpt.com)
            CASE WHEN (hash(i) % 2)=0 THEN 1 ELSE 0 END::UTINYINT AS is_buy,
            (1 + (hash(i*17) % 1000))::INTEGER AS size,
            (100.0
             + ((hash(i*101) % 20000)::DOUBLE) / 100.0
             + CASE WHEN (hash(i*7) % 2)=0 THEN -1 ELSE 1 END * ((hash(i*13) % 1000)::DOUBLE)/10000.0
            )::DOUBLE AS price
          FROM range({start}, {end}) t(i)
        )
        TO '{out_dir}'
        (FORMAT PARQUET,
         COMPRESSION ZSTD,
         OVERWRITE 1,
         PARTITION_BY (bucket, trade_date),
         ROW_GROUP_SIZE 250000,
         FILENAME_PATTERN 'trades_{k}_{{i}}.parquet');
        """
        con.execute(sql)
    print(f"[OK] trades written to {out_dir}")


def generate_quotes_parquet(con,
                           out_dir: str,
                           n_rows: int = 60_000_000,
                           n_symbols: int = 10_000,
                           n_buckets: int = 128,
                           chunk_rows: int = 5_000_000,
                           start_ts: str = "2025-01-02 09:30:00"):
    """
    Quotes schema:
      quote_id BIGINT
      sym      INTEGER
      ts       TIMESTAMP
      quote_date DATE
      bucket   INTEGER
      mid      DOUBLE
      bid      DOUBLE
      ask      DOUBLE
      bid_sz   INTEGER
      ask_sz   INTEGER
    """
    _ensure_dir(out_dir)
    n_chunks = math.ceil(n_rows / chunk_rows)

    for k in range(n_chunks):
        start = k * chunk_rows
        end = min((k + 1) * chunk_rows, n_rows)

        sql = f"""
        COPY (
          WITH base AS (
            SELECT
              i::BIGINT AS quote_id,
              (i % {n_symbols})::INTEGER AS sym,
              (TIMESTAMP '{start_ts}' + ((i % 23400000)::BIGINT) * INTERVAL 1 MILLISECOND) AS ts,
              CAST((TIMESTAMP '{start_ts}' + ((i % 23400000)::BIGINT) * INTERVAL 1 MILLISECOND) AS DATE) AS quote_date,
              ((i % {n_symbols}) % {n_buckets})::INTEGER AS bucket,

              (100.0 + ((hash(i*991) % 20000)::DOUBLE)/100.0)::DOUBLE AS mid,
              (0.01 + ((hash(i*37) % 50)::DOUBLE)/10000.0)::DOUBLE AS spr
            FROM range({start}, {end}) t(i)
          )
          SELECT
            quote_id, sym, ts, quote_date, bucket,
            mid,
            (mid - spr/2.0)::DOUBLE AS bid,
            (mid + spr/2.0)::DOUBLE AS ask,
            (1 + (hash(quote_id*19) % 2000))::INTEGER AS bid_sz,
            (1 + (hash(quote_id*23) % 2000))::INTEGER AS ask_sz
          FROM base
        )
        TO '{out_dir}'
        (FORMAT PARQUET,
         COMPRESSION ZSTD,
         OVERWRITE 1,
         PARTITION_BY (bucket, quote_date),
         ROW_GROUP_SIZE 250000,
         FILENAME_PATTERN 'quotes_{k}_{{i}}.parquet');
        """
        con.execute(sql)
    print(f"[OK] quotes written to {out_dir}")


# -----------------------------
# 2) Out-of-core merge (ASOF JOIN) to Parquet
# -----------------------------
def merge_trades_quotes_asof(con,
                             trades_dir: str,
                             quotes_dir: str,
                             merged_dir: str,
                             n_buckets: int = 128):
    """
    Uses DuckDB ASOF JOIN to attach prevailing quote to each trade.
    ASOF JOIN is designed for time alignment (t.ts >= q.ts)  [oai_citation:4‡DuckDB](https://duckdb.org/2023/09/15/asof-joins-fuzzy-temporal-lookups.html?utm_source=chatgpt.com)
    """
    _ensure_dir(merged_dir)

    for b in range(n_buckets):
        trades_glob = os.path.join(trades_dir, f"bucket={b}", "*", "*.parquet")
        quotes_glob = os.path.join(quotes_dir, f"bucket={b}", "*", "*.parquet")

        sql = f"""
        COPY (
          SELECT
            t.trade_id,
            t.sym,
            t.ts,
            t.trade_date,
            t.bucket,
            t.is_buy,
            t.size,
            t.price,

            q.mid,
            q.bid,
            q.ask,
            q.bid_sz,
            q.ask_sz,

            (q.ask - q.bid) AS spread,
            (t.price - q.mid) AS px_minus_mid,
            (q.bid_sz - q.ask_sz) / NULLIF((q.bid_sz + q.ask_sz), 0) AS book_imbalance
          FROM read_parquet('{trades_glob}') t
          ASOF JOIN read_parquet('{quotes_glob}') q
          USING (sym, ts)
        )
        TO '{merged_dir}'
        (FORMAT PARQUET,
         COMPRESSION ZSTD,
         OVERWRITE 1,
         PARTITION_BY (bucket, trade_date),
         ROW_GROUP_SIZE 250000,
         FILENAME_PATTERN 'merged_b{b}_{{uuid}}.parquet');
        """
        con.execute(sql)

    print(f"[OK] merged written to {merged_dir}")


# -----------------------------
# 3) Sample in SQL (keeps Python memory safe)
# -----------------------------
def make_training_sample(con,
                         merged_dir: str,
                         out_table: str = "train_sample",
                         n_rows: int = 500_000,
                         seed: int = 42):
    merged_glob = os.path.join(merged_dir, "**", "*.parquet").replace("\\", "/")
    con.execute("DROP TABLE IF EXISTS " + out_table)

    # Reservoir gives an exact-size sample; REPEATABLE makes it deterministic  [oai_citation:5‡DuckDB](https://duckdb.org/docs/stable/sql/samples.html?utm_source=chatgpt.com)
    con.execute(f"""
      CREATE TABLE {out_table} AS
      SELECT
        is_buy,
        size, price,
        mid, bid, ask,
        spread,
        px_minus_mid,
        book_imbalance
      FROM read_parquet('{merged_glob}', hive_partitioning=true)
      USING SAMPLE reservoir({n_rows} ROWS)
      REPEATABLE ({seed});
    """)
    print(f"[OK] training sample table: {out_table} ({n_rows} rows)")


# -----------------------------
# 4) Symbolic classifier (interpretable formula)
# -----------------------------
def fit_symbolic_buy_sell(con,
                          table: str = "train_sample",
                          test_size: float = 0.25,
                          random_state: int = 0):
    df = con.execute(f"SELECT * FROM {table}").fetchdf()  # sample-sized only
    y = df["is_buy"].astype(int).to_numpy()
    X = df.drop(columns=["is_buy"]).to_numpy()
    feature_names = df.drop(columns=["is_buy"]).columns.tolist()

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size,
                                          stratify=y, random_state=random_state)

    clf = SymbolicClassifier(
        population_size=2000,
        generations=30,
        tournament_size=30,
        function_set=("add", "sub", "mul", "div", "abs", "neg", "max", "min", "log", "sqrt", "inv"),
        metric="log loss",              # default for SymbolicClassifier  [oai_citation:6‡gplearn](https://gplearn.readthedocs.io/_/downloads/en/latest/pdf/?utm_source=chatgpt.com)
        transformer="sigmoid",          # turns score into probability  [oai_citation:7‡GitHub](https://github.com/trevorstephens/gplearn/blob/main/gplearn/genetic.py?utm_source=chatgpt.com)
        parsimony_coefficient=0.001,    # push simpler formulas
        max_samples=0.9,
        class_weight="balanced",
        n_jobs=-1,
        verbose=1,
        random_state=random_state,
        feature_names=feature_names,
    )
    if not hasattr(gp.BaseSymbolic, "_validate_data"):
        # Compat: gplearn expects sklearn BaseEstimator._validate_data
        def _validate_data(self, X, y, y_numeric=False):
            X, y = check_X_y(X, y, accept_sparse=False, y_numeric=y_numeric)
            self.n_features_in_ = X.shape[1]
            return X, y
        gp.BaseSymbolic._validate_data = _validate_data
    if not hasattr(SymbolicClassifier, "_validate_data"):
        SymbolicClassifier._validate_data = gp.BaseSymbolic._validate_data
    clf.fit(Xtr, ytr)

    print("\n=== Discovered functional form (raw score before sigmoid) ===")
    print(clf._program)  # best evolved expression  [oai_citation:8‡gplearn](https://gplearn.readthedocs.io/en/stable/advanced.html?utm_source=chatgpt.com)

    yhat = clf.predict(Xte)
    print("\n=== Holdout metrics ===")
    print(classification_report(yte, yhat, digits=4))

    return clf


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    DB_PATH = "./ticklab.duckdb"
    TMP_DIR = "./duckdb_tmp"

    TRADES_DIR = "./data/trades_parquet"
    QUOTES_DIR = "./data/quotes_parquet"
    MERGED_DIR = "./data/merged_parquet"

    con = connect_duckdb(DB_PATH, memory_limit="8GB", temp_dir=TMP_DIR, threads=8)

    # 1) Generate (set n_rows to 300_000_000 for your full dummy)
    generate_trades_parquet(con, TRADES_DIR, n_rows=300_000_000, n_symbols=10_000, n_buckets=128, chunk_rows=10_000_000)
    generate_quotes_parquet(con, QUOTES_DIR, n_rows=60_000_000,  n_symbols=10_000, n_buckets=128, chunk_rows=5_000_000)

    # 2) Merge without materializing to Python
    merge_trades_quotes_asof(con, TRADES_DIR, QUOTES_DIR, MERGED_DIR, n_buckets=128)

    # 3) Sample for ML
    make_training_sample(con, MERGED_DIR, out_table="train_sample", n_rows=500_000, seed=42)

    # 4) Symbolic classifier → interpretable “best-fit” composition
    _ = fit_symbolic_buy_sell(con, "train_sample")