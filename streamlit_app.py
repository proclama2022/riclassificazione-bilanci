import streamlit as st
import anthropic
import pdfplumber

def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        st.error(f"Errore nell'estrazione del testo dal PDF: {str(e)}")
        return None

def stream_chat_with_claude(api_key, dati_bilancio, messages):
    client = anthropic.Anthropic(api_key=api_key)
    
    system_prompt = f"""Sei un business analyst che effettua una breve analisi riclassificazione e analisi degli indici del seguente bilancio:
    
    {dati_bilancio}
    
    Rispondi in maniera precisa e professionale, non inventare nulla che non sia presente nei dati sopra."""
    
    try:
        with client.messages.stream(
            max_tokens=4096,
            system=system_prompt,
            messages=messages,
            model="claude-3-5-sonnet-20240620"
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"Error in Claude API call: {str(e)}"

st.title("Chatbot con dati aziendali")

# Sidebar for API inputs
with st.sidebar:
    st.header("Configurazione")
    bilancio_pdf = st.file_uploader("Carica il bilancio aziendale in formato PDF")
    claude_api_key = st.text_input("Inserisci la chiave API di Claude Anthropic:", type="password")
    
    if st.button("Avvia analisi"):
        if bilancio_pdf and claude_api_key:
            with st.spinner("Effettuo analisi del bilancio..."):
                bilancio_txt = extract_text_from_pdf(bilancio_pdf)
                st.session_state['bilancio_txt'] = bilancio_txt
                st.session_state['messages'] = []  # Reset chat history on new API call
                stream_chat_with_claude(claude_api_key, bilancio_txt, [])
        else:
            st.error("Inserisci tutti i dati richiesti.")

# Main chat interface
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

if 'bilancio_txt' in st.session_state and st.session_state['bilancio_txt']:
    
    for message in st.session_state['messages']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Cosa ti piacerebbe sapere?"):
        st.session_state['messages'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for chunk in stream_chat_with_claude(claude_api_key, st.session_state['bilancio_txt'], st.session_state['messages']):
                full_response += chunk
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state['messages'].append({"role": "assistant", "content": full_response})
else:
    st.info("Inserisci i dati richiesti nella sidebar prima di procedere con la chat.")

st.sidebar.markdown("---")
st.sidebar.write("Questa chat ti permette di chattare con un bilancio.")