
import asyncio
import io
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
# BOT TOKEN
TOKEN = "8996873078:AAHsOoQ3gHvSCjoNF1LSpH3Zx-tTFtqlc9w"
bot = Bot(token=TOKEN)
dp = Dispatcher()
bot = Bot(token=TOKEN)
dp = Dispatcher()


# HOLATLAR
class Hisob(StatesGroup):
    tur = State()
    sinf = State()
    fan = State()
    maks = State()
    royxat = State()


# ASOSIY MENYU
menyu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📊 Ballarni hisoblash")],
        [KeyboardButton(text="ℹ️ Ma'lumot")],
    ],
    resize_keyboard=True,
)


# BAHO HISOBLASH
def baho(foiz: float) -> int:
    if foiz >= 86:
        return 5
    if foiz >= 71:
        return 4
    if foiz >= 55:
        return 3
    return 2


# WORD HISOBOT
def hisobot_yasash(tur, sinf, fan, maks, oquvchilar) -> bytes:
    doc = Document()

    sarlavha = doc.add_heading(f"{tur} natijalari", level=1)
    sarlavha.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph(
        f"Sinf: {sinf}     Fan: {fan}     Maksimal ball: {maks:g}"
    )

    jadval = doc.add_table(rows=1, cols=5)
    jadval.style = "Table Grid"

    for i, matn in enumerate(["№", "F.I.Sh.", "Ball", "Foiz", "Baho"]):
        jadval.rows[0].cells[i].text = matn

    baholar = []
    foizlar = []

    for n, (ism, ball) in enumerate(oquvchilar, start=1):
        foiz = ball / maks * 100
        b = baho(foiz)

        baholar.append(b)
        foizlar.append(foiz)

        q = jadval.add_row().cells
        q[0].text = str(n)
        q[1].text = ism
        q[2].text = f"{ball:g}"
        q[3].text = f"{foiz:.0f}%"
        q[4].text = str(b)

    doc.add_paragraph()
    doc.add_paragraph(f"O'quvchilar soni: {len(oquvchilar)}")
    doc.add_paragraph(
        f"O'rtacha foiz: {sum(foizlar) / len(foizlar):.1f}%"
    )

    doc.add_paragraph(
        f"5 baho: {baholar.count(5)}\n"
        f"4 baho: {baholar.count(4)}\n"
        f"3 baho: {baholar.count(3)}\n"
        f"2 baho: {baholar.count(2)}"
    )

    buffer = io.BytesIO()
    doc.save(buffer)

    return buffer.getvalue()


# START
@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "Salom! 👋\n\n"
        "Men BSB va CHSB natijalarini hisoblab, "
        "Word hisobot tayyorlashga yordam beraman.\n\n"
        "🎉 Bot barcha foydalanuvchilar uchun MUTLAQO BEPUL!",
        reply_markup=menyu,
    )


# MA'LUMOT
@dp.message(F.text == "ℹ️ Ma'lumot")
async def malumot(message: Message, state: FSMContext):
    await state.clear()

    await message.answer(
        "📊 Bu bot BSB va CHSB natijalarini hisoblaydi.\n\n"
        "📄 Word hisobot tayyorlaydi.\n"
        "✅ Barcha funksiyalar bepul.\n"
        "💳 To'lov va obuna talab qilinmaydi.",
        reply_markup=menyu,
    )


# HISOBLASH BOSHLASH
@dp.message(F.text == "📊 Ballarni hisoblash")
async def hisoblash(message: Message, state: FSMContext):
    await state.clear()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="BSB",
                    callback_data="tur:BSB"
                ),
                InlineKeyboardButton(
                    text="CHSB",
                    callback_data="tur:CHSB"
                ),
            ]
        ]
    )

    await state.set_state(Hisob.tur)
    await message.answer("Hisobot turini tanlang:", reply_markup=kb)


# TUR TANLASH
@dp.callback_query(Hisob.tur, F.data.startswith("tur:"))
async def tur_tanlash(call: CallbackQuery, state: FSMContext):
    await state.update_data(tur=call.data.split(":")[1])
    await state.set_state(Hisob.sinf)

    await call.message.answer("Sinfni yozing (masalan: 9-A):")
    await call.answer()


# SINF
@dp.message(Hisob.sinf, F.text)
async def sinf_olish(message: Message, state: FSMContext):
    await state.update_data(sinf=message.text.strip())
    await state.set_state(Hisob.fan)

    await message.answer("Fan nomini yozing (masalan: Ona tili):")


# FAN
@dp.message(Hisob.fan, F.text)
async def fan_olish(message: Message, state: FSMContext):
    await state.update_data(fan=message.text.strip())
    await state.set_state(Hisob.maks)

    await message.answer("Maksimal ballni yozing (masalan: 30):")


# MAKSIMAL BALL
@dp.message(Hisob.maks, F.text)
async def maks_olish(message: Message, state: FSMContext):
    try:
        maks = float(message.text.replace(",", "."))

        if maks <= 0:
            raise ValueError

    except ValueError:
        await message.answer(
            "Iltimos, musbat raqam yozing. Masalan: 30"
        )
        return

    await state.update_data(maks=maks)
    await state.set_state(Hisob.royxat)

    await message.answer(
        "O'quvchilarni har qatorda bittadan yuboring:\n\n"
        "Aliyev Ali 25\n"
        "Karimova Zilola 28\n"
        "Rahimov Jasur 14\n\n"
        "Oxirida ball yozilishi shart."
    )


# O'QUVCHILAR RO'YXATI
@dp.message(Hisob.royxat, F.text)
async def royxat_olish(message: Message, state: FSMContext):
    data = await state.get_data()
    maks = data["maks"]

    oquvchilar = []
    xatolar = []

    for qator in message.text.splitlines():
        qator = qator.strip()

        if not qator:
            continue

        qismlar = qator.split()

        try:
            if len(qismlar) < 2:
                raise ValueError

            ball = float(qismlar[-1].replace(",", "."))

            if ball < 0 or ball > maks:
                raise ValueError

            ism = " ".join(qismlar[:-1])

            oquvchilar.append((ism, ball))

        except ValueError:
            xatolar.append(qator)

    if xatolar:
        await message.answer(
            "❌ Quyidagi qatorlarda xato bor:\n\n"
            + "\n".join(xatolar)
            + "\n\nRo'yxatni to'g'rilab qaytadan yuboring."
        )
        return

    if not oquvchilar:
        await message.answer("Ro'yxat bo'sh. Qaytadan yuboring.")
        return

    try:
        fayl = hisobot_yasash(
            data["tur"],
            data["sinf"],
            data["fan"],
            maks,
            oquvchilar,
        )

        document = BufferedInputFile(
            fayl,
            filename="hisobot.docx"
        )

        await message.answer_document(
            document,
            caption="✅ Hisobot tayyor!\n🎉 Botdan foydalanish bepul."
        )

    except Exception as e:
        print("XATOLIK:", e)

        await message.answer(
            "Hisobot tayyorlashda xatolik yuz berdi."
        )

    finally:
        await state.clear()


# BOSHQA XABARLAR
@dp.message()
async def boshqa(message: Message):
    await message.answer(
        "Menyudagi tugmalardan foydalaning.",
        reply_markup=menyu,
    )


# BOTNI ISHGA TUSHIRISH
async def main():
    print("Bot ishga tushdi!")
    print("Barcha foydalanuvchilar uchun bepul.")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
