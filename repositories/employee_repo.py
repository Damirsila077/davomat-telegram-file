from datetime import datetime


class EmployeeRepository:
    def __init__(self, pool):
        self.pool = pool

    async def create(self, employee_id, full_name, pin_code):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                """INSERT INTO employees (employee_id, full_name, pin_code)
                   VALUES ($1, $2, $3) RETURNING *""",
                employee_id, full_name, pin_code
            )

    async def get_by_id(self, employee_id):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(
                "SELECT * FROM employees WHERE employee_id = $1 AND active = TRUE",
                employee_id
            )

    async def get_all(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                "SELECT * FROM employees ORDER BY employee_id"
            )

    async def update(self, employee_id, full_name=None, pin_code=None, active=None):
        async with self.pool.acquire() as conn:
            if full_name:
                await conn.execute(
                    "UPDATE employees SET full_name = $1 WHERE employee_id = $2",
                    full_name, employee_id
                )
            if pin_code:
                await conn.execute(
                    "UPDATE employees SET pin_code = $1 WHERE employee_id = $2",
                    pin_code, employee_id
                )
            if active is not None:
                await conn.execute(
                    "UPDATE employees SET active = $1 WHERE employee_id = $2",
                    active, employee_id
                )

    async def delete(self, employee_id):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE employees SET active = FALSE WHERE employee_id = $1",
                employee_id
            )

    async def verify_pin(self, employee_id, pin_code):
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM employees WHERE employee_id = $1 AND pin_code = $2 AND active = TRUE",
                employee_id, pin_code
            )
            return row is not None
