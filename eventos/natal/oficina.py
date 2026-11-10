import json
from .banco import obter_conexao
from .inventario import registrar_jogador, obter_data_atual
from .configuracoes import ITENS_NATALINOS


# ============================================================
# RECEITAS DE FABRICAÇÃO
# ============================================================

RECEITAS = {
    "presente_vermelho": {
        "nome": "Presente Vermelho",
        "emoji": "🎁",
        "materiais": {
            "madeira_natalina": 3,
            "tecido_festivo": 2,
        },
        "quantidade": 1,
    },
    "presente_dourado": {
        "nome": "Presente Dourado",
        "emoji": "🎁",
        "materiais": {
            "tecido_festivo": 2,
            "cristal_glacial": 2,
            "estrela_fragmentada": 1,
        },
        "quantidade": 1,
    },
}


# ============================================================
# PROGRESSÃO COLETIVA DA VILA
# ============================================================

MELHORIAS_VILA = {
    "praca_congelada": {
        "nome": "Praça Congelada",
        "descricao": "Recuperar a praça central e abrir caminho pelo gelo.",
        "emoji": "🏘️",
        "ordem": 1,
        "materiais": {
            "madeira_natalina": 30,
            "tecido_festivo": 15,
        },
        "beneficio": "A praça central da vila foi restaurada.",
    },
    "oficina_noel": {
        "nome": "Oficina do Noel",
        "descricao": "Reconstruir a oficina onde os presentes são fabricados.",
        "emoji": "🛠️",
        "ordem": 2,
        "materiais": {
            "madeira_natalina": 40,
            "tecido_festivo": 25,
            "cristal_glacial": 10,
        },
        "beneficio": "A oficina está pronta para produzir presentes.",
    },
    "iluminacao_estelar": {
        "nome": "Iluminação Estelar",
        "descricao": "Instalar cristais mágicos para iluminar as ruas.",
        "emoji": "💡",
        "ordem": 3,
        "materiais": {
            "madeira_natalina": 20,
            "cristal_glacial": 25,
            "estrela_fragmentada": 10,
        },
        "beneficio": "As luzes mágicas voltaram a iluminar a vila.",
    },
    "grande_arvore": {
        "nome": "Grande Árvore",
        "descricao": "Restaurar a árvore central e devolver sua magia.",
        "emoji": "🎄",
        "ordem": 4,
        "materiais": {
            "madeira_natalina": 30,
            "tecido_festivo": 20,
            "cristal_glacial": 20,
            "estrela_fragmentada": 20,
        },
        "beneficio": "A Grande Árvore voltou a brilhar!",
    },
}


# ============================================================
# BANCO DE DADOS
# ============================================================

def inicializar_oficina():
    """
    Cria as tabelas próprias da oficina.
    Pode ser chamada várias vezes sem apagar o progresso.
    """

    with obter_conexao() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_oficina_progresso (
                melhoria_id TEXT PRIMARY KEY,
                progresso_json TEXT NOT NULL,
                concluida INTEGER NOT NULL DEFAULT 0,
                concluida_em TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_oficina_contribuicoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                melhoria_id TEXT NOT NULL,
                material_id TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                data TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES natal_jogadores(user_id),
                FOREIGN KEY (melhoria_id)
                    REFERENCES natal_oficina_progresso(melhoria_id)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_natal_oficina_usuario
            ON natal_oficina_contribuicoes(user_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_natal_oficina_melhoria
            ON natal_oficina_contribuicoes(melhoria_id)
        """)

        for melhoria_id, melhoria in MELHORIAS_VILA.items():
            progresso_inicial = {
                material_id: 0
                for material_id in melhoria["materiais"]
            }

            conn.execute("""
                INSERT OR IGNORE INTO natal_oficina_progresso (
                    melhoria_id,
                    progresso_json,
                    concluida
                )
                VALUES (?, ?, 0)
            """, (
                melhoria_id,
                json.dumps(progresso_inicial),
            ))


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def _validar_quantidade(quantidade):
    return (
        isinstance(quantidade, int)
        and not isinstance(quantidade, bool)
        and quantidade > 0
    )


def _obter_progresso(conn, melhoria_id):
    registro = conn.execute("""
        SELECT progresso_json, concluida, concluida_em
        FROM natal_oficina_progresso
        WHERE melhoria_id = ?
    """, (melhoria_id,)).fetchone()

    if registro is None:
        return None

    return {
        "progresso": json.loads(registro["progresso_json"]),
        "concluida": bool(registro["concluida"]),
        "concluida_em": registro["concluida_em"],
    }


def _obter_proxima_melhoria(conn):
    for melhoria_id, melhoria in sorted(
        MELHORIAS_VILA.items(),
        key=lambda item: item[1]["ordem"],
    ):
        progresso = _obter_progresso(conn, melhoria_id)

        if progresso and not progresso["concluida"]:
            return melhoria_id

    return None


# ============================================================
# CONSULTA DAS RECEITAS
# ============================================================

def consultar_receitas():
    """
    Retorna todas as receitas disponíveis na oficina.
    """

    return RECEITAS.copy()


# ============================================================
# FABRICAÇÃO DE PRESENTES
# ============================================================

def fabricar_presente(user_id, receita_id, quantidade=1):
    """
    Consome materiais e fabrica presentes.
    A operação é feita em uma única transação.
    """

    if receita_id not in RECEITAS:
        return {
            "sucesso": False,
            "motivo": "receita_inexistente",
        }

    if not _validar_quantidade(quantidade):
        return {
            "sucesso": False,
            "motivo": "quantidade_invalida",
        }

    receita = RECEITAS[receita_id]

    registrar_jogador(user_id)
    inicializar_oficina()

    materiais_necessarios = {
        material_id: custo * quantidade
        for material_id, custo in receita["materiais"].items()
    }

    with obter_conexao() as conn:
        conn.execute("BEGIN IMMEDIATE")

        # Primeiro verifica se o jogador possui tudo.
        faltantes = {}

        for material_id, necessario in materiais_necessarios.items():
            registro = conn.execute("""
                SELECT quantidade
                FROM natal_inventario
                WHERE user_id = ? AND item_id = ?
            """, (str(user_id), material_id)).fetchone()

            disponivel = registro["quantidade"] if registro else 0

            if disponivel < necessario:
                faltantes[material_id] = necessario - disponivel

        if faltantes:
            return {
                "sucesso": False,
                "motivo": "materiais_insuficientes",
                "faltantes": faltantes,
            }

        # Consome os materiais.
        for material_id, necessario in materiais_necessarios.items():
            conn.execute("""
                UPDATE natal_inventario
                SET quantidade = quantidade - ?
                WHERE user_id = ? AND item_id = ?
            """, (necessario, str(user_id), material_id))

            conn.execute("""
                INSERT INTO natal_transacoes (
                    user_id,
                    tipo,
                    item_id,
                    quantidade,
                    descricao,
                    data
                )
                VALUES (?, 'saida', ?, ?, ?, ?)
            """, (
                str(user_id),
                material_id,
                necessario,
                f"Fabricação de {receita['nome']}",
                obter_data_atual(),
            ))

        # Entrega os presentes fabricados.
        total_fabricado = receita["quantidade"] * quantidade

        conn.execute("""
            INSERT INTO natal_inventario (
                user_id,
                item_id,
                quantidade
            )
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, item_id)
            DO UPDATE SET quantidade =
                quantidade + excluded.quantidade
        """, (
            str(user_id),
            receita_id,
            total_fabricado,
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
            VALUES (?, 'entrada', ?, ?, ?, ?)
        """, (
            str(user_id),
            receita_id,
            total_fabricado,
            "Presente fabricado na Oficina Natalina",
            obter_data_atual(),
        ))

    return {
        "sucesso": True,
        "presente": receita_id,
        "nome": receita["nome"],
        "quantidade": total_fabricado,
    }


# ============================================================
# CONSULTA DA PROGRESSÃO DA VILA
# ============================================================

def consultar_progresso_vila():
    """
    Retorna o progresso de todas as melhorias coletivas.
    """

    inicializar_oficina()

    resultado = []

    with obter_conexao() as conn:
        melhoria_atual = _obter_proxima_melhoria(conn)

        for melhoria_id, melhoria in sorted(
            MELHORIAS_VILA.items(),
            key=lambda item: item[1]["ordem"],
        ):
            estado = _obter_progresso(conn, melhoria_id)

            materiais = {}

            for material_id, objetivo in melhoria["materiais"].items():
                atual = estado["progresso"].get(material_id, 0)

                materiais[material_id] = {
                    "atual": atual,
                    "objetivo": objetivo,
                    "concluido": atual >= objetivo,
                }

            resultado.append({
                "id": melhoria_id,
                "nome": melhoria["nome"],
                "descricao": melhoria["descricao"],
                "emoji": melhoria["emoji"],
                "ordem": melhoria["ordem"],
                "materiais": materiais,
                "concluida": estado["concluida"],
                "ativa": melhoria_id == melhoria_atual,
                "beneficio": melhoria["beneficio"],
            })

    return resultado


# ============================================================
# CONTRIBUIÇÃO PARA A VILA
# ============================================================

def contribuir_para_vila(user_id, material_id, quantidade):
    """
    Doa materiais para a próxima melhoria da vila.
    O jogador só pode contribuir com materiais necessários
    para a etapa coletiva atualmente ativa.
    """

    if material_id not in ITENS_NATALINOS:
        return {
            "sucesso": False,
            "motivo": "material_invalido",
        }

    if ITENS_NATALINOS[material_id]["tipo"] != "material":
        return {
            "sucesso": False,
            "motivo": "item_nao_e_material",
        }

    if not _validar_quantidade(quantidade):
        return {
            "sucesso": False,
            "motivo": "quantidade_invalida",
        }

    registrar_jogador(user_id)
    inicializar_oficina()

    with obter_conexao() as conn:
        conn.execute("BEGIN IMMEDIATE")

        melhoria_id = _obter_proxima_melhoria(conn)

        if melhoria_id is None:
            return {
                "sucesso": False,
                "motivo": "vila_completa",
            }

        melhoria = MELHORIAS_VILA[melhoria_id]
        estado = _obter_progresso(conn, melhoria_id)

        if material_id not in melhoria["materiais"]:
            return {
                "sucesso": False,
                "motivo": "material_nao_necessario",
                "melhoria": melhoria["nome"],
            }

        objetivo = melhoria["materiais"][material_id]
        atual = estado["progresso"].get(material_id, 0)
        restante = objetivo - atual

        if quantidade > restante:
            return {
                "sucesso": False,
                "motivo": "quantidade_acima_do_necessario",
                "restante": restante,
            }

        registro = conn.execute("""
            SELECT quantidade
            FROM natal_inventario
            WHERE user_id = ? AND item_id = ?
        """, (str(user_id), material_id)).fetchone()

        disponivel = registro["quantidade"] if registro else 0

        if disponivel < quantidade:
            return {
                "sucesso": False,
                "motivo": "materiais_insuficientes",
                "disponivel": disponivel,
                "necessario": quantidade,
            }

        # Retira os materiais do jogador.
        conn.execute("""
            UPDATE natal_inventario
            SET quantidade = quantidade - ?
            WHERE user_id = ? AND item_id = ?
        """, (quantidade, str(user_id), material_id))

        # Atualiza o progresso coletivo.
        estado["progresso"][material_id] = atual + quantidade

        concluida = all(
            estado["progresso"].get(item, 0) >= total
            for item, total in melhoria["materiais"].items()
        )

        data_atual = obter_data_atual()

        conn.execute("""
            UPDATE natal_oficina_progresso
            SET progresso_json = ?,
                concluida = ?,
                concluida_em = ?
            WHERE melhoria_id = ?
        """, (
            json.dumps(estado["progresso"]),
            int(concluida),
            data_atual if concluida else None,
            melhoria_id,
        ))

        # Registra quem contribuiu e quanto.
        conn.execute("""
            INSERT INTO natal_oficina_contribuicoes (
                user_id,
                melhoria_id,
                material_id,
                quantidade,
                data
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            str(user_id),
            melhoria_id,
            material_id,
            quantidade,
            data_atual,
        ))

        # Histórico individual de consumo.
        conn.execute("""
            INSERT INTO natal_transacoes (
                user_id,
                tipo,
                item_id,
                quantidade,
                descricao,
                data
            )
            VALUES (?, 'saida', ?, ?, ?, ?)
        """, (
            str(user_id),
            material_id,
            quantidade,
            f"Contribuição para {melhoria['nome']}",
            data_atual,
        ))

    return {
        "sucesso": True,
        "melhoria": melhoria["nome"],
        "material": material_id,
        "quantidade": quantidade,
        "progresso_atual": atual + quantidade,
        "objetivo": objetivo,
        "melhoria_concluida": concluida,
        "beneficio": melhoria["beneficio"] if concluida else None,
    }


# ============================================================
# RANKING DE CONTRIBUIÇÕES
# ============================================================

def consultar_ranking_vila(limite=10):
    """
    Retorna os jogadores que mais contribuíram
    para a reconstrução da vila.
    """

    if not _validar_quantidade(limite):
        limite = 10

    inicializar_oficina()

    with obter_conexao() as conn:
        registros = conn.execute("""
            SELECT
                user_id,
                SUM(quantidade) AS total_materiais,
                COUNT(*) AS total_contribuicoes
            FROM natal_oficina_contribuicoes
            GROUP BY user_id
            ORDER BY total_materiais DESC,
                     total_contribuicoes DESC
            LIMIT ?
        """, (limite,)).fetchall()

    return [
        {
            "user_id": registro["user_id"],
            "total_materiais": registro["total_materiais"],
            "total_contribuicoes": registro["total_contribuicoes"],
        }
        for registro in registros
    ]


# ============================================================
# CONTRIBUIÇÃO INDIVIDUAL
# ============================================================

def consultar_contribuicao_jogador(user_id):
    """
    Retorna o total de materiais doados por um jogador.
    """

    inicializar_oficina()

    with obter_conexao() as conn:
        registros = conn.execute("""
            SELECT
                melhoria_id,
                SUM(quantidade) AS total_materiais
            FROM natal_oficina_contribuicoes
            WHERE user_id = ?
            GROUP BY melhoria_id
        """, (str(user_id),)).fetchall()

    return {
        registro["melhoria_id"]: registro["total_materiais"]
        for registro in registros
    }
