"""
Inspeciona (e opcionalmente limpa) os dados de perfil personalizado de um usuário.
 
Uso:
    python verificar_perfil.py <ID_DO_USUARIO>          -> só mostra os dados salvos
    python verificar_perfil.py <ID_DO_USUARIO> --limpar -> mostra e depois apaga o perfil personalizado
 
Recomendado: pare o bot antes de rodar com --limpar.
"""
 
import sqlite3
import sys
 
def cor_hex_valida(valor):
    v = valor.lstrip("#")
    if len(v) != 6:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in v)
 
def main():
    if len(sys.argv) < 2:
        print("Uso: python verificar_perfil.py <ID_DO_USUARIO> [--limpar]")
        sys.exit(1)
 
    usuario_id = str(sys.argv[1])
    limpar = "--limpar" in sys.argv
 
    con = sqlite3.connect("jogadorbot.db")
    cur = con.cursor()
    cur.execute(
        "SELECT nome_personalizado, descricao, avatar_url, cor_hex FROM perfil_personalizado WHERE usuario_id = ?",
        (usuario_id,)
    )
    resultado = cur.fetchone()
 
    if not resultado:
        print(f"Usuário {usuario_id} não tem nenhum dado em perfil_personalizado.")
        print("O problema provavelmente NÃO está nessa tabela — me manda o log do console pra eu confirmar a causa real.")
        con.close()
        return
 
    nome, descricao, avatar_url, cor_hex = resultado
    print(f"--- Perfil personalizado de {usuario_id} ---")
    print(f"Nome personalizado: {nome!r}")
    print(f"Descrição: {descricao!r}  (tamanho: {len(descricao) if descricao else 0})")
    print(f"URL da foto: {avatar_url!r}")
    print(f"Cor hex: {cor_hex!r}")
 
    suspeitas = []
    if avatar_url and not avatar_url.startswith(("http://", "https://")):
        suspeitas.append("A URL da foto não começa com http:// ou https://")
    if cor_hex and not cor_hex_valida(cor_hex):
        suspeitas.append("A cor hex está em formato inválido")
    if descricao and len(descricao) > 200:
        suspeitas.append("A descrição passa de 200 caracteres")
 
    if suspeitas:
        print("\n⚠️ Possíveis causas do erro:")
        for s in suspeitas:
            print(f"  - {s}")
    else:
        print("\nNenhum valor visivelmente inválido encontrado. Pode ser uma URL de imagem que existe,")
        print("mas que o Discord não consegue processar como imagem (ex: link de uma página HTML, não do arquivo direto).")
 
    if limpar:
        cur.execute("DELETE FROM perfil_personalizado WHERE usuario_id = ?", (usuario_id,))
        con.commit()
        print(f"\n✅ Perfil personalizado de {usuario_id} apagado. O perfil dele volta a usar nome/foto padrão do Discord.")
    else:
        print("\n(Nada foi apagado. Rode novamente com --limpar se quiser resetar o perfil personalizado dele.)")
 
    con.close()
 
if __name__ == "__main__":
    main()
