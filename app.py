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

TRANSLATIONS = {
    'en': {
        'title': "Whisper Transcription Model",
        'author': "Scott Robert Patterson",
        'description': "This tool converts speech to text using OpenAI's Whisper model. You can record audio directly in your browser or upload audio files.",
        'language_selector': "Select Language",
        'record_audio': "Record Audio",
        'upload_files': "Upload Files",
        'record_instructions': "Click the microphone button below to start recording. When you click it again to stop recording, the audio will be automatically transcribed.",
        'start_recording': "Start Recording",
        'stop_recording': "Stop Recording",
        'transcribing': "Transcribing your recording... Please wait.",
        'processing': "Processing...",
        'transcription_complete': "Transcription complete! You can record another clip.",
        'transcription_failed': "Transcription failed. Please try recording again.",
        'transcript': "Transcript",
        'accumulated_transcriptions': "Accumulated Transcriptions",
        'download_transcript': "Download Transcript",
        'copy_to_clipboard': "Copy to Clipboard",
        'send_to_discord': "Send to Discord",
        'clear_transcript': "Clear Transcript",
        'trouble_recording': "Having trouble with recording?",
        'trouble_info': "If you're having trouble with the browser recording feature:\n1. Make sure your browser allows microphone access\n2. Try using the \"Upload Files\" tab instead to upload pre-recorded audio",
        'choose_audio_files': "Choose audio files",
        'start_transcription': "Start Transcription",
        'download_all': "Download All Transcriptions",
        'sent_to_discord': "✅ Sent to Discord!",
        'failed_to_send': "❌ Failed to send to Discord",
        'sending_to_discord': "Sending to Discord...",
        'copied': "Copied!",
        'discord_webhook_error': "Discord webhook URL not configured",
        'discord_send_error': "Error sending to Discord:",
        'transcription_error': "Error transcribing file:",
        'processing_error': "Error processing",
        'chunked_error': "Error sending chunked messages:",
        'part_prefix': "Part"
    },
    'fr': {
        'title': "Modèle de Transcription Whisper",
        'author': "Scott Robert Patterson",
        'description': "Cet outil convertit la parole en texte en utilisant le modèle Whisper d'OpenAI. Vous pouvez enregistrer l'audio directement dans votre navigateur ou télécharger des fichiers audio.",
        'language_selector': "Sélectionner la langue",
        'record_audio': "Enregistrer l'audio",
        'upload_files': "Télécharger des fichiers",
        'record_instructions': "Cliquez sur le bouton microphone ci-dessous pour commencer l'enregistrement. Lorsque vous cliquez à nouveau pour arrêter l'enregistrement, l'audio sera automatiquement transcrit.",
        'start_recording': "Commencer l'enregistrement",
        'stop_recording': "Arrêter l'enregistrement",
        'transcribing': "Transcription de votre enregistrement... Veuillez patienter.",
        'processing': "Traitement en cours...",
        'transcription_complete': "Transcription terminée ! Vous pouvez enregistrer un autre clip.",
        'transcription_failed': "Échec de la transcription. Veuillez essayer d'enregistrer à nouveau.",
        'transcript': "Transcription",
        'accumulated_transcriptions': "Transcriptions accumulées",
        'download_transcript': "Télécharger la transcription",
        'copy_to_clipboard': "Copier dans le presse-papiers",
        'send_to_discord': "Envoyer sur Discord",
        'clear_transcript': "Effacer la transcription",
        'trouble_recording': "Problèmes avec l'enregistrement ?",
        'trouble_info': "Si vous avez des problèmes avec la fonction d'enregistrement du navigateur :\n1. Assurez-vous que votre navigateur autorise l'accès au microphone\n2. Essayez d'utiliser l'onglet \"Télécharger des fichiers\" pour télécharger de l'audio pré-enregistré",
        'choose_audio_files': "Choisir des fichiers audio",
        'start_transcription': "Commencer la transcription",
        'download_all': "Télécharger toutes les transcriptions",
        'sent_to_discord': "✅ Envoyé sur Discord !",
        'failed_to_send': "❌ Échec de l'envoi sur Discord",
        'sending_to_discord': "Envoi sur Discord...",
        'copied': "Copié !",
        'discord_webhook_error': "URL webhook Discord non configurée",
        'discord_send_error': "Erreur lors de l'envoi sur Discord :",
        'transcription_error': "Erreur lors de la transcription du fichier :",
        'processing_error': "Erreur lors du traitement",
        'chunked_error': "Erreur lors de l'envoi de messages fragmentés :",
        'part_prefix': "Partie"
    },
    'de': {
        'title': "Whisper Transkriptions-Modell",
        'author': "Scott Robert Patterson",
        'description': "Dieses Tool konvertiert Sprache in Text mit OpenAIs Whisper-Modell. Sie können Audio direkt in Ihrem Browser aufnehmen oder Audio-Dateien hochladen.",
        'language_selector': "Sprache auswählen",
        'record_audio': "Audio aufnehmen",
        'upload_files': "Dateien hochladen",
        'record_instructions': "Klicken Sie auf die Mikrofon-Taste unten, um die Aufnahme zu starten. Wenn Sie erneut klicken, um die Aufnahme zu stoppen, wird das Audio automatisch transkribiert.",
        'start_recording': "Aufnahme starten",
        'stop_recording': "Aufnahme stoppen",
        'transcribing': "Ihre Aufnahme wird transkribiert... Bitte warten.",
        'processing': "Verarbeitung läuft...",
        'transcription_complete': "Transkription abgeschlossen! Sie können einen weiteren Clip aufnehmen.",
        'transcription_failed': "Transkription fehlgeschlagen. Bitte versuchen Sie erneut aufzunehmen.",
        'transcript': "Transkript",
        'accumulated_transcriptions': "Gesammelte Transkriptionen",
        'download_transcript': "Transkript herunterladen",
        'copy_to_clipboard': "In Zwischenablage kopieren",
        'send_to_discord': "An Discord senden",
        'clear_transcript': "Transkript löschen",
        'trouble_recording': "Probleme mit der Aufnahme?",
        'trouble_info': "Wenn Sie Probleme mit der Browser-Aufnahmefunktion haben:\n1. Stellen Sie sicher, dass Ihr Browser Mikrofon-Zugriff erlaubt\n2. Versuchen Sie stattdessen den \"Dateien hochladen\" Tab für voraufgenommenes Audio",
        'choose_audio_files': "Audio-Dateien auswählen",
        'start_transcription': "Transkription starten",
        'download_all': "Alle Transkriptionen herunterladen",
        'sent_to_discord': "✅ An Discord gesendet!",
        'failed_to_send': "❌ Senden an Discord fehlgeschlagen",
        'sending_to_discord': "Sende an Discord...",
        'copied': "Kopiert!",
        'discord_webhook_error': "Discord Webhook-URL nicht konfiguriert",
        'discord_send_error': "Fehler beim Senden an Discord:",
        'transcription_error': "Fehler beim Transkribieren der Datei:",
        'processing_error': "Fehler beim Verarbeiten",
        'chunked_error': "Fehler beim Senden von fragmentierten Nachrichten:",
        'part_prefix': "Teil"
    },
    'es': {
        'title': "Modelo de Transcripción Whisper",
        'author': "Scott Robert Patterson",
        'description': "Esta herramienta convierte voz a texto usando el modelo Whisper de OpenAI. Puedes grabar audio directamente en tu navegador o subir archivos de audio.",
        'language_selector': "Seleccionar idioma",
        'record_audio': "Grabar audio",
        'upload_files': "Subir archivos",
        'record_instructions': "Haz clic en el botón del micrófono abajo para comenzar a grabar. Cuando hagas clic nuevamente para detener la grabación, el audio será transcrito automáticamente.",
        'start_recording': "Comenzar grabación",
        'stop_recording': "Detener grabación",
        'transcribing': "Transcribiendo tu grabación... Por favor espera.",
        'processing': "Procesando...",
        'transcription_complete': "¡Transcripción completa! Puedes grabar otro clip.",
        'transcription_failed': "Transcripción fallida. Por favor intenta grabar nuevamente.",
        'transcript': "Transcripción",
        'accumulated_transcriptions': "Transcripciones acumuladas",
        'download_transcript': "Descargar transcripción",
        'copy_to_clipboard': "Copiar al portapapeles",
        'send_to_discord': "Enviar a Discord",
        'clear_transcript': "Limpiar transcripción",
        'trouble_recording': "¿Problemas con la grabación?",
        'trouble_info': "Si tienes problemas con la función de grabación del navegador:\n1. Asegúrate de que tu navegador permita acceso al micrófono\n2. Intenta usar la pestaña \"Subir archivos\" para subir audio pregrabado",
        'choose_audio_files': "Elegir archivos de audio",
        'start_transcription': "Iniciar transcripción",
        'download_all': "Descargar todas las transcripciones",
        'sent_to_discord': "✅ ¡Enviado a Discord!",
        'failed_to_send': "❌ Error al enviar a Discord",
        'sending_to_discord': "Enviando a Discord...",
        'copied': "¡Copiado!",
        'discord_webhook_error': "URL webhook de Discord no configurada",
        'discord_send_error': "Error enviando a Discord:",
        'transcription_error': "Error transcribiendo archivo:",
        'processing_error': "Error procesando",
        'chunked_error': "Error enviando mensajes fragmentados:",
        'part_prefix': "Parte"
    }
}

LANGUAGE_OPTIONS = {
    'en': 'English',
    'fr': 'Français',
    'de': 'Deutsch',
    'es': 'Español'
}

def get_text(key: str, lang: str) -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

class AudioTranscriber:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = whisper.load_model(model_name)
    
    def transcribe_file(self, input_path: str, language: str = "en") -> Optional[str]:
        try:
            result = self.model.transcribe(
                input_path,
                verbose=False,
                task="transcribe",
                language=language
            )
            return result["text"]
        except Exception as e:
            st.error(f"{get_text('transcription_error', st.session_state.language)} {str(e)}")
            return None

def send_to_discord(transcript: str, source: str = "transcription") -> bool:
    webhook_url = st.secrets.get("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        st.error(get_text('discord_webhook_error', st.session_state.language))
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
        st.error(f"{get_text('discord_send_error', st.session_state.language)} {str(e)}")
        return False

def send_chunked_messages(webhook_url: str, transcript: str) -> bool:
    try:
        chunk_size = DISCORD_MESSAGE_LIMIT - 50
        chunks = [transcript[i:i+chunk_size] for i in range(0, len(transcript), chunk_size)]
        
        for i, chunk in enumerate(chunks):
            part_text = get_text('part_prefix', st.session_state.language)
            message = f"**{part_text} {i+1}/{len(chunks)}:**\n{chunk}"
            if not send_single_message(webhook_url, message):
                return False
            time.sleep(0.5)
        
        return True
    except Exception as e:
        st.error(f"{get_text('chunked_error', st.session_state.language)} {str(e)}")
        return False

def copy_to_clipboard_component(text: str, button_text: str):
    escaped_text = text.replace('`', '\\`').replace('\\', '\\\\').replace('"', '\\"')
    copied_text = get_text('copied', st.session_state.language)
    
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
        ">{copied_text}</span>
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
            transcription = transcriber.transcribe_file(tmp_file_path, st.session_state.language)
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
            st.error(f"{get_text('processing_error', st.session_state.language)} {uploaded_file.name}: {str(e)}")
        
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
        transcription = transcriber.transcribe_file(audio_path, st.session_state.language)
        return transcription
    except Exception as e:
        st.error(f"{get_text('transcription_error', st.session_state.language)} {str(e)}")
        return None
    finally:
        try:
            os.unlink(audio_path)
        except:
            pass

def initialize_session_state():
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None
    if 'last_audio_id' not in st.session_state:
        st.session_state.last_audio_id = None
    if 'combined_transcript' not in st.session_state:
        st.session_state.combined_transcript = ""
    if 'transcribing' not in st.session_state:
        st.session_state.transcribing = False

def main():
    initialize_session_state()
    
    st.title(get_text('title', st.session_state.language))
    st.write(get_text('author', st.session_state.language))
    
    language = st.selectbox(
        get_text('language_selector', st.session_state.language),
        options=list(LANGUAGE_OPTIONS.keys()),
        format_func=lambda x: LANGUAGE_OPTIONS[x],
        index=list(LANGUAGE_OPTIONS.keys()).index(st.session_state.language)
    )
    
    if language != st.session_state.language:
        st.session_state.language = language
        st.rerun()
    
    st.write("---")
    
    st.write(get_text('description', st.session_state.language))
    
    tab1, tab2 = st.tabs([get_text('record_audio', st.session_state.language), get_text('upload_files', st.session_state.language)])
    
    with tab1:
        st.subheader(get_text('record_audio', st.session_state.language))
        
        st.write(get_text('record_instructions', st.session_state.language))
        
        status_container = st.empty()
        
        audio_data = mic_recorder(
            start_prompt=get_text('start_recording', st.session_state.language),
            stop_prompt=get_text('stop_recording', st.session_state.language),
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
                st.info(get_text('transcribing', st.session_state.language))
            
            st.audio(st.session_state.audio_data['bytes'], format="audio/wav")
            
            with st.spinner(get_text('processing', st.session_state.language)):
                transcription = transcribe_audio(st.session_state.audio_data)
                
                if transcription:
                    if st.session_state.combined_transcript:
                        st.session_state.combined_transcript += f"\n\n{transcription.strip()}"
                    else:
                        st.session_state.combined_transcript = transcription.strip()
                    
                    with status_container:
                        st.success(get_text('transcription_complete', st.session_state.language))
                else:
                    with status_container:
                        st.error(get_text('transcription_failed', st.session_state.language))
            
            st.session_state.transcribing = False
        
        if st.session_state.combined_transcript:
            st.subheader(get_text('transcript', st.session_state.language))
            
            st.text_area(
                get_text('accumulated_transcriptions', st.session_state.language),
                st.session_state.combined_transcript,
                height=300
            )
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.download_button(
                    get_text('download_transcript', st.session_state.language),
                    st.session_state.combined_transcript,
                    "transcript.txt",
                    "text/plain"
                )
            
            with col2:
                copy_to_clipboard_component(st.session_state.combined_transcript, get_text('copy_to_clipboard', st.session_state.language))
            
            with col3:
                if st.button(get_text('send_to_discord', st.session_state.language), key="discord_recording"):
                    with st.spinner(get_text('sending_to_discord', st.session_state.language)):
                        if send_to_discord(st.session_state.combined_transcript, "Microphone Recording"):
                            st.success(get_text('sent_to_discord', st.session_state.language))
                        else:
                            st.error(get_text('failed_to_send', st.session_state.language))
            
            with col4:
                if st.button(get_text('clear_transcript', st.session_state.language)):
                    st.session_state.combined_transcript = ""
                    st.rerun()
                
        with st.expander(get_text('trouble_recording', st.session_state.language)):
            st.info(get_text('trouble_info', st.session_state.language))
    
    with tab2:
        uploaded_files = st.file_uploader(
            get_text('choose_audio_files', st.session_state.language), 
            type=[fmt.replace('.', '') for fmt in SUPPORTED_FORMATS],
            accept_multiple_files=True
        )
        
        if uploaded_files:
            col1, col2 = st.columns([1, 1])
            start_button = col1.button(get_text('start_transcription', st.session_state.language), key="file_transcribe", type="primary")
            
            if start_button:
                transcriber = AudioTranscriber()
                transcriptions = process_files(transcriber, uploaded_files)
                
                if transcriptions:
                    combined_text = "\n\n".join(f"{text}" for fname, text in transcriptions.items())
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.download_button(
                            get_text('download_all', st.session_state.language),
                            combined_text,
                            "combined_transcriptions.txt",
                            "text/plain"
                        )
                    
                    with col2:
                        copy_to_clipboard_component(combined_text, get_text('copy_to_clipboard', st.session_state.language))
                    
                    with col3:
                        if st.button(get_text('send_to_discord', st.session_state.language), key="discord_files"):
                            with st.spinner(get_text('sending_to_discord', st.session_state.language)):
                                if send_to_discord(combined_text, "File Upload"):
                                    st.success(get_text('sent_to_discord', st.session_state.language))
                                else:
                                    st.error(get_text('failed_to_send', st.session_state.language))

if __name__ == "__main__":
    main()