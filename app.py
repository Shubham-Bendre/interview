import streamlit as st
import google.generativeai as genai
import speech_recognition as sr
import pyttsx3
import threading
import queue
import PyPDF2
import io
import os

# Configure Gemini API (Replace with your actual API key)
genai.configure(api_key="YOUR_GEMINI_API_KEY")

class VoiceResumeInterviewApp:
    def __init__(self):
        # Initialize speech recognition and text-to-speech
        self.recognizer = sr.Recognizer()
        self.tts_engine = pyttsx3.init()
        
        # Configure TTS properties
        self.tts_engine.setProperty('rate', 150)  # Speaking rate
        
        # Streamlit page configuration
        st.set_page_config(page_title="Voice Resume Interview", page_icon="🎙️")
        
        # Gemini model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # Queue for thread-safe audio processing
        self.audio_queue = queue.Queue()
        
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from uploaded PDF resume"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
            return None

    def speech_to_text(self):
        """Capture audio input and convert to text"""
        with sr.Microphone() as source:
            st.info("Listening... Speak now.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = self.recognizer.listen(source)
            
        try:
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            st.warning("Sorry, could not understand audio.")
            return None
        except sr.RequestError:
            st.error("Could not request results from speech recognition service.")
            return None

    def text_to_speech(self, text):
        """Convert text to speech"""
        try:
            # Temporarily save audio to a file
            self.tts_engine.save_to_file(text, 'response.mp3')
            self.tts_engine.runAndWait()
            
            # Play the audio file
            st.audio('response.mp3', format='audio/mp3')
        except Exception as e:
            st.error(f"Text-to-speech error: {e}")

    def parse_resume(self, resume_text):
        """Parse resume to extract key skills and projects"""
        try:
            prompt = f"""
            From the following resume text, extract:
            1. Professional Skills
            2. Technical Skills
            3. Projects
            4. Primary Domains/Expertise

            Resume Text:
            {resume_text}
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error parsing resume: {e}")
            return None

    def generate_voice_interview_questions(self, skills_and_projects):
        """Generate tailored voice interview questions"""
        try:
            prompt = f"""
            Based on the following skills and projects, generate a set of technical interview 
            questions that will be asked verbally to validate the candidate's actual knowledge:

            Skills and Projects:
            {skills_and_projects}

            Generate:
            - 5-7 in-depth technical questions
            - Questions should be conversational and voice-friendly
            - Include context and background for each question
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error generating interview questions: {e}")
            return None

    def evaluate_voice_answer(self, question, candidate_answer, context):
        """Evaluate candidate's voice answer using Gemini"""
        try:
            prompt = f"""
            Voice Interview Scenario:
            Question: {question}
            Candidate's Verbal Answer: {candidate_answer}
            Context from Resume: {context}

            Evaluation Criteria:
            1. Technical Depth
            2. Clarity of Communication
            3. Alignment with Claimed Skills
            4. Confidence and Articulation

            Provide a detailed evaluation with:
            - Rating (0-10)
            - Strengths in Verbal Response
            - Areas Needing Improvement
            - Recommendation for Skill Enhancement
            """
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error evaluating voice answer: {e}")
            return None

    def run_voice_interview(self):
        """Main Streamlit Voice Interview Interface"""
        st.title("🎙️ Voice-Powered Resume Interview")
        
        # Resume Upload
        st.sidebar.header("Upload Resume")
        resume_file = st.sidebar.file_uploader("Choose PDF Resume", type=['pdf'])
        
        if resume_file is not None:
            # Extract Resume Text
            resume_text = self.extract_text_from_pdf(resume_file)
            
            if resume_text:
                # Parse Resume
                parsed_resume = self.parse_resume(resume_text)
                st.sidebar.success("Resume Parsed Successfully!")
                
                # Generate Voice Interview Questions
                voice_questions = self.generate_voice_interview_questions(parsed_resume)
                
                # Initialize Session State
                if 'current_question_index' not in st.session_state:
                    st.session_state.current_question_index = 0
                    st.session_state.questions = voice_questions.split('\n')
                    st.session_state.voice_answers = []
                    st.session_state.evaluations = []
                
                # Current Question
                current_question = st.session_state.questions[st.session_state.current_question_index]
                
                # Display and Speak Current Question
                st.write(f"**Question {st.session_state.current_question_index + 1}:**")
                self.text_to_speech(current_question)
                st.write(current_question)
                
                # Voice Answer Capture
                if st.button("Speak My Answer"):
                    # Capture Voice Answer
                    voice_answer = self.speech_to_text()
                    
                    if voice_answer:
                        # Display Transcribed Answer
                        st.write("**Your Answer:**", voice_answer)
                        
                        # Evaluate Answer
                        evaluation = self.evaluate_voice_answer(
                            current_question, 
                            voice_answer, 
                            parsed_resume
                        )
                        
                        # Store Voice Answer and Evaluation
                        st.session_state.voice_answers.append(voice_answer)
                        st.session_state.evaluations.append(evaluation)
                        
                        # Speak and Display Evaluation
                        st.markdown("### Answer Evaluation")
                        self.text_to_speech(evaluation)
                        st.write(evaluation)
                        
                        # Move to Next Question
                        if st.session_state.current_question_index < len(st.session_state.questions) - 1:
                            st.session_state.current_question_index += 1
                            st.experimental_rerun()
                        else:
                            st.success("Voice Interview Completed! 🎉")

def main():
    interview_app = VoiceResumeInterviewApp()
    interview_app.run_voice_interview()

if __name__ == "__main__":
    main()
