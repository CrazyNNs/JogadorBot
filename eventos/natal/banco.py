import os
import sqlite3

from contextlib import contextmanager

from .configuracoes import GUARDIAO


# ==========================================
# CONFIGURAÇÃO DO BANCO-
# ==========================================

DB_PATH = os.path.abspath("jogadorbot.db")


# ==========================================
# CONEXÃO COM O SQLITE
# ==========================================

@contextmanager
def obter_conexao():
    conexao = sqlite3.connect(DB_PATH, timeout=30)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


# ==========================================
# INICIALIZAÇÃO DO BANCO
# ==========================================

def inicializar_banco():

    with obter_conexao() as conn:

        # ----------------------------------
        # JOGADORES
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_jogadores (

                user_id INTEGER PRIMARY KEY,

                flocos INTEGER NOT NULL DEFAULT 0,

                pontos INTEGER NOT NULL DEFAULT 0,

                exploracoes INTEGER NOT NULL DEFAULT 0,

                data_exploracao TEXT,

                criado_em TEXT NOT NULL
            )
        """)

        # ----------------------------------
        # INVENTÁRIO
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_inventario (

                user_id INTEGER NOT NULL,

                item_id TEXT NOT NULL,

                quantidade INTEGER NOT NULL DEFAULT 0,

                PRIMARY KEY (user_id, item_id),

                FOREIGN KEY (user_id)
                    REFERENCES natal_jogadores(user_id)
            )
        """)

        # ----------------------------------
        # HISTÓRICO DE TRANSAÇÕES
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_transacoes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                tipo TEXT NOT NULL,

                item_id TEXT,

                quantidade INTEGER NOT NULL,

                descricao TEXT,

                data TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES natal_jogadores(user_id)
            )
        """)

        # ----------------------------------
        # RECOMPENSAS ÚNICAS
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_recompensas (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                recompensa_id TEXT NOT NULL,

                data TEXT NOT NULL,

                UNIQUE(user_id, recompensa_id),

                FOREIGN KEY (user_id)
                    REFERENCES natal_jogadores(user_id)
            )
        """)

        # ----------------------------------
        # ÍNDICES
        # ----------------------------------

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_transacoes_usuario

            ON natal_transacoes(user_id)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_inventario_usuario

            ON natal_inventario(user_id)
        """)

        # ----------------------------------
        # GUARDIÃO
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_guardiao (

                id INTEGER PRIMARY KEY CHECK (id = 1),

                hp_maximo INTEGER NOT NULL,

                hp_atual INTEGER NOT NULL,

                fase INTEGER NOT NULL DEFAULT 1,

                derrotado INTEGER NOT NULL DEFAULT 0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_contribuicoes (

                user_id INTEGER PRIMARY KEY,

                dano_total INTEGER NOT NULL DEFAULT 0,

                participacoes INTEGER NOT NULL DEFAULT 0,

                ultima_contribuicao TEXT,

                FOREIGN KEY (user_id)
                    REFERENCES natal_jogadores(user_id)
            )
        """)

        # ----------------------------------
        # METAS COMUNITÁRIAS
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_metas (

                meta_id TEXT PRIMARY KEY,

                progresso INTEGER NOT NULL DEFAULT 0,

                objetivo INTEGER NOT NULL,

                concluida INTEGER NOT NULL DEFAULT 0
            )
        """)
        
        # ----------------------------------
        # SOLICITAÇÕES DE ENTREGA
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_entregas (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                pedido_id TEXT NOT NULL,

                pedido_json TEXT NOT NULL,

                data_rotacao TEXT NOT NULL,

                slot INTEGER NOT NULL,

                criado_em TEXT NOT NULL,

                expira_em TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'ativa',

                recompensa_flocos INTEGER NOT NULL DEFAULT 0,

                recompensa_pontos INTEGER NOT NULL DEFAULT 0,

                concluida_em TEXT,

                FOREIGN KEY (user_id)
                    REFERENCES natal_jogadores(user_id),

                UNIQUE (user_id, data_rotacao, slot)
            )
        """)

        # ----------------------------------
        # ÍNDICES DAS ENTREGAS
        # ----------------------------------

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_entregas_usuario

            ON natal_entregas(user_id, status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_entregas_expiracao

            ON natal_entregas(expira_em, status)
        """)

        # ----------------------------------
        # EXPLORAÇÕES NATALINAS
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_exploracoes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                regiao TEXT NOT NULL,

                etapa INTEGER NOT NULL DEFAULT 1,

                status TEXT NOT NULL DEFAULT 'ativa',

                estado_json TEXT NOT NULL,

                data_rotacao TEXT NOT NULL,

                iniciada_em TEXT NOT NULL,

                atualizada_em TEXT NOT NULL,

                expira_em TEXT NOT NULL,

                FOREIGN KEY (user_id)
                    REFERENCES natal_jogadores(user_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_exploracao_eventos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                exploracao_id INTEGER NOT NULL,

                etapa INTEGER NOT NULL,

                evento_id TEXT NOT NULL,

                narrativa TEXT NOT NULL,

                escolha_id TEXT,

                escolha_texto TEXT,

                consequencia_json TEXT,

                criado_em TEXT NOT NULL,

                FOREIGN KEY (exploracao_id)
                    REFERENCES natal_exploracoes(id)
                    ON DELETE CASCADE,

                UNIQUE (exploracao_id, etapa)
            )
        """)

        # ----------------------------------
        # ÍNDICES DAS EXPLORAÇÕES
        # ----------------------------------

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_exploracoes_usuario

            ON natal_exploracoes(user_id, status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_exploracoes_expiracao

            ON natal_exploracoes(expira_em, status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_exploracao_eventos

            ON natal_exploracao_eventos(exploracao_id, etapa)
        """)


        # ----------------------------------
        # HISTÓRICO DOS ACONTECIMENTOS
        # ----------------------------------

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_exploracao_eventos (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                exploracao_id INTEGER NOT NULL,

                etapa INTEGER NOT NULL,

                evento_id TEXT NOT NULL,

                narrativa TEXT NOT NULL,

                escolha_id TEXT,

                escolha_texto TEXT,

                consequencia_json TEXT,

                criado_em TEXT NOT NULL,

                FOREIGN KEY (exploracao_id)
                    REFERENCES natal_exploracoes(id)
                    ON DELETE CASCADE
            )
        """)

        # ----------------------------------
        # ÍNDICES DAS EXPLORAÇÕES
        # ----------------------------------

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_exploracoes_usuario_data

            ON natal_exploracoes(user_id, data_rotacao)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_exploracoes_status

            ON natal_exploracoes(status, expira_em)
        """)

        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_natal_exploracao_ativa_usuario

            ON natal_exploracoes(user_id)
            WHERE status = 'ativa'
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_exploracao_eventos_sessao

            ON natal_exploracao_eventos(exploracao_id, etapa)
        """)

        
        # ----------------------------------
        # INICIALIZAÇÃO DO GUARDIÃO
        # ----------------------------------

        conn.execute("""
            INSERT OR IGNORE INTO natal_guardiao (

                id,

                hp_maximo,

                hp_atual,

                fase,

                derrotado
            )

            VALUES (1, ?, ?, 1, 0)
        """, (
            GUARDIAO["hp_maximo"],
            GUARDIAO["hp_maximo"],
        ))
