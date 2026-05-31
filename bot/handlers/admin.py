from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date

from bot.keyboards.keyboards import *
from bot.middlewares.auth import is_admin, is_sub_admin, is_any_admin
from repositories.employee_repo import EmployeeRepository
from repositories.attendance_repo import AttendanceRepository
from repositories.other_repos import AllowedAccountsRepository, AuditLogRepository
from utils.excel_export import create_excel_report

router = Router()


def format_minutes(minutes):
    if not minutes:
        return "-"
    h = minutes // 60
    m = minutes % 60
    return f"{h}h {m:02d}m"


# ─── States ───────────────────────────────────────────────────────────────────

class AddEmployeeState(StatesGroup):
    employee_id = State()
    full_name = State()
    pin_code = State()


class EditEmployeeState(StatesGroup):
    employee_id = State()
    field = State()
    value = State()


class DeleteEmployeeState(StatesGroup):
    employee_id = State()


class EditAttendanceState(StatesGroup):
    employee_id = State()
    target_date = State()
    field = State()
    new_time = State()


class AddAccountState(StatesGroup):
    username = State()


class RemoveAccountState(StatesGroup):
    username = State()


# ─── Admin check filter ────────────────────────────────────────────────────────

from aiogram.filters import BaseFilter

class AdminFilter(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return is_admin(message.from_user.id)


# ─── Start & Main Menu ────────────────────────────────────────────────────────

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    if is_admin(message.from_user.id):
        await message.answer(
            f"👋 Xush kelibsiz, Admin!\n"
            f"Davomat boshqaruv tizimi tayyor.",
            reply_markup=admin_main_keyboard()
        )
    elif is_sub_admin(message.from_user.id):
        await message.answer(
            f"👋 Xush kelibsiz, Menejer!\n"
            f"Davomat boshqaruv tizimi tayyor.",
            reply_markup=sub_admin_keyboard()
        )
    else:
        await message.answer(
            "👋 Xush kelibsiz!\n"
            "Davomat tizimidan foydalaning.",
            reply_markup=office_main_keyboard()
        )


@router.message(F.text == "🔙 Orqaga")
async def go_back(message: Message, state: FSMContext):
    await state.clear()
    if is_admin(message.from_user.id):
        await message.answer("Asosiy menyu:", reply_markup=admin_main_keyboard())
    elif is_sub_admin(message.from_user.id):
        await message.answer("Asosiy menyu:", reply_markup=sub_admin_keyboard())
    else:
        await message.answer("Asosiy menyu:", reply_markup=office_main_keyboard())


# ─── Employee Management ───────────────────────────────────────────────────────

@router.message(F.text == "👥 Xodimlar")
async def employees_menu(message: Message):
    if not is_any_admin(message.from_user.id):
        return
    await message.answer("👥 Xodimlar boshqaruvi:", reply_markup=employee_management_keyboard())


@router.message(F.text == "➕ Xodim qo'shish")
async def add_employee_start(message: Message, state: FSMContext):
    if not is_any_admin(message.from_user.id):
        return
    await state.set_state(AddEmployeeState.employee_id)
    await message.answer("🆔 Xodim ID raqamini kiriting (masalan: 1001):", reply_markup=cancel_keyboard())


@router.message(AddEmployeeState.employee_id)
async def add_employee_id(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=employee_management_keyboard())
        return
    await state.update_data(employee_id=message.text.strip())
    await state.set_state(AddEmployeeState.full_name)
    await message.answer("👤 To'liq ismini kiriting:")


@router.message(AddEmployeeState.full_name)
async def add_employee_name(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=employee_management_keyboard())
        return
    await state.update_data(full_name=message.text.strip())
    await state.set_state(AddEmployeeState.pin_code)
    await message.answer("🔐 PIN kodni kiriting (4 raqam):")


@router.message(AddEmployeeState.pin_code)
async def add_employee_pin(message: Message, state: FSMContext, employee_repo: EmployeeRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=employee_management_keyboard())
        return
    data = await state.get_data()
    try:
        await employee_repo.create(data['employee_id'], data['full_name'], message.text.strip())
        await message.answer(
            f"✅ Xodim qo'shildi!\n\n"
            f"🆔 ID: {data['employee_id']}\n"
            f"👤 Ism: {data['full_name']}\n"
            f"🔐 PIN: {message.text.strip()}",
            reply_markup=employee_management_keyboard()
        )
    except Exception as e:
        await message.answer(f"❌ Xato: Bu ID allaqachon mavjud!", reply_markup=employee_management_keyboard())
    await state.clear()


@router.message(F.text == "📋 Xodimlar ro'yxati")
async def list_employees(message: Message, employee_repo: EmployeeRepository):
    if not is_any_admin(message.from_user.id):
        return
    employees = await employee_repo.get_all()
    if not employees:
        await message.answer("Xodimlar yo'q.", reply_markup=employee_management_keyboard())
        return
    text = "👥 Xodimlar ro'yxati:\n" + "─" * 30 + "\n"
    for emp in employees:
        status = "✅" if emp['active'] else "❌"
        text += f"{status} [{emp['employee_id']}] {emp['full_name']}\n"
    await message.answer(text, reply_markup=employee_management_keyboard())


@router.message(F.text == "🗑️ Xodimni o'chirish")
async def delete_employee_start(message: Message, state: FSMContext):
    if not is_any_admin(message.from_user.id):
        return
    await state.set_state(DeleteEmployeeState.employee_id)
    await message.answer("🆔 O'chirish uchun xodim ID sini kiriting:", reply_markup=cancel_keyboard())


@router.message(DeleteEmployeeState.employee_id)
async def delete_employee(message: Message, state: FSMContext, employee_repo: EmployeeRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=employee_management_keyboard())
        return
    employee_id = message.text.strip()
    employee = await employee_repo.get_by_id(employee_id)
    if not employee:
        await message.answer("❌ Xodim topilmadi.")
        await state.clear()
        return
    await employee_repo.delete(employee_id)
    await message.answer(f"✅ {employee['full_name']} (ID: {employee_id}) o'chirildi.", reply_markup=employee_management_keyboard())
    await state.clear()


# ─── Reports ──────────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Hisobotlar")
async def reports_menu(message: Message):
    if not is_any_admin(message.from_user.id):
        return
    await message.answer("📋 Hisobotlar:", reply_markup=report_keyboard())


@router.message(F.text == "📅 Bugungi hisobot")
async def daily_report(message: Message, attendance_repo: AttendanceRepository):
    if not is_any_admin(message.from_user.id):
        return
    records = await attendance_repo.get_today_all()
    if not records:
        await message.answer("📅 Bugun hech kim kelmagan.", reply_markup=report_keyboard())
        return
    text = f"📅 Bugungi hisobot ({date.today()}):\n" + "─" * 30 + "\n"
    for r in records:
        ci = r['clock_in'].strftime('%H:%M') if r['clock_in'] else '-'
        co = r['clock_out'].strftime('%H:%M') if r['clock_out'] else 'Hali ketmagan'
        text += f"[{r['employee_id']}] {r['full_name']}\n  🟢 {ci} → 🔴 {co} | {format_minutes(r['total_minutes'])}\n\n"
    await message.answer(text, reply_markup=report_keyboard())


@router.message(F.text == "📆 Oylik hisobot")
async def monthly_report(message: Message, attendance_repo: AttendanceRepository):
    if not is_any_admin(message.from_user.id):
        return
    now = datetime.now()
    records = await attendance_repo.get_monthly_all(now.year, now.month)
    if not records:
        await message.answer("Bu oy uchun ma'lumot yo'q.", reply_markup=report_keyboard())
        return

    summary = {}
    for r in records:
        eid = r['employee_id']
        if eid not in summary:
            summary[eid] = {'name': r['full_name'], 'minutes': 0, 'days': 0}
        summary[eid]['minutes'] += r['total_minutes'] or 0
        if r['clock_in']:
            summary[eid]['days'] += 1

    text = f"📆 Oylik hisobot ({now.strftime('%B %Y')}):\n" + "─" * 30 + "\n"
    for eid, data in summary.items():
        text += f"[{eid}] {data['name']}\n  📅 {data['days']} kun | ⏱ {format_minutes(data['minutes'])}\n\n"
    await message.answer(text, reply_markup=report_keyboard())


# ─── Excel Export ─────────────────────────────────────────────────────────────

@router.message(F.text == "📁 Excel export")
async def export_menu(message: Message):
    if not is_any_admin(message.from_user.id):
        return
    await message.answer("📁 Export turi:", reply_markup=export_keyboard())


@router.message(F.text.in_({"📤 Bugungi export", "📤 Haftalik export", "📤 Oylik export"}))
async def do_export(message: Message, attendance_repo: AttendanceRepository):
    if not is_any_admin(message.from_user.id):
        return
    now = datetime.now()

    if "Bugungi" in message.text:
        records = await attendance_repo.get_today_all()
        title = f"Bugungi hisobot - {date.today()}"
        filename = f"attendance_{date.today()}.xlsx"
    elif "Oylik" in message.text:
        records = await attendance_repo.get_monthly_all(now.year, now.month)
        title = f"Oylik hisobot - {now.strftime('%B %Y')}"
        filename = f"attendance_{now.strftime('%Y_%m')}.xlsx"
    else:
        from datetime import timedelta
        week_start = date.today() - timedelta(days=7)
        records = await attendance_repo.get_monthly_all(now.year, now.month)
        title = f"Haftalik hisobot"
        filename = f"attendance_week_{date.today()}.xlsx"

    if not records:
        await message.answer("❌ Ma'lumot topilmadi.")
        return

    buffer = create_excel_report([dict(r) for r in records], title)
    await message.answer_document(
        BufferedInputFile(buffer.read(), filename=filename),
        caption=f"📊 {title}"
    )


# ─── Attendance Editing ────────────────────────────────────────────────────────

@router.message(F.text == "✏️ Davomat tahrirlash")
async def edit_attendance_menu(message: Message):
    if not is_any_admin(message.from_user.id):
        return
    await message.answer("✏️ Davomat tahrirlash:", reply_markup=edit_attendance_keyboard())


@router.message(F.text.in_({"⏰ Kelish vaqtini tahrirlash", "⏰ Ketish vaqtini tahrirlash"}))
async def edit_attendance_start(message: Message, state: FSMContext):
    if not is_any_admin(message.from_user.id):
        return
    field = "clock_in" if "Kelish" in message.text else "clock_out"
    await state.update_data(field=field)
    await state.set_state(EditAttendanceState.employee_id)
    await message.answer("🆔 Xodim ID raqamini kiriting:", reply_markup=cancel_keyboard())


@router.message(EditAttendanceState.employee_id)
async def edit_att_id(message: Message, state: FSMContext, employee_repo: EmployeeRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=edit_attendance_keyboard())
        return
    employee = await employee_repo.get_by_id(message.text.strip())
    if not employee:
        await message.answer("❌ Xodim topilmadi.")
        return
    await state.update_data(employee_id=message.text.strip())
    await state.set_state(EditAttendanceState.target_date)
    await message.answer(f"📅 Sanani kiriting (YYYY-MM-DD formatida, masalan: {date.today()}):")


@router.message(EditAttendanceState.target_date)
async def edit_att_date(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=edit_attendance_keyboard())
        return
    try:
        target_date = datetime.strptime(message.text.strip(), "%Y-%m-%d").date()
    except ValueError:
        await message.answer("❌ Format noto'g'ri. YYYY-MM-DD formatida kiriting:")
        return
    await state.update_data(target_date=str(target_date))
    await state.set_state(EditAttendanceState.new_time)
    await message.answer("⏰ Yangi vaqtni kiriting (HH:MM formatida, masalan: 09:00):")


@router.message(EditAttendanceState.new_time)
async def edit_att_time(message: Message, state: FSMContext, attendance_repo: AttendanceRepository, audit_repo: AuditLogRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=edit_attendance_keyboard())
        return
    try:
        time_parts = datetime.strptime(message.text.strip(), "%H:%M")
    except ValueError:
        await message.answer("❌ Format noto'g'ri. HH:MM formatida kiriting:")
        return

    data = await state.get_data()
    employee_id = data['employee_id']
    field = data['field']
    target_date = datetime.strptime(data['target_date'], "%Y-%m-%d").date()
    new_dt = datetime.combine(target_date, time_parts.time())

    if field == "clock_in":
        old_value = await attendance_repo.edit_clock_in(employee_id, target_date, new_dt)
        field_label = "Kelish vaqti"
    else:
        old_value = await attendance_repo.edit_clock_out(employee_id, target_date, new_dt)
        field_label = "Ketish vaqti"

    admin_name = message.from_user.full_name
    await audit_repo.log(employee_id, field, old_value, str(new_dt), admin_name)

    await message.answer(
        f"✅ Muvaffaqiyatli tahrirlandi!\n\n"
        f"🆔 Xodim ID: {employee_id}\n"
        f"📅 Sana: {target_date}\n"
        f"📝 {field_label}: {old_value} → {new_dt.strftime('%H:%M')}",
        reply_markup=admin_main_keyboard()
    )
    await state.clear()


# ─── Allowed Accounts ─────────────────────────────────────────────────────────

@router.message(F.text == "🔐 Ruxsat etilgan akkauntlar")
async def allowed_accounts_menu(message: Message):
    if not is_any_admin(message.from_user.id):
        return
    await message.answer("🔐 Ruxsat etilgan akkauntlar:", reply_markup=allowed_accounts_keyboard())


@router.message(F.text == "📋 Akkauntlar ro'yxati")
async def list_accounts(message: Message, accounts_repo: AllowedAccountsRepository):
    if not is_any_admin(message.from_user.id):
        return
    accounts = await accounts_repo.get_all()
    if not accounts:
        await message.answer("Hech qanday akkaunt yo'q.", reply_markup=allowed_accounts_keyboard())
        return
    text = "🔐 Ruxsat etilgan akkauntlar:\n" + "─" * 30 + "\n"
    for acc in accounts:
        status = "✅" if acc['active'] else "❌"
        text += f"{status} @{acc['telegram_username']}\n"
    await message.answer(text, reply_markup=allowed_accounts_keyboard())


@router.message(F.text == "➕ Akkaunt qo'shish")
async def add_account_start(message: Message, state: FSMContext):
    if not is_any_admin(message.from_user.id):
        return
    await state.set_state(AddAccountState.username)
    await message.answer("📝 Telegram username kiriting (@username):", reply_markup=cancel_keyboard())


@router.message(AddAccountState.username)
async def add_account(message: Message, state: FSMContext, accounts_repo: AllowedAccountsRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=allowed_accounts_keyboard())
        return
    username = message.text.strip()
    result = await accounts_repo.add(username)
    if result:
        await message.answer(f"✅ @{username.replace('@','')} qo'shildi!", reply_markup=allowed_accounts_keyboard())
    else:
        await message.answer("❌ Bu akkaunt allaqachon mavjud!", reply_markup=allowed_accounts_keyboard())
    await state.clear()


@router.message(F.text == "🗑️ Akkaunt o'chirish")
async def remove_account_start(message: Message, state: FSMContext):
    if not is_any_admin(message.from_user.id):
        return
    await state.set_state(RemoveAccountState.username)
    await message.answer("📝 O'chirish uchun username kiriting:", reply_markup=cancel_keyboard())


@router.message(RemoveAccountState.username)
async def remove_account(message: Message, state: FSMContext, accounts_repo: AllowedAccountsRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=allowed_accounts_keyboard())
        return
    username = message.text.strip()
    await accounts_repo.remove(username)
    await message.answer(f"✅ @{username.replace('@','')} o'chirildi!", reply_markup=allowed_accounts_keyboard())
    await state.clear()


# ─── Audit Log ────────────────────────────────────────────────────────────────

@router.message(F.text == "📜 Audit log")
async def audit_log(message: Message, audit_repo: AuditLogRepository):
    if not is_admin(message.from_user.id):  # Only full admin
        return
    logs = await audit_repo.get_all(limit=20)
    if not logs:
        await message.answer("Audit log bo'sh.", reply_markup=admin_main_keyboard())
        return
    text = "📜 Oxirgi o'zgarishlar:\n" + "─" * 30 + "\n"
    for log in logs:
        text += (
            f"👤 Xodim: {log['employee_id']}\n"
            f"📝 {log['field_name']}: {log['old_value']} → {log['new_value']}\n"
            f"✏️ {log['edited_by']} | {log['edited_at'].strftime('%Y-%m-%d %H:%M')}\n"
            f"─ ─ ─\n"
        )
    await message.answer(text, reply_markup=admin_main_keyboard())



# ─── Delete Attendance ─────────────────────────────────────────────────────────

class DeleteAttendanceState(StatesGroup):
    employee_id = State()
    target_date = State()
    confirm = State()


@router.message(F.text == "🗑️ Davomatni o'chirish")
async def delete_attendance_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(DeleteAttendanceState.employee_id)
    await message.answer(
        "🗑️ Davomat o'chirish\n\n"
        "🆔 Xodim ID sini kiriting:",
        reply_markup=cancel_keyboard()
    )


@router.message(DeleteAttendanceState.employee_id)
async def delete_att_employee(message: Message, state: FSMContext, employee_repo: EmployeeRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    employee = await employee_repo.get_by_id(message.text.strip())
    if not employee:
        await message.answer("❌ Xodim topilmadi. ID ni tekshiring:")
        return
    await state.update_data(employee_id=message.text.strip(), full_name=employee["full_name"])
    await state.set_state(DeleteAttendanceState.target_date)
    await message.answer(
        f"👤 {employee['full_name']}\n\n"
        f"📅 Sanani kiriting (YYYY-MM-DD):\n"
        f"Masalan: {date.today()}\n\n"
        f"Yoki \"bugun\" yozing:"
    )


@router.message(DeleteAttendanceState.target_date)
async def delete_att_date(message: Message, state: FSMContext, attendance_repo: AttendanceRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_keyboard())
        return

    text = message.text.strip().lower()
    if text == "bugun":
        target_date = date.today()
    else:
        try:
            target_date = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            await message.answer("❌ Format noto'g'ri. YYYY-MM-DD yoki \"bugun\" yozing:")
            return

    data = await state.get_data()
    employee_id = data["employee_id"]

    records = await attendance_repo.get_by_date(employee_id, target_date)
    if not records:
        await message.answer(
            f"❌ {target_date} kuni {data['full_name']} uchun davomat topilmadi.",
            reply_markup=admin_main_keyboard()
        )
        await state.clear()
        return

    text_lines = f"👤 {data['full_name']} — {target_date}\n" + "─" * 25 + "\n"
    for i, r in enumerate(records, 1):
        ci = r["clock_in"].strftime("%H:%M") if r["clock_in"] else "-"
        co = r["clock_out"].strftime("%H:%M") if r["clock_out"] else "Hali ketmagan"
        text_lines += f"{i}. 🟢 {ci} → 🔴 {co}\n"

    await state.update_data(target_date=str(target_date))
    await state.set_state(DeleteAttendanceState.confirm)

    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    confirm_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha, o'chirish"), KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )
    await message.answer(
        f"⚠️ Quyidagi yozuvlar o'chiriladi:\n\n{text_lines}\nDavom etasizmi?",
        reply_markup=confirm_kb
    )


@router.message(DeleteAttendanceState.confirm)
async def delete_att_confirm(message: Message, state: FSMContext, attendance_repo: AttendanceRepository, audit_repo: AuditLogRepository):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    if message.text != "✅ Ha, o'chirish":
        return

    data = await state.get_data()
    employee_id = data["employee_id"]
    target_date = datetime.strptime(data["target_date"], "%Y-%m-%d").date()

    deleted = await attendance_repo.delete_by_employee_date(employee_id, target_date)

    await audit_repo.log(
        employee_id, "delete_attendance",
        str(target_date), f"{deleted} yozuv o'chirildi",
        message.from_user.full_name
    )

    await message.answer(
        f"✅ O'chirildi!\n\n"
        f"👤 {data['full_name']}\n"
        f"📅 {target_date}\n"
        f"🗑️ {deleted} ta yozuv o'chirildi.",
        reply_markup=admin_main_keyboard()
    )
    await state.clear()
