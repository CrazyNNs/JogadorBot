import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from zoneinfo import ZoneInfo
from discord import ui
import random
import datetime
import sqlite3
import os
import aiohttp
import io
import asyncio

# ============================================================
# CONFIGURAÇÃO
# ============================================================
TOKEN = os.environ.get("TOKEN")
PREFIX = "!"
DONO_ID = 880243114403573780  # Seu ID — sempre tem acesso total
FUSO_BR = ZoneInfo("America/Recife")

# Canais de notificação
CANAL_CONQUISTAS_ID = 1517028501356806144
CANAL_NOTIFICACOES_ID = 1520676033425313885

# Rotação da loja
DURACAO_ROTACAO_HORAS = 5
BANNERS_POR_ROTACAO = 4

# Raridades disponíveis e suas chances na rotação
RARIDADES = {
    "Comum":    0.50,
    "Incomum":  0.25,
    "Raro":     0.15,
    "Epico":    0.07,
    "Lendario": 0.03,
}

# Variavéis de level
LEVEL_MAX = 100

# ============================================================
# TIPOS EDITÁVEIS — Para adicionar novo tipo, copie um bloco
# e ajuste o nome e os campos. "tabela" é o nome da tabela
# no banco de dados e "campos" são os campos editáveis.
# ============================================================
TIPOS_EDITAVEIS = {
    "banner": {
        "tabela": "banners",
        "campos": ["novo_nome", "descricao", "preco", "raridade", "categoria", "imagem"]
    },
    "conquista": {
        "tabela": "conquistas",
        "campos": ["novo_nome", "descricao", "emoji"]
    },
}

# ============================================================
# CATEGORIAS VENDÁVEIS — Para adicionar nova categoria,
# copie um bloco e ajuste o nome, tabela, coluna de nome,
# coluna de preço e a tabela de posse do usuário.
# ============================================================
CATEGORIAS_VENDAVEIS = {
    "banner": {
        "tabela": "banners",
        "coluna_nome": "nome",
        "coluna_preco": "preco",
        "tabela_usuarios": "banners_usuarios",
        "coluna_id_usuario": "banner_id",
        "tabela_ativo": "banner_ativo",
        "coluna_ativo_id": "banner_id",
    },
    # Adicione novos tipos aqui no futuro
}

# ============================================================
# EMPREGOS — Para adicionar novo emprego, copie um bloco
# e ajuste nome, salario_min, salario_max, level_necessario
# e as mensagens de ação.
# ============================================================
EMPREGOS = {
    "Gari": {
        "salario_min": 1250,
        "salario_max": 1450,
        "level_necessario": 0,
        "emoji": "🧹",
        "descricao": "Mantém as ruas limpas da cidade.",
        "acoes": [
            "Você varreu as ruas do centro e ganhou {salario} Joyens!",
            "Você recolheu o lixo do bairro e ganhou {salario} Joyens!",
            "Você limpou a praça principal e ganhou {salario} Joyens!",
        ]
    },
    "Fotografo": {
        "salario_min": 1600,
        "salario_max": 1800,
        "level_necessario": 5,
        "emoji": "📷",
        "descricao": "Registra momentos especiais com sua câmera.",
        "acoes": [
            "Você fotografou um casamento e ganhou {salario} Joyens!",
            "Você fez um ensaio fotográfico e ganhou {salario} Joyens!",
            "Você fotografou um evento corporativo e ganhou {salario} Joyens!",
        ]
    },
    "Barman": {
        "salario_min": 2000,
        "salario_max": 2200,
        "level_necessario": 10,
        "emoji": "🍹",
        "descricao": "Prepara drinks e anima o bar todas as noites.",
        "acoes": [
            "Você preparou drinks a noite toda e ganhou {salario} Joyens!",
            "Você atendeu uma festa VIP no bar e ganhou {salario} Joyens!",
            "Você criou um novo drink especial e ganhou {salario} Joyens!",
        ]
    },
}

# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ============================================================
# BANCO DE DADOS
# ============================================================
def iniciar_banco():
    con = sqlite3.connect("jogadorbot.db")
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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categorias_banner (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            emoji TEXT NOT NULL
        )
    """)
    try:
        cur.execute("ALTER TABLE banners ADD COLUMN categoria_id INTEGER REFERENCES categorias_banner(id)")
    except:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rotacao_atual (
            banner_id INTEGER PRIMARY KEY,
            expira TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rotacao_historico (
            banner_id INTEGER NOT NULL
        )
    """)
    try:
        cur.execute("ALTER TABLE banners ADD COLUMN raridade TEXT DEFAULT 'Comum'")
    except:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS level_usuarios (
            usuario_id TEXT PRIMARY KEY,
            level INTEGER DEFAULT 0,
            xp INTEGER DEFAULT 0
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS banners_favoritos (
            usuario_id TEXT NOT NULL,
            banner_id INTEGER NOT NULL,
            PRIMARY KEY (usuario_id, banner_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS empregos_usuarios (
            usuario_id TEXT PRIMARY KEY,
            emprego TEXT NOT NULL,
            vezes_trabalhadas INTEGER DEFAULT 0,
            ultimo_trabalho TEXT
        )
    """)
    
    con.commit()
    con.close()

# ============================================================
# FUNÇÕES AUXILIARES - Conquistas
# ============================================================
def buscar_conquistas_usuario(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
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
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, descricao, emoji FROM conquistas ORDER BY nome")
    resultado = cur.fetchall()
    con.close()
    return resultado

# ============================================================
# FUNÇÕES AUXILIARES - Economia e loja de banners
# ============================================================

def buscar_joyens(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT joyens FROM economia WHERE usuario_id = ?", (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return resultado[0] if resultado else 0

def adicionar_joyens(usuario_id, quantidade):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO economia (usuario_id, joyens) VALUES (?, ?)
        ON CONFLICT(usuario_id) DO UPDATE SET joyens = joyens + ?
    """, (str(usuario_id), quantidade, quantidade))
    con.commit()
    con.close()

def remover_joyens(usuario_id, quantidade):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("UPDATE economia SET joyens = joyens - ? WHERE usuario_id = ?", (quantidade, str(usuario_id)))
    con.commit()
    con.close()

def usuario_tem_banner(usuario_id, banner_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT 1 FROM banners_usuarios WHERE usuario_id = ? AND banner_id = ?", (str(usuario_id), banner_id))
    resultado = cur.fetchone()
    con.close()
    return resultado is not None

def buscar_banner_ativo(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT b.arquivo FROM banner_ativo ba
        JOIN banners b ON ba.banner_id = b.id
        WHERE ba.usuario_id = ?
    """, (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    if resultado and os.path.exists(resultado[0]):
        return resultado[0]
    return "bannerbot.png"

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
    con = sqlite3.connect("jogadorbot.db")
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

def xp_necessario(level):
    """Calcula o XP necessário para atingir o próximo level."""
    if level >= LEVEL_MAX:
        return None
    xp = 1000
    for _ in range(level):
        xp = int(xp * 1.1)
    return xp

def buscar_level(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT level, xp FROM level_usuarios WHERE usuario_id = ?", (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return resultado if resultado else (0, 0)

async def adicionar_xp(usuario_id, quantidade, ctx_ou_channel):
    """Adiciona XP ao usuário e verifica se subiu de level."""
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    cur.execute("""
        INSERT INTO level_usuarios (usuario_id, level, xp) VALUES (?, 0, 0)
        ON CONFLICT(usuario_id) DO NOTHING
    """, (str(usuario_id),))

    cur.execute("SELECT level, xp FROM level_usuarios WHERE usuario_id = ?", (str(usuario_id),))
    level_atual, xp_atual = cur.fetchone()

    if level_atual >= LEVEL_MAX:
        con.close()
        return

    novo_xp = xp_atual + quantidade
    subiu_level = False
    levels_ganhos = 0

    while True:
        if level_atual >= LEVEL_MAX:
            break
        xp_prox = xp_necessario(level_atual)
        if novo_xp >= xp_prox:
            novo_xp -= xp_prox
            level_atual += 1
            subiu_level = True
            levels_ganhos += 1
        else:
            break

    cur.execute("UPDATE level_usuarios SET level = ?, xp = ? WHERE usuario_id = ?",
                (level_atual, novo_xp, str(usuario_id)))
    con.commit()
    con.close()

    if subiu_level:
        canal = ctx_ou_channel if isinstance(ctx_ou_channel, discord.TextChannel) else ctx_ou_channel.channel
        usuario = await bot.fetch_user(int(usuario_id))
        embed = discord.Embed(
            title="🎉 Level Up!",
            description=f"{usuario.mention} subiu para o **Level {level_atual}**!",
            color=discord.Color.gold()
        )
        if level_atual < LEVEL_MAX:
            embed.add_field(name="Próximo level", value=f"{xp_necessario(level_atual)} XP necessários", inline=False)
        else:
            embed.add_field(name="🏆 Level máximo atingido!", value="Parabéns, você chegou ao topo!", inline=False)
        mensagem = await canal.send(embed=embed)
        await mensagem.delete(delay=60)

# Dados foto de perfil
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((180, 180))
    mascara = Image.new("L", (180, 180), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, 180, 180), fill=255)
    avatar_circular = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    avatar_circular.paste(avatar, mask=mascara)
    
# Banner de perfil
    card = Image.open("perfil.png").convert("RGBA").resize((800, 600))

    draw = ImageDraw.Draw(card)
    card.paste(avatar_circular, (16, 16), avatar_circular)
    
    banner_arquivo = buscar_banner_ativo(usuario.id)
    if banner_arquivo and os.path.exists(banner_arquivo):
        banner = Image.open(banner_arquivo).convert("RGBA").resize((800, 375))
        card.paste(banner, (0, 225), banner)

# Textos de perfil
    fonte_nome = ImageFont.truetype("/app/fonte.ttf", 35)
    fonte_info = ImageFont.truetype("/app/fonte_regular.ttf", 25)
# Level do usuário
    level, xp = buscar_level(usuario.id)
    xp_prox = xp_necessario(level)
    xp_texto = f"XP: {xp}/{xp_prox}" if xp_prox else "Level MAX"
    draw.text((400, 140), f"Level {level}", font=fonte_nome, fill=(255, 215, 0))
    draw.text((400, 175), xp_texto, font=fonte_info, fill=(200, 200, 200))
# Nickname e @ do usuário
    draw.text((210, 30), usuario.display_name, font=fonte_nome, fill=(255, 255, 255))
    draw.text((210, 80), f"@{usuario.name}", font=fonte_info, fill=(100, 100, 100))
# Quantidade de conquistas
    conquistas = buscar_conquistas_usuario(usuario.id)
    draw.text((540, 97), f"{len(conquistas)}", font=fonte_info, fill=(255, 255, 255))
# Quantidade de Joyens do usuário
    joyens = buscar_joyens(usuario.id)
    draw.text((540, 27), f"{joyens}", font=fonte_info, fill=(255, 255, 255))

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer, len(conquistas)

from discord.ext import tasks

@tasks.loop(minutes=5)
async def verificar_admins_expirados():
    con = sqlite3.connect("jogadorbot.db")
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

@tasks.loop(minutes=1)
async def verificar_rotacao():
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT expira FROM rotacao_atual LIMIT 1")
    resultado = cur.fetchone()
    con.close()

    precisa_rotacionar = False
    if not resultado:
        precisa_rotacionar = True
    else:
        fuso_brasilia = datetime.timezone(datetime.timedelta(hours=-3))
        expira = datetime.datetime.fromisoformat(resultado[0])
        if expira.tzinfo is None:
            expira = expira.replace(tzinfo=fuso_brasilia)
        if datetime.datetime.now(fuso_brasilia) >= expira:
            precisa_rotacionar = True

    if precisa_rotacionar:
        ids_sorteados, expira = sortear_nova_rotacao()
        canal = bot.get_channel(CANAL_NOTIFICACOES_ID)
        if canal is None:
            return
        if ids_sorteados is None:
            await canal.send(f"⚠️ {expira}")
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            SELECT b.nome, b.raridade FROM rotacao_atual ra
            JOIN banners b ON ra.banner_id = b.id
        """)
        banners = cur.fetchall()
        con.close()

        expira_dt = datetime.datetime.fromisoformat(expira)
        embed = discord.Embed(
            title="🔄 Nova Rotação da Loja!",
            description="> Os banners da loja mudaram! Corra para conferir antes que acabe.",
            color=discord.Color.yellow()
        )
        for nome, raridade in banners:
            embed.add_field(name=nome, value=f"Raridade: **{raridade}**", inline=True)
        embed.set_footer(text=f"Próxima rotação: {expira_dt.strftime('%d/%m/%Y às %H:%M')}")
        await canal.send(embed=embed)
        verificar_favoritos_rotacao.start()

@tasks.loop(seconds=1)
async def verificar_favoritos_rotacao():
    await asyncio.sleep(5)
    verificar_favoritos_rotacao.stop()

    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT bf.usuario_id, b.id, b.nome
        FROM banners_favoritos bf
        JOIN banners b ON bf.banner_id = b.id
        JOIN rotacao_atual ra ON b.id = ra.banner_id
    """)
    resultados = cur.fetchall()
    con.close()

    for usuario_id, banner_id, banner_nome in resultados:
        try:
            usuario = await bot.fetch_user(int(usuario_id))
            membro_nome = usuario.display_name if hasattr(usuario, 'display_name') else usuario.name
            await usuario.send(
                f"🔔 **{membro_nome}**, o banner **{banner_nome}** está disponível na loja! Corra para comprar antes que a rotação mude."
            )
        except:
            pass
# ============================================================
# FUNÇÕES AUXILIARES - Categorias banner
# ============================================================

def buscar_todas_categorias():
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, emoji FROM categorias_banner ORDER BY nome")
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_banners_por_categoria(categoria_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, descricao, preco, arquivo FROM banners WHERE categoria_id = ? ORDER BY id", (categoria_id,))
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_banners_rotacao():
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    expira_row = cur.execute("SELECT expira FROM rotacao_atual LIMIT 1").fetchone()
    cur.execute("""
        SELECT b.id, b.nome, b.descricao, b.preco, b.arquivo, b.raridade
        FROM rotacao_atual ra
        JOIN banners b ON ra.banner_id = b.id
    """)
    banners = cur.fetchall()
    con.close()
    expira = expira_row[0] if expira_row else None
    return banners, expira

def buscar_banners_categoria_catalogo(categoria_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT b.id, b.nome, b.descricao, b.preco, b.arquivo, b.raridade
        FROM banners b
        WHERE b.categoria_id = ?
        ORDER BY b.id
    """, (categoria_id,))
    resultado = cur.fetchall()
    con.close()
    return resultado

def banner_em_rotacao(banner_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT 1 FROM rotacao_atual WHERE banner_id = ?", (banner_id,))
    resultado = cur.fetchone()
    con.close()
    return resultado is not None

def usuario_favoritou_banner(usuario_id, banner_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT 1 FROM banners_favoritos WHERE usuario_id = ? AND banner_id = ?",
                (str(usuario_id), banner_id))
    resultado = cur.fetchone()
    con.close()
    return resultado is not None

async def gerar_imagem_catalogo(banners_pagina):
    """Gera a imagem do catálogo com até 3 banners empilhados."""
    card = Image.open("catalogo.png").convert("RGBA")
    largura, altura = card.size
    
    altura_por_banner = altura // 3
    
    for i, (banner_id, nome, descricao, preco, arquivo, raridade) in enumerate(banners_pagina):
        if os.path.exists(arquivo):
            try:
                banner_img = Image.open(arquivo).convert("RGBA")
                banner_img = banner_img.resize((largura, altura_por_banner), Image.LANCZOS)
                card.paste(banner_img, (0, i * altura_por_banner), banner_img)
            except:
                pass
    
    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# ============================================================
# FUNÇÕES AUXILIARES - Rotação de banner na loja
# ============================================================

def sortear_nova_rotacao():
    import random as rnd
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    # Busca histórico para evitar repetição
    cur.execute("SELECT banner_id FROM rotacao_historico")
    historico = [row[0] for row in cur.fetchall()]

    # Busca todos os banners do catálogo
    cur.execute("SELECT id, raridade FROM banners")
    todos = cur.fetchall()

    # Filtra os do histórico recente
    disponiveis = [b for b in todos if b[0] not in historico]

    # Se não tiver suficientes fora do histórico, limpa o histórico
    if len(disponiveis) < BANNERS_POR_ROTACAO:
        cur.execute("DELETE FROM rotacao_historico")
        disponiveis = todos

    if len(disponiveis) < BANNERS_POR_ROTACAO:
        con.close()
        return None, f"❌ Não há banners suficientes no catálogo! São necessários pelo menos {BANNERS_POR_ROTACAO} banners."

    # Sorteia baseado na raridade
    pesos = []
    for banner_id, raridade in disponiveis:
        peso = RARIDADES.get(raridade, 0.50)
        pesos.append(peso)

    total_peso = sum(pesos)
    pesos_normalizados = [p / total_peso for p in pesos]

    ids_sorteados = []
    pool = list(zip([b[0] for b in disponiveis], pesos_normalizados))

    for _ in range(BANNERS_POR_ROTACAO):
        if not pool:
            break
        ids = [p[0] for p in pool]
        pesos_pool = [p[1] for p in pool]
        total = sum(pesos_pool)
        pesos_pool = [p / total for p in pesos_pool]
        escolhido = rnd.choices(ids, weights=pesos_pool, k=1)[0]
        ids_sorteados.append(escolhido)
        pool = [p for p in pool if p[0] != escolhido]

    # Atualiza a rotação
    fuso_brasilia = datetime.timezone(datetime.timedelta(hours=-3))
    expira = (datetime.datetime.now(fuso_brasilia) + datetime.timedelta(minutes=DURACAO_ROTACAO_HORAS)).isoformat()
    cur.execute("DELETE FROM rotacao_atual")
    for bid in ids_sorteados:
        cur.execute("INSERT INTO rotacao_atual (banner_id, expira) VALUES (?, ?)", (bid, expira))
        cur.execute("INSERT INTO rotacao_historico (banner_id) VALUES (?)", (bid,))

    con.commit()
    con.close()
    return ids_sorteados, expira

# ============================================================
# FUNÇÕES AUXILIARES - Empregos e Trabalhar
# ============================================================

def buscar_emprego(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT emprego, vezes_trabalhadas, ultimo_trabalho FROM empregos_usuarios WHERE usuario_id = ?",
                (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return resultado

def tempo_restante_trabalho(ultimo_trabalho):
    """Retorna o tempo restante em minutos ou 0 se já pode trabalhar."""
    if not ultimo_trabalho:
        return 0
    ultimo = datetime.datetime.fromisoformat(ultimo_trabalho)
    agora = datetime.datetime.now()
    diferenca = (ultimo + datetime.timedelta(minutes=40)) - agora
    if diferenca.total_seconds() <= 0:
        return 0
    minutos = int(diferenca.total_seconds() // 60)
    segundos = int(diferenca.total_seconds() % 60)
    return f"{minutos}m {segundos}s"

# ============================================================
# VIEWS (BOTÕES) - Perfil
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

    @discord.ui.button(label="🖼️ Banners", style=discord.ButtonStyle.secondary)
    async def ver_banners(self, interaction: discord.Interaction, button: discord.ui.Button):
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            SELECT b.id FROM banners_usuarios bu
            JOIN banners b ON bu.banner_id = b.id
            WHERE bu.usuario_id = ?
        """, (str(self.usuario.id),))
        resultado = cur.fetchall()
        con.close()
        if not resultado:
            await interaction.response.send_message("Este usuário não tem nenhum banner! Use `!loja` para comprar.", ephemeral=True)
            return
        view = ViewInventarioBanners(self.usuario)
        embed = view.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

# ============================================================
# VIEW (BOTÕES) - Conquistas de usuário
# ============================================================
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

    @discord.ui.button(label="🔙 Perfil", style=discord.ButtonStyle.danger)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        membro = self.usuario
        level, xp = buscar_level(membro.id)
        xp_prox = xp_necessario(level)
        joyens = buscar_joyens(membro.id)
        conquistas = buscar_conquistas_usuario(membro.id)
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM banners_usuarios WHERE usuario_id = ?", (str(membro.id),))
        total_banners = cur.fetchone()[0]
        con.close()
        banner_arquivo = buscar_banner_ativo(membro.id)

        embed1 = discord.Embed(title=f"Perfil — Lvl.``{level}``", color=discord.Color.blurple())
        embed1.set_thumbnail(url=membro.display_avatar.url)
        embed1.description = (
            f"**{membro.display_name}**\n"
            f"> {membro.name}\n"
            f"**ID:** ``{membro.id}``"
        )
        if xp_prox:
            porcentagem = int((xp / xp_prox) * 100)
            blocos_cheios = porcentagem // 10
            barra = "█" * blocos_cheios + "░" * (10 - blocos_cheios)
            embed1.add_field(name="XP", value=f"`{barra}` {porcentagem}%\n{xp}/{xp_prox} XP", inline=False)
        else:
            embed1.add_field(name="XP", value="🏆 Level máximo atingido!", inline=False)

        embed2 = discord.Embed(color=discord.Color.blurple())
        embed2.add_field(name="💰 Economia", value=f"> **Joyens:** ``{joyens}``", inline=False)
        embed2.add_field(
            name="📊 Outros",
            value=f"> **Conquistas:** ``{len(conquistas)}``\n> **Banners:** ``{total_banners}``",
            inline=False
        )

        emprego_dados = buscar_emprego(membro.id)
        if emprego_dados:
            emprego_nome, vezes_trabalhadas, _ = emprego_dados
            emprego_info = EMPREGOS.get(emprego_nome)
            emoji_emp = emprego_info["emoji"] if emprego_info else "💼"
            embed2.add_field(
                name="💼 Emprego",
                value=f"{emoji_emp} **{emprego_nome}** | {vezes_trabalhadas} vez(es) trabalhadas",
                inline=False
            )
        else:
            embed2.add_field(name="💼 Emprego", value="Desempregado — use `!empregos`", inline=False)

        if banner_arquivo and os.path.exists(banner_arquivo):
            nome_arquivo = os.path.basename(banner_arquivo)
            arquivo_discord = discord.File(banner_arquivo, filename=nome_arquivo)
            embed2.set_image(url=f"attachment://{nome_arquivo}")
            await interaction.response.edit_message(embeds=[embed1, embed2], view=ViewPerfil(membro), attachments=[arquivo_discord])
        else:
            await interaction.response.edit_message(embeds=[embed1, embed2], view=ViewPerfil(membro), attachments=[])

# ============================================================
# VIEW (BOTÕES) - Loja de banners
# ============================================================

class ViewLoja(discord.ui.View):
    def __init__(self, usuario_id, banners, rotacao=False, expira=None):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.banners = banners
        self.rotacao = rotacao
        self.expira = expira
        self.index = 0
        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.anterior.disabled = self.index == 0
        self.proximo.disabled = self.index >= len(self.banners) - 1
        banner_id = self.banners[self.index][0]
        self.comprar.disabled = usuario_tem_banner(self.usuario_id, banner_id)
        self.comprar.label = "✅ Já possui" if usuario_tem_banner(self.usuario_id, banner_id) else "🛒 Comprar"

    def gerar_embed(self):
        banner_id, nome, descricao, preco, arquivo, raridade = self.banners[self.index]
        joyens = buscar_joyens(self.usuario_id)
        tem = usuario_tem_banner(self.usuario_id, banner_id)
        embed = discord.Embed(
            title=f"🖼️ {nome}",
            description=descricao,
            color=discord.Color.gold()
        )
        embed.add_field(name="Raridade", value=f"**{raridade}**", inline=True)
        embed.add_field(name="Preço", value=f"{preco} Joyens", inline=True)
        embed.add_field(name="Seu saldo", value=f"{joyens} Joyens", inline=True)
        if tem:
            embed.add_field(name="Status", value="✅ Você já possui este banner", inline=False)
        elif joyens < preco:
            embed.add_field(name="Status", value="❌ Joyens insuficientes", inline=False)
        if self.expira:
            expira_dt = datetime.datetime.fromisoformat(self.expira)
            embed.set_footer(text=f"Banner {self.index + 1} de {len(self.banners)} • Rotação expira: {expira_dt.strftime('%d/%m/%Y às %H:%M')}")
        else:
            embed.set_footer(text=f"Banner {self.index + 1} de {len(self.banners)}")
        if os.path.exists(arquivo):
            embed.set_image(url="attachment://preview.png")
        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        self.atualizar_botoes()
        embed = self.gerar_embed()
        _, _, _, _, arquivo, _ = self.banners[self.index]
        if os.path.exists(arquivo):
            arquivo_discord = discord.File(arquivo, filename="preview.png")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[arquivo_discord])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        self.atualizar_botoes()
        embed = self.gerar_embed()
        _, _, _, _, arquivo, _ = self.banners[self.index]
        if os.path.exists(arquivo):
            arquivo_discord = discord.File(arquivo, filename="preview.png")
            await interaction.response.edit_message(embed=embed, view=self, attachments=[arquivo_discord])
        else:
            await interaction.response.edit_message(embed=embed, view=self, attachments=[])

    @discord.ui.button(label="🛒 Comprar", style=discord.ButtonStyle.success, row=0)
    async def comprar(self, interaction: discord.Interaction, button: discord.ui.Button):
        comprador_id = interaction.user.id
        banner_id, nome, descricao, preco, arquivo, raridade = self.banners[self.index]
        joyens = buscar_joyens(comprador_id)
        if joyens < preco:
            await interaction.response.send_message(
                f"❌ Você não tem Joyens suficientes! Você tem {joyens} e precisa de {preco}.",
                ephemeral=True
            )
            return
        if usuario_tem_banner(comprador_id, banner_id):
            await interaction.response.send_message(
                "❌ Você já possui este banner!",
                ephemeral=True
            )
            return
        remover_joyens(comprador_id, preco)
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO banners_usuarios (usuario_id, banner_id) VALUES (?, ?)",
                    (str(comprador_id), banner_id))
        cur.execute("DELETE FROM banners_favoritos WHERE usuario_id = ? AND banner_id = ?",
                    (str(comprador_id), banner_id))
        con.commit()
        con.close()
        
        await interaction.response.send_message(
            f"✅ Banner **{nome}** comprado! Use o botão **🖼️ Banners** no seu perfil para equipá-lo.",
            ephemeral=True
        )
        await interaction.message.edit(view=self)

    @discord.ui.button(label="🔙 Loja", style=discord.ButtonStyle.danger, row=0)
    async def voltar_loja(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏪 Loja do JogadorBot",
            description="Bem-vindo à loja! Use seus Joyens para comprar itens incríveis.\nEscolha uma categoria:",
            color=discord.Color.gold()
        )
        embed.add_field(name="🖼️ Banners", value="Banners exclusivos por tempo limitado!", inline=False)
        embed.set_footer(text=f"Seu saldo: {buscar_joyens(self.usuario_id)} Joyens")
        view = ViewMenuLoja(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ViewMenuLoja(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id

    @discord.ui.button(label="🖼️ Banners", style=discord.ButtonStyle.primary)
    async def abrir_banners(self, interaction: discord.Interaction, button: discord.ui.Button):
        banners, expira = buscar_banners_rotacao()
        if not banners:
            await interaction.response.send_message(
                "Nenhum banner disponível na rotação atual!", ephemeral=True
            )
            return
        view = ViewLoja(self.usuario_id, banners, rotacao=True, expira=expira)
        embed = view.gerar_embed()
        _, _, _, _, arquivo, _ = banners[0]
        if os.path.exists(arquivo):
            arquivo_discord = discord.File(arquivo, filename="preview.png")
            await interaction.response.edit_message(embed=embed, view=view, attachments=[arquivo_discord])
        else:
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])

# ============================================================
# VIEW (BOTÕES) - Inventário de banner
# ============================================================

class ViewInventarioBanners(discord.ui.View):
    def __init__(self, usuario: discord.Member, pagina: int = 0):
        super().__init__(timeout=120)
        self.usuario = usuario
        self.pagina = pagina
        self.por_pagina = 9
        self.banners = self.carregar_banners()
        self.total_paginas = max(1, -(-len(self.banners) // self.por_pagina))
        self.construir_botoes()

    def carregar_banners(self):
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            SELECT b.id, b.nome FROM banners_usuarios bu
            JOIN banners b ON bu.banner_id = b.id
            WHERE bu.usuario_id = ?
            ORDER BY b.nome
        """, (str(self.usuario.id),))
        resultado = cur.fetchall()
        con.close()
        return resultado

    def banner_ativo_id(self):
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("SELECT banner_id FROM banner_ativo WHERE usuario_id = ?", (str(self.usuario.id),))
        resultado = cur.fetchone()
        con.close()
        return resultado[0] if resultado else None

    def construir_botoes(self):
        self.clear_items()
        inicio = self.pagina * self.por_pagina
        fim = inicio + self.por_pagina
        pagina_banners = self.banners[inicio:fim]
        ativo_id = self.banner_ativo_id()

        for banner_id, nome in pagina_banners:
            eh_ativo = banner_id == ativo_id
            botao = discord.ui.Button(
                label=nome,
                style=discord.ButtonStyle.success if eh_ativo else discord.ButtonStyle.primary,
                disabled=eh_ativo,
                row=len(self.children) // 3
            )
            async def callback(interaction, bid=banner_id, bnome=nome):
                con2 = sqlite3.connect("jogadorbot.db")
                cur2 = con2.cursor()
                cur2.execute("INSERT OR REPLACE INTO banner_ativo (usuario_id, banner_id) VALUES (?, ?)",
                             (str(interaction.user.id), bid))
                con2.commit()
                con2.close()
                # Reconstrói os botões para atualizar qual está ativo
                self.banners = self.carregar_banners()
                self.construir_botoes()
                await interaction.response.edit_message(embed=self.gerar_embed(), view=self)
            botao.callback = callback
            self.add_item(botao)

        # Linha de navegação
        btn_anterior = discord.ui.Button(label="◀", style=discord.ButtonStyle.secondary,
                                          disabled=self.pagina == 0, row=3)
        btn_proximo = discord.ui.Button(label="▶", style=discord.ButtonStyle.secondary,
                                         disabled=self.pagina >= self.total_paginas - 1, row=3)
        btn_voltar = discord.ui.Button(label="🔙 Perfil", style=discord.ButtonStyle.danger, row=3)

        async def anterior_callback(interaction):
            self.pagina -= 1
            self.banners = self.carregar_banners()
            self.construir_botoes()
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

        async def proximo_callback(interaction):
            self.pagina += 1
            self.banners = self.carregar_banners()
            self.construir_botoes()
            await interaction.response.edit_message(embed=self.gerar_embed(), view=self)

        async def voltar_callback(interaction):
            membro = self.usuario
            level, xp = buscar_level(membro.id)
            xp_prox = xp_necessario(level)
            joyens = buscar_joyens(membro.id)
            conquistas = buscar_conquistas_usuario(membro.id)
            con = sqlite3.connect("jogadorbot.db")
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM banners_usuarios WHERE usuario_id = ?", (str(membro.id),))
            qtd_banners = cur.fetchone()[0]
            con.close()

            embed1 = discord.Embed(title=f"Perfil — Lvl.``{level}``", color=discord.Color.blurple())
            embed1.set_thumbnail(url=membro.display_avatar.url)
            embed1.description = (
                f"**{membro.display_name}**\n"
                f"> {membro.name}\n"
                f"**ID:** ``{membro.id}``"
            )
            if xp_prox:
                porcentagem = int((xp / xp_prox) * 100)
                blocos_cheios = porcentagem // 10
                barra = "█" * blocos_cheios + "░" * (10 - blocos_cheios)
                embed1.add_field(name="XP", value=f"`{barra}` {porcentagem}%\n{xp}/{xp_prox} XP", inline=False)
            else:
                embed1.add_field(name="XP", value="🏆 Level máximo atingido!", inline=False)

            embed2 = discord.Embed(color=discord.Color.blurple())
            embed2.add_field(name="💰 Economia", value=f"> **Joyens:** ``{joyens}``", inline=False)
            embed2.add_field(
                name="📊 Outros",
                value=f"> **Conquistas:** ``{len(conquistas)}``\n> **Banners:** ``{qtd_banners}``",
                inline=False
            )

            emprego_dados = buscar_emprego(membro.id)
            if emprego_dados:
                emprego_nome, vezes_trabalhadas, _ = emprego_dados
                emprego_info = EMPREGOS.get(emprego_nome)
                emoji_emp = emprego_info["emoji"] if emprego_info else "💼"
                embed2.add_field(
                    name="💼 Emprego",
                    value=f"{emoji_emp} **{emprego_nome}** | {vezes_trabalhadas} vez(es) trabalhadas",
                    inline=False
                )
            else:
                embed2.add_field(name="💼 Emprego", value="Desempregado — use `!empregos`", inline=False)

            banner_arquivo = buscar_banner_ativo(membro.id)
            if banner_arquivo and os.path.exists(banner_arquivo):
                nome_arquivo = os.path.basename(banner_arquivo)
                arquivo_discord = discord.File(banner_arquivo, filename=nome_arquivo)
                embed2.set_image(url=f"attachment://{nome_arquivo}")
                await interaction.response.edit_message(embeds=[embed1, embed2], view=ViewPerfil(membro), attachments=[arquivo_discord])
            else:
                await interaction.response.edit_message(embeds=[embed1, embed2], view=ViewPerfil(membro), attachments=[])

        btn_anterior.callback = anterior_callback
        btn_proximo.callback = proximo_callback
        btn_voltar.callback = voltar_callback

        self.add_item(btn_anterior)
        self.add_item(btn_proximo)
        self.add_item(btn_voltar)

    def gerar_embed(self):
        ativo_id = self.banner_ativo_id()
        embed = discord.Embed(
            title=f"🖼️ Banners de {self.usuario.display_name}",
            description="Selecione um banner para equipar no seu perfil.\n> O banner ativo aparece em verde.",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.usuario.display_avatar.url)
        embed.set_footer(text=f"Página {self.pagina + 1} de {self.total_paginas} • {len(self.banners)} banner(s) no total")
        return embed

class SelectCategoriaCatalogo(discord.ui.Select):
    def __init__(self, usuario_id):
        self.usuario_id = usuario_id
        categorias = buscar_todas_categorias()
        options = []
        for cat_id, nome, emoji in categorias:
            options.append(discord.SelectOption(label=nome, value=str(cat_id), emoji=emoji))
        if not options:
            options.append(discord.SelectOption(label="Nenhuma categoria disponível", value="0"))
        super().__init__(placeholder="Escolha uma categoria...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        categoria_id = int(self.values[0])
        if categoria_id == 0:
            await interaction.response.send_message("Nenhuma categoria disponível!", ephemeral=True)
            return
        banners = buscar_banners_categoria_catalogo(categoria_id)
        if not banners:
            await interaction.response.send_message("❌ Nenhum banner disponível nesta categoria ainda!", ephemeral=True)
            return
        view = ViewCatalogoBanners(self.usuario_id, banners, pagina=0)
        embed, arquivo = await view.gerar_embed_e_imagem()
        await interaction.response.edit_message(embed=embed, view=view, attachments=[arquivo])


class ViewMenuCatalogo(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.add_item(SelectMenuCatalogo(usuario_id))


class SelectMenuCatalogo(discord.ui.Select):
    def __init__(self, usuario_id):
        self.usuario_id = usuario_id
        options = [
            discord.SelectOption(label="Banners", value="banners", emoji="🖼️",
                                 description="Ver o catálogo completo de banners"),
        ]
        super().__init__(placeholder="O que você quer ver?", options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "banners":
            categorias = buscar_todas_categorias()
            if not categorias:
                await interaction.response.send_message("❌ Nenhuma categoria de banners criada ainda!", ephemeral=True)
                return
            view = ViewCategoriaCatalogo(self.usuario_id)
            embed = discord.Embed(
                title="📖 Catálogo de Banners",
                description="Escolha uma categoria para ver os banners disponíveis:",
                color=discord.Color.blue()
            )
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ViewCategoriaCatalogo(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.add_item(SelectCategoriaCatalogo(usuario_id))

    @discord.ui.button(label="🔙 Voltar", style=discord.ButtonStyle.danger, row=1)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📖 Catálogo do JogadorBot",
            description="Bem-vindo ao catálogo! Escolha o que deseja ver:",
            color=discord.Color.blue()
        )
        view = ViewMenuCatalogo(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

class ViewCatalogoBanners(discord.ui.View):
    def __init__(self, usuario_id, banners, pagina=0):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.banners = banners
        self.pagina = pagina
        self.por_pagina = 3
        self.total_paginas = max(1, -(-len(banners) // self.por_pagina))
        self.atualizar_botoes()

    def atualizar_botoes(self):
        self.anterior.disabled = self.pagina == 0
        self.proximo.disabled = self.pagina >= self.total_paginas - 1

        pagina_banners = self.pagina_atual()
        botoes_favoritar = [self.favoritar_1, self.favoritar_2, self.favoritar_3]

        for i, botao in enumerate(botoes_favoritar):
            if i >= len(pagina_banners):
                botao.disabled = True
                botao.label = "⭐ Favoritar"
                botao.style = discord.ButtonStyle.secondary
                continue

            banner_id = pagina_banners[i][0]
            possui = usuario_tem_banner(self.usuario_id, banner_id)
            favoritado = usuario_favoritou_banner(self.usuario_id, banner_id)

            if possui:
                botao.disabled = True
                botao.label = "✅ Você já possui"
                botao.style = discord.ButtonStyle.secondary
            elif favoritado:
                botao.disabled = False
                botao.label = "💔 Tirar dos Favoritos"
                botao.style = discord.ButtonStyle.danger
            else:
                botao.disabled = False
                botao.label = f"⭐ Favoritar Banner {i+1}"
                botao.style = discord.ButtonStyle.primary

    def pagina_atual(self):
        inicio = self.pagina * self.por_pagina
        fim = inicio + self.por_pagina
        return self.banners[inicio:fim]

    async def gerar_embed_e_imagem(self):
        pagina_banners = self.pagina_atual()

        embed = discord.Embed(
            title="🖼️ Catálogo de Banners",
            color=discord.Color.blue()
        )

        for i, (banner_id, nome, descricao, preco, arquivo, raridade) in enumerate(pagina_banners):
            em_rotacao = banner_em_rotacao(banner_id)
            favoritado = usuario_favoritou_banner(self.usuario_id, banner_id)
            status = "🟢 Na loja agora!" if em_rotacao else "🔴 Fora de rotação"
            fav_texto = " ⭐ Favoritado" if favoritado else ""
            embed.add_field(
                name=f"**{i+1}.** {nome} — {raridade}{fav_texto}",
                value=f"{descricao}\n💰 **{preco} Joyens** | {status}",
                inline=False
            )

        embed.set_image(url="attachment://catalogo_page.png")
        embed.set_footer(text=f"Página {self.pagina + 1} de {self.total_paginas} • {len(self.banners)} banner(s) no total")

        buffer = await gerar_imagem_catalogo(pagina_banners)
        arquivo_discord = discord.File(buffer, filename="catalogo_page.png")
        return embed, arquivo_discord

    async def atualizar_mensagem(self, interaction):
        embed, arquivo = await self.gerar_embed_e_imagem()
        await interaction.response.edit_message(embed=embed, view=self, attachments=[arquivo])

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina -= 1
        self.atualizar_botoes()
        await self.atualizar_mensagem(interaction)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.pagina += 1
        self.atualizar_botoes()
        await self.atualizar_mensagem(interaction)

    @discord.ui.button(label="🔙 Categorias", style=discord.ButtonStyle.danger, row=0)
    async def voltar_categorias(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewCategoriaCatalogo(self.usuario_id)
        embed = discord.Embed(
            title="📖 Catálogo de Banners",
            description="Escolha uma categoria para ver os banners disponíveis:",
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    @discord.ui.button(label="⭐ Favoritar Banner 1", style=discord.ButtonStyle.primary, row=1)
    async def favoritar_1(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_favorito(interaction, 0)

    @discord.ui.button(label="⭐ Favoritar Banner 2", style=discord.ButtonStyle.primary, row=1)
    async def favoritar_2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_favorito(interaction, 1)

    @discord.ui.button(label="⭐ Favoritar Banner 3", style=discord.ButtonStyle.primary, row=1)
    async def favoritar_3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.toggle_favorito(interaction, 2)

    async def toggle_favorito(self, interaction: discord.Interaction, indice: int):
        pagina_banners = self.pagina_atual()
        if indice >= len(pagina_banners):
            await interaction.response.send_message("❌ Não há banner nessa posição!", ephemeral=True)
            return

        banner_id, nome, _, _, _, _ = pagina_banners[indice]

        if usuario_tem_banner(self.usuario_id, banner_id):
            await interaction.response.send_message(
                f"❌ Você já possui o banner **{nome}**! Só é possível favoritar banners que você ainda não tem.",
                ephemeral=True
            )
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()

        if usuario_favoritou_banner(self.usuario_id, banner_id):
            cur.execute("DELETE FROM banners_favoritos WHERE usuario_id = ? AND banner_id = ?",
                        (str(self.usuario_id), banner_id))
            con.commit()
            con.close()
            mensagem_confirmacao = f"💔 Banner **{nome}** removido dos favoritos."
        else:
            cur.execute("INSERT OR IGNORE INTO banners_favoritos (usuario_id, banner_id) VALUES (?, ?)",
                        (str(self.usuario_id), banner_id))
            con.commit()
            con.close()
            mensagem_confirmacao = f"⭐ Banner **{nome}** favoritado! Você será avisado quando ele estiver na loja."

        self.atualizar_botoes()
        embed, arquivo = await self.gerar_embed_e_imagem()
        await interaction.response.edit_message(embed=embed, view=self, attachments=[arquivo])
        await interaction.followup.send(mensagem_confirmacao, ephemeral=True)

# ============================================================
# VIEW (BOTÕES) - Pagamento entre usuários
# ============================================================

class ViewPagamento(discord.ui.View):
    def __init__(self, remetente: discord.Member, destinatario: discord.Member, quantidade: int):
        super().__init__(timeout=60)
        self.remetente = remetente
        self.destinatario = destinatario
        self.quantidade = quantidade
        self.mensagem = None  # definida logo após o envio, usada no on_timeout

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Apenas quem vai RECEBER o pagamento pode aceitar/recusar
        if interaction.user.id != self.destinatario.id:
            await interaction.response.send_message(
                "❌ Apenas o destinatário pode responder a esta solicitação de pagamento.",
                ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.mensagem:
            try:
                embed = self.mensagem.embeds[0]
                embed.color = discord.Color.greyple()
                embed.add_field(name="Status", value="⌛ Solicitação expirada.", inline=False)
                await self.mensagem.edit(embed=embed, view=self)
            except Exception:
                pass

    @discord.ui.button(label="✅ Aceitar", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()

        # Reconfere o saldo do remetente no exato momento da aceitação,
        # já que ele pode ter gasto os Joyens enquanto o pedido estava pendente
        saldo_remetente = buscar_joyens(self.remetente.id)
        if saldo_remetente < self.quantidade:
            for item in self.children:
                item.disabled = True
            embed = interaction.message.embeds[0]
            embed.color = discord.Color.red()
            embed.add_field(
                name="Status",
                value=f"❌ Pagamento cancelado: {self.remetente.mention} não tem mais Joyens suficientes.",
                inline=False
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return

        remover_joyens(self.remetente.id, self.quantidade)
        adicionar_joyens(self.destinatario.id, self.quantidade)

        for item in self.children:
            item.disabled = True
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.green()
        embed.add_field(
            name="Status",
            value=f"✅ Pagamento aceito por {self.destinatario.mention}!",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        for item in self.children:
            item.disabled = True
        embed = interaction.message.embeds[0]
        embed.color = discord.Color.red()
        embed.add_field(
            name="Status",
            value=f"❌ Pagamento recusado por {self.destinatario.mention}.",
            inline=False
        )
        await interaction.response.edit_message(embed=embed, view=self)

class SelectEmprego(discord.ui.Select):
    def __init__(self, usuario_id, level_usuario):
        self.usuario_id = usuario_id
        options = []
        for nome, dados in EMPREGOS.items():
            level_req = dados["level_necessario"]
            pode = level_usuario >= level_req
            options.append(discord.SelectOption(
                label=f"{dados['emoji']} {nome}",
                value=nome,
                description=f"Salário: {dados['salario_min']}-{dados['salario_max']}J | Level {level_req}{'✅' if pode else '❌'}",
                default=False
            ))
        super().__init__(placeholder="Escolha um emprego...", options=options)

    async def callback(self, interaction: discord.Interaction):
        emprego_nome = self.values[0]
        emprego = EMPREGOS[emprego_nome]
        level_usuario, _ = buscar_level(self.usuario_id)

        if level_usuario < emprego["level_necessario"]:
            await interaction.response.send_message(
                f"❌ Você precisa ser **Level {emprego['level_necessario']}** para se tornar {emprego_nome}! Seu level atual é **{level_usuario}**.",
                ephemeral=True
            )
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO empregos_usuarios (usuario_id, emprego, vezes_trabalhadas)
            VALUES (?, ?, 0)
            ON CONFLICT(usuario_id) DO UPDATE SET emprego = ?, vezes_trabalhadas = 0, ultimo_trabalho = NULL
        """, (str(self.usuario_id), emprego_nome, emprego_nome))
        con.commit()
        con.close()

        embed = discord.Embed(
            title=f"{emprego['emoji']} Empregado como {emprego_nome}!",
            description=f"Você agora é um **{emprego_nome}**! Use `!trabalhar` para começar a ganhar Joyens.",
            color=discord.Color.green()
        )
        embed.add_field(name="Salário", value=f"{emprego['salario_min']} - {emprego['salario_max']} Joyens", inline=True)
        embed.add_field(name="Level necessário", value=f"Level {emprego['level_necessario']}", inline=True)
        await interaction.response.edit_message(embed=embed, view=None)

# ============================================================
# VIEW (BOTÕES) - Empregos e Trabalhar
# ============================================================

class ViewEmpregos(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        level_usuario, _ = buscar_level(usuario_id)
        self.add_item(SelectEmprego(usuario_id, level_usuario))

    def gerar_embed(self):
        embed = discord.Embed(
            title="💼 Menu de Empregos",
            description="Escolha um emprego abaixo! Empregos com ❌ precisam de level maior.",
            color=discord.Color.blue()
        )
        for nome, dados in EMPREGOS.items():
            embed.add_field(
                name=f"{dados['emoji']} {nome}",
                value=f"{dados['descricao']}\n💰 {dados['salario_min']}-{dados['salario_max']} Joyens | Level {dados['level_necessario']}",
                inline=False
            )
        return embed

# ============================================================
# VIEW (BOTÕES) - Comando de !ajuda
# ============================================================
class ViewAjuda(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    def embed_inicial(self):
        embed = discord.Embed(
            title="📖 Central de Comandos",
            description="Bem-vindo à central de comandos do **JogadorBot**!\nEscolha uma categoria abaixo para ver os comandos disponíveis.",
            color=discord.Color.blurple()
        )
        embed.add_field(
            name="💰 Economia",
            value="Comandos relacionados a Joyens, loja e trabalho.",
            inline=True
        )
        embed.add_field(
            name="ℹ️ Informação",
            value="Comandos para ver informações de usuários e do servidor.",
            inline=True
        )
        embed.add_field(
            name="🎮 Diversão",
            value="Comandos de jogos e entretenimento.",
            inline=True
        )
        embed.add_field(
            name="🔧 Outros",
            value="Comandos gerais e utilitários.",
            inline=True
        )
        embed.add_field(
            name="⚙️ Slash",
            value="Comandos de barra disponíveis apenas para admins.",
            inline=True
        )
        embed.set_footer(text="Clique em um botão para ver os comandos da categoria!")
        return embed

    def embed_economia(self):
        embed = discord.Embed(
            title="💰 Economia",
            description="Comandos relacionados a Joyens, loja e trabalho.",
            color=discord.Color.gold()
        )
        embed.add_field(name=f"`{PREFIX}empregos`", value="Abre o menu de empregos", inline=False)
        embed.add_field(name=f"`{PREFIX}trabalhar`", value="Trabalha e ganha Joyens", inline=False)
        embed.add_field(name=f"`{PREFIX}diario`", value="Coleta seus Joyens diários", inline=False)
        embed.add_field(name=f"`{PREFIX}pagar @usuario quantidade`", value="Envia Joyens para outro usuário", inline=False)
        embed.add_field(name=f"`{PREFIX}loja`", value="Abre a loja de banners", inline=False)
        embed.add_field(name=f"`{PREFIX}vender (categoria) (nome)`", value="Vende um produto pela metade do preço", inline=False)
        embed.add_field(name=f"`{PREFIX}addjoyens @usuario quantidade`", value="Adiciona Joyens a um usuário (admin)", inline=False)
        embed.set_footer(text="💰 Economia • JogadorBot")
        return embed

    def embed_informacao(self):
        embed = discord.Embed(
            title="ℹ️ Informação",
            description="Comandos para ver informações de usuários e do servidor.",
            color=discord.Color.blue()
        )
        embed.add_field(name=f"`{PREFIX}perfil [@usuario]`", value="Mostra o perfil completo do usuário", inline=False)
        embed.add_field(name=f"`{PREFIX}userinfo [@usuario]`", value="Mostra informações detalhadas de um usuário", inline=False)
        embed.add_field(name=f"`{PREFIX}level [@usuario]`", value="Mostra o level e XP do usuário", inline=False)
        embed.add_field(name=f"`{PREFIX}infojob [@usuario]`", value="Mostra informações do emprego do usuário", inline=False)
        embed.add_field(name=f"`{PREFIX}saldo [@usuario]`", value="Mostra o saldo de Joyens do usuário", inline=False)
        embed.add_field(name=f"`{PREFIX}catalogo`", value="Abre o catálogo completo de banners", inline=False)
        embed.set_footer(text="ℹ️ Informação • JogadorBot")
        return embed

    def embed_diversao(self):
        embed = discord.Embed(
            title="🎮 Diversão",
            description="Comandos de jogos e entretenimento.",
            color=discord.Color.green()
        )
        embed.add_field(name=f"`{PREFIX}dado [lados]`", value="Rola um dado. Ex: `!dado 20`", inline=False)
        embed.add_field(name=f"`{PREFIX}moeda`", value="Joga uma moeda (cara ou coroa)", inline=False)
        embed.add_field(name=f"`{PREFIX}apostar [quantidade]`", value="Aposta Joyens com 50% de chance de ganhar", inline=False)
        embed.add_field(name=f"`{PREFIX}enquete [pergunta]`", value="Cria uma enquete com ✅ e ❌", inline=False)
        embed.set_footer(text="🎮 Diversão • JogadorBot")
        return embed

    def embed_outros(self):
        embed = discord.Embed(
            title="🔧 Outros",
            description="Comandos gerais e utilitários.",
            color=discord.Color.og_blurple()
        )
        embed.add_field(name=f"`{PREFIX}oi`", value="Bot te cumprimenta", inline=False)
        embed.add_field(name=f"`{PREFIX}hora`", value="Mostra a data e hora atual", inline=False)
        embed.add_field(name=f"`{PREFIX}limpar [quantidade]`", value="Apaga mensagens (requer permissão)", inline=False)
        embed.set_footer(text="🔧 Outros • JogadorBot")
        return embed

    def embed_slash(self):
        embed = discord.Embed(
            title="⚙️ Slash",
            description="Comandos de barra disponíveis apenas para admins.",
            color=discord.Color.red()
        )
        embed.add_field(name="`/conquista criar`", value="Cria uma nova conquista no catálogo", inline=False)
        embed.add_field(name="`/conquista dar`", value="Dá uma conquista para um usuário", inline=False)
        embed.add_field(name="`/conquista lista`", value="Lista todas as conquistas disponíveis", inline=False)
        embed.add_field(name="`/banner adicionar`", value="Adiciona um banner à loja", inline=False)
        embed.add_field(name="`/banner deletar`", value="Deleta um banner da loja", inline=False)
        embed.add_field(name="`/categoria criar`", value="Cria uma categoria de banners", inline=False)
        embed.add_field(name="`/categoria deletar`", value="Deleta uma categoria e seus banners", inline=False)
        embed.add_field(name="`/categoria lista`", value="Lista todas as categorias", inline=False)
        embed.add_field(name="`/editar tipo nome`", value="Edita um produto (banner ou conquista)", inline=False)
        embed.add_field(name="`/rotacao ver`", value="Mostra os banners da rotação atual", inline=False)
        embed.add_field(name="`/rotacao forcar`", value="Força uma nova rotação imediatamente", inline=False)
        embed.add_field(name="`/adminbot gerenciar`", value="Adiciona ou remove um admin", inline=False)
        embed.add_field(name="`/adminbot lista`", value="Lista todos os admins ativos", inline=False)
        embed.set_footer(text="⚙️ Slash • JogadorBot")
        return embed

    @discord.ui.button(emoji="💰", style=discord.ButtonStyle.primary, row=0)
    async def btn_economia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embed_economia(), view=ViewAjudaCategoria())

    @discord.ui.button(emoji="ℹ️", style=discord.ButtonStyle.primary, row=0)
    async def btn_informacao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embed_informacao(), view=ViewAjudaCategoria())

    @discord.ui.button(emoji="🎮", style=discord.ButtonStyle.primary, row=0)
    async def btn_diversao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embed_diversao(), view=ViewAjudaCategoria())

    @discord.ui.button(emoji="🔧", style=discord.ButtonStyle.primary, row=0)
    async def btn_outros(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embed_outros(), view=ViewAjudaCategoria())

    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.primary, row=0)
    async def btn_slash(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=self.embed_slash(), view=ViewAjudaCategoria())


class ViewAjudaCategoria(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(emoji="💰", style=discord.ButtonStyle.secondary, row=0)
    async def btn_economia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=ViewAjuda().embed_economia(), view=self)

    @discord.ui.button(emoji="ℹ️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_informacao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=ViewAjuda().embed_informacao(), view=self)

    @discord.ui.button(emoji="🎮", style=discord.ButtonStyle.secondary, row=0)
    async def btn_diversao(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=ViewAjuda().embed_diversao(), view=self)

    @discord.ui.button(emoji="🔧", style=discord.ButtonStyle.secondary, row=0)
    async def btn_outros(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=ViewAjuda().embed_outros(), view=self)

    @discord.ui.button(emoji="⚙️", style=discord.ButtonStyle.secondary, row=0)
    async def btn_slash(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=ViewAjuda().embed_slash(), view=self)

    @discord.ui.button(label="🔙 Voltar", style=discord.ButtonStyle.danger, row=1)
    async def btn_voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=ViewAjuda().embed_inicial(), view=ViewAjuda())

# ============================================================
# EVENTOS
# ============================================================
@bot.event
async def on_ready():
    iniciar_banco()
    verificar_admins_expirados.start()
    verificar_rotacao.start()
    await bot.tree.sync()
    print(f"✅ Bot conectado como: {bot.user}")
    print(f"Servidores: {len(bot.guilds)}")
    await bot.change_presence(activity=discord.Game(name="!ajuda para ver os comandos."))

# ============================================================
# COMANDOS DE PREFIXO
# ============================================================
@bot.remove_command("help")
@bot.command(name="ajuda")
async def ajuda(ctx):
    view = ViewAjuda()
    await ctx.send(embed=view.embed_inicial(), view=view)

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
    if not ctx.guild.me.guild_permissions.manage_messages:
        await ctx.send("❌ Eu não tenho permissão para apagar mensagens aqui.")
        return
    if quantidade > 1000:
        await ctx.send("Você pode apagar no máximo 1000 mensagens de uma vez.")
        return
    await ctx.channel.purge(limit=quantidade + 1)
    confirmacao = await ctx.send(f"🗑️ {quantidade} mensagens apagadas!")
    await confirmacao.delete(delay=3)

@bot.command(name="enquete")
async def enquete(ctx, *, pergunta: str):
    embed = discord.Embed(title="📊 Enquete", description=pergunta, color=discord.Color.blue())
    embed.set_footer(text=f"Pergunta feita por {ctx.author.display_name}")
    mensagem = await ctx.send(embed=embed)
    await mensagem.add_reaction("✅")
    await mensagem.add_reaction("❌")
    await ctx.message.delete()

@bot.command(name="perfil")
async def perfil(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author

    level, xp = buscar_level(membro.id)
    xp_prox = xp_necessario(level)
    joyens = buscar_joyens(membro.id)
    conquistas = buscar_conquistas_usuario(membro.id)
    banner_arquivo = buscar_banner_ativo(membro.id)

 # Quantidade de banners do usuário
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM banners_usuarios WHERE usuario_id = ?", (str(membro.id),))
    total_banners = cur.fetchone()[0]
    con.close()

# Primeira embed — Informações gerais
    embed1 = discord.Embed(
        title=f"Perfil — Lvl.``{level}``",
        color=discord.Color.blurple()
    )
    embed1.set_thumbnail(url=membro.display_avatar.url)
    embed1.description = (
        f"**{membro.display_name}**\n"
        f"> {membro.name}\n"
        f"**ID:** ``{membro.id}``"
    )
    if xp_prox:
        porcentagem = int((xp / xp_prox) * 100)
        blocos_cheios = porcentagem // 10
        barra = "█" * blocos_cheios + "░" * (10 - blocos_cheios)
        embed1.add_field(name="XP", value=f"`{barra}` {porcentagem}%\n{xp}/{xp_prox} XP", inline=False)
    else:
        embed1.add_field(name="XP", value="🏆 Level máximo atingido!", inline=False)

# Segunda embed — Economia e outros
    embed2 = discord.Embed(color=discord.Color.blurple())
    embed2.add_field(
        name="💰 Economia",
        value=f"> **Joyens:** ``{joyens}``",
        inline=False
    )
    embed2.add_field(
        name="📊 Outros",
        value=(
            f"> **Conquistas:** ``{len(conquistas)}``\n"
            f"> **Banners:** ``{total_banners}``"
        ),
        inline=False
    )

    emprego_dados = buscar_emprego(membro.id)
    if emprego_dados:
        emprego_nome, vezes_trabalhadas, _ = emprego_dados
        emprego_info = EMPREGOS.get(emprego_nome)
        emoji_emp = emprego_info["emoji"] if emprego_info else "💼"
        embed2.add_field(
            name="💼 Emprego",
            value=f"{emoji_emp} **{emprego_nome}** | {vezes_trabalhadas} vez(es) trabalhadas",
            inline=False
        )
    else:
        embed2.add_field(name="💼 Emprego", value="Desempregado — use `!empregos`", inline=False)

# Banner ativo como imagem
    if banner_arquivo and os.path.exists(banner_arquivo):
        nome_arquivo = os.path.basename(banner_arquivo)
        arquivo_discord = discord.File(banner_arquivo, filename=nome_arquivo)
        embed2.set_image(url=f"attachment://{nome_arquivo}")
        view = ViewPerfil(membro)
        await ctx.send(embeds=[embed1, embed2], file=arquivo_discord, view=view)
    else:
        view = ViewPerfil(membro)
        await ctx.send(embeds=[embed1, embed2], view=view)
            
@bot.command(name="diario")
async def diario(ctx):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    agora = datetime.datetime.now(FUSO_BR)
    hoje = agora.date().isoformat()

    cur.execute("SELECT ultimo_diario, joyens FROM economia WHERE usuario_id = ?", (str(ctx.author.id),))
    resultado = cur.fetchone()

    if resultado and resultado[0] == hoje:
        con.close()

        # Calcula o tempo restante até a próxima meia-noite (horário de Pernambuco/Brasília)
        amanha = agora.date() + datetime.timedelta(days=1)
        proxima_meia_noite = datetime.datetime.combine(amanha, datetime.time(0, 0), tzinfo=FUSO_BR)
        restante = proxima_meia_noite - agora

        horas, resto = divmod(int(restante.total_seconds()), 3600)
        minutos, segundos = divmod(resto, 60)
        tempo_formatado = f"{horas}h {minutos}min {segundos}s"

        await ctx.send(
            f"{ctx.author.mention} Você já coletou seus Joyens hoje! "
            f"Volte daqui **{tempo_formatado}**."
        )
        return

    quantidade = random.randint(1200, 2000)
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

    xp_ganho = random.randint(250, 500)
    embed.add_field(name="XP ganho", value=f"+{xp_ganho} XP", inline=True)

    await ctx.send(embed=embed)
    await adicionar_xp(str(ctx.author.id), xp_ganho, ctx)

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
        description="Bem-vindo à loja! Use seus Joyens para comprar itens incríveis.\n> Escolha uma categoria:",
        color=discord.Color.gold()
    )
    embed.add_field(name="🖼️ Banners", value="Personalize o seu perfil com banners exclusivos!", inline=False)
    embed.set_footer(text=f"Seu saldo: {buscar_joyens(ctx.author.id)} Joyens")
    view = ViewMenuLoja(ctx.author.id)
    await ctx.send(embed=embed, view=view)

@bot.command(name="addjoyens")
async def addjoyens(ctx, membro: discord.Member, quantidade: int):
    if not eh_admin(ctx.author.id):
        await ctx.send("❌ Você não tem permissão para usar este comando.")
        return
    adicionar_joyens(membro.id, quantidade)
    novo_saldo = buscar_joyens(membro.id)
    await ctx.send(f"✅ **{quantidade} Joyens** adicionados para {membro.mention}!\nNovo saldo: **{novo_saldo} Joyens**.")

@bot.command(name="apostar")
async def apostar(ctx, quantidade: int):
    if quantidade <= 0:
        await ctx.send(f"{ctx.author.mention} tá liso? Dorme. Não dá para apostar 0 Joyens!")
        return

    saldo = buscar_joyens(ctx.author.id)
    if quantidade > saldo:
        await ctx.send(f"{ctx.author.mention} Você não tem Joyens suficientes! Seu saldo é de **{saldo} Joyens**.")
        return

    ganhou = random.random() < 0.5

    if ganhou:
        adicionar_joyens(ctx.author.id, quantidade)
        novo_saldo = buscar_joyens(ctx.author.id)
        embed = discord.Embed(
            title="🎰 Você ganhou!",
            description=f"A sorte estava do seu lado!",
            color=discord.Color.green()
        )
        embed.add_field(name="Ganho", value=f"+{quantidade} Joyens", inline=True)
        embed.add_field(name="Novo saldo", value=f"{novo_saldo} Joyens", inline=True)
    else:
        remover_joyens(ctx.author.id, quantidade)
        novo_saldo = buscar_joyens(ctx.author.id)
        embed = discord.Embed(
            title="🎰 Você perdeu!",
            description=f"Mais sorte na próxima vez!",
            color=discord.Color.red()
        )
        embed.add_field(name="Perda", value=f"-{quantidade} Joyens", inline=True)
        embed.add_field(name="Novo saldo", value=f"{novo_saldo} Joyens", inline=True)

    embed.set_footer(text=f"Aposta de {ctx.author.display_name}")
    await ctx.send(embed=embed)

@bot.command(name="catalogo")
async def catalogo(ctx):
    embed = discord.Embed(
        title="📖 Catálogo do JogadorBot",
        description="Bem-vindo ao catálogo! Escolha o que deseja ver:",
        color=discord.Color.blue()
    )
    view = ViewMenuCatalogo(ctx.author.id)
    await ctx.send(embed=embed, view=view)

@bot.command(name="pagar")
async def pay(ctx, membro: discord.Member = None, quantidade: int = None):
    if membro is None or quantidade is None:
        await ctx.send("❌ Uso correto: `!pagar @usuário quantidade`")
        return

    if membro.id == ctx.author.id:
        await ctx.send(f"{ctx.author.mention} Você não pode pagar a si mesmo!")
        return

    if membro.bot:
        await ctx.send(f"{ctx.author.mention} Você não pode pagar um bot!")
        return

    if quantidade <= 0:
        await ctx.send(f"{ctx.author.mention} A quantidade deve ser maior que 0!")
        return

    saldo = buscar_joyens(ctx.author.id)
    if quantidade > saldo:
        await ctx.send(
            f"{ctx.author.mention} Você não tem Joyens suficientes! Seu saldo é de **{saldo} Joyens**."
        )
        return

    embed = discord.Embed(
        title="💸 Solicitação de Pagamento",
        description=f"**{ctx.author.display_name}**, você recebeu uma solicitação de pagamento!",
        color=discord.Color.blue()
    )
    embed.add_field(name="De", value=ctx.author.mention, inline=True)
    embed.add_field(name="Para", value=membro.mention, inline=True)
    embed.add_field(name="Quantidade", value=f"{quantidade} Joyens", inline=True)
    embed.set_footer(text="Aguardando resposta • Expira em 60 segundos")

    view = ViewPagamento(ctx.author, membro, quantidade)
    mensagem = await ctx.send(embed=embed, view=view)
    view.mensagem = mensagem

@bot.command(name="level")
async def level_cmd(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author
    level, xp = buscar_level(membro.id)
    xp_prox = xp_necessario(level)

    embed = discord.Embed(
        title=f"⭐ Level de {membro.display_name}",
        color=discord.Color.gold()
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="Level", value=f"**{level}**", inline=True)
    embed.add_field(name="XP atual", value=f"**{xp} XP**", inline=True)

    if xp_prox:
        porcentagem = int((xp / xp_prox) * 100)
        blocos_cheios = porcentagem // 10
        barra = "█" * blocos_cheios + "░" * (10 - blocos_cheios)
        embed.add_field(name="Próximo level", value=f"`{barra}` {porcentagem}%\n{xp}/{xp_prox} XP", inline=False)
    else:
        embed.add_field(name="🏆 Level máximo!", value="Você chegou ao nível máximo!", inline=False)

    await ctx.send(embed=embed)

@bot.command(name="vender")
async def vender(ctx, categoria: str, *, nome_produto: str):
    categoria = categoria.lower()

    if categoria not in CATEGORIAS_VENDAVEIS:
        categorias_disponiveis = ", ".join(CATEGORIAS_VENDAVEIS.keys())
        await ctx.send(f"❌ Categoria **{categoria}** inválida! Categorias disponíveis: `{categorias_disponiveis}`")
        return

    config = CATEGORIAS_VENDAVEIS[categoria]
    tabela = config["tabela"]
    coluna_nome = config["coluna_nome"]
    coluna_preco = config["coluna_preco"]
    tabela_usuarios = config["tabela_usuarios"]
    coluna_id = config["coluna_id_usuario"]
    tabela_ativo = config["tabela_ativo"]
    coluna_ativo_id = config["coluna_ativo_id"]

    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    # Verifica se o produto existe no catálogo
    cur.execute(f"SELECT id, {coluna_nome}, {coluna_preco} FROM {tabela} WHERE LOWER({coluna_nome}) = LOWER(?)",
                (nome_produto,))
    produto = cur.fetchone()

    if not produto:
        await ctx.send(f"❌ Produto **{nome_produto}** não encontrado na categoria **{categoria}**.")
        con.close()
        return

    produto_id, produto_nome, produto_preco = produto

    # Verifica se o usuário possui o produto
    cur.execute(f"SELECT 1 FROM {tabela_usuarios} WHERE usuario_id = ? AND {coluna_id} = ?",
                (str(ctx.author.id), produto_id))
    possui = cur.fetchone()

    if not possui:
        await ctx.send(f"❌ Você não possui o produto **{produto_nome}**!")
        con.close()
        return

    valor_venda = produto_preco // 2

    # Remove o produto do inventário do usuário
    cur.execute(f"DELETE FROM {tabela_usuarios} WHERE usuario_id = ? AND {coluna_id} = ?",
                (str(ctx.author.id), produto_id))

    # Remove dos favoritos se for banner
    if categoria == "banner":
        cur.execute("DELETE FROM banners_favoritos WHERE usuario_id = ? AND banner_id = ?",
                    (str(ctx.author.id), produto_id))

    # Remove o produto ativo se for o que está sendo vendido
    cur.execute(f"SELECT {coluna_ativo_id} FROM {tabela_ativo} WHERE usuario_id = ?",
                (str(ctx.author.id),))
    ativo = cur.fetchone()
    if ativo and ativo[0] == produto_id:
        cur.execute(f"DELETE FROM {tabela_ativo} WHERE usuario_id = ?", (str(ctx.author.id),))

    con.commit()
    con.close()

    adicionar_joyens(ctx.author.id, valor_venda)
    novo_saldo = buscar_joyens(ctx.author.id)

    embed = discord.Embed(
        title="💸 Produto Vendido!",
        color=discord.Color.green()
    )
    embed.add_field(name="Produto", value=f"{produto_nome}", inline=True)
    embed.add_field(name="Categoria", value=categoria.capitalize(), inline=True)
    embed.add_field(name="Valor recebido", value=f"{valor_venda} Joyens", inline=True)
    embed.add_field(name="Novo saldo", value=f"{novo_saldo} Joyens", inline=False)
    embed.set_footer(text=f"Preço original: {produto_preco} Joyens — vendido por metade do valor")
    await ctx.send(embed=embed)

@bot.command(name="empregos")
async def empregos(ctx):
    view = ViewEmpregos(ctx.author.id)
    embed = view.gerar_embed()
    await ctx.send(embed=embed, view=view)

@bot.command(name="trabalhar")
async def trabalhar(ctx):
    emprego_dados = buscar_emprego(ctx.author.id)

    # Se não tiver emprego, redireciona para o menu
    if not emprego_dados:
        view = ViewEmpregos(ctx.author.id)
        embed = view.gerar_embed()
        await ctx.send("Você ainda não tem um emprego! Escolha um abaixo:", embed=embed, view=view)
        return

    emprego_nome, vezes_trabalhadas, ultimo_trabalho = emprego_dados

    # Verifica cooldown
    restante = tempo_restante_trabalho(ultimo_trabalho)
    if restante != 0:
        await ctx.send(f"⏰ {ctx.author.mention} Você precisa descansar! Pode trabalhar novamente em **{restante}**.")
        return

    emprego = EMPREGOS.get(emprego_nome)
    if not emprego:
        await ctx.send("❌ Seu emprego não foi encontrado! Use `!empregos` para escolher um novo.")
        return

    # Calcula salário e XP
    salario = random.randint(emprego["salario_min"], emprego["salario_max"])
    xp_ganho = random.randint(50, 100)
    acao = random.choice(emprego["acoes"]).format(salario=salario)

    # Atualiza banco
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    agora = datetime.datetime.now().isoformat()
    cur.execute("""
        UPDATE empregos_usuarios
        SET vezes_trabalhadas = vezes_trabalhadas + 1, ultimo_trabalho = ?
        WHERE usuario_id = ?
    """, (agora, str(ctx.author.id)))
    con.commit()
    con.close()

    adicionar_joyens(ctx.author.id, salario)
    novo_saldo = buscar_joyens(ctx.author.id)

    embed = discord.Embed(
        title=f"{emprego['emoji']} {emprego_nome}",
        description=acao,
        color=discord.Color.green()
    )
    embed.add_field(name="Salário recebido", value=f"{salario} Joyens", inline=True)
    embed.add_field(name="Novo saldo", value=f"{novo_saldo} Joyens", inline=True)
    embed.add_field(name="XP ganho", value=f"+{xp_ganho} XP", inline=True)
    embed.set_footer(text=f"Próximo trabalho em 40 minutos")
    await ctx.send(embed=embed)
    await adicionar_xp(str(ctx.author.id), xp_ganho, ctx)

@bot.command(name="infojob")
async def infojob(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author

    emprego_dados = buscar_emprego(membro.id)
    if not emprego_dados:
        await ctx.send(f"**{membro.display_name}** não tem emprego! Use `!empregos` para escolher um.")
        return

    emprego_nome, vezes_trabalhadas, ultimo_trabalho = emprego_dados
    emprego = EMPREGOS.get(emprego_nome)
    if not emprego:
        await ctx.send("❌ Emprego não encontrado no sistema.")
        return

    restante = tempo_restante_trabalho(ultimo_trabalho)
    disponivel = "Disponível agora!" if restante == 0 else f"Disponível em {restante}"

    embed = discord.Embed(
        title=f"{emprego['emoji']} Informações de Emprego",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="Funcionário", value=membro.display_name, inline=True)
    embed.add_field(name="Emprego", value=emprego_nome, inline=True)
    embed.add_field(name="Salário", value=f"{emprego['salario_min']}-{emprego['salario_max']} Joyens", inline=True)
    embed.add_field(name="Level necessário", value=f"Level {emprego['level_necessario']}", inline=True)
    embed.add_field(name="Vezes trabalhadas", value=str(vezes_trabalhadas), inline=True)
    embed.add_field(name="Próximo trabalho", value=disponivel, inline=True)
    await ctx.send(embed=embed)

class Layout(ui.LayoutView):
    def __init__(self):
        super().__init__()

        container = ui.Container(ui.TextDisplay("Salve! Este é um comando teste de V2."))
        container.accent_color = discord.Colour.purple()
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        botao_1 = ui.Button(label="Botão 1")
        
        sessao = ui.Section(ui.TextDisplay("Botão ao lado:"), accessory=botao_1)
        
        container.add_item(sessao)
        self.add_item(container)

    async def botao_1_resposta(self, interect:discord.Interaction)
        await interact.response.send_message(f"Olá, {interact.user.name}!")

@bot.command(name="Teste")
async def Teste(ctx:commands.Context):
    layout = Layout()
    await ctx.reply(view=layout)

# ============================================================
# COMANDOS SLASH — CONQUISTAS
# ============================================================
conquista_group = app_commands.Group(name="conquista", description="Sistema de conquistas")

@conquista_group.command(name="criar", description="Cria uma nova conquista no catálogo")
@app_commands.describe(
    nome="Nome da conquista",
    descricao="Descrição da conquista",
    emoji="Emoji que representa a conquista"
)
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def conquista_criar(interaction: discord.Interaction, nome: str, descricao: str, emoji: str):
    con = sqlite3.connect("jogadorbot.db")
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
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    cur.execute("SELECT id, nome, descricao, emoji FROM conquistas WHERE LOWER(nome) = LOWER(?)", (nome,))
    conquista = cur.fetchone()

    if conquista is None:
        await interaction.response.send_message(f"❌ Conquista **{nome}** não encontrada. Use `/conquista lista` para ver as disponíveis.", ephemeral=True)
        con.close()
        return

    conquista_id, c_nome, c_descricao, c_emoji = conquista
    data_atual = datetime.datetime.now().strftime("%d/%m/%Y")

    # ✅ Verifica ANTES de inserir
    cur.execute("SELECT 1 FROM conquistas_usuarios WHERE usuario_id = ? AND conquista_id = ?",
                (str(membro.id), conquista_id))
    if cur.fetchone():
        await interaction.response.send_message(
            f"⚠️ {membro.mention} já possui a conquista **{c_emoji} {c_nome}**!",
            ephemeral=True
        )
        con.close()
        return

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
    raridade="Comum, Incomum, Raro, Epico ou Lendario",
    categoria="Nome exato da categoria",
    imagem="Imagem do banner"
)
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def banner_adicionar(interaction: discord.Interaction, nome: str, descricao: str, preco: int, raridade: str, categoria: str, imagem: discord.Attachment):
    if raridade not in RARIDADES:
        raridades_disponiveis = ", ".join(RARIDADES.keys())
        await interaction.response.send_message(
            f"❌ Raridade **{raridade}** inválida! Use: `{raridades_disponiveis}`",
            ephemeral=True
        )
        return
    
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id FROM categorias_banner WHERE LOWER(nome) = LOWER(?)", (categoria,))
    resultado = cur.fetchone()
    if not resultado:
        await interaction.response.send_message(
            f"❌ Categoria **{categoria}** não encontrada.",
            ephemeral=True
        )
        con.close()
        return
    
    cat_id = resultado[0]
    os.makedirs("banners", exist_ok=True)
    
    # ✅ Detecta extensão correta
    if imagem.content_type and "gif" in imagem.content_type:
        extensao = ".gif"
    elif imagem.content_type and "png" in imagem.content_type:
        extensao = ".png"
    elif imagem.content_type and ("jpeg" in imagem.content_type or "jpg" in imagem.content_type):
        extensao = ".jpg"
    else:
        extensao = ".png"  # padrão
    
    arquivo_path = f"banners/{nome.replace(' ', '_')}{extensao}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(imagem.url) as resp:
            imagem_bytes = await resp.read()
    
    with open(arquivo_path, "wb") as f:
        f.write(imagem_bytes)
    
    try:
        cur.execute("INSERT INTO banners (nome, descricao, preco, arquivo, categoria_id, raridade) VALUES (?, ?, ?, ?, ?, ?)",
                    (nome, descricao, preco, arquivo_path, cat_id, raridade))
        con.commit()
        await interaction.response.send_message(
            f"✅ Banner **{nome}** ({raridade}) adicionado por {preco} Joyens!", ephemeral=True
        )
    except sqlite3.IntegrityError:
        await interaction.response.send_message(f"❌ Já existe um banner com o nome **{nome}**.", ephemeral=True)
    finally:
        con.close()

@banner_group.command(name="deletar", description="Deleta um banner da loja (admin)")
@app_commands.describe(nome="Nome exato do banner a deletar")
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def banner_deletar(interaction: discord.Interaction, nome: str):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, arquivo FROM banners WHERE LOWER(nome) = LOWER(?)", (nome,))
    resultado = cur.fetchone()
    if not resultado:
        await interaction.response.send_message(f"❌ Banner **{nome}** não encontrado.", ephemeral=True)
        con.close()
        return
    banner_id, arquivo_path = resultado
    cur.execute("DELETE FROM banners_usuarios WHERE banner_id = ?", (banner_id,))
    cur.execute("DELETE FROM banner_ativo WHERE banner_id = ?", (banner_id,))
    cur.execute("DELETE FROM banners WHERE id = ?", (banner_id,))
    con.commit()
    con.close()
    if os.path.exists(arquivo_path):
        os.remove(arquivo_path)
    await interaction.response.send_message(f"✅ Banner **{nome}** deletado da loja e removido de todos os usuários.", ephemeral=True)

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

        con = sqlite3.connect("jogadorbot.db")
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
        con = sqlite3.connect("jogadorbot.db")
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
    con = sqlite3.connect("jogadorbot.db")
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

categoria_group = app_commands.Group(name="categoria", description="Gerenciamento de categorias de banners")

@categoria_group.command(name="criar", description="Cria uma nova categoria de banners")
@app_commands.describe(nome="Nome da categoria", emoji="Emoji da categoria")
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def categoria_criar(interaction: discord.Interaction, nome: str, emoji: str):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO categorias_banner (nome, emoji) VALUES (?, ?)", (nome, emoji))
        con.commit()
        await interaction.response.send_message(f"✅ Categoria **{emoji} {nome}** criada!", ephemeral=True)
    except sqlite3.IntegrityError:
        await interaction.response.send_message(f"❌ Já existe uma categoria com o nome **{nome}**.", ephemeral=True)
    finally:
        con.close()

@categoria_group.command(name="deletar", description="Deleta uma categoria e todos os seus banners")
@app_commands.describe(nome="Nome da categoria a deletar")
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def categoria_deletar(interaction: discord.Interaction, nome: str):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id FROM categorias_banner WHERE LOWER(nome) = LOWER(?)", (nome,))
    resultado = cur.fetchone()
    if not resultado:
        await interaction.response.send_message(f"❌ Categoria **{nome}** não encontrada.", ephemeral=True)
        con.close()
        return
    cat_id = resultado[0]
    # ✅ Buscar arquivos ANTES de deletar
    cur.execute("SELECT arquivo FROM banners WHERE categoria_id = ?", (cat_id,))
    arquivos = [row[0] for row in cur.fetchall()]
    
    cur.execute("SELECT id FROM banners WHERE categoria_id = ?", (cat_id,))
    banner_ids = [row[0] for row in cur.fetchall()]
    for bid in banner_ids:
        cur.execute("DELETE FROM banners_usuarios WHERE banner_id = ?", (bid,))
        cur.execute("DELETE FROM banner_ativo WHERE banner_id = ?", (bid,))
    cur.execute("DELETE FROM banners WHERE categoria_id = ?", (cat_id,))
    cur.execute("DELETE FROM categorias_banner WHERE id = ?", (cat_id,))
    con.commit()
    con.close()
    
    # ✅ Remover arquivos do disco
    for arquivo in arquivos:
        if os.path.exists(arquivo):
            try:
                os.remove(arquivo)
            except OSError:
                pass
    await interaction.response.send_message(
        f"✅ Categoria **{nome}** e todos os seus banners foram deletados.", ephemeral=True
    )

@categoria_group.command(name="lista", description="Lista todas as categorias disponíveis")
async def categoria_lista(interaction: discord.Interaction):
    categorias = buscar_todas_categorias()
    if not categorias:
        await interaction.response.send_message("Nenhuma categoria criada ainda.", ephemeral=True)
        return
    embed = discord.Embed(title="📋 Categorias de Banners", color=discord.Color.purple())
    for _, nome, emoji in categorias:
        embed.add_field(name=f"{emoji} {nome}", value="\u200b", inline=True)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@admin_group.command(name="dar", description="Dá XP, Level, Joyens ou Banner para um usuário (admin)")
@app_commands.describe(
    categoria="O que você quer dar para o usuário",
    valor="Quantidade (para xp/level/joyens) ou nome exato do banner (para banner)",
    membro="Quem vai receber"
)
@app_commands.choices(categoria=[
    app_commands.Choice(name="XP", value="xp"),
    app_commands.Choice(name="Level", value="level"),
    app_commands.Choice(name="Joyens", value="joyens"),
    app_commands.Choice(name="Banner", value="banner"),
])
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def adminbot_dar(
    interaction: discord.Interaction,
    categoria: app_commands.Choice[str],
    valor: str,
    membro: discord.Member
):
    if membro.bot:
        await interaction.response.send_message("❌ Não é possível dar itens para um bot!", ephemeral=True)
        return

    cat = categoria.value

    if cat == "xp":
        if not valor.lstrip("-").isdigit():
            await interaction.response.send_message("❌ Para XP, o valor deve ser um número inteiro.", ephemeral=True)
            return
        quantidade = int(valor)
        if quantidade <= 0:
            await interaction.response.send_message("❌ A quantidade deve ser maior que 0!", ephemeral=True)
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO level_usuarios (usuario_id, level, xp) VALUES (?, 0, 0)
            ON CONFLICT(usuario_id) DO NOTHING
        """, (str(membro.id),))
        con.commit()
        con.close()

        await interaction.response.send_message(
            f"✅ **{quantidade} XP** adicionado para {membro.mention}!", ephemeral=True
        )
        await adicionar_xp(str(membro.id), quantidade, interaction)

    elif cat == "level":
        if not valor.lstrip("-").isdigit():
            await interaction.response.send_message("❌ Para Level, o valor deve ser um número inteiro.", ephemeral=True)
            return
        quantidade = int(valor)
        if quantidade <= 0:
            await interaction.response.send_message("❌ A quantidade deve ser maior que 0!", ephemeral=True)
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO level_usuarios (usuario_id, level, xp) VALUES (?, 0, 0)
            ON CONFLICT(usuario_id) DO NOTHING
        """, (str(membro.id),))
        con.commit()
        con.close()

        level_atual, xp_atual = buscar_level(membro.id)
        novo_level = min(level_atual + quantidade, LEVEL_MAX)

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("UPDATE level_usuarios SET level = ? WHERE usuario_id = ?",
                    (novo_level, str(membro.id)))
        con.commit()
        con.close()

        embed = discord.Embed(
            title="⬆️ Level Concedido!",
            description=f"{membro.mention} subiu para o **level {novo_level}**!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Concedido por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif cat == "joyens":
        if not valor.lstrip("-").isdigit():
            await interaction.response.send_message("❌ Para Joyens, o valor deve ser um número inteiro.", ephemeral=True)
            return
        quantidade = int(valor)
        if quantidade <= 0:
            await interaction.response.send_message("❌ A quantidade deve ser maior que 0!", ephemeral=True)
            return

        adicionar_joyens(membro.id, quantidade)
        novo_saldo = buscar_joyens(membro.id)

        embed = discord.Embed(
            title="💰 Joyens Concedidos!",
            description=f"{membro.mention} recebeu **{quantidade} Joyens**!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Novo saldo", value=f"{novo_saldo} Joyens")
        embed.set_footer(text=f"Concedido por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    elif cat == "banner":
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("SELECT id, nome FROM banners WHERE LOWER(nome) = LOWER(?)", (valor,))
        resultado = cur.fetchone()

        if not resultado:
            con.close()
            await interaction.response.send_message(
                f"❌ Banner **{valor}** não encontrado. Confira o nome exato no catálogo.",
                ephemeral=True
            )
            return

        banner_id, banner_nome = resultado

        if usuario_tem_banner(membro.id, banner_id):
            con.close()
            await interaction.response.send_message(
                f"❌ {membro.mention} já possui o banner **{banner_nome}**.", ephemeral=True
            )
            return

        cur.execute("INSERT OR IGNORE INTO banners_usuarios (usuario_id, banner_id) VALUES (?, ?)",
                     (str(membro.id), banner_id))
        cur.execute("DELETE FROM banners_favoritos WHERE usuario_id = ? AND banner_id = ?",
                     (str(membro.id), banner_id))
        con.commit()
        con.close()

        embed = discord.Embed(
            title="🖼️ Banner Concedido!",
            description=f"{membro.mention} recebeu o banner **{banner_nome}**!",
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Concedido por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # 👉 PARA ADICIONAR UMA NOVA CATEGORIA NO FUTURO, cole aqui um novo bloco:
    # elif cat == "nome_da_categoria":
    #     ... sua lógica de banco de dados para essa categoria ...

@adminbot_dar.error
async def adminbot_dar_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
    else:
        raise error

# ============================================================
# COMANDOS SLASH — Edição de produtos
# ============================================================

@bot.tree.command(name="editar", description="Edita um produto da loja ou catálogo (admin)")
@app_commands.describe(
    tipo="Tipo do produto: banner ou conquista",
    nome="Nome atual do produto",
    novo_nome="Novo nome (opcional)",
    descricao="Nova descrição (opcional)",
    preco="Novo preço em Joyens (apenas banners)",
    categoria="Nova categoria (apenas banners)",
    emoji="Novo emoji (apenas conquistas)",
    imagem="Nova imagem (apenas banners)"
)
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def editar(
    interaction: discord.Interaction,
    tipo: str,
    nome: str,
    novo_nome: str = None,
    descricao: str = None,
    preco: int = None,
    raridade: str = None,
    categoria: str = None,
    emoji: str = None,
    imagem: discord.Attachment = None
):
    tipo = tipo.lower()

    if tipo not in TIPOS_EDITAVEIS:
        tipos_disponiveis = ", ".join(TIPOS_EDITAVEIS.keys())
        await interaction.response.send_message(
            f"❌ Tipo **{tipo}** inválido! Tipos disponíveis: `{tipos_disponiveis}`",
            ephemeral=True
        )
        return

    config = TIPOS_EDITAVEIS[tipo]
    tabela = config["tabela"]
    campos = config["campos"]

    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    # Verifica se o produto existe
    cur.execute(f"SELECT id FROM {tabela} WHERE LOWER(nome) = LOWER(?)", (nome,))
    resultado = cur.fetchone()
    if not resultado:
        await interaction.response.send_message(
            f"❌ {tipo.capitalize()} **{nome}** não encontrado.", ephemeral=True
        )
        con.close()
        return

    produto_id = resultado[0]
    alteracoes = []

    # Novo nome
    if novo_nome and "novo_nome" in campos:
        cur.execute(f"UPDATE {tabela} SET nome = ? WHERE id = ?", (novo_nome, produto_id))
        alteracoes.append(f"Nome → **{novo_nome}**")

    # Descrição
    if descricao and "descricao" in campos:
        cur.execute(f"UPDATE {tabela} SET descricao = ? WHERE id = ?", (descricao, produto_id))
        alteracoes.append(f"Descrição atualizada")

    # Preço (apenas banners)
    if preco is not None and "preco" in campos:
        cur.execute(f"UPDATE {tabela} SET preco = ? WHERE id = ?", (preco, produto_id))
        alteracoes.append(f"Preço → **{preco} Joyens**")

    # Emoji (apenas conquistas)
    if emoji and "emoji" in campos:
        cur.execute(f"UPDATE {tabela} SET emoji = ? WHERE id = ?", (emoji, produto_id))
        alteracoes.append(f"Emoji → {emoji}")

    # Raridade (apenas banners)
    if "raridade" in campos and raridade:
        if raridade not in RARIDADES:
            raridades_disponiveis = ", ".join(RARIDADES.keys())
            await interaction.response.send_message(
                f"❌ Raridade inválida! Use: `{raridades_disponiveis}`", ephemeral=True
            )
            con.close()
            return
        cur.execute(f"UPDATE {tabela} SET raridade = ? WHERE id = ?", (raridade, produto_id))
        alteracoes.append(f"Raridade → **{raridade}**")
    
    # Categoria (apenas banners)
    if categoria and "categoria" in campos:
        cur.execute("SELECT id FROM categorias_banner WHERE LOWER(nome) = LOWER(?)", (categoria,))
        cat_resultado = cur.fetchone()
        if not cat_resultado:
            await interaction.response.send_message(
                f"❌ Categoria **{categoria}** não encontrada. Use `/categoria lista` para ver as disponíveis.",
                ephemeral=True
            )
            con.close()
            return
        cur.execute(f"UPDATE {tabela} SET categoria_id = ? WHERE id = ?", (cat_resultado[0], produto_id))
        alteracoes.append(f"Categoria → **{categoria}**")

    # Imagem (apenas banners)
    if imagem and "imagem" in campos:
        cur.execute("SELECT arquivo FROM banners WHERE id = ?", (produto_id,))
        arquivo_antigo = cur.fetchone()[0]
        novo_arquivo = f"banners/{(novo_nome or nome).replace(' ', '_')}.png"
        async with aiohttp.ClientSession() as session:
            async with session.get(imagem.url) as resp:
                imagem_bytes = await resp.read()
        with open(novo_arquivo, "wb") as f:
            f.write(imagem_bytes)
        if arquivo_antigo != novo_arquivo and os.path.exists(arquivo_antigo):
            os.remove(arquivo_antigo)
        cur.execute("UPDATE banners SET arquivo = ? WHERE id = ?", (novo_arquivo, produto_id))
        alteracoes.append("Imagem atualizada")

    if not alteracoes:
        await interaction.response.send_message(
            "❌ Nenhuma alteração foi feita! Preencha pelo menos um campo para editar.",
            ephemeral=True
        )
        con.close()
        return

    con.commit()
    con.close()

    embed = discord.Embed(
        title=f"✅ {tipo.capitalize()} editado com sucesso!",
        description="\n".join(alteracoes),
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Produto: {nome}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

rotacao_group = app_commands.Group(name="rotacao", description="Gerenciamento da rotação da loja")

@rotacao_group.command(name="ver", description="Mostra os banners da rotação atual")
async def rotacao_ver(interaction: discord.Interaction):
    banners, expira = buscar_banners_rotacao()
    if not banners:
        await interaction.response.send_message("Nenhuma rotação ativa no momento.", ephemeral=True)
        return
    expira_dt = datetime.datetime.fromisoformat(expira)
    embed = discord.Embed(
        title="🔄 Rotação Atual da Loja",
        color=discord.Color.purple()
    )
    for banner_id, nome, descricao, preco, arquivo, raridade in banners:
        embed.add_field(name=nome, value=f"Raridade: **{raridade}** | Preço: **{preco} Joyens**", inline=False)
    embed.set_footer(text=f"Próxima rotação: {expira_dt.strftime('%d/%m/%Y às %H:%M')}")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@rotacao_group.command(name="forcar", description="Força uma nova rotação imediatamente (admin)")
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def rotacao_forcar(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    ids_sorteados, expira = sortear_nova_rotacao()
    if ids_sorteados is None:
        await interaction.followup.send(expira, ephemeral=True)
        return
    canal = bot.get_channel(CANAL_NOTIFICACOES_ID)
    if canal:
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            SELECT b.nome, b.raridade FROM rotacao_atual ra
            JOIN banners b ON ra.banner_id = b.id
        """)
        banners = cur.fetchall()
        con.close()
        expira_dt = datetime.datetime.fromisoformat(expira)
        embed = discord.Embed(
            title="🔄 Nova Rotação da Loja!",
            description="Os banners disponíveis na loja mudaram!",
            color=discord.Color.purple()
        )
        for nome, raridade in banners:
            embed.add_field(name=nome, value=f"Raridade: **{raridade}**", inline=True)
        embed.set_footer(text=f"Próxima rotação: {expira_dt.strftime('%d/%m/%Y às %H:%M')}")
        await canal.send(embed=embed)
    await interaction.followup.send("✅ Nova rotação forçada com sucesso!", ephemeral=True)

# ============================================================
# COMANDOS SLASH — Level e XP
# ============================================================

level_group = app_commands.Group(name="level", description="Gerenciamento de level e XP")

@level_group.command(name="dar", description="Dá XP ou Level para um usuário (admin)")
@app_commands.describe(
    tipo="Se vai dar XP ou Level diretamente",
    quantidade="Quantidade a ser adicionada",
    membro="Quem vai receber o XP/Level"
)
@app_commands.choices(tipo=[
    app_commands.Choice(name="XP", value="xp"),
    app_commands.Choice(name="Level", value="level"),
])
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def level_dar(interaction: discord.Interaction, tipo: app_commands.Choice[str], quantidade: int, membro: discord.Member):
    if membro.bot:
        await interaction.response.send_message("❌ Não é possível dar XP/Level para um bot!", ephemeral=True)
        return

    if quantidade <= 0:
        await interaction.response.send_message("❌ A quantidade deve ser maior que 0!", ephemeral=True)
        return

    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO level_usuarios (usuario_id, level, xp) VALUES (?, 0, 0)
        ON CONFLICT(usuario_id) DO NOTHING
    """, (str(membro.id),))
    con.commit()
    con.close()

    if tipo.value == "xp":
        await interaction.response.send_message(
            f"✅ **{quantidade} XP** adicionado para {membro.mention}!",
            ephemeral=True
        )
        await adicionar_xp(str(membro.id), quantidade, interaction)
    else:
        level_atual, xp_atual = buscar_level(membro.id)
        novo_level = min(level_atual + quantidade, LEVEL_MAX)

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("UPDATE level_usuarios SET level = ? WHERE usuario_id = ?",
                    (novo_level, str(membro.id)))
        con.commit()
        con.close()

        embed = discord.Embed(
            title="⬆️ Level Concedido!",
            description=f"{membro.mention} subiu para o **level {novo_level}**!",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Concedido por {interaction.user.display_name}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@level_dar.error
async def level_dar_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)
    else:
        raise error

bot.tree.add_command(rotacao_group)

bot.tree.add_command(categoria_group)

bot.tree.add_command(level_group)

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

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CheckFailure):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar este comando.", ephemeral=True
            )
    elif isinstance(error, app_commands.MissingPermissions):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Permissões insuficientes.", ephemeral=True
            )

bot.run(TOKEN)
