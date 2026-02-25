"""
Minimal YouTube Video Summarizer with LangChain
Paste a YouTube URL, get summary + key points + ask follow-up questions

Streamlit Interface by Codanics YouTube Channel (M. Ammar Tufail)
"""

import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import re

# ==================== ORIGINAL CODE (UNCHANGED) ====================

def get_video_id(url):
    """Extract video ID from YouTube URL"""
    pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]*)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_transcript(video_id):
    """Fetch transcript from YouTube video"""
    try:
        ytt_api = YouTubeTranscriptApi()
        
        # First, list what transcripts are available
        try:
            transcript_list = ytt_api.list(video_id)
            available_transcripts = list(transcript_list)
            
            if not available_transcripts:
                return "Error: No transcripts available for this video"
            
            # Try to find any available transcript (manual or auto-generated)
            for lang in ['en', 'en-US', 'en-GB', 'a.en']:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    data = transcript.fetch()
                    return ' '.join([entry.text for entry in data])
                except:
                    continue
            
            # If specific languages fail, take first available
            transcript = available_transcripts[0]
            data = transcript.fetch()
            return ' '.join([entry.text for entry in data])
            
        except Exception as list_error:
            # Fallback: try direct fetch with common languages
            try:
                transcript = ytt_api.fetch(video_id, languages=['en', 'en-US', 'en-GB', 'es', 'fr', 'de'])
                return ' '.join([entry.text for entry in transcript])
            except:
                return f"Error: No transcripts available for this video"
                
    except Exception as e:
        return f"Error: {str(e)}"

def summarize_video(url, api_key):
    """Main function to summarize YouTube video"""
    
    # Get video ID and transcript
    video_id = get_video_id(url)
    if not video_id:
        return "Invalid YouTube URL"
    
    transcript = get_transcript(video_id)
    
    if transcript.startswith("Error"):
        return transcript
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
    
    # Create summary prompt
    summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that summarizes YouTube videos concisely."),
        ("user", """Analyze this video transcript and provide:

1. **Summary** (2-3 sentences)
2. **Key Points** (bullet points)
3. **Main Takeaways**

Transcript:
{transcript}""")
    ])
    
    # Generate summary
    chain = summary_prompt | llm
    response = chain.invoke({"transcript": transcript})
    
    return response.content, transcript, llm

def ask_question(question, transcript, llm):
    """Ask follow-up questions about the video"""
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant answering questions about a YouTube video transcript."),
        ("user", """Based on this video transcript, answer the question:

Question: {question}

Transcript:
{transcript}""")
    ])
    
    chain = qa_prompt | llm
    response = chain.invoke({"question": question, "transcript": transcript})
    return response.content
# ==================== STREAMLIT INTERFACE ====================

# Page configuration
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF0000, #FF6B6B);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .credit-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF0000;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 0.2rem;
    }
    .stButton>button:hover {
        background-color: #CC0000;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎥 YouTube Video Summarizer</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Powered by LangChain & OpenAI | Get instant summaries and ask questions</p>', unsafe_allow_html=True)

# Credit box
st.markdown("""
    <div class="credit-box">
        <h3>📺 Created by Touseef Afridi</h3>
        <div style="display: flex; justify-content: center; gap: 10px; margin-top: 10px;">
            <a href="https://linkedin.com/in/touseef-afridi-35a59a250" target="_blank" style="background-color: #0077b5; color: white; padding: 5px 15px; border-radius: 5px; text-decoration: none; font-size: 0.9rem;">LinkedIn</a>
            <a href="https://github.com/tosif7727" target="_blank" style="background-color: #333; color: white; padding: 5px 15px; border-radius: 5px; text-decoration: none; font-size: 0.9rem;">GitHub</a>
            <a href="https://facebook.com/touseef.afridii.1" target="_blank" style="background-color: #1877f2; color: white; padding: 5px 15px; border-radius: 5px; text-decoration: none; font-size: 0.9rem;">Facebook</a>
        </div>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'summary_generated' not in st.session_state:
    st.session_state.summary_generated = False
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'llm' not in st.session_state:
    st.session_state.llm = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for API Key
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input("Enter OpenAI API Key", type="password")
    
    # Validation shows here but doesn't control other content
    if api_key:
        if api_key.startswith('sk-') and len(api_key) > 20:
            st.success("✓ API Key valid")
        else:
            st.error("✗ Invalid API Key")
    
    st.markdown("---")
    st.markdown("### 📖 How to Use")
    st.markdown("""
    1. Enter your OpenAI API key
    2. Paste a YouTube video URL
    3. Click 'Summarize Video'
    4. Ask follow-up questions!
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 Supported URLs")
    st.markdown("""
    - youtube.com/watch?v=...
    - youtu.be/...
    """)

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📺 Enter YouTube URL")
    youtube_url = st.text_input(
        "Paste YouTube URL",
        placeholder="https://www.youtube.com/watch?v= ...",
        label_visibility="collapsed"
    )
    
    # ADD VALIDATION HERE - INSIDE col1
    if youtube_url:
        pattern = r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        if re.search(pattern, youtube_url):
            st.success("✓ Valid URL")
        else:
            st.error("✗ Invalid URL")

with col2:
    st.subheader("🚀 Action")
    summarize_btn = st.button("🎬 Summarize Video", use_container_width=True)

# Process summarization
if summarize_btn:
    if not api_key:
        st.error("⚠️ Please enter your OpenAI API key in the sidebar!")
    elif not youtube_url:
        st.error("⚠️ Please enter a YouTube URL!")
    else:
        with st.spinner("🔄 Fetching transcript and generating summary..."):
            result = summarize_video(youtube_url, api_key)
            
            if isinstance(result, tuple):
                summary, transcript, llm = result
                st.session_state.summary_generated = True
                st.session_state.transcript = transcript
                st.session_state.llm = llm
                st.session_state.chat_history = []
                
                st.success("✅ Summary generated successfully!")
                
                # Display summary
                st.markdown("---")
                st.subheader("📝 Video Summary")
                st.markdown(summary)
                
            else:
                st.error(f"❌ {result}")

# Q&A Section (only show if summary is generated)
if st.session_state.summary_generated:
    st.markdown("---")
    st.subheader("💬 Ask Questions About the Video")
    
    # Display chat history
    if st.session_state.chat_history:
        for i, (q, a) in enumerate(st.session_state.chat_history):
            with st.container():
                st.markdown(f"**❓ Question {i+1}:** {q}")
                st.markdown(f"**💡 Answer:** {a}")
                st.markdown("---")
    
    # Question input
    with st.form(key="question_form", clear_on_submit=True):
        question = st.text_input(
            "Type your question here",
            placeholder="What is the main topic discussed in the video?",
            label_visibility="collapsed"
        )
        ask_btn = st.form_submit_button("🔍 Ask Question", use_container_width=True)
        
        if ask_btn and question:
            with st.spinner("🤔 Thinking..."):
                answer = ask_question(
                    question, 
                    st.session_state.transcript, 
                    st.session_state.llm
                )
                st.session_state.chat_history.append((question, answer))
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Made with ❤️ by Codanics YouTube Channel (M. Ammar Tufail)</p>
        <p>Powered by LangChain, OpenAI & Streamlit</p>
    </div>
""", unsafe_allow_html=True)