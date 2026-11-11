import asyncio
import os
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup,
    KeyboardButton, Message, ReplyKeyboardMarkup,
)
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

# ================= SOZLAMALAR (faqat shu qismni to'ldiring) =================
TOKEN = "8996873078:AAE7dDGWCbMFzQscYv0-AVBAHtmcCrofKr4"        # @BotFather bergan token, qo'shtirnoq ichida
ADMIN_ID = 6843924134            # sizning Telegram ID raqamingiz (@userinfobot)
KARTA = "5614 6838 6170 8717"   # o'qituvchilar pul o'tkazadigan karta
KARTA_EGASI = "Muhammadjanov Jahongir"
NARX = 80000                    # 1 yillik obuna narxi (so'm)
KUN = 365                       # obuna muddati (kun)
ADMIN_BEPUL = True              # True: siz botdan to'lovsiz foydalanasiz
# ==========================================================================

bot = Bot(TOKEN)
dp = Dispatcher()

db = sqlite3.connect("bot.db")
db.execute("CREATE TABLE IF NOT EXISTS obuna (user_id INTEGER PRIMARY KEY, tugaydi TEXT)")
db.commit()


def tugash_sanasi(user_id):
    q = db.execute("SELECT tugaydi FROM obuna WHERE user_id=?", (user_id,)).fetchone()
    if not q:
        return None
    t = datetime.fromisoformat(q[0])
    return t if t > datetime.now() else None


def ruxsat_bormi(user_id):
    if ADMIN_BEPUL and user_id == ADMIN_ID:
        return True
    return tugash_sanasi(user_id) is not None


def obuna_ber(user_id, kun=KUN):
    bor = tugash_sanasi(user_id)
    boshlanish = bor if bor else datetime.now()
    tugaydi = boshlanish + timedelta(days=kun)
    db.execute("INSERT OR REPLACE INTO obuna (user_id, tugaydi) VALUES (?, ?)",
               (user_id, tugaydi.isoformat()))
    db.commit()
    return tugaydi


# Foizdan bahoga o'tish. Namuna chegaralar: maktab qoidangizga almashtiring.
def baho(foiz):
    if foiz >= 86:
        return 5
    if foiz >= 71:
        return 4
    if foiz >= 55:
        return 3
    return 2


def hisobot_yasash(fayl, tur, sinf, fan, maks, oquvchilar):
    doc = Document()
    sarlavha = doc.add_heading(f"{tur} natijalari", level=1)
    sarlavha.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Sinf: {sinf}     Fan: {fan}     Maksimal ball: {maks:g}")

    jadval = doc.add_table(rows=1, cols=5)
    jadval.style = "Table Grid"
    for i, matn in enumerate(["№", "F.I.Sh.", "Ball", "Foiz", "Baho"]):
        jadval.rows[0].cells[i].text = matn

    baholar, foizlar = [], []
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
    doc.add_paragraph(f"O'rtacha foiz: {sum(foizlar) / len(foizlar):.1f}%")
    doc.add_paragraph(
        f"Baholar: 5 ta - {baholar.count(5)}, 4 ta - {baholar.count(4)}, "
        f"3 ta - {baholar.count(3)}, 2 ta - {baholar.count(2)}"
    )
    doc.save(fayl)


class Hisob(StatesGroup):
    tur = State()
    sinf = State()
    fan = State()
    maks = State()
    royxat = State()


class Tolov(StatesGroup):
    chek = State()


menyu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📊 Ballarni hisoblash"),
               KeyboardButton(text="ℹ️ Ma'lumot")],
              [KeyboardButton(text="💳 Obuna / To'lov")]],
    resize_keyboard=True,
)


async def tolov_sorash(message: Message, state: FSMContext):
    await state.set_state(Tolov.chek)
    await message.answer(
        f"💳 Obuna narxi: {NARX:,} so'm ({KUN} kun).\n\n"
        f"Shu kartaga o'tkazing:\n<code>{KARTA}</code>\n{KARTA_EGASI}\n\n"
        "O'tkazgach, <b>chek rasmini</b> shu yerga yuboring. "
        "Admin tekshirib, obunangizni faollashtiradi.",
        parse_mode="HTML",
    )


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    t = tugash_sanasi(message.from_user.id)
    if ruxsat_bormi(message.from_user.id):
        holat = f"✅ Obunangiz {t:%d.%m.%Y} gacha faol." if t else "✅ Admin rejimi."
    else:
        holat = (f"⚠️ Bot pullik: {NARX:,} so'm / {KUN} kun.\n"
                 "Obunani faollashtirish uchun «💳 Obuna / To'lov» tugmasini bosing.")
    await message.answer("Salom! Men BSB va CHSB hisobotlarini tayyorlashda yordam beraman.\n\n"
                         + holat, reply_markup=menyu)


@dp.message(Command("tolov"))
@dp.message(F.text == "💳 Obuna / To'lov")
async def tolov(message: Message, state: FSMContext):
    await state.clear()
    t = tugash_sanasi(message.from_user.id)
    if t:
        await message.answer(f"Obunangiz faol: {t:%d.%m.%Y} gacha.\n"
                             "Muddatni uzaytirmoqchi bo'lsangiz, to'lov ma'lumotlari quyida.")
    await tolov_sorash(message, state)


@dp.message(F.text == "ℹ️ Ma'lumot")
async def malumot(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Bu bot o'qituvchilarga BSB va CHSB natijalarini hisoblab, "
        "Word hisobot tayyorlashda yordam beradi.\n"
        f"Narxi: {NARX:,} so'm ({KUN} kun)."
    )


@dp.message(F.text == "📊 Ballarni hisoblash")
async def hisoblash(message: Message, state: FSMContext):
    await state.clear()
    if not ruxsat_bormi(message.from_user.id):
        await message.answer("⚠️ Obunangiz yo'q yoki muddati tugagan.")
        await tolov_sorash(message, state)
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="BSB", callback_data="tur:BSB"),
        InlineKeyboardButton(text="CHSB", callback_data="tur:CHSB"),
    ]])
    await state.set_state(Hisob.tur)
    await message.answer("Hisobot turini tanlang:", reply_markup=kb)


@dp.callback_query(Hisob.tur, F.data.startswith("tur:"))
async def tur_tanlash(call: CallbackQuery, state: FSMContext):
    await state.update_data(tur=call.data.split(":")[1])
    await state.set_state(Hisob.sinf)
    await call.message.answer("Sinfni yozing (masalan: 9-A):")
    await call.answer()


@dp.message(Hisob.sinf, F.text)
async def sinf_olish(message: Message, state: FSMContext):
    await state.update_data(sinf=message.text.strip())
    await state.set_state(Hisob.fan)
    await message.answer("Fan nomini yozing (masalan: Ona tili):")


@dp.message(Hisob.fan, F.text)
async def fan_olish(message: Message, state: FSMContext):
    await state.update_data(fan=message.text.strip())
    await state.set_state(Hisob.maks)
    await message.answer("Maksimal ballni yozing (masalan: 30):")


@dp.message(Hisob.maks, F.text)
async def maks_olish(message: Message, state: FSMContext):
    try:
        maks = float(message.text.replace(",", "."))
        if maks <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Raqam yozing, masalan: 30")
        return
    await state.update_data(maks=maks)
    await state.set_state(Hisob.royxat)
    await message.answer(
        "Endi o'quvchilarni yuboring, har qatorda bittadan: ism-familiya va ball.\n\n"
        "Aliyev Ali 25\nKarimova Zilola 28\nRahimov Jasur 14"
    )


@dp.message(Hisob.royxat, F.text)
async def royxat_olish(message: Message, state: FSMContext):
    if not ruxsat_bormi(message.from_user.id):
        await state.clear()
        await message.answer("⚠️ Obuna muddati tugagan.")
        await tolov_sorash(message, state)
        return
    data = await state.get_data()
    maks = data["maks"]
    oquvchilar, xatolar = [], []
    for q in [x.strip() for x in message.text.split("\n") if x.strip()]:
        qismlar = q.split()
        try:
            if len(qismlar) < 2:
                raise ValueError
            ball = float(qismlar[-1].replace(",", "."))
            if ball < 0 or ball > maks:
                raise ValueError
            oquvchilar.append((" ".join(qismlar[:-1]), ball))
        except ValueError:
            xatolar.append(q)

    if xatolar:
        await message.answer(
            "Bu qatorlarda xato bor (oxirida ball 0 dan maksimalgacha bo'lishi kerak):\n"
            + "\n".join(xatolar) + "\n\nTuzatib, butun ro'yxatni qaytadan yuboring.")
        return
    if not oquvchilar:
        await message.answer("Ro'yxat bo'sh. Qaytadan yuboring.")
        return

    fayl = f"hisobot_{message.from_user.id}.docx"
    try:
        hisobot_yasash(fayl, data["tur"], data["sinf"], data["fan"], maks, oquvchilar)
        await message.answer_document(FSInputFile(fayl, filename="hisobot.docx"),
                                      caption="✅ Hisobot tayyor.")
    finally:
        if os.path.exists(fayl):
            os.remove(fayl)
    await state.clear()


@dp.message(Tolov.chek, F.photo)
async def chek_keldi(message: Message, state: FSMContext):
    u = message.from_user
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok:{u.id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"no:{u.id}"),
    ]])
    try:
        await bot.send_photo(
            ADMIN_ID, message.photo[-1].file_id,
            caption=f"Yangi chek\nIsm: {u.full_name}\nID: {u.id}", reply_markup=kb)
    except Exception as e:
        print("Adminga yuborib bo'lmadi:", e)
        await message.answer("Chekni adminga yuborib bo'lmadi. Keyinroq urinib ko'ring.")
        return
    await state.clear()
    await message.answer("Chek yuborildi. Admin tasdiqlagach xabar olasiz.")


@dp.message(Tolov.chek)
async def chek_emas(message: Message):
    await message.answer("Iltimos, chek rasmini yuboring (rasm ko'rinishida).")


@dp.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def tasdiqlash(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("Ruxsat yo'q", show_alert=True)
        return
    amal, uid = call.data.split(":")
    uid = int(uid)
    if amal == "ok":
        tugaydi = obuna_ber(uid)
        belgi = "✅ Tasdiqlandi"
        matn = f"✅ To'lov tasdiqlandi! Obuna {tugaydi:%d.%m.%Y} gacha faol."
    else:
        belgi = "❌ Rad etildi"
        matn = "❌ To'lov tasdiqlanmadi. Chekni qayta yuboring: «💳 Obuna / To'lov»."
    try:
        await bot.send_message(uid, matn)
    except Exception as e:
        print("Foydalanuvchiga yuborib bo'lmadi:", e)
    await call.message.edit_caption(caption=(call.message.caption or "") + f"\n\n{belgi}")
    await call.answer()


@dp.message(Command("obuna"))
async def qolda_obuna(message: Message):
    # Admin uchun: /obuna 123456789   yoki   /obuna 123456789 30
    if message.from_user.id != ADMIN_ID:
        return
    qismlar = (message.text or "").split()
    try:
        uid = int(qismlar[1])
        kun = int(qismlar[2]) if len(qismlar) > 2 else KUN
    except (ValueError, IndexError):
        await message.answer("Yozilishi: /obuna ID [kun]")
        return
    tugaydi = obuna_ber(uid, kun)
    await message.answer(f"{uid} uchun obuna {tugaydi:%d.%m.%Y} gacha berildi.")


@dp.message(Command("stat"))
async def statistika(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    hozir = datetime.now().isoformat()
    faol = db.execute("SELECT COUNT(*) FROM obuna WHERE tugaydi > ?", (hozir,)).fetchone()[0]
    jami = db.execute("SELECT COUNT(*) FROM obuna").fetchone()[0]
    await message.answer(f"Faol obunalar: {faol}\nJami berilgan: {jami}")


@dp.message()
async def boshqa(message: Message):
    await message.answer("Menyudagi tugmalardan foydalaning.", reply_markup=menyu)


async def main():
    await dp.start_polling(bot)


asyncio.run(main())
