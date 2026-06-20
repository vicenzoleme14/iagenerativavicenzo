# =====================================================================
# PROJETO FINAL: DASHBOARD DE PRODUÇÃO COM IA (Versão Completa)
# =====================================================================

# 1. IMPORTANDO AS FERRAMENTAS
import streamlit as st       
import pandas as pd          
import matplotlib.pyplot as plt  
import seaborn as sns        
from openai import OpenAI    

# 2. CONFIGURANDO A PÁGINA WEB
st.set_page_config(page_title="Dashboard SENAI", page_icon="🏭", layout="wide")

# =====================================================================
# 3. CARREGANDO DADOS DO ARQUIVO REAL (CSV)
# =====================================================================
# Lembre-se de ter o arquivo 'dados_producao.csv' na mesma pasta com as colunas:
# Data,Hora,Tempo_Produção,Máquina,PeçasBoas,Defeitos,Setor,Operador
@st.cache_data
def carregar_dados():
    try:
        tabela = pd.read_csv("dados_producao.csv")
        tabela["Data"] = pd.to_datetime(tabela["Data"])
        return tabela
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo CSV: {e}")
        return pd.DataFrame()

df = carregar_dados()

if df.empty:
    st.stop() # Para o programa se não achar os dados

# =====================================================================
# 4. CONSTRUINDO O VISUAL DO SITE E OS GRÁFICOS
# =====================================================================
st.image("logo-senai-1.png")
st.title("🏭 Centro de Controle de Produção Avançado - IA Transformers")
st.markdown("Monitoramento detalhado por **Setor** e **Operador**.")
st.divider() 

# --- CARDS DE MÉTRICAS ---
c1, c2, c3, c4 = st.columns(4)
total_boas = df["PeçasBoas"].sum()
total_def = df["Defeitos"].sum()
tempo_total = df["Tempo_Produção"].sum()
taxa_erro = (total_def / (total_boas + total_def)) * 100

c1.metric("Total Peças Boas", f"{total_boas:,}".replace(",", "."))
c2.metric("Total de Refugos", f"{total_def:,}".replace(",", "."))
c3.metric("Tempo Produzindo", f"{tempo_total} min")
c4.metric("Taxa de Erro Global", f"{taxa_erro:.2f}%")

st.divider()

# --- GRÁFICOS LADO A LADO ---
g1, g2 = st.columns(2)

with g1:
    st.subheader("📦 Produção por Setor")
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    setor_prod = df.groupby("Setor")["PeçasBoas"].sum().reset_index()
    sns.barplot(data=setor_prod, x="Setor", y="PeçasBoas", palette="viridis", ax=ax1)
    st.pyplot(fig1)

with g2:
    st.subheader("👤 Performance por Operador (Peças Boas)")
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    op_prod = df.groupby("Operador")["PeçasBoas"].sum().sort_values(ascending=False).reset_index()
    # Gráfico horizontal (y="Operador") para ler melhor os nomes
    sns.barplot(data=op_prod, x="PeçasBoas", y="Operador", palette="magma", ax=ax2)
    st.pyplot(fig2)

st.divider()

# =====================================================================
# 5. O CHATBOT: ANALISTA VIRTUAL COM IA E MEMÓRIA
# =====================================================================
st.subheader("🤖 Analista Virtual de Produção")

# --- BOTÃO DE LIMPAR CHAT ---
col_tit, col_btn = st.columns([0.85, 0.15])
with col_btn:
    if st.button("🗑️ Limpar Chat"):
        if "historico_chat" in st.session_state:
            del st.session_state["historico_chat"] # Apaga a memória
        st.rerun() # Reinicia a página para limpar a tela

# --- AUTENTICAÇÃO ---
meu_token = st.text_input("Insira sua API Key da OpenAI para habilitar o chat:", type="password")

if meu_token:
    cliente = OpenAI(base_url="https://models.inference.ai.azure.com", api_key=meu_token)

    # --- INICIANDO A MEMÓRIA SE ELA ESTIVER VAZIA ---
    if "historico_chat" not in st.session_state:
        
        # Converte a tabela do Pandas para texto para a IA conseguir ler
        dados_texto = df.to_csv(index=False)
        
        # A instrução secreta do sistema
        contexto_sistema = f"""Você é um analista industrial sênior. 
        Você tem acesso a estes dados de produção da fábrica: 
        
        {dados_texto}
        
        Ajude o usuário a identificar gargalos, melhores operadores e falhas por setor.
        Responda de forma clara, prestativa e direta."""
        
        # Criamos a lista já com o recado do sistema E a mensagem de boas-vindas visível!
        st.session_state["historico_chat"] = [
            {"role": "system", "content": contexto_sistema},
            {"role": "assistant", "content": "Olá! O histórico está limpo. O que você gostaria de analisar nos dados de produção de hoje?"}
        ]

    # --- DESENHANDO AS MENSAGENS ANTIGAS NA TELA ---
    for msg in st.session_state["historico_chat"]:
        if msg["role"] != "system":
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # --- RECEBENDO NOVA PERGUNTA ---
    pergunta = st.chat_input("Ex: Qual o operador com mais defeitos no setor de Usinagem?")
    
    if pergunta:
        # Mostra a pergunta na tela
        with st.chat_message("user"):
            st.markdown(pergunta)
        
        # Guarda na memória secreta
        st.session_state["historico_chat"].append({"role": "user", "content": pergunta})
        
        # Envia para a nuvem
        response = cliente.chat.completions.create(
            model="gpt-4o-mini",
            messages=st.session_state["historico_chat"]
        )
        
        # Extrai a resposta
        texto_ia = response.choices[0].message.content
        
        # Mostra a resposta na tela
        with st.chat_message("assistant"):
            st.markdown(texto_ia)
            
        # Guarda a resposta na memória
        st.session_state["historico_chat"].append({"role": "assistant", "content": texto_ia})