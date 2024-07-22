import streamlit as st
import pdfplumber
import anthropic

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'client' not in st.session_state:
    st.session_state['client'] = None
if 'pdf_text' not in st.session_state:
    st.session_state['pdf_text'] = None
if 'chat_started' not in st.session_state:
    st.session_state['chat_started'] = False
if 'initial_analysis_done' not in st.session_state:
    st.session_state['initial_analysis_done'] = False

st.title('Analisi Bilancio XBRL con Claude AI')

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

# Sidebar for configuration
with st.sidebar:
    st.header("Configurazione")
    bilancio_xbrl = st.file_uploader('Carica il bilancio XBRL in PDF', accept_multiple_files=False)
    claude_api_key = st.text_input("Inserisci la chiave API di Claude Anthropic:", type="password")
    
    if st.button("Avvia Analisi"):
        if claude_api_key and bilancio_xbrl:
            st.session_state['client'] = anthropic.Anthropic(api_key=claude_api_key)
            st.session_state['pdf_text'] = extract_text_from_pdf(bilancio_xbrl)
            if st.session_state['pdf_text']:
                st.session_state['chat_started'] = True
                st.success("Configurazione completata. L'analisi iniziale sta per cominciare.")
            else:
                st.error("Errore nell'estrazione del testo dal PDF.")
        else:
            st.error("Inserisci tutti i dati richiesti.")

def get_claude_response(prompt):
    try:
        with st.session_state['client'].messages.stream(
            max_tokens=1000,
            system=f"Sei un assistente esperto in analisi di bilanci. Analizza e rispondi alle domande basandoti sul seguente bilancio XBRL:\n\n{st.session_state['pdf_text']}",
            messages=[
                {"role": "user", "content": prompt}
            ],
            model="claude-3-sonnet-20240229"
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        st.error(f"Errore durante l'elaborazione della risposta: {str(e)}")

# Initial analysis function
def perform_initial_analysis():
    initial_prompt = """
    Analizza il bilancio XBRL fornito e fornisci:
    1. Una riclassificazione del bilancio
    2. I principali indici finanziari
    3. Un breve commento sulla situazione finanziaria dell'azienda

    Rispondi fornendo una breve riclassificazione e i principali indici di bilancio.
    """
    
    st.subheader("Analisi Iniziale del Bilancio")
    
    with st.spinner("Analisi in corso..."):
        full_analysis = ""
        for response_chunk in get_claude_response(initial_prompt):
            full_analysis += response_chunk
    
    st.markdown(full_analysis)
    
    st.session_state['messages'].extend([
        {"role": "user", "content": initial_prompt},
        {"role": "assistant", "content": full_analysis}
    ])
    st.session_state['initial_analysis_done'] = True

# Chat interface
if st.session_state['chat_started']:
    if not st.session_state['initial_analysis_done']:
        perform_initial_analysis()
    
    st.subheader("Chat con Claude AI")
    
    # Display chat history
    for message in st.session_state['messages']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    user_input = st.chat_input("Inserisci la tua domanda sul bilancio:")
    
    if user_input:
        # Add user message to chat history
        st.session_state['messages'].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get and display Claude's response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            for response_chunk in get_claude_response(user_input):
                full_response += response_chunk
                response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
        
        # Add Claude's response to chat history
        st.session_state['messages'].append({"role": "assistant", "content": full_response})

else:
    st.info("Configura l'applicazione nella barra laterale e avvia l'analisi per iniziare.")