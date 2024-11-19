import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
import datetime
import sqlite3
from plyer import notification
import pyttsx3
import speech_recognition as sr
from dateparser import parse as parse_date


class PersonalAssistantAgent:
    def __init__(self):
        # Set up SQLite database
        self.conn = sqlite3.connect("assistant_data.db")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                name TEXT,
                deadline TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY,
                time TEXT
            )
        """)
        self.conn.commit()

    def schedule_meeting(self, time):
        # Check for conflicts with existing meetings
        cursor = self.conn.cursor()
        cursor.execute("SELECT time FROM meetings")
        existing_meetings = cursor.fetchall()
        for meeting in existing_meetings:
            if self.time_conflicts(time, meeting[0]):
                alternative_times = self.suggest_alternative_times(time)
                return f"Meeting conflicts with an existing meeting. Suggesting alternative times: {', '.join(alternative_times)}"
        cursor.execute("INSERT INTO meetings (time) VALUES (?)", (time,))
        self.conn.commit()
        return f"Meeting scheduled at {time}"

    def schedule_task(self, task_name, deadline):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO tasks (name, deadline) VALUES (?, ?)", (task_name, deadline))
        self.conn.commit()
        return f"Task '{task_name}' scheduled with deadline {deadline}"

    def send_reminder(self):
        current_time = datetime.datetime.now()
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, deadline FROM tasks")
        tasks = cursor.fetchall()
        reminders_sent = []
        for task in tasks:
            deadline = datetime.datetime.strptime(task[1], '%Y-%m-%d %H:%M:%S')
            if deadline - current_time <= datetime.timedelta(hours=24):  # If deadline is within 24 hours
                reminder_message = f"Reminder: '{task[0]}' deadline is approaching at {task[1]}"
                reminders_sent.append(reminder_message)
                # Show notification
                notification.notify(
                    title="Task Reminder",
                    message=reminder_message,
                    timeout=10
                )
        return reminders_sent if reminders_sent else "No reminders for today."

    def suggest_alternative_times(self, time):
        # List potential alternative times (30 min intervals) up to 5 alternatives
        base_time = datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        alternative_times = []
        for i in range(1, 6):
            new_time = (base_time + datetime.timedelta(minutes=30 * i)).strftime('%Y-%m-%d %H:%M:%S')
            if not self.is_time_taken(new_time):
                alternative_times.append(new_time)
        return alternative_times

    def time_conflicts(self, time1, time2):
        return time1 == time2

    def is_time_taken(self, time):
        cursor = self.conn.cursor()
        cursor.execute("SELECT time FROM meetings WHERE time = ?", (time,))
        result = cursor.fetchone()
        return result is not None

    def check_free_time(self, time):
        cursor = self.conn.cursor()
        cursor.execute("SELECT time FROM meetings")
        existing_meetings = cursor.fetchall()
        for meeting in existing_meetings:
            if self.time_conflicts(time, meeting[0]):
                return "No free time available at this time."
        
        # Suggest a break or task completion if free time is available
        task_cursor = self.conn.cursor()
        task_cursor.execute("SELECT name, deadline FROM tasks ORDER BY deadline LIMIT 1")  # Get the nearest task
        task = task_cursor.fetchone()
        if task:
            task_name = task[0]
            task_deadline = task[1]
            return f"The time is free. You could use this time to complete your task: '{task_name}' with deadline at {task_deadline}."
        else:
            return "The time is free. How about taking a break?"

    def interact(self, command):
        if "schedule meeting" in command:
            time = parse_date(command.split("at")[1].strip())
            return self.schedule_meeting(time.strftime('%Y-%m-%d %H:%M:%S'))

        elif "schedule task" in command:
            parts = command.split("to")
            task_name = parts[1].strip().split("by")[0].strip()
            deadline = parse_date(parts[1].strip().split("by")[1].strip())
            return self.schedule_task(task_name, deadline.strftime('%Y-%m-%d %H:%M:%S'))

        elif "send reminders" in command:
            return self.send_reminder()

        elif "check free time" in command:
            time = parse_date(command.split("at")[1].strip())
            return self.check_free_time(time.strftime('%Y-%m-%d %H:%M:%S'))

        else:
            return "Unknown command."


class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Assistant Agent")
        self.root.geometry("500x500")

        # Set up the agent
        self.agent = PersonalAssistantAgent()

        # Voice assistant setup
        self.recognizer = sr.Recognizer()
        self.speaker = pyttsx3.init()

        # GUI components
        self.instruction_label = tk.Label(root, text="Enter Command Below or Use Voice Input:", font=("Arial", 12))
        self.instruction_label.pack(pady=10)

        self.command_entry = tk.Entry(root, width=50, font=("Arial", 14))
        self.command_entry.pack(pady=10)

        self.submit_button = tk.Button(root, text="Submit Command", width=20, height=2, font=("Arial", 12),
                                       command=self.process_command)
        self.submit_button.pack(pady=10)

        self.response_text = tk.Text(root, height=10, width=60, font=("Arial", 12))
        self.response_text.pack(pady=10)

        self.calendar = Calendar(root, selectmode='day', date_pattern='y-mm-dd')
        self.calendar.pack(pady=10)

        self.voice_button = tk.Button(root, text="Use Voice Command", width=20, height=2, font=("Arial", 12),
                                      command=self.process_voice_command)
        self.voice_button.pack(pady=10)

    def process_command(self):
        user_input = self.command_entry.get()
        print(f"User input: {user_input}")  # Debugging output
        try:
            if hasattr(self.agent, 'interact'):
                print("Agent has interact method")  # Debugging output
                response = self.agent.interact(user_input)
            else:
                print("Agent doesn't have interact method")  # Debugging output
                response = "Method not found"
        except Exception as e:
            response = f"Error: {str(e)}"
        self.command_entry.delete(0, tk.END)
        self.response_text.delete(1.0, tk.END)
        self.response_text.insert(tk.END, response)

    def process_voice_command(self):
        try:
            with sr.Microphone() as source:
                self.speaker.say("Listening for your command...")
                self.speaker.runAndWait()
                audio = self.recognizer.listen(source)
                command = self.recognizer.recognize_google(audio)
                print(f"Voice command received: {command}")  # Debugging output
                response = self.agent.interact(command)
                self.response_text.delete(1.0, tk.END)
                self.response_text.insert(tk.END, response)
        except Exception as e:
            self.response_text.delete(1.0, tk.END)
            self.response_text.insert(tk.END, f"Error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AssistantGUI(root)
    root.mainloop()
