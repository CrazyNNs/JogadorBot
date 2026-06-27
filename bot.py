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
DONO_ID = 880243114403573780  # Seu ID — sempre tem acesso total
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS economia (
            usuario_id TEXT PRIMARY KEY,
            joyens INTEGER DEFAULT 0,
            ultimo_diario TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS banners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            preco INTEGER NOT NULL,
            arquivo TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS banners_usuarios (
            usuario_id TEXT NOT NULL,
            banner_id INTEGER NOT NULL,
            PRIMARY KEY (usuario_id, banner_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS banner_ativo (
            usuario_id TEXT PRIMARY KEY,
            banner_id INTEGER
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            usuario_id TEXT PRIMARY KEY,
            expira TEXT
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

# ============================================================
# FUNÇÕES AUXILIARES - Economia e loja de banners
# ============================================================

def buscar_joyens(usuario_id):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT joyens FROM economia WHERE usuario_id = ?", (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return resultado[0] if resultado else 0

def adicionar_joyens(usuario_id, quantidade):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO economia (usuario_id, joyens) VALUES (?, ?)
        ON CONFLICT(usuario_id) DO UPDATE SET joyens = joyens + ?
    """, (str(usuario_id), quantidade, quantidade))
    con.commit()
    con.close()

def remover_joyens(usuario_id, quantidade):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("UPDATE economia SET joyens = joyens - ? WHERE usuario_id = ?", (quantidade, str(usuario_id)))
    con.commit()
    con.close()

def buscar_todos_banners():
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, descricao, preco, arquivo FROM banners ORDER BY id")
    resultado = cur.fetchall()
    con.close()
    return resultado

def usuario_tem_banner(usuario_id, banner_id):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT 1 FROM banners_usuarios WHERE usuario_id = ? AND banner_id = ?", (str(usuario_id), banner_id))
    resultado = cur.fetchone()
    con.close()
    return resultado is not None

def buscar_banner_ativo(usuario_id):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT b.arquivo FROM banner_ativo ba
        JOIN banners b ON ba.banner_id = b.id
        WHERE ba.usuario_id = ?
    """, (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return resultado[0] if resultado else None

def parsear_tempo(tempo_str):
    """Converte string como 1d5h30m para segundos. Retorna None se for 'infinito'."""
    if tempo_str.lower() == "infinito":
        return None
    import re
    total = 0
    partes = re.findall(r"(\d+)([dhm])", tempo_str.lower())
    if not partes:
        raise ValueError("Formato inválido")
    for valor, unidade in partes:
        valor = int(valor)
        if unidade == "d":
            total += valor * 86400
        elif unidade == "h":
            total += valor * 3600
        elif unidade == "m":
            total += valor * 60
    return total

def eh_admin(usuario_id):
    """Verifica se o usuário é admin válido (não expirado)."""
    if usuario_id == DONO_ID:
        return True
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT expira FROM admins WHERE usuario_id = ?", (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    if not resultado:
        return False
    expira = resultado[0]
    if expira is None:
        return True
    return datetime.datetime.fromisoformat(expira) > datetime.datetime.now()

async def gerar_card_perfil(usuario: discord.Member):
    async with aiohttp.ClientSession() as session:
        async with session.get(str(usuario.display_avatar.url)) as resp:
            avatar_bytes = await resp.read()

    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((120, 120))
    mascara = Image.new("L", (120, 120), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, 120, 120), fill=255)
    avatar_circular = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    avatar_circular.paste(avatar, mask=mascara)

    card = Image.open("perfil.png").convert("RGBA").resize((800, 400))

    banner_arquivo = buscar_banner_ativo(usuario.id)
    if banner_arquivo and os.path.exists(banner_arquivo):
        banner = Image.open(banner_arquivo).convert("RGBA").resize((799, 262))
        card.paste(banner, (0, 137), banner)

    draw = ImageDraw.Draw(card)
    card.paste(avatar_circular, (40, 40), avatar_circular)

    fonte_nome = ImageFont.truetype("/app/fonte.ttf", 35)
    fonte_info = ImageFont.truetype("/app/fonte_regular.ttf", 30)

    draw.text((190, 35), usuario.display_name, font=fonte_nome, fill=(255, 255, 255))
    draw.text((190, 85), f"@{usuario.name}", font=fonte_info, fill=(100, 100, 100))
    conquistas = buscar_conquistas_usuario(usuario.id)
    draw.text((60, 365), f"{len(conquistas)} Conquistas", font=fonte_info, fill=(255, 255, 0))
    joyens = buscar_joyens(usuario.id)
    draw.text((400, 365), f"{joyens} Joyens", font=fonte_info, fill=(255, 215, 0))

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer, len(conquistas)

from discord.ext import tasks

@tasks.loop(minutes=5)
async def verificar_admins_expirados():
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    agora = datetime.datetime.now().isoformat()
    cur.execute("SELECT usuario_id FROM admins WHERE expira IS NOT NULL AND expira <= ?", (agora,))
    expirados = cur.fetchall()
    for (usuario_id,) in expirados:
        cur.execute("DELETE FROM admins WHERE usuario_id = ?", (usuario_id,))
        try:
            usuario = await bot.fetch_user(int(usuario_id))
            await usuario.send("⏰ Seu acesso de admin no **JogadorBot** expirou.")
        except:
            pass
    con.commit()
    con.close()

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
# VIEW (BOTÕES) - Loja de banners
# ============================================================

class ViewLoja(discord.ui.View):
    def __init__(self, usuario_id, banners, index=0):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.banners = banners
        self.index = index
        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.anterior.disabled = self.index == 0
        self.proximo.disabled = self.index >= len(self.banners) - 1
        banner_id = self.banners[self.index][0]
        self.comprar.disabled = usuario_tem_banner(self.usuario_id, banner_id)
        self.comprar.label = "✅ Já possui" if usuario_tem_banner(self.usuario_id, banner_id) else "🛒 Comprar"

    def gerar_embed(self):
        banner_id, nome, descricao, preco, arquivo = self.banners[self.index]
        joyens = buscar_joyens(self.usuario_id)
        tem = usuario_tem_banner(self.usuario_id, banner_id)
        embed = discord.Embed(
            title=f"🖼️ {nome}",
            description=descricao,
            color=discord.Color.purple()
        )
        embed.add_field(name="Preço", value=f"{preco} Joyens", inline=True)
        embed.add_field(name="Seu saldo", value=f"{joyens} Joyens", inline=True)
        if tem:
            embed.add_field(name="Status", value="✅ Você já possui este banner", inline=False)
        elif joyens < preco:
            embed.add_field(name="Status", value="❌ Joyens insuficientes", inline=False)
        if os.path.exists(arquivo):
            file = discord.File(arquivo, filename="preview.png")
            embed.set_image(url="attachment://preview.png")
        embed.set_footer(text=f"Banner {self.index + 1} de {len(self.banners)}")
        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        self.atualizar_botoes()
        embed = self.gerar_embed()
        banner_id, nome, descricao, preco, arquivo = self.banners[self.index]
        if os.path.exists(arquivo):
            arquivo_discord = discord.File(arquivo, filename="preview.png")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[arquivo_discord])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        self.atualizar_botoes()
        embed = self.gerar_embed()
        banner_id, nome, descricao, preco, arquivo = self.banners[self.index]
        if os.path.exists(arquivo):
            arquivo_discord = discord.File(arquivo, filename="preview.png")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[arquivo_discord])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🛒 Comprar", style=discord.ButtonStyle.success)
    async def comprar(self, interaction: discord.Interaction, button: discord.ui.Button):
        banner_id, nome, descricao, preco, arquivo = self.banners[self.index]
        joyens = buscar_joyens(self.usuario_id)
        if joyens < preco:
            await interaction.response.send_message(f"❌ Você não tem Joyens suficientes! Você tem {joyens} e precisa de {preco}.", ephemeral=True)
            return
        remover_joyens(self.usuario_id, preco)
        con = sqlite3.connect("/data/jogadorbot.db")
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO banners_usuarios (usuario_id, banner_id) VALUES (?, ?)", (str(self.usuario_id), banner_id))
        con.commit()
        con.close()
        self.atualizar_botoes()
        await interaction.response.send_message(f"✅ Banner **{nome}** comprado com sucesso! Use `!banner` para equipá-lo no seu perfil.", ephemeral=True)
        await interaction.message.edit(view=self)


class ViewMenuLoja(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id

    @discord.ui.button(label="🖼️ Banners", style=discord.ButtonStyle.primary)
    async def abrir_banners(self, interaction: discord.Interaction, button: discord.ui.Button):
        banners = buscar_todos_banners()
        if not banners:
            await interaction.response.send_message("Nenhum banner disponível na loja ainda!", ephemeral=True)
            return
        view = ViewLoja(self.usuario_id, banners)
        embed = view.gerar_embed()
        banner_id, nome, descricao, preco, arquivo = banners[0]
        if os.path.exists(arquivo):
            arquivo_discord = discord.File(arquivo, filename="preview.png")
            await interaction.response.edit_message(embed=embed, view=view, attachments=[arquivo_discord])
        else:
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])

# ============================================================
# EVENTOS
# ============================================================
@bot.event
async def on_ready():
    iniciar_banco()
    verificar_admins_expirados.start()
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
        try:
            buffer, total = await gerar_card_perfil(membro)
            arquivo = discord.File(buffer, filename="perfil.png")
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_image(url="attachment://perfil.png")
            view = ViewPerfil(membro)
            await ctx.send(file=arquivo, embed=embed, view=view)
        except Exception as e:
            await ctx.send(f"❌ Erro ao gerar perfil: `{e}`")
            
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
    embed.add_field(name="!diario", value="Coleta seus Joyens diários", inline=False)
    embed.add_field(name="!saldo [@usuario]", value="Mostra o saldo de Joyens", inline=False)
    embed.add_field(name="!loja", value="Abre a loja do bot", inline=False)
    embed.add_field(name="!banner", value="Gerencia seus banners", inline=False)
    embed.add_field(name="/banner adicionar", value="Adiciona um banner à loja (admin)", inline=False)
    embed.add_field(name="!addjoyens @usuario quantidade", value="Adiciona Joyens a um usuário (admin)", inline=False)
    embed.add_field(name="/adminbot gerenciar", value="Adiciona ou remove um admin (dono)", inline=False)
    embed.add_field(name="/adminbot lista", value="Lista os admins ativos (dono)", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="diario")
async def diario(ctx):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    hoje = datetime.date.today().isoformat()
    cur.execute("SELECT ultimo_diario, joyens FROM economia WHERE usuario_id = ?", (str(ctx.author.id),))
    resultado = cur.fetchone()
    if resultado and resultado[0] == hoje:
        con.close()
        await ctx.send(f"{ctx.author.mention} Você já coletou seus Joyens hoje! Volte amanhã.")
        return
    quantidade = random.randint(50, 150)
    cur.execute("""
        INSERT INTO economia (usuario_id, joyens, ultimo_diario) VALUES (?, ?, ?)
        ON CONFLICT(usuario_id) DO UPDATE SET joyens = joyens + ?, ultimo_diario = ?
    """, (str(ctx.author.id), quantidade, hoje, quantidade, hoje))
    con.commit()
    novo_saldo = cur.execute("SELECT joyens FROM economia WHERE usuario_id = ?", (str(ctx.author.id),)).fetchone()[0]
    con.close()
    embed = discord.Embed(title="💰 Recompensa Diária!", color=discord.Color.gold())
    embed.add_field(name="Joyens recebidos", value=f"+{quantidade} Joyens", inline=True)
    embed.add_field(name="Saldo atual", value=f"{novo_saldo} Joyens", inline=True)
    embed.set_footer(text="Volte amanhã para mais Joyens!")
    await ctx.send(embed=embed)

@bot.command(name="saldo")
async def saldo(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author
    joyens = buscar_joyens(membro.id)
    embed = discord.Embed(title=f"💰 Saldo de {membro.display_name}", color=discord.Color.gold())
    embed.add_field(name="Joyens", value=f"{joyens} Joyens", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="loja")
async def loja(ctx):
    embed = discord.Embed(
        title="🏪 Loja do JogadorBot",
        description="Bem-vindo à loja! Use seus Joyens para comprar itens exclusivos.\nEscolha uma categoria abaixo:",
        color=discord.Color.purple()
    )
    embed.add_field(name="🖼️ Banners", value="Personalize o seu perfil com banners exclusivos!", inline=False)
    embed.set_footer(text=f"Seu saldo: {buscar_joyens(ctx.author.id)} Joyens")
    view = ViewMenuLoja(ctx.author.id)
    await ctx.send(embed=embed, view=view)

@bot.command(name="banner")
async def banner_cmd(ctx):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT b.id, b.nome FROM banners_usuarios bu
        JOIN banners b ON bu.banner_id = b.id
        WHERE bu.usuario_id = ?
    """, (str(ctx.author.id),))
    banners = cur.fetchall()
    con.close()
    if not banners:
        await ctx.send("Você não tem nenhum banner! Use `!loja` para comprar.")
        return
    embed = discord.Embed(title="🖼️ Seus Banners", description="Escolha um banner para equipar:", color=discord.Color.purple())
    view = discord.ui.View(timeout=60)
    for banner_id, nome in banners:
        async def equipar_callback(interaction, bid=banner_id, bnome=nome):
            con2 = sqlite3.connect("/data/jogadorbot.db")
            cur2 = con2.cursor()
            cur2.execute("INSERT OR REPLACE INTO banner_ativo (usuario_id, banner_id) VALUES (?, ?)", (str(interaction.user.id), bid))
            con2.commit()
            con2.close()
            await interaction.response.send_message(f"✅ Banner **{bnome}** equipado! Aparecerá no seu `!perfil`.", ephemeral=True)
        botao = discord.ui.Button(label=nome, style=discord.ButtonStyle.primary)
        botao.callback = equipar_callback
        view.add_item(botao)
    await ctx.send(embed=embed, view=view)

@bot.command(name="addjoyens")
async def addjoyens(ctx, membro: discord.Member, quantidade: int):
    if not eh_admin(ctx.author.id):
        await ctx.send("❌ Você não tem permissão para usar este comando.")
        return
    adicionar_joyens(membro.id, quantidade)
    novo_saldo = buscar_joyens(membro.id)
    await ctx.send(f"✅ **{quantidade} Joyens** adicionados para {membro.mention}! Novo saldo: **{novo_saldo} Joyens**.")

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
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
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
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
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

# ============================================================
# COMANDOS SLASH — Loja de banners
# ============================================================

banner_group = app_commands.Group(name="banner", description="Gerenciamento de banners")

@banner_group.command(name="adicionar", description="Adiciona um novo banner à loja (admin)")
@app_commands.describe(
    nome="Nome do banner",
    descricao="Descrição do banner",
    preco="Preço em Joyens",
    imagem="Imagem do banner"
)
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def banner_adicionar(interaction: discord.Interaction, nome: str, descricao: str, preco: int, imagem: discord.Attachment):
    os.makedirs("/data/banners", exist_ok=True)
    arquivo_path = f"/data/banners/{nome.replace(' ', '_')}.png"
    async with aiohttp.ClientSession() as session:
        async with session.get(imagem.url) as resp:
            imagem_bytes = await resp.read()
    with open(arquivo_path, "wb") as f:
        f.write(imagem_bytes)
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO banners (nome, descricao, preco, arquivo) VALUES (?, ?, ?, ?)", (nome, descricao, preco, arquivo_path))
        con.commit()
        await interaction.response.send_message(f"✅ Banner **{nome}** adicionado à loja por {preco} Joyens!", ephemeral=True)
    except sqlite3.IntegrityError:
        await interaction.response.send_message(f"❌ Já existe um banner com o nome **{nome}**.", ephemeral=True)
    finally:
        con.close()

# ============================================================
# COMANDOS SLASH — Medida de proteção
# ============================================================

admin_group = app_commands.Group(name="adminbot", description="Gerenciamento de admins")

@admin_group.command(name="gerenciar", description="Adiciona ou remove um admin")
@app_commands.describe(
    usuario="Usuário a ser gerenciado",
    acao="adicionar ou remover",
    tempo="Tempo do admin (ex: 1d5h30m) ou 'infinito'"
)
async def adminbot_gerenciar(interaction: discord.Interaction, usuario: discord.Member, acao: str, tempo: str = "infinito"):
    if interaction.user.id != DONO_ID:
        await interaction.response.send_message("❌ Apenas o dono do bot pode usar este comando.", ephemeral=True)
        return

    if acao.lower() == "adicionar":
        try:
            segundos = parsear_tempo(tempo)
        except ValueError:
            await interaction.response.send_message("❌ Formato de tempo inválido! Use algo como `1d5h30m` ou `infinito`.", ephemeral=True)
            return

        expira = None if segundos is None else (datetime.datetime.now() + datetime.timedelta(seconds=segundos)).isoformat()

        con = sqlite3.connect("/data/jogadorbot.db")
        cur = con.cursor()
        cur.execute("INSERT OR REPLACE INTO admins (usuario_id, expira) VALUES (?, ?)", (str(usuario.id), expira))
        con.commit()
        con.close()

        tempo_texto = "permanentemente" if expira is None else f"até {datetime.datetime.fromisoformat(expira).strftime('%d/%m/%Y às %H:%M')}"
        await interaction.response.send_message(f"✅ **{usuario.display_name}** agora é admin {tempo_texto}!", ephemeral=True)

        try:
            await usuario.send(f"✅ Você recebeu acesso de admin no **JogadorBot** {tempo_texto}!")
        except:
            pass

    elif acao.lower() == "remover":
        con = sqlite3.connect("/data/jogadorbot.db")
        cur = con.cursor()
        cur.execute("DELETE FROM admins WHERE usuario_id = ?", (str(usuario.id),))
        con.commit()
        con.close()
        await interaction.response.send_message(f"✅ Admin de **{usuario.display_name}** removido.", ephemeral=True)
        try:
            await usuario.send("❌ Seu acesso de admin no **JogadorBot** foi removido.")
        except:
            pass
    else:
        await interaction.response.send_message("❌ Ação inválida! Use `adicionar` ou `remover`.", ephemeral=True)

@admin_group.command(name="lista", description="Lista todos os admins ativos")
async def adminbot_lista(interaction: discord.Interaction):
    if interaction.user.id != DONO_ID:
        await interaction.response.send_message("❌ Apenas o dono do bot pode ver esta lista.", ephemeral=True)
        return
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT usuario_id, expira FROM admins")
    admins = cur.fetchall()
    con.close()
    if not admins:
        await interaction.response.send_message("Nenhum admin cadastrado.", ephemeral=True)
        return
    embed = discord.Embed(title="👑 Lista de Admins", color=discord.Color.gold())
    for usuario_id, expira in admins:
        try:
            usuario = await bot.fetch_user(int(usuario_id))
            nome = usuario.display_name
        except:
            nome = f"ID {usuario_id}"
        expira_texto = "Permanente" if expira is None else datetime.datetime.fromisoformat(expira).strftime("%d/%m/%Y às %H:%M")
        embed.add_field(name=nome, value=f"Expira: {expira_texto}", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

bot.tree.add_command(admin_group)

bot.tree.add_command(banner_group)

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
