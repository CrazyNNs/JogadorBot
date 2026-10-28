# -*- coding: utf-8 -*-
"""Evento de Halloween do Sakurai — módulo separado para bot.py.

Registre com:
    import evento_halloween
    evento_halloween.configurar_halloween(bot, globals())
antes de bot.run(TOKEN).
"""

import asyncio
import contextlib
import datetime
import os
import random
import sqlite3

import discord
from discord import ui

HALLOWEEN_ATIVO = True
FUSO = datetime.timezone(datetime.timedelta(hours=-3))

# Os nomes precisam existir exatamente assim no catálogo de banners do bot.
HALLOWEEN_BANNERS = {
    "aboboras": "Abóboras Animadas",
    "morcegos": "Morcegos",
    "sakura": "Sakura Sombria",
}

HALLOWEEN_CONQUISTAS = {
    "Halloween 26": ("🎃", "Participou das aventuras de Halloween 2026 do Sakurai."),
    "Criatura da Noite": ("🌙", "Uma criatura que prosperou durante a noite de Halloween."),
    "Guardião das Cerejeiras Sombria": ("🌸", "Protegeu as cerejeiras durante o Halloween sombrio."),
    "Fantasminha Camarada": ("👻", "Um fantasminha simpático que acompanha a comunidade."),
    "Fome de Sangue": ("🩸", "Um título temático conquistado no evento de Halloween."),
}

HALLOWEEN_LOJA = {
    "banner_aboboras": {"nome": "Abóboras Animadas", "tipo": "banner", "alvo": HALLOWEEN_BANNERS["aboboras"], "preco": 30, "emoji": "🎃", "descricao": "Abobóras atrás de doces... ou travessuras."},
    "banner_morcegos": {"nome": "Morcegos", "tipo": "banner", "alvo": HALLOWEEN_BANNERS["morcegos"], "preco": 30, "emoji": "🦇", "descricao": "Melhor manter o pescoço protegido... eles estão com fome."},
    "banner_sakura": {"nome": "Sakura Sombria", "tipo": "banner", "alvo": HALLOWEEN_BANNERS["sakura"], "preco": 70, "emoji": "🌸", "descricao": "Suas pétalas possuem escuridão."},
    "titulo_fantasma": {"nome": "Fantasminha Camarada", "tipo": "conquista", "alvo": "Fantasminha Camarada", "preco": 20, "emoji": "👻", "descricao": "Desbloqueia a conquista: Fantasminha Camarada."},
    "titulo_sangue": {"nome": "Fome de Sangue", "tipo": "conquista", "alvo": "Fome de Sangue", "preco": 35, "emoji": "🩸", "descricao": "Desbloqueia a conquista: Fome de Sangue."},
    "pet_dullahan": {"nome": "Cão Dullahan", "tipo": "pet", "alvo": "Cão Dullahan", "preco": 120, "emoji": "🐕‍🦺", "descricao": "O amigo do homem, ás vezes, perde a cabeça por ai."},
}

HALLOWEEN_CAIXAS = {
    "assombrada": {"nome": "Caixa Assombrada", "emoji": "🎃", "preco_chaves": 1, "imagem": "caixaassombrada.png", "descricao": "Doces | 1 Pétala | Banner Exclusivo | Conquista exclusiva | Itens aleatórios."},
    "sakura": {"nome": "Caixa da Sakura Sombria", "emoji": "🌸", "preco_chaves": 2, "imagem": "caixasakura.png", "descricao": "Mais doces | 2-3 Pétalas | Banners Exclusivos | Conquistas exclusivas."},
}

HALLOWEEN_DOCES_CAIXA_ASSOMBRADA = (12, 22)
HALLOWEEN_DOCES_CAIXA_SAKURA = (30, 45)
PRECO_REDE_FANTASMAS = 5000
DURABILIDADE_REDE_FANTASMAS = 20
DURACAO_CACA_SEGUNDOS = 300
INTERVALO_CACA_SEGUNDOS = 10
PAUSA_CACA_SEGUNDOS = 600

HALLOWEEN_MISSOES = {
    "diario": {"nome": "📅 Visita à Cidade Assombrada", "descricao": "Use !diario uma vez depois de iniciar sua participação no evento.", "contador": "diario_total", "meta": 1, "chaves": 1},
    "mensagens": {"nome": "💬 Vozes na Névoa", "descricao": "Envie 40 mensagens depois de abrir o painel do evento.", "contador": "msg_total", "meta": 40, "chaves": 2},
    "trabalho": {"nome": "🧹 Trabalho Sob a Lua", "descricao": "Trabalhe 20 vezes depois de iniciar sua participação no evento.", "contador": "trabalhar_total", "meta": 20, "chaves": 2},
}

CENARIOS_FANTASMAS = [
    "🌫️ A névoa se adensa entre as árvores. Algo pequeno atravessa o caminho!",
    "👻 Um fantasma aparece perto de uma lápide e tenta escapar da sua rede.",
    "🕯️ As lanternas piscam. Você ouve risadinhas vindo de uma casa abandonada.",
    "🦇 Um bando de morcegos passa por cima de você; uma sombra espectral surge logo atrás.",
    "✨ A rede brilha por um instante e um fantasma é capturado!",
    "🌸 Pétalas escuras giram no ar enquanto uma silhueta transparente se esconde na névoa.",
    "🎃 Uma abóbora iluminada revela pegadas flutuando sobre o chão.",
    "👀 Você vê dois olhos brilhantes entre as árvores — e então um fantasma dispara pelo caminho!",
]


def _conectar():
    con = sqlite3.connect("jogadorbot.db", timeout=15)
    con.execute("PRAGMA busy_timeout=15000")
    return con


@contextlib.contextmanager
def _db():
    """Contexto SQLite que também fecha a conexão (with sqlite3.connect não fecha)."""
    con = _conectar()
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _criar_tabelas():
    con = _conectar()
    try:
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS halloween_usuarios (
            usuario_id TEXT PRIMARY KEY, doces INTEGER NOT NULL DEFAULT 0,
            base_mensagens INTEGER NOT NULL DEFAULT 0, base_trabalho INTEGER NOT NULL DEFAULT 0,
            base_diario INTEGER NOT NULL DEFAULT 0, iniciou_em TEXT NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS halloween_missoes_usuarios (
            usuario_id TEXT NOT NULL, missao_id TEXT NOT NULL, concluida INTEGER NOT NULL DEFAULT 0,
            concluida_em TEXT, PRIMARY KEY (usuario_id, missao_id))""")
        cur.execute("""CREATE TABLE IF NOT EXISTS halloween_rede_fantasmas (
            usuario_id TEXT PRIMARY KEY, durabilidade INTEGER NOT NULL DEFAULT 0)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS halloween_caca_estado (
            usuario_id TEXT PRIMARY KEY, cooldown_ate TEXT, ultimo_resultado INTEGER NOT NULL DEFAULT 0)""")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS halloween_fantasmas (
                usuario_id TEXT PRIMARY KEY,
                quantidade INTEGER NOT NULL DEFAULT 0
            )
        """)
        con.commit()
    finally:
        con.close()


def _contador(usuario_id, coluna):
    permitidas = {"msg_total", "trabalhar_total", "diario_total"}
    if coluna not in permitidas:
        return 0
    con = _conectar()
    try:
        cur = con.cursor()
        cur.execute(f"SELECT {coluna} FROM contadores_usuarios WHERE usuario_id = ?", (str(usuario_id),))
        row = cur.fetchone()
        return int(row[0] or 0) if row else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        con.close()


def _garantir_usuario(usuario_id):
    uid = str(usuario_id)
    con = _conectar()
    try:
        cur = con.cursor()
        cur.execute("SELECT 1 FROM halloween_usuarios WHERE usuario_id = ?", (uid,))
        if not cur.fetchone():
            cur.execute("SELECT msg_total, trabalhar_total, diario_total FROM contadores_usuarios WHERE usuario_id = ?", (uid,))
            row = cur.fetchone() or (0, 0, 0)
            cur.execute("INSERT INTO halloween_usuarios (usuario_id, base_mensagens, base_trabalho, base_diario, iniciou_em) VALUES (?, ?, ?, ?, ?)",
                        (uid, int(row[0] or 0), int(row[1] or 0), int(row[2] or 0), datetime.datetime.now(FUSO).isoformat()))
        con.commit()
    finally:
        con.close()


def _doces(usuario_id):
    _garantir_usuario(usuario_id)
    con = _conectar()
    try:
        row = con.execute("SELECT doces FROM halloween_usuarios WHERE usuario_id = ?", (str(usuario_id),)).fetchone()
        return int(row[0] or 0) if row else 0
    finally:
        con.close()


def _adicionar_doces(usuario_id, qtd):
    _garantir_usuario(usuario_id)
    with _db() as con:
        con.execute("UPDATE halloween_usuarios SET doces = doces + ? WHERE usuario_id = ?", (int(qtd), str(usuario_id)))


def _gastar_doces(usuario_id, qtd):
    _garantir_usuario(usuario_id)
    with _db() as con:
        cur = con.execute("UPDATE halloween_usuarios SET doces = doces - ? WHERE usuario_id = ? AND doces >= ?", (int(qtd), str(usuario_id), int(qtd)))
        return cur.rowcount == 1
        
def _fantasmas_capturados(usuario_id):
    with _db() as con:
        row = con.execute(
            "SELECT quantidade FROM halloween_fantasmas WHERE usuario_id = ?",
            (str(usuario_id),)
        ).fetchone()

        return int(row[0]) if row else 0


def _registrar_fantasma(usuario_id):
    with _db() as con:
        con.execute("""
            INSERT INTO halloween_fantasmas (usuario_id, quantidade)
            VALUES (?, 1)
            ON CONFLICT(usuario_id)
            DO UPDATE SET quantidade = quantidade + 1
        """, (str(usuario_id),))


def _adoçar_fantasmas(usuario_id):
    _garantir_usuario(usuario_id)

    with _db() as con:
        # Impede duas conversões simultâneas de usarem os mesmos fantasmas.
        con.execute("BEGIN IMMEDIATE")

        row = con.execute(
            "SELECT quantidade FROM halloween_fantasmas WHERE usuario_id = ?",
            (str(usuario_id),)
        ).fetchone()

        quantidade = int(row[0]) if row else 0

        if quantidade <= 0:
            return 0

        # Consome os fantasmas e adiciona a mesma quantidade de doces.
        con.execute(
            "UPDATE halloween_fantasmas SET quantidade = 0 WHERE usuario_id = ?",
            (str(usuario_id),)
        )

        con.execute(
            "UPDATE halloween_usuarios SET doces = doces + ? WHERE usuario_id = ?",
            (quantidade, str(usuario_id))
        )

        return quantidade

def _conquista(usuario_id, nome):
    emoji, descricao = HALLOWEEN_CONQUISTAS.get(nome, ("🎃", "Recompensa especial do evento de Halloween."))
    with _db() as con:
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO conquistas (nome, descricao, emoji) VALUES (?, ?, ?)", (nome, descricao, emoji))
        row = cur.execute("SELECT id FROM conquistas WHERE LOWER(nome) = LOWER(?)", (nome,)).fetchone()
        if not row:
            return False
        cid = row[0]
        if cur.execute("SELECT 1 FROM conquistas_usuarios WHERE usuario_id = ? AND conquista_id = ?", (str(usuario_id), cid)).fetchone():
            return False
        cur.execute("INSERT INTO conquistas_usuarios (usuario_id, conquista_id, data) VALUES (?, ?, ?)",
                    (str(usuario_id), cid, datetime.datetime.now(FUSO).strftime("%d/%m/%Y")))
        return True


def _dar_banner(usuario_id, nome):
    with _db() as con:
        row = con.execute("SELECT id FROM banners WHERE LOWER(nome) = LOWER(?)", (nome,)).fetchone()
        if not row:
            return False, "não encontrado"
        if con.execute("SELECT 1 FROM banners_usuarios WHERE usuario_id = ? AND banner_id = ?", (str(usuario_id), row[0])).fetchone():
            return False, "duplicado"
        con.execute("INSERT OR IGNORE INTO banners_usuarios (usuario_id, banner_id) VALUES (?, ?)", (str(usuario_id), row[0]))
        return True, "concedido"


def _dar_pet(usuario_id):
    agora = datetime.datetime.now(FUSO).isoformat()
    with _db() as con:
        total = con.execute("SELECT COUNT(*) FROM pets WHERE usuario_id = ? AND disponivel_adocao = 0", (str(usuario_id),)).fetchone()[0]
        if total >= 3:
            return False, "Você já atingiu o limite de 3 pets."
        existe = con.execute("SELECT 1 FROM pets WHERE usuario_id = ? AND (LOWER(nome) = LOWER('Cão Dullahan') OR LOWER(raca) = LOWER('Cão Dullahan')) AND disponivel_adocao = 0", (str(usuario_id),)).fetchone()
        if existe:
            return False, "Você já possui o Cão Dullahan."
        con.execute("INSERT INTO pets (usuario_id, especie, raca, nome, fome, energia, higiene, felicidade, hp, criado_em, ultima_atualizacao, disponivel_adocao) VALUES (?, 'Cachorros', 'Cão Dullahan', 'Cão Dullahan', 100, 100, 100, 100, 100, ?, ?, 0)", (str(usuario_id), agora, agora))
        return True, "concedido"


def _comprar(ns, usuario_id, item_id):
    if item_id == "rede_fantasmas":
        atual = _rede_durabilidade(usuario_id)
        if atual > 0:
            return False, f"Você já possui uma rede com **{atual}/{DURABILIDADE_REDE_FANTASMAS}** capturas restantes."
        with _db() as con:
            cur = con.execute("UPDATE economia SET joyens = joyens - ? WHERE usuario_id = ? AND joyens >= ?", (PRECO_REDE_FANTASMAS, str(usuario_id), PRECO_REDE_FANTASMAS))
            if cur.rowcount != 1:
                return False, f"Você precisa de **{PRECO_REDE_FANTASMAS:,} Joyens** para comprar uma Rede de Fantasmas."
        with _db() as con:
            con.execute("INSERT INTO halloween_rede_fantasmas (usuario_id, durabilidade) VALUES (?, ?) ON CONFLICT(usuario_id) DO UPDATE SET durabilidade = excluded.durabilidade", (str(usuario_id), DURABILIDADE_REDE_FANTASMAS))
        return True, f"Rede de Fantasmas comprada! Durabilidade: **{DURABILIDADE_REDE_FANTASMAS} fantasmas**."

    item = HALLOWEEN_LOJA.get(item_id)
    if not item:
        return False, "Esse item não existe."
    if item["tipo"] == "banner":
        with _db() as con:
            row = con.execute("SELECT id FROM banners WHERE LOWER(nome) = LOWER(?)", (item["alvo"],)).fetchone()
            if not row:
                return False, f"O banner **{item['alvo']}** não está cadastrado. Confira HALLOWEEN_BANNERS."
            if con.execute("SELECT 1 FROM banners_usuarios WHERE usuario_id = ? AND banner_id = ?", (str(usuario_id), row[0])).fetchone():
                return False, "Você já possui esse banner."
    elif item["tipo"] == "conquista":
        with _db() as con:
            row = con.execute("SELECT id FROM conquistas WHERE LOWER(nome) = LOWER(?)", (item["alvo"],)).fetchone()
            if row and con.execute("SELECT 1 FROM conquistas_usuarios WHERE usuario_id = ? AND conquista_id = ?", (str(usuario_id), row[0])).fetchone():
                return False, "Você já possui essa conquista/título."
    elif item["tipo"] == "pet":
        with _db() as con:
            total = con.execute("SELECT COUNT(*) FROM pets WHERE usuario_id = ? AND disponivel_adocao = 0", (str(usuario_id),)).fetchone()[0]
            if total >= 3:
                return False, "Você já atingiu o limite de 3 pets."
            if con.execute("SELECT 1 FROM pets WHERE usuario_id = ? AND LOWER(nome) = LOWER('Cão Dullahan') AND disponivel_adocao = 0", (str(usuario_id),)).fetchone():
                return False, "Você já possui o Cão Dullahan."

    # Gasto atômico em Joyens ou doces para evitar saldo negativo por cliques simultâneos.
    with _db() as con:
        cur = con.execute("UPDATE halloween_usuarios SET doces = doces - ? WHERE usuario_id = ? AND doces >= ?", (item["preco"], str(usuario_id), item["preco"]))
        if cur.rowcount != 1:
            return False, "Saldo insuficiente de doces." 

    if item["tipo"] == "banner":
        ok, motivo = _dar_banner(usuario_id, item["alvo"])
        if not ok:
            _adicionar_doces(usuario_id, item["preco"])
            return False, "Não foi possível entregar o banner; os doces foram devolvidos."
    elif item["tipo"] == "conquista":
        if not _conquista(usuario_id, item["alvo"]):
            _adicionar_doces(usuario_id, item["preco"])
            return False, "Você já possui essa conquista ou não foi possível entregá-la; os doces foram devolvidos."
    elif item["tipo"] == "pet":
        ok, motivo = _dar_pet(usuario_id)
        if not ok:
            _adicionar_doces(usuario_id, item["preco"])
            return False, f"{motivo} Seus doces foram devolvidos."
    return True, f"Você adquiriu **{item['nome']}**!"


def _chaves_gastar(usuario_id, qtd):
    with _db() as con:
        cur = con.execute("UPDATE chaves_usuario SET quantidade = quantidade - ? WHERE usuario_id = ? AND quantidade >= ?", (int(qtd), str(usuario_id), int(qtd)))
        return cur.rowcount == 1


def _loot_caixa(ns, usuario_id, tipo):
    out = []

    if tipo == "assombrada":
        if random.random() < 0.22:
            nome = random.choice([
                HALLOWEEN_BANNERS["aboboras"],
                HALLOWEEN_BANNERS["morcegos"]
            ])

            ok, motivo = _dar_banner(usuario_id, nome)

            if ok:
                out.append(f"🖼️ Banner **{nome}**")
            elif motivo == "duplicado":
                out.append(f"🖼️ Você já possuía o banner **{nome}**.")
            else:
                out.append(f"⚠️ Banner **{nome}** não está cadastrado.")

        if random.random() < 0.16:
            if _conquista(usuario_id, "Halloween 26"):
                out.append("🏆 Conquista **Halloween 26**")
            else:
                out.append("🏆 Você já possuía a conquista **Halloween 26**.")

        if random.random() < 0.38:
            try:
                item = ns["sortear_item_aleatorio_mineracao_petshop_sync"](
                    usuario_id
                )
                out.append(f"🎁 Item aleatório: {item}")
            except Exception as e:
                print(f"[Halloween] Erro no item aleatório: {e}")
                out.append("⚠️ Não foi possível entregar o item aleatório.")

    else:
        petalas = random.randint(2, 3)
        ns["adicionar_petalas"](usuario_id, petalas)
        out.append(f"🌸 **+{petalas} Pétalas**")

        if random.random() < 0.38:
            ok, motivo = _dar_banner(
                usuario_id,
                HALLOWEEN_BANNERS["sakura"]
            )

            if ok:
                out.append(
                    f"🖼️ Banner raro **{HALLOWEEN_BANNERS['sakura']}**"
                )
            elif motivo == "duplicado":
                out.append(
                    f"🖼️ Você já possuía o banner "
                    f"**{HALLOWEEN_BANNERS['sakura']}**."
                )
            else:
                out.append("⚠️ O banner Sakura Sombria não está cadastrado.")

        for nome, chance in [
            ("Criatura da Noite", 0.30),
            ("Guardião das Cerejeiras Sombria", 0.18)
        ]:
            if random.random() < chance:
                if _conquista(usuario_id, nome):
                    out.append(f"🏆 Conquista **{nome}**")
                else:
                    out.append(f"🏆 Você já possuía a conquista **{nome}**.")

        if random.random() < 0.25:
            try:
                item = ns["sortear_item_aleatorio_mineracao_petshop_sync"](
                    usuario_id
                )
                out.append(f"🎁 Item aleatório: {item}")
            except Exception as e:
                print(f"[Halloween] Erro no item aleatório: {e}")
                out.append("⚠️ Não foi possível entregar o item aleatório.")

    return out

def _status_missoes(usuario_id):
    _garantir_usuario(usuario_id)
    with _db() as con:
        bases = con.execute("SELECT base_mensagens, base_trabalho, base_diario FROM halloween_usuarios WHERE usuario_id = ?", (str(usuario_id),)).fetchone() or (0, 0, 0)
        colunas = {"msg_total": bases[0], "trabalhar_total": bases[1], "diario_total": bases[2]}
        saida = []
        for mid, m in HALLOWEEN_MISSOES.items():
            atual = _contador(usuario_id, m["contador"])
            progresso = max(0, atual - int(colunas[m["contador"]] or 0))
            row = con.execute("SELECT concluida FROM halloween_missoes_usuarios WHERE usuario_id = ? AND missao_id = ?", (str(usuario_id), mid)).fetchone()
            saida.append((mid, m, progresso, bool(row and row[0])))
        return saida


def _resgatar_missao(usuario_id, missao_id):
    missao = HALLOWEEN_MISSOES.get(missao_id)
    if not missao: return False, "Missão não encontrada."
    estados = {mid: (m, prog, feita) for mid, m, prog, feita in _status_missoes(usuario_id)}
    _, progresso, concluida = estados[missao_id]
    if concluida: return False, "Essa missão já foi resgatada."
    if progresso < missao["meta"]: return False, "Você ainda não concluiu essa missão."
    with _db() as con:
        cur = con.execute("INSERT OR IGNORE INTO halloween_missoes_usuarios (usuario_id, missao_id, concluida, concluida_em) VALUES (?, ?, 1, ?)", (str(usuario_id), missao_id, datetime.datetime.now(FUSO).isoformat()))
        if cur.rowcount != 1: return False, "Essa missão já foi resgatada."
    return True, missao["chaves"]


def _rede_durabilidade(uid):
    with _db() as con:
        row = con.execute("SELECT durabilidade FROM halloween_rede_fantasmas WHERE usuario_id = ?", (str(uid),)).fetchone()
        return int(row[0]) if row else 0


def _gastar_durabilidade_rede(uid):
    with _db() as con:
        cur = con.execute("UPDATE halloween_rede_fantasmas SET durabilidade = durabilidade - 1 WHERE usuario_id = ? AND durabilidade > 0", (str(uid),))
        row = con.execute("SELECT durabilidade FROM halloween_rede_fantasmas WHERE usuario_id = ?", (str(uid),)).fetchone()
        return cur.rowcount == 1, int(row[0]) if row else 0


def _cooldown_ate(uid):
    with _db() as con:
        row = con.execute("SELECT cooldown_ate FROM halloween_caca_estado WHERE usuario_id = ?", (str(uid),)).fetchone()
        if not row or not row[0]: return None
        try: return datetime.datetime.fromisoformat(row[0])
        except ValueError: return None


def _definir_cooldown(uid, segundos, capturados):
    ate = (datetime.datetime.now(FUSO) + datetime.timedelta(seconds=segundos)).isoformat()
    with _db() as con:
        con.execute("INSERT INTO halloween_caca_estado (usuario_id, cooldown_ate, ultimo_resultado) VALUES (?, ?, ?) ON CONFLICT(usuario_id) DO UPDATE SET cooldown_ate = excluded.cooldown_ate, ultimo_resultado = excluded.ultimo_resultado", (str(uid), ate, int(capturados)))


def _saldo_joyens(uid):
    with _db() as con:
        row = con.execute("SELECT joyens FROM economia WHERE usuario_id = ?", (str(uid),)).fetchone()
        return int(row[0] or 0) if row else 0


# Estado das caçadas ativas vive em memória; cooldown e durabilidade são persistidos no SQLite.
_CACAS_ATIVAS = {}
_MAIN_MESSAGES = {}


def configurar_halloween(bot, ns):
    _criar_tabelas()

    class HalloweenView(ui.LayoutView):
        def __init__(self, uid, timeout=300):
            super().__init__(timeout=timeout)
            self.uid = int(uid)

        async def interaction_check(self, interaction):
            if interaction.user.id != self.uid:
                await interaction.response.send_message("Este painel pertence a outra pessoa. Use `!halloween` para abrir o seu.", ephemeral=True)
                return False
            if not HALLOWEEN_ATIVO:
                await interaction.response.send_message("🎃 O evento de Halloween está encerrado.", ephemeral=True)
                return False
            return True

    def _container():
        c = ui.Container()
        c.accent_color = discord.Colour.dark_purple()
        return c

    def _btn(label, callback, style=discord.ButtonStyle.primary, emoji=None, disabled=False):
        b = ui.Button(label=label, style=style, emoji=emoji, disabled=disabled)
        b.callback = callback
        return b

    def _main_view(uid):
        view = HalloweenView(uid)
        c = _container()
        keys = ns["buscar_chaves"](uid)
        sweets = _doces(uid)
        petals = ns["buscar_petalas"](uid)
        net = _rede_durabilidade(uid)
        cooldown = _cooldown_ate(uid)
        now = datetime.datetime.now(FUSO)
        active = uid in _CACAS_ATIVAS
        cooling = bool(cooldown and cooldown > now)
        if active:
            hunt_label, hunt_disabled = "Caçar Fantasmas (em andamento)", True
        elif cooling:
            secs = max(0, int((cooldown - now).total_seconds()))
            hunt_label, hunt_disabled = f"Caçar Fantasmas ({secs // 60}:{secs % 60:02d})", True
        else:
            hunt_label, hunt_disabled = "Caçar Fantasmas", net <= 0
        c.add_item(ui.TextDisplay("# 🎃 Halloween do Sakurai\n## Festival das Pétalas Perdidas\nA névoa roxa cobre a cidade. Complete missões, capture fantasmas e troque doces por lembranças exclusivas."))
        c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
        fantasmas = _fantasmas_capturados(uid)

        c.add_item(ui.TextDisplay(
            f"### 💰 Seus recursos\n"
            f"🗝️ **Chaves:** {keys}\n"
            f"🍬 **Doces:** {sweets}\n"
            f"🌸 **Pétalas:** {petals}\n"
            f"🕸️ **Durabilidade da rede:** "
            f"{net}/{DURABILIDADE_REDE_FANTASMAS}\n"
            f"💵 **Joyens:** {_saldo_joyens(uid):,}"
        ))

        c.add_item(ui.Separator())

        texto_fantasmas = ui.TextDisplay(
            f"👻 **Fantasmas Capturados:** {fantasmas}"
        )

        if fantasmas > 0:
            botao_adocar = _btn(
                "Adoçar",
                lambda i: _adoçar(i, uid),
                style=discord.ButtonStyle.success,
                emoji="🍬"
            )

            c.add_item(
                ui.Section(
                    texto_fantasmas,
                    accessory=botao_adocar
                )
            )
        else:
            c.add_item(texto_fantasmas)

        c.add_item(ui.Separator())
        row = ui.ActionRow()
        row.add_item(_btn("Hallobox", lambda i: _open_hallobox(i, uid), emoji="🎁"))
        row.add_item(_btn("Lembrancinhas", lambda i: _open_shop(i, uid), style=discord.ButtonStyle.success, emoji="🛍️"))
        row.add_item(_btn("Missões", lambda i: _open_missions(i, uid), style=discord.ButtonStyle.secondary, emoji="🎃"))
        c.add_item(row)
        huntrow = ui.ActionRow()
        huntrow.add_item(_btn(hunt_label, lambda i: _start_hunt(i, uid), style=discord.ButtonStyle.primary, emoji="👻", disabled=hunt_disabled))
        c.add_item(huntrow)
        if net <= 0:
            c.add_item(ui.TextDisplay("-# Você precisa comprar uma Rede de Fantasmas por 5.000 Joyens para iniciar ou continuar a caça."))
        view.add_item(c)
        return view

    async def _open_main(interaction, uid):
        await interaction.response.edit_message(view=_main_view(uid), attachments=[])
        
    async def _adoçar(interaction, uid):
        quantidade = await asyncio.to_thread(
            _adoçar_fantasmas,
            uid
        )

        if quantidade <= 0:
            await interaction.response.send_message(
                "👻 Você não possui fantasmas disponíveis para converter.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"🍬 Você converteu **{quantidade} fantasma(s)** "
            f"em **{quantidade} doce(s)**!",
            ephemeral=True
        )

        # Atualiza o painel e remove o botão se não houver fantasmas restantes.
        try:
            await interaction.message.edit(
                view=_main_view(uid),
                attachments=[]
            )
        except (discord.NotFound, discord.HTTPException) as e:
            print(f"[Halloween] Erro ao atualizar o painel após adoçar: {e}")
            
    async def _open_hallobox(interaction, uid):
        view = HalloweenHallobox(uid)
        files = view.arquivos()
        await interaction.response.edit_message(view=view, attachments=files)

    async def _open_shop(interaction, uid):
        await interaction.response.edit_message(view=HalloweenLoja(uid), attachments=[])

    async def _open_missions(interaction, uid):
        await interaction.response.edit_message(view=HalloweenMissoes(uid), attachments=[])

    class HalloweenHallobox(HalloweenView):
        def __init__(self, uid):
            super().__init__(uid)
            self.montar()

        def arquivos(self):
            return [discord.File(d["imagem"], filename=d["imagem"]) for d in HALLOWEEN_CAIXAS.values() if os.path.isfile(d["imagem"])]

        def montar(self):
            c = _container()
            c.add_item(ui.TextDisplay(f"# 🎁 Hallobox\n🗝️ **Suas Chaves:** {ns['buscar_chaves'](self.uid)}\nEscolha uma caixa para abrir. Cada compra consome a quantidade de Chaves indicada."))
            c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
            for tipo in ("assombrada", "sakura"):
                d = HALLOWEEN_CAIXAS[tipo]
                texto = f"### {d['emoji']} {d['nome']}\n{d['descricao']}\n\n🗝️ **Custo: {d['preco_chaves']} Chave(s)**"
                img = ui.Thumbnail(f"attachment://{d['imagem']}") if os.path.isfile(d["imagem"]) else None
                if img:
                    c.add_item(ui.Section(ui.TextDisplay(texto), accessory=img))
                else:
                    c.add_item(ui.TextDisplay(texto + f"\n-# Coloque `{d['imagem']}` ao lado de bot.py para mostrar a thumbnail."))
                row = ui.ActionRow()
                b = _btn("Comprar", lambda i, t=tipo: self.comprar(i, t), style=discord.ButtonStyle.success)
                row.add_item(b)
                c.add_item(row)
                c.add_item(ui.Separator())
            row = ui.ActionRow()
            row.add_item(_btn("Voltar", lambda i: _open_main(i, self.uid), style=discord.ButtonStyle.secondary, emoji="↩️"))
            c.add_item(row)
            self.add_item(c)

        async def comprar(self, interaction, tipo):
            qtd = HALLOWEEN_CAIXAS[tipo]["preco_chaves"]
            consumidas = await asyncio.to_thread(_chaves_gastar, self.uid, qtd)
            if not consumidas:
                await interaction.response.send_message(f"Você precisa de **{qtd} Chave(s)** para comprar essa caixa.", ephemeral=True)
                return
            try:
                recompensas = await asyncio.to_thread(_loot_caixa, ns, self.uid, tipo)
            except Exception as e:
                print(f"[Halloween] Erro abrindo caixa: {e}")
                # Não reembolsa automaticamente porque uma recompensa pode já ter sido gravada.
                await interaction.response.send_message("Ocorreu um erro ao abrir a caixa. Avise a administração.", ephemeral=True)
                return
            result = ui.LayoutView(timeout=90)
            cont = _container()
            cont.add_item(ui.TextDisplay(f"# {HALLOWEEN_CAIXAS[tipo]['emoji']} Caixa aberta!\n" + "\n".join(f"• {x}" for x in recompensas) + f"\n\n🗝️ Chaves restantes: {ns['buscar_chaves'](self.uid)}"))
            cont.add_item(ui.ActionRow(_btn("Fechar", lambda i: i.response.edit_message(view=None), style=discord.ButtonStyle.secondary)))
            result.add_item(cont)
            await interaction.response.send_message(view=result, ephemeral=True)
            self.montar()
            await interaction.message.edit(view=self, attachments=self.arquivos())

    class HalloweenLoja(HalloweenView):
        def __init__(self, uid):
            super().__init__(uid)
            self.montar()

        def montar(self):
            c = _container()
            c.add_item(ui.TextDisplay(f"# 🛍️ Lembrancinhas — Bazar da Lua Roxa\n🍬 **Seus doces:** {_doces(self.uid)}\nCada item permanente só pode ser adquirido uma vez. A Rede de Fantasmas é comprada com Joyens e pode ser reposta quando quebrar."))
            c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
            for item_id, item in HALLOWEEN_LOJA.items():
                texto = f"{item['emoji']} **{item['nome']}** — 🍬 {item['preco']} doces\n{item['descricao']}"
                botao = _btn("Comprar", lambda i, iid=item_id: self.comprar(i, iid), style=discord.ButtonStyle.success)
                c.add_item(ui.Section(ui.TextDisplay(texto), accessory=botao))
                c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            texto_rede = f"👻 **Rede de Fantasmas** — <:JoyensIcon:1536254492797050880> {PRECO_REDE_FANTASMAS:,} Joyens\nDurabilidade: {DURABILIDADE_REDE_FANTASMAS} fantasmas capturados. Quebra após a 20ª captura."
            botao_rede = _btn("Comprar", lambda i: self.comprar_rede(i), style=discord.ButtonStyle.success)
            c.add_item(ui.Section(ui.TextDisplay(texto_rede), accessory=botao_rede))
            c.add_item(ui.Separator())
            c.add_item(ui.ActionRow(_btn("Voltar", lambda i: _open_main(i, self.uid), style=discord.ButtonStyle.secondary, emoji="↩️")))
            self.add_item(c)

        async def comprar(self, interaction, item_id):
            ok, texto = await asyncio.to_thread(_comprar, ns, self.uid, item_id)
            await interaction.response.send_message(("✅ " if ok else "⚠️ ") + texto, ephemeral=True)
            if ok:
                self.montar()
                await interaction.message.edit(view=self, attachments=[])

        async def comprar_rede(self, interaction):
            ok, texto = await asyncio.to_thread(_comprar, ns, self.uid, "rede_fantasmas")
            if not ok:
                await interaction.response.send_message("⚠️ " + texto, ephemeral=True)
                return
            # Se a rede quebrou durante uma caçada, ela continua do mesmo ponto.
            sessao = _CACAS_ATIVAS.get(self.uid)
            if sessao and sessao.get("pausada_rede"):
                sessao["pausada_rede"] = False
                sessao["eventos"].append("🕸️ Você comprou uma nova rede! A caçada foi retomada.")
                sessao["task"] = asyncio.create_task(_rodar_caca(self.uid))
            await interaction.response.send_message("✅ " + texto, ephemeral=True)
            self.montar()
            await interaction.message.edit(view=self, attachments=[])

    class HalloweenMissoes(HalloweenView):
        def __init__(self, uid):
            super().__init__(uid)
            self.montar()

        def montar(self):
            c = _container()
            c.add_item(ui.TextDisplay("# 🗝️ Missões — Chaves Perdidas\nComplete os objetivos e resgate as Chaves. O progresso é contado desde a primeira vez que abriu o evento."))
            c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
            for mid, m, progresso, concluida in _status_missoes(self.uid):
                status = "✅ Resgatada" if concluida else ("🎁 Pronta para resgatar" if progresso >= m["meta"] else "⏳ Em andamento")
                texto = f"**{m['nome']}**\n{m['descricao']}\nProgresso: **{min(progresso, m['meta'])}/{m['meta']}** · Recompensa: 🗝️ **{m['chaves']}** · {status}"
                row = ui.ActionRow()
                row.add_item(_btn("Resgatar", lambda i, miss=mid: self.resgatar(i, miss), style=discord.ButtonStyle.success, disabled=concluida or progresso < m["meta"]))
                c.add_item(ui.Section(ui.TextDisplay(texto), accessory=row.children[0]))
                c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
            c.add_item(ui.ActionRow(_btn("Voltar", lambda i: _open_main(i, self.uid), style=discord.ButtonStyle.secondary, emoji="↩️")))
            self.add_item(c)

        async def resgatar(self, interaction, mid):
            ok, valor = _resgatar_missao(self.uid, mid)
            if ok:
                await asyncio.to_thread(ns["adicionar_chaves"], self.uid, valor)
                texto = f"Você recebeu **{valor} 🗝️ Chave(s)**!"
            else:
                texto = valor
            await interaction.response.send_message(texto, ephemeral=True)
            if ok:
                self.montar()
                await interaction.message.edit(view=self, attachments=[])

    class HalloweenCaca(HalloweenView):
        def __init__(self, uid):
            super().__init__(uid, timeout=None)
            self.montar()

        def montar(self):
            sessao = _CACAS_ATIVAS.get(self.uid, {})
            segundos = int(sessao.get("segundos", 0))
            progresso = min(100, int(segundos / DURACAO_CACA_SEGUNDOS * 100))
            blocos = progresso // 5
            barra = "█" * blocos + "░" * (20 - blocos)
            eventos = sessao.get("eventos", [])[-4:]
            c = _container()
            c.add_item(ui.TextDisplay(f"# 👻 Caça aos Fantasmas\n`{barra}` **{progresso}%**\n⏱️ Tempo: **{segundos // 60}:{segundos % 60:02d} / 5:00** · Atualização a cada 10 segundos"))
            c.add_item(ui.Separator(spacing=discord.SeparatorSpacing.large))
            c.add_item(ui.TextDisplay("### 🌫️ Acontecimentos recentes\n" + ("\n\n".join(f"• {x}" for x in eventos) if eventos else "A névoa se move silenciosamente...")))
            c.add_item(ui.Separator())
            c.add_item(ui.TextDisplay(f"👻 **Fantasmas capturados:** {sessao.get('capturados', 0)}\n🕸️ **Durabilidade da rede:** {_rede_durabilidade(self.uid)}/{DURABILIDADE_REDE_FANTASMAS}"))
            if sessao.get("pausada_rede"):
                c.add_item(ui.TextDisplay("⚠️ **Sua Rede de Fantasmas quebrou!** O contador está pausado. Compre outra rede por 5.000 Joyens para continuar, ou finalize a caçada para receber as capturas."))
                c.add_item(ui.ActionRow(_btn("Comprar Rede", lambda i: self.comprar_rede(i), style=discord.ButtonStyle.success, emoji="🕸️"), _btn("Finalizar", lambda i: self.finalizar(i), style=discord.ButtonStyle.danger)))
            else:
                c.add_item(ui.ActionRow(_btn("Finalizar", lambda i: self.finalizar(i), style=discord.ButtonStyle.danger)))
            self.add_item(c)

        async def comprar_rede(self, interaction):
            ok, texto = await asyncio.to_thread(_comprar, ns, self.uid, "rede_fantasmas")
            if not ok:
                await interaction.response.send_message("⚠️ " + texto, ephemeral=True)
                return
            sessao = _CACAS_ATIVAS.get(self.uid)
            if sessao and sessao.get("pausada_rede"):
                sessao["pausada_rede"] = False
                sessao["eventos"].append("🕸️ Uma nova rede foi equipada. A caça continua!")
                sessao["task"] = asyncio.create_task(_rodar_caca(self.uid))
            self.montar()
            await interaction.response.edit_message(view=self)

        async def finalizar(self, interaction):
            sessao = _CACAS_ATIVAS.pop(self.uid, None)
            if not sessao:
                await interaction.response.send_message("Esta caçada já foi encerrada.", ephemeral=True)
                return
            task = sessao.get("task")
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
            capturados = int(sessao.get("capturados", 0))
            _definir_cooldown(self.uid, PAUSA_CACA_SEGUNDOS, capturados)
            asyncio.create_task(_atualizar_painel_apos_pausa(self.uid))
            result = _container()
            result.add_item(ui.TextDisplay(f"# 🌙 Caçada finalizada\nVocê capturou **{capturados} fantasma(s)**.\n⏳ Você poderá caçar novamente em **10 minutos**.\n\nA Rede de Fantasmas restante: **{_rede_durabilidade(self.uid)}/{DURABILIDADE_REDE_FANTASMAS}**."))
            result.add_item(ui.ActionRow(_btn("Voltar ao Halloween", lambda i: _open_main(i, self.uid), style=discord.ButtonStyle.secondary)))
            nova = HalloweenView(self.uid)
            await interaction.response.edit_message(view=result and _view_from_container(result, nova))

    def _view_from_container(container, view):
        view.add_item(container)
        return view

    async def _rodar_caca(uid):
        try:
            while uid in _CACAS_ATIVAS:
                sessao = _CACAS_ATIVAS[uid]
                if sessao.get("pausada_rede"):
                    return
                await asyncio.sleep(INTERVALO_CACA_SEGUNDOS)
                if uid not in _CACAS_ATIVAS: return
                sessao = _CACAS_ATIVAS[uid]
                if sessao.get("pausada_rede"): return
                sessao["segundos"] = min(DURACAO_CACA_SEGUNDOS, sessao["segundos"] + INTERVALO_CACA_SEGUNDOS)
                sessao["eventos"].append(random.choice(CENARIOS_FANTASMAS))
                if random.random() < 0.58:
                    ok, restante = await asyncio.to_thread(_gastar_durabilidade_rede, uid)
                    if ok:
                        sessao["capturados"] += 1

                        # Registra a captura no banco, independentemente
                        # de a rede ainda possuir durabilidade.
                        await asyncio.to_thread(
                            _registrar_fantasma,
                            uid
                        )

                        sessao["eventos"].append(
                            f"👻 Fantasma capturado! "
                            f"Total nesta caçada: **{sessao['capturados']}**."
                        )
                        if restante <= 0:
                            sessao["pausada_rede"] = True
                            sessao["eventos"].append("💥 A Rede de Fantasmas quebrou depois da 20ª captura!")
                sessao["eventos"] = sessao["eventos"][-4:]
                msg = sessao.get("message")
                if msg:
                    try:
                        view = HalloweenCaca(uid)
                        await msg.edit(view=view)
                    except (discord.NotFound, discord.HTTPException) as e:
                        print(f"[Halloween] Não foi possível atualizar painel da caça: {e}")
                if sessao.get("pausada_rede"):
                    return
                if sessao["segundos"] >= DURACAO_CACA_SEGUNDOS:
                    # Encerra automaticamente ao atingir cinco minutos.
                    sessao = _CACAS_ATIVAS.pop(uid, None)
                    if sessao:
                        _definir_cooldown(uid, PAUSA_CACA_SEGUNDOS, sessao["capturados"])
                        asyncio.create_task(_atualizar_painel_apos_pausa(uid))
                        msg = sessao.get("message")
                        if msg:
                            c = _container()
                            c.add_item(ui.TextDisplay(f"# 🌕 Caça concluída!\nVocê capturou **{sessao['capturados']} fantasma(s)** em 5 minutos.\n⏳ Próxima caçada disponível em **10 minutos**."))
                            v = HalloweenView(uid)
                            v.add_item(c)
                            try: await msg.edit(view=v)
                            except discord.HTTPException: pass
                    return
        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"[Halloween] Erro na caçada de {uid}: {e}")

    async def _atualizar_painel_apos_pausa(uid):
        await asyncio.sleep(PAUSA_CACA_SEGUNDOS)
        msg = _MAIN_MESSAGES.get(uid)
        if msg:
            try:
                await msg.edit(view=_main_view(uid), attachments=[])
            except discord.HTTPException:
                pass

    async def _start_hunt(interaction, uid):
        if uid in _CACAS_ATIVAS:
            await interaction.response.send_message("Você já está em uma caçada!", ephemeral=True)
            return
        cooldown = _cooldown_ate(uid)
        now = datetime.datetime.now(FUSO)
        if cooldown and cooldown > now:
            secs = int((cooldown - now).total_seconds())
            await interaction.response.send_message(f"A caçada está em pausa. Tente novamente em **{secs // 60}:{secs % 60:02d}**.", ephemeral=True)
            return
        if _rede_durabilidade(uid) <= 0:
            await interaction.response.send_message(f"Você precisa comprar uma Rede de Fantasmas por **{PRECO_REDE_FANTASMAS:,} Joyens** na categoria Lembrancinhas.", ephemeral=True)
            return
        _CACAS_ATIVAS[uid] = {"segundos": 0, "capturados": 0, "eventos": ["🌫️ Você entra na névoa com a rede preparada. A caça começou!"], "pausada_rede": False, "task": None, "message": None}
        view = HalloweenCaca(uid)
        await interaction.response.send_message(view=view)
        msg = await interaction.original_response()
        _CACAS_ATIVAS[uid]["message"] = msg
        _CACAS_ATIVAS[uid]["task"] = asyncio.create_task(_rodar_caca(uid))
        # Desabilita o botão no painel principal enquanto a caçada está ativa.
        _MAIN_MESSAGES[uid] = interaction.message
        try: await interaction.message.edit(view=_main_view(uid))
        except discord.HTTPException: pass

    @bot.command(name="halloween")
    async def halloween_comando(ctx):
        if not HALLOWEEN_ATIVO:
            await ctx.send("🎃 O evento de Halloween está encerrado.")
            return
        if ctx.author.bot: return
        _garantir_usuario(ctx.author.id)
        with _db() as con:
            for nome, (emoji, descricao) in HALLOWEEN_CONQUISTAS.items():
                con.execute("INSERT OR IGNORE INTO conquistas (nome, descricao, emoji) VALUES (?, ?, ?)", (nome, descricao, emoji))
        mensagem = await ctx.send(view=_main_view(ctx.author.id))
        _MAIN_MESSAGES[ctx.author.id] = mensagem

    @bot.command(name="halloween_missoes")
    async def halloween_missoes_comando(ctx):
        if not HALLOWEEN_ATIVO:
            await ctx.send("🎃 O evento de Halloween está encerrado.")
            return
        if ctx.author.bot: return
        _garantir_usuario(ctx.author.id)
        await ctx.send(view=HalloweenMissoes(ctx.author.id))

    print("✅ Módulo V2 do evento de Halloween registrado.")
