
import json
import random

from datetime import datetime, timedelta

from .banco import obter_conexao
from .configuracoes import FUSO_HORARIO, ITENS_NATALINOS


# ==========================================
# CONFIGURAÇÕES DAS ENTREGAS
# ==========================================

QUANTIDADE_ENTREGAS_DIARIAS = 3

DIFICULDADES = {
    "facil": {
        "nome": "Fácil",
        "emoji": "🟢",
        "flocos": (35, 55),
        "pontos": (10, 18),
    },
    "media": {
        "nome": "Média",
        "emoji": "🟡",
        "flocos": (70, 105),
        "pontos": (20, 32),
    },
    "dificil": {
        "nome": "Difícil",
        "emoji": "🔴",
        "flocos": (130, 190),
        "pontos": (38, 55),
    },
}


# ==========================================
# MODELOS DE SOLICITAÇÕES
# ==========================================

MODELOS_ENTREGAS = {
    "facil": [
        {
            "titulo": "Reforçando a oficina",
            "descricao": "A oficina precisa de madeira para continuar trabalhando.",
            "materiais": {
                "madeira_natalina": 3,
            },
        },
        {
            "titulo": "Preparativos festivos",
            "descricao": "Precisamos de tecidos para decorar a vila.",
            "materiais": {
                "tecido_festivo": 3,
            },
        },
        {
            "titulo": "Pequenos presentes",
            "descricao": "Ajude a separar alguns presentes para os moradores.",
            "materiais": {
                "presente_vermelho": 2,
            },
        },
    ],

    "media": [
        {
            "titulo": "Reparo nas construções",
            "descricao": "A oficina precisa de materiais para reforçar as construções.",
            "materiais": {
                "madeira_natalina": 4,
                "tecido_festivo": 2,
            },
        },
        {
            "titulo": "Decoração brilhante",
            "descricao": "Lumi precisa de cristais para iluminar a vila.",
            "materiais": {
                "cristal_glacial": 2,
                "tecido_festivo": 2,
            },
        },
        {
            "titulo": "Entrega especial",
            "descricao": "Pipo está organizando uma remessa de presentes.",
            "materiais": {
                "presente_vermelho": 3,
                "madeira_natalina": 2,
            },
        },
    ],

    "dificil": [
        {
            "titulo": "Fragmentos da estrela",
            "descricao": "Noel precisa de fragmentos para continuar a restauração da estrela.",
            "materiais": {
                "estrela_fragmentada": 2,
                "cristal_glacial": 2,
            },
        },
        {
            "titulo": "Presentes da esperança",
            "descricao": "Uma grande entrega precisa ser preparada para a vila.",
            "materiais": {
                "presente_dourado": 2,
                "presente_vermelho": 3,
            },
        },
        {
            "titulo": "Energia para a oficina",
            "descricao": "A oficina precisa de recursos raros para concluir um projeto.",
            "materiais": {
                "estrela_fragmentada": 1,
                "cristal_glacial": 3,
                "madeira_natalina": 3,
            },
        },
    ],
}


# ==========================================
# DATA ATUAL
# ==========================================

def obter_agora():
    return datetime.now(FUSO_HORARIO)


# ==========================================
# GERAR UMA SOLICITAÇÃO
# ==========================================

def gerar_pedido(dificuldade):

    modelo = random.choice(MODELOS_ENTREGAS[dificuldade])
    dados_dificuldade = DIFICULDADES[dificuldade]

    recompensa_flocos = random.randint(
        *dados_dificuldade["flocos"]
    )

    recompensa_pontos = random.randint(
        *dados_dificuldade["pontos"]
    )

    pedido = {
        "titulo": modelo["titulo"],
        "descricao": modelo["descricao"],
        "dificuldade": dificuldade,
        "materiais": modelo["materiais"],
    }

    return {
        "pedido": pedido,
        "recompensa_flocos": recompensa_flocos,
        "recompensa_pontos": recompensa_pontos,
    }


# ==========================================
# GERAR AS ENTREGAS DIÁRIAS
# ==========================================

def gerar_entregas_diarias(user_id):

    agora_dt = obter_agora()
    agora = agora_dt.isoformat()
    data_hoje = agora_dt.date().isoformat()
    
    proxima_meia_noite = (
        agora.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        + timedelta(days=1)
    )

    agora_texto = agora.isoformat()
    expiracao_texto = proxima_meia_noite.isoformat()

    dificuldades = ["facil", "media", "dificil"]

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        conn.execute("""
            INSERT OR IGNORE INTO natal_jogadores (
                user_id,
                criado_em
            )
            VALUES (?, ?)
        """, (
            user_id,
            agora_texto,
        ))

        conn.execute("""
            UPDATE natal_entregas
            SET status = 'expirada'
            WHERE user_id = ?
            AND status = 'ativa'
            AND data_rotacao < ?
        """, (
            user_id,
            data_hoje,
        ))

        existentes = conn.execute("""
            SELECT slot
            FROM natal_entregas
            WHERE user_id = ?
            AND data_rotacao = ?
        """, (
            user_id,
            data_hoje,
        )).fetchall()

        slots_existentes = {
            linha["slot"]
            for linha in existentes
        }

        for slot, dificuldade in enumerate(dificuldades, start=1):

            if slot in slots_existentes:
                continue

            resultado = gerar_pedido(dificuldade)

            pedido_id = f"{data_hoje}_{slot}"

            pedido_json = json.dumps(
                resultado["pedido"],
                ensure_ascii=False,
            )

            conn.execute("""
                INSERT OR IGNORE INTO natal_entregas (
                    user_id,
                    pedido_id,
                    pedido_json,
                    data_rotacao,
                    slot,
                    criado_em,
                    expira_em,
                    recompensa_flocos,
                    recompensa_pontos
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                pedido_id,
                pedido_json,
                data_hoje,
                slot,
                agora_texto,
                expiracao_texto,
                resultado["recompensa_flocos"],
                resultado["recompensa_pontos"],
            ))


# ==========================================
# CONSULTAR ENTREGAS DO JOGADOR
# ==========================================

def consultar_entregas(user_id):

    gerar_entregas_diarias(user_id)

    agora = obter_agora().isoformat()
    data_hoje = obter_agora().date().isoformat()

    with obter_conexao() as conn:

        resultados = conn.execute("""
            SELECT *
            FROM natal_entregas
            WHERE user_id = ?
            AND data_rotacao = ?
            AND status = 'ativa'
            AND expira_em > ?
            ORDER BY slot ASC
        """, (
            user_id,
            data_hoje,
            agora,
        )).fetchall()

        entregas = []

        for linha in resultados:

            entrega = dict(linha)

            entrega["pedido"] = json.loads(
                entrega.pop("pedido_json")
            )

            entregas.append(entrega)

        return entregas


# ==========================================
# CONFIRMAR UMA ENTREGA
# ==========================================

def concluir_entrega(user_id, entrega_id):

    agora = obter_agora()
    agora_texto = agora.isoformat()

    with obter_conexao() as conn:

        conn.execute("BEGIN IMMEDIATE")

        entrega = conn.execute("""
            SELECT *
            FROM natal_entregas
            WHERE id = ?
            AND user_id = ?
        """, (
            entrega_id,
            user_id,
        )).fetchone()

        if entrega is None:
            return {
                "sucesso": False,
                "motivo": "nao_encontrada",
            }

        if entrega["status"] != "ativa":
            return {
                "sucesso": False,
                "motivo": "indisponivel",
            }

        if entrega["expira_em"] <= agora_texto:

            conn.execute("""
                UPDATE natal_entregas
                SET status = 'expirada'
                WHERE id = ?
            """, (entrega_id,))

            return {
                "sucesso": False,
                "motivo": "expirada",
            }

        pedido = json.loads(entrega["pedido_json"])
        materiais = pedido["materiais"]

        # ----------------------------------
        # VALIDAR TODOS OS MATERIAIS
        # ----------------------------------

        inventario = conn.execute("""
            SELECT item_id, quantidade
            FROM natal_inventario
            WHERE user_id = ?
        """, (user_id,)).fetchall()

        quantidades = {
            item["item_id"]: item["quantidade"]
            for item in inventario
        }

        faltantes = {}

        for item_id, quantidade_necessaria in materiais.items():

            quantidade_atual = quantidades.get(item_id, 0)

            if quantidade_atual < quantidade_necessaria:
                faltantes[item_id] = (
                    quantidade_necessaria - quantidade_atual
                )

        if faltantes:
            return {
                "sucesso": False,
                "motivo": "materiais_insuficientes",
                "faltantes": faltantes,
            }

        # ----------------------------------
        # CONSUMIR MATERIAIS
        # ----------------------------------

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

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Falha inesperada ao consumir material da entrega."
                )

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
                f"Entrega natalina: {pedido['titulo']}",
                agora_texto,
            ))

        # ----------------------------------
        # CONCEDER RECOMPENSAS
        # ----------------------------------

        flocos = entrega["recompensa_flocos"]
        pontos = entrega["recompensa_pontos"]

        conn.execute("""
            UPDATE natal_jogadores
            SET flocos = flocos + ?,
                pontos = pontos + ?
            WHERE user_id = ?
        """, (
            flocos,
            pontos,
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
            f"Recompensa da entrega: {pedido['titulo']}",
            agora_texto,
        ))

        # ----------------------------------
        # MARCAR COMO CONCLUÍDA
        # ----------------------------------

        conn.execute("""
            UPDATE natal_entregas
            SET status = 'concluida',
                concluida_em = ?
            WHERE id = ?
            AND status = 'ativa'
        """, (
            agora_texto,
            entrega_id,
        ))

        return {
            "sucesso": True,
            "titulo": pedido["titulo"],
            "flocos": flocos,
            "pontos": pontos,
        }
