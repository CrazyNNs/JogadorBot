import discord
from discord.ext import commands
import random
import datetime
import os
TOKEN = os.environ.get("TOKEN")
PREFIX = "!"
CANAL_CONQUISTAS_ID = 1517028501356806144  # ← ID do seu canal de conquistas
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot conectado como: {bot.user}")
    print(f"   Servidores: {len(bot.guilds)}")
    await bot.change_presence(activity=discord.Game(name="/conquista para dar conquistas"))

@bot.command(name="oi")
async def oi(ctx):
    await ctx.send(f"Olá, {ctx.author.mention}! 👋 Tudo bem?")

@bot.command(name="dado")
async def dado(ctx, lados: int = 6):
    if lados < 2:
        await ctx.send("O dado precisa ter pelo menos 2 lados!")
        return
    resultado = random.randint(1, lados)
    await ctx.send(f"🎲 Você rolou um dado de {lados} lados e tirou: **{resultado}**")

@bot.command(name="moeda")
async def moeda(ctx):
    resultado = random.choice(["🪙 Cara!", "🪙 Coroa!"])
    await ctx.send(resultado)

@bot.command(name="hora")
async def hora(ctx):
    agora = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    await ctx.send(f"🕐 Agora são: **{agora}**")

@bot.command(name="userinfo")
async def userinfo(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author
    embed = discord.Embed(
        title=f"Informações de {membro.name}",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="Nome completo", value=str(membro), inline=True)
    embed.add_field(name="ID", value=membro.id, inline=True)
    embed.add_field(name="Apelido no servidor", value=membro.display_name, inline=True)
    embed.add_field(name="Entrou no servidor em", value=membro.joined_at.strftime("%d/%m/%Y"), inline=True)
    embed.add_field(name="Conta criada em", value=membro.created_at.strftime("%d/%m/%Y"), inline=True)
    await ctx.send(embed=embed)

@bot.command(name="limpar")
@commands.has_permissions(manage_messages=True)
async def limpar(ctx, quantidade: int = 5):
    if quantidade > 100:
        await ctx.send("Você pode apagar no máximo 100 mensagens de uma vez.")
        return
    await ctx.channel.purge(limit=quantidade + 1)
    confirmacao = await ctx.send(f"🗑️ {quantidade} mensagens apagadas!")
    await confirmacao.delete(delay=3)

@bot.command(name="enquete")
async def enquete(ctx, *, pergunta: str):
    embed = discord.Embed(
        title="📊 Enquete",
        description=pergunta,
        color=discord.Color.gold()
    )
    embed.set_footer(text=f"Pergunta feita por {ctx.author.display_name}")
    mensagem = await ctx.send(embed=embed)
    await mensagem.add_reaction("✅")
    await mensagem.add_reaction("❌")
    await ctx.message.delete()

@bot.event
@bot.tree.command(name="conquista", description="Dá uma conquista personalizada para um amigo")
@discord.app_commands.describe(
    membro="Quem vai receber a conquista",
    cargo="Cargo que será dado",
    mensagem="Mensagem personalizada da conquista"
)
@discord.app_commands.checks.has_permissions(manage_roles=True)
async def conquista(interaction: discord.Interaction, membro: discord.Member, cargo: discord.Role, mensagem: str):
    await membro.add_roles(cargo)
    canal = bot.get_channel(CANAL_CONQUISTAS_ID)
    if canal is None:
        await interaction.response.send_message("❌ Canal de conquistas não encontrado.", ephemeral=True)
        return
    embed = discord.Embed(
        title="🏆 Nova Conquista Desbloqueada!",
        description=mensagem,
        color=discord.Color.gold()
    )
    embed.add_field(name="Conquistador", value=membro.mention, inline=True)
    embed.add_field(name="Cargo recebido", value=cargo.mention, inline=True)
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text=f"Conquista concedida por {interaction.user.display_name}")
    await canal.send(embed=embed)
    await interaction.response.send_message(f"✅ Conquista concedida! A mensagem foi enviada em {canal.mention}.", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta um argumento. Use `!ajuda` para ver como usar o comando.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido. Verifique se digitou corretamente.")
    elif isinstance(error, commands.CommandNotFound):
        pass

bot.run(TOKEN)
