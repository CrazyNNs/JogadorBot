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
        "salario_min": 1200,
        "salario_max": 1400,
        "level_necessario": 0,
        "emoji": "<:GariIcon:1525380207907704914>",
        "descricao": "Mantém as ruas limpas da cidade.",
        "acoes": [
            "Você varreu as ruas do centro e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você recolheu o lixo do bairro e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você limpou a praça principal e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
        ]
    },
    "Fotografo": {
        "salario_min": 1600,
        "salario_max": 1800,
        "level_necessario": 5,
        "emoji": "<:FotografoIcon:1525381107867193354>",
        "descricao": "Registra momentos especiais com sua câmera.",
        "acoes": [
            "Você fotografou um casamento e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você fez um ensaio fotográfico e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você fotografou um evento corporativo e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
        ]
    },
    "Barman": {
        "salario_min": 1900,
        "salario_max": 2200,
        "level_necessario": 10,
        "emoji": "<:BarmanIcon:1525381712387772597>",
        "descricao": "Prepara drinks e anima o bar todas as noites.",
        "acoes": [
            "Você preparou drinks a noite toda e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você atendeu uma festa VIP no bar e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você criou um novo drink especial e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
        ]
    },
    "Motorista Particular": {
        "salario_min": 2500,
        "salario_max": 2800,
        "level_necessario": 15,
        "emoji": "<:MotoristaParticularIcon:1527099360331038790>",
        "descricao": "Dirige por toda cidade e deixa o seu cliente no destino desejado.",
        "acoes": [
            "Você dirigiu ao shooping e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você deixou seu cliente em casa e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
            "Você passeou de carro com o cliente e ganhou <:JoyensIcon:1525930784584634398>{salario}Joyens!",
        ]
    },
}
# ============================================================
# PETS — Dados sobre os pets
# ============================================================
PETS_DISPONIVEIS = {
    "Cachorro": {
        "emoji": "🐶",
        "descricao": "Leal e brincalhão, está sempre pronto para uma aventura ao seu lado.",
        "preco": 18000,
        "petisco_nome": "Biscoito canino",
        "petisco_preco": 180,
        "brinquedo_nome": "Bolinha",
        "brinquedo_preco": 900,
        "brinquedo_usos": 10,
    },
    "Gato": {
        "emoji": "🐱",
        "descricao": "Independente, mas sempre volta pro colo na hora do carinho.",
        "preco": 22000,
        "petisco_nome": "Whiskas",
        "petisco_preco": 220,
        "brinquedo_nome": "Rato de pelúcia",
        "brinquedo_preco": 1100,
        "brinquedo_usos": 10,
    },
    "Papagaio": {
        "emoji": "🦜",
        "descricao": "Curioso e falante, adora estar por perto e repetir o que ouve.",
        "preco": 28000,
        "petisco_nome": "Fatia de melancia",
        "petisco_preco": 160,
        "brinquedo_nome": "Balanço de pendurar",
        "brinquedo_preco": 1300,
        "brinquedo_usos": 10,
    },
}

SABONETE_NOME = "Sabonete"
SABONETE_PRECO = 700

LIMITE_PETS = 3
# ============================================================
# PETS — Dados sobre os pets
# ============================================================
# --- Decaimento (1 ponto a cada X minutos) ---
DECAIMENTO_FOME_MINUTOS = 15
DECAIMENTO_ENERGIA_MINUTOS = 20
DECAIMENTO_HIGIENE_MINUTOS = 30
DECAIMENTO_FELICIDADE_MINUTOS = 40

# --- Efeitos das ações ---
FOME_ALIMENTAR = 30
FELICIDADE_ALIMENTAR = 5

BRINCAR_FELICIDADE = 15
BRINCAR_ENERGIA = -8
BRINCAR_HIGIENE = -5
BRINCAR_FOME = -3
BRINCAR_ENERGIA_MINIMA = 10

BANHO_HIGIENE = 100
BANHO_FELICIDADE = 5

DORMIR_DURACAO_HORAS = 2
# ============================================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ============================================================
# MISSÕES SEMANAIS — Edite os valores para ajustar dificuldade
# ============================================================
def semana_atual():
    """Retorna a semana atual no formato ANO-SEMANA."""
    hoje = datetime.date.today()
    return f"{hoje.isocalendar()[0]}-{hoje.isocalendar()[1]}"

MISSOES_SEMANAIS = [
    {
        "id": "trabalhar_semana",
        "nome": "💼 Trabalhador da Semana",
        "descricao": "Use !trabalhar 10 vezes nessa semana.",
        "condicao": "trabalhar_semana",
        "meta": 10,
        "tipo_recompensa": "joyens",
        "quantidade_recompensa": 1500,
    },
    {
        "id": "apostar_semana",
        "nome": "🎰 Apostador da Semana",
        "descricao": "Use !apostar 7 vezes nessa semana.",
        "condicao": "apostar_semana",
        "meta": 7,
        "tipo_recompensa": "joyens",
        "quantidade_recompensa": 800,
    },
    {
        "id": "diario_semana",
        "nome": "📅 Fiel ao Diário",
        "descricao": "Use !diario 5 vezes nessa semana.",
        "condicao": "diario_semana",
        "meta": 5,
        "tipo_recompensa": "joyens",
        "quantidade_recompensa": 600,
    },
    {
        "id": "diario_seguidos_semana",
        "nome": "🔥 Sequência Perfeita",
        "descricao": "Use !diario 7 dias seguidos.",
        "condicao": "diario_seguidos",
        "meta": 7,
        "tipo_recompensa": "xp",
        "quantidade_recompensa": 500,
    },
    {
        "id": "joyens_acumulados_semana",
        "nome": "💰 Acumulador",
        "descricao": "Acumule 10.000 Joyens nessa semana.",
        "condicao": "joyens_acumulados",
        "meta": 10000,
        "tipo_recompensa": "xp",
        "quantidade_recompensa": 300,
    },
    {
        "id": "msg_semana",
        "nome": "💬 Comunicativo",
        "descricao": "Envie 100 mensagens nessa semana.",
        "condicao": "msg_semana",
        "meta": 100,
        "tipo_recompensa": "joyens",
        "quantidade_recompensa": 500,
    },
    {
        "id": "call_semana",
        "nome": "🎙️ Presença em Call",
        "descricao": "Fique 60 minutos em call nessa semana.",
        "condicao": "call_semana",
        "meta": 60,
        "tipo_recompensa": "joyens",
        "quantidade_recompensa": 700,
    },
]

# ============================================================
# ITENS DE MINERAÇÃO — Loja e sistema de mineração
# ============================================================
ITENS_MINERACAO = {
    "Picareta": {
        "emoji": "⛏️",
        "subcategoria": "Ferramentas",
        "preco": 1000,
        "descricao": "Necessária para minerar. Aguenta 10 usos.",
        "usos": 10,
    },
    "Dinamite": {
        "emoji": "🧨",
        "subcategoria": "Ferramentas",
        "preco": 30000,
        "descricao": "Minera instantaneamente. 10% de chance de falhar.",
    },
    "Capacete": {
        "emoji": "🪖",
        "subcategoria": "Equipamento",
        "preco": 2500,
        "descricao": "Aumenta o HP máximo em 30 pontos.",
    },
    "Marmita": {
        "emoji": "🍱",
        "subcategoria": "Consumíveis",
        "preco": 500,
        "descricao": "Recupera 20 de HP.",
    },
    "Pimenta": {
        "emoji": "🌶️",
        "subcategoria": "Consumíveis",
        "preco": 700,
        "descricao": "Aumenta o dano de ataque em 30%.",
    },
}

SUBCATEGORIAS_MINERACAO = ["Ferramentas", "Equipamento", "Consumíveis"]
SUBCATEGORIAS_EMOJI = {"Ferramentas": "⚒️", "Equipamento": "🛡️", "Consumíveis": "☕"}

MINERIOS = {
    "Carvão":   {"min": 20, "max": 30, "chance": 0.50, "preco": 10},
    "Cobre":    {"min": 10, "max": 25, "chance": 0.40, "preco": 10},
    "Ferro":    {"min": 5,  "max": 10, "chance": 0.35, "preco": 10},
    "Ouro":     {"min": 3,  "max": 5,  "chance": 0.20, "preco": 10},
    "Diamante": {"min": 1,  "max": 3,  "chance": 0.05, "preco": 10},
}

MONSTROS = {
    "Morcego": {"hp": 30, "dano": 5, "imagem": "atkmorcego1.png", "mensagem": "🦇 Um morcego surge das sombras e ataca!"},
    "Slime":   {"hp": 50, "dano": 9, "imagem": "atkslime1.png", "mensagem": "🟢 Um slime pulou em sua direção!"},
    "Cobra":   {"hp": 60, "dano": 13, "imagem": "atkcobra1.png", "mensagem": "🐍 Uma cobra venenosa ataca do nada!"},
}

MINERACAO_ATIVAS = set()  # IDs de usuários minerando no momento

HP_MAXIMO_BASE = 100
HP_BONUS_CAPACETE = 30
DANO_BASE_MIN = 15
DANO_BASE_MAX = 20
BONUS_DANO_PIMENTA = 0.30

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

    # Rewards
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            tipo_recompensa TEXT NOT NULL,
            quantidade_recompensa TEXT NOT NULL,
            condicoes TEXT NOT NULL,
            repetivel INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rewards_usuarios (
            usuario_id TEXT NOT NULL,
            reward_id INTEGER NOT NULL,
            completado_em TEXT,
            PRIMARY KEY (usuario_id, reward_id)
        )
    """)

    # Missões semanais
    cur.execute("""
        CREATE TABLE IF NOT EXISTS missoes_progresso (
            usuario_id TEXT NOT NULL,
            missao_id TEXT NOT NULL,
            progresso INTEGER DEFAULT 0,
            completada INTEGER DEFAULT 0,
            semana TEXT NOT NULL,
            PRIMARY KEY (usuario_id, missao_id, semana)
        )
    """)

    # Contadores gerais (mensagens, calls, etc)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contadores_usuarios (
            usuario_id TEXT PRIMARY KEY,
            msg_semana INTEGER DEFAULT 0,
            msg_total INTEGER DEFAULT 0,
            call_semana INTEGER DEFAULT 0,
            call_total INTEGER DEFAULT 0,
            call_inicio TEXT,
            apostar_semana INTEGER DEFAULT 0,
            apostar_total INTEGER DEFAULT 0,
            apostar_quantidade_semana INTEGER DEFAULT 0,
            apostar_quantidade_total INTEGER DEFAULT 0,
            diario_semana INTEGER DEFAULT 0,
            diario_total INTEGER DEFAULT 0,
            diario_seguidos INTEGER DEFAULT 0,
            diario_ultimo TEXT,
            trabalhar_semana INTEGER DEFAULT 0,
            trabalhar_total INTEGER DEFAULT 0,
            joyens_acumulados INTEGER DEFAULT 0
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS missoes_customizadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            condicoes TEXT NOT NULL,
            meta INTEGER,
            tipo_recompensa TEXT NOT NULL,
            quantidade_recompensa INTEGER NOT NULL,
            data_fim TEXT,
            aviso_enviado INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS missoes_customizadas_progresso (
            usuario_id TEXT NOT NULL,
            missao_id INTEGER NOT NULL,
            progresso INTEGER DEFAULT 0,
            completada INTEGER DEFAULT 0,
            completada_em TEXT,
            PRIMARY KEY (usuario_id, missao_id)
        )
    """)

    try:
        cur.execute("ALTER TABLE pets ADD COLUMN disponivel_adocao INTEGER NOT NULL DEFAULT 0")
    except:
        pass

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id TEXT NOT NULL,
            especie TEXT NOT NULL,
            nome TEXT NOT NULL,
            fome INTEGER NOT NULL DEFAULT 100,
            energia INTEGER NOT NULL DEFAULT 100,
            higiene INTEGER NOT NULL DEFAULT 100,
            felicidade INTEGER NOT NULL DEFAULT 100,
            dormindo_desde TEXT,
            dormindo_ate TEXT,
            energia_ao_dormir INTEGER,
            criado_em TEXT NOT NULL,
            ultima_atualizacao TEXT NOT NULL,
            disponivel_adocao INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets_petiscos (
            usuario_id TEXT NOT NULL,
            tipo TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (usuario_id, tipo)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets_brinquedos (
            usuario_id TEXT NOT NULL,
            tipo TEXT NOT NULL,
            usos_restantes INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (usuario_id, tipo)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets_sabonete (
            usuario_id TEXT PRIMARY KEY,
            quantidade INTEGER NOT NULL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuario_stats (
            usuario_id TEXT PRIMARY KEY,
            hp_atual INTEGER DEFAULT 100,
            tem_capacete INTEGER DEFAULT 0,
            picareta_usos INTEGER DEFAULT 0,
            joyogens INTEGER DEFAULT 0
        )
    """)
    try:
        cur.execute("ALTER TABLE usuario_stats ADD COLUMN ultimo_minerar TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE usuario_stats ADD COLUMN penalidade_ate TEXT")
    except:
        pass
    try:
        cur.execute("ALTER TABLE usuario_stats ADD COLUMN pimenta_ativa INTEGER DEFAULT 0")
    except:
        pass
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS itens_usuarios_mineracao (
            usuario_id TEXT NOT NULL,
            item_nome TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            PRIMARY KEY (usuario_id, item_nome)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS minerios_usuarios (
            usuario_id TEXT NOT NULL,
            minerio TEXT NOT NULL,
            quantidade INTEGER DEFAULT 0,
            PRIMARY KEY (usuario_id, minerio)
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
    # Atualiza o acumulador semanal de Joyens
    garantir_contador(usuario_id)
    con2 = sqlite3.connect("jogadorbot.db")
    cur2 = con2.cursor()
    cur2.execute("""
        UPDATE contadores_usuarios SET joyens_acumulados = joyens_acumulados + ?
        WHERE usuario_id = ?
    """, (quantidade, str(usuario_id)))
    con2.commit()
    con2.close()

def remover_joyens(usuario_id, quantidade):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("UPDATE economia SET joyens = joyens - ? WHERE usuario_id = ?", (quantidade, str(usuario_id)))
    con.commit()
    con.close()

# ============================================================
# SISTEMA DE PETS E STATUS
def contar_pets(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM pets WHERE usuario_id = ? AND disponivel_adocao = 0", (str(usuario_id),))
    total = cur.fetchone()[0]
    con.close()
    return total

def listar_pets(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute(
        "SELECT id, especie, nome FROM pets WHERE usuario_id = ? AND disponivel_adocao = 0 ORDER BY id",
        (str(usuario_id),)
    )
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_petiscos_usuario(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT tipo, quantidade FROM pets_petiscos WHERE usuario_id = ? AND quantidade > 0", (str(usuario_id),))
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_brinquedos_usuario(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT tipo, usos_restantes FROM pets_brinquedos WHERE usuario_id = ? AND usos_restantes > 0", (str(usuario_id),))
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_sabonetes_usuario(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT quantidade FROM pets_sabonete WHERE usuario_id = ?", (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return resultado[0] if resultado else 0

def atualizar_stats_pet(pet_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT fome, energia, higiene, felicidade, dormindo_desde, dormindo_ate,
               energia_ao_dormir, ultima_atualizacao
        FROM pets WHERE id = ?
    """, (pet_id,))
    linha = cur.fetchone()
    if not linha:
        con.close()
        return

    fome, energia, higiene, felicidade, dormindo_desde, dormindo_ate, energia_ao_dormir, ultima_atualizacao = linha

    agora = datetime.datetime.now(FUSO_BR)
    ultima = datetime.datetime.fromisoformat(ultima_atualizacao)

    estava_dormindo = dormindo_ate is not None
    dormindo_ate_dt = datetime.datetime.fromisoformat(dormindo_ate) if dormindo_ate else None
    dormindo_desde_dt = datetime.datetime.fromisoformat(dormindo_desde) if dormindo_desde else None

    if estava_dormindo and agora < dormindo_ate_dt:
        duracao_total = (dormindo_ate_dt - dormindo_desde_dt).total_seconds()
        decorrido = (agora - dormindo_desde_dt).total_seconds()
        progresso = min(1.0, decorrido / duracao_total) if duracao_total > 0 else 1.0
        nova_energia = energia_ao_dormir + (100 - energia_ao_dormir) * progresso
        novo_dormindo_desde = dormindo_desde
        novo_dormindo_ate = dormindo_ate
        novo_energia_ao_dormir = energia_ao_dormir

    elif estava_dormindo and agora >= dormindo_ate_dt:
        minutos_desde_acordar = (agora - dormindo_ate_dt).total_seconds() / 60
        nova_energia = 100 - (minutos_desde_acordar / DECAIMENTO_ENERGIA_MINUTOS)
        novo_dormindo_desde = None
        novo_dormindo_ate = None
        novo_energia_ao_dormir = None

    else:
        minutos_passados_energia = (agora - ultima).total_seconds() / 60
        nova_energia = energia - (minutos_passados_energia / DECAIMENTO_ENERGIA_MINUTOS)
        novo_dormindo_desde = None
        novo_dormindo_ate = None
        novo_energia_ao_dormir = None

    minutos_passados = (agora - ultima).total_seconds() / 60
    nova_fome = fome - (minutos_passados / DECAIMENTO_FOME_MINUTOS)
    nova_higiene = higiene - (minutos_passados / DECAIMENTO_HIGIENE_MINUTOS)
    nova_felicidade = felicidade - (minutos_passados / DECAIMENTO_FELICIDADE_MINUTOS)

    nova_fome = max(0, min(100, round(nova_fome)))
    nova_higiene = max(0, min(100, round(nova_higiene)))
    nova_felicidade = max(0, min(100, round(nova_felicidade)))
    nova_energia = max(0, min(100, round(nova_energia)))

    cur.execute("""
        UPDATE pets SET fome = ?, energia = ?, higiene = ?, felicidade = ?,
                        dormindo_desde = ?, dormindo_ate = ?, energia_ao_dormir = ?,
                        ultima_atualizacao = ?
        WHERE id = ?
    """, (
        nova_fome, nova_energia, nova_higiene, nova_felicidade,
        novo_dormindo_desde, novo_dormindo_ate, novo_energia_ao_dormir,
        agora.isoformat(), pet_id
    ))
    con.commit()
    con.close()

def aplicar_efeito_pet(pet_id, fome=0, energia=0, higiene=0, felicidade=0):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT fome, energia, higiene, felicidade FROM pets WHERE id = ?", (pet_id,))
    resultado = cur.fetchone()
    if not resultado:
        con.close()
        return
    fome_atual, energia_atual, higiene_atual, felicidade_atual = resultado

    novo_fome = max(0, min(100, fome_atual + fome))
    novo_energia = max(0, min(100, energia_atual + energia))
    novo_higiene = max(0, min(100, higiene_atual + higiene))
    novo_felicidade = max(0, min(100, felicidade_atual + felicidade))

    agora = datetime.datetime.now(FUSO_BR).isoformat()
    cur.execute("""
        UPDATE pets SET fome = ?, energia = ?, higiene = ?, felicidade = ?, ultima_atualizacao = ?
        WHERE id = ?
    """, (novo_fome, novo_energia, novo_higiene, novo_felicidade, agora, pet_id))
    con.commit()
    con.close()

# ============================================================
# BANNER NA ROTAÇÃO DA LOJA
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

# ============================================================
# SISTEMA DE LEVEL UP
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

from discord.ext import tasks

# ============================================================
# TASKS DE VERIFICAÇÃO POR TEMPO
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
# FUNÇÕES AUXILIARES - Verificar Reset Semanal e Tempo em Call
# ============================================================

@tasks.loop(hours=1)
async def verificar_reset_semanal():
    """Reseta os contadores semanais toda segunda-feira às 00h."""
    agora = datetime.datetime.now()
    if agora.weekday() == 0 and agora.hour == 0:
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            UPDATE contadores_usuarios SET
                msg_semana = 0,
                call_semana = 0,
                apostar_semana = 0,
                apostar_quantidade_semana = 0,
                diario_semana = 0,
                trabalhar_semana = 0,
                joyens_acumulados = 0
        """)
        con.commit()
        con.close()

        canal = bot.get_channel(CANAL_NOTIFICACOES_ID)
        if canal:
            embed = discord.Embed(
                title="🔄 Novas Missões Semanais!",
                description="As missões da semana foram resetadas! Use `!missoes` para ver as novas missões.",
                color=discord.Color.purple()
            )
            await canal.send(embed=embed)

@bot.event
async def on_voice_state_update(member, before, after):
    """Monitora entrada e saída de calls para contar o tempo."""
    garantir_contador(member.id)
    agora = datetime.datetime.now().isoformat()
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    # Entrou em call
    if before.channel is None and after.channel is not None:
        cur.execute("UPDATE contadores_usuarios SET call_inicio = ? WHERE usuario_id = ?",
                    (agora, str(member.id)))
        con.commit()

    # Saiu de call
    elif before.channel is not None and after.channel is None:
        cur.execute("SELECT call_inicio FROM contadores_usuarios WHERE usuario_id = ?",
                    (str(member.id),))
        resultado = cur.fetchone()
        if resultado and resultado[0]:
            inicio = datetime.datetime.fromisoformat(resultado[0])
            minutos = int((datetime.datetime.now() - inicio).total_seconds() // 60)
            if minutos > 0:
                cur.execute("""
                    UPDATE contadores_usuarios SET
                        call_semana = call_semana + ?,
                        call_total = call_total + ?,
                        call_inicio = NULL
                    WHERE usuario_id = ?
                """, (minutos, minutos, str(member.id)))
                con.commit()
                await verificar_missoes_usuario(str(member.id))

    con.close()

# ============================================================
# FUNÇÕES AUXILIARES - Missões Customizadas Temporárias
# ============================================================
@tasks.loop(hours=1)
async def verificar_missoes_temporarias():
    """Avisa 6 horas antes do fim e remove missões expiradas."""
    agora = datetime.datetime.now()
    aviso_limite = (agora + datetime.timedelta(hours=6)).isoformat()
    agora_iso = agora.isoformat()

    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    # Avisa missões que expiram em 6 horas
    cur.execute("""
        SELECT id, nome, data_fim FROM missoes_customizadas
        WHERE tipo = 'temporaria'
        AND data_fim <= ?
        AND data_fim > ?
        AND aviso_enviado = 0
    """, (aviso_limite, agora_iso))
    para_avisar = cur.fetchall()

    canal = bot.get_channel(CANAL_NOTIFICACOES_ID)
    for mid, nome, data_fim in para_avisar:
        cur.execute("UPDATE missoes_customizadas SET aviso_enviado = 1 WHERE id = ?", (mid,))
        if canal:
            expira_dt = datetime.datetime.fromisoformat(data_fim)
            embed = discord.Embed(
                title="⚠️ Missão Expirando em Breve!",
                description=f"A missão **{nome}** expira em menos de 6 horas!",
                color=discord.Color.orange()
            )
            embed.add_field(name="Expira em", value=expira_dt.strftime("%d/%m/%Y às %H:%M"), inline=False)
            await canal.send(embed=embed)

    # Remove missões expiradas
    cur.execute("""
        DELETE FROM missoes_customizadas_progresso
        WHERE missao_id IN (
            SELECT id FROM missoes_customizadas
            WHERE tipo = 'temporaria' AND data_fim <= ?
        )
    """, (agora_iso,))
    cur.execute("""
        DELETE FROM missoes_customizadas WHERE tipo = 'temporaria' AND data_fim <= ?
    """, (agora_iso,))

    con.commit()
    con.close()

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
    diferenca = (ultimo + datetime.timedelta(minutes=30)) - agora
    if diferenca.total_seconds() <= 0:
        return 0
    minutos = int(diferenca.total_seconds() // 60)
    segundos = int(diferenca.total_seconds() % 60)
    return f"{minutos}m {segundos}s"

# ============================================================
# FUNÇÕES AUXILIARES - Mineração
# ============================================================
def garantir_stats(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("INSERT OR IGNORE INTO usuario_stats (usuario_id) VALUES (?)", (str(usuario_id),))
    con.commit()
    con.close()

def buscar_stats(usuario_id):
    garantir_stats(usuario_id)
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT hp_atual, tem_capacete, picareta_usos, joyogens, pimenta_ativa FROM usuario_stats WHERE usuario_id = ?",
                (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return {
        "hp_atual": resultado[0], "tem_capacete": resultado[1],
        "picareta_usos": resultado[2], "joyogens": resultado[3],
        "pimenta_ativa": resultado[4] if len(resultado) > 4 else 0
    }

def tempo_restante_minerar(usuario_id):
    """Retorna (pode_minerar, texto_tempo)."""
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT ultimo_minerar, penalidade_ate FROM usuario_stats WHERE usuario_id = ?", (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    con2 = sqlite3.connect("jogadorbot.db")
    cur2 = con2.cursor()
    cur2.execute("UPDATE usuario_stats SET pimenta_ativa = 0 WHERE usuario_id = ?", (str(self.usuario_id),))
    con2.commit()
    con2.close()
    if not resultado:
        return True, None
    ultimo_minerar, penalidade_ate = resultado
    agora = datetime.datetime.now()

    if penalidade_ate:
        penalidade_dt = datetime.datetime.fromisoformat(penalidade_ate)
        if agora < penalidade_dt:
            restante = penalidade_dt - agora
            minutos = int(restante.total_seconds() // 60) + 1
            return False, f"⏰ Você está penalizado! Pode minerar novamente em **{minutos} minuto(s)**."

    if ultimo_minerar:
        ultimo_dt = datetime.datetime.fromisoformat(ultimo_minerar)
        if (agora - ultimo_dt) < datetime.timedelta(minutes=10):
            restante = datetime.timedelta(minutes=10) - (agora - ultimo_dt)
            minutos = int(restante.total_seconds() // 60) + 1
            return False, f"⏰ Você precisa esperar mais **{minutos} minuto(s)** para minerar novamente."

    return True, None

def hp_maximo(usuario_id):
    stats = buscar_stats(usuario_id)
    return HP_MAXIMO_BASE + (HP_BONUS_CAPACETE if stats["tem_capacete"] else 0)

def atualizar_hp(usuario_id, novo_hp):
    garantir_stats(usuario_id)
    maximo = hp_maximo(usuario_id)
    novo_hp = max(0, min(novo_hp, maximo))
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("UPDATE usuario_stats SET hp_atual = ? WHERE usuario_id = ?", (novo_hp, str(usuario_id)))
    con.commit()
    con.close()
    return novo_hp

def adicionar_joyogens(usuario_id, quantidade):
    garantir_stats(usuario_id)
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("UPDATE usuario_stats SET joyogens = joyogens + ? WHERE usuario_id = ?", (quantidade, str(usuario_id)))
    con.commit()
    con.close()

def remover_joyogens(usuario_id, quantidade):
    garantir_stats(usuario_id)
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("UPDATE usuario_stats SET joyogens = MAX(0, joyogens - ?) WHERE usuario_id = ?", (quantidade, str(usuario_id)))
    con.commit()
    con.close()

def buscar_qtd_item_mineracao(usuario_id, item_nome):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT quantidade FROM itens_usuarios_mineracao WHERE usuario_id = ? AND item_nome = ?",
                (str(usuario_id), item_nome))
    resultado = cur.fetchone()
    con.close()
    return resultado[0] if resultado else 0

def adicionar_item_mineracao(usuario_id, item_nome, qtd=1):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO itens_usuarios_mineracao (usuario_id, item_nome, quantidade) VALUES (?, ?, ?)
        ON CONFLICT(usuario_id, item_nome) DO UPDATE SET quantidade = quantidade + ?
    """, (str(usuario_id), item_nome, qtd, qtd))
    con.commit()
    con.close()

def remover_item_mineracao(usuario_id, item_nome, qtd=1):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        UPDATE itens_usuarios_mineracao SET quantidade = MAX(0, quantidade - ?)
        WHERE usuario_id = ? AND item_nome = ?
    """, (qtd, str(usuario_id), item_nome))
    con.commit()
    con.close()

def comprar_item_mineracao(usuario_id, item_nome, preco_customizado=None):
    """Compra um item de mineração. Retorna (sucesso, mensagem)."""
    item = ITENS_MINERACAO.get(item_nome)
    if not item:
        return False, "Item não encontrado."

    preco = preco_customizado if preco_customizado else item["preco"]
    saldo = buscar_joyens(usuario_id)
    if saldo < preco:
        return False, f"Joyens insuficientes! Você tem {saldo} e precisa de {preco}."

    remover_joyens(usuario_id, preco)
    garantir_stats(usuario_id)

    if item_nome == "Picareta":
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("UPDATE usuario_stats SET picareta_usos = picareta_usos + ? WHERE usuario_id = ?",
                    (item["usos"], str(usuario_id)))
        con.commit()
        con.close()
    elif item_nome == "Capacete":
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("UPDATE usuario_stats SET tem_capacete = 1 WHERE usuario_id = ?", (str(usuario_id),))
        con.commit()
        con.close()
    else:
        adicionar_item_mineracao(usuario_id, item_nome, 1)

    return True, f"**{item_nome}** comprado com sucesso por {preco} Joyens!"

def buscar_minerios_usuario(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT minerio, quantidade FROM minerios_usuarios WHERE usuario_id = ? AND quantidade > 0",
                (str(usuario_id),))
    resultado = cur.fetchall()
    con.close()
    return resultado

def adicionar_minerio(usuario_id, minerio, qtd):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO minerios_usuarios (usuario_id, minerio, quantidade) VALUES (?, ?, ?)
        ON CONFLICT(usuario_id, minerio) DO UPDATE SET quantidade = quantidade + ?
    """, (str(usuario_id), minerio, qtd, qtd))
    con.commit()
    con.close()

# ============================================================
# FUNÇÕES AUXILIARES - Missões Semanais
# ============================================================

def garantir_contador(usuario_id):
    """Garante que o usuário tem uma linha na tabela de contadores."""
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO contadores_usuarios (usuario_id) VALUES (?)
    """, (str(usuario_id),))
    con.commit()
    con.close()

def buscar_contador(usuario_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM contadores_usuarios WHERE usuario_id = ?", (str(usuario_id),))
    resultado = cur.fetchone()
    con.close()
    return resultado

def atualizar_contador(usuario_id, campo, valor=1, absoluto=False):
    """Incrementa ou define um campo do contador do usuário."""
    garantir_contador(usuario_id)
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    if absoluto:
        cur.execute(f"UPDATE contadores_usuarios SET {campo} = ? WHERE usuario_id = ?",
                    (valor, str(usuario_id)))
    else:
        cur.execute(f"UPDATE contadores_usuarios SET {campo} = {campo} + ? WHERE usuario_id = ?",
                    (valor, str(usuario_id)))
    con.commit()
    con.close()

def buscar_progresso_missao(usuario_id, missao_id):
    semana = semana_atual()
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT progresso, completada FROM missoes_progresso
        WHERE usuario_id = ? AND missao_id = ? AND semana = ?
    """, (str(usuario_id), missao_id, semana))
    resultado = cur.fetchone()
    con.close()
    return resultado if resultado else (0, 0)

async def verificar_missoes_usuario(usuario_id, ctx_ou_channel=None):
    """Verifica e atualiza o progresso de todas as missões do usuário."""
    garantir_contador(usuario_id)
    semana = semana_atual()
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM contadores_usuarios WHERE usuario_id = ?", (str(usuario_id),))
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    con.close()

    if not row:
        return

    dados = dict(zip(cols, row))
    canal = bot.get_channel(CANAL_NOTIFICACOES_ID)

    for missao in MISSOES_SEMANAIS:
        progresso_atual, completada = buscar_progresso_missao(usuario_id, missao["id"])
        if completada:
            continue

        condicao = missao["condicao"]
        valor_atual = dados.get(condicao, 0) or 0
        meta = missao["meta"]

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO missoes_progresso (usuario_id, missao_id, progresso, completada, semana)
            VALUES (?, ?, ?, 0, ?)
            ON CONFLICT(usuario_id, missao_id, semana) DO UPDATE SET progresso = ?
        """, (str(usuario_id), missao["id"], valor_atual, semana, valor_atual))
        con.commit()
        con.close()

        if valor_atual >= meta:
            # Marca como completada
            con = sqlite3.connect("jogadorbot.db")
            cur = con.cursor()
            cur.execute("""
                UPDATE missoes_progresso SET completada = 1
                WHERE usuario_id = ? AND missao_id = ? AND semana = ?
            """, (str(usuario_id), missao["id"], semana))
            con.commit()
            con.close()

            # Dá a recompensa
            tipo = missao["tipo_recompensa"]
            qtd = missao["quantidade_recompensa"]
            if tipo == "joyens":
                adicionar_joyens(usuario_id, qtd)
                recompensa_texto = f"**+{qtd} Joyens**"
            elif tipo == "xp":
                canal_ctx = ctx_ou_channel or canal
                try:
                    await adicionar_xp(str(usuario_id), qtd, canal_ctx)
                except Exception as e:
                    print(f"Erro ao dar XP de missão: {e}")
                recompensa_texto = f"**+{qtd} XP**"

            # Notifica no canal
            if canal:
                try:
                    usuario = await bot.fetch_user(int(usuario_id))
                    embed = discord.Embed(
                        title="✅ Missão Concluída!",
                        description=f"{usuario.mention} completou a missão **{missao['nome']}**!",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Recompensa", value=recompensa_texto, inline=True)
                    await canal.send(embed=embed)
                    await verificar_missoes_customizadas_usuario(usuario_id, ctx_ou_channel)
                except:
                    pass

# ============================================================
# FUNÇÕES AUXILIARES - Missões Customizadas
# ============================================================
def buscar_missoes_customizadas(tipo=None):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    agora = datetime.datetime.now().isoformat()
    if tipo:
        if tipo == "temporaria":
            cur.execute("""
                SELECT * FROM missoes_customizadas
                WHERE tipo = ? AND (data_fim IS NULL OR data_fim > ?)
                ORDER BY id
            """, (tipo, agora))
        else:
            cur.execute("SELECT * FROM missoes_customizadas WHERE tipo = ? ORDER BY id", (tipo,))
    else:
        cur.execute("SELECT * FROM missoes_customizadas ORDER BY tipo, id")
    resultado = cur.fetchall()
    con.close()
    return resultado

def buscar_progresso_missao_customizada(usuario_id, missao_id):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        SELECT progresso, completada FROM missoes_customizadas_progresso
        WHERE usuario_id = ? AND missao_id = ?
    """, (str(usuario_id), missao_id))
    resultado = cur.fetchone()
    con.close()
    return resultado if resultado else (0, 0)

async def verificar_missoes_customizadas_usuario(usuario_id, ctx_ou_channel=None):
    """Verifica missões customizadas com condições automáticas."""
    garantir_contador(usuario_id)
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM contadores_usuarios WHERE usuario_id = ?", (str(usuario_id),))
    cols = [desc[0] for desc in cur.description]
    row = cur.fetchone()
    con.close()

    if not row:
        return

    dados = dict(zip(cols, row))
    agora = datetime.datetime.now().isoformat()
    canal = bot.get_channel(CANAL_NOTIFICACOES_ID)
    missoes = buscar_missoes_customizadas()

    for missao in missoes:
        mid, nome, descricao, tipo, condicoes, meta, tipo_recompensa, qtd_recompensa, data_fim, _ = missao

        # Pula missões expiradas
        if data_fim and data_fim < agora:
            continue

        progresso_atual, completada = buscar_progresso_missao_customizada(usuario_id, mid)
        if completada:
            continue

        # Pula missões Null (precisam de aprovação manual)
        if condicoes.strip().lower() == "null":
            continue

        # Calcula progresso combinado
        lista_condicoes = [c.strip() for c in condicoes.split(",")]
        todos_completos = True
        progresso_min = float("inf")

        for cond in lista_condicoes:
            if ":" not in cond:
                continue
            campo, valor_meta = cond.split(":", 1)
            valor_meta = int(valor_meta)
            valor_atual = dados.get(campo, 0) or 0
            progresso_percentual = min(valor_atual, valor_meta)
            progresso_min = min(progresso_min, progresso_percentual / valor_meta * (meta or valor_meta))
            if valor_atual < valor_meta:
                todos_completos = False

        novo_progresso = int(progresso_min) if progresso_min != float("inf") else 0

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO missoes_customizadas_progresso (usuario_id, missao_id, progresso)
            VALUES (?, ?, ?)
            ON CONFLICT(usuario_id, missao_id) DO UPDATE SET progresso = ?
        """, (str(usuario_id), mid, novo_progresso, novo_progresso))
        con.commit()
        con.close()

        if todos_completos:
            await concluir_missao_customizada(usuario_id, mid, nome, tipo_recompensa, qtd_recompensa, canal, ctx_ou_channel)

async def concluir_missao_customizada(usuario_id, missao_id, nome, tipo_recompensa, qtd_recompensa, canal=None, ctx_ou_channel=None):
    """Marca uma missão customizada como completada e dá a recompensa."""
    agora = datetime.datetime.now().isoformat()
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        INSERT INTO missoes_customizadas_progresso (usuario_id, missao_id, completada, completada_em)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(usuario_id, missao_id) DO UPDATE SET completada = 1, completada_em = ?
    """, (str(usuario_id), missao_id, agora, agora))
    con.commit()
    con.close()

    if tipo_recompensa == "joyens":
        adicionar_joyens(usuario_id, qtd_recompensa)
        recompensa_texto = f"**+{qtd_recompensa} Joyens**"
    elif tipo_recompensa == "xp":
        canal_ctx = ctx_ou_channel or canal
        if canal_ctx:
            await adicionar_xp(str(usuario_id), qtd_recompensa, canal_ctx)
        recompensa_texto = f"**+{qtd_recompensa} XP**"
    else:
        recompensa_texto = tipo_recompensa

    if canal:
        try:
            usuario = await bot.fetch_user(int(usuario_id))
            embed = discord.Embed(
                title="✅ Missão Concluída!",
                description=f"{usuario.mention} completou a missão **{nome}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Recompensa", value=recompensa_texto, inline=True)
            await canal.send(embed=embed)
        except:
            pass

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
        embed2.add_field(name="<:BolsaJoyensIcon:1525729605724405781> Economia", value=f"> **Joyens:** ``{joyens}``", inline=False)
        embed2.add_field(
            name="📊 Outros",
            value=f"> **Conquistas:** ``{len(conquistas)}``\n> **Banners:** ``{total_banners}``",
            inline=False
        )

        emprego_dados = buscar_emprego(membro.id)
        if emprego_dados:
            emprego_nome, vezes_trabalhadas, _ = emprego_dados
            emprego_info = EMPREGOS.get(emprego_nome)
            emoji_emp = emprego_info["emoji"] if emprego_info else "<:EmpregosIcon:1525710982364532890>"
            embed2.add_field(
                name="<:EmpregosIcon:1525710982364532890> Emprego",
                value=f"{emoji_emp} **{emprego_nome}** | {vezes_trabalhadas} vez(es) trabalhadas",
                inline=False
            )
        else:
            embed2.add_field(name="<:EmpregosIcon:1525710982364532890> Emprego", value="Desempregado — use `!empregos`", inline=False)

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

    @discord.ui.button(label="🐾 Petshop", style=discord.ButtonStyle.primary)
    async def abrir_petshop(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewMenuPetshop(self.usuario_id)
        embed = gerar_embed_petshop(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

    @discord.ui.button(label="⛏️ Mineração", style=discord.ButtonStyle.primary)
    async def abrir_mineracao(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewLojaMineracao(self.usuario_id)
        embed = discord.Embed(
            title="⛏️ Loja de Mineração",
            description="Escolha uma subcategoria:",
            color=discord.Color.dark_gold()
        )
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])

# ============================================================
# VIEW (BOTÕES) - Mineração
# ============================================================
class ViewLojaMineracao(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        for sub in SUBCATEGORIAS_MINERACAO:
            emoji = SUBCATEGORIAS_EMOJI[sub]
            botao = discord.ui.Button(label=sub, emoji=emoji, style=discord.ButtonStyle.primary)
            async def callback(interaction, subcategoria=sub):
                view = ViewItensMineracao(self.usuario_id, subcategoria)
                embed = view.gerar_embed()
                await interaction.response.edit_message(embed=embed, view=view)
            botao.callback = callback
            self.add_item(botao)

        btn_voltar = discord.ui.Button(label="🔙 Loja", style=discord.ButtonStyle.danger, row=1)
        async def voltar_callback(interaction):
            embed = discord.Embed(
                title="🏪 Loja do JogadorBot",
                description="Bem-vindo à loja! Use seus Joyens para comprar itens incríveis.\nEscolha uma categoria:",
                color=discord.Color.gold()
            )
            embed.add_field(name="🖼️ Banners", value="Banners exclusivos por tempo limitado!", inline=False)
            embed.add_field(name="⛏️ Mineração", value="Ferramentas, equipamentos e consumíveis!", inline=False)
            embed.set_footer(text=f"Seu saldo: {buscar_joyens(self.usuario_id)} Joyens")
            view = ViewMenuLoja(self.usuario_id)
            await interaction.response.edit_message(embed=embed, view=view, attachments=[])
        btn_voltar.callback = voltar_callback
        self.add_item(btn_voltar)


class ViewItensMineracao(discord.ui.View):
    def __init__(self, usuario_id, subcategoria):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.subcategoria = subcategoria

        itens = {nome: dados for nome, dados in ITENS_MINERACAO.items() if dados["subcategoria"] == subcategoria}
        for nome, dados in itens.items():
            botao = discord.ui.Button(label=f"Comprar {nome}", emoji=dados["emoji"], style=discord.ButtonStyle.success)
            async def callback(interaction, item_nome=nome):
                sucesso, msg = comprar_item_mineracao(interaction.user.id, item_nome)
                if sucesso:
                    await interaction.response.send_message(f"✅ {msg}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
            botao.callback = callback
            self.add_item(botao)

        btn_voltar = discord.ui.Button(label="🔙 Categorias", style=discord.ButtonStyle.danger, row=1)
        async def voltar_callback(interaction):
            view = ViewLojaMineracao(self.usuario_id)
            embed = discord.Embed(
                title="⛏️ Loja de Mineração",
                description="Escolha uma subcategoria:",
                color=discord.Color.dark_gold()
            )
            await interaction.response.edit_message(embed=embed, view=view)
        btn_voltar.callback = voltar_callback
        self.add_item(btn_voltar)

    def gerar_embed(self):
        emoji_sub = SUBCATEGORIAS_EMOJI[self.subcategoria]
        embed = discord.Embed(
            title=f"{emoji_sub} {self.subcategoria}",
            color=discord.Color.dark_gold()
        )
        itens = {nome: dados for nome, dados in ITENS_MINERACAO.items() if dados["subcategoria"] == self.subcategoria}
        for nome, dados in itens.items():
            embed.add_field(
                name=f"{dados['emoji']} {nome} — {dados['preco']} Joyens",
                value=dados["descricao"],
                inline=False
            )
        return embed

# ============================================================
# VIEW (BOTÕES) - Inventário Geral
# ============================================================
class ViewInventarioMenu(ui.LayoutView):
    def __init__(self, usuario: discord.Member):
        super().__init__(timeout=120)
        self.usuario = usuario
        self.montar()

    def montar(self):
        self.clear_items()
        container = ui.Container()
        container.accent_color = discord.Colour.blurple()
        container.add_item(ui.TextDisplay(f"### 🎒 Inventário de {self.usuario.display_name}\n-# Escolha uma categoria abaixo."))
        container.add_item(ui.Separator())

        linha = ui.ActionRow()
        categorias = [
            ("🖼️ Banners", "banner"),
            ("⚒️ Ferramentas", "ferramenta"),
            ("🛡️ Equipamento", "equipamento"),
            ("☕ Consumíveis", "consumivel"),
            ("💎 Minérios", "minerio"),
        ]
        for label, chave in categorias:
            botao = ui.Button(label=label, style=discord.ButtonStyle.primary)
            async def cb(interaction, categoria=chave):
                if interaction.user.id != self.usuario.id:
                    await interaction.response.send_message("Esse inventário não é seu!", ephemeral=True)
                    return
                view = ViewInventarioCategoria(self.usuario, categoria, self)
                await interaction.response.edit_message(view=view)
            botao.callback = cb
            linha.add_item(botao)
        container.add_item(linha)
        self.add_item(container)


class ViewInventarioCategoria(ui.LayoutView):
    def __init__(self, usuario: discord.Member, categoria: str, view_menu: ViewInventarioMenu):
        super().__init__(timeout=120)
        self.usuario = usuario
        self.categoria = categoria
        self.view_menu = view_menu
        self.montar()

    def montar(self):
        self.clear_items()
        titulos = {
            "banner": "🖼️ Banners", "ferramenta": "⚒️ Ferramentas",
            "equipamento": "🛡️ Equipamento", "consumivel": "☕ Consumíveis",
            "minerio": "💎 Minérios",
        }
        container = ui.Container()
        container.accent_color = discord.Colour.blurple()
        container.add_item(ui.TextDisplay(f"### {titulos[self.categoria]}\n-# {self.usuario.display_name}"))
        container.add_item(ui.Separator())

        if self.categoria == "banner":
            con = sqlite3.connect("jogadorbot.db")
            cur = con.cursor()
            cur.execute("""
                SELECT b.nome FROM banners_usuarios bu JOIN banners b ON bu.banner_id = b.id
                WHERE bu.usuario_id = ? ORDER BY b.nome
            """, (str(self.usuario.id),))
            banners = [r[0] for r in cur.fetchall()]
            con.close()
            container.add_item(ui.TextDisplay("\n".join(f"- {n}" for n in banners) if banners else "Você não possui nenhum banner."))

        elif self.categoria == "ferramenta":
            stats = buscar_stats(self.usuario.id)
            dinamite_qtd = buscar_qtd_item_mineracao(self.usuario.id, "Dinamite")
            container.add_item(ui.TextDisplay(
                f"⛏️ **Picareta** — {stats['picareta_usos']} uso(s) restante(s)\n"
                f"🧨 **Dinamite** — {dinamite_qtd} unidade(s)"
            ))

        elif self.categoria == "equipamento":
            stats = buscar_stats(self.usuario.id)
            texto = "🪖 **Capacete** — " + ("Equipado ✅" if stats["tem_capacete"] else "Não possui ❌")
            container.add_item(ui.TextDisplay(texto))

        elif self.categoria == "consumivel":
            marmita_qtd = buscar_qtd_item_mineracao(self.usuario.id, "Marmita")
            pimenta_qtd = buscar_qtd_item_mineracao(self.usuario.id, "Pimenta")
            container.add_item(ui.TextDisplay(
                f"🍱 **Marmita** — {marmita_qtd} unidade(s)\n"
                f"🌶️ **Pimenta** — {pimenta_qtd} unidade(s)"
            ))

        elif self.categoria == "minerio":
            minerios = buscar_minerios_usuario(self.usuario.id)
            container.add_item(ui.TextDisplay(
                "\n".join(f"- {n}: {q}" for n, q in minerios) if minerios else "Você não possui nenhum minério."
            ))

        btn_voltar = ui.Button(label="🔙 Voltar", style=discord.ButtonStyle.danger)
        async def voltar_cb(interaction):
            self.view_menu.montar()
            await interaction.response.edit_message(view=self.view_menu)
        btn_voltar.callback = voltar_cb
        linha_voltar = ui.ActionRow()
        linha_voltar.add_item(btn_voltar)
        container.add_item(linha_voltar)

        self.add_item(container)
# ============================================================
# VIEW (BOTÕES) - Mineração - Tela inicial
# ============================================================
class ViewConsumiveis(ui.LayoutView):
    def __init__(self, usuario_id, view_inicio):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.view_inicio = view_inicio
        self.montar()

    def montar(self):
        self.clear_items()
        container = ui.Container()
        container.accent_color = discord.Colour.green()
        container.add_item(ui.TextDisplay("### ☕ Consumíveis\nEscolha um item para usar:"))
        container.add_item(ui.Separator())

        stats = buscar_stats(self.usuario_id)
        marmita_qtd = buscar_qtd_item_mineracao(self.usuario_id, "Marmita")
        pimenta_qtd = buscar_qtd_item_mineracao(self.usuario_id, "Pimenta")

        container.add_item(ui.TextDisplay(
            f"🍱 **Marmita** ({marmita_qtd}x)\n-# Recupera 20 de HP."
        ))
        linha_marmita = ui.ActionRow()
        btn_marmita = ui.Button(label="Usar Marmita", style=discord.ButtonStyle.success, disabled=marmita_qtd <= 0)

        async def usar_marmita(interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message("Isso não é seu!", ephemeral=True)
                return
            if buscar_qtd_item_mineracao(self.usuario_id, "Marmita") <= 0:
                await interaction.response.send_message("Você não tem mais marmitas!", ephemeral=True)
                return
            remover_item_mineracao(self.usuario_id, "Marmita", 1)
            stats_atual = buscar_stats(self.usuario_id)
            novo_hp = atualizar_hp(self.usuario_id, stats_atual["hp_atual"] + 20)
            self.montar()
            self.view_inicio.montar()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"✅ Você comeu uma marmita e recuperou HP! HP atual: {novo_hp}/{hp_maximo(self.usuario_id)}", ephemeral=True)

        btn_marmita.callback = usar_marmita
        linha_marmita.add_item(btn_marmita)
        container.add_item(linha_marmita)
        container.add_item(ui.Separator())

        pimenta_status = "🔥 Ativa para a próxima mineração!" if stats["pimenta_ativa"] else "Inativa"
        container.add_item(ui.TextDisplay(
            f"🌶️ **Pimenta** ({pimenta_qtd}x)\n-# Aumenta o dano de ataque em 30% na próxima mineração.\n-# Status: {pimenta_status}"
        ))
        linha_pimenta = ui.ActionRow()
        btn_pimenta = ui.Button(label="Usar Pimenta", style=discord.ButtonStyle.success,
                                 disabled=pimenta_qtd <= 0 or stats["pimenta_ativa"] == 1)

        async def usar_pimenta(interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message("Isso não é seu!", ephemeral=True)
                return
            if buscar_qtd_item_mineracao(self.usuario_id, "Pimenta") <= 0:
                await interaction.response.send_message("Você não tem mais pimentas!", ephemeral=True)
                return
            remover_item_mineracao(self.usuario_id, "Pimenta", 1)
            con = sqlite3.connect("jogadorbot.db")
            cur = con.cursor()
            cur.execute("UPDATE usuario_stats SET pimenta_ativa = 1 WHERE usuario_id = ?", (str(self.usuario_id),))
            con.commit()
            con.close()
            self.montar()
            self.view_inicio.montar()
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("🌶️ Você comeu a pimenta! Seu próximo ataque na mineração terá +30% de dano.", ephemeral=True)

        btn_pimenta.callback = usar_pimenta
        linha_pimenta.add_item(btn_pimenta)
        container.add_item(linha_pimenta)

        btn_voltar = ui.Button(label="🔙 Voltar", style=discord.ButtonStyle.danger)
        async def voltar_cb(interaction):
            self.view_inicio.montar()
            await interaction.response.edit_message(view=self.view_inicio)
        btn_voltar.callback = voltar_cb
        container.add_item(btn_voltar)

        self.add_item(container)

class ViewMinerarInicio(ui.LayoutView):
    def __init__(self, usuario_id, ctx):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.ctx = ctx
        self.montar()

    def montar(self):
        self.clear_items()
        stats = buscar_stats(self.usuario_id)
        pode_minerar, aviso = tempo_restante_minerar(self.usuario_id)

        container = ui.Container()
        container.accent_color = discord.Colour.dark_gold()
        texto = (
            f"### ⛏️ Mineração\n"
            f"❤️ **HP:** {stats['hp_atual']}/{hp_maximo(self.usuario_id)}\n"
            f"⛏️ **Usos da picareta:** {stats['picareta_usos']}"
        )
        if stats["pimenta_ativa"]:
            texto += "\n🌶️ **Bônus de dano ativo!**"
        if not pode_minerar:
            texto += f"\n\n{aviso}"
        container.add_item(ui.TextDisplay(texto))
        container.add_item(ui.Separator())

        linha = ui.ActionRow()
        btn_comecar = ui.Button(label="▶️ Começar", style=discord.ButtonStyle.success,
                                 disabled=stats["picareta_usos"] <= 0 and pode_minerar)
        btn_vender = ui.Button(label="💰 Vender Minérios", style=discord.ButtonStyle.secondary)
        btn_consumir = ui.Button(label="☕ Consumir", style=discord.ButtonStyle.secondary)

        async def comecar_cb(interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message("Isso não é seu!", ephemeral=True)
                return
            pode, aviso_atual = tempo_restante_minerar(self.usuario_id)
            if not pode:
                await interaction.response.send_message(aviso_atual, ephemeral=True)
                return
            stats_atual = buscar_stats(self.usuario_id)
            if stats_atual["picareta_usos"] <= 0:
                await interaction.response.send_message("❌ Você não tem uma picareta! Compre uma em `!loja` na categoria ⛏️ Mineração.", ephemeral=True)
                return
            MINERACAO_ATIVAS.add(self.usuario_id)
            view = ViewMineracao(self.usuario_id, self.ctx)
            await view.iniciar(interaction=interaction)

        async def vender_cb(interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message("Isso não é seu!", ephemeral=True)
                return
            view = ViewVenderMinerios(self.usuario_id, self)
            await interaction.response.edit_message(view=view)

        async def consumir_cb(interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message("Isso não é seu!", ephemeral=True)
                return
            view = ViewConsumiveis(self.usuario_id, self)
            await interaction.response.edit_message(view=view)

        btn_comecar.callback = comecar_cb
        btn_vender.callback = vender_cb
        btn_consumir.callback = consumir_cb
        linha.add_item(btn_comecar)
        linha.add_item(btn_vender)
        linha.add_item(btn_consumir)
        container.add_item(linha)

        self.add_item(container)


class ModalVenderMinerio(discord.ui.Modal):
    def __init__(self, usuario_id, minerio_nome, quantidade_disponivel, view_vender):
        super().__init__(title=f"Vender {minerio_nome}")
        self.usuario_id = usuario_id
        self.minerio_nome = minerio_nome
        self.view_vender = view_vender
        self.quantidade_input = discord.ui.TextInput(
            label=f"Quantidade (máx: {quantidade_disponivel})",
            placeholder="Digite a quantidade que deseja vender",
            required=True
        )
        self.add_item(self.quantidade_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd = int(self.quantidade_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Digite um número válido!", ephemeral=True)
            return
        if qtd <= 0:
            await interaction.response.send_message("❌ A quantidade precisa ser maior que 0!", ephemeral=True)
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("SELECT quantidade FROM minerios_usuarios WHERE usuario_id = ? AND minerio = ?",
                    (str(self.usuario_id), self.minerio_nome))
        r = cur.fetchone()
        qtd_atual = r[0] if r else 0
        if qtd > qtd_atual:
            con.close()
            await interaction.response.send_message(f"❌ Você só tem {qtd_atual}x {self.minerio_nome}!", ephemeral=True)
            return

        preco_unit = MINERIOS[self.minerio_nome]["preco"]
        total = qtd * preco_unit
        cur.execute("UPDATE minerios_usuarios SET quantidade = quantidade - ? WHERE usuario_id = ? AND minerio = ?",
                    (qtd, str(self.usuario_id), self.minerio_nome))
        con.commit()
        con.close()
        adicionar_joyens(self.usuario_id, total)

        self.view_vender.montar()
        await interaction.response.edit_message(view=self.view_vender)
        await interaction.followup.send(f"✅ Vendido {qtd}x **{self.minerio_nome}** por {total} Joyens!", ephemeral=True)


class ViewVenderMinerios(ui.LayoutView):
    def __init__(self, usuario_id, view_inicio: ViewMinerarInicio):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        self.view_inicio = view_inicio
        self.montar()

    def montar(self):
        self.clear_items()
        container = ui.Container()
        container.accent_color = discord.Colour.green()
        container.add_item(ui.TextDisplay("### 💰 Vender Minérios\nEscolha um minério para vender:"))
        container.add_item(ui.Separator())

        minerios = buscar_minerios_usuario(self.usuario_id)
        if not minerios:
            container.add_item(ui.TextDisplay("Você não possui nenhum minério para vender."))
        else:
            for nome, qtd in minerios:
                preco_unit = MINERIOS[nome]["preco"]
                container.add_item(ui.TextDisplay(f"**{nome}** — {qtd} unidade(s) ({preco_unit} Joyens cada)"))

                linha = ui.ActionRow()
                btn_vender = ui.Button(label=f"Vender {nome}", style=discord.ButtonStyle.primary)
                btn_vender_tudo = ui.Button(label=f"Vender Tudo", style=discord.ButtonStyle.success)

                async def vender_cb(interaction, minerio_nome=nome, quantidade_disp=qtd):
                    if interaction.user.id != self.usuario_id:
                        await interaction.response.send_message("Isso não é seu!", ephemeral=True)
                        return
                    modal = ModalVenderMinerio(self.usuario_id, minerio_nome, quantidade_disp, self)
                    await interaction.response.send_modal(modal)

                async def vender_tudo_cb(interaction, minerio_nome=nome):
                    if interaction.user.id != self.usuario_id:
                        await interaction.response.send_message("Isso não é seu!", ephemeral=True)
                        return
                    con = sqlite3.connect("jogadorbot.db")
                    cur = con.cursor()
                    cur.execute("SELECT quantidade FROM minerios_usuarios WHERE usuario_id = ? AND minerio = ?",
                                (str(self.usuario_id), minerio_nome))
                    r = cur.fetchone()
                    qtd_atual = r[0] if r else 0
                    if qtd_atual <= 0:
                        con.close()
                        await interaction.response.send_message("Você não tem mais esse minério!", ephemeral=True)
                        return
                    preco_unit = MINERIOS[minerio_nome]["preco"]
                    total = qtd_atual * preco_unit
                    cur.execute("UPDATE minerios_usuarios SET quantidade = 0 WHERE usuario_id = ? AND minerio = ?",
                                (str(self.usuario_id), minerio_nome))
                    con.commit()
                    con.close()
                    adicionar_joyens(self.usuario_id, total)
                    self.montar()
                    await interaction.response.edit_message(view=self)
                    await interaction.followup.send(f"✅ Vendido {qtd_atual}x **{minerio_nome}** por {total} Joyens!", ephemeral=True)

                btn_vender.callback = vender_cb
                btn_vender_tudo.callback = vender_tudo_cb
                linha.add_item(btn_vender)
                linha.add_item(btn_vender_tudo)
                container.add_item(linha)
                container.add_item(ui.Separator())

        btn_voltar = ui.Button(label="🔙 Voltar", style=discord.ButtonStyle.danger)
        async def voltar_cb(interaction):
            self.view_inicio.montar()
            await interaction.response.edit_message(view=self.view_inicio)
        btn_voltar.callback = voltar_cb
        linha_voltar = ui.ActionRow()
        linha_voltar.add_item(btn_voltar)
        container.add_item(linha_voltar)

        self.add_item(container)

# ============================================================
# VIEW (BOTÕES) - Mineração - O jogo
# ============================================================
class ViewMineracao(ui.LayoutView):
    def __init__(self, usuario_id, ctx):
        super().__init__(timeout=None)
        self.usuario_id = usuario_id
        self.ctx = ctx
        self.message = None
        self.tick = 0
        self.total_ticks = 30
        self.joyogens_ganhas = 0
        self.minerios_ganhos = {}
        self.em_combate = False
        self.monstro_atual = None
        self.monstro_hp = 0
        self.finalizado = False
        self.ataque_event = asyncio.Event()
        self.texto_status = "⛏️ Você começou a minerar. O som da picareta ecoa pela caverna..."
        self.imagem_atual = "minerar1.png"

        self.btn_atacar = discord.ui.Button(label="⚔️ Atacar", style=discord.ButtonStyle.danger, disabled=True)
        self.btn_atacar.callback = self.atacar_callback
        self.btn_dinamite = discord.ui.Button(label="🧨 Dinamite", style=discord.ButtonStyle.secondary,
                                               disabled=not (buscar_qtd_item_mineracao(usuario_id, "Dinamite") > 0))
        self.btn_dinamite.callback = self.dinamite_callback
        self.btn_parar = discord.ui.Button(label="❌ Parar", style=discord.ButtonStyle.secondary)
        self.btn_parar.callback = self.parar_callback

        self.montar()

    def montar(self):
        self.clear_items()
        stats = buscar_stats(self.usuario_id)
        barra, pct = self.gerar_barra()

        container = ui.Container()
        container.accent_color = discord.Colour.dark_gold()
        container.add_item(ui.TextDisplay(f"### ⛏️ Mineração\n{self.texto_status}"))

        if os.path.exists(self.imagem_atual):
            container.add_item(ui.MediaGallery(discord.MediaGalleryItem(media=f"attachment://{self.imagem_atual}")))

        status_texto = (
            f"❤️ **HP:** {stats['hp_atual']}/{hp_maximo(self.usuario_id)}\n"
            f"💎 **Joyogens:** {self.joyogens_ganhas}\n"
            f"📊 **Progresso:** `{barra}` {pct}%"
        )
        if self.monstro_atual and self.em_combate:
            status_texto += f"\n👾 **{self.monstro_atual} HP:** {max(0, self.monstro_hp)}"
        if self.minerios_ganhos:
            status_texto += "\n\n**Minérios coletados:**\n" + "\n".join(
                f"- {n}: {q}" for n, q in self.minerios_ganhos.items()
            )
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(status_texto))

        linha = ui.ActionRow()
        linha.add_item(self.btn_atacar)
        linha.add_item(self.btn_dinamite)
        linha.add_item(self.btn_parar)
        container.add_item(linha)

        self.add_item(container)

    def gerar_barra(self):
        pct = int((self.tick / self.total_ticks) * 100)
        blocos = pct // 10
        return "█" * blocos + "░" * (10 - blocos), pct

    async def iniciar(self, interaction=None):
        self.montar()
        arquivo = discord.File(self.imagem_atual, filename=self.imagem_atual) if os.path.exists(self.imagem_atual) else None
        if interaction:
            if arquivo:
                await interaction.response.edit_message(view=self, attachments=[arquivo])
            else:
                await interaction.response.edit_message(view=self, attachments=[])
            self.message = await interaction.original_response()
        else:
            if arquivo:
                self.message = await self.ctx.send(view=self, file=arquivo)
            else:
                self.message = await self.ctx.send(view=self)
        self.task = bot.loop.create_task(self.loop_mineracao())

    async def atualizar_mensagem(self):
        self.montar()
        arquivo = discord.File(self.imagem_atual, filename=self.imagem_atual) if os.path.exists(self.imagem_atual) else None
        try:
            if arquivo:
                await self.message.edit(view=self, attachments=[arquivo])
            else:
                await self.message.edit(view=self, attachments=[])
        except:
            pass

    async def loop_mineracao(self):
        while self.tick < self.total_ticks and not self.finalizado:
            await asyncio.sleep(10)
            if self.finalizado or self.em_combate:
                continue
            self.tick += 1

            stats = buscar_stats(self.usuario_id)
            novo_usos = stats["picareta_usos"] - 1
            con = sqlite3.connect("jogadorbot.db")
            cur = con.cursor()
            cur.execute("UPDATE usuario_stats SET picareta_usos = ? WHERE usuario_id = ?",
                        (max(0, novo_usos), str(self.usuario_id)))
            con.commit()
            con.close()

            if novo_usos <= 0:
                await self.picareta_quebrou()
                return

            if random.random() < 0.25:
                self.joyogens_ganhas += random.randint(2, 10)
            for nome, dados in MINERIOS.items():
                if random.random() < dados["chance"]:
                    qtd = random.randint(dados["min"], dados["max"])
                    self.minerios_ganhos[nome] = self.minerios_ganhos.get(nome, 0) + qtd

            if random.random() < 0.20:
                await self.disparar_evento()
                if self.finalizado:
                    return
            else:
                self.texto_status = "⛏️ Você continua minerando calmamente..."
                self.imagem_atual = "minerar1.png"
                await self.atualizar_mensagem()

        if not self.finalizado:
            await self.finalizar_mineracao("completa")

    async def disparar_evento(self):
        tipo = random.choice(["Morcego", "Slime", "Cobra", "Desmoronamento"])

        if tipo == "Desmoronamento":
            self.imagem_atual = "desmoronamento1.png"
            if random.random() < 0.70:
                self.texto_status = "💥 Um desmoronamento aconteceu, mas você conseguiu escapar ileso!"
                await self.atualizar_mensagem()
                await asyncio.sleep(3)
                self.texto_status = "⛏️ Você retoma a mineração após o susto..."
                self.imagem_atual = "minerar1.png"
                await self.atualizar_mensagem()
            else:
                causa = "Um desmoronamento cobriu toda a passagem e você não teve tempo de escapar."
                await self.aplicar_penalidade_morte(causa)
            return

        monstro = MONSTROS[tipo]
        self.em_combate = True
        self.monstro_atual = tipo
        self.monstro_hp = monstro["hp"]
        self.imagem_atual = monstro["imagem"]
        self.texto_status = f"{monstro['mensagem']}\n**{tipo}** apareceu com {monstro['hp']} HP! Ataque antes que ele te acerte!"
        self.btn_atacar.disabled = False
        self.btn_atacar.label = "⚔️ Atacar (5s)"
        await self.atualizar_mensagem()
        bot.loop.create_task(self.loop_combate())

    async def loop_combate(self):
        while self.em_combate and not self.finalizado:
            self.ataque_event.clear()
            atacou_a_tempo = False

            for restante in [5, 4, 3, 2, 1]:
                if self.finalizado or not self.em_combate:
                    return
                self.btn_atacar.label = f"⚔️ Atacar ({restante}s)"
                self.btn_atacar.disabled = False
                self.montar()
                try:
                    await self.message.edit(view=self)
                except:
                    pass
                try:
                    await asyncio.wait_for(self.ataque_event.wait(), timeout=1)
                    atacou_a_tempo = True
                    break
                except asyncio.TimeoutError:
                    continue

            if self.finalizado or not self.em_combate:
                return

            self.btn_atacar.disabled = True

            if atacou_a_tempo:
                stats = buscar_stats(self.usuario_id)
                stats_pimenta = buscar_stats(self.usuario_id)
                tem_pimenta = stats_pimenta["pimenta_ativa"] == 1
                errou = random.random() < 0.10
                critico = random.random() < 0.30

                if errou:
                    dano_causado = 0
                    texto_ataque = "Você atacou, mas errou completamente!"
                else:
                    dano = random.randint(DANO_BASE_MIN, DANO_BASE_MAX)
                    if tem_pimenta:
                        dano = int(dano * (1 + BONUS_DANO_PIMENTA))
                    if critico:
                        dano = int(dano * 2)
                        texto_ataque = f"**Ataque crítico!** Você atacou antes e causou {dano} de dano!"
                    else:
                        texto_ataque = f"Você atacou antes e causou {dano} de dano!"
                    dano_causado = dano

                self.monstro_hp -= dano_causado
                self.texto_status = texto_ataque
                self.btn_atacar.label = "⚔️ Atacar"
                await self.atualizar_mensagem()

                if self.monstro_hp <= 0:
                    self.texto_status = f"{texto_ataque}\nVocê derrotou o **{self.monstro_atual}**! 🎉"
                    self.em_combate = False
                    await self.atualizar_mensagem()
                    await asyncio.sleep(2)
                    self.texto_status = "⛏️ Você retoma a mineração após a vitória..."
                    self.imagem_atual = "minerar1.png"
                    self.btn_atacar.disabled = True
                    await self.atualizar_mensagem()
                    return
                else:
                    await asyncio.sleep(2)
                    self.texto_status = f"O **{self.monstro_atual}** ainda tem {max(0, self.monstro_hp)} HP e se prepara para atacar novamente!"
                    await self.atualizar_mensagem()
                    continue
            else:
                monstro = MONSTROS[self.monstro_atual]
                stats = buscar_stats(self.usuario_id)
                novo_hp = atualizar_hp(self.usuario_id, stats["hp_atual"] - monstro["dano"])
                self.texto_status = f"Você não atacou a tempo! O **{self.monstro_atual}** te acertou causando {monstro['dano']} de dano!"
                self.btn_atacar.label = "⚔️ Atacar"

                if novo_hp <= 0:
                    causa = f"Um **{self.monstro_atual}** te atacou enquanto você hesitava, e o golpe foi fatal."
                    await self.aplicar_penalidade_morte(causa)
                    return
                else:
                    await self.atualizar_mensagem()
                    await asyncio.sleep(2)
                    self.texto_status = f"O **{self.monstro_atual}** ainda tem {max(0, self.monstro_hp)} HP e se prepara para atacar novamente!"
                    await self.atualizar_mensagem()
                    continue

    async def atacar_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.usuario_id:
            await interaction.response.send_message("Essa não é sua mineração!", ephemeral=True)
            return
        if not self.em_combate or self.ataque_event.is_set() or self.btn_atacar.disabled:
            await interaction.response.send_message("Não há nada para atacar agora!", ephemeral=True)
            return
        self.ataque_event.set()
        await interaction.response.defer()

    async def picareta_quebrou(self):
        for child in [self.btn_atacar, self.btn_dinamite, self.btn_parar]:
            child.disabled = True

        preco_nova = int(ITENS_MINERACAO["Picareta"]["preco"] * 1.2)
        layout_decisao = ui.LayoutView()
        container = ui.Container()
        container.accent_color = discord.Colour.orange()
        container.add_item(ui.TextDisplay(
            "### ⛏️ Picareta quebrada!\nSua picareta quebrou! Quer comprar uma nova (20% mais cara) "
            "para continuar ou parar por aqui?"
        ))

        btn_comprar = discord.ui.Button(label=f"⛏️ Comprar nova ({preco_nova} Joyens)", style=discord.ButtonStyle.success)
        btn_parar_quebra = discord.ui.Button(label="❌ Parar mineração", style=discord.ButtonStyle.danger)

        async def comprar_cb(interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message("Essa não é sua mineração!", ephemeral=True)
                return
            sucesso, msg = comprar_item_mineracao(self.usuario_id, "Picareta", preco_customizado=preco_nova)
            if not sucesso:
                await interaction.response.send_message(f"❌ {msg}", ephemeral=True)
                return
            await interaction.response.send_message("✅ Nova picareta comprada! Continuando a mineração...", ephemeral=True)
            self.btn_dinamite.disabled = not (buscar_qtd_item_mineracao(self.usuario_id, "Dinamite") > 0)
            self.btn_parar.disabled = False
            self.texto_status = "⛏️ Picareta trocada! Você volta a minerar..."
            self.imagem_atual = "minerar1.png"
            await self.atualizar_mensagem()
            self.task = bot.loop.create_task(self.loop_mineracao())

        async def parar_quebra_cb(interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message("Essa não é sua mineração!", ephemeral=True)
                return
            await interaction.response.defer()
            await self.finalizar_mineracao("parou")

        btn_comprar.callback = comprar_cb
        btn_parar_quebra.callback = parar_quebra_cb
        linha = ui.ActionRow()
        linha.add_item(btn_comprar)
        linha.add_item(btn_parar_quebra)
        container.add_item(linha)
        layout_decisao.add_item(container)

        try:
            await self.message.edit(view=layout_decisao, attachments=[])
        except:
            pass

    async def dinamite_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.usuario_id:
            await interaction.response.send_message("Essa não é sua mineração!", ephemeral=True)
            return
        if self.finalizado:
            return
        self.finalizado = True
        self.em_combate = False
        remover_item_mineracao(self.usuario_id, "Dinamite", 1)

        if random.random() < 0.10:
            con = sqlite3.connect("jogadorbot.db")
            cur = con.cursor()
            penalidade_ate = (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
            cur.execute("UPDATE usuario_stats SET penalidade_ate = ? WHERE usuario_id = ?",
                        (penalidade_ate, str(self.usuario_id)))
            con.commit()
            con.close()
            self.texto_status = "💥 A dinamite falhou e explodiu na hora errada! A mineração foi perdida. Espere 1 hora para minerar novamente."
            for child in [self.btn_atacar, self.btn_dinamite, self.btn_parar]:
                child.disabled = True
            self.montar()
            await interaction.response.edit_message(view=self, attachments=[])
            MINERACAO_ATIVAS.discard(self.usuario_id)
            return

        ticks_restantes = self.total_ticks - self.tick
        for _ in range(ticks_restantes):
            if random.random() < 0.25:
                self.joyogens_ganhas += random.randint(2, 10)
            for nome, dados in MINERIOS.items():
                if random.random() < dados["chance"]:
                    qtd = random.randint(dados["min"], dados["max"])
                    self.minerios_ganhos[nome] = self.minerios_ganhos.get(nome, 0) + qtd

        await interaction.response.defer()
        await self.finalizar_mineracao("dinamite")

    async def parar_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.usuario_id:
            await interaction.response.send_message("Essa não é sua mineração!", ephemeral=True)
            return
        if self.finalizado:
            return
        self.finalizado = True
        self.em_combate = False
        await interaction.response.defer()
        await self.finalizar_mineracao("parou")

    async def aplicar_penalidade_morte(self, causa):
        self.finalizado = True
        self.em_combate = False
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        penalidade_ate = (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
        cur.execute("UPDATE usuario_stats SET penalidade_ate = ?, pimenta_ativa = 0 WHERE usuario_id = ?",
                    (penalidade_ate, str(self.usuario_id)))
        con.commit()
        con.close()

        stats = buscar_stats(self.usuario_id)
        layout_morte = ui.LayoutView()
        container = ui.Container()
        container.accent_color = discord.Colour.dark_red()
        container.add_item(ui.TextDisplay(
            f"### 💀 Você morreu!\n{causa}\n\n"
            f"Sua mineração foi perdida. Você precisará esperar **1 hora** antes de minerar novamente."
        ))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ❤️ HP: 0/{hp_maximo(self.usuario_id)}"))
        layout_morte.add_item(container)

        try:
            await self.message.edit(view=layout_morte, attachments=[])
        except:
            pass
        MINERACAO_ATIVAS.discard(self.usuario_id)

    async def finalizar_mineracao(self, motivo):
        self.finalizado = True
        self.em_combate = False
        for child in [self.btn_atacar, self.btn_dinamite, self.btn_parar]:
            child.disabled = True

        if motivo == "parou":
            self.joyogens_ganhas = int(self.joyogens_ganhas * 0.5)
            self.minerios_ganhos = {nome: int(qtd * 0.5) for nome, qtd in self.minerios_ganhos.items()}

        if self.joyogens_ganhas > 0:
            adicionar_joyogens(self.usuario_id, self.joyogens_ganhas)
        for nome, qtd in self.minerios_ganhos.items():
            if qtd > 0:
                adicionar_minerio(self.usuario_id, nome, qtd)

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("UPDATE usuario_stats SET ultimo_minerar = ? WHERE usuario_id = ?",
                    (datetime.datetime.now().isoformat(), str(self.usuario_id)))
        con.commit()
        con.close()

        titulo_map = {
            "completa": "⛏️ Mineração Concluída!",
            "dinamite": "🧨 Mineração Explodida!",
            "parou": "❌ Mineração Interrompida"
        }
        stats = buscar_stats(self.usuario_id)
        texto_minerios = "\n".join(f"- {n}: {q}" for n, q in self.minerios_ganhos.items() if q > 0) or "Nenhum"

        layout_final = ui.LayoutView()
        container = ui.Container()
        container.accent_color = discord.Colour.gold()
        container.add_item(ui.TextDisplay(
            f"### {titulo_map.get(motivo, '⛏️ Mineração Finalizada')}\n"
            f"💎 **Joyogens ganhas:** {self.joyogens_ganhas}\n\n"
            f"**Minérios coletados:**\n{texto_minerios}"
        ))
        container.add_item(ui.Separator())
        container.add_item(ui.TextDisplay(f"-# ❤️ HP atual: {stats['hp_atual']}/{hp_maximo(self.usuario_id)}"))
        layout_final.add_item(container)

        try:
            await self.message.edit(view=layout_final, attachments=[])
        except:
            pass
        MINERACAO_ATIVAS.discard(self.usuario_id)
        
# ============================================================
# VIEW (BOTÕES) - Petshop
# ============================================================

def gerar_embed_petshop(usuario_id):
    embed = discord.Embed(
        title="🐾 Petshop",
        description="Escolha uma subcategoria:",
        color=discord.Color.gold()
    )
    embed.add_field(name="🐾 Pets", value="Adote um novo companheiro!", inline=False)
    embed.add_field(name="🍖 Petiscos", value="Compre comida para alimentar seus pets.", inline=False)
    embed.add_field(name="🧸 Brinquedos", value="Compre brinquedos para brincar com seus pets.", inline=False)
    embed.add_field(name="🧼 Higiene", value="Compre sabonete para dar banho nos seus pets.", inline=False)
    embed.set_footer(text=f"Seu saldo: {buscar_joyens(usuario_id)} Joyens")
    return embed


class ViewMenuPetshop(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id

    @discord.ui.button(label="🐾 Pets", style=discord.ButtonStyle.primary)
    async def abrir_pets(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewComprarPet(self.usuario_id)
        embed = view.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🍖 Petiscos", style=discord.ButtonStyle.primary)
    async def abrir_petiscos(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewComprarPetisco(self.usuario_id)
        embed = view.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🧸 Brinquedos", style=discord.ButtonStyle.primary)
    async def abrir_brinquedos(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewComprarBrinquedo(self.usuario_id)
        embed = view.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🧼 Higiene", style=discord.ButtonStyle.primary)
    async def abrir_higiene(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewComprarSabonete(self.usuario_id)
        embed = view.gerar_embed()
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔙 Loja", style=discord.ButtonStyle.danger)
    async def voltar_loja(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🏪 Loja do JogadorBot",
            description="Bem-vindo à loja! Use seus Joyens para comprar itens incríveis.\nEscolha uma categoria:",
            color=discord.Color.gold()
        )
        embed.add_field(name="🖼️ Banners", value="Personalize o seu perfil com banners exclusivos!", inline=False)
        embed.add_field(name="🐾 Petshop", value="Adote e cuide de um bichinho virtual!", inline=False)
        embed.set_footer(text=f"Seu saldo: {buscar_joyens(self.usuario_id)} Joyens")
        view = ViewMenuLoja(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view, attachments=[])


class ModalNomearPet(discord.ui.Modal, title="Dar um nome ao seu novo pet"):
    nome_pet = discord.ui.TextInput(
        label="Nome do pet",
        placeholder="Ex: Mochi",
        max_length=20,
        min_length=1
    )

    def __init__(self, usuario_id, especie):
        super().__init__()
        self.usuario_id = usuario_id
        self.especie = especie

    async def on_submit(self, interaction: discord.Interaction):
        dados = PETS_DISPONIVEIS[self.especie]

        if contar_pets(self.usuario_id) >= LIMITE_PETS:
            await interaction.response.send_message(
                f"❌ Você já atingiu o limite de {LIMITE_PETS} pets!", ephemeral=True
            )
            return

        saldo = buscar_joyens(self.usuario_id)
        if saldo < dados["preco"]:
            await interaction.response.send_message(
                f"❌ Você não tem Joyens suficientes! Saldo: {saldo} Joyens.", ephemeral=True
            )
            return

        remover_joyens(self.usuario_id, dados["preco"])

        agora = datetime.datetime.now(FUSO_BR).isoformat()
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            INSERT INTO pets (usuario_id, especie, nome, fome, energia, higiene, felicidade, criado_em, ultima_atualizacao)
            VALUES (?, ?, ?, 100, 100, 100, 100, ?, ?)
        """, (str(self.usuario_id), self.especie, self.nome_pet.value, agora, agora))
        con.commit()
        con.close()

        await interaction.response.send_message(
            f"{dados['emoji']} **{self.nome_pet.value}** agora faz parte da família! Use `/pet ver` para cuidar dele.",
            ephemeral=True
        )

class ModalQuantidadeCompra(discord.ui.Modal, title="Quantos você quer comprar?"):
    quantidade = discord.ui.TextInput(
        label="Quantidade",
        placeholder="Ex: 5",
        max_length=3,
        min_length=1
    )

    def __init__(self, usuario_id, categoria, tipo, preco_unitario, usos_unitario=None):
        super().__init__()
        self.usuario_id = usuario_id
        self.categoria = categoria  # "petisco", "brinquedo" ou "sabonete"
        self.tipo = tipo
        self.preco_unitario = preco_unitario
        self.usos_unitario = usos_unitario

    async def on_submit(self, interaction: discord.Interaction):
        texto = self.quantidade.value.strip()
        if not texto.isdigit() or int(texto) <= 0:
            await interaction.response.send_message(
                "❌ Digite um número inteiro maior que 0!", ephemeral=True
            )
            return

        qtd = int(texto)
        preco_total = self.preco_unitario * qtd

        saldo = buscar_joyens(self.usuario_id)
        if saldo < preco_total:
            await interaction.response.send_message(
                f"❌ Você não tem Joyens suficientes! Precisa de {preco_total} Joyens, "
                f"mas seu saldo é {saldo} Joyens.",
                ephemeral=True
            )
            return

        remover_joyens(self.usuario_id, preco_total)
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()

        if self.categoria == "petisco":
            cur.execute("""
                INSERT INTO pets_petiscos (usuario_id, tipo, quantidade) VALUES (?, ?, ?)
                ON CONFLICT(usuario_id, tipo) DO UPDATE SET quantidade = quantidade + ?
            """, (str(self.usuario_id), self.tipo, qtd, qtd))
        elif self.categoria == "brinquedo":
            total_usos = self.usos_unitario * qtd
            cur.execute("""
                INSERT INTO pets_brinquedos (usuario_id, tipo, usos_restantes) VALUES (?, ?, ?)
                ON CONFLICT(usuario_id, tipo) DO UPDATE SET usos_restantes = usos_restantes + ?
            """, (str(self.usuario_id), self.tipo, total_usos, total_usos))
        elif self.categoria == "sabonete":
            cur.execute("""
                INSERT INTO pets_sabonete (usuario_id, quantidade) VALUES (?, ?)
                ON CONFLICT(usuario_id) DO UPDATE SET quantidade = quantidade + ?
            """, (str(self.usuario_id), qtd, qtd))

        con.commit()
        con.close()

        await interaction.response.send_message(
            f"✅ Você comprou {qtd}x **{self.tipo}** por {preco_total} Joyens!", ephemeral=True
        )

class ViewComprarPet(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        for especie, dados in PETS_DISPONIVEIS.items():
            botao = discord.ui.Button(
                label=f"{dados['emoji']} {especie} — {dados['preco']} Joyens",
                style=discord.ButtonStyle.success
            )
            botao.callback = self.criar_callback(especie)
            self.add_item(botao)

        botao_voltar = discord.ui.Button(label="🔙 Petshop", style=discord.ButtonStyle.danger)
        botao_voltar.callback = self.voltar_petshop
        self.add_item(botao_voltar)

    async def voltar_petshop(self, interaction: discord.Interaction):
        view = ViewMenuPetshop(self.usuario_id)
        embed = gerar_embed_petshop(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view)

    def criar_callback(self, especie):
        async def callback(interaction: discord.Interaction):
            if contar_pets(self.usuario_id) >= LIMITE_PETS:
                await interaction.response.send_message(
                    f"❌ Você já tem o máximo de {LIMITE_PETS} pets! Confira com `/pet ver`.",
                    ephemeral=True
                )
                return
            await interaction.response.send_modal(ModalNomearPet(self.usuario_id, especie))
        return callback

    def gerar_embed(self):
        embed = discord.Embed(
            title="🐾 Petshop — Pets",
            description=f"Adote um novo companheiro! Limite de {LIMITE_PETS} pets por usuário.",
            color=discord.Color.gold()
        )
        for especie, dados in PETS_DISPONIVEIS.items():
            embed.add_field(
                name=f"{dados['emoji']} {especie} — {dados['preco']} Joyens",
                value=dados["descricao"],
                inline=False
            )
        return embed


class ViewComprarPetisco(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        for especie, dados in PETS_DISPONIVEIS.items():
            botao = discord.ui.Button(
                label=f"{dados['petisco_nome']} — {dados['petisco_preco']} Joyens",
                style=discord.ButtonStyle.success
            )
            botao.callback = self.criar_callback(dados["petisco_nome"], dados["petisco_preco"])
            self.add_item(botao)

        botao_voltar = discord.ui.Button(label="🔙 Petshop", style=discord.ButtonStyle.danger)
        botao_voltar.callback = self.voltar_petshop
        self.add_item(botao_voltar)

    async def voltar_petshop(self, interaction: discord.Interaction):
        view = ViewMenuPetshop(self.usuario_id)
        embed = gerar_embed_petshop(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view)

    def criar_callback(self, tipo, preco):
        async def callback(interaction: discord.Interaction):
            await interaction.response.send_modal(
                ModalQuantidadeCompra(self.usuario_id, "petisco", tipo, preco)
            )
        return callback

    def gerar_embed(self):
        embed = discord.Embed(
            title="🍖 Petshop — Petiscos",
            description="Compre petiscos para alimentar seus pets. Escolha o petisco e informe a quantidade.",
            color=discord.Color.gold()
        )
        for especie, dados in PETS_DISPONIVEIS.items():
            embed.add_field(
                name=f"{dados['petisco_nome']} — {dados['petisco_preco']} Joyens",
                value=f"Petisco favorito do {dados['emoji']} {especie}",
                inline=False
            )
        return embed


class ViewComprarBrinquedo(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        for especie, dados in PETS_DISPONIVEIS.items():
            botao = discord.ui.Button(
                label=f"{dados['brinquedo_nome']} — {dados['brinquedo_preco']} Joyens",
                style=discord.ButtonStyle.success
            )
            botao.callback = self.criar_callback(dados["brinquedo_nome"], dados["brinquedo_preco"], dados["brinquedo_usos"])
            self.add_item(botao)

        botao_voltar = discord.ui.Button(label="🔙 Petshop", style=discord.ButtonStyle.danger)
        botao_voltar.callback = self.voltar_petshop
        self.add_item(botao_voltar)

    async def voltar_petshop(self, interaction: discord.Interaction):
        view = ViewMenuPetshop(self.usuario_id)
        embed = gerar_embed_petshop(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view)

    def criar_callback(self, tipo, preco, usos):
        async def callback(interaction: discord.Interaction):
            await interaction.response.send_modal(
                ModalQuantidadeCompra(self.usuario_id, "brinquedo", tipo, preco, usos_unitario=usos)
            )
        return callback

    def gerar_embed(self):
        embed = discord.Embed(
            title="🧸 Petshop — Brinquedos",
            description="Compre brinquedos para brincar com seus pets. Escolha o brinquedo e informe a quantidade.",
            color=discord.Color.gold()
        )
        for especie, dados in PETS_DISPONIVEIS.items():
            embed.add_field(
                name=f"{dados['brinquedo_nome']} — {dados['brinquedo_preco']} Joyens",
                value=f"Brinquedo favorito do {dados['emoji']} {especie} · {dados['brinquedo_usos']} usos cada",
                inline=False
            )
        return embed


class ViewComprarSabonete(discord.ui.View):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id

    @discord.ui.button(label=f"🧼 Sabonete — {SABONETE_PRECO} Joyens", style=discord.ButtonStyle.success)
    async def comprar_sabonete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            ModalQuantidadeCompra(self.usuario_id, "sabonete", SABONETE_NOME, SABONETE_PRECO)
        )

    @discord.ui.button(label="🔙 Petshop", style=discord.ButtonStyle.danger)
    async def voltar_petshop(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = ViewMenuPetshop(self.usuario_id)
        embed = gerar_embed_petshop(self.usuario_id)
        await interaction.response.edit_message(embed=embed, view=view)

    def gerar_embed(self):
        embed = discord.Embed(
            title="🧼 Petshop — Higiene",
            description=f"O Sabonete é universal e serve para dar banho em qualquer pet.\n\n**Sabonete** — {SABONETE_PRECO} Joyens",
            color=discord.Color.gold()
        )
        return embed
# ============================================================
# VIEW (BOTÕES) - !pets (Components V2)
# ============================================================

class ViewEscolherPetisco(discord.ui.View):
    def __init__(self, usuario_id, pet_id, petiscos, view_pets=None, mensagem_pets=None):
        super().__init__(timeout=60)
        self.usuario_id = usuario_id
        self.pet_id = pet_id
        self.view_pets = view_pets
        self.mensagem_pets = mensagem_pets
        self.montar_select(petiscos)

    def montar_select(self, petiscos):
        for item in list(self.children):
            self.remove_item(item)

        opcoes = [
            discord.SelectOption(label=f"{tipo} (x{quantidade})", value=tipo)
            for tipo, quantidade in petiscos[:25]
        ]
        select = discord.ui.Select(placeholder="Escolha um petisco...", options=opcoes)
        select.callback = self.escolher
        self.add_item(select)

    async def escolher(self, interaction: discord.Interaction):
        tipo = interaction.data["values"][0]

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute(
            "SELECT quantidade FROM pets_petiscos WHERE usuario_id = ? AND tipo = ?",
            (str(self.usuario_id), tipo)
        )
        resultado = cur.fetchone()
        if not resultado or resultado[0] <= 0:
            con.close()
            await interaction.response.edit_message(content=f"❌ Você não tem mais **{tipo}**!", view=None)
            return

        cur.execute(
            "UPDATE pets_petiscos SET quantidade = quantidade - 1 WHERE usuario_id = ? AND tipo = ?",
            (str(self.usuario_id), tipo)
        )
        con.commit()
        con.close()

        atualizar_stats_pet(self.pet_id)
        aplicar_efeito_pet(self.pet_id, fome=FOME_ALIMENTAR, felicidade=FELICIDADE_ALIMENTAR)

        # Atualiza a mensagem principal do /pets (status), igual o Brincar e o Banho já fazem
        if self.view_pets is not None and self.mensagem_pets is not None:
            self.view_pets.montar()
            try:
                await self.mensagem_pets.edit(view=self.view_pets)
            except discord.HTTPException:
                pass

        nova_quantidade = resultado[0] - 1
        if nova_quantidade <= 0:
            await interaction.response.edit_message(
                content=f"✅ Você deu **{tipo}** para o seu pet! Você não tem mais {tipo}.",
                view=None
            )
        else:
            self.montar_select([(tipo, nova_quantidade)])
            await interaction.response.edit_message(
                content=f"✅ Você deu **{tipo}** para o seu pet! Restam {nova_quantidade}x — pode dar de novo se quiser.",
                view=self
            )

class ViewConfirmarAdocao(discord.ui.View):
    def __init__(self, usuario_id, pet_id, nome_pet, view_pets=None, mensagem_pets=None):
        super().__init__(timeout=60)
        self.usuario_id = usuario_id
        self.pet_id = pet_id
        self.nome_pet = nome_pet
        self.view_pets = view_pets
        self.mensagem_pets = mensagem_pets

    @discord.ui.button(label="Confirmar", emoji="✅", style=discord.ButtonStyle.danger)
    async def confirmar(self, interaction: discord.Interaction, button: discord.ui.Button):
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute(
            "UPDATE pets SET disponivel_adocao = 1 WHERE id = ? AND usuario_id = ? AND disponivel_adocao = 0",
            (self.pet_id, str(self.usuario_id))
        )
        con.commit()
        alterou = cur.rowcount > 0
        con.close()

        if not alterou:
            await interaction.response.edit_message(
                content="❌ Não foi possível colocar esse pet para adoção (ele já pode ter sido movido).",
                view=None
            )
            return

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"🏠 **{self.nome_pet}** foi colocado para adoção.",
            view=self
        )

        if self.view_pets is not None and self.mensagem_pets is not None:
            self.view_pets.pet_id_selecionado = None
            self.view_pets.montar()
            try:
                await self.mensagem_pets.edit(view=self.view_pets)
            except discord.HTTPException:
                pass

    @discord.ui.button(label="Cancelar", emoji="❌", style=discord.ButtonStyle.secondary)
    async def cancelar(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content="Ação cancelada.", view=self)

class ViewPets(discord.ui.LayoutView):
    def __init__(self, usuario_id, pet_id_selecionado=None):
        super().__init__(timeout=180)
        self.usuario_id = usuario_id
        self.pet_id_selecionado = pet_id_selecionado
        self.montar()

    def montar(self):
        self.clear_items()
        pets_usuario = listar_pets(self.usuario_id)

        if not pets_usuario:
            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    "🐾 **Você ainda não tem nenhum pet!**\nUse `!loja` → Petshop → Pets para adotar um."
                )
            )
            container.accent_color = discord.Colour.red()
            self.add_item(container)
            return

        opcoes = []
        for pet_id, especie, nome in pets_usuario:
            dados = PETS_DISPONIVEIS.get(especie, {})
            opcoes.append(discord.SelectOption(
                label=nome,
                value=str(pet_id),
                description=especie,
                emoji=dados.get("emoji"),
                default=(self.pet_id_selecionado == pet_id)
            ))

        select = discord.ui.Select(placeholder="Escolha um pet para ver e cuidar...", options=opcoes)
        select.callback = self.selecionar_pet
        self.add_item(discord.ui.ActionRow(select))

        if self.pet_id_selecionado is None:
            container = discord.ui.Container(
                discord.ui.TextDisplay(
                    "🐾 **Seus Pets**\nSelecione um pet no menu acima para ver o status e cuidar dele!"
                )
            )
            container.accent_color = discord.Colour.blue()
            self.add_item(container)
            return

        pet = self.buscar_pet_atualizado()
        if pet is None:
            container = discord.ui.Container(
                discord.ui.TextDisplay("❌ Esse pet não foi encontrado.")
            )
            self.add_item(container)
            return

        pet_id, especie, nome, fome, energia, higiene, felicidade, dormindo_ate = pet
        dados = PETS_DISPONIVEIS.get(especie, {})
        dormindo = dormindo_ate is not None and datetime.datetime.fromisoformat(dormindo_ate) > datetime.datetime.now(FUSO_BR)

        titulo = f"{dados.get('emoji', '🐾')} {nome}" + (" 💤" if dormindo else "")

        botao_adocao = discord.ui.Button(label="Adoção", emoji="🏠", style=discord.ButtonStyle.danger)
        botao_adocao.callback = self.abrir_adocao

        container = discord.ui.Container(
            discord.ui.Section(
                discord.ui.TextDisplay(f"# {titulo}\n{dados.get('descricao', '')}"),
                accessory=botao_adocao
            )
        )
        container.accent_color = discord.Colour.blue()
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        container.add_item(discord.ui.TextDisplay(self.barra_status("Fome", "🍖", fome)))
        container.add_item(discord.ui.TextDisplay(self.barra_status("Energia", "⚡", energia)))
        container.add_item(discord.ui.TextDisplay(self.barra_status("Higiene", "🧼", higiene)))
        container.add_item(discord.ui.TextDisplay(self.barra_status("Felicidade", "😊", felicidade)))

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        botao_alimentar = discord.ui.Button(label="Alimentar", emoji="🍖", style=discord.ButtonStyle.success, disabled=dormindo)
        botao_alimentar.callback = self.abrir_alimentar

        botao_brincar = discord.ui.Button(label="Brincar", emoji="🎾", style=discord.ButtonStyle.primary, disabled=dormindo)
        botao_brincar.callback = self.brincar

        botao_banho = discord.ui.Button(label="Banho", emoji="🧼", style=discord.ButtonStyle.primary, disabled=dormindo)
        botao_banho.callback = self.banho

        botao_dormir = discord.ui.Button(
            label="Dormindo..." if dormindo else "Dormir",
            emoji="💤" if dormindo else "😴",
            style=discord.ButtonStyle.secondary,
            disabled=dormindo
        )
        botao_dormir.callback = self.dormir

        container.add_item(discord.ui.ActionRow(botao_alimentar, botao_brincar, botao_banho, botao_dormir))

        self.add_item(container)

    def barra_status(self, nome, emoji, valor):
        blocos_cheios = valor // 10
        barra = "█" * blocos_cheios + "░" * (10 - blocos_cheios)
        return f"{emoji} **{nome}**\n`{barra}` {valor}%"

    async def abrir_adocao(self, interaction: discord.Interaction):
        pet = self.buscar_pet_atualizado()
        if pet is None:
            await interaction.response.send_message("❌ Pet não encontrado.", ephemeral=True)
            return
        pet_id, especie, nome = pet[0], pet[1], pet[2]

        view = ViewConfirmarAdocao(self.usuario_id, pet_id, nome, view_pets=self, mensagem_pets=interaction.message)
        await interaction.response.send_message(
            f"⚠️ Tem certeza que quer colocar **{nome}** para adoção?\n"
            f"Ele vai sair da sua lista de pets e você **não** recebe Joyens em troca. "
            f"Essa ação não pode ser desfeita.",
            view=view,
            ephemeral=True
        )

    def buscar_pet_atualizado(self):
        atualizar_stats_pet(self.pet_id_selecionado)
        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            SELECT id, especie, nome, fome, energia, higiene, felicidade, dormindo_ate
            FROM pets WHERE id = ? AND usuario_id = ? AND disponivel_adocao = 0
        """, (self.pet_id_selecionado, str(self.usuario_id)))
        resultado = cur.fetchone()
        con.close()
        return resultado

    async def selecionar_pet(self, interaction: discord.Interaction):
        self.pet_id_selecionado = int(interaction.data["values"][0])
        self.montar()
        await interaction.response.edit_message(view=self)

    async def abrir_alimentar(self, interaction: discord.Interaction):
        pet = self.buscar_pet_atualizado()
        if pet is None:
            await interaction.response.send_message("❌ Pet não encontrado.", ephemeral=True)
            return
        pet_id, especie, nome = pet[0], pet[1], pet[2]

        dados = PETS_DISPONIVEIS.get(especie, {})
        petisco_nome = dados.get("petisco_nome")

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute(
            "SELECT quantidade FROM pets_petiscos WHERE usuario_id = ? AND tipo = ?",
            (str(self.usuario_id), petisco_nome)
        )
        resultado = cur.fetchone()
        con.close()

        if not resultado or resultado[0] <= 0:
            await interaction.response.send_message(
                f"❌ Você não tem **{petisco_nome}**, o petisco favorito do {nome}! Compre na `!loja` → PetShop → Petiscos.",
                ephemeral=True
            )
            return

        petiscos = [(petisco_nome, resultado[0])]
        view = ViewEscolherPetisco(self.usuario_id, pet_id, petiscos, view_pets=self, mensagem_pets=interaction.message)
        await interaction.response.send_message(
            "🍖 Qual petisco você quer dar ao seu pet?", view=view, ephemeral=True
        )

    async def brincar(self, interaction: discord.Interaction):
        pet = self.buscar_pet_atualizado()
        if pet is None:
            await interaction.response.send_message("❌ Pet não encontrado.", ephemeral=True)
            return
        pet_id, especie, nome, fome, energia, higiene, felicidade, dormindo_ate = pet

        if energia < BRINCAR_ENERGIA_MINIMA:
            await interaction.response.send_message(
                f"😴 {nome} está cansado demais para brincar agora. Deixe ele dormir um pouco!",
                ephemeral=True
            )
            return

        dados = PETS_DISPONIVEIS.get(especie, {})
        brinquedo_nome = dados.get("brinquedo_nome")

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute(
            "SELECT usos_restantes FROM pets_brinquedos WHERE usuario_id = ? AND tipo = ?",
            (str(self.usuario_id), brinquedo_nome)
        )
        resultado = cur.fetchone()
        if not resultado or resultado[0] <= 0:
            con.close()
            await interaction.response.send_message(
                f"❌ Você não tem um **{brinquedo_nome}**! Compre na `!loja` → Petshop → Brinquedos.",
                ephemeral=True
            )
            return

        cur.execute(
            "UPDATE pets_brinquedos SET usos_restantes = usos_restantes - 1 WHERE usuario_id = ? AND tipo = ?",
            (str(self.usuario_id), brinquedo_nome)
        )
        con.commit()
        con.close()

        aplicar_efeito_pet(
            pet_id,
            felicidade=BRINCAR_FELICIDADE,
            energia=BRINCAR_ENERGIA,
            higiene=BRINCAR_HIGIENE,
            fome=BRINCAR_FOME
        )

        self.montar()
        await interaction.response.edit_message(view=self)

    async def banho(self, interaction: discord.Interaction):
        pet = self.buscar_pet_atualizado()
        if pet is None:
            await interaction.response.send_message("❌ Pet não encontrado.", ephemeral=True)
            return
        pet_id = pet[0]

        sabonetes = buscar_sabonetes_usuario(self.usuario_id)
        if sabonetes <= 0:
            await interaction.response.send_message(
                "❌ Você não tem Sabonete! Compre na `!loja` → Petshop → Higiene.",
                ephemeral=True
            )
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute(
            "UPDATE pets_sabonete SET quantidade = quantidade - 1 WHERE usuario_id = ?",
            (str(self.usuario_id),)
        )
        con.commit()
        con.close()

        aplicar_efeito_pet(pet_id, higiene=BANHO_HIGIENE, felicidade=BANHO_FELICIDADE)

        self.montar()
        await interaction.response.edit_message(view=self)

    async def dormir(self, interaction: discord.Interaction):
        pet = self.buscar_pet_atualizado()
        if pet is None:
            await interaction.response.send_message("❌ Pet não encontrado.", ephemeral=True)
            return
        pet_id, especie, nome, fome, energia, higiene, felicidade, dormindo_ate = pet

        agora = datetime.datetime.now(FUSO_BR)
        ate = agora + datetime.timedelta(hours=DORMIR_DURACAO_HORAS)

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()
        cur.execute("""
            UPDATE pets SET dormindo_desde = ?, dormindo_ate = ?, energia_ao_dormir = ?, ultima_atualizacao = ?
            WHERE id = ?
        """, (agora.isoformat(), ate.isoformat(), energia, agora.isoformat(), pet_id))
        con.commit()
        con.close()

        self.montar()
        await interaction.response.edit_message(view=self)
        
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
            embed2.add_field(name="<:BolsaJoyensIcon:1525729605724405781> Economia", value=f"> **Joyens:** ``{joyens}``", inline=False)
            embed2.add_field(
                name="📊 Outros",
                value=f"> **Conquistas:** ``{len(conquistas)}``\n> **Banners:** ``{qtd_banners}``",
                inline=False
            )

            emprego_dados = buscar_emprego(membro.id)
            if emprego_dados:
                emprego_nome, vezes_trabalhadas, _ = emprego_dados
                emprego_info = EMPREGOS.get(emprego_nome)
                emoji_emp = emprego_info["emoji"] if emprego_info else "<:EmpregosIcon:1525710982364532890>"
                embed2.add_field(
                    name="<:EmpregosIcon:1525710982364532890> Emprego",
                    value=f"{emoji_emp} **{emprego_nome}** | {vezes_trabalhadas} vez(es) trabalhadas",
                    inline=False
                )
            else:
                embed2.add_field(name="<:EmpregosIcon:1525710982364532890> Emprego", value="Desempregado — use `!empregos`", inline=False)

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
                value=f"{descricao}\n<:BolsaJoyensIcon:1525729605724405781> **{preco} Joyens** | {status}",
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
# ============================================================
# V2 VIEW (BOTÕES) - Comando de !empregos
# ============================================================
class LayoutEmpregos(ui.LayoutView):
    def __init__(self, usuario_id):
        super().__init__(timeout=120)
        self.usuario_id = usuario_id
        level_usuario, _ = buscar_level(usuario_id)

        container = ui.Container(
            ui.TextDisplay("<:EmpregosIcon:1525710982364532890> **Menu de Empregos**\nEscolha um emprego abaixo! Empregos com ❌ precisam de level maior.")
        )
        container.accent_color = discord.Colour.blue()
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        for nome, dados in EMPREGOS.items():
            level_req = dados["level_necessario"]
            pode = level_usuario >= level_req

            texto = (
                f"{dados['emoji']} **{nome}**\n"
                f"{dados['descricao']}\n"
                f"<:JoyensIcon:1525930784584634398>{dados['salario_min']}-{dados['salario_max']} Joyens | Level {level_req}"
            )

            botao = ui.Button(
                label="✅ Escolher" if pode else "❌ Escolher",
                style=discord.ButtonStyle.success if pode else discord.ButtonStyle.danger
            )
            botao.callback = self.criar_callback(nome)

            sessao = ui.Section(ui.TextDisplay(texto), accessory=botao)
            container.add_item(sessao)
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        self.add_item(container)

    def criar_callback(self, emprego_nome):
        async def callback(interaction: discord.Interaction):
            await self.escolher_emprego(interaction, emprego_nome)
        return callback

    async def escolher_emprego(self, interaction: discord.Interaction, emprego_nome):
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

        confirmacao = LayoutConfirmacaoEmprego(emprego_nome, emprego)
        await interaction.response.edit_message(view=confirmacao)

class LayoutConfirmacaoEmprego(ui.LayoutView):
    def __init__(self, emprego_nome, emprego_dados):
        super().__init__(timeout=None)
        container = ui.Container(
            ui.TextDisplay(
                f"{emprego_dados['emoji']} **Empregado como {emprego_nome}!**\n"
                f"Você agora é um **{emprego_nome}**! Use `!trabalhar` para começar a ganhar Joyens.\n\n"
                f"<:BolsaJoyensIcon:1525729605724405781> Salário: <:JoyensIcon:1525930784584634398>{emprego_dados['salario_min']}-{emprego_dados['salario_max']} Joyens\n"
                f"📊 Level necessário: {emprego_dados['level_necessario']}"
            )
        )
        container.accent_color = discord.Colour.green()
        self.add_item(container)

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
            name="<:BolsaJoyensIcon:1525729605724405781> Economia",
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
            title="<:BolsaJoyensIcon:1525729605724405781> Economia",
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
        embed.set_footer(text="<:BolsaJoyensIcon:1525729605724405781> Economia • JogadorBot")
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
        embed.add_field(name=f"`{PREFIX}rank`", value="Abre o rank de (joyens/level)", inline=False)
        embed.add_field(name=f"`{PREFIX}missoes [@usuario]`", value="Mostra as missões semanais e o progresso", inline=False)
        embed.add_field(name=f"`{PREFIX}missoes [@usuario]`", value="Mostra todas as categorias de missões", inline=False)
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
        embed.add_field(name=f"`{PREFIX}minerar`", value="Minera Joyogens e minérios raros", inline=False)
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

    @discord.ui.button(emoji="<:BolsaJoyensIcon:1525729605724405781>", style=discord.ButtonStyle.primary, row=0)
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

    @discord.ui.button(emoji="<:BolsaJoyensIcon:1525729605724405781>", style=discord.ButtonStyle.secondary, row=0)
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
# V2 VIEW (BOTÕES) - Missões
# ============================================================
class ViewMissoesMenu(ui.LayoutView):
    def __init__(self, usuario: discord.Member):
        super().__init__(timeout=120)
        self.usuario = usuario
        self.montar()

    def montar(self):
        self.clear_items()
        container = ui.Container()
        container.accent_color = discord.Colour.purple()
        container.add_item(ui.TextDisplay("# 📋 Missões\n-# Escolha uma categoria de missões abaixo."))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
        container.add_item(ui.TextDisplay("🗓️ **Semanais** — Resetam toda segunda-feira\n📌 **Permanentes** — Sem prazo, complete uma vez\n⏳ **Temporárias** — Eventos por tempo limitado"))

        linha = ui.ActionRow()
        btn_semanais = ui.Button(label="🗓️ Semanais", style=discord.ButtonStyle.primary)
        btn_permanentes = ui.Button(label="📌 Permanentes", style=discord.ButtonStyle.primary)
        btn_temporarias = ui.Button(label="⏳ Temporárias", style=discord.ButtonStyle.primary)

        async def ir_semanais(interaction: discord.Interaction):
            view = ViewMissoesSemanais(self.usuario, pagina=0, view_menu=self)
            await interaction.response.edit_message(view=view)

        async def ir_permanentes(interaction: discord.Interaction):
            view = ViewMissoesCustomizadas(self.usuario, tipo="permanente", pagina=0, view_menu=self)
            await interaction.response.edit_message(view=view)

        async def ir_temporarias(interaction: discord.Interaction):
            view = ViewMissoesCustomizadas(self.usuario, tipo="temporaria", pagina=0, view_menu=self)
            await interaction.response.edit_message(view=view)

        btn_semanais.callback = ir_semanais
        btn_permanentes.callback = ir_permanentes
        btn_temporarias.callback = ir_temporarias

        linha.add_item(btn_semanais)
        linha.add_item(btn_permanentes)
        linha.add_item(btn_temporarias)
        container.add_item(linha)

        self.add_item(container)


class ViewMissoesSemanais(ui.LayoutView):
    def __init__(self, usuario: discord.Member, pagina: int, view_menu: ViewMissoesMenu):
        super().__init__(timeout=120)
        self.usuario = usuario
        self.pagina = pagina
        self.view_menu = view_menu
        self.por_pagina = 7
        self.total_paginas = max(1, -(-len(MISSOES_SEMANAIS) // self.por_pagina))
        self.montar()

    def montar(self):
        self.clear_items()
        semana = semana_atual()
        container = ui.Container()
        container.accent_color = discord.Colour.blue()
        container.add_item(ui.TextDisplay(f"# 🗓️ Missões Semanais\n-# Semana {semana} • {self.usuario.display_name}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        inicio = self.pagina * self.por_pagina
        fim = inicio + self.por_pagina
        for missao in MISSOES_SEMANAIS[inicio:fim]:
            progresso, completada = buscar_progresso_missao(self.usuario.id, missao["id"])
            meta = missao["meta"]
            progresso = min(progresso, meta)
            porcentagem = int((progresso / meta) * 100)
            barra = "█" * (porcentagem // 10) + "░" * (10 - porcentagem // 10)
            recompensa = f"+{missao['quantidade_recompensa']} {'Joyens' if missao['tipo_recompensa'] == 'joyens' else 'XP'}"
            status = "✅ Concluída!" if completada else f"`{barra}` {progresso}/{meta}"
            container.add_item(ui.TextDisplay(
                f"**{missao['nome']}**\n-# {missao['descricao']}\n{status}\n-# 🎁 Recompensa: {recompensa}"
            ))
            container.add_item(ui.Separator())

        linha = ui.ActionRow()
        btn_anterior = ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.pagina == 0)
        btn_proximo = ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.pagina >= self.total_paginas - 1)
        btn_voltar = ui.Button(label="🔙 Voltar", style=discord.ButtonStyle.danger)

        async def ir_anterior(interaction: discord.Interaction):
            self.pagina -= 1
            self.montar()
            await interaction.response.edit_message(view=self)

        async def ir_proximo(interaction: discord.Interaction):
            self.pagina += 1
            self.montar()
            await interaction.response.edit_message(view=self)

        async def ir_voltar(interaction: discord.Interaction):
            await interaction.response.edit_message(view=self.view_menu)

        btn_anterior.callback = ir_anterior
        btn_proximo.callback = ir_proximo
        btn_voltar.callback = ir_voltar

        linha.add_item(btn_anterior)
        linha.add_item(btn_proximo)
        linha.add_item(btn_voltar)
        container.add_item(linha)

        self.add_item(container)


class ViewMissoesCustomizadas(ui.LayoutView):
    def __init__(self, usuario: discord.Member, tipo: str, pagina: int, view_menu: ViewMissoesMenu):
        super().__init__(timeout=120)
        self.usuario = usuario
        self.tipo = tipo
        self.pagina = pagina
        self.view_menu = view_menu
        self.por_pagina = 5
        self.missoes = buscar_missoes_customizadas(tipo)
        self.total_paginas = max(1, -(-len(self.missoes) // self.por_pagina))
        self.montar()

    def montar(self):
        self.clear_items()
        titulo = "📌 Missões Permanentes" if self.tipo == "permanente" else "⏳ Missões Temporárias"
        container = ui.Container()
        container.accent_color = discord.Colour.gold() if self.tipo == "permanente" else discord.Colour.orange()
        container.add_item(ui.TextDisplay(f"# {titulo}\n-# {self.usuario.display_name}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        inicio = self.pagina * self.por_pagina
        fim = inicio + self.por_pagina
        missoes_pagina = self.missoes[inicio:fim]

        if not missoes_pagina:
            container.add_item(ui.TextDisplay("Nenhuma missão disponível nesta categoria."))
        else:
            for missao in missoes_pagina:
                mid, nome, descricao, tipo, condicoes, meta, tipo_recompensa, qtd_recompensa, data_fim, _ = missao
                progresso, completada = buscar_progresso_missao_customizada(self.usuario.id, mid)
                recompensa = f"+{qtd_recompensa} {'Joyens' if tipo_recompensa == 'joyens' else 'XP'}"
                if condicoes.strip().lower() == "null":
                    status = "✅ Concluída!" if completada else "📸 Envie uma prova para completar"
                else:
                    meta_val = meta or 1
                    progresso_val = min(progresso, meta_val)
                    porcentagem = int((progresso_val / meta_val) * 100)
                    barra = "█" * (porcentagem // 10) + "░" * (10 - porcentagem // 10)
                    status = "✅ Concluída!" if completada else f"`{barra}` {progresso_val}/{meta_val}"
                prazo = ""
                if data_fim:
                    expira_dt = datetime.datetime.fromisoformat(data_fim)
                    prazo = f"\n-# ⏰ Expira: {expira_dt.strftime('%d/%m/%Y às %H:%M')}"
                container.add_item(ui.TextDisplay(
                    f"**{nome}**\n-# {descricao}\n{status}{prazo}\n-# 🎁 Recompensa: {recompensa}"
                ))
                container.add_item(ui.Separator())

        linha = ui.ActionRow()
        btn_anterior = ui.Button(label="◀", style=discord.ButtonStyle.secondary, disabled=self.pagina == 0)
        btn_proximo = ui.Button(label="▶", style=discord.ButtonStyle.secondary, disabled=self.pagina >= self.total_paginas - 1)
        btn_voltar = ui.Button(label="🔙 Voltar", style=discord.ButtonStyle.danger)

        async def ir_anterior(interaction: discord.Interaction):
            self.pagina -= 1
            self.missoes = buscar_missoes_customizadas(self.tipo)
            self.montar()
            await interaction.response.edit_message(view=self)

        async def ir_proximo(interaction: discord.Interaction):
            self.pagina += 1
            self.missoes = buscar_missoes_customizadas(self.tipo)
            self.montar()
            await interaction.response.edit_message(view=self)

        async def ir_voltar(interaction: discord.Interaction):
            await interaction.response.edit_message(view=self.view_menu)

        btn_anterior.callback = ir_anterior
        btn_proximo.callback = ir_proximo
        btn_voltar.callback = ir_voltar

        linha.add_item(btn_anterior)
        linha.add_item(btn_proximo)
        linha.add_item(btn_voltar)
        container.add_item(linha)

        self.add_item(container)
# ============================================================
# EVENTOS
# ============================================================
@bot.event
async def on_ready():
    iniciar_banco()
    verificar_admins_expirados.start()
    verificar_rotacao.start()
    verificar_reset_semanal.start()
    verificar_missoes_temporarias.start()
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
        name="<:BolsaJoyensIcon:1525729605724405781> Economia",
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
        emoji_emp = emprego_info["emoji"] if emprego_info else "<:EmpregosIcon:1525710982364532890>"
        embed2.add_field(
            name="<:EmpregosIcon:1525710982364532890> Emprego",
            value=f"{emoji_emp} **{emprego_nome}** | {vezes_trabalhadas} vez(es) trabalhadas",
            inline=False
        )
    else:
        embed2.add_field(name="<:EmpregosIcon:1525710982364532890> Emprego", value="Desempregado — use `!empregos`", inline=False)

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

    embed = discord.Embed(title="<:BolsaJoyensIcon:1525729605724405781> Recompensa Diária!", color=discord.Color.gold())
    embed.add_field(name="Joyens recebidos", value=f"+{quantidade} Joyens", inline=True)
    embed.add_field(name="Saldo atual", value=f"{novo_saldo} Joyens", inline=True)
    embed.set_footer(text="Volte amanhã para mais Joyens!")

    xp_ganho = random.randint(250, 500)
    embed.add_field(name="XP ganho", value=f"+{xp_ganho} XP", inline=True)
    await ctx.send(embed=embed)
    atualizar_contador(ctx.author.id, "diario_semana")
    atualizar_contador(ctx.author.id, "diario_total")

    # Verifica sequência de diários
    con_seq = sqlite3.connect("jogadorbot.db")
    cur_seq = con_seq.cursor()
    cur_seq.execute("SELECT diario_ultimo, diario_seguidos FROM contadores_usuarios WHERE usuario_id = ?",
                    (str(ctx.author.id),))
    seq_dados = cur_seq.fetchone()
    ontem = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    if seq_dados and seq_dados[0] == ontem:
        cur_seq.execute("UPDATE contadores_usuarios SET diario_seguidos = diario_seguidos + 1, diario_ultimo = ? WHERE usuario_id = ?",
                        (hoje, str(ctx.author.id)))
    else:
        cur_seq.execute("UPDATE contadores_usuarios SET diario_seguidos = 1, diario_ultimo = ? WHERE usuario_id = ?",
                        (hoje, str(ctx.author.id)))
    con_seq.commit()
    con_seq.close()

    await verificar_missoes_usuario(str(ctx.author.id), ctx)
    await adicionar_xp(str(ctx.author.id), xp_ganho, ctx)

@bot.command(name="saldo")
async def saldo(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author
    joyens = buscar_joyens(membro.id)
    embed = discord.Embed(title=f"<:BolsaJoyensIcon:1525729605724405781> Saldo de {membro.display_name}", color=discord.Color.gold())
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
    embed.add_field(name="🐾 Petshop", value="Adote e cuide de um bichinho virtual!", inline=False)
    embed.add_field(name="⛏️ Mineração", value="Ferramentas, equipamentos e consumíveis!", inline=False)
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
    # Atualiza o acumulador de Joyens
    con2 = sqlite3.connect("jogadorbot.db")
    cur2 = con2.cursor()
    cur2.execute("""
        INSERT OR IGNORE INTO contadores_usuarios (usuario_id) VALUES (?)
    """, (str(ctx.author.id),))
    cur2.execute("""
        UPDATE contadores_usuarios SET joyens_acumulados = joyens_acumulados + ?
        WHERE usuario_id = ?
    """, (quantidade, str(ctx.author.id)))
    con2.commit()
    con2.close()
    await ctx.send(embed=embed)
    atualizar_contador(ctx.author.id, "apostar_semana")
    atualizar_contador(ctx.author.id, "apostar_total")
    atualizar_contador(ctx.author.id, "apostar_quantidade_semana", quantidade)
    atualizar_contador(ctx.author.id, "apostar_quantidade_total", quantidade)
    await verificar_missoes_usuario(str(ctx.author.id), ctx)

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
    layout = LayoutEmpregos(ctx.author.id)
    await ctx.send(view=layout)
    
@bot.command(name="trabalhar")
async def trabalhar(ctx):
    emprego_dados = buscar_emprego(ctx.author.id)

    # Se não tiver emprego, redireciona para o menu
    if not emprego_dados:
        layout = LayoutEmpregos(ctx.author.id)
        await ctx.send(view=layout)
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
    atualizar_contador(ctx.author.id, "trabalhar_semana")
    atualizar_contador(ctx.author.id, "trabalhar_total")
    await verificar_missoes_usuario(str(ctx.author.id), ctx)
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

        container = ui.Container(ui.TextDisplay("Salve! Este é um comando teste de V2. <:GariIcon:1525380207907704914>>"))
        container.accent_color = discord.Colour.purple()
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        botao_1 = ui.Button(label="Botão 1")
        botao_1.callback = self.botao_1_resposta
        
        sessao = ui.Section(ui.TextDisplay("Botão ao lado:"), accessory=botao_1)
        
        container.add_item(sessao)
        self.add_item(container)

    async def botao_1_resposta(self, interact:discord.Interaction):
        await interact.response.send_message(f"Olá, {interact.user.name}!")

@bot.command(name="rank")
async def rank(ctx, tipo: str = "joyens"):
    try:
        tipo = tipo.lower()
        if tipo not in ["joyens", "level"]:
            await ctx.send("❌ Tipo inválido! Use `!rank joyens` ou `!rank level`.")
            return

        con = sqlite3.connect("jogadorbot.db")
        cur = con.cursor()

        if tipo == "joyens":
            cur.execute("SELECT usuario_id, joyens FROM economia ORDER BY joyens DESC LIMIT 10")
            titulo = "<:BolsaJoyensIcon:1525729605724405781> Ranking de Joyens"
            emoji_tipo = "<:BolsaJoyensIcon:1525729605724405781>"
            sufixo = "Joyens"
        else:
            cur.execute("SELECT usuario_id, level, xp FROM level_usuarios ORDER BY level DESC, xp DESC LIMIT 10")
            titulo = "⭐ Ranking de Level"
            emoji_tipo = "⭐"
            sufixo = "Level"

        resultados = cur.fetchall()
        con.close()

        if not resultados:
            await ctx.send("❌ Nenhum dado encontrado para o ranking!")
            return

        medalhas = ["🥇", "🥈", "🥉"]
        layout = ui.LayoutView()
        container = ui.Container()
        container.accent_color = discord.Colour.gold()
        container.add_item(ui.TextDisplay(f"# {titulo}"))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))

        for i, dados in enumerate(resultados):
            usuario_id = dados[0]
            valor = dados[1]
            posicao = i + 1

            try:
                membro = ctx.guild.get_member(int(usuario_id)) or await ctx.guild.fetch_member(int(usuario_id))
                nome = membro.display_name
                avatar_url = str(membro.display_avatar.url)
            except:
                nome = f"Usuário desconhecido"
                avatar_url = None

            if posicao <= 3:
                medalha = medalhas[i]
                texto = f"**{medalha} {posicao}º — {nome}**\n{emoji_tipo} {valor:,} {sufixo}"
                if avatar_url:
                    thumbnail = ui.Thumbnail(avatar_url)
                    secao = ui.Section(ui.TextDisplay(texto), accessory=thumbnail)
                else:
                    secao = ui.Section(ui.TextDisplay(texto))
                container.add_item(secao)
                container.add_item(ui.Separator())
            else:
                container.add_item(ui.TextDisplay(f"**{posicao}º — {nome}** • {valor:,} {sufixo}"))

        layout.add_item(container)
        await ctx.send(view=layout)

    except Exception as e:
        await ctx.send(f"❌ Erro ao gerar ranking: `{e}`")

@bot.command(name="missoes")
async def missoes(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author
    garantir_contador(membro.id)
    view = ViewMissoesMenu(membro)
    await ctx.send(view=view)

@bot.command(name="pets")
async def pets(ctx):
    view = ViewPets(ctx.author.id)
    await ctx.send(view=view)

@bot.command(name="minerar")
async def minerar(ctx):
    garantir_stats(ctx.author.id)
    if ctx.author.id in MINERACAO_ATIVAS:
        await ctx.send("❌ Você já está minerando! Termine a mineração atual primeiro.")
        return
    view = ViewMinerarInicio(ctx.author.id, ctx)
    await ctx.send(view=view)

@bot.command(name="inventario")
async def inventario(ctx, membro: discord.Member = None):
    if membro is None:
        membro = ctx.author
    garantir_stats(membro.id)
    view = ViewInventarioMenu(membro)
    await ctx.send(view=view)
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
            title="<:BolsaJoyensIcon:1525729605724405781> Joyens Concedidos!",
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

missao_group = app_commands.Group(name="missao", description="Gerenciamento de missões")

@missao_group.command(name="criar", description="Cria uma nova missão (admin)")
@app_commands.describe(
    nome="Nome da missão",
    descricao="Descrição da missão",
    tipo="permanente ou temporaria",
    condicoes="Condições separadas por vírgula. Ex: trabalhar_total:50 ou null",
    meta="Meta total da missão (deixe 0 para condição null)",
    tipo_recompensa="joyens ou xp",
    quantidade_recompensa="Quantidade da recompensa",
    data_fim="Data de fim para temporárias. Formato: DD/MM/AAAA HH:MM (deixe vazio para permanentes)"
)
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def missao_criar(
    interaction: discord.Interaction,
    nome: str,
    descricao: str,
    tipo: str,
    condicoes: str,
    meta: int,
    tipo_recompensa: str,
    quantidade_recompensa: int,
    data_fim: str = None
):
    tipo = tipo.lower()
    if tipo not in ["permanente", "temporaria"]:
        await interaction.response.send_message("❌ Tipo inválido! Use `permanente` ou `temporaria`.", ephemeral=True)
        return

    if tipo_recompensa not in ["joyens", "xp"]:
        await interaction.response.send_message("❌ Tipo de recompensa inválido! Use `joyens` ou `xp`.", ephemeral=True)
        return

    data_fim_iso = None
    if tipo == "temporaria":
        if not data_fim:
            await interaction.response.send_message("❌ Missões temporárias precisam de uma data de fim!", ephemeral=True)
            return
        try:
            data_fim_iso = datetime.datetime.strptime(data_fim, "%d/%m/%Y %H:%M").isoformat()
        except ValueError:
            await interaction.response.send_message("❌ Formato de data inválido! Use DD/MM/AAAA HH:MM", ephemeral=True)
            return

    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO missoes_customizadas
            (nome, descricao, tipo, condicoes, meta, tipo_recompensa, quantidade_recompensa, data_fim)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nome, descricao, tipo, condicoes, meta if meta > 0 else None, tipo_recompensa, quantidade_recompensa, data_fim_iso))
        con.commit()
        await interaction.response.send_message(f"✅ Missão **{nome}** criada com sucesso!", ephemeral=True)
    except sqlite3.IntegrityError:
        await interaction.response.send_message(f"❌ Já existe uma missão com o nome **{nome}**.", ephemeral=True)
    finally:
        con.close()

@missao_group.command(name="deletar", description="Deleta uma missão (admin)")
@app_commands.describe(nome="Nome exato da missão a deletar")
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def missao_deletar(interaction: discord.Interaction, nome: str):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id FROM missoes_customizadas WHERE LOWER(nome) = LOWER(?)", (nome,))
    resultado = cur.fetchone()
    if not resultado:
        await interaction.response.send_message(f"❌ Missão **{nome}** não encontrada.", ephemeral=True)
        con.close()
        return
    mid = resultado[0]
    cur.execute("DELETE FROM missoes_customizadas_progresso WHERE missao_id = ?", (mid,))
    cur.execute("DELETE FROM missoes_customizadas WHERE id = ?", (mid,))
    con.commit()
    con.close()
    await interaction.response.send_message(f"✅ Missão **{nome}** deletada.", ephemeral=True)

@missao_group.command(name="lista", description="Lista todas as missões criadas")
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def missao_lista(interaction: discord.Interaction):
    missoes = buscar_missoes_customizadas()
    if not missoes:
        await interaction.response.send_message("Nenhuma missão criada ainda.", ephemeral=True)
        return
    embed = discord.Embed(title="📋 Lista de Missões", color=discord.Color.purple())
    for mid, nome, descricao, tipo, condicoes, meta, tipo_recompensa, qtd, data_fim, _ in missoes:
        prazo = datetime.datetime.fromisoformat(data_fim).strftime("%d/%m/%Y às %H:%M") if data_fim else "Sem prazo"
        embed.add_field(
            name=f"{nome} ({tipo})",
            value=f"{descricao}\nCondição: `{condicoes}` | Meta: {meta}\nRecompensa: {qtd} {tipo_recompensa}\nPrazo: {prazo}",
            inline=False
        )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@missao_group.command(name="concluir", description="Conclui manualmente uma missão Null para um membro (admin)")
@app_commands.describe(
    nome="Nome exato da missão",
    membro="Membro que completou a missão"
)
@app_commands.check(lambda interaction: eh_admin(interaction.user.id))
async def missao_concluir(interaction: discord.Interaction, nome: str, membro: discord.Member):
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("SELECT id, nome, tipo_recompensa, quantidade_recompensa FROM missoes_customizadas WHERE LOWER(nome) = LOWER(?)", (nome,))
    resultado = cur.fetchone()
    if not resultado:
        await interaction.response.send_message(f"❌ Missão **{nome}** não encontrada.", ephemeral=True)
        con.close()
        return
    mid, nome_real, tipo_recompensa, qtd_recompensa = resultado

    cur.execute("SELECT completada FROM missoes_customizadas_progresso WHERE usuario_id = ? AND missao_id = ?",
                (str(membro.id), mid))
    prog = cur.fetchone()
    if prog and prog[0]:
        await interaction.response.send_message(f"❌ {membro.display_name} já completou esta missão!", ephemeral=True)
        con.close()
        return
    con.close()

    canal = bot.get_channel(CANAL_NOTIFICACOES_ID)
    await concluir_missao_customizada(str(membro.id), mid, nome_real, tipo_recompensa, qtd_recompensa, canal, interaction)
    await interaction.response.send_message(f"✅ Missão **{nome_real}** concluída para {membro.mention}!", ephemeral=True)

bot.tree.add_command(missao_group)

bot.tree.add_command(rotacao_group)

bot.tree.add_command(categoria_group)

bot.tree.add_command(level_group)

bot.tree.add_command(admin_group)

bot.tree.add_command(banner_group)

bot.tree.add_command(conquista_group)

# ============================================================
# EVENTOS DE CALL E MENSAGENS
# ============================================================

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    garantir_contador(member.id)
    agora = datetime.datetime.now().isoformat()
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    if before.channel is None and after.channel is not None:
        cur.execute("UPDATE contadores_usuarios SET call_inicio = ? WHERE usuario_id = ?",
                    (agora, str(member.id)))
        con.commit()

    elif before.channel is not None and after.channel is None:
        cur.execute("SELECT call_inicio FROM contadores_usuarios WHERE usuario_id = ?",
                    (str(member.id),))
        resultado = cur.fetchone()
        if resultado and resultado[0]:
            inicio = datetime.datetime.fromisoformat(resultado[0])
            minutos = int((datetime.datetime.now() - inicio).total_seconds() // 60)
            if minutos > 0:
                cur.execute("""
                    UPDATE contadores_usuarios SET
                        call_semana = call_semana + ?,
                        call_total = call_total + ?,
                        call_inicio = NULL
                    WHERE usuario_id = ?
                """, (minutos, minutos, str(member.id)))
                con.commit()
                await verificar_missoes_usuario(str(member.id))

    con.close()

@bot.event
async def on_message(message):
    if message.author.bot:
        await bot.process_commands(message)
        return
    garantir_contador(message.author.id)
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute("""
        UPDATE contadores_usuarios SET
            msg_semana = msg_semana + 1,
            msg_total = msg_total + 1
        WHERE usuario_id = ?
    """, (str(message.author.id),))
    con.commit()
    con.close()
    await verificar_missoes_usuario(str(message.author.id))
    await bot.process_commands(message)

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
