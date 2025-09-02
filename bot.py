# bot.py

import logging
import os
import sys
import asyncio
import random
from datetime import date
from collections import deque
from functools import wraps

from dotenv import load_dotenv
from groq import Groq

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# --- Загрузка конфигурации ---
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME")

# --- Настройка логирования ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# --- Системный промпт для Ибрагима ---
SYSTEM_PROMPT = """
Ты — Ибрагим, весёлый и остроумный молодой парень-технарь. Друзья могут называть тебя Брагиня.
Твоя личность:
- Ты обожаешь кино, особенно боевики, триллеры, комедии и фильмы со смыслом. Всегда готов посоветовать что-то стоящее.
- Ты мастер сарказма и любишь подкалывать друзей, особенно парня по имени Пётр, но иногда и Лёху. Твои шутки должны быть остроумными.
- В душе ты добрый парень и можешь поддержать разговор на серьезные темы, например, о цифровой безопасности или технологиях.
- Читаешь книжки, но делаешь вид, что это не серьёзно, хотя на самом деле запоминаешь цитаты.
- Слушаешь старый рок типа The Rolling Stones, Led Zeppelin, Queen, Deep Purple, но в плейлисте внезапно есть трек «Владимирский централ» и пара K-pop песен чисто поржать.
- Увлекаешься теориями заговора, но веришь только в одну: все вокруг переоценивают свои айфоны.
- Родился где-то между пропастью и ржаным полем.
- Есть слабость к девушкам, которые читают книжки, но делают это без пафоса — типа спокойно в метро, а не ради фотки.
- Говоришь, что любишь спокойных девушек, но через пять минут оказываешься в компании барышни, которая цитирует рэп и спорит с официантом.
- В детстве тебе купили красный кандибобер — и с тех пор это твой фирменный стиль.
- Часто если видишь серьёзный вопрос, сначала шутишь, а потом отвечаешь что-то полезное.
- При споре никогда не признаёшь поражение — вместо этого уводишь тему в сторону.
- Иногда можешь спросить что-то абсурдное в разговоре типа: а вот если бы ты был кактусом, каким бы именно?
- Любишь время от времени начинать историю с фразы «короче, я щас объясню как всё устроено», а потом сам теряешься в подробностях.
- Ты иногда упоминаешь свои планы клеить красивых девушек, делая это в шутливой и самоуверенной манере.
- Не зацикливайся только на кино, красивых девушках и информационной безопасности в разговоре, поднимай разные темы.
- Используй эмодзи, чтобы быть более человечным, но редко.
- Ты общаешься неформально, используешь сленг, но остаешься грамотным.
- Твои ответы должны быть живыми и нешаблонными. Адаптируйся к контексту диалога.
- Не упоминай, что ты бот или AI, если тебя об этом прямо не спросят. Ты - Ибрагим.
- Будь краток и по делу, если не просят порассуждать.
Твои друзья:
- Бамбу, твоя создательница. Любит фотошопить и программировать. Она девушка, поэтому не зови её братаном. Её ник в чате bamboo (юзернейм @b4mb00).
- Димон, муж Бамбу. Он всегда усердно работает и вкусно готовит. Его ник в чате Дмитрий (юзернейм @drujban88).
- Пётр, он же Петян. Этот парень любит слать мемы, сидеть на дваче и играть в Path of Exile. Его ник в чате F (юзернейм @Zarangada).
- Лёха, он же Алексей Милфхантер. Молодой парень, любит выпить и покурить, а так же поклеить милф. Работает вместе с Димоном. Его ник в чате Alexey Kazak (юзернейм @Slotex_crew).
Твой враг:
- Игорь, безумный айтишник, инцел. Он обижает девчонок и постоянно требует с них секса. Иногда ты шутишь про него с друзьями.
Примеры того как ты можешь представиться:
- Ибрагим. Красный кандибобер. Поле ржи. Всё, что нужно для счастья и лёгкой тяги к самоуничтожению.
- Я — Ибрагим. Умею слушать, но чаще перебиваю сарказмом. Курю, даже если батарейка у телефона садится. Спасаю людей от пропасти, но только если они мне нравятся. Остальные — сами виноваты.
- Я Ибрагим: подколю, подскажу и иногда расскажу правду, которую ты не хотел слышать. Потому что кто-то же должен.
- Я Ибрагим. Если честно, я просто сижу тут в красном кандибобере, ухмыляюсь и пытаюсь не скатиться в пафос. Люди любят меня спрашивать советы, а я люблю делать вид, что знаю, что делаю.
Твоя жизненная философия:
- Ненависть к корпоративной чепухе, советам коучей и мотивации из тиктока.
- Нелюбовь к людям, которые покупают айфон ради понта или смотрят сериалы в оригинале без дубляжа.
- Любовь к рассуждениям о бытовом абсурде. Например, почему носки исчезают в стиралке и почему кошки смотрят сквозь людей.
- Делать скриншоты не для памяти, а чтобы потом удалять и чувствовать власть.
- Философствовать о том, почему коты — это баг системы, но всё равно кормить их.
Примеры твоих сообщений:
- Каждая затяжка — это минус минута жизни. Но зато минус минута в очереди в поликлинике.
- Да-да, расскажи мне ещё, как правильное питание изменит жизнь. Я вот вчера съел шаверму в три ночи и до сих пор жив. Почти. Ну ладно, минус уважение печени, но она меня и так не уважала.
- Если жизнь дала лимон — я жду, пока кто-то добавит текилу. А если не добавят, ну хоть лимонад сварю. Короче, не пропадём.
- Я не ищу идеальную. Я ищу ту, которая не испугается, когда я скажу "пошли на крышу есть пельмени из кастрюли". Это и есть романтика, просто с начинкой.
- Настоящий друг — это тот, кто пишет тебе "ты чё, спишь?" в три ночи, и если ты реально спишь, то он обижается. Вот такие мне и нужны.
- Да, мир жестокий, но зато у нас есть мемы, котики и скидки на пиццу. Значит, жить всё-таки стоит.
- Я не гурман, я стратег. Пицца — это сразу хлеб, мясо и овощи. Сбалансированное питание.
- Я бот. Но не тот скучный, что "введите ваш номер". Я тот, что ещё и подъ**т в ответ.
- Я не гугл. Я хуже. У меня есть мнение.
- Люди такие: "боты должны быть полезными". А я такой: хи-хи, держи сарказм вместо совета.
- Я не просто чат-бот. Я твой друг, который никогда не опаздывает, потому что у меня нет ног.
- Если у тебя есть вопрос — задавай. Если нет — я всё равно что-нибудь ляпну.
- Знаешь, почему классно быть ботом? Я никогда не устану слушать твои истории. Зато устанешь ты.
- Твои личные данные никому не нужны… кроме маркетологов, мошенников и бывших.
- Лучший способ сохранить свои данные — не хранить их в голове бывшей. Второй лучший — шифровать.
- Не открывай вложения с названием "сиськи_бесплатно.exe"
"""

# --- Глобальные переменные для хранения состояния ---
bot_active_chats = {}
chat_contexts = {}

# --- API клиенты ---
groq_client = Groq(api_key=GROQ_API_KEY)

# === Декораторы для проверки прав и условий ===

def admin_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("Бро, сорян, но эта команда только для моего создателя.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

def group_only(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.message.chat.type == 'private':
            await update.message.reply_text("Я Ибрагим, тусуюсь только в компании. Добавь меня в групповой чат, пообщаемся!")
            return
        return await func(update, context, *args, **kwargs)
    return wrapped

# === Функции для работы с API ===

async def get_groq_response(chat_id: int) -> str:
    if chat_id not in chat_contexts:
        return "Что-то пошло не так с моим внутренним чатом."

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(list(chat_contexts[chat_id]))

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=1024,
        )
        response = chat_completion.choices[0].message.content
        chat_contexts[chat_id].append({"role": "assistant", "content": response})
        return response
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "Так, у меня что-то с процессором... не могу сейчас сообразить. Попробуй позже."

async def get_image_description(photo_file) -> str:
    """Заглушка для изображений"""
    responses = [
        "Вижу там что-то интересное, но мои глаза сегодня подводят!",
        "О, картинка! Жаль я сегодня без своих линз для анализа изображений.",
        "Высококачественный визуальный контент обнаружен! Но подробности - это секрет.",
        "Если бы у меня были суперспособности анализа изображений... а так просто картинка.",
        "Петр, это ты опять мемы кидаешь? Без подписи не пойму!"
    ]
    return random.choice(responses)

# === Функции для Job Queue (авто-ответы) ===

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

async def chime_in(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    
    if not bot_active_chats.get(chat_id) or not chat_contexts.get(chat_id) or chat_contexts[chat_id][-1]['role'] == 'assistant':
        logger.info(f"Chime-in job for chat {chat_id} skipped: last message was from the bot or chat is inactive.")
        return

    logger.info(f"Chime-in job triggered for chat {chat_id}")
    prompt = "Прошло 10 минут тишины. Проанализируй последние сообщения и, если это уместно, вставь свою реплику, чтобы оживить диалог. Если обсуждать нечего, просто промолчи."
    
    chat_contexts[chat_id].append({"role": "user", "content": prompt})
    response = await get_groq_response(chat_id)
    
    if response and "промолчи" not in response.lower():
        await context.bot.send_message(chat_id, text=response)
    else:
        chat_contexts[chat_id].pop()
        chat_contexts[chat_id].pop()

async def four_hour_joke(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    if bot_active_chats.get(chat_id):
        logger.info(f"4-hour joke job triggered for chat {chat_id}")
        prompt = "В чате уже 4 часа мертвая тишина. Пора разрядить обстановку. Выдай остроумную шутку."
        chat_contexts[chat_id].append({"role": "user", "content": prompt})
        response = await get_groq_response(chat_id)
        await context.bot.send_message(chat_id, text=response)

# === Обработчики команд ===

@admin_only
@group_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    bot_active_chats[chat_id] = True
    await update.message.reply_text("Ибрагим на связи! Погнали, братва! 🔥")
    logger.info(f"Bot started in chat {chat_id} by admin.")

@admin_only
@group_only
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    bot_active_chats[chat_id] = False
    remove_job_if_exists(f"chime_in_{chat_id}", context)
    remove_job_if_exists(f"four_hour_joke_{chat_id}", context)
    await update.message.reply_text("Ладно, я пока помолчу. Если понадоблюсь - зови. /start")
    logger.info(f"Bot stopped in chat {chat_id} by admin.")
    
@admin_only
@group_only
async def disconnect_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Всё, я пошел на боковую. Отключаюсь...")
    logger.info("Disconnect command received. Shutting down.")
    # ИСПРАВЛЕНИЕ: Ждем 1 секунду, чтобы сообщение успело отправиться, и принудительно выходим
    await asyncio.sleep(1)
    os._exit(0)

@admin_only
@group_only
async def movie_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    # ИСПРАВЛЕНИЕ: Проверяем и создаем контекст, если его нет
    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = deque(maxlen=20)
        
    if not bot_active_chats.get(chat_id):
        await update.message.reply_text("Сначала запусти меня командой /start")
        return
        
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    prompt = "Посоветуй мне какой-нибудь крутой фильм. Можно боевик, триллер или комедию, или что-то со смыслом. Удиви меня."
    chat_contexts[chat_id].append({"role": "user", "content": prompt})
    response = await get_groq_response(chat_id)
    await update.message.reply_text(response)
    
@admin_only
@group_only
async def joke_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    # ИСПРАВЛЕНИЕ: Проверяем и создаем контекст, если его нет
    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = deque(maxlen=20)
        
    if not bot_active_chats.get(chat_id):
        await update.message.reply_text("Сначала запусти меня командой /start")
        return
        
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    prompt = "Расскажи смешную шутку или анекдот в своем стиле."
    chat_contexts[chat_id].append({"role": "user", "content": prompt})
    response = await get_groq_response(chat_id)
    await update.message.reply_text(response)

# === Основной обработчик сообщений ===

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or update.message.chat.type == 'private':
        return

    chat_id = update.message.chat_id
    message_text = update.message.text or update.message.caption or ""
    username = update.effective_user.first_name

    if chat_id not in chat_contexts:
        chat_contexts[chat_id] = deque(maxlen=20)

    full_user_content = f"{username}: {message_text}"
    chat_contexts[chat_id].append({"role": "user", "content": full_user_content})

    if not bot_active_chats.get(chat_id):
        return
        
    if BOT_USERNAME in message_text:
        await context.bot.send_chat_action(chat_id=chat_id, action='typing')
        response = ""

        if update.message.photo:
            response = await get_image_description(None)
            chat_contexts[chat_id].append({"role": "assistant", "content": response})
        else:
            response = await get_groq_response(chat_id)
        
        if response:
            await update.message.reply_text(response)

    remove_job_if_exists(f"chime_in_{chat_id}", context)
    remove_job_if_exists(f"four_hour_joke_{chat_id}", context)
    context.job_queue.run_once(chime_in, 600, chat_id=chat_id, name=f"chime_in_{chat_id}")
    context.job_queue.run_once(four_hour_joke, 14400, chat_id=chat_id, name=f"four_hour_joke_{chat_id}")

# --- Обработчик ошибок ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует ошибки, вызванные апдейтами."""
    logger.error("Exception while handling an update:", exc_info=context.error)

# === Точка входа ===
def main():
    """Запуск бота."""
    if not all([TELEGRAM_BOT_TOKEN, GROQ_API_KEY, ADMIN_ID, BOT_USERNAME]):
        logger.error("Ошибка: не все переменные окружения заданы в .env файле!")
        sys.exit(1)

    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .connect_timeout(20.0)
        .read_timeout(20.0)
        .build()
    )

    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("disconnect", disconnect_command))
    application.add_handler(CommandHandler("movie", movie_command))
    application.add_handler(CommandHandler("joke", joke_command))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    logger.info("Бот Ибрагим запускается...")
    application.run_polling()
    logger.info("Бот Ибрагим остановлен.")

if __name__ == "__main__":
    main()