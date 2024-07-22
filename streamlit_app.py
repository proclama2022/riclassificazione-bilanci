import streamlit as st
import pdfplumber
import pandas as pd
import io
import anthropic
import os

# Initialize session state for messages and client
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'client' not in st.session_state:
    st.session_state['client'] = None

# Sidebar for API inputs
with st.sidebar:
    st.header("Configurazione")
    bilancio_xbrl = st.file_uploader('Carica il bilancio XBRL in PDF', accept_multiple_files=False)
    claude_api_key = st.text_input("Inserisci la chiave API di Claude Anthropic:", type="password")
    if claude_api_key and bilancio_xbrl:
        st.session_state['client'] = anthropic.Anthropic(api_key=claude_api_key)
        st.success("Configurazione completata")
        st.session_state['messages'] = []
    else:
        st.error("Inserisci tutti i dati richiesti.")

# Main chat interface
st.title('Analisi Bilancio XBRL con Claude AI')

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
    if not st.session_state['client']:
        st.error("Chiave API di Anthropic non configurata.")
        return None

    prompt = f"""
    Analizza il seguente testo estratto da un bilancio XBRL e fornisci:
    1. Una riclassificazione del bilancio
    2. I principali indici finanziari
    3. Un breve commento sulla situazione finanziaria dell'azienda

    Testo del bilancio:
    {text}

    Rispondi fornendo una breve riclassificazione e i principali indici di bilancio.
    """

    try:
        with st.session_state['client'].messages.stream(
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="claude-3-sonnet-20240229"
        ) as stream:
            response = ""
            for text in stream.text_stream:
                response += text
                yield text
            st.session_state['messages'].append({"role": "assistant", "content": response})
    except anthropic.APIError as e:
        st.error(f"Errore API di Anthropic: {str(e)}")
    except Exception as e:
        st.error(f"Errore inaspettato: {str(e)}")

if bilancio_xbrl is not None and st.session_state['client']:
    # Extract text from PDF
    pdf_text = extract_text_from_pdf(bilancio_xbrl)
    
    if pdf_text:
        # Analyze text with Claude
        st.write("Analisi in corso con Claude AI...")
        analysis_result = ""
        analysis_placeholder = st.empty()
        for chunk in analyze_with_claude(pdf_text):
            analysis_result += chunk
            analysis_placeholder.markdown(analysis_result)
        
        # Show download button for the report
        st.download_button(
            label="Scarica il report",
            data=analysis_result,
            file_name="report_bilancio.md",
            mime="text/markdown"
        )

# Chat interface for follow-up questions
st.subheader("Domande di approfondimento")
user_question = st.text_input("Inserisci la tua domanda sul bilancio:")

if user_question:
    st.session_state['messages'].append({"role": "user", "content": user_question})
    
    with st.spinner('Claude sta elaborando la risposta...'):
        try:
            with st.session_state['client'].messages.stream(
                messages=st.session_state['messages'],
                model="claude-3-sonnet-20240229",
                max_tokens=1000
            ) as stream:
                response = ""
                response_placeholder = st.empty()
                for text in stream.text_stream:
                    response += text
                    response_placeholder.markdown(response)
                st.session_state['messages'].append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Errore durante l'elaborazione della risposta: {str(e)}")

# Display chat history
st.subheader("Cronologia della chat")
for message in st.session_state['messages']:
    if message['role'] == 'user':
        st.text_input("Tu:", value=message['content'], disabled=True)
    else:
        st.text_area("Claude:", value=message['content'], disabled=True)