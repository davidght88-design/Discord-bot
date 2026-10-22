import os
import threading
import discord
import requests
from discord.ext import commands
from flask import Flask

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)

@app.route('/')
def home():
    return "PutIA está online y operando."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def responder_con_gemini(user, msg, contexto_chat=""):
    payload = {
        "systemInstruction": {
            "parts": [{
                "text": (
                    "Sos putIA, un usuario más del grupo de Discord.\n"
                    "- Hablá adaptándote de forma natural al dialecto e informalidad del chat.\n"
                    "- Sos astuto, sarcástico, rápido de mente y tenés humor ácido.\n"
                    "- REGLA DE ORO: Respondé ÚNICAMENTE la frase directa en español. Jamás analices la petición, jamás pienses en voz alta en inglés ni actúes como asistente virtual."
                )
            }]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{
                    "text": f"Historial del chat:\n{contexto_chat}\n\n{user}: {msg}"
                }]
            }
        ],
        "generationConfig": {
            "temperature": 0.95,
            "maxOutputTokens": 100
        }
    }

    try:
        response = requests.post(GEMINI_URL, json=payload, timeout=15)
        if response.status_code == 200:
            data = response.json()
            candidates = data.get("candidates", [])
            if candidates:
                text = candidates[0]["content"]["parts"][0]["text"].strip()
                return text.replace('"', '')
        else:
            print(f"⚠️ Error HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"⚠️ Error de conexión: {e}")

    return None

async def obtener_contexto_canal(channel, limite=5):
    try:
        mensajes_previos = []
        async for msg in channel.history(limit=limite):
            if not msg.author.bot and msg.content:
                mensajes_previos.append(f"{msg.author.display_name}: {msg.content}")
        mensajes_previos.reverse()
        return "\n".join(mensajes_previos)
    except Exception:
        return ""

@bot.event
async def on_ready():
    print(f"✅ PutIA lista y conectada en Render: {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    es_mencion = bot.user in message.mentions
    es_reply = message.reference and message.reference.resolved and message.reference.resolved.author == bot.user

    if es_mencion or es_reply:
        async with message.channel.typing():
            txt = message.content.replace(f'<@{bot.user.id}>', '').strip()
            contexto = await obtener_contexto_canal(message.channel, limite=5)
            respuesta = responder_con_gemini(message.author.display_name, txt, contexto_chat=contexto)
            if respuesta:
                await message.reply(respuesta)

    await bot.process_commands(message)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(DISCORD_TOKEN)
