import tkinter as tk
from tkinter import scrolledtext
import sqlite3
import logging
import threading
import speech_recognition as sr
import pyttsx3
from datetime import datetime
from weather import get_weather
from reminders import set_reminder, check_reminders
import google.generativeai as genai  # Import Google Gemini API

# Initialize logging
logging.basicConfig(filename='assistant.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Initialize SQLite database for history
def init_db():
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS history
                      (id INTEGER PRIMARY KEY, command TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

# Log user commands to the database
def log_command(command):
    conn = sqlite3.connect('history.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO history (command, timestamp) VALUES (?, ?)",
                   (command, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

# Function to answer simple questions using Google Gemini API
def answer_question(question):
    try:
        # Initialize Google Gemini API
        genai.configure(api_key="AIzaSyCPDfg9TUbVqPLd5fFoK_S6iKFXkViINgo")  # Replace with your openai API key
        model = genai.GenerativeModel('gemini-pro')  # Use the model

        # Generate a response
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        return f"I'm sorry, I couldn't process your question. Error: {str(e)}"

# GUI Application
class VirtualAssistantApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Virtual Assistant")
        self.root.geometry("500x400")

        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)  # Speed of speech
        self.engine.setProperty('volume', 1.0)  # Volume level (0.0 to 1.0)

        # Text area for output
        self.output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=20, state='disabled')
        self.output_area.pack(pady=10)

        # Initialize database
        init_db()

        # Greet the user
        self.greet_user()

        # Start voice command listener in a separate thread
        self.listening = True
        self.voice_thread = threading.Thread(target=self.voice_command_listener, daemon=True)
        self.voice_thread.start()

    # Greet the user
    def greet_user(self):
        greeting = (
            "Hello! I am Orion. I am your virtual assistant. "
        )
        self.display_output(greeting)

        self.speak(greeting)
        task_info = "You can ask me about the weather, set reminders, ask questions, or view command history."
        self.display_output(task_info)

    # Process user command
    def process_command(self, command=None):
        if command in ( "weather" , "weather info" , "weather forecast" , "current weather" , "weather report"): 
            self.speak("Please say the city name.")
            city = self.get_voice_input()
            if city:
                weather_info = get_weather(city, "102a3b2fefa5a1c133384ff65a49ab04")  # Replace with API key
                self.display_output(weather_info)
                self.speak(weather_info)
                log_command(f"Weather query for {city}: {weather_info}")

        elif command in ( "reminder", "set reminder" , "remind me"):
            self.speak("Please say the reminder text.")
            text = self.get_voice_input()
            if text:
                self.speak("Please say the reminder time in YYYY-MM-DD HH:MM:SS format.")
                time_str = self.get_voice_input()
                if time_str:
                    try:
                        reminder_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        reminder_confirmation = set_reminder(text, reminder_time)
                        self.display_output(reminder_confirmation)
                        self.speak(reminder_confirmation)
                        log_command(f"Reminder set: {text} at {time_str}")
                    except ValueError:
                        error_message = "Invalid date format. Please use YYYY-MM-DD HH:MM:SS."
                        self.display_output(error_message)
                        self.speak(error_message)

        elif command in ( "question" , "ask" , "ask question") :
            self.speak("Ask me something.")
            question = self.get_voice_input()
            if question:
                answer = answer_question(question)  # Use Google Gemini API to answer
                self.display_output(answer)
                self.speak(answer)
                log_command(f"Question: {question} - Answer: {answer}")

        elif command in ("history", "command history", "view history"):
            conn = sqlite3.connect('history.db')
            cursor = conn.cursor()
            cursor.execute("SELECT command, timestamp FROM history ORDER BY timestamp DESC")
            records = cursor.fetchall()
            conn.close()
            if records:
                self.display_output("\nCommand History:")
                self.speak("Here is your command history.")
                for record in records:
                    history_entry = f"{record[1]} - {record[0]}"
                    self.display_output(history_entry)
                    self.speak(history_entry)
            else:
                self.display_output("No history found.")
                self.speak("No history found.")

        elif command == "exit":
            self.display_output("Goodbye!")
            self.speak("Goodbye!")
            self.root.quit()

        else:
            error_message = "Invalid command. Please try again."
            self.display_output(error_message)
            self.speak(error_message)

        # Check for due reminders
        check_reminders()

    # Display output in the text area
    def display_output(self, message):
        self.output_area.config(state='normal')
        self.output_area.insert(tk.END, message + "\n")
        self.output_area.config(state='disabled')
        self.output_area.yview(tk.END)

        #log to file
        logging.info(message)   

    # Speak text using text-to-speech
    def speak(self, text):
        self.engine.say(text)
        self.engine.runAndWait()

    # Get voice input
    def get_voice_input(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                self.display_output("Listening...")
                # self.speak("Listening...")
                audio = recognizer.listen(source, timeout=5)  # Listen for 5 seconds
                text = recognizer.recognize_google(audio).lower()
                self.display_output(f"You said: {text}")
                return text
            except sr.UnknownValueError:
                self.display_output("Sorry, I did not understand that.")
                self.speak("Sorry, I did not understand that.")
            except sr.RequestError:
                self.display_output("Sorry, my speech service is down.")
                self.speak("Sorry, my speech service is down.")
            except sr.WaitTimeoutError:
                self.display_output("No speech detected.")
                self.speak("No speech detected.")
        return None

    # Voice command listener
    def voice_command_listener(self):
        recognizer = sr.Recognizer()
        while self.listening:
            with sr.Microphone() as source:
                try:
                    self.display_output("Listening for a command...")
                    # self.speak("Listening for a command...")
                    audio = recognizer.listen(source, timeout=3)  # Listen for 3 seconds
                    command = recognizer.recognize_google(audio).lower()
                    self.display_output(f"Voice command: {command}")
                    self.process_command(command)
                except sr.UnknownValueError:
                    self.display_output("Sorry, I did not understand that.")
                    self.speak("Sorry, I did not understand that.")
                except sr.RequestError:
                    self.display_output("Sorry, my speech service is down.")
                    self.speak("Sorry, my speech service is down.")
                except sr.WaitTimeoutError:
                    continue  # Continue listening if no speech is detected

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = VirtualAssistantApp(root)
    root.mainloop()