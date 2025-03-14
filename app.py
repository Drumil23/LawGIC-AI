import streamlit as st
import os
from agno.agent import Agent, RunResponse
from agno.models.google.gemini import Gemini
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.document.chunking.document import DocumentChunking
from agno.vectordb.qdrant import Qdrant
from agno.embedder.google import GeminiEmbedder
from pypdf import PdfReader
from dotenv import load_dotenv
from htmlTemplates import css, bot_template, user_template

# Set page configuration
st.set_page_config(
    page_title="lawgic-ai",
    page_icon="📚",
    layout="wide"
)

# Initialize session state variables
if 'law_docs_content' not in st.session_state:
    st.session_state.law_docs_content = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "references" not in st.session_state:
    st.session_state.references = []
if "knowledge_base_loaded" not in st.session_state:
    st.session_state.knowledge_base_loaded = False

load_dotenv()
# Initialize API keys and database connections once
if 'vector_db' not in st.session_state:
    # key=os.environ["GOOGLE_API_KEY"]
    st.session_state.vector_db = Qdrant(
        collection=os.getenv("QDRANT_COLLECTION"),
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY"),
        embedder=GeminiEmbedder(dimensions=768)
    )
    
    st.session_state.BNS_knowledge_base = PDFUrlKnowledgeBase(
        urls=["https://www.indiacode.nic.in/bitstream/123456789/20062/1/a2023-45.pdf","https://www.indiacode.nic.in/bitstream/123456789/20099/3/aa2023-46.pdf","https://www.indiacode.nic.in/bitstream/123456789/20063/1/a2023-47.pdf"],
        vector_db=st.session_state.vector_db,
        num_documents=3,
        embedder=GeminiEmbedder(dimensions=768),
        chunking_strategy=DocumentChunking(chunk_size=1500)
    )

# Load knowledge base only once
if not st.session_state.knowledge_base_loaded:
    with st.spinner("🔄 Training model on Bharatiya Nyaya Sanhita and more..."):
        st.session_state.BNS_knowledge_base.load(upsert=True)
        st.session_state.knowledge_base_loaded = True

# Sidebar for settings and information
with st.sidebar:
    st.title("LawGIC - AI")
    st.markdown("Ask questions about *Bharatiya Nyaya Sanhita, 2023* and get AI-powered answers.")
    st.divider()
    
    if st.button("Clear Chat 🗑️"):
        st.session_state.messages = []
        st.cache_data.clear()
        st.rerun(scope="app")

    # File uploader for legal proceedings
    law_docs = st.file_uploader("Upload Your Legal Proceedings", type=["pdf"], help="Upload a PDF file to use as the knowledge base.")
    
    if law_docs is not None:
       pdf_reader = PdfReader(law_docs)
       text = ""
       for page_num in range(len(pdf_reader.pages)):
           page = pdf_reader.pages[page_num]
           text += page.extract_text()
       st.session_state.law_docs_content = text
    
    # Add document button
    if st.button("Add  document"):
        # Update agent with new content without reloading knowledge base
        st.session_state.agent = Agent(
            # model=Groq(id="deepseek-r1-distill-llama-70b", max_tokens=1024),
            model=Gemini("gemini-2.0-flash-lite",api_key=os.environ["GOOGLE_API_KEY"], max_output_tokens=1024),
            markdown=True,
            knowledge=st.session_state.BNS_knowledge_base,
            debug_mode=True,
            search_knowledge=True,
            add_references=True,
            expected_output="An unbiased advice to the query based on the provided content.",
            num_history_responses=3,
            show_tool_calls=False,
            additional_context=st.session_state.law_docs_content,
            instructions=[
                "You are a legal assistant who will respond based on *Bharatiya Nyaya Sanhita, 2023*.",
                "Understand the legal query from the user.",
                "Search the knowledge base for relevant information.",
                "Provide a relevant legal answer to the user.",
                "For questions such as 'Hi', 'Hello', 'How are you?', the assistant will respond with a greeting."
            ]
        )
        st.success("Document added")
    
    # Clear document button
    if st.button("Clear document"):
        st.session_state.law_docs_content = ""
        # Update agent with empty additional context
        st.session_state.agent = Agent(
            model=Gemini("gemini-2.0-flash-lite",api_key=os.environ["GOOGLE_API_KEY"], max_output_tokens=1024),
            markdown=True,
            knowledge=st.session_state.BNS_knowledge_base,
            debug_mode=True,
            search_knowledge=True,
            add_references=True,
            expected_output="An unbiased advice to the query based on the provided content.",
            num_history_responses=3,
            show_tool_calls=False,
            additional_context="",
            instructions=[
                "You are a legal assistant who will respond based on *Bharatiya Nyaya Sanhita, 2023*.",
                "Understand the legal query from the user.",
                "Search the knowledge base for relevant information.",
                "Provide a relevant legal answer to the user.",
                "If there are no relevant results, provide a generic response.",
                "For questions such as 'Hi', 'Hello', 'How are you?', the assistant will respond with a greeting."
            ]
        )
        st.success("Document cleared")

# Initialize agent if not already done
if 'agent' not in st.session_state:
    st.session_state.agent = Agent(
        model= Gemini("gemini-2.0-flash-lite",api_key=os.environ["GOOGLE_API_KEY"], max_output_tokens=1024),
        markdown=True,
        knowledge=st.session_state.BNS_knowledge_base,
        debug_mode=True,
        search_knowledge=True,
        add_references=True,
        expected_output="An unbiased advice to the query based on the provided content.",
        num_history_responses=3,
        show_tool_calls=False,
        additional_context=st.session_state.law_docs_content,
        instructions=[
            "You are a legal assistant who will respond based on *Bharatiya Nyaya Sanhita, 2023*.",
            "Understand the legal query from the user.",
            "Search the knowledge base for relevant information.",
            "Provide a relevant legal answer to the user.",
            "If there are no relevant results, provide a generic response.",
            "For questions such as 'Hi', 'Hello', 'How are you?', the assistant will respond with a greeting."
        ]
    )


if 'messages' not in st.session_state:
    st.session_state.messages = []

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("## Chat with Legal Assistant 💬 ")
    st.divider()

    # Display the CSS for custom styles
    st.markdown(css, unsafe_allow_html=True)

    # Container for messages
    chat_container = st.container(height=500)

    # Display messages inside the container
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] == "user":
                # Render the user's message with the custom user template
                user_msg_html = user_template.replace("{{MSG}}", message["content"])
                st.markdown(user_msg_html, unsafe_allow_html=True)
            elif message["role"] == "assistant":
                # Render the assistant's message with the custom bot template
                bot_msg_html = bot_template.replace("{{MSG}}", message["content"])
                st.markdown(bot_msg_html, unsafe_allow_html=True)

    # Input and processing below the container
    if prompt := st.chat_input("Ask a legal question..."):
        # Add user message to state
        st.session_state.messages.append({"role": "user", "content": prompt})

        try:
            with st.spinner("✍️ Generating response..."):
                response: RunResponse = st.session_state.agent.run(prompt)
                if hasattr(response, 'extra_data') and hasattr(response.extra_data, 'references'):
                    st.session_state.references = response.extra_data.references[0].references
                else:
                    st.session_state.references = []
            
            # Add assistant response to state
            st.session_state.messages.append({"role": "assistant", "content": response.content})
            
            # Force rerun to update the container with new messages
            st.rerun()
            
        except Exception as e:
            st.error(f"⚠️ An error occurred: {str(e)}")
            st.session_state.references = []

with col2:
    st.markdown("## References 📚")
    st.divider()
    
    # Access references from session state instead of local variable
    if st.session_state.references:
        for reference in st.session_state.references:
            try:
                with st.expander(label=f"Page no. {reference.get('meta_data', 'Unknown').get('page', 'Unknown')}"):
                    with st.container(height=300):
                        st.markdown(f"- {reference.get('content', 'Nothing here')}")
            except Exception as e:
                st.error(f"Error displaying reference: {str(e)}")
    else:
        st.write("No references available.")
