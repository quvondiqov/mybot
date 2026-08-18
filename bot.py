import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

# --- SOZLAMALAR ---
BOT_TOKEN = "8981242781:AAEm3VckbN5yUziuUEUSw7Rhmov75hSiprk"  # BotFather'dan olingan token
ADMIN_ID = 8914547953              # O'zingizning Telegram ID'ingiz
TAPS_USERNAME = "topkinone"        # Taps.uz nik nomingiz

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# === ASOSIY BITTANING AKKAUNTI (Hamma profillar uchun bitta kontakt beriladi) ===
MAIN_CONTACT = "@qaysarcha_ool"  # O'zingiz ochgan akkaunt username'i

# === KO'PAYTIRILGAN QIZLAR RO'YXATI (12 ta profil) ===
GIRLS_DATA = {
    1001: {"name": "Madina, 21 (Toshkent)", "contact": MAIN_CONTACT},
    1002: {"name": "Sevinch, 23 (Samarqand)", "contact": MAIN_CONTACT},
    1003: {"name": "Rayhon, 20 (Farg'ona)", "contact": MAIN_CONTACT},
    1004: {"name": "Laylo, 22 (Toshkent)", "contact": MAIN_CONTACT},
    1005: {"name": "Diyora, 19 (Andijon)", "contact": MAIN_CONTACT},
    1006: {"name": "Shaxzoda, 21 (Buxoro)", "contact": MAIN_CONTACT},
    1007: {"name": "Nigora, 24 (Toshkent)", "contact": MAIN_CONTACT},
    1008: {"name": "Asal, 20 (Namangan)", "contact": MAIN_CONTACT},
    1009: {"name": "Kamola, 22 (Qarshi)", "contact": MAIN_CONTACT},
    1010: {"name": "Zilola, 23 (Toshkent)", "contact": MAIN_CONTACT},
    1011: {"name": "Guli, 21 (Urganch)", "contact": MAIN_CONTACT},
    1012: {"name": "Lola, 20 (Jizzax)", "contact": MAIN_CONTACT},
}

@dp.message(CommandStart())
async def start_cmd(message: types.Message):
    # Anketalarni tugmacha shaklida chiqarish
    buttons = []
    for g_id, g_info in GIRLS_DATA.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"✨ {g_info['name']} — (15,000 so'm)", 
                callback_data=f"buy_{g_id}"
            )
        ])
    
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        "👋 **Xush kelibsiz!**\n\n"
        "Tanishish uchun o'zingizga yoqqan nomzodni tanlang va kontaktini oling:", 
        reply_markup=kb, 
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("buy_"))
async def buy_profile(callback: types.CallbackQuery):
    girl_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    girl = GIRLS_DATA.get(girl_id)
    
    amount = 15000
    comment = f"UNLOCK_{user_id}_{girl_id}"
    taps_link = f"https://taps.uz/{TAPS_USERNAME}?amount={amount}&comment={comment}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 15,000 so'm to'lash (Taps.uz)", url=taps_link)],
        [InlineKeyboardButton(text="✅ To'lov qildim (Tekshirish)", callback_data=f"check_{girl_id}")],
        [InlineKeyboardButton(text="⬅️ Bosh sahifa", callback_data="back")]
    ])
    
    text = (
        f"👤 **Tanlangan profil:** {girl['name']}\n"
        f"💰 **Profilni ochish narxi:** 15,000 so'm\n\n"
        f"📌 *Yo'riqnoma:* Taps.uz orqali to'lovni bajarib, **'To'lov qildim'** tugmasini bosing."
    )
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "back")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.delete()
    await start_cmd(callback.message)

@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: types.CallbackQuery):
    girl_id = int(callback.data.split("_")[1])
    user = callback.from_user
    
    await callback.message.answer(
        "⏳ **So'rovingiz adminga yuborildi.**\n"
        "To'lov tekshirilgach, kontakt 1-5 daqiqada ochiladi.",
        parse_mode="Markdown"
    )
    
    kb_admin = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash (Ochish)", callback_data=f"approve_{user.id}_{girl_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"decline_{user.id}")
        ]
    ])
    
    admin_text = (
        f"💳 **Yangi to'lov so'rovi!**\n\n"
        f"👤 **Foydalanuvchi:** {user.full_name} (@{user.username})\n"
        f"🆔 **User ID:** `{user.id}`\n"
        f"🎯 **Tanlangan profil ID:** `{girl_id}`\n"
        f"💰 **Summa:** 15,000 so'm\n\n"
        f"Taps.uz hisobingizni tekshirib tasdiqlang:"
    )
    
    await bot.send_message(chat_id=ADMIN_ID, text=admin_text, reply_markup=kb_admin, parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: types.CallbackQuery):
    _, user_id, girl_id = callback.data.split("_")
    user_id, girl_id = int(user_id), int(girl_id)
    
    girl = GIRLS_DATA.get(girl_id, {"name": "Profil", "contact": MAIN_CONTACT})
    
    # Foydalanuvchiga kontakt yuboriladi
    await bot.send_message(
        chat_id=user_id,
        text=f"🎉 **To'lovingiz tasdiqlandi!**\n\nSiz tanlagan profil: **{girl['name']}**\nTelegram kontakti: {girl['contact']}\n\nBezorilik qilmasdan, xushfe'llik bilan muloqot qilishingizni so'raymiz!",
        parse_mode="Markdown"
    )
    
    await callback.message.edit_text(f"✅ ID {user_id} uchun to'lov tasdiqlandi va profil ochib berildi!")

@dp.callback_query(F.data.startswith("decline_"))
async def decline_payment(callback: types.CallbackQuery):
    user_id = int(callback.data.split("_")[1])
    
    await bot.send_message(
        chat_id=user_id,
        text="❌ **To'lovingiz tasdiqlanmadi.**\nTaps.uz hisobiga to'lov tushgani aniqlanmadi."
    )
    await callback.message.edit_text(f"❌ ID {user_id} so'rovi rad etildi.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())