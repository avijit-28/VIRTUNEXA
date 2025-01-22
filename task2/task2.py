import speech_recognition as sr
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import logging
from datetime import datetime
import re
import time

class SpeechCalculator:
    def __init__(self):
        self.setup_logging()
        self.setup_database()
        self.setup_gui()
        self.setup_recognizer()
        
    def setup_recognizer(self):
        self.recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.recognizer.energy_threshold = 4000
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 1
        except Exception as e:
            logging.error(f"Microphone setup error: {str(e)}")
            messagebox.showerror("Error", "Microphone not found")

    def setup_logging(self):
        logging.basicConfig(
            filename='calculator.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

    def setup_database(self):
        self.conn = sqlite3.connect('calculator.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS calculations
            (timestamp TEXT, operation TEXT, result TEXT)
        ''')
        self.conn.commit()

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("Speech Calculator")
        
        self.display = ttk.Entry(self.root, width=40)
        self.display.grid(row=0, column=0, columnspan=4, padx=5, pady=5)
        
        self.speech_frame = ttk.Frame(self.root)
        self.speech_frame.grid(row=0, column=4, padx=5, pady=5)
        
        self.speech_btn = ttk.Button(self.speech_frame, text="🎤", command=self.listen)
        self.speech_btn.pack()
        
        self.status_label = ttk.Label(self.speech_frame, text="Ready")
        self.status_label.pack()
        
        # Clear button
        ttk.Button(self.root, text="Clear", command=self.clear).grid(row=1, column=4, padx=2, pady=2)
        
        # Backspace button
        ttk.Button(self.root, text="⌫", command=self.delete_last).grid(row=2, column=4, padx=2, pady=2)
        
        #exit button
        ttk.Button(self.root, text="Exit", command=self.exit_app, style='Accent.TButton').grid(row=3, column=4, padx=2, pady=2)

        buttons = [
            '7', '8', '9', '/',
            '4', '5', '6', '*',
            '1', '2', '3', '-',
            '0', '.', '=', '+'
        ]
        
        row = 1
        col = 0
        for button in buttons:
            cmd = lambda x=button: self.click(x)
            ttk.Button(self.root, text=button, command=cmd).grid(
                row=row, column=col, padx=2, pady=2
            )
            col += 1
            if col > 3:
                col = 0
                row += 1

    def clear(self):
        self.display.delete(0, tk.END)

    def update_status(self, text, duration=None):
        self.status_label.config(text=text)
        print(f"Status: {text}")  # Terminal status
        if duration:
            self.root.after(duration, lambda: self.status_label.config(text="Ready"))
    def exit_app(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.conn.close()
            self.root.quit()
            self.root.destroy()

    def delete_last(self):
        current = self.display.get()
        if current:
            self.display.delete(len(current)-1, tk.END)

    def listen(self):
        try:
            with sr.Microphone() as source:
                self.update_status("Listening...")
                self.display.delete(0, tk.END)
                self.display.insert(0, "Listening...")
                
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Starting to listen...")
                
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    self.update_status("Processing...")
                    print("Processing speech...")
                    
                    text = self.recognizer.recognize_google(audio)
                    print(f"Recognized: {text}")
                    
                    text = self.convert_speech_to_expression(text)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, text)
                    
                    # Automatically calculate after recognition
                    self.root.after(1000, self.calculate)  # Calculate after 1 second
                    
                    self.update_status("Success!", 2000)
                    
                except sr.WaitTimeoutError:
                    self.update_status("No speech detected", 2000)
                    self.display.delete(0, tk.END)
                except sr.UnknownValueError:
                    self.update_status("Could not understand audio", 2000)
                    self.display.delete(0, tk.END)
                    
        except Exception as e:
            logging.error(f"Speech recognition error: {str(e)}")
            self.update_status("Microphone error", 2000)
            self.display.delete(0, tk.END)
            messagebox.showerror("Error", f"Speech recognition error: {str(e)}")

    def convert_speech_to_expression(self, text):
        text = text.lower()
        
        replacements = {
            'plus': '+',
            'add': '+',
            'minus': '-',
            'subtract': '-',
            'times': '*',
            'multiplied by': '*',
            'multiply': '*',
            'divided by': '/',
            'divide': '/',
            'equals': '=',
            'equal': '=',
            'point': '.',
            'zero': '0',
            'one': '1',
            'two': '2',
            'three': '3',
            'four': '4',
            'five': '5',
            'six': '6',
            'seven': '7',
            'eight': '8',
            'nine': '9'
        }
        
        for word, replacement in replacements.items():
            text = text.replace(word, replacement)
        
        text = re.sub(r'[^0-9+\-*/=\.]', '', text)
        return text

    def click(self, key):
        if key == '=':
            self.calculate()
        else:
            current = self.display.get()
            self.display.delete(0, tk.END)
            self.display.insert(0, current + key)

    def calculate(self):
        try:
            expression = self.display.get().replace('=', '')
            
            # Check for division by zero
            if '/0' in expression:
                messagebox.showerror("Error", "Division by zero!")
                self.display.delete(0, tk.END)
                self.display.insert(0, "ERROR")
                return
                
            result = eval(expression)
            
            logging.info(f"Calculation: {expression} = {result}")
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute(
                "INSERT INTO calculations VALUES (?, ?, ?)",
                (timestamp, expression, str(result))
            )
            self.conn.commit()
            
            self.display.delete(0, tk.END)
            self.display.insert(0, str(result))
            
        except Exception as e:
            self.display.delete(0, tk.END)
            self.display.insert(0, "Error")
            logging.error(f"Calculation error: {str(e)}")
            messagebox.showerror("Error", f"Invalid calculation: {str(e)}")

    def run(self):
        self.root.mainloop()

    def __del__(self):
        self.conn.close()

if __name__ == "__main__":
    calculator = SpeechCalculator()
    calculator.run()