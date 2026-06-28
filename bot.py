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
DONO_ID = 880243114403573780  # Seu ID — sempre tem acesso total

# Canais de notificação
CANAL_CONQUISTAS_ID = 1517028501356806144
CANAL_NOTIFICACOES_ID = 1520676033425313885

# Rotação da loja
DURACAO_ROTACAO_HORAS = 6
BANNERS_POR_ROTACAO = 4

# Raridades disponíveis e suas chances na rotação
RARIDADES = {
    "Comum":    0.50,
    "Incomum":  0.25,
    "Raro":     0.15,
    "Epico":    0.07,
    "Lendario": 0.03,
}

# ============================================================
# TIPOS EDITÁVEIS — Para adicionar novo tipo, copie um bloco
# e ajuste o nome e os campos. "tabela" é o nome da tabela
# no banco de dados e "campos" são os campos editáveis.
# ============================================================
TIPOS_EDITAVEIS = {
    "banner": {
        "tabela": "banners",
        "campos": ["novo_nome", "descricao", "preco", "categoria", "imagem"]
    },
    "conquista": {
        "tabela": "conquistas",
        "campos": ["novo_nome", "descricao", "emoji"]
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

# Dados foto de perfil
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((120, 120))
    mascara = Image.new("L", (120, 120), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, 120, 120), fill=255)
    avatar_circular = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    avatar_circular.paste(avatar, mask=mascara)
    
# Banner de perfil
    card = Image.open("perfil.png").convert("RGBA").resize((800, 400))

    draw = ImageDraw.Draw(card)
    card.paste(avatar_circular, (8, 8), avatar_circular)
    
    banner_arquivo = buscar_banner_ativo(usuario.id)
    if banner_arquivo and os.path.exists(banner_arquivo):
        banner = Image.open(banner_arquivo).convert("RGBA").resize((800, 263))
        card.paste(banner, (0, 137), banner)

# Textos de perfil
    fonte_nome = ImageFont.truetype("/app/fonte.ttf", 35)
    fonte_info = ImageFont.truetype("/app/fonte_regular.ttf", 25)

    draw.text((140, 10), usuario.display_name, font=fonte_nome, fill=(255, 255, 255))
    draw.text((140, 40), f"@{usuario.name}", font=fonte_info, fill=(100, 100, 100))
    conquistas = buscar_conquistas_usuario(usuario.id)
    draw.text((140, 97), f"{len(conquistas)} Conquistas", font=fonte_info, fill=(255, 255, 255))
    joyens = buscar_joyens(usuario.id)
    draw.text((345, 97), f"{joyens} Joyens", font=fonte_info, fill=(255, 255, 255))

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

@tasks.loop(minutes=10)
async def verificar_rotacao():
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT expira FROM rotacao_atual LIMIT 1")
    resultado = cur.fetchone()
    con.close()

    precisa_rotacionar = False
    if not resultado:
        precisa_rotacionar = True
    else:
        expira = datetime.datetime.fromisoformat(resultado[0])
        fuso_brasilia = datetime.timezone(datetime.timedelta(hours=-3))
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

        con = sqlite3.connect("/data/jogadorbot.db")
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
            description="Os banners disponíveis na loja mudaram! Corra para conferir antes que acabe.",
            color=discord.Color.purple()
        )
        for nome, raridade in banners:
            embed.add_field(name=nome, value=f"Raridade: **{raridade}**", inline=True)
        embed.set_footer(text=f"Próxima rotação: {expira_dt.strftime('%d/%m/%Y às %H:%M')}")
        await canal.send(embed=embed)

# ============================================================
# FUNÇÕES AUXILIARES - Categorias banner
# ============================================================

def buscar_todas_categorias():
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, emoji FROM categorias_banner ORDER BY nome")
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_banners_por_categoria(categoria_id):
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, descricao, preco, arquivo FROM banners WHERE categoria_id = ? ORDER BY id", (categoria_id,))
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_banners_rotacao():
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT b.id, b.nome, b.descricao, b.preco, b.arquivo, b.raridade
        FROM rotacao_atual ra
        JOIN banners b ON ra.banner_id = b.id
        LIMIT 1
    """)
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

# ============================================================
# FUNÇÕES AUXILIARES - Rotação de banner na loja
# ============================================================

def sortear_nova_rotacao():
    import random as rnd
    con = sqlite3.connect("/data/jogadorbot.db")
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
    expira = (datetime.datetime.now(fuso_brasilia) + datetime.timedelta(hours=DURACAO_ROTACAO_HORAS)).isoformat()
    cur.execute("DELETE FROM rotacao_atual")
    for bid in ids_sorteados:
        cur.execute("INSERT INTO rotacao_atual (banner_id, expira) VALUES (?, ?)", (bid, expira))
        cur.execute("INSERT INTO rotacao_historico (banner_id) VALUES (?)", (bid,))

    con.commit()
    con.close()
    return ids_sorteados, expira

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
        con = sqlite3.connect("/data/jogadorbot.db")
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
            color=discord.Color.purple()
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
        banner_id, nome, descricao, preco, arquivo, raridade = self.banners[self.index]
        joyens = buscar_joyens(self.usuario_id)
        if joyens < preco:
            await interaction.response.send_message(
                f"❌ Você não tem Joyens suficientes! Você tem {joyens} e precisa de {preco}.",
                ephemeral=True
            )
            return
        remover_joyens(self.usuario_id, preco)
        con = sqlite3.connect("/data/jogadorbot.db")
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO banners_usuarios (usuario_id, banner_id) VALUES (?, ?)",
                    (str(self.usuario_id), banner_id))
        con.commit()
        con.close()
        self.atualizar_botoes()
        await interaction.response.send_message(
            f"✅ Banner **{nome}** comprado! Use o botão **🖼️ Banners** no seu perfil para equipá-lo.",
            ephemeral=True
        )
        await interaction.message.edit(view=self)

    @discord.ui.button(label="🔙 Loja", style=discord.ButtonStyle.danger, row=0)
    async def voltar_loja(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏪 Loja do JogadorBot",
            description="Bem-vindo à loja! Use seus Joyens para comprar itens exclusivos.\nEscolha uma categoria abaixo:",
            color=discord.Color.purple()
        )
        embed.add_field(name="🖼️ Banners da rotação", value="Banners exclusivos por tempo limitado!", inline=False)
        embed.set_footer(text=f"Seu saldo: {buscar_joyens(self.usuario_id)} Joyens")
        view = ViewMenuLoja(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ViewMenuLoja(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id

    @discord.ui.button(label="🖼️ Banners da rotação", style=discord.ButtonStyle.primary)
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
        con = sqlite3.connect("/data/jogadorbot.db")
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
        con = sqlite3.connect("/data/jogadorbot.db")
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
                con2 = sqlite3.connect("/data/jogadorbot.db")
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
        btn_voltar = discord.ui.Button(label="🔙 Voltar ao Perfil", style=discord.ButtonStyle.danger, row=3)

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
            buffer, total = await gerar_card_perfil(self.usuario)
            arquivo = discord.File(buffer, filename="perfil.png")
            embed = discord.Embed(color=discord.Color.blurple())
            embed.set_image(url="attachment://perfil.png")
            view = ViewPerfil(self.usuario)
            await interaction.response.edit_message(embed=embed, view=view, attachments=[arquivo])

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
            description="Selecione um banner para equipar no seu perfil.\nO banner ativo aparece em verde.",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=self.usuario.display_avatar.url)
        embed.set_footer(text=f"Página {self.pagina + 1} de {self.total_paginas} • {len(self.banners)} banner(s) no total")
        return embed

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
    print(f"   Servidores: {len(bot.guilds)}")
    await bot.change_presence(activity=discord.Game(name="!perfil para ver seu perfil"))

# ============================================================
# COMANDOS DE PREFIXO
# ============================================================
@bot.remove_command("help")
@bot.command(name="ajuda")
async def ajuda(ctx):
    embed = discord.Embed(
        title="📖 Lista de Comandos",
        description=f"Todos os comandos usam o prefixo `{PREFIX}`",
        color=discord.Color.green()
    )
    embed.add_field(name="!dado [lados]", value="Rola um dado. Ex: `!dado 20`", inline=False)
    embed.add_field(name="!moeda", value="Joga uma moeda (cara ou coroa)", inline=False)
    embed.add_field(name="!userinfo [@usuario]", value="Mostra info de um usuário", inline=False)
    embed.add_field(name="!limpar [quantidade]", value="Apaga mensagens (requer permissão)", inline=False)
    embed.add_field(name="!enquete [pergunta]", value="Cria uma enquete com ✅ e ❌", inline=False)
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
    embed.add_field(name="/categoria criar", value="Cria uma categoria de banners (admin)", inline=False)
    embed.add_field(name="/categoria deletar", value="Deleta uma categoria e seus banners (admin)", inline=False)
    embed.add_field(name="/categoria lista", value="Lista todas as categorias", inline=False)
    embed.add_field(name="/banner deletar", value="Deleta um banner da loja (admin)", inline=False)
    embed.add_field(name="/editar tipo nome", value="Edita um produto (banner ou conquista)", inline=False)
    embed.add_field(name="/rotacao ver", value="Mostra os banners da rotação atual", inline=False)
    embed.add_field(name="/rotacao forcar", value="Força uma nova rotação (admin)", inline=False)
    await ctx.send(embed=embed)

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
    con = sqlite3.connect("/data/jogadorbot.db")
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
    os.makedirs("/data/banners", exist_ok=True)
    arquivo_path = f"/data/banners/{nome.replace(' ', '_')}.png"
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
    con = sqlite3.connect("/data/jogadorbot.db")
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

categoria_group = app_commands.Group(name="categoria", description="Gerenciamento de categorias de banners")

@categoria_group.command(name="criar", description="Cria uma nova categoria de banners")
@app_commands.describe(nome="Nome da categoria", emoji="Emoji da categoria")
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def categoria_criar(interaction: discord.Interaction, nome: str, emoji: str):
    con = sqlite3.connect("/data/jogadorbot.db")
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
    con = sqlite3.connect("/data/jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id FROM categorias_banner WHERE LOWER(nome) = LOWER(?)", (nome,))
    resultado = cur.fetchone()
    if not resultado:
        await interaction.response.send_message(f"❌ Categoria **{nome}** não encontrada.", ephemeral=True)
        con.close()
        return
    cat_id = resultado[0]
    cur.execute("SELECT id FROM banners WHERE categoria_id = ?", (cat_id,))
    banner_ids = [row[0] for row in cur.fetchall()]
    for bid in banner_ids:
        cur.execute("DELETE FROM banners_usuarios WHERE banner_id = ?", (bid,))
        cur.execute("DELETE FROM banner_ativo WHERE banner_id = ?", (bid,))
    cur.execute("DELETE FROM banners WHERE categoria_id = ?", (cat_id,))
    cur.execute("DELETE FROM categorias_banner WHERE id = ?", (cat_id,))
    con.commit()
    con.close()
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

    con = sqlite3.connect("/data/jogadorbot.db")
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
        novo_arquivo = f"/data/banners/{(novo_nome or nome).replace(' ', '_')}.png"
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
        con = sqlite3.connect("/data/jogadorbot.db")
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

bot.tree.add_command(rotacao_group)

bot.tree.add_command(categoria_group)

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
