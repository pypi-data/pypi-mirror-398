from asgiref.sync import async_to_sync, sync_to_async
import os
from django.dispatch import receiver
from .signals import notifire, send_sms, send_mail
import re
from telegram import Bot
import logging
from dotenv import load_dotenv
load_dotenv()

def get_bot():
    TOKEN = os.getenv('UTILS_BOT_TOKEN')
    if not TOKEN:
        logging.error("Telegram bot token not found in environment variables.")
        raise ValueError("Telegram bot token is required.\nUTILS_BOT_TOKEN must be set in environment variables.")
    return Bot(token=TOKEN)


def clean_html_for_telegram(text: str) -> str:
    """
    حذف تگ‌های HTML نامجاز برای استفاده در Telegram با parse_mode='HTML'
    و جایگزینی برخی از آن‌ها مثل <p> با newline
    """
    # تگ‌های مجاز HTML برای تلگرام
    allowed_tags = ['b', 'strong', 'i', 'em', 'u', 's', 'strike', 'del',
                    'span', 'a', 'code', 'pre']

    # جایگزینی <p> و </p> با newline
    text = re.sub(r'</?p\s*>', '\n', text)

    # حذف تگ‌های غیرمجاز
    def remove_invalid_tags(match):
        tag = match.group(1)
        if tag.lower() not in allowed_tags:
            return ''
        return match.group(0)

    # حذف تگ‌های باز
    text = re.sub(r'<(/?\s*?)(\w+)([^>]*)>',
                  lambda m: remove_invalid_tags((m.group(2),)) if m.group(2).lower() not in allowed_tags else m.group(
                      0), text)

    return text.strip()


@receiver(notifire)
def handle_notifire(sender, text, chat_id=None, label=True, **kwargs):
    chat_id = chat_id if chat_id else os.getenv('UTILS_TELEGRAM_CHAT_ID')
    if not chat_id:
        logging.error("Telegram chat ID not found in environment variables.")
        raise ValueError("Telegram chat ID is required.\nUTILS_TELEGRAM_CHAT_ID must be set in environment variables.")
    file = kwargs.get('file')
    parse_mode = kwargs.get('parse_mode', 'HTML')
    disable_notification = kwargs.get('disable_notification', False)
    protect_content = kwargs.get('protect_content')
    reply_markup = kwargs.get('reply_markup')
    reply_to_message_id = kwargs.get('reply_to_message_id')
    disable_web_page_preview = kwargs.get('disable_web_page_preview')
    data = {
        'chat_id': chat_id,
        'parse_mode': parse_mode,
        'disable_notification': disable_notification,
        'protect_content': protect_content,
        'reply_markup': reply_markup,
        'reply_to_message_id': reply_to_message_id,

    }
    if label:
        text = f"#{os.getenv('PROJECT_NAME')}:{sender}\n{text}"
    if kwargs.get('parse_mode') == 'HTML':
        text = clean_html_for_telegram(text)
    try:
        bot = get_bot()
        if file:
            res = async_to_sync(bot.send_document)(document=file, caption=text, **data)
            print(res)

        else:
            data['disable_web_page_preview'] = disable_web_page_preview
            res = async_to_sync(bot.send_message)(text=text, **data)
            print(res)
    except Exception as e:
        print(e)
