from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime

from bot.keyboards.keyboards import office_main_keyboard, cancel_keyboard
from repositories.employee_repo import EmployeeRepository
from repositories.attendance_repo import AttendanceRepository

router = Router()


class ClockInState(StatesGroup):
    waiting_id = State()


class ClockOutState(StatesGroup):
    waiting_id = State()


class SelfServiceState(StatesGroup):
    waiting_id = State()
    waiting_pin = State()


def format_minutes(minutes):
    if not minutes:
        return "-"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m:02d}m"


@router.message(F.text == "🟢 Ishni boshlash")
async def start_clock_in(message: Message, state: FSMContext):
    await state.set_state(ClockInState.waiting_id)
    await message.answer("👤 Xodim ID raqamini kiriting:", reply_markup=cancel_keyboard())


@router.message(ClockInState.waiting_id)
async def process_clock_in(message: Message, state: FSMContext, employee_repo: EmployeeRepository, attendance_repo: AttendanceRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=office_main_keyboard())
        return

    employee_id = message.text.strip()
    employee = await employee_repo.get_by_id(employee_id)

    if not employee:
        await message.answer("❌ Xodim topilmadi. ID ni tekshiring.")
        return

    clock_time, status = await attendance_repo.clock_in(employee_id)

    if status == "already_clocked_in":
        await message.answer(
            f"⚠️ {employee['full_name']} (ID: {employee_id}) bugun allaqachon ishni boshlagan!"
        )
    else:
        await message.answer(
            f"✅ Ish muvaffaqiyatli boshlandi!\n\n"
            f"👤 Xodim: {employee['full_name']}\n"
            f"🆔 ID: {employee_id}\n"
            f"⏰ Vaqt: {clock_time.strftime('%H:%M')}\n"
            f"📅 Sana: {clock_time.strftime('%Y-%m-%d')}",
            reply_markup=office_main_keyboard()
        )

    await state.clear()


@router.message(F.text == "🔴 Ishni yakunlash")
async def start_clock_out(message: Message, state: FSMContext):
    await state.set_state(ClockOutState.waiting_id)
    await message.answer("👤 Xodim ID raqamini kiriting:", reply_markup=cancel_keyboard())


@router.message(ClockOutState.waiting_id)
async def process_clock_out(message: Message, state: FSMContext, employee_repo: EmployeeRepository, attendance_repo: AttendanceRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=office_main_keyboard())
        return

    employee_id = message.text.strip()
    employee = await employee_repo.get_by_id(employee_id)

    if not employee:
        await message.answer("❌ Xodim topilmadi. ID ni tekshiring.")
        return

    clock_in, clock_out, total_minutes, status = await attendance_repo.clock_out(employee_id)

    if status == "not_clocked_in":
        await message.answer(f"⚠️ {employee['full_name']} bugun ishni boshlamagan!")
    elif status == "already_clocked_out":
        await message.answer(f"⚠️ {employee['full_name']} allaqachon ishni yakunlagan!")
    else:
        await message.answer(
            f"✅ Ish muvaffaqiyatli yakunlandi!\n\n"
            f"👤 Xodim: {employee['full_name']}\n"
            f"🆔 ID: {employee_id}\n"
            f"🟢 Kelish: {clock_in.strftime('%H:%M')}\n"
            f"🔴 Ketish: {clock_out.strftime('%H:%M')}\n"
            f"⏱ Jami ish vaqti: {format_minutes(total_minutes)}",
            reply_markup=office_main_keyboard()
        )

    await state.clear()


@router.message(F.text == "📊 Mening ma'lumotlarim")
async def start_self_service(message: Message, state: FSMContext):
    await state.set_state(SelfServiceState.waiting_id)
    await message.answer("👤 Xodim ID raqamini kiriting:", reply_markup=cancel_keyboard())


@router.message(SelfServiceState.waiting_id)
async def self_service_id(message: Message, state: FSMContext, employee_repo: EmployeeRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=office_main_keyboard())
        return

    employee_id = message.text.strip()
    employee = await employee_repo.get_by_id(employee_id)
    if not employee:
        await message.answer("❌ Xodim topilmadi.")
        return

    await state.update_data(employee_id=employee_id)
    await state.set_state(SelfServiceState.waiting_pin)
    await message.answer("🔐 PIN kodingizni kiriting:")


@router.message(SelfServiceState.waiting_pin)
async def self_service_pin(message: Message, state: FSMContext, employee_repo: EmployeeRepository, attendance_repo: AttendanceRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=office_main_keyboard())
        return

    data = await state.get_data()
    employee_id = data['employee_id']
    pin = message.text.strip()

    valid = await employee_repo.verify_pin(employee_id, pin)
    if not valid:
        await message.answer("❌ PIN kod noto'g'ri!")
        await state.clear()
        return

    employee = await employee_repo.get_by_id(employee_id)
    today_record = await attendance_repo.get_employee_today(employee_id)

    now = datetime.now()
    monthly = await attendance_repo.get_employee_monthly(employee_id, now.year, now.month)

    total_month_minutes = sum(r['total_minutes'] or 0 for r in monthly)
    work_days = len([r for r in monthly if r['clock_in']])

    today_text = "Bugun hali kelmagan"
    if today_record:
        ci = today_record['clock_in'].strftime('%H:%M') if today_record['clock_in'] else '-'
        co = today_record['clock_out'].strftime('%H:%M') if today_record['clock_out'] else 'Hali ketmagan'
        today_text = f"Kelish: {ci} | Ketish: {co}"

    await message.answer(
        f"📊 {employee['full_name']} ma'lumotlari\n"
        f"{'─' * 30}\n"
        f"📅 Bugun: {today_text}\n\n"
        f"📆 Bu oy ({now.strftime('%B %Y')}):\n"
        f"  • Ish kunlari: {work_days} kun\n"
        f"  • Jami ish vaqti: {format_minutes(total_month_minutes)}\n",
        reply_markup=office_main_keyboard()
    )

    await state.clear()
