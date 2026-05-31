import asyncpg
import os
from datetime import datetime


async def get_db_pool():
    return await asyncpg.create_pool(os.getenv("DATABASE_URL"))


async def init_db(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                telegram_user_id BIGINT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS allowed_accounts (
                id SERIAL PRIMARY KEY,
                telegram_username TEXT UNIQUE NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                employee_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                pin_code TEXT NOT NULL,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                employee_id TEXT NOT NULL,
                attendance_date DATE NOT NULL,
                clock_in TIMESTAMP,
                clock_out TIMESTAMP,
                total_minutes INTEGER,
                status TEXT DEFAULT 'Present',
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                employee_id TEXT NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                edited_by TEXT NOT NULL,
                edited_at TIMESTAMP DEFAULT NOW()
            );
        """)
