import sqlite3
import os

from .configuracoes import GUARDIAO


# ==========================================
# CONFIGURAÇÃO DO BANCO
# ==========================================

DB_PATH = os.path.abspath("jogadorbot.db")


def obter_conexao():
    conexao = sqlite3.connect(
        DB_PATH,
        timeout=30,
    )

    conexao.row_factory = sqlite3.Row

    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


# ==========================================
# INICIALIZAÇÃO DAS TABELAS
# ==========================================

def inicializar_banco():

    with obter_conexao() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_jogadores (
                user_id INTEGER PRIMARY KEY,

                flocos INTEGER NOT NULL DEFAULT 0,

                pontos INTEGER NOT NULL DEFAULT 0,

                exploracoes INTEGER NOT NULL DEFAULT 0,

                data_exploracao TEXT,

                criado_em TEXT
            )
        """)

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

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_missoes (
                user_id INTEGER NOT NULL,

                missao_id TEXT NOT NULL,

                progresso INTEGER NOT NULL DEFAULT 0,

                concluida INTEGER NOT NULL DEFAULT 0,

                resgatada INTEGER NOT NULL DEFAULT 0,

                PRIMARY KEY (user_id, missao_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_transacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                tipo TEXT NOT NULL,

                item_id TEXT,

                quantidade INTEGER NOT NULL,

                descricao TEXT,

                data TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_recompensas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                recompensa_id TEXT NOT NULL,

                data TEXT NOT NULL,

                UNIQUE(user_id, recompensa_id)
            )
        """)
        
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

                ultima_contribuicao TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS natal_metas (
                meta_id TEXT PRIMARY KEY,

                progresso INTEGER NOT NULL DEFAULT 0,

                objetivo INTEGER NOT NULL,

                concluida INTEGER NOT NULL DEFAULT 0
            )
        """)

        # Inicializa o Guardião apenas se ainda não existir.

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

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_natal_transacoes_usuario
            ON natal_transacoes(user_id)
        """)

        conn.commit()
