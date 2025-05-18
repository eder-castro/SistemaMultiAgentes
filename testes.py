import os
from google import genai

chave_api_file = 'chave-api.txt'
try:
    with open(chave_api_file, 'r') as f:
        API_KEY = f.readline().strip()
except FileNotFoundError:
    print(f"Erro: Arquivo {chave_api_file} não encontrado.")
    exit()

if not API_KEY:
    print("Erro: A chave API não foi definida.")
    exit()

try:
    client = genai.Client(api_key=API_KEY)
    print("Cliente inicializado com sucesso!")
except Exception as e:
    print(f"Erro ao inicializar o cliente: {e}")