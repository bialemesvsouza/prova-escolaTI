import os
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

fuso_br = timezone(timedelta(hours=-3))

def agora_iso():
    return datetime.now(fuso_br).isoformat()

def hoje_str():
    return datetime.now(fuso_br).strftime("%Y-%m-%d")

PREFIXO = "A"
RAZAO_PREFERENCIAL = 2

try:
    caminho_params = os.path.join(os.path.dirname(__file__), "..", "variante", "params.json")
    with open(caminho_params, "r") as f:
        dados = json.load(f)
        PREFIXO = dados.get("PREFIXO", dados.get("uso", {}).get("PREFIXO", "A"))
        RAZAO_PREFERENCIAL = int(dados.get("RAZAO_PREFERENCIAL", dados.get("uso", {}).get("RAZAO_PREFERENCIAL", 2)))
except Exception as e:
    print(f"Aviso: Não foi possível ler params.json, usando defaults (Prefixo: {PREFIXO}, Razao: {RAZAO_PREFERENCIAL})")

DB_DIR = "/data"
if not os.path.exists(DB_DIR) or not os.access(DB_DIR, os.W_OK):
    DB_DIR = "./data" 
    os.makedirs(DB_DIR, exist_ok=True)

DB_PATH = os.path.join(DB_DIR, "fila.db")

def get_db():
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS senhas (
                codigo TEXT PRIMARY KEY,
                tipo TEXT,
                status TEXT,
                emissao TEXT,
                chamada_em TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS controle_diario (
                data TEXT PRIMARY KEY,
                sequencia INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS estado_fila (
                id INTEGER PRIMARY KEY,
                preferenciais_seguidas INTEGER
            )
        """)
        conn.execute("INSERT OR IGNORE INTO estado_fila (id, preferenciais_seguidas) VALUES (1, 0)")
        
init_db()

class SenhaRequest(BaseModel):
    tipo: str = None

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/senhas", status_code=201)
def emitir_senha(req: dict):
    tipo = req.get("tipo")
    if tipo not in ["normal", "preferencial"]:
        return JSONResponse(status_code=422, content={"erro": "tipo_invalido"})
    
    hoje = hoje_str()
    emissao = agora_iso()
    
    with get_db() as conn:
        cursor = conn.execute("SELECT sequencia FROM controle_diario WHERE data = ?", (hoje,))
        row = cursor.fetchone()
        
        if row:
            seq = row["sequencia"] + 1
            conn.execute("UPDATE controle_diario SET sequencia = ? WHERE data = ?", (seq, hoje))
        else:
            seq = 1
            conn.execute("INSERT INTO controle_diario (data, sequencia) VALUES (?, ?)", (hoje, seq))
            
        codigo = f"{PREFIXO}{seq:03d}"
        
        conn.execute("""
            INSERT INTO senhas (codigo, tipo, status, emissao, chamada_em)
            VALUES (?, ?, ?, ?, ?)
        """, (codigo, tipo, "aguardando", emissao, ""))
        
        return {
            "codigo": codigo,
            "tipo": tipo,
            "emissao": emissao,
            "status": "aguardando"
        }

@app.get("/senhas/proxima")
def proxima_senha():
    with get_db() as conn:
        cursor = conn.execute("SELECT preferenciais_seguidas FROM estado_fila WHERE id = 1")
        pref_seguidas = cursor.fetchone()["preferenciais_seguidas"]
        
        senha_alvo = None
 
        if pref_seguidas < RAZAO_PREFERENCIAL:
            cursor = conn.execute("SELECT * FROM senhas WHERE status = 'aguardando' AND tipo = 'preferencial' ORDER BY emissao ASC LIMIT 1")
            senha_alvo = cursor.fetchone()

            if not senha_alvo:
                cursor = conn.execute("SELECT * FROM senhas WHERE status = 'aguardando' AND tipo = 'normal' ORDER BY emissao ASC LIMIT 1")
                senha_alvo = cursor.fetchone()

        else:
            cursor = conn.execute("SELECT * FROM senhas WHERE status = 'aguardando' AND tipo = 'normal' ORDER BY emissao ASC LIMIT 1")
            senha_alvo = cursor.fetchone()
            
            if not senha_alvo:
                cursor = conn.execute("SELECT * FROM senhas WHERE status = 'aguardando' AND tipo = 'preferencial' ORDER BY emissao ASC LIMIT 1")
                senha_alvo = cursor.fetchone()
                
        if not senha_alvo:
            return JSONResponse(status_code=404, content={"erro": "fila_vazia"})
            
        codigo = senha_alvo["codigo"]
        tipo_chamado = senha_alvo["tipo"]
        agora = agora_iso()
        
        nova_contagem = pref_seguidas + 1 if tipo_chamado == "preferencial" else 0
        conn.execute("UPDATE estado_fila SET preferenciais_seguidas = ? WHERE id = 1", (nova_contagem,))
        
        conn.execute("UPDATE senhas SET status = 'chamada', chamada_em = ? WHERE codigo = ?", (agora, codigo))
        
        return {
            "codigo": codigo,
            "tipo": tipo_chamado,
            "emissao": senha_alvo["emissao"],
            "status": "chamada",
            "chamada_em": agora
        }

@app.post("/senhas/{codigo}/concluir")
def concluir_senha(codigo: str):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM senhas WHERE codigo = ?", (codigo,))
        senha = cursor.fetchone()
        
        if not senha:
            return JSONResponse(status_code=404, content={"erro": "senha_nao_encontrada"})
        if senha["status"] != "chamada":
            return JSONResponse(status_code=409, content={"erro": "senha_nao_chamada"})
            
        conn.execute("UPDATE senhas SET status = 'concluida' WHERE codigo = ?", (codigo,))
        
        return {
            "codigo": senha["codigo"],
            "tipo": senha["tipo"],
            "emissao": senha["emissao"],
            "status": "concluida",
            "chamada_em": senha["chamada_em"]
        }

@app.post("/senhas/{codigo}/rechamar")
def rechamar_senha(codigo: str):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM senhas WHERE codigo = ?", (codigo,))
        senha = cursor.fetchone()
        
        if not senha:
            return JSONResponse(status_code=404, content={"erro": "senha_nao_encontrada"})
        if senha["status"] != "chamada":
            return JSONResponse(status_code=409, content={"erro": "senha_nao_chamada"})
            
        agora = agora_iso()
        conn.execute("UPDATE senhas SET chamada_em = ? WHERE codigo = ?", (agora, codigo))
        
        return {
            "codigo": senha["codigo"],
            "tipo": senha["tipo"],
            "emissao": senha["emissao"],
            "status": "chamada",
            "chamada_em": agora
        }

@app.post("/senhas/{codigo}/cancelar")
def cancelar_senha(codigo: str):
    with get_db() as conn:
        cursor = conn.execute("SELECT * FROM senhas WHERE codigo = ?", (codigo,))
        senha = cursor.fetchone()
        
        if not senha:
            return JSONResponse(status_code=404, content={"erro": "senha_nao_encontrada"})
        if senha["status"] != "aguardando":
            return JSONResponse(status_code=409, content={"erro": "senha_nao_aguardando"})
            
        conn.execute("UPDATE senhas SET status = 'cancelada' WHERE codigo = ?", (codigo,))
        
        return {
            "codigo": senha["codigo"],
            "tipo": senha["tipo"],
            "emissao": senha["emissao"],
            "status": "cancelada",
            "chamada_em": senha["chamada_em"]
        }

@app.get("/painel")
def consultar_painel():
    with get_db() as conn:
        cursor = conn.execute("""
            SELECT * FROM senhas 
            WHERE status IN ('chamada', 'concluida') 
            ORDER BY chamada_em DESC 
            LIMIT 5
        """)
        chamadas = []
        for row in cursor.fetchall():
            chamadas.append({
                "codigo": row["codigo"],
                "tipo": row["tipo"],
                "emissao": row["emissao"],
                "status": row["status"],
                "chamada_em": row["chamada_em"]
            })
            
        return {"chamadas": chamadas}