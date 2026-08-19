import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

BOT_TOKEN = "8981242781:AAEm3VckbN5yUziuUEUSw7Rhmov75hSiprk"
ADMIN_ID = 8914547953
TAPS_USERNAME = "topkinone"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Anketalar bazasi
profiles = []

# Holatlar (States)
class AddProfile(StatesGroup):
    photo = State()
    name = State()
    age = State()
    city = State()
    contact = State()

class UserReceipt(StatesGroup):
    waiting_photo = State()

# --- ADMIN BEKOR QILISH BUYRUG'I ---
@dp.message(Command("cancel"), StateFilter('*'))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Amaliyot bekor qilindi.", reply_markup=ReplyKeyboardRemove())

# --- USER QISMI ---

@dp.message(CommandStart(), StateFilter('*'))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    if not profiles:
        await message.answer("⚠️ Hozircha hech qanday anketa mavjud emas.")
        return
    
    await state.update_data(index=0)
    await show_profile(message.chat.id, 0, state)

async def show_profile(chat_id: int, index: int, state: FSMContext):
    if not profiles or index >= len(profiles):
        await bot.send_message(chat_id, "🎉 Barcha anketalar tugadi!")
        return

    profile = profiles[index]
    
    caption = (
        f"✨ **{profile['name']}**, {profile['age']} yosh\n"
        f"📍 **Shahar:** {profile['city']}\n"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❤️ Like", callback_data=f"like_{index}"),
            InlineKeyboardButton(text="💔 Dislike", callback_data=f"dislike_{index}")
        ]
    ])

    await bot.send_photo(
        chat_id=chat_id,
        photo=profile["photo"],
        caption=caption,
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("dislike_"))
async def handle_dislike(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("index", 0) + 1
    
    try:
        await call.message.delete()
    except Exception:
        pass

    if index < len(profiles):
        await state.update_data(index=index)
        await show_profile(call.message.chat.id, index, state)
    else:
        await call.message.answer("🎉 Barcha anketalar tugadi!")
    await call.answer()

@dp.callback_query(F.data.startswith("like_"))
async def handle_like(call: types.CallbackQuery, state: FSMContext):
    index = int(call.data.split("_")[1])
    
    if index >= len(profiles):
        await call.answer("Profil topilmadi.", show_alert=True)
        return

    profile = profiles[index]
    pay_link = f"https://taps.uz/{TAPS_USERNAME}?amount=15000"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 15 000 so'm to'lov qilish", url=pay_link)],
        [InlineKeyboardButton(text="🧾 Chek yuborish", callback_data="send_receipt")]
    ])
    
    text = (
        f"❤️ **So'rovingiz {profile['name']}ga yuborildi!**\n\n"
        f"Agar u ham rasmingizga like bossa, uning akkaunti sizga tekinga ko'rinadi.\n\n"
        f"⚡️ *Akkauntni hoziroq ko'rishni istasangiz, 15 000 so'm to'lov qilishingiz mumkin:*"
    )
    
    await call.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

# CHEK YUBORISH KNOPKASI BOSILGANIDA
@dp.callback_query(F.data == "send_receipt")
async def start_receipt_upload(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(UserReceipt.waiting_photo)
    await call.message.answer("📸 **Iltimos, to'lov cheki rasmini (skrinshotini) shu yerga yuboring:**")
    await call.answer()

# FOYDALANUVCHI CHEK RASMINI YUBORGAN ZAHOTI ISHLAYDI
@dp.message(UserReceipt.waiting_photo, F.photo)
async def process_receipt_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
        ]
    ])
    
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    
    # Adminga rasm va tugmalarni yuborish
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=(
            f"📥 **Yangi to'lov cheki keldi!**\n\n"
            f"👤 **Foydalanuvchi:** {user_info}\n"
            f"💰 **Summa:** 15 000 so'm"
        ),
        parse_mode="Markdown",
        reply_markup=admin_kb
    )
    
    await state.clear()
    await message.answer("⏳ Chekingiz adminga muvaffaqiyatli yuborildi! Tekshirib bo'lingach, admin siz bilan bog'lanadi.")

# MATN YUBORIB QO'YSA OGOHLANTIRISH
@dp.message(UserReceipt.waiting_photo)
async def process_receipt_not_photo(message: types.Message):
    await message.answer("⚠️ Iltimos, faqat **rasm (skrinshot)** ko'rinishida yuboring!")

# --- ADMIN TASDIQLASH QISMI ---

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
        
    user_id = int(call.data.split("_")[1])
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text="✅ To'lovingiz tasdiqlandi! Admin siz bilan tez orada bog'lanadi."
        )
        await call.message.edit_caption(caption=call.message.caption + "\n\n✅ **TASDIQLANDI**")
        await call.answer("Tasdiqlandi!")
    except Exception as e:
        await call.answer(f"Xatolik: {e}", show_alert=True)

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
        
    user_id = int(call.data.split("_")[1])
    
    try:
        await bot.send_message(
            chat_id=user_id,
            text="❌ To'lovingiz tasdiqlanmadi. Chek rasmini qayta tekshirib yuboring."
        )
        await call.message.edit_caption(caption=call.message.caption + "\n\n❌ **RAD ETILDI**")
        await call.answer("Rad etildi!")
    except Exception as e:
        await call.answer(f"Xatolik: {e}", show_alert=True)

# --- ADMIN BUYRUQLARI (/add, /list, /del) ---

@dp.message(Command("add"), StateFilter('*'))
async def add_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    await state.set_state(AddProfile.photo)
    await message.answer("📸 Yangi anketa uchun rasm yuboring:")

@dp.message(AddProfile.photo, F.photo)
async def add_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await state.set_state(AddProfile.name)
    await message.answer("✍️ Ismini kiriting:")

@dp.message(AddProfile.name)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProfile.age)
    await message.answer("🔢 Yoshini kiriting:")

@dp.message(AddProfile.age)
async def add_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(AddProfile.city)
    await message.answer("📍 Viloyat/Shaharni kiriting:")

@dp.message(AddProfile.city)
async def add_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(AddProfile.contact)
    await message.answer("🔗 Kontaktni kiriting (masalan: @username):")

@dp.message(AddProfile.contact)
async def add_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    profiles.append({
        "photo": data["photo"],
        "name": data["name"],
        "age": data["age"],
        "city": data["city"],
        "contact": message.text
    })
    await state.clear()
    await message.answer("✅ Yangi anketa saqlandi!")

@dp.message(Command("list"), StateFilter('*'))
async def list_profiles(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    
    if not profiles:
        await message.answer("📁 Hozircha anketalar bazasi bo'sh.")
        return
    
    text = "📋 **Mavjud anketalar ro'yxati:**\n\n"
    for idx, p in enumerate(profiles, start=1):
        text += f"️⃣ **{idx}** | {p['name']}, {p['age']} yosh ({p['city']})\n"
    
    text += "\n🗑 O'chirish uchun buyruq: `/del 1` (tartib raqamini yozing)"
    await message.answer(text, parse_mode="Markdown")

@dp.message(Command("del"), StateFilter('*'))
async def delete_profile(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await state.clear()
    
    try:
        args = message.text.split()
        if len(args) < 2:
            await message.answer("⚠️ O'chirish uchun tartib raqamini yozing. Masalan: `/del 1`", parse_mode="Markdown")
            return
            
        index_to_del = int(args[1]) - 1
        
        if 0 <= index_to_del < len(profiles):
            removed = profiles.pop(index_to_del)
            await message.answer(f"✅ **{removed['name']}** anketasi muvaffaqiyatli o'chirildi!")
        else:
            await message.answer("❌ Bunday tartib raqamli anketa topilmadi. `/list` deb yozib ko'ring.")
    except Exception as e:
        await message.answer(f"⚠️ Xatolik: `/del 1` ko'rinishida yuboring.")

# --- WEB SERVER & POLLING ---

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def main():
    logging.basicConfig(level=logging.INFO)
    
    app = web.Application()
    app.router.add_get("/", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
