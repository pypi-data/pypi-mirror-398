# antispam_core/text_manager.py
import os, logging,random
from ..core.config import spam_config
logger = logging.getLogger(__name__)

TEXT_FILE_PATH = 'downloads/fosh.txt'
        
def get_spam_texts():
    return str(random.choice(spam_config["text_list"]))

async def save_text_cmd(message):
    try:
        content = message.text.replace('text', '').strip()
        if not content:
            await message.reply('لطفا متن را وارد کنید')
            return
        spam_config["text_list"].append(content)
        await message.reply('**سیو شد**')
    except Exception as e:
        await message.reply(f'خطا در ذخیره متن: {e}')

async def clear_texts_cmd(message):
    try:
        spam_config["text_list"].clear()
        with open(TEXT_FILE_PATH, 'w', encoding='utf-8') as file:
            file.write('')
        await message.reply('**لیست تکست‌ها پاکسازی شد!**')
    except Exception as e:
        await message.reply(f'خطا در پاکسازی متن‌ها: {e}')

async def show_texts_cmd(message):
    try:
        texts = spam_config["text_list"]
        lines = []
        for i, line in enumerate(texts, 1):
            lines.append(f"{i} - {line}")
        text = "\n".join(lines) if lines else "(خالی)"
        await message.reply(text)
    except Exception as e:
        await message.reply(f'خطا در مشاهده متن: {e}')
