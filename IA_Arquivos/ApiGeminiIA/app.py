from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import google.generativeai as ai_gpt
import json
import pandas as pd
import sqlite3
import xml.etree.ElementTree as XmlParser

app = Flask(__name__)
CORS(app)
ai_gpt.configure(api_key='AIzaSyCapOMt_DGXzPznbcJNE1O-288D0Ng224Q')

def criar_db():
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tabela_metadados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            nome_arquivo TEXT,
            tipo_arquivo TEXT,
            cabecalhos TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tabela_conteudos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_metadado INTEGER,
            coluna_nome TEXT,
            tipo_dado TEXT,
            conteudo TEXT,
            FOREIGN KEY (id_metadado) REFERENCES tabela_metadados(id)
        )
    ''')
    conexao.commit()
    conexao.close()

def classificar_arquivo(conteudo_texto):
    try:
        modelo = ai_gpt.GenerativeModel('gemini-1.0-pro')
        prompt = f"Por favor, classifique o seguinte conteúdo: '{conteudo_texto[:500]}...'"
        resposta = modelo.generate_content(prompt)
        print(f"Resposta obtida da API: {resposta}")

        if resposta and hasattr(resposta, 'candidates') and len(resposta.candidates) > 0:
            texto_gerado = resposta.candidates[0].content
            classificacao = texto_gerado.parts[0].text if texto_gerado.parts else "Classificação indisponível."
        else:
            classificacao = "Classificação indisponível."
        return classificacao

    except Exception as erro:
        return f"Erro ao classificar: {str(erro)}"

@app.route('/analise', methods=['POST'])
def rota_classificar():
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo foi enviado."}), 400

    arquivo = request.files['file']
    tipo_arquivo = arquivo.filename.split('.')[-1]

    try:
        if tipo_arquivo == 'csv':
            dados = pd.read_csv(arquivo)
        elif tipo_arquivo == 'json':
            dados = pd.DataFrame(json.load(arquivo))
        elif tipo_arquivo == 'xml':
            arvore = XmlParser.parse(arquivo)
            raiz = arvore.getroot()
            registros = []

            for elemento in raiz:
                linha = {}
                for sub_item in elemento:
                    linha[sub_item.tag] = sub_item.text
                registros.append(linha)

            dados = pd.DataFrame(registros)
        elif tipo_arquivo == 'txt':
            dados = pd.read_csv(arquivo, delimiter="\t")
        else:
            return jsonify({"erro": "Formato de arquivo não suportado."}), 400
    except Exception as erro:
        return jsonify({"erro": f"Falha ao processar o arquivo: {str(erro)}"}), 400

    conteudo = dados.to_string()
    categoria = classificar_arquivo(conteudo)

    return jsonify({"classificacao": categoria})

@app.route('/enviar', methods=['POST'])
def rota_upload():
    arquivo = request.files['file']
    tipo_arquivo = arquivo.filename.split('.')[-1]

    if tipo_arquivo == 'csv':
        dados = pd.read_csv(arquivo)
    elif tipo_arquivo == 'json':
        dados = pd.DataFrame(json.load(arquivo))
    elif tipo_arquivo == 'xml':
        try:
            arvore = XmlParser.parse(arquivo)
            raiz = arvore.getroot()
            registros = []

            for elemento in raiz:
                linha = {}
                for sub_item in elemento:
                    linha[sub_item.tag] = sub_item.text
                registros.append(linha)

            dados = pd.DataFrame(registros)
        except XmlParser.ParseError as erro:
            return jsonify({"erro": f"Erro ao processar arquivo XML: {str(erro)}"}), 400
    elif tipo_arquivo == 'txt':
        dados = pd.read_csv(arquivo, delimiter="\t")
    else:
        return jsonify({"erro": "Tipo de arquivo não suportado"}), 400

    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute('''
        SELECT * FROM tabela_metadados WHERE nome_arquivo = ? AND tipo_arquivo = ?
    ''', (arquivo.filename, tipo_arquivo))
    resultado = cursor.fetchone()

    if resultado:
        conexao.close()
        return jsonify({"mensagem": "Este arquivo já foi carregado."}), 409

    colunas = ', '.join(dados.columns)
    metadados = {
        "timestamp": datetime.now(),
        "nome_arquivo": arquivo.filename,
        "tipo_arquivo": tipo_arquivo,
        "cabecalhos": colunas
    }

    cursor.execute('''
        INSERT INTO tabela_metadados (timestamp, nome_arquivo, tipo_arquivo, cabecalhos)
        VALUES (?, ?, ?, ?)
    ''', (metadados["timestamp"], metadados["nome_arquivo"], metadados["tipo_arquivo"], metadados["cabecalhos"]))
    id_metadado = cursor.lastrowid

    for _, linha in dados.iterrows():
        for coluna in dados.columns:
            cursor.execute('''
                INSERT INTO tabela_conteudos (id_metadado, coluna_nome, tipo_dado, conteudo)
                VALUES (?, ?, ?, ?)
            ''', (id_metadado, coluna, str(type(linha[coluna]).__name__), str(linha[coluna])))

    conexao.commit()
    conexao.close()

    return jsonify({"mensagem": "Arquivo salvo com sucesso."}), 200

@app.route('/metadados', methods=['GET'])
def listar_metadados():
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM tabela_metadados')
    resultado = cursor.fetchall()
    conexao.close()
    return jsonify(resultado)

@app.route('/conteudos/<int:id_metadado>', methods=['GET'])
def obter_conteudo(id_metadado):
    conexao = sqlite3.connect('banco_dados.db')
    cursor = conexao.cursor()
    cursor.execute('SELECT * FROM tabela_conteudos WHERE id_metadado = ?', (id_metadado,))
    conteudos = cursor.fetchall()
    conexao.close()
    return jsonify(conteudos)

if __name__ == '__main__':
    criar_db()
    app.run(debug=True)
