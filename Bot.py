from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ConversationHandler,
    CallbackQueryHandler,
)
import re
from datetime import datetime, time

# تنظیمات
TOKEN = ':AAG-pTBfbT8XzCGlhJAvTlQdi405SRWq9FI'  # توکن ربات
START_PASSWORD = 'Afshar20157'  # رمز شروع به کار
WORKING_HOURS = (time(8, 0), time(23, 59))  # ساعت کاری (۸ صبح تا ۱۲ شب)

# حالت‌های گفتگو
PASSWORD, ADD_SOURCE, SET_DESTINATION = range(3)

# ذخیره اطلاعات
source_chats = []
destination_chat = None
activated = False

# بررسی ساعت کاری
def is_working_hours():
    now = datetime.now().time()
    return WORKING_HOURS[0] <= now <= WORKING_HOURS[1]

# تابع شروع
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Start", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('برای شروع ربات، دکمه Start رو بزنید.', reply_markup=reply_markup)

# تابع شروع گفتگو
def start_conversation(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text('لطفاً رمز رو وارد کنید:')
    return PASSWORD

# تابع بررسی رمز
def check_password(update: Update, context: CallbackContext):
    global activated
    password = update.message.text

    if password == START_PASSWORD:
        activated = True
        update.message.reply_text('ربات با موفقیت فعال شد!')
        show_menu(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text('رمز اشتباه است. لطفاً دوباره امتحان کنید.')
        return PASSWORD

# تابع نمایش منو
def show_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("اضافه کردن کانال مبدأ", callback_data='add_source')],
        [InlineKeyboardButton("معرفی کانال مقصد", callback_data='set_destination')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('لطفاً یک گزینه انتخاب کنید:', reply_markup=reply_markup)

# تابع اضافه کردن کانال مبدأ
def add_source(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text('لطفاً شناسه کانال یا گروه مبدأ رو وارد کنید:')
    return ADD_SOURCE

# تابع ذخیره کانال مبدأ
def save_source(update: Update, context: CallbackContext):
    source_chat = update.message.text
    source_chats.append(source_chat)
    update.message.reply_text(f'کانال/گروه مبدأ "{source_chat}" با موفقیت اضافه شد.')
    show_menu(update, context)
    return ConversationHandler.END

# تابع معرفی کانال مقصد
def set_destination(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    query.edit_message_text('لطفاً شناسه کانال یا گروه مقصد رو وارد کنید:')
    return SET_DESTINATION

# تابع ذخیره کانال مقصد
def save_destination(update: Update, context: CallbackContext):
    global destination_chat
    destination_chat = update.message.text
    update.message.reply_text(f'کانال/گروه مقصد "{destination_chat}" با موفقیت تنظیم شد.')
    show_menu(update, context)
    return ConversationHandler.END

# تابع کپی و ارسال پیام
def forward_message(update: Update, context: CallbackContext):
    if not activated or not is_working_hours():
        return

    # حذف نام کانال/گروه مبدأ از پیام
    message_text = update.message.text
    if message_text:
        for source_chat in source_chats:
            message_text = re.sub(rf'@{source_chat}', '', message_text)  # حذف نام کانال/گروه مبدأ

        # اضافه کردن نام کانال/گروه مقصد به انتهای پیام
        message_text += f'\n\nارسال شده به: {destination_chat}'

        # ارسال پیام به کانال/گروه مقصد
        context.bot.send_message(chat_id=destination_chat, text=message_text)

def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # دستور /start
    dispatcher.add_handler(CommandHandler("start", start))

    # گفتگو برای فعال‌سازی و تنظیمات
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_conversation, pattern='^start$')],
        states={
            PASSWORD: [MessageHandler(Filters.text & ~Filters.command, check_password)],
            ADD_SOURCE: [MessageHandler(Filters.text & ~Filters.command, save_source)],
            SET_DESTINATION: [MessageHandler(Filters.text & ~Filters.command, save_destination)],
        },
        fallbacks=[]
    )
    dispatcher.add_handler(conv_handler)

    # دکمه‌های منو
    dispatcher.add_handler(CallbackQueryHandler(add_source, pattern='^add_source$'))
    dispatcher.add_handler(CallbackQueryHandler(set_destination, pattern='^set_destination$'))

    # دریافت و فوروارد پیام‌ها
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, forward_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
