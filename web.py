# web.py
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)

DB_PATH = "/data/jogadorbot.db"

def adicionar_joyens(usuario_id, quantidade):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO economia (usuario_id, joyens) VALUES (?, ?)
        ON CONFLICT(usuario_id) DO UPDATE SET joyens = joyens + ?
    """, (str(usuario_id), quantidade, quantidade))
    con.commit()
    con.close()

# Token store global (você precisa compartilhar de alguma forma)
# Solução simples: arquivo de tokens
TOKENS_FILE = "/tmp/snake_tokens.txt"

def load_tokens():
    if not os.path.exists(TOKENS_FILE):
        return {}
    tokens = {}
    with open(TOKENS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if ':' in line:
                user_id, token = line.split(':', 1)
                tokens[user_id] = token
    return tokens

@app.route('/snake_eat', methods=['POST', 'OPTIONS'])
def snake_eat():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json or {}
        user_id = str(data.get('user_id', ''))
        token = data.get('token', '')
        apples = int(data.get('apples', 0))
        
        tokens = load_tokens()
        
        if tokens.get(user_id) != token:
            return jsonify({"success": False, "error": "Token inválido"}), 403
        
        if apples <= 0 or apples > 50:
            return jsonify({"success": False, "error": "Qtd inválida"}), 400
        
        reward = apples * 5
        adicionar_joyens(user_id, reward)
        return jsonify({"success": True, "reward": reward})
    except Exception as e:
        print(f"Erro: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/snake_game.html')
def snake_game():
    return send_from_directory('.', 'snake_game.html')

@app.route('/')
def home():
    return "🐍 Bot ativo!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
