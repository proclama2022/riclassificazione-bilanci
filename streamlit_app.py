import streamlit as st
import pdfplumber
import pandas as pd
import io
import json
import anthropic
import os

client = None

# Sidebar for API inputs
with st.sidebar:
    st.header("API Configuration")
    bilancio_xbrl= st.file_uploader('Carica il bilancio XBRL', accept_multiple_files=False)
    claude_api_key = st.text_input("Inserisci la chiave API di Claude Anthropic:", type="password")
    if claude_api_key:
        client = anthropic.Anthropic(api_key=claude_api_key)
    else:
        st.error("Inserisci tutti i dati richiesti.")

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        st.error(f"Errore nell'estrazione del testo dal PDF: {str(e)}")
        return None
    return text

def analyze_with_claude(text):
    if not client:
        st.error("Chiave API di Anthropic non configurata. Controlla il file .env.")
        return None

    prompt = f"""
    Analizza il seguente testo estratto da un bilancio XBRL e fornisci:
    1. Una riclassificazione del bilancio
    2. I principali indici finanziari
    3. Un breve commento sulla situazione finanziaria dell'azienda

    Testo del bilancio:
    {text[:10000]}

    Rispondi in formato JSON con le seguenti chiavi:
    "riclassificazione", "indici", "commento"
    """

    try:
        response = client.completions.create(
            model="claude-2.1",
            prompt=f"{anthropic.HUMAN_PROMPT} {prompt}{anthropic.AI_PROMPT}",
            max_tokens_to_sample=1000,
        )
        return response.completion
    except anthropic.APIError as e:
        st.error(f"Errore API di Anthropic: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Errore inaspettato: {str(e)}")
        return None

def generate_report(analysis_result):
    if not analysis_result:
        return "Nessun risultato da analizzare."

    try:
        result_dict = json.loads(analysis_result)
        report = ""
        if "riclassificazione" in result_dict:
            report += "## Riclassificazione del bilancio\n"
            report += result_dict["riclassificazione"] + "\n\n"
        if "indici" in result_dict:
            report += "## Principali indici finanziari\n"
            report += result_dict["indici"] + "\n\n"
        if "commento" in result_dict:
            report += "## Commento sulla situazione finanziaria\n"
            report += result_dict["commento"] + "\n\n"
        return report
    except json.JSONDecodeError:
        return "Errore nella decodifica del JSON. Risultato grezzo:\n\n" + analysis_result

st.title('Analisi Bilancio XBRL con Claude AI')

if bilancio_xbrl is not None:
    # Estrai il testo dal PDF
    pdf_text = extract_text_from_pdf(bilancio_xbrl)
    
    if pdf_text:
        # Analizza il testo con Claude
        with st.spinner('Analisi in corso con Claude AI...'):
            analysis_result = analyze_with_claude(pdf_text)
        
        if analysis_result:
            # Genera il report
            report = generate_report(analysis_result)
            
            # Mostra il report
            st.markdown(report)
            
            # Opzione per scaricare il report
            st.download_button(
                label="Scarica il report",
                data=report,
                file_name="report_bilancio.md",
                mime="text/markdown"
            )

            # Mostra il JSON grezzo (opzionale, per debug)
            if st.checkbox("Mostra JSON grezzo"):
                st.json(analysis_result)