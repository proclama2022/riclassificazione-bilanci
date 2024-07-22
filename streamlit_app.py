import streamlit as st
import pdfplumber
import anthropic

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state['messages'] = []
if 'pdf_text' not in st.session_state:
    st.session_state['pdf_text'] = None
if 'chat_started' not in st.session_state:
    st.session_state['chat_started'] = False
if 'system_prompt' not in st.session_state:
    st.session_state['system_prompt'] = None

st.title('Analisi Bilancio XBRL con Claude AI')

client = None

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

def start_chat():
    st.session_state['system_prompt'] = f"Sei un assistente esperto in analisi di bilanci. Analizza e rispondi alle domande basandoti sul seguente bilancio XBRL:\n\n{st.session_state['pdf_text']}"
    
    try:
        with client.messages.stream(
            max_tokens=4096,
            system=st.session_state['system_prompt'],
            model="claude-3-sonnet-20240229"
        ) as stream:
            response = ""
            for text in stream.text_stream:
                response += text
                yield text
        
        # Add the initial response to messages
        st.session_state['messages'].append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"Errore durante l'avvio della chat: {str(e)}")

# Sidebar for configuration
with st.sidebar:
    st.header("Configurazione")
    bilancio_xbrl = st.file_uploader('Carica il bilancio XBRL in PDF', accept_multiple_files=False)
    claude_api_key = st.text_input("Inserisci la chiave API di Claude Anthropic:", type="password")
    
    if st.button("Avvia Chat"):
        if claude_api_key and bilancio_xbrl:
            client = anthropic.Anthropic(api_key=claude_api_key)
            st.session_state['pdf_text'] = extract_text_from_pdf(bilancio_xbrl)
            if st.session_state['pdf_text']:
                st.session_state['chat_started'] = True
                st.success("Configurazione completata. La chat è pronta!")
                
                # Display initial message
                with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    for response_chunk in start_chat():
                        full_response += response_chunk
                        response_placeholder.markdown(full_response + "▌")
                    response_placeholder.markdown(full_response)
            else:
                st.error("Errore nell'estrazione del testo dal PDF.")
        else:
            st.error("Inserisci tutti i dati richiesti.")

def get_claude_response(user_input):
    messages = st.session_state['messages'] + [{"role": "user", "content": user_input}]
    try:
        with client.messages.stream(
            max_tokens=4096,
            system=st.session_state['system_prompt'],
            messages=messages,
            model="claude-3-sonnet-20240229"
        ) as stream:
            response = ""
            for text in stream.text_stream:
                response += text
                yield text
    except Exception as e:
        st.error(f"Errore durante l'elaborazione della risposta: {str(e)}")

# Chat interface
if st.session_state['chat_started']:
    
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
    st.info("Configura l'applicazione nella barra laterale e avvia la chat per iniziare.")