import streamlit as st
from streamlit.components.v1 import html
import os
from email_generator import init_llm, generate_email_enhanced

# Page configuration
st.set_page_config(
    page_title="Professional Email Writer",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Card styling */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Content box styling */
    .content-box {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }
    
    /* Header styling */
    .header-text {
        color: white;
        text-align: center;
        padding: 2rem 0;
        font-size: 3rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    .subheader-text {
        color: white;
        text-align: center;
        font-size: 1.2rem;
        margin-top: -1.5rem;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    /* Text area styling */
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Input styling */
    .stTextInput input {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Select box styling */
    .stSelectbox select {
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        transition: all 0.3s ease;
    }
    
    /* Success message styling */
    .stSuccess {
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
    }
    
    /* Email output box */
    .email-output {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        font-family: 'Courier New', monospace;
        white-space: pre-wrap;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    /* Tone card styling */
    .tone-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .tone-card:hover {
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: white;
    }
    
    /* Info box styling */
    .info-box {
        background: #e7f3ff;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    
    /* Feature badge */
    .feature-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_email' not in st.session_state:
    st.session_state.generated_email = None
if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = False

# Tone options
TONE_OPTIONS = {
    "Professional": {
        "icon": "💼",
        "description": "Formal and business-appropriate",
        "color": "#2c3e50"
    },
    "Friendly": {
        "icon": "😊",
        "description": "Warm and approachable while maintaining professionalism",
        "color": "#3498db"
    },
    "Casual": {
        "icon": "👋",
        "description": "Relaxed and informal",
        "color": "#1abc9c"
    },
    "Formal": {
        "icon": "🎩",
        "description": "Very formal and diplomatic",
        "color": "#34495e"
    },
    "Urgent": {
        "icon": "⚡",
        "description": "Direct and time-sensitive",
        "color": "#e74c3c"
    },
    "Apologetic": {
        "icon": "🙏",
        "description": "Expressing regret or making amends",
        "color": "#9b59b6"
    }
}

# Header
st.markdown('<h1 class="header-text">✉️ Professional Email Writer</h1>', unsafe_allow_html=True)
st.markdown('<p class="subheader-text">Transform your bullet points into polished, professional emails in seconds</p>', unsafe_allow_html=True)

# Sidebar for API Key and Settings
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    
    # API Key input
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        value=os.getenv("OPENAI_API_KEY", ""),
        help="Enter your OpenAI API key to use the email generator"
    )
    
    if api_key:
        st.session_state.api_key_set = True
        st.success("✅ API Key configured!")
    else:
        st.warning("⚠️ Please enter your API key to continue")
    
    st.markdown("---")
    
    # Feature highlights
    st.markdown("## ✨ Features")
    st.markdown("""
    <div class="feature-badge">6 Tone Options</div>
    <div class="feature-badge">Personalization</div>
    <div class="feature-badge">AI-Powered</div>
    <div class="feature-badge">Instant Generation</div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # About section
    st.markdown("## 📖 About")
    st.markdown("""
    This tool uses advanced AI to convert your brief notes into 
    well-structured, professional emails. Simply enter your key 
    points and let the AI handle the rest!
    """)

# Main content
if st.session_state.api_key_set:
    # Create two columns for better layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 Email Details")
        
        # Email notes input
        notes = st.text_area(
            "Enter your email notes (bullet points)",
            height=150,
            placeholder="• Meeting scheduled for tomorrow at 2pm\n• Need project update\n• Deadline is Friday",
            help="Enter the key points you want to include in your email"
        )
        
        # Recipient name
        recipient_name = st.text_input(
            "Recipient's Name (Optional)",
            placeholder="John Smith",
            help="Enter the recipient's name for a personalized greeting"
        )
        
        # Sender name
        sender_name = st.text_input(
            "Your Name (Optional)",
            placeholder="Jane Doe",
            help="Enter your name for the email sign-off"
        )
    
    with col2:
        st.markdown("### 🎨 Select Email Tone")
        
        # Tone selection with custom styling
        tone_options = list(TONE_OPTIONS.keys())
        
        # Create a more visual tone selector
        selected_tone = st.selectbox(
            "Choose the tone for your email",
            tone_options,
            format_func=lambda x: f"{TONE_OPTIONS[x]['icon']} {x} - {TONE_OPTIONS[x]['description']}",
            help="Select the appropriate tone for your email based on the context"
        )
        
        # Display tone info
        st.markdown(f"""
        <div class="info-box">
            <strong>{TONE_OPTIONS[selected_tone]['icon']} {selected_tone} Tone</strong><br>
            {TONE_OPTIONS[selected_tone]['description']}
        </div>
        """, unsafe_allow_html=True)
    
    # Generate button
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    
    with col_btn2:
        generate_button = st.button("🚀 Generate Professional Email", use_container_width=True)
    
    # Generate email
    if generate_button:
        if not notes.strip():
            st.error("⚠️ Please enter some notes for your email!")
        else:
            with st.spinner("✨ Crafting your professional email..."):
                # Initialize LLM
                llm = init_llm(api_key)
                
                # Generate email
                email = generate_email_enhanced(
                    notes,
                    selected_tone,
                    recipient_name if recipient_name else None,
                    sender_name if sender_name else None,
                    llm
                )
                
                st.session_state.generated_email = email
    
    # Display generated email
    if st.session_state.generated_email:
        st.markdown("---")
        st.markdown("### 📧 Generated Email")
        
        # Email output with copy button
        st.markdown(f"""
        <div class="email-output">
{st.session_state.generated_email}
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col_action1, col_action2, col_action3 = st.columns(3)
        
        with col_action1:
            st.download_button(
                label="📥 Download Email",
                data=st.session_state.generated_email,
                file_name="professional_email.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_action2:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(st.session_state.generated_email, language=None)
                st.success("✅ Email displayed above - copy from the code block!")
        
        with col_action3:
            if st.button("🔄 Generate New", use_container_width=True):
                st.session_state.generated_email = None
                st.rerun()

else:
    # Show instructions when API key is not set
    st.markdown("""
    <div class="content-box">
        <h2>👋 Welcome to Professional Email Writer!</h2>
        <p>To get started, please enter your OpenAI API key in the sidebar.</p>
        
    <h3>🚀 How to use:</h3>
        <ol>
            <li>Enter your OpenAI API key in the sidebar</li>
            <li>Write your email notes or bullet points</li>
            <li>Select your preferred tone</li>
            <li>Add recipient and sender names (optional)</li>
            <li>Click "Generate Professional Email"</li>
        </ol>
        
    <h3>💡 Tips for best results:</h3>
        <ul>
            <li>Be clear and specific with your bullet points</li>
            <li>Include key information like dates, times, and action items</li>
            <li>Choose the tone that matches your relationship with the recipient</li>
            <li>Review and customize the generated email before sending</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ============================================
# CUSTOM CSS FOR HOVER EFFECTS
# Injected via st.markdown with style tags
# ============================================
st.markdown("""
<style>
/* YouTube Button Hover Effects */
.yt-subscribe-btn {
    border-radius: 25px !important;
    box-shadow: 0 4px 15px rgba(255,0,0,0.3) !important;
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    cursor: pointer !important;
}

.yt-subscribe-btn:hover {
    transform: scale(1.15) rotate(-2deg) !important;
    box-shadow: 0 8px 30px rgba(255,0,0,0.6), 0 0 20px rgba(255,0,0,0.4) !important;
    filter: brightness(1.2) !important;
}

/* Social Links Hover Effects */
.social-btn {
    margin: 5px !important;
    transition: all 0.3s ease !important;
}

.social-btn:hover {
    transform: scale(1.1) !important;
    filter: brightness(1.2) !important;
}

/* Instructor Card Hover */
.instructor-card {
    transform: scale(1);
    transition: transform 0.3s ease;
}

.instructor-card:hover {
    transform: scale(1.02);
}
</style>
""", unsafe_allow_html=True)

# ============================================
# MAIN FOOTER HTML
# Using class-based CSS instead of inline JS
# ============================================
footer_html = """
<div align="center">

<!-- ============================================ -->
<!-- ANIMATED GRADIENT WAVE HEADER -->
<!-- ============================================ -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=120&section=footer&text=Thank%20You!&fontSize=50&fontAlignY=65&animation=twinkling" width="100%"/>

<br>

<!-- ============================================ -->
<!-- GLASSMORPHISM CARD CONTAINER -->
<!-- ============================================ -->
<div style="
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 30px;
  max-width: 600px;
  margin: 20px auto;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
">

<!-- ============================================ -->
<!-- ANIMATED TYPING BADGE -->
<!-- ============================================ -->
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&duration=3000&pause=1000&color=00D9FF&center=true&vCenter=true&width=500&lines=Crafted+with+%E2%9D%A4%EF%B8%8F+by+Touseef+Afridi;Proud+Student+of+Codanics;Learning+from+the+Best!" alt="Typing SVG" />

<br>

<!-- ============================================ -->
<!-- INSTRUCTOR SPOTLIGHT CARD -->
<!-- ============================================ -->
<div class="instructor-card" style="
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  padding: 20px;
  margin: 15px 0;
">
  
  <img src="https://img.shields.io/badge/👨‍🏫-Mentor-ff6b6b?style=for-the-badge&labelColor=black" />
  
  <h3 style="color: white; margin: 10px 0;">
    <a href="https://www.youtube.com/c/Codanics" style="color: #ffd700; text-decoration: none; font-weight: bold;">
      ✨ Dr. Ammar Tufail ✨
    </a>
  </h3>
  
<p style="color: #e0e0e0; font-size: 14px;">
    Transforming students into AI Engineers at 
    <a href="https://www.youtube.com/c/Codanics" target="_blank" style="color: #00d9ff; text-decoration: none;">
      <strong>Codanics</strong>
    </a>
</p>
  
</div>

<br>

<!-- ============================================ -->
<!-- SOCIAL LINKS WITH CSS HOVER -->
<!-- ============================================ -->
<p align="center">

<!-- LinkedIn - ACTIVE -->
<a href="https://www.linkedin.com/in/touseef-afridi-35a59a250/" target="_blank">
  <img class="social-btn" src="https://img.shields.io/badge/🔗_LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white&labelColor=0d1117" height="35"/>
</a>

<!-- GitHub - ACTIVE -->
<a href="https://github.com/tosif7727" target="_blank">
  <img class="social-btn" src="https://img.shields.io/badge/🔗_GitHub-100000?style=for-the-badge&logo=github&logoColor=white&labelColor=0d1117" height="35"/>
</a>

<!-- Twitter - COMMENTED OUT -->
<!-- <a href="your-twitter-url" target="_blank">
  <img class="social-btn" src="https://img.shields.io/badge/🔗_Twitter-1DA1F2?style=for-the-badge&logo=twitter&logoColor=white&labelColor=0d1117" height="35"/>
</a> -->

<!-- Portfolio - COMMENTED OUT -->
<!-- <a href="your-portfolio-url" target="_blank">
  <img class="social-btn" src="https://img.shields.io/badge/🔗_Portfolio-FF6B6B?style=for-the-badge&logo=firefox&logoColor=white&labelColor=0d1117" height="35"/>
</a> -->

</p>

<br>

<!-- ============================================ -->
<!-- YOUTUBE SUBSCRIBE BUTTON WITH CSS HOVER -->
<!-- ============================================ -->
<a href="https://www.youtube.com/c/Codanics" target="_blank">
  <img src="https://img.shields.io/badge/▶️_Subscribe_to_Codanics-FF0000?style=for-the-badge&logo=youtube&logoColor=white&labelColor=8B0000" 
       height="45"
       onmouseover="this.style.transform='scale(1.05)'; this.style.transition='0.3s'"
       onmouseout="this.style.transform='scale(1)'"
       style="text-decoration: none; cursor: pointer;"/>
</a>

<br>

<!-- ============================================ -->
<!-- SNAKE ANIMATION -->
<!-- ============================================ -->
<img src="https://raw.githubusercontent.com/Platane/snk/output/github-contribution-grid-snake.svg" width="100%" style="max-width: 600px;"/>

</div>
"""
# Render the footer using components.v1.html for full CSS support
html(footer_html, height=800, scrolling=False)