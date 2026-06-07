import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from pydub import AudioSegment
import speech_recognition as sr
from aiohttp import web

# Твой токен для голосового бота
BOT_TOKEN = "8529141308:AAHhZeA2Jpclx5emLC4_gp5E9LTAggWsz2Y"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.voice)
async def handle_voice(message: Message):
    msg = await message.reply("⏳ <i>Слушаю и перевожу в текст...</i>", parse_mode="HTML")
    
    file_id = message.voice.file_id
    ogg_path = f"voice_{file_id}.ogg"
    wav_path = f"voice_{file_id}.wav"
    
    try:
        # 1. Скачиваем голосовуху
        await bot.download(message.voice, destination=ogg_path)
        
        # 2. Конвертируем OGG в WAV
        audio = AudioSegment.from_file(ogg_path)
        audio.export(wav_path, format="wav")
        
        # 3. Распознаем текст через Google
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            
        # --- НАВОДИМ КРАСОТУ (Заглавная буква и точка) ---
        if text:
            text = text[0].upper() + text[1:]
            if not text.endswith(('.', '!', '?')):
                text += '.'
        # -------------------------------------------------
            
        # 4. Отправляем текст обратно в виде цитаты
        await msg.edit_text(f"<blockquote>{text}</blockquote>", parse_mode="HTML")
        
    except sr.UnknownValueError:
        await msg.edit_text("🤷‍♂️ <i>Не смог разобрать слова. Попробуй сказать четче.</i>", parse_mode="HTML")
    except Exception as e:
        await msg.edit_text("❌ <i>Произошла ошибка при обработке аудио.</i>", parse_mode="HTML")
        print(f"Ошибка: {e}")
    finally:
        if os.path.exists(ogg_path): os.remove(ogg_path)
        if os.path.exists(wav_path): os.remove(wav_path)

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.reply("Привет! Просто перешли мне любое голосовое сообщение, и я переведу его в текст 📝")

# Маленький веб-сервер, чтобы Render понимал, что бот жив
async def handle_ping(request):
    return web.Response(text="Бот работает!")

async def main():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    print("Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
