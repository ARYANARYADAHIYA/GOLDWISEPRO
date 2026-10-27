import logging
from sqlalchemy import text
from app.core.database import engine

logger = logging.getLogger("goldwise.migrations")

def run_db_migrations():
    """
    Applies non-destructive schema migrations for existing SQLite databases.
    Preserves all existing data while ensuring new fields are accessible.
    """
    with engine.connect() as conn:
        # Check observations table columns
        res = conn.execute(text("PRAGMA table_info(observations)")).fetchall()
        col_names = {row[1] for row in res}

        if "previous_close" not in col_names:
            logger.info("Migrating schema: Adding 'previous_close' column to observations table")
            conn.execute(text("ALTER TABLE observations ADD COLUMN previous_close FLOAT"))
            conn.commit()

        if "turnover" not in col_names:
            logger.info("Migrating schema: Adding 'turnover' column to observations table")
            conn.execute(text("ALTER TABLE observations ADD COLUMN turnover FLOAT"))
            conn.commit()

        # Check datasets table columns
        res_ds = conn.execute(text("PRAGMA table_info(datasets)")).fetchall()
        ds_col_names = {row[1] for row in res_ds}

        if "provenance" not in ds_col_names:
            logger.info("Migrating schema: Adding 'provenance' column to datasets table")
            conn.execute(text("ALTER TABLE datasets ADD COLUMN provenance TEXT"))
            conn.commit()

        if "collection_timestamp" not in ds_col_names:
            logger.info("Migrating schema: Adding 'collection_timestamp' column to datasets table")
            conn.execute(text("ALTER TABLE datasets ADD COLUMN collection_timestamp DATETIME"))
            conn.commit()

        if "raw_file_path" not in ds_col_names:
            logger.info("Migrating schema: Adding 'raw_file_path' column to datasets table")
            conn.execute(text("ALTER TABLE datasets ADD COLUMN raw_file_path TEXT"))
            conn.commit()
