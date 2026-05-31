class AllowedAccountsRepository:
    def __init__(self, pool):
        self.pool = pool

    async def add(self, username):
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO allowed_accounts (telegram_username) VALUES ($1)",
                    username.lower().replace("@", "")
                )
                return True
            except Exception:
                return False

    async def remove(self, username):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM allowed_accounts WHERE telegram_username = $1",
                username.lower().replace("@", "")
            )

    async def is_allowed(self, username):
        if not username:
            return False
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM allowed_accounts WHERE telegram_username = $1 AND active = TRUE",
                username.lower().replace("@", "")
            )
            return row is not None

    async def get_all(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("SELECT * FROM allowed_accounts ORDER BY created_at")

    async def toggle(self, username, active):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE allowed_accounts SET active = $1 WHERE telegram_username = $2",
                active, username.lower().replace("@", "")
            )


class AuditLogRepository:
    def __init__(self, pool):
        self.pool = pool

    async def log(self, employee_id, field_name, old_value, new_value, edited_by):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO audit_logs (employee_id, field_name, old_value, new_value, edited_by)
                   VALUES ($1, $2, $3, $4, $5)""",
                employee_id, field_name, old_value, new_value, edited_by
            )

    async def get_all(self, limit=50):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM audit_logs ORDER BY edited_at DESC LIMIT $1",
                limit
            )

    async def get_by_employee(self, employee_id):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM audit_logs WHERE employee_id = $1 ORDER BY edited_at DESC",
                employee_id
            )
