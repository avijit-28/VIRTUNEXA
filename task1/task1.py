import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import csv
import os
import sqlite3
import logging

class GradeCalculatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Grade Calculator")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # CSV file path
        self.csv_file = "export.csv"
        
        # Style configuration
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Arial", 16, "bold"))
        style.configure("Header.TLabel", font=("Arial", 12, "bold"))
        
        # Variables for entry fields
        self.student_name = tk.StringVar()
        self.subject_marks = {
            "English": tk.StringVar(),
            "Mathematics": tk.StringVar(),
            "Science": tk.StringVar(),
            "Hindi": tk.StringVar(),
            "SST": tk.StringVar()
        }
        
        self.create_widgets()
        self.ensure_csv_exists()
        
    def ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            headers = ['Student Name', 'English', 'Mathematics', 'Science', 
                      'Hindi', 'SST', 'Total Marks', 'Average Marks', 'Final Grade']
            with open(self.csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(headers)
        
    def create_widgets(self):
        # Title
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill="x")
        ttk.Label(title_frame, text="Student Grade Calculator", style="Title.TLabel").pack()
        
        # Student Information
        info_frame = ttk.LabelFrame(self.root, text="Student Information", padding="10")
        info_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(info_frame, text="Student Name:").grid(row=0, column=0, padx=5, pady=5)
        ttk.Entry(info_frame, textvariable=self.student_name).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Marks Entry
        marks_frame = ttk.LabelFrame(self.root, text="Subject Marks", padding="10")
        marks_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(marks_frame, text="Enter marks for each subject (0-100):", style="Header.TLabel").grid(row=0, column=0, columnspan=2, pady=5)
        
        row_num = 1
        for subject, var in self.subject_marks.items():
            ttk.Label(marks_frame, text=f"{subject}:").grid(row=row_num, column=0, padx=5, pady=5, sticky="e")
            ttk.Entry(marks_frame, textvariable=var).grid(row=row_num, column=1, padx=5, pady=5, sticky="ew")
            row_num += 1
        
        # Buttons
        button_frame = ttk.Frame(self.root, padding="10")
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(button_frame, text="Calculate Grades", command=self.calculate_grades).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side="left", padx=5)
        
        # Result Display
        self.result_frame = ttk.LabelFrame(self.root, text="Results", padding="10")
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(self.result_frame, height=15, width=50)
        self.result_text.pack(fill="both", expand=True)
        self.result_text.config(state="disabled")
        
    def calculate_grade(self, marks):
        if marks >= 90:
            return 'A+'
        elif marks >= 80:
            return 'A'
        elif marks >= 70:
            return 'B'
        elif marks >= 60:
            return 'C'
        elif marks >= 50:
            return 'D'
        else:
            return 'F'
    
    def calculate_grades(self):
        # Validate student name
        name = self.student_name.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter student name!")
            return
        
        try:
            # Convert and validate marks
            marks_dict = {}
            for subject, var in self.subject_marks.items():
                marks = float(var.get())
                if not (0 <= marks <= 100):
                    raise ValueError(f"Marks for {subject} must be between 0 and 100")
                marks_dict[subject] = marks
            
            # Calculate statistics
            total_marks = sum(marks_dict.values())
            average_marks = total_marks / len(marks_dict)
            final_grade = self.calculate_grade(average_marks)
            
            # Log calculation
            log_calculation(name, marks_dict, total_marks, average_marks, final_grade)
            log_grade_to_db(name, marks_dict, total_marks, average_marks, final_grade)
            
            # Prepare data for CSV
            csv_data = [
                name,
                marks_dict['English'],
                marks_dict['Mathematics'],
                marks_dict['Science'],
                marks_dict['Hindi'],
                marks_dict['SST'],
                total_marks,
                average_marks,
                final_grade
            ]
            
            # Append to CSV file
            with open(self.csv_file, 'a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(csv_data)
            
            # Generate display report
            report = f"Grade Report for {name}\n"
            report += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report += "=" * 50 + "\n\n"
            
            # Subject-wise details
            report += "Subject-wise Details:\n"
            report += "-" * 50 + "\n"
            report += f"{'Subject':<15} {'Marks':<10} {'Grade':<10}\n"
            report += "-" * 50 + "\n"
            
            for subject, marks in marks_dict.items():
                grade = self.calculate_grade(marks)
                report += f"{subject:<15} {marks:<10.2f} {grade:<10}\n"
            
            # Summary
            report += "-" * 50 + "\n"
            report += f"{'Total Marks:':<15} {total_marks:<10.2f}\n"
            report += f"{'Average:':<15} {average_marks:<10.2f}\n"
            report += f"{'Final Grade:':<15} {final_grade}\n"
            report += "=" * 50 + "\n"
            report += "\nResults have been saved to export.csv"
            
            # Display report
            self.result_text.config(state="normal")
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, report)
            self.result_text.config(state="disabled")
            
            messagebox.showinfo("Success", "Grades calculated and saved to export.csv")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def clear_fields(self):
        self.student_name.set("")
        for var in self.subject_marks.values():
            var.set("")
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.config(state="disabled")

# SQLite Functions

def create_db():
    """Creates a SQLite database to store the operation history."""
    conn = sqlite3.connect("grade_calculator_history.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grade_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            subject_marks TEXT,
            total_marks REAL,
            average_marks REAL,
            final_grade TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_grade_to_db(student_name, marks_dict, total_marks, average_marks, final_grade):
    """Logs grade calculation results to SQLite database."""
    conn = sqlite3.connect("grade_calculator_history.db")
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO grade_history (student_name, subject_marks, total_marks, average_marks, final_grade, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_name, str(marks_dict), total_marks, average_marks, final_grade, timestamp))
    
    conn.commit()
    conn.close()

# Logging Functions

logging.basicConfig(filename="grade_calculator.log", level=logging.INFO, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

def log_calculation(student_name, marks_dict, total_marks, average_marks, final_grade):
    """Logs a grade calculation."""
    logging.info(f"Student: {student_name}, Marks: {marks_dict}, Total: {total_marks}, Average: {average_marks}, Grade: {final_grade}")

# Console Interface

def console_interface():
    """Console-based grade calculator interface."""
    print("Welcome to the Grade Calculator!")
    
    student_name = input("Enter the student's name: ").strip()
    if not student_name:
        print("Error: Please enter a valid student name.")
        return
    
    marks_dict = {}
    subjects = ["English", "Mathematics", "Science", "Hindi", "SST"]
    
    for subject in subjects:
        while True:
            try:
                marks = float(input(f"Enter marks for {subject} (0-100): ").strip())
                if 0 <= marks <= 100:
                    marks_dict[subject] = marks
                    break
                else:
                    print(f"Error: Marks for {subject} must be between 0 and 100.")
            except ValueError:
                print(f"Error: Please enter a valid number for {subject}.")
    
    # Calculate total, average, and grade
    total_marks = sum(marks_dict.values())
    average_marks = total_marks / len(marks_dict)
    
    def calculate_grade(marks):
        if marks >= 90:
            return 'A+'
        elif marks >= 80:
            return 'A'
        elif marks >= 70:
            return 'B'
        elif marks >= 60:
            return 'C'
        elif marks >= 50:
            return 'D'
        else:
            return 'F'
    
    final_grade = calculate_grade(average_marks)
    
    # Log calculation
    log_calculation(student_name, marks_dict, total_marks, average_marks, final_grade)
    log_grade_to_db(student_name, marks_dict, total_marks, average_marks, final_grade)
    
    # Display results
    print("\nGrade Report:")
    print("="*50)
    print(f"Student: {student_name}")
    print(f"Total Marks: {total_marks}")
    print(f"Average Marks: {average_marks:.2f}")
    print(f"Final Grade: {final_grade}")
    print("="*50)
    
    # Optionally, save results to CSV
    csv_data = [student_name, marks_dict['English'], marks_dict['Mathematics'], marks_dict['Science'],
                marks_dict['Hindi'], marks_dict['SST'], total_marks, average_marks, final_grade]
    with open("export.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(csv_data)
    
    print("Results have been saved to export.csv.")

def main():
    create_db()  # Initialize SQLite database
    choice = input("Choose interface (1 - Console, 2 - GUI): ").strip()
    if choice == '1':
        console_interface()
    elif choice == '2':
        root = tk.Tk()
        app = GradeCalculatorGUI(root)
        root.mainloop()
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()
