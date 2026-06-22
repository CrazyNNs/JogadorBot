import discord
from discord.ext import commands
from discord import app_commands
import random
import datetime
import sqlite3
import os
import aiohttp
from PIL import Image, ImageDraw, ImageFont
import io

# ============================================================
# CONFIGURAÇÃO
# ============================================================
TOKEN = os.environ.get("TOKEN")
PREFIX = "!"
CANAL_CONQUISTAS_ID = 1517028501356806144  # ← ID do seu canal de conquistas
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ============================================================
# BANCO DE DADOS
# ============================================================
def iniciar_banco():
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conquistas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            emoji TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS conquistas_usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT NOT NULL,
            conquista_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            FOREIGN KEY (conquista_id) REFERENCES conquistas(id)
        )
    """)
    con.commit()
    con.close()

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def buscar_conquistas_usuario(usuario_id):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT c.nome, c.descricao, c.emoji, cu.data
        FROM conquistas_usuarios cu
        JOIN conquistas c ON cu.conquista_id = c.id
        WHERE cu.usuario_id = ?
        ORDER BY cu.data DESC
    """, (str(usuario_id),))
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_todas_conquistas():
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, descricao, emoji FROM conquistas ORDER BY nome")
    resultado = cur.fetchall()
    con.close()
    return resultado

async def gerar_card_perfil(usuario: discord.Member):
    async with aiohttp.ClientSession() as session:
        async with session.get(str(usuario.display_avatar.url)) as resp:
            avatar_bytes = await resp.read()

    # Avatar circular — 110px para caber no círculo
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((110, 110))
    mascara = Image.new("L", (110, 110), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, 110, 110), fill=255)
    avatar_circular = Image.new("RGBA", (110, 110), (0, 0, 0, 0))
    avatar_circular.paste(avatar, mask=mascara)

    # Abre o fundo
    card = Image.open("perfil.png").convert("RGBA").resize((800, 400))
    draw = ImageDraw.Draw(card)

    # Cola o avatar no círculo (ajuste x e y se precisar)
    card.paste(avatar_circular, (45, 45), avatar_circular)

    # Fontes
    try:
        fonte_nome = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        fonte_info = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        fonte_nome = ImageFont.load_default()
        fonte_info = ImageFont.load_default()

    # Nickname na barra cinza
    draw.text((190, 45), usuario.display_name, font=fonte_nome, fill=(255, 255, 255))

    # @ e conquistas abaixo da barra
    draw.text((190, 55), f"@{usuario.name}", font=fonte_info, fill=(200, 200, 200))
    conquistas = buscar_conquistas_usuario(usuario.id)
    draw.text((190, 125), f"{len(conquistas)} conquista(s)", font=fonte_info, fill=(212, 175, 55))

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer, len(conquistas)

# ============================================================
# VIEWS (BOTÕES)
# ============================================================
class ViewPerfil(discord.ui.View):
    def __init__(self, usuario: discord.Member):
        super().__init__(timeout=120)
        self.usuario = usuario

    @discord.ui.button(label="🏆 Conquistas", style=discord.ButtonStyle.primary)
    async def ver_conquistas(self, interaction: discord.Interaction, button: discord.ui.Button):
        conquistas = buscar_conquistas_usuario(self.usuario.id)
        if not conquistas:
            await interaction.response.send_message("Este usuário ainda não tem conquistas!", ephemeral=True)
            return
        view = ViewConquistas(self.usuario, conquistas, pagina=0)
        embed = view.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ViewConquistas(discord.ui.View):
    def __init__(self, usuario: discord.Member, conquistas: list, pagina: int):
        super().__init__(timeout=120)
        self.usuario = usuario
        self.conquistas = conquistas
        self.pagina = pagina
        self.por_pagina = 10
        self.total_paginas = max(1, -(-len(conquistas) // self.por_pagina))
        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.anterior.disabled = self.pagina == 0
        self.proximo.disabled = self.pagina >= self.total_paginas - 1

    def gerar_embed(self):
        inicio = self.pagina * self.por_pagina
        fim = inicio + self.por_pagina
        pagina_conquistas = self.conquistas[inicio:fim]

        embed = discord.Embed(
            title=f"🏆 Conquistas de {self.usuario.display_name}",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.usuario.display_avatar.url)

        for nome, descricao, emoji, data in pagina_conquistas:
            embed.add_field(
                name=f"{emoji} {nome}",
                value=f"{descricao}\n📅 {data}",
                inline=False
            )

        embed.set_footer(text=f"Página {self.pagina + 1} de {self.total_paginas} • {len(self.conquistas)} conquista(s) no total")
        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina -= 1
        self.atualizar_botoes()
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina += 1
        self.atualizar_botoes()
        await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

    @discord.ui.button(label="🔙 Voltar ao Perfil", style=discord.ButtonStyle.danger)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        buffer, total = await gerar_card_perfil(self.usuario)
        arquivo = discord.File(buffer, filename="perfil.png")
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_image(url="attachment://perfil.png")
        view = ViewPerfil(self.usuario)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[arquivo])

# ============================================================
# EVENTOS
# ============================================================
@bot.event
async def on_ready():
    iniciar_banco()
    await bot.tree.sync()
    print(f"✅ Bot conectado como: {bot.user}")
    print(f"   Servidores: {len(bot.guilds)}")
    await bot.change_presence(activity=discord.Game(name="!perfil para ver seu perfil"))

# ============================================================
# COMANDOS DE PREFIXO
# ============================================================
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
    embed = discord.Embed(title=f"Informações de {membro.name}", color=discord.Color.blue())
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
    embed = discord.Embed(title="📊 Enquete", description=pergunta, color=discord.Color.gold())
    embed.set_footer(text=f"Pergunta feita por {ctx.author.display_name}")
    mensagem = await ctx.send(embed=embed)
    await mensagem.add_reaction("✅")
    await mensagem.add_reaction("❌")
    await ctx.message.delete()

@bot.command(name="coelho")
async def coelho(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://some-random-api.com/animal/rabbit") as resposta:
            if resposta.status == 200:
                dados = await resposta.json()
                embed = discord.Embed(title="🐰 Coelho aleatório!", color=discord.Color.pink())
                embed.set_image(url=dados["image"])
                embed.set_footer(text=f"Pedido por {ctx.author.display_name}")
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Não consegui buscar um coelho agora. Tenta de novo!")

@bot.command(name="perfil")
async def perfil(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author
    async with ctx.typing():
        buffer, total = await gerar_card_perfil(membro)
        arquivo = discord.File(buffer, filename="perfil.png")
        embed = discord.Embed(color=discord.Color.blurple())
        embed.set_image(url="attachment://perfil.png")
        view = ViewPerfil(membro)
        await ctx.send(file=arquivo, embed=embed, view=view)

@bot.remove_command("help")
@bot.command(name="ajuda")
async def ajuda(ctx):
    embed = discord.Embed(
        title="📖 Lista de Comandos",
        description=f"Todos os comandos usam o prefixo `{PREFIX}`",
        color=discord.Color.green()
    )
    embed.add_field(name="!oi", value="Bot te cumprimenta", inline=False)
    embed.add_field(name="!dado [lados]", value="Rola um dado. Ex: `!dado 20`", inline=False)
    embed.add_field(name="!moeda", value="Joga uma moeda (cara ou coroa)", inline=False)
    embed.add_field(name="!hora", value="Mostra a data e hora atual", inline=False)
    embed.add_field(name="!userinfo [@usuario]", value="Mostra info de um usuário", inline=False)
    embed.add_field(name="!limpar [quantidade]", value="Apaga mensagens (requer permissão)", inline=False)
    embed.add_field(name="!enquete [pergunta]", value="Cria uma enquete com ✅ e ❌", inline=False)
    embed.add_field(name="!coelho", value="Manda uma foto aleatória de coelho", inline=False)
    embed.add_field(name="!perfil [@usuario]", value="Mostra o perfil com conquistas do usuário", inline=False)
    embed.add_field(name="/conquista criar", value="Cria uma nova conquista (admin)", inline=False)
    embed.add_field(name="/conquista dar", value="Dá uma conquista para um usuário (admin)", inline=False)
    embed.add_field(name="/conquista lista", value="Mostra todas as conquistas disponíveis", inline=False)
    await ctx.send(embed=embed)

# ============================================================
# COMANDOS SLASH — CONQUISTAS
# ============================================================
conquista_group = app_commands.Group(name="conquista", description="Sistema de conquistas")

@conquista_group.command(name="criar", description="Cria uma nova conquista no catálogo")
@app_commands.describe(
    nome="Nome da conquista (ex: Sortudo)",
    descricao="Descrição da conquista",
    emoji="Emoji que representa a conquista (ex: 🍀)"
)
@app_commands.checks.has_permissions(manage_roles=True)
async def conquista_criar(interaction: discord.Interaction, nome: str, descricao: str, emoji: str):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO conquistas (nome, descricao, emoji) VALUES (?, ?, ?)", (nome, descricao, emoji))
        con.commit()
        await interaction.response.send_message(f"✅ Conquista **{emoji} {nome}** criada com sucesso!", ephemeral=True)
    except sqlite3.IntegrityError:
        await interaction.response.send_message(f"❌ Já existe uma conquista com o nome **{nome}**.", ephemeral=True)
    finally:
        con.close()

@conquista_group.command(name="dar", description="Dá uma conquista para um usuário")
@app_commands.describe(
    membro="Quem vai receber a conquista",
    nome="Nome exato da conquista",
    midia="Foto ou vídeo opcional da conquista"
)
@app_commands.checks.has_permissions(manage_roles=True)
async def conquista_dar(interaction: discord.Interaction, membro: discord.Member, nome: str, midia: discord.Attachment = None):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()

    cur.execute("SELECT id, nome, descricao, emoji FROM conquistas WHERE LOWER(nome) = LOWER(?)", (nome,))
    conquista = cur.fetchone()

    if conquista is None:
        await interaction.response.send_message(f"❌ Conquista **{nome}** não encontrada. Use `/conquista lista` para ver as disponíveis.", ephemeral=True)
        con.close()
        return

    conquista_id, c_nome, c_descricao, c_emoji = conquista
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y")

    cur.execute("INSERT INTO conquistas_usuarios (usuario_id, conquista_id, data) VALUES (?, ?, ?)",
                (str(membro.id), conquista_id, data_atual))
    con.commit()
    con.close()

    canal = bot.get_channel(CANAL_CONQUISTAS_ID)
    if canal is None:
        await interaction.response.send_message("❌ Canal de conquistas não encontrado.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🏆 Nova Conquista Desbloqueada!",
        description=c_descricao,
        color=discord.Color.gold()
    )
    embed.add_field(name="Conquistador", value=membro.mention, inline=True)
    embed.add_field(name="Conquista", value=f"{c_emoji} {c_nome}", inline=True)
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text=f"Conquista concedida por {interaction.user.display_name} • {data_atual}")

    if midia is not None:
        if midia.content_type and midia.content_type.startswith("image/"):
            embed.set_image(url=midia.url)
            await canal.send(embed=embed)
        elif midia.content_type and midia.content_type.startswith("video/"):
            await canal.send(embed=embed)
            await canal.send(midia.url)
        else:
            await canal.send(embed=embed)
    else:
        await canal.send(embed=embed)

    await interaction.response.send_message(f"✅ Conquista **{c_emoji} {c_nome}** dada para {membro.mention}!", ephemeral=True)

@conquista_group.command(name="lista", description="Mostra todas as conquistas disponíveis no catálogo")
async def conquista_lista(interaction: discord.Interaction):
    conquistas = buscar_todas_conquistas()
    if not conquistas:
        await interaction.response.send_message("Nenhuma conquista criada ainda. Use `/conquista criar` para adicionar!", ephemeral=True)
        return
    embed = discord.Embed(title="📋 Catálogo de Conquistas", color=discord.Color.blurple())
    for _, nome, descricao, emoji in conquistas:
        embed.add_field(name=f"{emoji} {nome}", value=descricao, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.tree.add_command(conquista_group)

# ============================================================
# TRATAMENTO DE ERROS
# ============================================================
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Falta um argumento. Use `!ajuda` para ver como usar o comando.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Argumento inválido. Verifique se digitou corretamente.")
    elif isinstance(error, commands.CommandNotFound):
        pass

bot.run(TOKEN)
