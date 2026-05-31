from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def office_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🟢 Ishni boshlash"), KeyboardButton(text="🔴 Ishni yakunlash")],
            [KeyboardButton(text="📊 Mening ma'lumotlarim")],
        ],
        resize_keyboard=True
    )


def admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Xodimlar"), KeyboardButton(text="📋 Hisobotlar")],
            [KeyboardButton(text="✏️ Davomat tahrirlash"), KeyboardButton(text="📁 Excel export")],
            [KeyboardButton(text="🔐 Ruxsat etilgan akkauntlar"), KeyboardButton(text="📜 Audit log")],
        ],
        resize_keyboard=True
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )


def employee_management_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Xodim qo'shish"), KeyboardButton(text="📋 Xodimlar ro'yxati")],
            [KeyboardButton(text="✏️ Xodimni tahrirlash"), KeyboardButton(text="🗑️ Xodimni o'chirish")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )


def report_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Bugungi hisobot"), KeyboardButton(text="📆 Oylik hisobot")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )


def export_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📤 Bugungi export"), KeyboardButton(text="📤 Haftalik export")],
            [KeyboardButton(text="📤 Oylik export")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )


def allowed_accounts_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Akkaunt qo'shish"), KeyboardButton(text="📋 Akkauntlar ro'yxati")],
            [KeyboardButton(text="🗑️ Akkaunt o'chirish")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )


def edit_attendance_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏰ Kelish vaqtini tahrirlash")],
            [KeyboardButton(text="⏰ Ketish vaqtini tahrirlash")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )
