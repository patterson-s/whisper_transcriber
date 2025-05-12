import streamlit as st
from pathlib import Path
import whisper
import tempfile
import os
from typing import Optional, Dict
import time
from streamlit_mic_recorder import mic_recorder
import datetime

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

def save_audio_file(audio_data):
    """Save audio bytes to a temporary file."""
    if not audio_data or 'bytes' not in audio_data:
        return None
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
        tmp_file.write(audio_data['bytes'])
        return tmp_file.name

def transcribe_audio(audio_data):
    """Transcribe audio data and return the transcription text."""
    if not audio_data or 'bytes' not in audio_data:
        return None
        
    # Save the audio to a temporary file
    audio_path = save_audio_file(audio_data)
    
    if not audio_path:
        return None
        
    try:
        # Transcribe the audio
        transcriber = AudioTranscriber()
        transcription = transcriber.transcribe_file(audio_path)
        return transcription
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        return None
    finally:
        # Clean up the temporary file
        try:
            os.unlink(audio_path)
        except:
            pass

def initialize_session_state():
    """Initialize the session state variables."""
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
    
    # Initialize session state
    initialize_session_state()
    
    # Create tabs with "Record Audio" first, followed by "Upload Files"
    tab1, tab2 = st.tabs(["Record Audio", "Upload Files"])
    
    # Tab 1: Audio recording with streamlit-mic-recorder (now first)
    with tab1:
        st.subheader("Record Audio")
        
        st.write("""
        Click the microphone button below to start recording. 
        When you click it again to stop recording, the audio will be automatically transcribed.
        """)
        
        # Status area for feedback
        status_container = st.empty()
        
        # Add the audio recorder with the correct parameters
        audio_data = mic_recorder(
            start_prompt="Start Recording",
            stop_prompt="Stop Recording",
            just_once=False,
            use_container_width=True,
            key="recorder"
        )
        
        # Check if we have new audio data
        if audio_data and 'id' in audio_data and audio_data['id'] != st.session_state.last_audio_id:
            # Update the last audio ID
            st.session_state.last_audio_id = audio_data['id']
            st.session_state.audio_data = audio_data
            
            # Set transcribing flag
            st.session_state.transcribing = True
            
            # Rerun to show the transcribing status
            st.rerun()
        
        # If we're transcribing, process the audio
        if st.session_state.transcribing and st.session_state.audio_data:
            # Show status
            with status_container:
                st.info("Transcribing your recording... Please wait.")
            
            # Play the audio for feedback
            st.audio(st.session_state.audio_data['bytes'], format="audio/wav")
            
            # Transcribe the audio
            with st.spinner("Processing..."):
                transcription = transcribe_audio(st.session_state.audio_data)
                
                if transcription:
                    # Add to combined transcript (without timestamps/recording numbers, just with spacing)
                    if st.session_state.combined_transcript:
                        st.session_state.combined_transcript += f"\n\n{transcription.strip()}"
                    else:
                        st.session_state.combined_transcript = transcription.strip()
                    
                    # Update status
                    with status_container:
                        st.success("Transcription complete! You can record another clip.")
                else:
                    # Update status
                    with status_container:
                        st.error("Transcription failed. Please try recording again.")
            
            # Reset transcribing flag
            st.session_state.transcribing = False
        
        # Display the combined transcript
        if st.session_state.combined_transcript:
            st.subheader("Transcript")
            
            # Display the combined transcript
            st.text_area(
                "Accumulated Transcriptions",
                st.session_state.combined_transcript,
                height=300
            )
            
            # Column layout for buttons
            col1, col2 = st.columns(2)
            
            # Download button for the combined transcript
            with col1:
                st.download_button(
                    "Download Transcript",
                    st.session_state.combined_transcript,
                    "transcript.txt",
                    "text/plain"
                )
            
            # Clear transcript button
            with col2:
                if st.button("Clear Transcript"):
                    st.session_state.combined_transcript = ""
                    st.rerun()
                
        # Provide a fallback message if the browser recording doesn't work
        with st.expander("Having trouble with recording?"):
            st.info("""
            If you're having trouble with the browser recording feature:
            1. Make sure your browser allows microphone access
            2. Try using the "Upload Files" tab instead to upload pre-recorded audio
            """)
    
    # Tab 2: File upload functionality (now second)
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
                    st.download_button(
                        "Download All Transcriptions",
                        combined_text,
                        "combined_transcriptions.txt",
                        "text/plain"
                    )

if __name__ == "__main__":
    main()