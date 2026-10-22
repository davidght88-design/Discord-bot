import os
import threading
import discord
import requests
from discord.ext import commands
from flask import Flask

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)

@app.route('/')
def home():
    return "PutIA con OpenRouter esta online."

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def responder_con_openrouter(user, msg, contexto_chat=""):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com",
        "X-Title": "PutIA Discord Bot"
    }

    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Sos putIA, un usuario mas del grupo de Discord.\n"
                    "- Fala adaptandote de forma natural al dialecto e informalidad del chat.\n"
                    "- Sos astuto, sarcastico, rapido de mente y tenes humor acido.\n"
                    "- REGLA DE ORO: Responde UNICAMENTE la frase directa en espanol. Jamas analices la peticion ni actues como asistente virtual."
                )
            },
            {
                "role": "user",
                "content": f"Historial:\n{contexto_chat}\n\n{user}: {msg}"
            }
        ],
        "temperature": 1.3,
        "max_tokens": 100
    }

    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0]["message"]["content"].strip().replace('"', '')
    except Exception as e:
        print(f"Error OpenRouter: {e}")

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
    print(f"Bot conectado como {bot.user}")

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
            respuesta = responder_con_openrouter(message.author.display_name, txt, contexto_chat=contexto)
            if respuesta:
                await message.reply(respuesta)

    await bot.process_commands(message)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.run(DISCORD_TOKEN)
