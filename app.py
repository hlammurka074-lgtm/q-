import os
import asyncio

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT1_TOKEN = os.getenv("BOT1_TOKEN")
BOT2_TOKEN = os.getenv("BOT2_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
USDT_TRC20_ADDRESS = os.getenv("USDT_TRC20_ADDRESS")
TON_BINANCE_ADDRESS = os.getenv("TON_BINANCE_ADDRESS")

PLANS = {
    "7d": {"title": "7 дней", "amount_usd": "5.00"},
    "30d": {"title": "30 дней", "amount_usd": "15.00"},
    "90d": {"title": "90 дней", "amount_usd": "30.00"},
}


async def start_bot1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Перейти в канал", url=CHANNEL_URL)]
    ])
    await update.message.reply_text("Нажми кнопку ниже:", reply_markup=kb)


def main_menu():
    rows = [[InlineKeyboardButton("Перейти в канал", url=CHANNEL_URL)]]
    for key, plan in PLANS.items():
        rows.append([
            InlineKeyboardButton(
                f"{plan['title']} — {plan['amount_usd']} USD",
                callback_data=f"plan:{key}"
            )
        ])
    return InlineKeyboardMarkup(rows)


def methods_menu(plan_key: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Оплата USDT TRC20", callback_data=f"method:{plan_key}:usdt")],
        [InlineKeyboardButton("Оплата TON Binance", callback_data=f"method:{plan_key}:ton")],
        [InlineKeyboardButton("Назад", callback_data="back")]
    ])


def paid_menu(plan_key: str, method_key: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Я ОПЛАТИЛ", callback_data=f"paid:{plan_key}:{method_key}")],
        [InlineKeyboardButton("Назад", callback_data=f"plan:{plan_key}")]
    ])


async def start_bot2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать. Выберите тариф:",
        reply_markup=main_menu()
    )


async def callbacks_bot2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    try:
        await query.answer()
    except Exception:
        pass

    if data == "back":
        await query.message.reply_text(
            "Добро пожаловать. Выберите тариф:",
            reply_markup=main_menu()
        )
        return

    if data.startswith("plan:"):
        plan_key = data.split(":")[1]
        if plan_key not in PLANS:
            await query.message.reply_text("Неизвестный тариф")
            return

        plan = PLANS[plan_key]
        text = (
            f"Тариф: {plan['title']}\n"
            f"Стоимость: {plan['amount_usd']} USD\n\n"
            f"Выберите способ оплаты:"
        )
        await query.message.reply_text(text, reply_markup=methods_menu(plan_key))
        return

    if data.startswith("method:"):
        _, plan_key, method_key = data.split(":")
        if plan_key not in PLANS:
            await query.message.reply_text("Ошибка")
            return

        plan = PLANS[plan_key]

        if method_key == "usdt":
            address = USDT_TRC20_ADDRESS
            method_title = "USDT TRC20"
            amount = f"{plan['amount_usd']} USDT"
        else:
            address = TON_BINANCE_ADDRESS
            method_title = "TON Binance"
            amount = f"{plan['amount_usd']} USD в TON"

        text = (
            f"Способ оплаты: {method_title}\n"
            f"К оплате: {amount}\n"
            f"Ваш ID: {query.from_user.id}\n\n"
            f"Адрес для оплаты:\n{address}\n\n"
            f"После оплаты нажмите кнопку «Я ОПЛАТИЛ»."
        )

        await query.message.reply_text(
            text,
            reply_markup=paid_menu(plan_key, method_key)
        )
        return

    if data.startswith("paid:"):
        _, plan_key, method_key = data.split(":")
        if plan_key not in PLANS:
            await query.message.reply_text("Ошибка")
            return

        plan = PLANS[plan_key]
        username = f"@{query.from_user.username}" if query.from_user.username else "нет"
        method_title = "USDT TRC20" if method_key == "usdt" else "TON Binance"

        admin_text = (
            f"Новая заявка на оплату\n\n"
            f"User ID: {query.from_user.id}\n"
            f"Username: {username}\n"
            f"Тариф: {plan['title']}\n"
            f"Сумма: {plan['amount_usd']} USD\n"
            f"Способ: {method_title}"
        )

        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text)
        await query.message.reply_text("Заявка отправлена администратору.")
        return


async def run_app(app: Application):
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    while True:
        await asyncio.sleep(3600)


async def main():
    app1 = Application.builder().token(BOT1_TOKEN).build()
    app1.add_handler(CommandHandler("start", start_bot1))

    app2 = Application.builder().token(BOT2_TOKEN).build()
    app2.add_handler(CommandHandler("start", start_bot2))
    app2.add_handler(CallbackQueryHandler(callbacks_bot2))

    await asyncio.gather(
        run_app(app1),
        run_app(app2),
    )

if __name__ == "__main__":
    asyncio.run(main())
