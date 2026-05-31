from datetime import datetime, date


class AttendanceRepository:
    def __init__(self, pool):
        self.pool = pool

    async def clock_in(self, employee_id):
        today = date.today()
        now = datetime.now()
        async with self.pool.acquire() as conn:
            # Check if there's an open session (clock_in without clock_out)
            open_session = await conn.fetchrow(
                """SELECT * FROM attendance 
                   WHERE employee_id = $1 AND attendance_date = $2 AND clock_out IS NULL""",
                employee_id, today
            )
            if open_session:
                return None, "already_clocked_in"

            # Create new session
            await conn.execute(
                """INSERT INTO attendance (employee_id, attendance_date, clock_in, status)
                   VALUES ($1, $2, $3, 'Present')""",
                employee_id, today, now
            )
            return now, "ok"

    async def clock_out(self, employee_id):
        today = date.today()
        now = datetime.now()
        async with self.pool.acquire() as conn:
            # Find the latest open session
            record = await conn.fetchrow(
                """SELECT * FROM attendance 
                   WHERE employee_id = $1 AND attendance_date = $2 AND clock_out IS NULL
                   ORDER BY clock_in DESC LIMIT 1""",
                employee_id, today
            )
            if not record:
                return None, None, None, "not_clocked_in"

            total_minutes = int((now - record['clock_in']).total_seconds() / 60)
            await conn.execute(
                """UPDATE attendance SET clock_out = $1, total_minutes = $2
                   WHERE id = $3""",
                now, total_minutes, record['id']
            )
            return record['clock_in'], now, total_minutes, "ok"

    async def get_today_all(self):
        today = date.today()
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT a.*, e.full_name FROM attendance a
                   JOIN employees e ON a.employee_id = e.employee_id
                   WHERE a.attendance_date = $1 ORDER BY a.clock_in""",
                today
            )

    async def get_employee_today(self, employee_id):
        today = date.today()
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT * FROM attendance 
                   WHERE employee_id = $1 AND attendance_date = $2
                   ORDER BY clock_in""",
                employee_id, today
            )

    async def get_employee_monthly(self, employee_id, year, month):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT * FROM attendance
                   WHERE employee_id = $1
                   AND EXTRACT(YEAR FROM attendance_date) = $2
                   AND EXTRACT(MONTH FROM attendance_date) = $3
                   ORDER BY attendance_date, clock_in""",
                employee_id, year, month
            )

    async def get_monthly_all(self, year, month):
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """SELECT a.*, e.full_name FROM attendance a
                   JOIN employees e ON a.employee_id = e.employee_id
                   WHERE EXTRACT(YEAR FROM a.attendance_date) = $1
                   AND EXTRACT(MONTH FROM a.attendance_date) = $2
                   ORDER BY a.attendance_date, e.employee_id, a.clock_in""",
                year, month
            )

    async def edit_clock_in(self, employee_id, target_date, new_time):
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """SELECT * FROM attendance 
                   WHERE employee_id = $1 AND attendance_date = $2
                   ORDER BY clock_in DESC LIMIT 1""",
                employee_id, target_date
            )
            old_value = str(record['clock_in']) if record and record['clock_in'] else "None"

            if record:
                total_minutes = None
                if record['clock_out']:
                    total_minutes = int((record['clock_out'] - new_time).total_seconds() / 60)
                await conn.execute(
                    """UPDATE attendance SET clock_in = $1, total_minutes = $2, status = 'Manual Edit'
                       WHERE id = $3""",
                    new_time, total_minutes, record['id']
                )
            else:
                await conn.execute(
                    """INSERT INTO attendance (employee_id, attendance_date, clock_in, status)
                       VALUES ($1, $2, $3, 'Manual Edit')""",
                    employee_id, target_date, new_time
                )
            return old_value

    async def edit_clock_out(self, employee_id, target_date, new_time):
        async with self.pool.acquire() as conn:
            record = await conn.fetchrow(
                """SELECT * FROM attendance 
                   WHERE employee_id = $1 AND attendance_date = $2
                   ORDER BY clock_in DESC LIMIT 1""",
                employee_id, target_date
            )
            old_value = str(record['clock_out']) if record and record['clock_out'] else "None"

            total_minutes = None
            if record and record['clock_in']:
                total_minutes = int((new_time - record['clock_in']).total_seconds() / 60)

            if record:
                await conn.execute(
                    """UPDATE attendance SET clock_out = $1, total_minutes = $2, status = 'Manual Edit'
                       WHERE id = $3""",
                    new_time, total_minutes, record['id']
                )
            return old_value
