import streamlit as st
from pathlib import Path
import whisper
import tempfile
import os
from typing import Optional, Dict

SUPPORTED_FORMATS = ['.mp3', '.m4a', '.wav', '.ogg', '.mp4']
MODEL_NAME = "base"

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

def main():
    st.title("Whisper Transcription Model")
    st.write("Scott Robert Patterson")
    st.write("---")
    
    st.write("""
    This tool converts speech to text using OpenAI's Whisper model. 
    Simply upload your audio files, click 'Start Transcription', and the model will convert the speech to text. 
    You can download individual transcriptions or get all transcriptions in a single file.
    """)
    
    uploaded_files = st.file_uploader(
        "Choose audio files", 
        type=[fmt.replace('.', '') for fmt in SUPPORTED_FORMATS],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        col1, col2 = st.columns([1, 1])
        start_button = col1.button("Start Transcription", type="primary")
        
        if start_button:
            transcriber = AudioTranscriber()
            transcriptions = process_files(transcriber, uploaded_files)
            
            if transcriptions:
                combined_text = "\n\n".join(f"File: {fname}\n{text}" 
                                          for fname, text in transcriptions.items())
                st.download_button(
                    "Download All Transcriptions",
                    combined_text,
                    "combined_transcriptions.txt",
                    "text/plain"
                )

if __name__ == "__main__":
    main()