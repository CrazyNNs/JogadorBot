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
