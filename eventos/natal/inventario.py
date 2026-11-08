from datetime import datetime

from .banco import obter_conexao
from .configuracoes import (
    FUSO_HORARIO,
    ITENS_NATALINOS,
)


# ==========================================
# DATA E HORA
# ==========================================

def obter_data_atual():

    return datetime.now(FUSO_HORARIO).isoformat()


# ==========================================
# REGISTRAR JOGADOR
# ==========================================

def registrar_jogador(user_id):

    agora = obter_data_atual()

    with obter_conexao() as conn:

        conn.execute("""
            INSERT OR IGNORE INTO natal_jogadores (

                user_id,

                criado_em
            )

            VALUES (?, ?)
        """, (
            user_id,
            agora,
        ))


# ==========================================
# CONSULTAR INVENTÁRIO COMPLETO
# ==========================================

def consultar_inventario(user_id):

    registrar_jogador(user_id)

    with obter_conexao() as conn:

        jogador = conn.execute("""
            SELECT flocos, pontos

            FROM natal_jogadores

            WHERE user_id = ?
        """, (user_id,)).fetchone()

        itens = conn.execute("""
            SELECT item_id, quantidade

            FROM natal_inventario

            WHERE user_id = ?

            AND quantidade > 0

            ORDER BY item_id
        """, (user_id,)).fetchall()

        return {
            "flocos": jogador["flocos"],

            "pontos": jogador["pontos"],

            "itens": {
                item["item_id"]: item["quantidade"]
                for item in itens
            },
        }


# ==========================================
# CONSULTAR FLOCOS
# ==========================================

def consultar_flocos(user_id):

    inventario = consultar_inventario(user_id)

    return inventario["flocos"]


# ==========================================
# ADICIONAR FLOCOS
# ==========================================

def adicionar_flocos(
    user_id,
    quantidade,
    descricao="Recebimento de Flocos de Neve",
):

    if not isinstance(quantidade, int) or quantidade <= 0:
        return False

    registrar_jogador(user_id)

    agora = obter_data_atual()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        conn.execute("""
            UPDATE natal_jogadores

            SET flocos = flocos + ?

            WHERE user_id = ?
        """, (
            quantidade,
            user_id,
        ))

        conn.execute("""
            INSERT INTO natal_transacoes (

                user_id,

                tipo,

                quantidade,

                descricao,

                data
            )

            VALUES (?, 'credito', ?, ?, ?)
        """, (
            user_id,
            quantidade,
            descricao,
            agora,
        ))

    return True


# ==========================================
# REMOVER FLOCOS
# ==========================================

def remover_flocos(
    user_id,
    quantidade,
    descricao="Gasto de Flocos de Neve",
):

    if not isinstance(quantidade, int) or quantidade <= 0:
        return False

    registrar_jogador(user_id)

    agora = obter_data_atual()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        cursor = conn.execute("""
            UPDATE natal_jogadores

            SET flocos = flocos - ?

            WHERE user_id = ?

            AND flocos >= ?
        """, (
            quantidade,
            user_id,
            quantidade,
        ))

        if cursor.rowcount == 0:
            return False

        conn.execute("""
            INSERT INTO natal_transacoes (

                user_id,

                tipo,

                quantidade,

                descricao,

                data
            )

            VALUES (?, 'debito', ?, ?, ?)
        """, (
            user_id,
            quantidade,
            descricao,
            agora,
        ))

    return True


# ==========================================
# CONSULTAR QUANTIDADE DE UM ITEM
# ==========================================

def consultar_item(user_id, item_id):

    if item_id not in ITENS_NATALINOS:
        return 0

    with obter_conexao() as conn:

        resultado = conn.execute("""
            SELECT quantidade

            FROM natal_inventario

            WHERE user_id = ?

            AND item_id = ?
        """, (
            user_id,
            item_id,
        )).fetchone()

        if resultado is None:
            return 0

        return resultado["quantidade"]


# ==========================================
# ADICIONAR ITEM
# ==========================================

def adicionar_item(
    user_id,
    item_id,
    quantidade,
    descricao="Recebimento de material natalino",
):

    if item_id not in ITENS_NATALINOS:
        return False

    if not isinstance(quantidade, int) or quantidade <= 0:
        return False

    registrar_jogador(user_id)

    agora = obter_data_atual()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        conn.execute("""
            INSERT INTO natal_inventario (

                user_id,

                item_id,

                quantidade
            )

            VALUES (?, ?, ?)

            ON CONFLICT(user_id, item_id)

            DO UPDATE SET

                quantidade = quantidade + excluded.quantidade
        """, (
            user_id,
            item_id,
            quantidade,
        ))

        conn.execute("""
            INSERT INTO natal_transacoes (

                user_id,

                tipo,

                item_id,

                quantidade,

                descricao,

                data
            )

            VALUES (?, 'credito', ?, ?, ?, ?)
        """, (
            user_id,
            item_id,
            quantidade,
            descricao,
            agora,
        ))

    return True


# ==========================================
# REMOVER ITEM
# ==========================================

def remover_item(
    user_id,
    item_id,
    quantidade,
    descricao="Consumo de material natalino",
):

    if item_id not in ITENS_NATALINOS:
        return False

    if not isinstance(quantidade, int) or quantidade <= 0:
        return False

    agora = obter_data_atual()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        cursor = conn.execute("""
            UPDATE natal_inventario

            SET quantidade = quantidade - ?

            WHERE user_id = ?

            AND item_id = ?

            AND quantidade >= ?
        """, (
            quantidade,
            user_id,
            item_id,
            quantidade,
        ))

        if cursor.rowcount == 0:
            return False

        conn.execute("""
            INSERT INTO natal_transacoes (

                user_id,

                tipo,

                item_id,

                quantidade,

                descricao,

                data
            )

            VALUES (?, 'debito', ?, ?, ?, ?)
        """, (
            user_id,
            item_id,
            quantidade,
            descricao,
            agora,
        ))

    return True


# ==========================================
# CONSUMIR VÁRIOS MATERIAIS
# ==========================================

def consumir_materiais(
    user_id,
    materiais,
    descricao="Consumo de materiais natalinos",
):

    if not materiais:
        return False

    for item_id, quantidade in materiais.items():

        if item_id not in ITENS_NATALINOS:
            return False

        if not isinstance(quantidade, int) or quantidade <= 0:
            return False

    agora = obter_data_atual()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        for item_id, quantidade in materiais.items():

            cursor = conn.execute("""
                UPDATE natal_inventario

                SET quantidade = quantidade - ?

                WHERE user_id = ?

                AND item_id = ?

                AND quantidade >= ?
            """, (
                quantidade,
                user_id,
                item_id,
                quantidade,
            ))

            if cursor.rowcount == 0:
                return False

            conn.execute("""
                INSERT INTO natal_transacoes (

                    user_id,

                    tipo,

                    item_id,

                    quantidade,

                    descricao,

                    data
                )

                VALUES (?, 'debito', ?, ?, ?, ?)
            """, (
                user_id,
                item_id,
                quantidade,
                descricao,
                agora,
            ))

    return True


# ==========================================
# CONCEDER RECOMPENSA ÚNICA
# ==========================================

def conceder_recompensa_unica(
    user_id,
    recompensa_id,
    itens=None,
    flocos=0,
    descricao="Recompensa especial",
):

    itens = itens or {}

    if not recompensa_id:
        return False

    if not isinstance(flocos, int) or flocos < 0:
        return False

    for item_id, quantidade in itens.items():

        if item_id not in ITENS_NATALINOS:
            return False

        if not isinstance(quantidade, int) or quantidade <= 0:
            return False

    if flocos == 0 and not itens:
        return False

    registrar_jogador(user_id)

    agora = obter_data_atual()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        cursor = conn.execute("""
            INSERT OR IGNORE INTO natal_recompensas (

                user_id,

                recompensa_id,

                data
            )

            VALUES (?, ?, ?)
        """, (
            user_id,
            recompensa_id,
            agora,
        ))

        if cursor.rowcount == 0:
            return False

        if flocos > 0:

            conn.execute("""
                UPDATE natal_jogadores

                SET flocos = flocos + ?

                WHERE user_id = ?
            """, (
                flocos,
                user_id,
            ))

            conn.execute("""
                INSERT INTO natal_transacoes (

                    user_id,

                    tipo,

                    quantidade,

                    descricao,

                    data
                )

                VALUES (?, 'credito', ?, ?, ?)
            """, (
                user_id,
                flocos,
                descricao,
                agora,
            ))

        for item_id, quantidade in itens.items():

            conn.execute("""
                INSERT INTO natal_inventario (

                    user_id,

                    item_id,

                    quantidade
                )

                VALUES (?, ?, ?)

                ON CONFLICT(user_id, item_id)

                DO UPDATE SET

                    quantidade = quantidade + excluded.quantidade
            """, (
                user_id,
                item_id,
                quantidade,
            ))

            conn.execute("""
                INSERT INTO natal_transacoes (

                    user_id,

                    tipo,

                    item_id,

                    quantidade,

                    descricao,

                    data
                )

                VALUES (?, 'credito', ?, ?, ?, ?)
            """, (
                user_id,
                item_id,
                quantidade,
                descricao,
                agora,
            ))

    return True


# ==========================================
# CONSULTAR HISTÓRICO
# ==========================================

def consultar_historico(user_id, limite=10):

    if not isinstance(limite, int) or limite < 1:
        return []

    limite = min(limite, 50)

    with obter_conexao() as conn:

        resultados = conn.execute("""
            SELECT

                tipo,

                item_id,

                quantidade,

                descricao,

                data

            FROM natal_transacoes

            WHERE user_id = ?

            ORDER BY id DESC

            LIMIT ?
        """, (
            user_id,
            limite,
        )).fetchall()

        return [
            dict(resultado)
            for resultado in resultados
        ]
