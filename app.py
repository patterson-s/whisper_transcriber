import streamlit as st
from pathlib import Path
import whisper
import tempfile
import os
from typing import Optional, Dict
import time
from streamlit_mic_recorder import mic_recorder
import datetime
import streamlit.components.v1 as components
import requests
import json

SUPPORTED_FORMATS = ['.mp3', '.m4a', '.wav', '.ogg', '.mp4']
MODEL_NAME = "base"
DISCORD_MESSAGE_LIMIT = 1900

class AudioTranscriber:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = whisper.load_model(model_name)
    
    def transcribe_file(self, input_path: str) -> Optional[str]:
        try:
            result = self.model.transcribe(
                input_path,
                verbose=False,
                task="transcribe",
                language="en"
            )
            return result["text"]
        except Exception as e:
            st.error(f"Error transcribing file: {str(e)}")
            return None

def send_to_discord(transcript: str, source: str = "transcription") -> bool:
    webhook_url = st.secrets.get("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        st.error("Discord webhook URL not configured")
        return False
    
    if len(transcript) <= DISCORD_MESSAGE_LIMIT:
        return send_single_message(webhook_url, transcript)
    else:
        return send_chunked_messages(webhook_url, transcript)

def send_single_message(webhook_url: str, message: str) -> bool:
    try:
        data = {"content": message}
        response = requests.post(webhook_url, json=data, timeout=10)
        return response.status_code == 204
    except Exception as e:
        st.error(f"Error sending to Discord: {str(e)}")
        return False

def send_chunked_messages(webhook_url: str, transcript: str) -> bool:
    try:
        chunk_size = DISCORD_MESSAGE_LIMIT - 50
        chunks = [transcript[i:i+chunk_size] for i in range(0, len(transcript), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            message = f"**Part {i+1}/{len(chunks)}:**\n{chunk}"
            if not send_single_message(webhook_url, message):
                return False
            time.sleep(0.5)
        
        return True
    except Exception as e:
        st.error(f"Error sending chunked messages: {str(e)}")
        return False

def copy_to_clipboard_component(text: str, button_text: str = "Copy to Clipboard"):
    escaped_text = text.replace('`', '\\`').replace('\\', '\\\\').replace('"', '\\"')
    
    copy_button_html = f"""
    <div>
        <button onclick="copyToClipboard()" style="
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 0.375rem 0.75rem;
            border-radius: 0.25rem;
            cursor: pointer;
            font-size: 0.875rem;
            font-weight: 400;
            line-height: 1.6;
            text-align: center;
            text-decoration: none;
            white-space: nowrap;
            margin: 0;
        ">{button_text}</button>
        <span id="copy-feedback" style="
            margin-left: 10px;
            color: green;
            font-size: 0.875rem;
            display: none;
        ">Copied!</span>
    </div>
    
    <script>
    function copyToClipboard() {{
        const text = `{escaped_text}`;
        
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(text).then(function() {{
                showFeedback();
            }}).catch(function(err) {{
                fallbackCopyTextToClipboard(text);
            }});
        }} else {{
            fallbackCopyTextToClipboard(text);
        }}
    }}
    
    function fallbackCopyTextToClipboard(text) {{
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.top = "0";
        textArea.style.left = "0";
        textArea.style.position = "fixed";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {{
            document.execCommand('copy');
            showFeedback();
        }} catch (err) {{
            console.error('Fallback: Oops, unable to copy', err);
        }}
        
        document.body.removeChild(textArea);
    }}
    
    function showFeedback() {{
        const feedback = document.getElementById('copy-feedback');
        feedback.style.display = 'inline';
        setTimeout(function() {{
            feedback.style.display = 'none';
        }}, 2000);
    }}
    </script>
    """
    
    components.html(copy_button_html, height=50)

def process_files(transcriber: AudioTranscriber, files) -> Dict[str, str]:
    transcriptions = {}
    
    for uploaded_file in files:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.write(f"{uploaded_file.name}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            transcription = transcriber.transcribe_file(tmp_file_path)
            if transcription:
                transcriptions[uploaded_file.name] = transcription
                with col2:
                    st.download_button(
                        "Download",
                        transcription,
                        f"{Path(uploaded_file.name).stem}_transcription.txt",
                        "text/plain",
                        key=f"download_{uploaded_file.name}"
                    )
                
                with st.expander(f"Show transcription for {uploaded_file.name}"):
                    st.write(transcription)
        
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        
        finally:
            try:
                os.unlink(tmp_file_path)
            except:
                pass
    
    return transcriptions

def save_audio_file(audio_data):
    if not audio_data or 'bytes' not in audio_data:
        return None
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        tmp_file.write(audio_data['bytes'])
        return tmp_file.name

def transcribe_audio(audio_data):
    if not audio_data or 'bytes' not in audio_data:
        return None
        
    audio_path = save_audio_file(audio_data)
    
    if not audio_path:
        return None
        
    try:
        transcriber = AudioTranscriber()
        transcription = transcriber.transcribe_file(audio_path)
        return transcription
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None
    finally:
        try:
            os.unlink(audio_path)
        except:
            pass

def initialize_session_state():
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None
    if 'last_audio_id' not in st.session_state:
        st.session_state.last_audio_id = None
    if 'combined_transcript' not in st.session_state:
        st.session_state.combined_transcript = ""
    if 'transcribing' not in st.session_state:
        st.session_state.transcribing = False

def main():
    st.title("Whisper Transcription Model")
    st.write("Scott Robert Patterson")
    st.write("---")
    
    st.write("""
    This tool converts speech to text using OpenAI's Whisper model. 
    You can record audio directly in your browser or upload audio files.
    """)
    
    initialize_session_state()
    
    tab1, tab2 = st.tabs(["Record Audio", "Upload Files"])
    
    with tab1:
        st.subheader("Record Audio")
        
        st.write("""
        Click the microphone button below to start recording. 
        When you click it again to stop recording, the audio will be automatically transcribed.
        """)
        
        status_container = st.empty()
        
        audio_data = mic_recorder(
            start_prompt="Start Recording",
            stop_prompt="Stop Recording",
            just_once=False,
            use_container_width=True,
            key="recorder"
        )
        
        if audio_data and 'id' in audio_data and audio_data['id'] != st.session_state.last_audio_id:
            st.session_state.last_audio_id = audio_data['id']
            st.session_state.audio_data = audio_data
            st.session_state.transcribing = True
            st.rerun()
        
        if st.session_state.transcribing and st.session_state.audio_data:
            with status_container:
                st.info("Transcribing your recording... Please wait.")
            
            st.audio(st.session_state.audio_data['bytes'], format="audio/wav")
            
            with st.spinner("Processing..."):
                transcription = transcribe_audio(st.session_state.audio_data)
                
                if transcription:
                    if st.session_state.combined_transcript:
                        st.session_state.combined_transcript += f"\n\n{transcription.strip()}"
                    else:
                        st.session_state.combined_transcript = transcription.strip()
                    
                    with status_container:
                        st.success("Transcription complete! You can record another clip.")
                else:
                    with status_container:
                        st.error("Transcription failed. Please try recording again.")
            
            st.session_state.transcribing = False
        
        if st.session_state.combined_transcript:
            st.subheader("Transcript")
            
            st.text_area(
                "Accumulated Transcriptions",
                st.session_state.combined_transcript,
                height=300
            )
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.download_button(
                    "Download Transcript",
                    st.session_state.combined_transcript,
                    "transcript.txt",
                    "text/plain"
                )
            
            with col2:
                copy_to_clipboard_component(st.session_state.combined_transcript)
            
            with col3:
                if st.button("Send to Discord", key="discord_recording"):
                    with st.spinner("Sending to Discord..."):
                        if send_to_discord(st.session_state.combined_transcript, "Microphone Recording"):
                            st.success("✅ Sent to Discord!")
                        else:
                            st.error("❌ Failed to send to Discord")
            
            with col4:
                if st.button("Clear Transcript"):
                    st.session_state.combined_transcript = ""
                    st.rerun()
                
        with st.expander("Having trouble with recording?"):
            st.info("""
            If you're having trouble with the browser recording feature:
            1. Make sure your browser allows microphone access
            2. Try using the "Upload Files" tab instead to upload pre-recorded audio
            """)
    
    with tab2:
        uploaded_files = st.file_uploader(
            "Choose audio files", 
            type=[fmt.replace('.', '') for fmt in SUPPORTED_FORMATS],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            col1, col2 = st.columns([1, 1])
            start_button = col1.button("Start Transcription", key="file_transcribe", type="primary")
            
            if start_button:
                transcriber = AudioTranscriber()
                transcriptions = process_files(transcriber, uploaded_files)
                
                if transcriptions:
                    combined_text = "\n\n".join(f"{text}" for fname, text in transcriptions.items())
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.download_button(
                            "Download All Transcriptions",
                            combined_text,
                            "combined_transcriptions.txt",
                            "text/plain"
                        )
                    
                    with col2:
                        copy_to_clipboard_component(combined_text)
                    
                    with col3:
                        if st.button("Send to Discord", key="discord_files"):
                            with st.spinner("Sending to Discord..."):
                                if send_to_discord(combined_text, "File Upload"):
                                    st.success("✅ Sent to Discord!")
                                else:
                                    st.error("❌ Failed to send to Discord")

if __name__ == "__main__":
    main()