# -*- coding: utf-8 -*-
"""
Evento de Halloween do Sakurai.
Este módulo NÃO substitui bot.py. Ele é registrado passando o objeto bot e
as funções já existentes no bot.py para configurar_halloween().
"""

import discord
import sqlite3
import random
import datetime
import asyncio


# ============================================================
# HALLOWEEN — CONFIGURAÇÃO DO EVENTO
# Edite nomes, preços e recompensas nesta seção.
# ============================================================

HALLOWEEN_ATIVO = True
HALLOWEEN_FUSO = datetime.timezone(datetime.timedelta(hours=-3))

HALLOWEEN_BANNERS = {
    "aboboras": "Abóboras",
    "sakura": "Sakura Sombria",
    "morcegos": "Morcegos",
}

HALLOWEEN_CONQUISTAS = {
    "Halloween 26": {
        "emoji": "🎃",
        "descricao": "Participou das aventuras do Halloween 2026 do Sakurai.",
    },
    "Criatura da Noite": {
        "emoji": "🌙",
        "descricao": "Uma criatura que prosperou durante a noite de Halloween.",
    },
    "Guardião da Cerejeira Sombria": {
        "emoji": "🌸",
        "descricao": "Protegeu as cerejeiras durante o Halloween sombrio.",
    },
    "Fantasminha Camarada": {
        "emoji": "👻",
        "descricao": "Um fantasminha simpático que acompanha a comunidade.",
    },
    "Fome de Sangue": {
        "emoji": "🩸",
        "descricao": "Um título temático conquistado no evento de Halloween.",
    },
}

HALLOWEEN_LOJA = {
    "banner_aboboras": {
        "nome": "Banner Abóboras",
        "tipo": "banner",
        "alvo": HALLOWEEN_BANNERS["aboboras"],
        "preco": 30,
        "emoji": "🎃",
        "descricao": "Um banner decorado com abóboras de Halloween.",
    },
    "banner_morcegos": {
        "nome": "Banner Morcegos",
        "tipo": "banner",
        "alvo": HALLOWEEN_BANNERS["morcegos"],
        "preco": 30,
        "emoji": "🦇",
        "descricao": "Um banner com morcegos e sombras.",
    },
    "banner_sakura": {
        "nome": "Banner Sakura Sombria",
        "tipo": "banner",
        "alvo": HALLOWEEN_BANNERS["sakura"],
        "preco": 70,
        "emoji": "🌸",
        "descricao": "O banner raro das cerejeiras sombrias.",
    },
    "titulo_fantasma": {
        "nome": "Fantasminha Camarada",
        "tipo": "conquista",
        "alvo": "Fantasminha Camarada",
        "preco": 20,
        "emoji": "👻",
        "descricao": "Desbloqueia a conquista/título Fantasminha Camarada.",
    },
    "titulo_sangue": {
        "nome": "Fome de Sangue",
        "tipo": "conquista",
        "alvo": "Fome de Sangue",
        "preco": 35,
        "emoji": "🩸",
        "descricao": "Desbloqueia a conquista/título Fome de Sangue.",
    },
    "pet_dullahan": {
        "nome": "Cão Dullahan",
        "tipo": "pet",
        "alvo": "Cão Dullahan",
        "preco": 120,
        "emoji": "🐕‍🦺",
        "descricao": "Um pet especial e exclusivo do Halloween.",
    },
}

HALLOWEEN_CAIXAS = {
    "assombrada": {
        "nome": "Caixa Assombrada",
        "emoji": "🎃",
        "descricao": (
            "Custa 1 <:ChaveIcon:1564804190184935444> Chave. Concede doces garantidos e pode trazer "
            "banners, a conquista Halloween 26 e itens normais do bot."
        ),
    },
    "sakura": {
        "nome": "Caixa da Sakura Sombria",
        "emoji": "🌸",
        "descricao": (
            "Custa 1 <:ChaveIcon:1564804190184935444> Chave. Concede mais doces, 2–3 Pétalas e tem "
            "chances de trazer o banner raro e conquistas exclusivas."
        ),
    },
}

HALLOWEEN_MISSOES = {
    "mensagens": {
        "nome": "💬 Vozes na Névoa",
        "descricao": "Envie 20 mensagens depois de abrir o painel do evento.",
        "contador": "msg_total",
        "meta": 20,
        "chaves": 2,
    },
    "trabalho": {
        "nome": "🧹 Trabalho Sob a Lua",
        "descricao": "Trabalhe 2 vezes depois de iniciar sua participação no evento.",
        "contador": "trabalhar_total",
        "meta": 2,
        "chaves": 2,
    },
    "diario": {
        "nome": "📅 Visita à Cidade Assombrada",
        "descricao": "Use !diario uma vez depois de iniciar sua participação no evento.",
        "contador": "diario_total",
        "meta": 1,
        "chaves": 1,
    },
}

HALLOWEEN_DOCES_CAIXA_ASSOMBRADA = (12, 22)
HALLOWEEN_DOCES_CAIXA_SAKURA = (30, 45)


def _halloween_conectar():
    con = sqlite3.connect("jogadorbot.db", timeout=15)
    con.execute("PRAGMA busy_timeout=15000;")
    return con


def _halloween_criar_tabelas():
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS halloween_usuarios (
                usuario_id TEXT PRIMARY KEY,
                doces INTEGER NOT NULL DEFAULT 0,
                base_mensagens INTEGER NOT NULL DEFAULT 0,
                base_trabalho INTEGER NOT NULL DEFAULT 0,
                base_diario INTEGER NOT NULL DEFAULT 0,
                iniciou_em TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS halloween_missoes_usuarios (
                usuario_id TEXT NOT NULL,
                missao_id TEXT NOT NULL,
                concluida INTEGER NOT NULL DEFAULT 0,
                concluida_em TEXT,
                PRIMARY KEY (usuario_id, missao_id)
            )
        """)
        con.commit()
    finally:
        con.close()


def _halloween_contador(usuario_id, coluna):
    # Coluna vem exclusivamente da configuração fixa do módulo, nunca do usuário.
    colunas_permitidas = {"msg_total", "trabalhar_total", "diario_total"}
    if coluna not in colunas_permitidas:
        return 0
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute(f"SELECT {coluna} FROM contadores_usuarios WHERE usuario_id = ?",
                    (str(usuario_id),))
        linha = cur.fetchone()
        return int(linha[0] or 0) if linha else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        con.close()


def _halloween_garantir_usuario(usuario_id):
    """Registra a linha e guarda os contadores atuais como ponto inicial do evento."""
    usuario_id = str(usuario_id)
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("SELECT 1 FROM halloween_usuarios WHERE usuario_id = ?", (usuario_id,))
        existe = cur.fetchone()
        if not existe:
            # A tabela de contadores já é inicializada pelo bot principal.
            cur.execute("SELECT msg_total, trabalhar_total, diario_total "
                        "FROM contadores_usuarios WHERE usuario_id = ?", (usuario_id,))
            linha = cur.fetchone() or (0, 0, 0)
            agora = datetime.datetime.now(HALLOWEEN_FUSO).isoformat()
            cur.execute("""
                INSERT INTO halloween_usuarios
                (usuario_id, doces, base_mensagens, base_trabalho, base_diario, iniciou_em)
                VALUES (?, 0, ?, ?, ?, ?)
            """, (usuario_id, int(linha[0] or 0), int(linha[1] or 0),
                  int(linha[2] or 0), agora))
        con.commit()
    finally:
        con.close()


def _halloween_dados_usuario(usuario_id):
    _halloween_garantir_usuario(usuario_id)
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT doces, base_mensagens, base_trabalho, base_diario
            FROM halloween_usuarios WHERE usuario_id = ?
        """, (str(usuario_id),))
        return cur.fetchone() or (0, 0, 0, 0)
    finally:
        con.close()


def _halloween_doces(usuario_id):
    return int(_halloween_dados_usuario(usuario_id)[0])


def _halloween_adicionar_doces(usuario_id, quantidade):
    _halloween_garantir_usuario(usuario_id)
    con = _halloween_conectar()
    try:
        con.execute("UPDATE halloween_usuarios SET doces = doces + ? WHERE usuario_id = ?",
                    (int(quantidade), str(usuario_id)))
        con.commit()
    finally:
        con.close()


def _halloween_gastar_doces(usuario_id, quantidade):
    """Retira doces apenas se o saldo ainda for suficiente; devolve True/False."""
    _halloween_garantir_usuario(usuario_id)
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("""
            UPDATE halloween_usuarios SET doces = doces - ?
            WHERE usuario_id = ? AND doces >= ?
        """, (int(quantidade), str(usuario_id), int(quantidade)))
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def _halloween_conquista_usuario(usuario_id, nome):
    """Concede conquista existente; se ainda não existir, cria no catálogo."""
    dados = HALLOWEEN_CONQUISTAS.get(nome, {
        "emoji": "🎃",
        "descricao": "Recompensa especial do evento de Halloween.",
    })
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO conquistas (nome, descricao, emoji)
            VALUES (?, ?, ?)
        """, (nome, dados["descricao"], dados["emoji"]))
        cur.execute("SELECT id FROM conquistas WHERE LOWER(nome) = LOWER(?)", (nome,))
        linha = cur.fetchone()
        if not linha:
            return False
        conquista_id = linha[0]
        cur.execute("""
            SELECT 1 FROM conquistas_usuarios
            WHERE usuario_id = ? AND conquista_id = ?
        """, (str(usuario_id), conquista_id))
        ja_tem = cur.fetchone() is not None
        if not ja_tem:
            cur.execute("""
                INSERT INTO conquistas_usuarios (usuario_id, conquista_id, data)
                VALUES (?, ?, ?)
            """, (str(usuario_id), conquista_id,
                  datetime.datetime.now(HALLOWEEN_FUSO).strftime("%d/%m/%Y")))
        con.commit()
        return not ja_tem
    finally:
        con.close()


def _halloween_conceder_banner(ns, usuario_id, nome_banner):
    """Entrega um banner do catálogo atual. Retorna False se não existir."""
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("SELECT id FROM banners WHERE LOWER(nome) = LOWER(?)", (nome_banner,))
        linha = cur.fetchone()
        if not linha:
            return False, "não encontrado"
        banner_id = linha[0]
        cur.execute("SELECT 1 FROM banners_usuarios WHERE usuario_id = ? AND banner_id = ?",
                    (str(usuario_id), banner_id))
        if cur.fetchone():
            return False, "duplicado"
        cur.execute("INSERT OR IGNORE INTO banners_usuarios (usuario_id, banner_id) VALUES (?, ?)",
                    (str(usuario_id), banner_id))
        con.commit()
        return True, "concedido"
    finally:
        con.close()


def _halloween_conceder_pet(usuario_id):
    """Entrega o pet especial usando a tabela de pets já existente."""
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM pets
            WHERE usuario_id = ? AND disponivel_adocao = 0
        """, (str(usuario_id),))
        total = int(cur.fetchone()[0] or 0)
        if total >= 3:
            return False, "limite"
        cur.execute("""
            SELECT 1 FROM pets
            WHERE usuario_id = ? AND (LOWER(nome) = LOWER(?) OR LOWER(raca) = LOWER(?))
              AND disponivel_adocao = 0
        """, (str(usuario_id), "Cão Dullahan", "Cão Dullahan"))
        if cur.fetchone():
            return False, "duplicado"
        agora = datetime.datetime.now(HALLOWEEN_FUSO).isoformat()
        cur.execute("""
            INSERT INTO pets
            (usuario_id, especie, raca, nome, fome, energia, higiene, felicidade,
             hp, criado_em, ultima_atualizacao, disponivel_adocao)
            VALUES (?, 'Cachorros', 'Cão Dullahan', 'Cão Dullahan',
                    100, 100, 100, 100, 100, ?, ?, 0)
        """, (str(usuario_id), agora, agora))
        con.commit()
        return True, "concedido"
    finally:
        con.close()


def _halloween_recompensar_titulo(usuario_id, nome):
    novo = _halloween_conquista_usuario(usuario_id, nome)
    if novo:
        return f"🏆 Conquista desbloqueada: **{nome}**"
    return f"🏆 **{nome}** (você já possuía; recebeu doces de compensação)"


def _halloween_consumir_chave(usuario_id):
    """Consome exatamente uma Chave, apenas se ainda houver saldo."""
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("""
            UPDATE chaves_usuario SET quantidade = quantidade - 1
            WHERE usuario_id = ? AND quantidade >= 1
        """, (str(usuario_id),))
        con.commit()
        return cur.rowcount == 1
    finally:
        con.close()


def _halloween_loot_caixa(ns, usuario_id, tipo):
    mensagens = []
    if tipo == "assombrada":
        doces = random.randint(*HALLOWEEN_DOCES_CAIXA_ASSOMBRADA)
        _halloween_adicionar_doces(usuario_id, doces)
        mensagens.append(f"🍬 **+{doces} doces**")

        # Recompensas extras independentes; é possível obter mais de uma.
        if random.random() < 0.22:
            nome_banner = random.choice([
                HALLOWEEN_BANNERS["aboboras"],
                HALLOWEEN_BANNERS["morcegos"],
            ])
            ok, motivo = _halloween_conceder_banner(ns, usuario_id, nome_banner)
            if ok:
                mensagens.append(f"🖼️ Banner **{nome_banner}**")
            elif motivo == "duplicado":
                bonus = 8
                _halloween_adicionar_doces(usuario_id, bonus)
                mensagens.append(f"🍬 Banner repetido convertido em **+{bonus} doces**")
            else:
                mensagens.append(f"⚠️ Banner **{nome_banner}** não está cadastrado no catálogo.")

        if random.random() < 0.16:
            if _halloween_conquista_usuario(usuario_id, "Halloween 26"):
                mensagens.append("🏆 Conquista **Halloween 26**")
            else:
                bonus = 6
                _halloween_adicionar_doces(usuario_id, bonus)
                mensagens.append(f"🍬 Conquista repetida convertida em **+{bonus} doces**")

        if random.random() < 0.38:
            try:
                item_texto = ns["sortear_item_aleatorio_mineracao_petshop_sync"](usuario_id)
                mensagens.append(f"🎁 Item aleatório: {item_texto}")
            except Exception as erro:
                print(f"[Halloween] Erro ao conceder item aleatório: {erro}")
                mensagens.append("⚠️ Não foi possível conceder o item aleatório. Avise a administração.")

    elif tipo == "sakura":
        doces = random.randint(*HALLOWEEN_DOCES_CAIXA_SAKURA)
        petalas = random.randint(2, 3)
        _halloween_adicionar_doces(usuario_id, doces)
        ns["adicionar_petalas"](usuario_id, petalas)
        mensagens.append(f"🍬 **+{doces} doces**")
        mensagens.append(f"<:PetalaIcon:1564803824906932385> **+{petalas} Pétalas**")

        if random.random() < 0.38:
            ok, motivo = _halloween_conceder_banner(ns, usuario_id, HALLOWEEN_BANNERS["sakura"])
            if ok:
                mensagens.append(f"🖼️ Banner raro **{HALLOWEEN_BANNERS['sakura']}**")
            elif motivo == "duplicado":
                bonus = 15
                _halloween_adicionar_doces(usuario_id, bonus)
                mensagens.append(f"🍬 Banner repetido convertido em **+{bonus} doces**")
            else:
                mensagens.append("⚠️ O banner Sakura Sombria não está cadastrado no catálogo.")

        for titulo, chance, compensacao in [
            ("Criatura da Noite", 0.30, 10),
            ("Guardião da Cerejeira Sombria", 0.18, 12),
        ]:
            if random.random() < chance:
                if _halloween_conquista_usuario(usuario_id, titulo):
                    mensagens.append(f"🏆 Conquista **{titulo}**")
                else:
                    _halloween_adicionar_doces(usuario_id, compensacao)
                    mensagens.append(f"🍬 Conquista repetida convertida em **+{compensacao} doces**")

        if random.random() < 0.25:
            try:
                item_texto = ns["sortear_item_aleatorio_mineracao_petshop_sync"](usuario_id)
                mensagens.append(f"🎁 Item aleatório: {item_texto}")
            except Exception as erro:
                print(f"[Halloween] Erro ao conceder item aleatório: {erro}")
                mensagens.append("⚠️ Não foi possível conceder o item aleatório. Avise a administração.")

    return mensagens


def _halloween_comprar(ns, usuario_id, item_id):
    item = HALLOWEEN_LOJA.get(item_id)
    if not item:
        return False, "Esse item não existe."

    # Verifica se o item já foi obtido antes de retirar a moeda.
    if item["tipo"] == "banner":
        con = _halloween_conectar()
        try:
            cur = con.cursor()
            cur.execute("SELECT id FROM banners WHERE LOWER(nome) = LOWER(?)", (item["alvo"],))
            linha = cur.fetchone()
            if not linha:
                return False, (
                    f"O banner **{item['alvo']}** ainda não existe na tabela `banners`. "
                    "Cadastre-o primeiro e confira o nome em HALLOWEEN_BANNERS."
                )
            cur.execute("SELECT 1 FROM banners_usuarios WHERE usuario_id = ? AND banner_id = ?",
                        (str(usuario_id), linha[0]))
            if cur.fetchone():
                return False, "Você já possui esse banner."
        finally:
            con.close()

    elif item["tipo"] == "conquista":
        con = _halloween_conectar()
        try:
            cur = con.cursor()
            cur.execute("SELECT id FROM conquistas WHERE LOWER(nome) = LOWER(?)", (item["alvo"],))
            linha = cur.fetchone()
            if linha:
                cur.execute("SELECT 1 FROM conquistas_usuarios WHERE usuario_id = ? AND conquista_id = ?",
                            (str(usuario_id), linha[0]))
                if cur.fetchone():
                    return False, "Você já possui essa conquista/título."
        finally:
            con.close()

    elif item["tipo"] == "pet":
        con = _halloween_conectar()
        try:
            cur = con.cursor()
            cur.execute("""
                SELECT 1 FROM pets
                WHERE usuario_id = ? AND (LOWER(nome) = LOWER(?) OR LOWER(raca) = LOWER(?))
                  AND disponivel_adocao = 0
            """, (str(usuario_id), "Cão Dullahan", "Cão Dullahan"))
            if cur.fetchone():
                return False, "Você já possui o Cão Dullahan."
            cur.execute("SELECT COUNT(*) FROM pets WHERE usuario_id = ? AND disponivel_adocao = 0",
                        (str(usuario_id),))
            if int(cur.fetchone()[0] or 0) >= 3:
                return False, "Seu inventário de pets está cheio (limite de 3). Libere um espaço antes de comprar."
        finally:
            con.close()

    saldo = _halloween_doces(usuario_id)
    if saldo < item["preco"]:
        return False, f"Você tem **{saldo} doces**, mas precisa de **{item['preco']}**."

    # Cobra primeiro; se a entrega falhar, devolve o saldo.
    if not _halloween_gastar_doces(usuario_id, item["preco"]):
        return False, "Seu saldo mudou; tente novamente."

    try:
        if item["tipo"] == "banner":
            ok, motivo = _halloween_conceder_banner(ns, usuario_id, item["alvo"])
            if not ok:
                _halloween_adicionar_doces(usuario_id, item["preco"])
                return False, "Não foi possível entregar o banner. Seus doces foram devolvidos."

        elif item["tipo"] == "conquista":
            novo = _halloween_conquista_usuario(usuario_id, item["alvo"])
            if not novo:
                _halloween_adicionar_doces(usuario_id, item["preco"])
                return False, "Você já possui essa conquista/título. Seus doces foram devolvidos."

        elif item["tipo"] == "pet":
            ok, motivo = _halloween_conceder_pet(usuario_id)
            if not ok:
                _halloween_adicionar_doces(usuario_id, item["preco"])
                if motivo == "limite":
                    return False, "Seu inventário de pets está cheio. Seus doces foram devolvidos."
                return False, "Você já possui o Cão Dullahan. Seus doces foram devolvidos."

    except Exception as erro:
        _halloween_adicionar_doces(usuario_id, item["preco"])
        print(f"[Halloween] Erro na compra {item_id}: {erro}")
        return False, "Ocorreu um erro ao entregar o item; seus doces foram devolvidos."

    return True, f"Você comprou **{item['nome']}** por 🍬 {item['preco']} doces!"


def _halloween_missoes_status(usuario_id):
    doces, base_msg, base_trabalho, base_diario = _halloween_dados_usuario(usuario_id)
    bases = {
        "msg_total": base_msg,
        "trabalhar_total": base_trabalho,
        "diario_total": base_diario,
    }
    resultado = []
    con = _halloween_conectar()
    try:
        cur = con.cursor()
        for missao_id, missao in HALLOWEEN_MISSOES.items():
            cur.execute("""
                SELECT concluida FROM halloween_missoes_usuarios
                WHERE usuario_id = ? AND missao_id = ?
            """, (str(usuario_id), missao_id))
            linha = cur.fetchone()
            concluida = bool(linha and linha[0])
            atual = _halloween_contador(usuario_id, missao["contador"])
            progresso = max(0, atual - int(bases[missao["contador"]]))
            resultado.append((missao_id, missao, progresso, concluida))
    finally:
        con.close()
    return resultado


def _halloween_reivindicar_missao(usuario_id, missao_id):
    if missao_id not in HALLOWEEN_MISSOES:
        return False, "Missão inválida."
    status = {mid: (missao, progresso, concluida)
              for mid, missao, progresso, concluida in _halloween_missoes_status(usuario_id)}
    missao, progresso, concluida = status[missao_id]
    if concluida:
        return False, "Você já resgatou essa missão."
    if progresso < missao["meta"]:
        return False, f"Progresso: **{progresso}/{missao['meta']}**. Complete o objetivo primeiro."

    con = _halloween_conectar()
    try:
        cur = con.cursor()
        cur.execute("""
            INSERT OR IGNORE INTO halloween_missoes_usuarios
            (usuario_id, missao_id, concluida, concluida_em)
            VALUES (?, ?, 1, ?)
        """, (str(usuario_id), missao_id, datetime.datetime.now(HALLOWEEN_FUSO).isoformat()))
        if cur.rowcount != 1:
            con.rollback()
            return False, "Essa missão já foi resgatada."
        con.commit()
    finally:
        con.close()

    # Concede as chaves existentes do sistema principal.
    # A função existente é síncrona, por isso executamos em thread.
    return True, missao["chaves"]


def configurar_halloween(bot, ns):
    """
    Registra o comando !halloween. Chamar uma única vez em bot.py antes de bot.run().
    ns deve ser globals() do bot.py, para reutilizar suas funções existentes.
    """
    _halloween_criar_tabelas()

    class HalloweenView(discord.ui.View):
        def __init__(self, usuario_id):
            super().__init__(timeout=180)
            self.usuario_id = int(usuario_id)

        async def interaction_check(self, interaction: discord.Interaction):
            if interaction.user.id != self.usuario_id:
                await interaction.response.send_message(
                    "Este painel pertence a outra pessoa. Use `!halloween` para abrir o seu.",
                    ephemeral=True
                )
                return False
            if not HALLOWEEN_ATIVO:
                await interaction.response.send_message("O evento de Halloween está encerrado.", ephemeral=True)
                return False
            return True

    class HalloweenPrincipal(HalloweenView):
        @discord.ui.button(label="Hallobox", emoji="🎁", style=discord.ButtonStyle.primary, row=0)
        async def hallobox(self, interaction: discord.Interaction, button: discord.ui.Button):
            view = HalloweenHallobox(self.usuario_id)
            await interaction.response.edit_message(embed=view.embed(), view=view)

        @discord.ui.button(label="Lembrancinhas", emoji="🛍️", style=discord.ButtonStyle.success, row=0)
        async def lembrancinhas(self, interaction: discord.Interaction, button: discord.ui.Button):
            view = HalloweenLembrancinhas(self.usuario_id)
            await interaction.response.edit_message(embed=view.embed(), view=view)

        def embed(self):
            chaves = ns["buscar_chaves"](self.usuario_id)
            doces = _halloween_doces(self.usuario_id)
            petalas = ns["buscar_petalas"](self.usuario_id)
            embed = discord.Embed(
                title="🎃 Halloween do Sakurai — Festival das Pétalas Perdidas",
                description=(
                    "A névoa cobriu a cidade e as cerejeiras brilham sob a lua roxa.\n"
                    "Complete missões para ganhar **Chaves**, abra caixas na **Hallobox** "
                    "e troque os **doces** por lembranças exclusivas.\n\n"
                    f"<:ChaveIcon:1564804190184935444> **Chaves:** {chaves}\n"
                    f"🍬 **Doces do evento:** {doces}\n"
                    f"<:PetalaIcon:1564803824906932385> **Pétalas:** {petalas}"
                ),
                color=discord.Color.dark_purple()
            )
            embed.set_footer(text="As chaves são a moeda existente do Sakurai; doces são exclusivos deste evento.")
            return embed

    class HalloweenHallobox(HalloweenView):
        def embed(self):
            return discord.Embed(
                title="🎁 Hallobox — Caixas do Halloween",
                description=(
                    f"<:ChaveIcon:1564804190184935444> **Suas chaves:** {ns['buscar_chaves'](self.usuario_id)}\n\n"
                    f"🎃 **Caixa Assombrada**\n{HALLOWEEN_CAIXAS['assombrada']['descricao']}\n\n"
                    f"🌸 **Caixa da Sakura Sombria**\n{HALLOWEEN_CAIXAS['sakura']['descricao']}\n\n"
                    "Cada abertura consome 1 Chave. Os itens repetidos são convertidos em doces."
                ),
                color=discord.Color.purple()
            )

        @discord.ui.button(label="Abrir Caixa Assombrada", emoji="🎃", style=discord.ButtonStyle.primary, row=0)
        async def abrir_assombrada(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.abrir_caixa(interaction, "assombrada")

        @discord.ui.button(label="Abrir Caixa da Sakura Sombria", emoji="🌸", style=discord.ButtonStyle.success, row=0)
        async def abrir_sakura(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.abrir_caixa(interaction, "sakura")

        async def abrir_caixa(self, interaction, tipo):
            # Consumo atômico evita duas aberturas simultâneas com a mesma chave.
            consumida = await asyncio.to_thread(_halloween_consumir_chave, self.usuario_id)
            if not consumida:
                await interaction.response.send_message("Você não tem Chaves suficientes. Complete missões para ganhar mais.", ephemeral=True)
                return
            try:
                recompensas = await asyncio.to_thread(_halloween_loot_caixa, ns, self.usuario_id, tipo)
            except Exception as erro:
                # Não devolvemos a chave automaticamente se já houve entrega parcial, para evitar duplicações.
                print(f"[Halloween] Erro ao abrir caixa {tipo}: {erro}")
                await interaction.response.send_message(
                    "Ocorreu um erro durante a abertura. Avise a administração e informe o horário.",
                    ephemeral=True
                )
                return
            embed = discord.Embed(
                title=f"{HALLOWEEN_CAIXAS[tipo]['emoji']} Caixa aberta!",
                description="\n".join(f"• {linha}" for linha in recompensas) or "A caixa estava vazia.",
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Chaves restantes: {ns['buscar_chaves'](self.usuario_id)}")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.message.edit(embed=self.embed(), view=self)

        @discord.ui.button(label="Voltar", emoji="↩️", style=discord.ButtonStyle.secondary, row=1)
        async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
            view = HalloweenPrincipal(self.usuario_id)
            await interaction.response.edit_message(embed=view.embed(), view=view)

    class HalloweenLembrancinhas(HalloweenView):
        def embed(self):
            doces = _halloween_doces(self.usuario_id)
            embed = discord.Embed(
                title="🛍️ Lembrancinhas — Bazar da Lua Roxa",
                description=f"🍬 **Seus doces:** {doces}\n\nOs itens são permanentes. Cada item só pode ser comprado uma vez.",
                color=discord.Color.purple()
            )
            for item_id, item in HALLOWEEN_LOJA.items():
                embed.add_field(
                    name=f"{item['emoji']} {item['nome']} — 🍬 {item['preco']}",
                    value=item["descricao"],
                    inline=False
                )
            embed.set_footer(text="Se um banner não estiver cadastrado, ajuste o nome em HALLOWEEN_BANNERS.")
            return embed

        async def comprar(self, interaction, item_id):
            ok, mensagem = await asyncio.to_thread(_halloween_comprar, ns, self.usuario_id, item_id)
            await interaction.response.send_message(
                ("✅ " if ok else "⚠️ ") + mensagem,
                ephemeral=True
            )
            if ok:
                await interaction.message.edit(embed=self.embed(), view=self)

        @discord.ui.button(label="Abóboras", emoji="🎃", style=discord.ButtonStyle.primary, row=0)
        async def comprar_aboboras(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.comprar(interaction, "banner_aboboras")

        @discord.ui.button(label="Morcegos", emoji="🦇", style=discord.ButtonStyle.primary, row=0)
        async def comprar_morcegos(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.comprar(interaction, "banner_morcegos")

        @discord.ui.button(label="Sakura Sombria", emoji="🌸", style=discord.ButtonStyle.primary, row=0)
        async def comprar_sakura(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.comprar(interaction, "banner_sakura")

        @discord.ui.button(label="Fantasminha Camarada", emoji="👻", style=discord.ButtonStyle.success, row=1)
        async def comprar_fantasma(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.comprar(interaction, "titulo_fantasma")

        @discord.ui.button(label="Fome de Sangue", emoji="🩸", style=discord.ButtonStyle.success, row=1)
        async def comprar_sangue(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.comprar(interaction, "titulo_sangue")

        @discord.ui.button(label="Cão Dullahan", emoji="🐕‍🦺", style=discord.ButtonStyle.success, row=2)
        async def comprar_dullahan(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.comprar(interaction, "pet_dullahan")

        @discord.ui.button(label="Voltar", emoji="↩️", style=discord.ButtonStyle.secondary, row=3)
        async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
            view = HalloweenPrincipal(self.usuario_id)
            await interaction.response.edit_message(embed=view.embed(), view=view)

    class HalloweenMissoes(HalloweenView):
        def embed(self):
            embed = discord.Embed(
                title="<:ChaveIcon:1564804190184935444> Missões — Chaves Perdidas",
                description="Complete os objetivos abaixo e clique em resgatar para receber as Chaves.",
                color=discord.Color.dark_teal()
            )
            for missao_id, missao, progresso, concluida in _halloween_missoes_status(self.usuario_id):
                status = "✅ Resgatada" if concluida else (
                    "🎁 Pronta para resgatar" if progresso >= missao["meta"] else "⏳ Em andamento"
                )
                embed.add_field(
                    name=missao["nome"],
                    value=f"{missao['descricao']}\nProgresso: **{min(progresso, missao['meta'])}/{missao['meta']}**\n"
                          f"Recompensa: <:ChaveIcon:1564804190184935444> **{missao['chaves']} Chave(s)** • {status}",
                    inline=False
                )
            embed.set_footer(text="O progresso começa quando você abre o painel do evento pela primeira vez.")
            return embed

        async def resgatar(self, interaction, missao_id):
            ok, resultado = _halloween_reivindicar_missao(self.usuario_id, missao_id)
            if ok:
                await asyncio.to_thread(ns["adicionar_chaves"], self.usuario_id, resultado)
                texto = f"Você recebeu **{resultado} <:ChaveIcon:1564804190184935444> Chave(s)**!"
            else:
                texto = resultado
            await interaction.response.send_message(texto, ephemeral=True)
            if ok:
                await interaction.message.edit(embed=self.embed(), view=self)

        @discord.ui.button(label="Resgatar: Mensagens", emoji="💬", style=discord.ButtonStyle.success, row=0)
        async def resgatar_mensagens(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.resgatar(interaction, "mensagens")

        @discord.ui.button(label="Resgatar: Trabalho", emoji="🧹", style=discord.ButtonStyle.success, row=0)
        async def resgatar_trabalho(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.resgatar(interaction, "trabalho")

        @discord.ui.button(label="Resgatar: Diário", emoji="📅", style=discord.ButtonStyle.success, row=1)
        async def resgatar_diario(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self.resgatar(interaction, "diario")

        @discord.ui.button(label="Voltar", emoji="↩️", style=discord.ButtonStyle.secondary, row=1)
        async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
            view = HalloweenPrincipal(self.usuario_id)
            await interaction.response.edit_message(embed=view.embed(), view=view)

    @bot.command(name="halloween")
    async def halloween_comando(ctx):
        if not HALLOWEEN_ATIVO:
            await ctx.send("🎃 O evento de Halloween está encerrado.")
            return
        if ctx.author.bot:
            return
        _halloween_garantir_usuario(ctx.author.id)
        # Garante que os títulos do evento já existam no catálogo de conquistas.
        con = _halloween_conectar()
        try:
            cur = con.cursor()
            for nome, dados in HALLOWEEN_CONQUISTAS.items():
                cur.execute("INSERT OR IGNORE INTO conquistas (nome, descricao, emoji) VALUES (?, ?, ?)",
                            (nome, dados["descricao"], dados["emoji"]))
            con.commit()
        finally:
            con.close()
        view = HalloweenPrincipal(ctx.author.id)
        await ctx.send(embed=view.embed(), view=view)

    @bot.command(name="halloween_missoes")
    async def halloween_missoes_comando(ctx):
        if not HALLOWEEN_ATIVO:
            await ctx.send("🎃 O evento de Halloween está encerrado.")
            return
        if ctx.author.bot:
            return
        _halloween_garantir_usuario(ctx.author.id)
        view = HalloweenMissoes(ctx.author.id)
        await ctx.send(embed=view.embed(), view=view)

    print("✅ Módulo do evento de Halloween registrado.")
