import discord
from discord.ext import commands
import os
from gemini import chat_with_gemini
from flask import Flask
from threading import Thread
import textwrap

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

app = Flask('')

# --- Nouvelle fonction de découpage ---
def split_message(content, max_length=1950):
    """
    Découpe une longue chaîne de caractères en plusieurs morceaux 
    compatibles avec la limite Discord. On utilise 1950 pour laisser une marge.
    """
    # Découpe le contenu en chunks (morceaux)
    chunks = textwrap.wrap(content, max_length, break_long_words=False, replace_whitespace=False)
    
    # Si le découpage standard ne fonctionne pas bien, on utilise un découpage simple
    if not chunks:
        return [content[i:i + max_length] for i in range(0, len(content), max_length)]

    return chunks
# --- Fin de la nouvelle fonction ---

@app.route('/')
def home():
    return "Bot en ligne!"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.start()

@bot.event
async def on_ready():
    print(f'{bot.user} s\'est connecté à Discord!')
    print(f'Bot ID: {bot.user.id}')
    print('------')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.startswith('!'):
        await bot.process_commands(message)
        return

    if len(message.content) > 0:
        async with message.channel.typing():
            try:
                response = chat_with_gemini(message.content)

                #if len(response) > 2000:
                   # response = response[:1997] + "..."
                message_chunks = split_message(response)
                first_chunk = True
                for chunk in message_chunks:
                    if first_chunk:
                        # Le premier morceau utilise 'message.reply' pour mentionner l'utilisateur
                        await message.reply(chunk)
                        first_chunk = False
                    else:
                        # Les morceaux suivants sont envoyés sans mention, dans le même canal
                        await message.channel.send(chunk)
                
                await message.reply(response)
            except Exception as e:
                print(f"Erreur lors de l'appel à Gemini: {e}")
                await message.reply(
                    f"Désolé, une erreur s'est produite: {str(e)}")

    await bot.process_commands(message)

@bot.command(name='help', help='Affiche cette aide')
async def help_command(ctx):
    embed = discord.Embed(title="🤖 Aide du Bot",
                          description="Voici les commandes disponibles:",
                          color=discord.Color.blue())
    embed.add_field(name="!help",
                    value="Affiche ce message d'aide",
                    inline=False)
    embed.add_field(name="!info",
                    value="Informations sur le bot",
                    inline=False)
    embed.add_field(name="!ping",
                    value="Vérifie la latence du bot",
                    inline=False)
    embed.add_field(
        name="💬 Réponses automatiques",
        value=
        "Posez-moi n'importe quelle question et je répondrai intelligemment avec Gemini AI!",
        inline=False)
    await ctx.send(embed=embed)

@bot.command(name='info', help='Informations sur le bot')
async def info_command(ctx):
    embed = discord.Embed(title="ℹ️ Informations du Bot",
                          description="Bot Discord créé en Python",
                          color=discord.Color.green())
    embed.add_field(name="Nom", value=bot.user.name, inline=True)
    embed.add_field(name="ID", value=bot.user.id, inline=True)
    embed.add_field(name="Serveurs", value=len(bot.guilds), inline=True)
    await ctx.send(embed=embed)

@bot.command(name='ping', help='Vérifie la latence du bot')
async def ping_command(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latence: {latency}ms')

if __name__ == '__main__':
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print(
            "ERREUR: La variable d'environnement DISCORD_BOT_TOKEN n'est pas définie!"
        )
        print("Veuillez configurer votre token Discord dans les Secrets.")
    else:
        try:
            keep_alive()
            bot.run(token)
        except discord.LoginFailure:
            print(
                "ERREUR: Token Discord invalide. Vérifiez votre DISCORD_BOT_TOKEN."
            )
        except Exception as e:
            print(f"ERREUR: Une erreur est survenue: {e}")
