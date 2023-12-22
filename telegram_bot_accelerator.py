import json
import os
from typing import Union, TypedDict

import requests
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram import __version__ as TG_VER
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters, CallbackContext, \
    CallbackQueryHandler, Application

from logger import logger

"""
start - Start the bot
set_engine - To choose the engine 
set_language - To choose language of your choice
"""

load_dotenv()

botName = os.environ['botName']

concurrent_updates = int(os.getenv('concurrent_updates', '8'))
pool_time_out = int(os.getenv('pool_timeout', '30'))
connection_pool_size = int(os.getenv('connection_pool_size', '512'))

# bot = Bot(token=os.environ['token'])
# bot.request.max_connections = connection_pool_size
# bot.request.connect_timeout = pool_time_out

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

language_msg_mapping: dict = {
    "en": "You have chosen English. \nPlease give your query now",
    "bn": "আপনি বাংলা বেছে নিয়েছেন। \nঅনুগ্রহ করে এখন আপনার প্রশ্ন দিন",
    "gu": "તમે ગુજરાતી પસંદ કર્યું છે. \nકૃપા કરીને હવે તમારો પ્રશ્ન પૂછો",
    "hi": "आपने हिंदी चुना है। \nआप अपना सवाल अब हिंदी में पूछ सकते हैं।",
    "kn": "ಕನ್ನಡ ಆಯ್ಕೆ ಮಾಡಿಕೊಂಡಿದ್ದೀರಿ. \nದಯವಿಟ್ಟು ಈಗ ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ನೀಡಿ",
    "ml": "നിങ്ങൾ മലയാളം തിരഞ്ഞെടുത്തു. \nദയവായി നിങ്ങളുടെ ചോദ്യം ഇപ്പോൾ നൽകുക",
    "mr": "तुम्ही मराठीची निवड केली आहे. \nकृपया तुमची शंका आता द्या",
    "or": "ଆପଣ ଓଡିଆକୁ ବାଛିଛନ୍ତି | \n ବର୍ତ୍ତମାନ ଆପଣଙ୍କର ଜିଜ୍ଞାସା ଦିଅନ୍ତୁ |",
    "pa": "ਤੁਸੀਂ ਪੰਜਾਬੀ ਨੂੰ ਚੁਣਿਆ ਹੈ। \nਕਿਰਪਾ ਕਰਕੇ ਹੁਣੇ ਆਪਣੀ ਪੁੱਛਗਿੱਛ ਦਿਓ",
    "ta": "நீங்கள் தமிழைத் தேர்ந்தெடுத்துள்ளீர்கள். \nஉங்கள் வினவலை இப்போதே தரவும்",
    "te": "మీరు తెలుగును ఎంచుకున్నారు. \nదయచేసి ఇప్పుడు మీ ప్రశ్నను ఇవ్వండి"
}


async def send_message_to_bot(chat_id, text, context: CallbackContext, parse_mode="Markdown", ) -> None:
    """Send a message  to bot"""
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_name = update.message.chat.first_name
    logger.info({"id": update.effective_chat.id, "username": user_name, "category": "logged_in", "label": "logged_in"})
    await send_message_to_bot(update.effective_chat.id,
                              f"Hello, {user_name}! I am **{botName}**, your companion. \n\nI can assist you in finding stories, rhymes, puzzles, and a variety of other enjoyable activities.  \n\nFurthermore, I can also answer your questions  or offer assistance with any other needs you may have.", context)
    await send_message_to_bot(update.effective_chat.id, "What would you like to do today?", context)
    await relay_handler(update, context)


async def relay_handler(update: Update, context: CallbackContext):
    # setting engine manually
    language = context.user_data.get('language')

    if language is None:
        await language_handler(update, context)
    # else:
    # await keyword_handler(update, context)


async def language_handler(update: Update, context: CallbackContext):
    inline_keyboard_buttons = [
        [InlineKeyboardButton('English', callback_data='lang_en')],
        [InlineKeyboardButton('বাংলা', callback_data='lang_bn')],
        [InlineKeyboardButton('ગુજરાતી', callback_data='lang_gu')],
        [InlineKeyboardButton('हिंदी', callback_data='lang_hi')],
        [InlineKeyboardButton('ಕನ್ನಡ', callback_data='lang_kn')],
        [InlineKeyboardButton('മലയാളം', callback_data='lang_ml')],
        [InlineKeyboardButton('मराठी', callback_data='lang_mr')], [InlineKeyboardButton('ଓଡ଼ିଆ', callback_data='or')],
        [InlineKeyboardButton('ਪੰਜਾਬੀ', callback_data='lang_pa')],
        [InlineKeyboardButton('தமிழ்', callback_data='lang_ta')],
        [InlineKeyboardButton('తెలుగు', callback_data='lang_te')]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard_buttons)

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Choose a Language:", reply_markup=reply_markup)


async def preferred_language_callback(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    preferred_language = callback_query.data.lstrip('lang_')
    context.user_data['language'] = preferred_language

    text_message = language_msg_mapping[preferred_language]
    logger.info(
        {"id": update.effective_chat.id, "username": update.effective_chat.first_name, "category": "language_selection",
         "label": "engine_selection", "value": preferred_language})
    await send_message_to_bot(update.effective_chat.id, text_message, context)
    return query_handler


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


class ApiResponse(TypedDict):
    output: any


class ApiError(TypedDict):
    error: Union[str, requests.exceptions.RequestException]


async def get_query_response(query: str, voice_message_url: str, voice_message_language: str) -> Union[
    ApiResponse, ApiError]:
    _domain = os.environ['upstream']
    audienceType = os.environ['audienceType']
    params: dict
    try:
        if voice_message_url is None:
            reqBody = json.dumps({
                "input": {
                    "language": voice_message_language,
                    "text": query,
                    'audienceType': audienceType
                },
                "output": {
                    'format': 'text'
                }
            })
        else:
            reqBody = json.dumps({
                "input": {
                    "language": voice_message_language,
                    "audio": voice_message_url,
                    'audienceType': audienceType
                },
                "output": {
                    'format': 'audio'
                }
            })
        url = f'{_domain}/v1/query'
        response = requests.post(url, data=reqBody)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        return {'error': e}
    except (KeyError, ValueError):
        return {'error': 'Invalid response received from API'}


async def response_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await query_handler(update, context)


async def query_handler(update: Update, context: CallbackContext):
    voice_message_language = context.user_data.get('language') or 'en'
    voice_message = None
    query = None
    if update.message.text:
        query = update.message.text
        logger.info(
            {"id": update.effective_chat.id, "username": update.effective_chat.first_name, "category": "query_handler",
             "label": "question", "value": query})
    elif update.message.voice:
        voice_message = update.message.voice

    voice_message_url = None
    if voice_message is not None:
        voice_file = await voice_message.get_file()
        voice_message_url = voice_file.file_path
        logger.info(
            {"id": update.effective_chat.id, "username": update.effective_chat.first_name, "category": "query_handler",
             "label": "voice_question", "value": voice_message_url})
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Just a few seconds...')
    await context.bot.sendChatAction(chat_id=update.effective_chat.id, action="typing")
    await handle_query_response(update, context, query, voice_message_url, voice_message_language)
    return query_handler


async def handle_query_response(update: Update, context: CallbackContext, query: str, voice_message_url: str, voice_message_language: str):
    response = await get_query_response(query, voice_message_url, voice_message_language)
    if "error" in response:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                               text='An error has been encountered. Please try again.')
        info_msg = {"id": update.effective_chat.id, "username": update.effective_chat.first_name,
                    "category": "handle_query_response", "label": "question_sent", "value": query}
        logger.info(info_msg)
        merged = dict()
        merged.update(info_msg)
        merged.update(response)
        logger.error(merged)
    else:
        logger.info({"id": update.effective_chat.id, "username": update.effective_chat.first_name,
                     "category": "handle_query_response", "label": "answer_received", "value": query})
        answer = response['output']["text"]
        await context.bot.send_message(chat_id=update.effective_chat.id, text=answer, parse_mode="Markdown")
        if response['output']["audio"]:
            audio_output_url = response['output']["audio"]
            audio_request = requests.get(audio_output_url)
            audio_data = audio_request.content
            await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_data)


def main() -> None:
    logger.info('################################################')
    logger.info('# Telegram bot name %s', os.environ['botName'])
    logger.info('################################################')

    logger.info({"concurrent_updates": concurrent_updates})
    logger.info({"pool_time_out": pool_time_out})
    logger.info({"connection_pool_size": connection_pool_size})

    application = Application.builder().token(os.environ['token']).pool_timeout(pool_time_out).connection_pool_size(connection_pool_size).concurrent_updates(concurrent_updates).connect_timeout(pool_time_out).read_timeout(pool_time_out).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler('select_language', language_handler))

    application.add_handler(CallbackQueryHandler(preferred_language_callback, pattern=r'lang_\w*'))

    application.add_handler(MessageHandler(filters.TEXT | filters.VOICE, response_handler))

    application.run_polling()


if __name__ == "__main__":
    main()
