import logging
import sqlite3

from telegram import ReplyKeyboardMarkup,\
    InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, Application, CommandHandler,\
    CallbackQueryHandler, MessageHandler, filters,  ConversationHandler

with open('token.txt') as token:
    BOT_TOKEN = token.read()

app = ApplicationBuilder().token(BOT_TOKEN).build()

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

question = ''

def get_operators():
    try:
        sqlite_connection = sqlite3.connect('db/database.db')
        cursor = sqlite_connection.cursor()
        res = list(cursor.execute(f'SELECT * FROM Operators'))
        res = {i[1]: i[2] for i in res}
        return res
    except sqlite3.Error as error:
        print(error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()

def get_companies():
    try:
        sqlite_connection = sqlite3.connect('db/database.db')
        cursor = sqlite_connection.cursor()
        res = list(cursor.execute(f'SELECT Company FROM Operators'))
        return res
    except sqlite3.Error as error:
        print(error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()


async def start(update, context):
    user = update.effective_user
    keyboard = [["Задать вопрос"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)

    await update.message.reply_html(
        f"Здравствуйте, {user.mention_html()}!\nВойдите в меню и нажмите кнопку 'Задать вопрос'",
        reply_markup=markup)


async def ask_question(update, context):
    await update.message.reply_text(
        text=f"Пожалуйста введите вопрос:")
    return 1


async def choose_company(update, context):
    global question
    question = update.message.text

    keyboard = []
    admin = ''
    for key in get_companies():
        if key[0] != 'Администратор чата':
            keyboard.append([InlineKeyboardButton(key[0], callback_data=key[0])])
        else:
            admin = key[0]
    keyboard.append([InlineKeyboardButton(admin, callback_data=admin)])
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_html(
        "Выберите компанию:",
        reply_markup=markup)
    return 2


async def send_question_to_operator(update, context):
    global question
    query = update.callback_query
    await query.answer()
    choosen_company = query.data
    user = update.effective_user
    await context.bot.send_message(get_operators()[choosen_company],
                                   f"{user.mention_html()}:\n{question}", parse_mode=ParseMode.HTML)
    keyboard = [["Задать вопрос"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=False)
    await query.edit_message_text(
        f"Вопрос переслан оператору компании {choosen_company}!")
    return ConversationHandler.END


async def stop(update, context):
    return ConversationHandler.END



def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Задать вопрос$"),
                                     ask_question)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_company)],
            2: [CallbackQueryHandler(send_question_to_operator)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    main()