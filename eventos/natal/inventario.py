# ==========================================
# ADICIONAR MATERIAL
# ==========================================

def adicionar_item(user_id, item_id, quantidade, descricao=None):

    if quantidade <= 0:
        return False

    registrar_jogador(user_id)

    agora = datetime.now(FUSO_HORARIO).isoformat()

    with obter_conexao() as conn:

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
            descricao or "Recebimento de material natalino",
            agora,
        ))

    return True
  
# ==========================================
# CONSULTAR INVENTÁRIO COMPLETO
# ==========================================

def consultar_inventario(user_id):

    registrar_jogador(user_id)

    with obter_conexao() as conn:

        jogador = conn.execute("""
            SELECT flocos

            FROM natal_jogadores

            WHERE user_id = ?
        """, (user_id,)).fetchone()

        itens = conn.execute("""
            SELECT item_id, quantidade

            FROM natal_inventario

            WHERE user_id = ?
            AND quantidade > 0

            ORDER BY item_id ASC
        """, (user_id,)).fetchall()

        return {
            "flocos": jogador["flocos"],

            "itens": {
                item["item_id"]: item["quantidade"]
                for item in itens
            },
        }

# ==========================================
# REMOVER MATERIAL
# ==========================================

def remover_item(user_id, item_id, quantidade, descricao=None):

    if quantidade <= 0:
        return False

    agora = datetime.now(FUSO_HORARIO).isoformat()

    with obter_conexao() as conn:

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
            descricao or "Consumo de material natalino",
            agora,
        ))

    return True

# ==========================================
# CONSUMIR VÁRIOS MATERIAIS
# ==========================================

def consumir_materiais(user_id, materiais, descricao=None):

    if not materiais:
        return False

    if any(
        quantidade <= 0
        for quantidade in materiais.values()
    ):
        return False

    agora = datetime.now(FUSO_HORARIO).isoformat()

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
                descricao or "Consumo de materiais",
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
    descricao=None,
):

    itens = itens or {}

    if flocos < 0:
        return False

    if any(
        quantidade <= 0
        for quantidade in itens.values()
    ):
        return False

    registrar_jogador(user_id)

    agora = datetime.now(FUSO_HORARIO).isoformat()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        try:

            conn.execute("""
                INSERT INTO natal_recompensas (
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

        except Exception as erro:

            if "UNIQUE constraint failed" in str(erro):
                return False

            raise

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
                descricao or "Recompensa especial",
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
                descricao or "Recompensa especial",
                agora,
            ))

    return True
