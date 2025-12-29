import argparse
import os
from pathlib import Path
import sys
sys.path.append("/Users/aaryan/AI Agent Builder")
from tempfile import NamedTemporaryFile
import time
from fabriq.rag_pipeline import RAGPipeline
from fabriq.indexing import DocumentIndexer
from fabriq.config_parser import ConfigParser
import streamlit as st
st.set_page_config(page_title="Chat Agent", page_icon="🤖", layout='wide', initial_sidebar_state='collapsed')

@st.cache_resource(show_spinner=False)
def load_chatbot(_config: ConfigParser):
    """Cache chatbot initialization to avoid reloading"""
    rag_pipeline = RAGPipeline(_config)
    return rag_pipeline

@st.cache_data(show_spinner=False)
def load_config(config_path: str):
    """Cache config loading to avoid repeated file reads"""
    return ConfigParser(config_path)

def index_documents(file_paths: list, config: ConfigParser):
    """Index documents from a given file path"""
    indexer = DocumentIndexer(config)
    indexer.index_documents(file_paths)
    return True

def stream_data(chatbot, prompt):
    """Generator for streaming response chunks"""
    with st.spinner("Thinking..."):
        response = chatbot.get_response(prompt, stream=True)
    for c in response["text"]:
        yield c
        time.sleep(0.01)


def app(config_path="config/config.yaml"):
    
    # Load cached config
    config = load_config(config_path)
    chatbot = load_chatbot(config)
    
    col1, col2 = st.columns([1, 0.15])
    col1.title("Chat Agent")

    # Add footer at the bottom of the page
    footer = """
    <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            text-align: center;
            padding: 10px;
            background-color: transparent;
            z-index: 999;
        }
    </style>
    <div class="footer">
        <small><i>Powered by <b>Fabriq</b><i></small>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)
    
    uploaded_files = st.sidebar.file_uploader("Upload documents to index", accept_multiple_files=True, type=['pdf', 'docx', 'pptx', 'xlsx'])
    if uploaded_files:
        doc_indexed = None
        file_paths = []
        for f in uploaded_files:
            with NamedTemporaryFile(delete=False) as tmp:
                # Write uploaded file contents to the temp file
                tmp.write(f.getbuffer())
                tmp_path = tmp.name  # Get the temp file path
                file_paths.append(tmp_path)
        
        if st.sidebar.button("Submit"):
            with st.sidebar:
                with st.spinner("Indexing documents..."):
                    doc_indexed = index_documents(file_paths, config)
        if doc_indexed:
            st.sidebar.success("Documents indexed successfully!")

        for path in file_paths:
            if os.path.exists(path):
                os.remove(path)
    
    # Initialize messages once
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "sources" not in st.session_state:
        st.session_state.sources = []

    # Render existing messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new input
    if prompt := st.chat_input("Ask your query"):
        # Append and display user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Stream assistant response using st.write_stream
        with st.chat_message("assistant"):
            full_response = st.write_stream(stream_data(chatbot, prompt))
        
        # Append assistant response
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Add a clear chat button
    col2.write("\n")
    col2.write("\n")
    if col2.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# app("/Users/aaryan/AI Agent Builder/config/config.yaml")
def main():
    """Entry point for the Chat UI tool"""
    parser = argparse.ArgumentParser(
        description="Chat with your Documents using Fabriq Chat UI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--config",
        "-c",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)"
    )
    
    args = parser.parse_args()
    
    # Check if config file exists
    if not Path(args.config).exists():
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)
    
    # Initialize and run chatbot
    app(config_path=args.config)


if __name__ == "__main__":
    main()
