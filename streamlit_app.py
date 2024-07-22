import streamlit as st
from anthropic import Anthropic
import PyPDF2

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def stream_claude_response(prompt, api_key):
    client = Anthropic(api_key=api_key)
    system_prompt = "Sei un esperto analista finanziario. Fornisci analisi dettagliate e professionali basate sulle richieste dell'utente."
    
    messages = [
        {"role": "user", "content": prompt}
    ]

    try:
        with client.messages.stream(
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            model="claude-3-sonnet-20240229"
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"Errore nella chiamata all'API di Claude: {str(e)}"

st.set_page_config(layout="wide")
st.title("Chatbot Analisi di Bilancio")

# Sidebar per input iniziali
with st.sidebar:
    st.header("Configurazione")
    uploaded_file = st.file_uploader("Carica il file PDF del bilancio", type="pdf")
    api_key = st.text_input("Inserisci la tua API key di Claude Anthropic", type="password")

    if uploaded_file is not None and api_key:
        pdf_text = extract_text_from_pdf(uploaded_file)
        st.success("File PDF caricato con successo!")
        st.session_state['pdf_text'] = pdf_text
        st.session_state['api_key'] = api_key

# Main area per la chat
if 'pdf_text' in st.session_state and 'api_key' in st.session_state:
    st.write("Seleziona un'opzione per iniziare l'analisi:")
    options = [
        "Riclassificazione del bilancio",
        "Analisi dei principali indici",
        "Analisi del cash flow",
        "Valutazione della situazione patrimoniale"
    ]

    selected_option = st.selectbox("Scegli un'analisi", options)

    if st.button("Avvia analisi"):
        prompt = f"""
        Ti è stato fornito il seguente bilancio:

        {st.session_state['pdf_text']}

        L'utente ha richiesto un'analisi su: {selected_option}
        
        Fornisci un'analisi dettagliata e professionale basata su questa richiesta.
        """

        st.write("Analisi:")
        response_container = st.empty()
        full_response = ""

        for chunk in stream_claude_response(prompt, st.session_state['api_key']):
            full_response += chunk
            response_container.markdown(full_response)

else:
    st.write("Per favore, carica un file PDF e inserisci l'API key nella sidebar per iniziare.")

st.write("Sviluppato con ❤️ utilizzando Streamlit e Claude AI")