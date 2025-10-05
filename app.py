import streamlit as st
from docling.document_converter import DocumentConverter
from openai import OpenAI
import time
import os

st.set_page_config(page_title="Notas Fiscais LLM", layout="wide")

st.title("📑 Leitor de Notas Fiscais com LLM")

# 🔑 Configuração da chave OpenAI
api_key = st.sidebar.text_input("Cole sua chave da OpenAI:", type="password")
if api_key:
    client = OpenAI(api_key=api_key)

# --- Barra lateral para inserir notas fiscais ---
st.sidebar.header("Inserir Notas Fiscais")
uploaded_files = st.sidebar.file_uploader(
    "Envie suas notas fiscais (PDF, PNG, JPG etc.)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    if "notas" not in st.session_state:
        st.session_state["notas"] = []

    for file in uploaded_files:
        if file.name not in [f["name"] for f in st.session_state["notas"]]:
            st.session_state["notas"].append(
                {"name": file.name, "data": file.getvalue(), "type": file.type}
            )
    st.sidebar.success(f"{len(uploaded_files)} arquivo(s) adicionado(s)!")

if "notas" in st.session_state and st.session_state["notas"]:
    st.sidebar.subheader("Notas salvas:")
    for nota in st.session_state["notas"]:
        st.sidebar.write(f"📄 {nota['name']}")

    st.header("📄 Resultado extraído com LLM")

    ultimo = st.session_state["notas"][-1]

    with open(ultimo["name"], "wb") as f:
        f.write(ultimo["data"])

    # --- Barra de progresso ---
    progress_bar = st.progress(0, text="Convertendo arquivo para Markdown...")
    for percent in range(0, 100, 20):
        time.sleep(0.2)
        progress_bar.progress(percent + 20, text=f"Convertendo... {percent+20}%")

    # --- Conversão com docling ---
    converter = DocumentConverter()
    result = converter.convert(ultimo["name"])
    md_text = result.document.export_to_markdown()

    progress_bar.progress(100, text="Conversão concluída!")
    time.sleep(0.5)
    progress_bar.empty()

    st.subheader(f"📄 {ultimo['name']}")
    st.markdown("### Markdown extraído")
    with st.expander("Ver Markdown completo"):
        st.markdown(md_text)

    # --- Processar com LLM ---
    if api_key:
        with st.spinner("Processando com LLM..."):
            prompt = f"""
            Você é um especialista em leitura de Notas Fiscais.
            Abaixo está o conteúdo da nota em Markdown:

            {md_text}

            Extraia e responda APENAS nos campos abaixo:

            - Data de Emissão:
            - Retenções Federais:
            - Total Bruto:
            - Total Líquido:
            - CNPJ da empresa que realizou o serviço:
            - Nome da empresa que realizou o serviço:
            - CNPJ da empresa que comprou o serviço:
            - Nome da empresa que comprou o serviço:
            """

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Você é um assistente que extrai informações de notas fiscais."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            resultado = response.choices[0].message.content
            st.success("Extração concluída!")
            st.markdown("### 📊 Dados da Nota Fiscal")
            st.markdown(resultado)
    else:
        st.warning("⚠️ Insira sua chave da OpenAI na barra lateral para processar a nota.")
