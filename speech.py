import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
from deep_translator.exceptions import NotValidPayload
import sounddevice as sd
from scipy.io.wavfile import write
import os
from dotenv import load_dotenv
from gtts import gTTS
import base64
import time
import hashlib
import sqlite3
from datetime import datetime
import PyDictionary
from io import StringIO

# Initialize database
def init_db():
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, 
                  password TEXT,
                  email TEXT,
                  created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

# User authentication functions
def create_user(username, password, email):
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?)",
              (username, hashed_pw, email, datetime.now()))
    conn.commit()
    conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", 
              (username, hashed_pw))
    result = c.fetchone()
    conn.close()
    return result is not None

def user_exists(username):
    conn = sqlite3.connect('auth.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    result = c.fetchone()
    conn.close()
    return result is not None

# Initialize database
init_db()

# Set page config
st.set_page_config(
    page_title="Voice Translator Pro",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main color scheme (Beige/Black theme)
BEIGE = "#F5F5DC"
DARK_BEIGE = "#E8E8D0"
BLACK = "#121212"
DARK_GRAY = "#1E1E1E"
PRIMARY = "#4A6FA5"
SECONDARY = "#6B8CBE"
ACCENT = "#FF9F1C"

# CSS for the entire app
st.markdown(f"""
<style>
    /* Base styles */
    :root {{
        --background-color: {BEIGE};
        --text-color: {BLACK};
        --primary-color: {PRIMARY};
        --secondary-color: {SECONDARY};
        --accent-color: {ACCENT};
        --card-bg: {DARK_BEIGE};
        --hover-color: {DARK_GRAY};
        --hover-text: white;
    }}

    /* Dark mode override */
    @media (prefers-color-scheme: dark) {{
        :root {{
            --background-color: {DARK_GRAY};
            --text-color: {BEIGE};
            --card-bg: {BLACK};
            --hover-color: {BEIGE};
            --hover-text: {BLACK};
        }}
    }}

    /* Global styles */
    .stApp {{
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }}
    
    /* Button styles */
    .stButton>button {{
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        background-color: var(--primary-color);
        color: white;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    
    .stButton>button:hover {{
        background-color: var(--accent-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        color: var(--hover-text);
    }}
    
    /* Card styles */
    .card {{
        background-color: var(--card-bg);
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }}
    
    .card:hover {{
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
    }}
    
    /* Input fields */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea {{
        background-color: var(--card-bg);
        color: var(--text-color);
    }}
    
    /* Select boxes */
    .stSelectbox>div>div {{
        background-color: var(--card-bg);
        color: var(--text-color);
    }}
    
    /* File uploader */
    .stFileUploader>div {{
        border: 2px dashed var(--primary-color);
        border-radius: 10px;
        padding: 30px;
        background-color: var(--card-bg);
        transition: all 0.3s ease;
    }}
    
    .stFileUploader>div:hover {{
        border-color: var(--accent-color);
        background-color: var(--hover-color);
    }}
    
    /* Special elements */
    .title-container {{
        background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
        padding: 25px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .indian-lang {{
        font-size: 24px;
        text-align: center;
        margin: 20px 0;
        padding: 20px;
        background-color: var(--card-bg);
        border-radius: 10px;
        border-left: 5px solid var(--accent-color);
    }}
    
    /* Auth pages */
    .auth-container {{
        max-width: 500px;
        margin: 0 auto;
        padding: 30px;
        background-color: var(--card-bg);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .auth-title {{
        text-align: center;
        margin-bottom: 30px;
        color: var(--primary-color);
    }}
    
    /* Navbar */
    .navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 0;
        margin-bottom: 30px;
        border-bottom: 1px solid var(--primary-color);
    }}
    
    .nav-links {{
        display: flex;
        gap: 20px;
    }}
    
    .nav-link {{
        color: var(--primary-color);
        text-decoration: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    
    .nav-link:hover {{
        color: var(--accent-color);
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
        transition: all 0.3s ease;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--primary-color);
        color: white !important;
    }}
    
    /* Text file preview */
    .text-preview {{
        max-height: 200px;
        overflow-y: auto;
        padding: 15px;
        background-color: var(--card-bg);
        border-radius: 8px;
        margin-top: 10px;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize recognizer
recognizer = sr.Recognizer()

# Initialize dictionary
dictionary = PyDictionary.PyDictionary()

# Language options
LANGUAGE_OPTIONS = {
    'en': 'English',
    'hi': 'Hindi',
    'kn': 'Kannada',
    'mr': 'Marathi',
    'ta': 'Tamil',
    'te': 'Telugu',
    'bn': 'Bengali',
    'gu': 'Gujarati',
    'ml': 'Malayalam',
    'pa': 'Punjabi'
}

def get_default_language_index():
    return list(LANGUAGE_OPTIONS.keys()).index('en')

# Authentication pages
def login_page():
    st.markdown("""
    <div class="auth-container">
        <h2 class="auth-title">Login to Voice Translator Pro</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful! Redirecting...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Account"):
            st.session_state.auth_page = "signup"
            st.rerun()
    with col2:
        if st.button("Forgot Password"):
            st.session_state.auth_page = "forgot"
            st.rerun()

def signup_page():
    st.markdown("""
    <div class="auth-container">
        <h2 class="auth-title">Create New Account</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("signup_form"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Create Account")
        
        if submit:
            if user_exists(username):
                st.error("Username already exists")
            elif password != confirm_password:
                st.error("Passwords don't match")
            else:
                create_user(username, password, email)
                st.success("Account created successfully! Please login.")
                time.sleep(1)
                st.session_state.auth_page = "login"
                st.rerun()
    
    if st.button("Back to Login"):
        st.session_state.auth_page = "login"
        st.rerun()

def forgot_password_page():
    st.markdown("""
    <div class="auth-container">
        <h2 class="auth-title">Reset Password</h2>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("forgot_form"):
        email = st.text_input("Enter your email")
        submit = st.form_submit_button("Send Reset Link")
        
        if submit:
            st.success("If an account exists with this email, you'll receive a reset link")
    
    if st.button("Back to Login"):
        st.session_state.auth_page = "login"
        st.rerun()

# Text processing functions
def extract_text_from_file(file):
    if file.name.endswith('.txt'):
        stringio = StringIO(file.getvalue().decode("utf-8"))
        return stringio.read()
    elif file.name.endswith('.docx'):
        import docx
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        st.error("Unsupported file format")
        return None

def get_synonyms_antonyms(word, language='en'):
    try:
        # For English only (PyDictionary limitation)
        if language != 'en':
            return {"synonyms": [], "antonyms": []}
            
        synonyms = dictionary.synonym(word) or []
        antonyms = dictionary.antonym(word) or []
        return {
            "synonyms": list(set(synonyms))[:10],  # Limit to 10 synonyms
            "antonyms": list(set(antonyms))[:10]    # Limit to 10 antonyms
        }
    except:
        return {"synonyms": [], "antonyms": []}

# Main app functions
def record_audio(duration=5, sample_rate=44100):
    with st.spinner(f"Recording for {duration} seconds... Speak now!"):
        recording = sd.rec(int(duration * sample_rate), 
                        samplerate=sample_rate, 
                        channels=1, 
                        dtype='int16')
        sd.wait()
        write("temp_recording.wav", sample_rate, recording)
        st.toast("Recording complete!", icon="🎤")
    return "temp_recording.wav"

def speech_to_text(audio_file, input_lang='en'):
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            lang_map = {
                'English': 'en-IN',
                'Hindi': 'hi-IN',
                'Kannada': 'kn-IN',
                'Marathi': 'mr-IN',
                'Tamil': 'ta-IN',
                'Telugu': 'te-IN',
                'Bengali': 'bn-IN',
                'Gujarati': 'gu-IN',
                'Malayalam': 'ml-IN',
                'Punjabi': 'pa-IN'
            }
            language_code = lang_map.get(input_lang, 'en-IN')
            text = recognizer.recognize_google(audio_data, language=language_code)
            return text
    except sr.UnknownValueError:
        st.error("Could not understand audio")
        return None
    except sr.RequestError as e:
        st.error(f"Service error: {e}")
        return None

def translate_text(text, target_language='en'):
    try:
        translation = GoogleTranslator(source='auto', target=target_language).translate(text)
        return translation
    except NotValidPayload as e:
        st.error(f"Translation error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected translation error: {e}")
        return None

def text_to_speech(text, language_code):
    try:
        tts = gTTS(text=text, lang=language_code, slow=False)
        audio_file = "translated_speech.mp3"
        tts.save(audio_file)
        return audio_file
    except Exception as e:
        st.error(f"Text-to-speech error: {e}")
        return None

def autoplay_audio(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)

def main_app():
    # Navigation bar
    st.markdown(f"""
    <div class="navbar">
        <h2>Voice Translator Pro</h2>
        <div class="nav-links">
            <span style="color: var(--text-color);">Welcome, {st.session_state.username}</span>
            <a class="nav-link" href="#" onclick="alert('Logged out'); window.location.href = '?logout=true';">Logout</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # App title
    st.markdown("""
    <div class="title-container">
        <h1>🗣️ Voice Translator Pro</h1>
        <h4>Premium Translation Experience</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["Translation", "Text Processing", "Word Analysis"])
    
    with tab1:
        # Language selection
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            input_lang = st.selectbox("Input Language", 
                                    ['English', 'Hindi', 'Kannada', 'Marathi', 
                                     'Tamil', 'Telugu', 'Bengali', 'Gujarati', 
                                     'Malayalam', 'Punjabi'])
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            target_language = st.selectbox(
                "Translation Language",
                list(LANGUAGE_OPTIONS.values()),
                index=get_default_language_index()
            )
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Input method tabs
        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🎤 Voice Input", "✍️ Text Input", "📄 File Upload"])
        
        with sub_tab1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            duration = st.slider("Recording duration (seconds)", 1, 10, 5)
            if st.button("🎙️ Start Recording", key="record_btn"):
                audio_file = record_audio(duration)
                st.audio(audio_file)
                text = speech_to_text(audio_file, input_lang)
                if text:
                    st.subheader("Recognized Text")
                    st.markdown(f"<div style='background-color: var(--card-bg); padding: 15px; border-radius: 10px;'>{text}</div>", unsafe_allow_html=True)
                    st.session_state.original_text = text
                    os.remove(audio_file)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with sub_tab2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            text_input = st.text_area("Enter text to translate", height=150)
            if st.button("Translate Text", key="text_translate_btn"):
                if text_input:
                    st.session_state.original_text = text_input
                else:
                    st.warning("Please enter some text to translate")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with sub_tab3:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("""
            <div style="border: 2px dashed var(--primary-color); border-radius: 10px; padding: 30px; text-align: center; margin-bottom: 20px; background-color: var(--card-bg);">
                <p style="font-size: 16px; color: var(--text-color);">Drag and drop your text file here or click to browse</p>
            </div>
            """, unsafe_allow_html=True)
            
            text_file = st.file_uploader("Upload text file", type=["txt", "docx"], label_visibility="collapsed", key="text_file_uploader")
            if text_file:
                with st.spinner("Processing file..."):
                    extracted_text = extract_text_from_file(text_file)
                    if extracted_text:
                        st.subheader("File Content Preview")
                        st.markdown(f'<div class="text-preview">{extracted_text[:1000]}{"..." if len(extracted_text) > 1000 else ""}</div>', unsafe_allow_html=True)
                        st.session_state.original_text = extracted_text
            st.markdown("</div>", unsafe_allow_html=True)
        
        # Translation section
        if 'original_text' in st.session_state:
            st.divider()
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            if st.button("🌍 Translate Text", key="translate_btn"):
                target_code = list(LANGUAGE_OPTIONS.keys())[list(LANGUAGE_OPTIONS.values()).index(target_language)]
                translated_text = translate_text(st.session_state.original_text, target_code)
                
                if translated_text:
                    st.markdown(f"""
                    <div style='background-color: var(--primary-color); color: white; border-radius: 15px; padding: 20px; margin-bottom: 20px;'>
                        <h3>Translated to {target_language}</h3>
                        <p>{translated_text}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if target_code in ['hi', 'kn', 'mr', 'ta', 'te', 'bn', 'gu', 'ml', 'pa']:
                        st.markdown(f"<div class='indian-lang'>{translated_text}</div>", unsafe_allow_html=True)
                    
                    st.subheader("🔊 Speech Output")
                    audio_file = text_to_speech(translated_text, target_code)
                    if audio_file:
                        st.audio(audio_file)
                        autoplay_audio(audio_file)
                        if os.path.exists(audio_file):
                            os.remove(audio_file)
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.header("Text Processing Tools")
        
        processing_option = st.radio("Select operation:", 
                                   ["Text Summarization", "Keyword Extraction", "Sentiment Analysis"])
        
        text_input = st.text_area("Enter text to process", height=200)
        
        if st.button("Process Text"):
            if text_input:
                with st.spinner("Processing..."):
                    if processing_option == "Text Summarization":
                        # Simple summarization (would replace with proper NLP in production)
                        sentences = text_input.split('.')
                        summary = '. '.join(sentences[:3]) + '.' if len(sentences) > 3 else text_input
                        st.subheader("Summary")
                        st.write(summary)
                    elif processing_option == "Keyword Extraction":
                        # Simple keyword extraction (would replace with proper NLP in production)
                        words = [word for word in text_input.split() if len(word) > 5]
                        keywords = list(set(words))[:10]  # Get first 10 unique longer words
                        st.subheader("Keywords")
                        st.write(", ".join(keywords))
                    elif processing_option == "Sentiment Analysis":
                        # Simple sentiment (would replace with proper NLP in production)
                        positive_words = ["good", "great", "excellent", "happy"]
                        sentiment = "positive" if any(word in text_input.lower() for word in positive_words) else "neutral/negative"
                        st.subheader("Sentiment")
                        st.write(sentiment)
            else:
                st.warning("Please enter some text to process")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.header("Word Analysis")
        
        col1, col2 = st.columns(2)
        with col1:
            word = st.text_input("Enter a word")
            language = st.selectbox("Select language", 
                                   ['English', 'Hindi', 'Kannada', 'Marathi', 
                                    'Tamil', 'Telugu', 'Bengali', 'Gujarati', 
                                    'Malayalam', 'Punjabi'])
        
        if st.button("Analyze Word"):
            if word:
                lang_code = list(LANGUAGE_OPTIONS.keys())[list(LANGUAGE_OPTIONS.values()).index(language)]
                results = get_synonyms_antonyms(word, lang_code)
                
                st.subheader("Analysis Results")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("""
                    <div style='background-color: var(--card-bg); padding: 15px; border-radius: 10px;'>
                        <h4>Synonyms</h4>
                        <ul>
                    """ + "\n".join([f"<li>{syn}</li>" for syn in results["synonyms"]]) + """
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div style='background-color: var(--card-bg); padding: 15px; border-radius: 10px;'>
                        <h4>Antonyms</h4>
                        <ul>
                    """ + "\n".join([f"<li>{ant}</li>" for ant in results["antonyms"]]) + """
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
                
                if not results["synonyms"] and not results["antonyms"]:
                    st.warning("No synonyms/antonyms found or language not supported (currently only English fully supported)")
            else:
                st.warning("Please enter a word to analyze")
        st.markdown("</div>", unsafe_allow_html=True)

# Main app flow
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.auth_page = "login"

if 'logout' in st.query_params:
    st.session_state.logged_in = False
    st.session_state.auth_page = "login"
    st.query_params.clear()
    st.rerun()

if not st.session_state.logged_in:
    if st.session_state.auth_page == "login":
        login_page()
    elif st.session_state.auth_page == "signup":
        signup_page()
    elif st.session_state.auth_page == "forgot":
        forgot_password_page()
else:
    main_app()
