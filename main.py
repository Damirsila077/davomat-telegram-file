import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from models.database import get_db_pool, init_db
from repositories.employee_repo import EmployeeRepository
from repositories.attendance_repo import AttendanceRepository
from repositories.other_repos import AllowedAccountsRepository, AuditLogRepository
from bot.handlers import admin, office
from bot.middlewares.auth import AllowedAccountMiddleware

load_dotenv()
logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # DB
    pool = await get_db_pool()
    await init_db(pool)

    # Repos
    employee_repo = EmployeeRepository(pool)
    attendance_repo = AttendanceRepository(pool)
    accounts_repo = AllowedAccountsRepository(pool)
    audit_repo = AuditLogRepository(pool)

    # Inject dependencies
    dp["employee_repo"] = employee_repo
    dp["attendance_repo"] = attendance_repo
    dp["accounts_repo"] = accounts_repo
    dp["audit_repo"] = audit_repo

    # Middleware (only for office handler, admin bypasses)
    dp.message.middleware(AllowedAccountMiddleware(accounts_repo))

    # Routers
    dp.include_router(admin.router)
    dp.include_router(office.router)

    logging.info("Bot ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
