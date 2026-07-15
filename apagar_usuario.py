"""
Apaga TODOS os dados de um usuário específico do jogadorbot.db.

Uso:
    python apagar_usuario.py <ID_DO_USUARIO>

Recomendado: pare o bot antes de rodar este script, para evitar
conflitos de acesso ao arquivo do banco (jogadorbot.db).
"""

import sqlite3
import sys

# Tabelas que possuem uma coluna usuario_id (TEXT)
TABELAS = [
    "conquistas_usuarios",
    "economia",
    "banners_usuarios",
    "banner_ativo",
    "level_usuarios",
    "banners_favoritos",
    "empregos_usuarios",
    "rewards_usuarios",
    "missoes_progresso",
    "contadores_usuarios",
    "missoes_customizadas_progresso",
    "admins",  # só remove se o usuário por acaso for admin
]

def main():
    if len(sys.argv) != 2:
        print("Uso: python apagar_usuario.py <ID_DO_USUARIO>")
        sys.exit(1)

    usuario_id = str(sys.argv[1])

    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()

    total_removido = 0
    print(f"Apagando dados do usuário {usuario_id}...\n")

    for tabela in TABELAS:
        try:
            cur.execute(f"DELETE FROM {tabela} WHERE usuario_id = ?", (usuario_id,))
            removidos = cur.rowcount
            total_removido += removidos
            print(f"  {tabela}: {removidos} linha(s) removida(s)")
        except sqlite3.OperationalError as e:
            print(f"  {tabela}: erro ao acessar ({e})")

    con.commit()
    con.close()

    print(f"\nConcluído. Total de linhas removidas: {total_removido}")
    print("O usuário será tratado como novo na próxima interação com o bot.")

if __name__ == "__main__":
    main()
