import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "BOT_TOKENINI_SHUYERGA_YOZING"
ADMIN_ID = 8914547953  # Sizning Telegram ID raqamingiz
TAPS_USERNAME = "topkinone"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Soxta anketalar bazasi
profiles = [
    {
        "id": 1,
        "photo": "https://picsum.photos/400/500",
        "name": "Madina",
        "age": 21,
        "city": "Toshkent",
        "contact": "@qaysarcha_ool"
    },
    {
        "id": 2,
        "photo": "https://picsum.photos/401/500",
        "name": "Sevinch",
        "age": 23,
        "city": "Samarqand",
        "contact": "@qaysarcha_ool"
    }
]

# Admin va User holatlari
class AddProfile(StatesGroup):
    photo = State()
    name = State()
    age = State()
    city = State()
    contact = State()

class UserState(StatesGroup):
    view_index = State()
    waiting_receipt = State()

# --- USER QISMI ---

@dp.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    if not profiles:
        await message.answer("Hozircha anketalar yo'q.")
        return
    
    await state.set_state(UserState.view_index)
    await state.update_data(index=0)
    await show_profile(message.chat.id, 0, state)

async def show_profile(chat_id: int, index: int, state: FSMContext):
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
    
    if index < len(profiles):
        await state.update_data(index=index)
        await call.message.delete()
        await show_profile(call.message.chat.id, index, state)
    else:
        await call.message.delete()
        await call.message.answer("🎉 Barcha anketalar tugadi!")
    await call.answer()

@dp.callback_query(F.data.startswith("like_"))
async def handle_like(call: types.CallbackQuery, state: FSMContext):
    index = int(call.data.split("_")[1])
    profile = profiles[index]
    
    pay_link = f"https://taps.uz/{TAPS_USERNAME}?amount=15000&comment=Profile_{profile['id']}"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 15 000 so'm to'lov qilish", url=pay_link)],
        [InlineKeyboardButton(text="🧾 Chek yuborish", callback_data=f"send_receipt_{index}")]
    ])
    
    text = (
        f"❤️ **So'rovingiz {profile['name']}ga yuborildi!**\n\n"
        f"Agar u ham rasmingizga like bossa, uning akkaunti sizga tekinga ko'rinadi.\n\n"
        f"⚡️ *Akkauntni hoziroq ko'rishni istasangiz, 15 000 so'm to'lov qilishingiz mumkin:* "
    )
    
    await call.message.answer(text, parse_mode="Markdown", reply_markup=kb)
    await call.answer()

@dp.callback_query(F.data.startswith("send_receipt_"))
async def start_receipt_upload(call: types.CallbackQuery, state: FSMContext):
    index = int(call.data.split("_")[1])
    await state.update_data(target_index=index)
    await state.set_state(UserState.waiting_receipt)
    
    await call.message.answer("📸 Iltimos, to'lov cheki (skrinshot/rasm)ni yuboring:")
    await call.answer()

@dp.message(UserState.waiting_receipt, F.photo)
async def receive_receipt(message: types.Message, state: FSMContext):
    data = await state.get_data()
    index = data.get("target_index", 0)
    profile = profiles[index]
    
    photo_id = message.photo[-1].file_id
    
    # Admin uchun tasdiqlash tugmalari
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash (Ochish)", callback_data=f"approve_{message.from_user.id}_{index}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{message.from_user.id}")
        ]
    ])
    
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=(
            f"📥 **Yangi to'lov cheki!**\n\n"
            f"👤 **Foydalanuvchi:** {user_info}\n"
            f"🎯 **Tanlangan profil:** {profile['name']} ({profile['city']})\n"
            f"💰 **Summa:** 15 000 so'm"
        ),
        parse_mode="Markdown",
        reply_markup=admin_kb
    )
    
    await state.set_state(UserState.view_index)
    await message.answer("⏳ Chekingiz adminga yuborildi. To'lov tasdiqlangach, kontakt 1-5 daqiqada sizga yuboriladi.")

# --- ADMIN TASDIQLASH QISMI ---

@dp.callback_query(F.data.startswith("approve_"))
async def approve_payment(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
        
    _, user_id, index = call.data.split("_")
    profile = profiles[int(index)]
    
    # Userga kontaktni yuborish
    await bot.send_message(
        chat_id=int(user_id),
        text=f"✅ To'lovingiz tasdiqlandi!\n\n✨ **{profile['name']}** bilan bog'lanish uchun kontakt: {profile['contact']}"
    )
    
    await call.message.edit_caption(caption=call.message.caption + "\n\n✅ **TASDIQLANDI**")
    await call.answer("Kontakt foydalanuvchiga yuborildi!")

@dp.callback_query(F.data.startswith("reject_"))
async def reject_payment(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
        
    user_id = call.data.split("_")[1]
    
    await bot.send_message(
        chat_id=int(user_id),
        text="❌ To'lovingiz tasdiqlanmadi. Chek rasmini tekshirib qayta yuboring."
    )
    
    await call.message.edit_caption(caption=call.message.caption + "\n\n❌ **RAD ETILDI**")
    await call.answer("To'lov rad etildi.")

# --- ADMIN SOXTA ANKETA QO'SHISH (/add) ---

@dp.message(Command("add"), F.from_user.id == ADMIN_ID)
async def add_start(message: types.Message, state: FSMContext):
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
    await message.answer("🔗 Kontaktni kiriting (masalan: @qaysarcha_ool):")

@dp.message(AddProfile.contact)
async def add_contact(message: types.Message, state: FSMContext):
    data = await state.get_data()
    profiles.append({
        "id": len(profiles) + 1,
        "photo": data["photo"],
        "name": data["name"],
        "age": data["age"],
        "city": data["city"],
        "contact": message.text
    })
    await state.clear()
    await message.answer("✅ Yangi anketa saqlandi!")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
