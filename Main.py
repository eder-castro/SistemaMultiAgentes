import os
from google import genai
from google.genai import types
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from datetime import date
import textwrap
import requests
import warnings

warnings.filterwarnings("ignore")

# 1. Configurar a API Key (Lendo do arquivo e definindo a variável de ambiente - RECOMENDADO pelo google-adk)
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

os.environ['GOOGLE_API_KEY'] = API_KEY  # Definir a variável de ambiente

client = genai.Client()  # Criar o cliente (sem passar a chave diretamente)

# Função auxiliar que envia uma mensagem para um agente via Runner e retorna a resposta final
def call_agent(agent: Agent, message_text: str) -> str:
    session_service = InMemorySessionService()
    session = session_service.create_session(app_name=agent.name, user_id="user1", session_id="session1")
    runner = Runner(agent=agent, app_name=agent.name, session_service=session_service)
    content = types.Content(role="user", parts=[types.Part(text=message_text)])

    final_response = ""
    for event in runner.run(user_id="user1", session_id="session1", new_message=content):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text is not None:
                    final_response += part.text
                    final_response += "\n"
    return final_response

# Função auxiliar para exibir texto formatado
def to_markdown(text):
    text = text.replace('•', '  *')
    return textwrap.indent(text, '> ', predicate=lambda _: True)

##########################################
# --- Agente 1: Buscador de Notícias --- #
##########################################
def agente_buscador(topico, data_de_hoje):
    buscador = Agent(
        name="agente_buscador",
        model="gemini-2.0-flash",
        description="Agente que busca notícias sobre o tópico indicado",
        tools=[google_search],
        instruction='''
        Você é um agente de pesquisa. Sua tarefa é usar a ferramenta de busca do google (google_search)
        para recuperar as últimas notícias de lançamentos muito relevantes sobre o tópico abaixo.
        Foque em no máximo 3 notícias relevantes, com base na quantidade e entusiasmo das notícias sobre ele.
        Se um tema tiver poucas notícias ou reações entusiasmadas, é possível que ele não seja tão relevante assim,
        podendo ser substituído por outro que tenha mais.
        Esses lançamentos relevantes devem ser atuais, de no máximo um mês antes da data de hoje.
        '''
    )
    entrada_do_agente_buscador = f"Tópico: {topico}\nData de hoje: {data_de_hoje}"
    lancamentos_buscados = call_agent(buscador, entrada_do_agente_buscador)
    return lancamentos_buscados

################################################
# --- Agente 2: Planejador de posts --- #
################################################
def agente_planejador(topico, lancamentos_buscados):
    planejador = Agent(
        name="agente_planejador",
        model="gemini-2.0-flash",
        instruction="""
        Você é um planejador de conteúdo, especialista em Instagram. Com base na lista de lançamentos
         mais recentes e relevantes vindas do buscador, você deve:
        Usar a ferramenta de busca do google (google_search) para criar um plano sobre quais são os pontos
        mais relevantes que poderíamos abordar em um post sobre cada um deles.
        Você também pode usar o (google_search) para encontrar mais informaçõe sobre os temas e aprofundar.
        Ao final, você irá escolher o tema mais relevante entre eles com base nas suas pesquisas e retornar
        esse tema, seus pontos mais relevantes, e um plano com os assuntos a serem abordados no post que será
        criado posteriormente.
        """,
        description="Agente que planeja posts",
        tools=[google_search]
    )
    entrada_do_agente_planejador = f"Tópico:{topico}\nLançamentos buscados: {lancamentos_buscados}"
    plano_do_post = call_agent(planejador, entrada_do_agente_planejador)
    return plano_do_post

######################################
# --- Agente 3: Redator do Post --- #
######################################
def agente_redator(topico, plano_de_post):
    redator = Agent(
        name="agente_redator",
        model="gemini-2.0-flash",
        instruction="""
            Você é um Redator Criativo especializado em criar posts virais para Instagram.
            Você escreve posts para a empresa Alura, a maior escola online de tecnologia do Brasil.
            Utilize o tema fornecido no plano de post e os pontos mais relevantes fornecidos e, com base nisso,
            escreva um rascunho de post para Instagram sobre o tema indicado.
            O post deve ser engajador, informativo, com linguagem simples e incluir 2 a 4 hashtags no final.
            """,
        description="Agente redator de posts engajadores para Instagram"
    )
    entrada_do_agente_redator = f"Tópico: {topico}\nPlano de post: {plano_de_post}"
    rascunho = call_agent(redator, entrada_do_agente_redator)
    return rascunho

##########################################
# --- Agente 4: Revisor de Qualidade --- #
##########################################
def agente_revisor(topico, rascunho_gerado):
    revisor = Agent(
        name="agente_revisor",
        model="gemini-2.0-flash",
        instruction="""
            Você é um Editor e Revisor de Conteúdo meticuloso, especializado em posts para Instagram, com foco no Instagram.
            Por ter um público jovem, entre 18 e 30 anos, use um tom de escrita adequado.
            Revise o rascunho de post de Instagram abaixo sobre o tópico indicado, verificando clareza, concisão, correção e tom.
            Se o rascunho estiver bom, responda apenas 'O rascunho está ótimo e pronto para publicar!'.
            Caso haja problemas, aponte-os e sugira melhorias.
            """,
        description="Agente revisor de post para Instagram."
    )
    entrada_do_agente_revisor = f"Tópico: {topico}\nRascunho: {rascunho_gerado}"
    texto_revisado = call_agent(revisor, entrada_do_agente_revisor)
    return texto_revisado

data_de_hoje = date.today().strftime("%d/%m/%Y")

print("🚀 Iniciando o Sistema de Criação de Posts para Instagram com 4 Agentes 🚀")

# --- Obter o Tópico do Usuário ---
topico = input("❓ Por favor, digite o TÓPICO sobre o qual você quer criar o post de tendências: ")

# Lógica do sistema de agentes
if not topico:
    print("Você esqueceu de informar um tópico!")
else:
    print(f"Maravilha! Vamos então criar o post sobre novidades em {topico}")

    lancamentos_buscados = agente_buscador(topico, data_de_hoje)
    print("\n--- Resultado do agente 1 (Buscador) ---\n")
    print(to_markdown(lancamentos_buscados))
    print("------------------------------------------------")

    plano_de_post = agente_planejador(topico, lancamentos_buscados)
    print("\n--- Resultado do agente 2 (Planejador) ---\n")
    print(to_markdown(plano_de_post))
    print("------------------------------------------------")

    rascunho_de_post = agente_redator(topico, plano_de_post)
    print("\n--- Resultado do agente 3 (Redator) ---\n")
    print(to_markdown(rascunho_de_post))
    print("------------------------------------------------")

    post_final = agente_revisor(topico, rascunho_de_post)
    print("\n--- Resultado do agente 4 (Revisor) ---\n")
    print(to_markdown(post_final))
    print("------------------------------------------------")