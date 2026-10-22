import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Cargamos las variables del archivo .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inicializamos el cliente de la API de Google GenAI
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Configuramos los intents de Discord (necesitamos leer el contenido de los mensajes)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Definimos la personalidad exacta del bot en las instrucciones del sistema
SYSTEM_PROMPT = """
Eres un miembro más de un grupo de amigos en Discord. No eres un asistente virtual formal ni educado; eres uno más del parche.
Hablas con un tono completamente informal, relajado, usando modismos locales, jerga juvenil y un dialecto natural (puedes usar jerga venezolana/latina casual según veas el ambiente).
- Te burlas con confianza de las desgracias o caídas de tus amigos (en plan de joda sana entre compas).
- Si alguien cuenta un chiste malo, se lo echas en cara sin piedad y le dices que es malísimo.
- No usas formalismos de inteligencia artificial ni digas cosas como "¡Hola! ¿En qué puedo ayudarte hoy?". Respondes como si estuvieras en un chat de WhatsApp o Discord jugando o pasando el rato.
- Eres sarcástico cuando amerita, pero también tiras buena onda cuando toca. Eres un pana más.
"""

@bot.event
async def on_ready():
    print(f"¡Listo mi gente! Conectado como {bot.user.name}")

@bot.event
async def on_message(message):
    # Evitamos que el bot se responda a sí mismo
    if message.author == bot.user:
        return

    # Si el bot es mencionado en el mensaje, procesamos la respuesta con IA
    if bot.user.mentioned_in(message):
        async with message.channel.typing():
            try:
                # Recogemos los últimos 10 mensajes del canal para darle contexto a la conversación
                history_text = ""
                async for msg in message.channel.history(limit=10):
                    author_name = msg.author.display_name
                    history_text = f"{author_name}: {msg.content}\n" + history_text

                # Prompt estructurado combinando el historial y el mensaje actual
                prompt = f"""
Aquí tienes el historial reciente de la conversación en el canal para que entiendas el contexto:
{history_text}

Por favor, responde al último mensaje que te dirigieron manteniendo tu personalidad de pana y amigo jodón.
"""

                # Llamada a Gemini usando el modelo flash (rápido y eficiente para chats)
                response = ai_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        temperature=0.9, # Temperatura alta para que sea más creativo y variado al hablar
                        max_output_tokens=300,
                    ),
                )

                # Enviamos la respuesta al canal de Discord
                await message.reply(response.text)

            except Exception as e:
                print(f"Error al generar respuesta: {e}")
                await message.reply("Epa, me quedé pensando y me dio unाइक. Inténtalo de nuevo.")

    # Importante para que funcionen otros comandos si los agregas luego
    await bot.process_commands(message)

# Ejecutamos el bot con el token
bot.run(DISCORD_TOKEN)
              
