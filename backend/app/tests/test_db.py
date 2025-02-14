from sqlalchemy import create_engine, text

# HARDCODED CREDENTIALS - REPLACE WITH YOURS
DATABASE_URI = "postgresql+psycopg://postgres:postgrespassword@localhost:5432/app"

engine = create_engine(DATABASE_URI)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print("🔥 SUCCESS! PostgreSQL Version:", result.scalar())
except Exception as e:
    print("💥 FAILED! Error:", e)
finally:
    engine.dispose()