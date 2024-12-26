import tkinter as tk
from tkinter import messagebox, simpledialog
from tkcalendar import Calendar
import datetime
import sqlite3
import pyttsx3
import time

class PersonalAssistantAgent:
    def __init__(self):
        # Set up SQLite database
        self.conn = sqlite3.connect("assistant_data.db")
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Drop the meetings table if it exists
        cursor.execute("DROP TABLE IF EXISTS meetings")

        # Create tasks table with a column to track completion status
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                name TEXT,
                deadline TEXT,
                completed BOOLEAN
            )
        """)

        # Create meetings table with 'description' and 'completed' columns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY,
                time TEXT,
                description TEXT,
                completed BOOLEAN
            )
        """)

        self.conn.commit()

    def schedule_task(self, task_name, deadline):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO tasks (name, deadline, completed) VALUES (?, ?, ?)", (task_name, deadline, False))
        self.conn.commit()

    def delete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def update_task(self, task_id, new_name, new_deadline):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET name = ?, deadline = ? WHERE id = ?", (new_name, new_deadline, task_id))
        self.conn.commit()

    def complete_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET completed = ? WHERE id = ?", (True, task_id))
        self.conn.commit()

    def get_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, deadline, completed FROM tasks")
        return cursor.fetchall()

    def schedule_meeting(self, meeting_time, description):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO meetings (time, description, completed) VALUES (?, ?, ?)", (meeting_time, description, False))
        self.conn.commit()

    def delete_meeting(self, meeting_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        self.conn.commit()

    def update_meeting(self, meeting_id, new_time, new_description):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE meetings SET time = ?, description = ? WHERE id = ?", (new_time, new_description, meeting_id))
        self.conn.commit()

    def complete_meeting(self, meeting_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE meetings SET completed = ? WHERE id = ?", (True, meeting_id))
        self.conn.commit()

    def get_meetings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, time, description, completed FROM meetings")
        return cursor.fetchall()

    def check_for_upcoming_tasks(self):
        now = datetime.datetime.now()
        reminder_messages = []
        tasks = self.get_tasks()
        for task in tasks:
            if not task[3]:  # Only remind for incomplete tasks
                task_deadline = datetime.datetime.strptime(task[2], '%Y-%m-%d %H:%M:%S')
                if 0 < (task_deadline - now).total_seconds() <= 3600:  # Reminder for tasks 1 hour before the deadline
                    reminder_messages.append(f"Task '{task[1]}' is approaching its deadline at {task[2]}.")
        return reminder_messages

    def check_for_upcoming_meetings(self):
        now = datetime.datetime.now()
        reminder_messages = []
        meetings = self.get_meetings()
        for meeting in meetings:
            if not meeting[3]:  # Only remind for incomplete meetings
                meeting_time = datetime.datetime.strptime(meeting[1], '%Y-%m-%d %H:%M:%S')
                if 0 < (meeting_time - now).total_seconds() <= 1800:  # Reminder for meetings 30 minutes before the time
                    reminder_messages.append(f"Meeting '{meeting[2]}' is scheduled to begin at {meeting[1]}.")
        return reminder_messages

class AssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Assistant Agent")
        self.root.geometry("600x600")

        # Set up the agent
        self.agent = PersonalAssistantAgent()

        # Voice assistant setup
        self.speaker = pyttsx3.init()

        # GUI components
        self.instruction_label = tk.Label(root, text="Personal Assistant Agent", font=("Arial", 16))
        self.instruction_label.grid(row=0, column=0, columnspan=3, pady=10)

        # Task List Section
        self.task_list_label = tk.Label(root, text="Tasks", font=("Arial", 14))
        self.task_list_label.grid(row=1, column=0, columnspan=3, pady=10)

        self.task_list = tk.Listbox(root, height=10, width=70, font=("Arial", 12))
        self.task_list.grid(row=2, column=0, columnspan=3, pady=10)
        self.populate_task_list()

        # Buttons: Horizontally arranged using grid
        self.add_task_button = tk.Button(root, text="Add Task", command=self.add_task)
        self.add_task_button.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        self.update_task_button = tk.Button(root, text="Update Task", command=self.update_task)
        self.update_task_button.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.delete_task_button = tk.Button(root, text="Delete Task", command=self.delete_task)
        self.delete_task_button.grid(row=3, column=2, padx=5, pady=5, sticky="ew")

        self.complete_task_button = tk.Button(root, text="Complete Task", command=self.complete_task)
        self.complete_task_button.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Meeting List Section
        self.meeting_list_label = tk.Label(root, text="Meetings", font=("Arial", 14))
        self.meeting_list_label.grid(row=5, column=0, columnspan=3, pady=10)

        self.meeting_list = tk.Listbox(root, height=10, width=70, font=("Arial", 12))
        self.meeting_list.grid(row=6, column=0, columnspan=3, pady=10)
        self.populate_meeting_list()

        # Buttons for meetings
        self.add_meeting_button = tk.Button(root, text="Add Meeting", command=self.add_meeting)
        self.add_meeting_button.grid(row=7, column=0, padx=5, pady=5, sticky="ew")

        self.update_meeting_button = tk.Button(root, text="Update Meeting", command=self.update_meeting)
        self.update_meeting_button.grid(row=7, column=1, padx=5, pady=5, sticky="ew")

        self.delete_meeting_button = tk.Button(root, text="Delete Meeting", command=self.delete_meeting)
        self.delete_meeting_button.grid(row=7, column=2, padx=5, pady=5, sticky="ew")

        self.complete_meeting_button = tk.Button(root, text="Complete Meeting", command=self.complete_meeting)
        self.complete_meeting_button.grid(row=8, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Reminder Button
        self.reminder_button = tk.Button(root, text="Send Reminders", command=self.send_reminder)
        self.reminder_button.grid(row=9, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

        # Periodically check for upcoming tasks and meetings
        self.check_for_upcoming_events()


    def populate_task_list(self):
        self.task_list.delete(0, tk.END)  # Clear current list
        tasks = self.agent.get_tasks()
        for task in tasks:
            status = "Completed" if task[3] else "Pending"
            self.task_list.insert(tk.END, f"{task[0]}: {task[1]} - {task[2]} - {status}")

    def populate_meeting_list(self):
        self.meeting_list.delete(0, tk.END)  # Clear current list
        meetings = self.agent.get_meetings()
        for meeting in meetings:
            status = "Completed" if meeting[3] else "Pending"
            self.meeting_list.insert(tk.END, f"{meeting[0]}: {meeting[1]} - {meeting[2]} - {status}")

    def add_task(self):
        task_name = simpledialog.askstring("Add Task", "Enter task name:")
        if task_name:
            deadline = simpledialog.askstring("Add Task", "Enter deadline (YYYY-MM-DD HH:MM:SS):")
            try:
                parsed_deadline = datetime.datetime.strptime(deadline, '%Y-%m-%d %H:%M:%S')
                self.agent.schedule_task(task_name, parsed_deadline.strftime('%Y-%m-%d %H:%M:%S'))
                self.populate_task_list()
                messagebox.showinfo("Success", f"Task '{task_name}' added!")
            except ValueError:
                messagebox.showerror("Error", "Invalid deadline format!")

    def delete_task(self):
        selected_task = self.task_list.get(tk.ACTIVE)
        if selected_task:
            task_id = int(selected_task.split(":")[0])
            self.agent.delete_task(task_id)
            self.populate_task_list()
            messagebox.showinfo("Success", f"Task ID {task_id} deleted!")

    def update_task(self):
        selected_task = self.task_list.get(tk.ACTIVE)
        if selected_task:
            task_id = int(selected_task.split(":")[0])
            new_name = simpledialog.askstring("Update Task", "Enter new task name:")
            if new_name:
                new_deadline = simpledialog.askstring("Update Task", "Enter new deadline (YYYY-MM-DD HH:MM:SS):")
                try:
                    parsed_deadline = datetime.datetime.strptime(new_deadline, '%Y-%m-%d %H:%M:%S')
                    self.agent.update_task(task_id, new_name, parsed_deadline.strftime('%Y-%m-%d %H:%M:%S'))
                    self.populate_task_list()
                    messagebox.showinfo("Success", f"Task ID {task_id} updated!")
                except ValueError:
                    messagebox.showerror("Error", "Invalid deadline format!")

    def complete_task(self):
        selected_task = self.task_list.get(tk.ACTIVE)
        if selected_task:
            task_id = int(selected_task.split(":")[0])
            self.agent.complete_task(task_id)
            self.populate_task_list()
            messagebox.showinfo("Success", f"Task ID {task_id} marked as completed!")

    def add_meeting(self):
        meeting_time = simpledialog.askstring("Add Meeting", "Enter meeting time (YYYY-MM-DD HH:MM:SS):")
        if meeting_time:
            description = simpledialog.askstring("Add Meeting", "Enter meeting description:")
            if description:
                try:
                    # Parse the input meeting time
                    parsed_time = datetime.datetime.strptime(meeting_time, '%Y-%m-%d %H:%M:%S')

                    # Check if there's already a meeting scheduled at this time
                    existing_meetings = self.agent.get_meetings()
                    conflict_found = False
                    for meeting in existing_meetings:
                        meeting_time_db = datetime.datetime.strptime(meeting[1], '%Y-%m-%d %H:%M:%S')
                        if meeting_time_db == parsed_time:
                            conflict_found = True
                            break

                    if conflict_found:
                        # If a conflict is found, suggest alternative times
                        alternative_time_found = False
                        for delta_minutes in range(10, 60, 10):  # Try suggesting times 10, 20, 30, 40, 50 minutes later
                            alternative_time = parsed_time + datetime.timedelta(minutes=delta_minutes)
                            # Check if the new time is available
                            if not any(datetime.datetime.strptime(meeting[1], '%Y-%m-%d %H:%M:%S') == alternative_time for meeting in existing_meetings):
                                alternative_time_found = True
                                message = f"The meeting time you chose is already taken. Would you like to schedule the meeting for {alternative_time.strftime('%Y-%m-%d %H:%M:%S')} instead?"
                                if messagebox.askyesno("Time Conflict", message):
                                    self.agent.schedule_meeting(alternative_time.strftime('%Y-%m-%d %H:%M:%S'), description)
                                    self.populate_meeting_list()
                                    messagebox.showinfo("Success", f"Meeting scheduled for {alternative_time.strftime('%Y-%m-%d %H:%M:%S')}")
                                    break

                        if not alternative_time_found:
                            messagebox.showerror("Error", "No available alternative times in the next hour.")
                    else:
                        # If no conflict, schedule the meeting at the requested time
                        self.agent.schedule_meeting(parsed_time.strftime('%Y-%m-%d %H:%M:%S'), description)
                        self.populate_meeting_list()
                        messagebox.showinfo("Success", "Meeting added!")
                except ValueError:
                    messagebox.showerror("Error", "Invalid time format!")


    def delete_meeting(self):
        selected_meeting = self.meeting_list.get(tk.ACTIVE)
        if selected_meeting:
            meeting_id = int(selected_meeting.split(":")[0])
            self.agent.delete_meeting(meeting_id)
            self.populate_meeting_list()
            messagebox.showinfo("Success", f"Meeting ID {meeting_id} deleted!")

    def update_meeting(self):
        selected_meeting = self.meeting_list.get(tk.ACTIVE)
        if selected_meeting:
            meeting_id = int(selected_meeting.split(":")[0])
            new_time = simpledialog.askstring("Update Meeting", "Enter new meeting time (YYYY-MM-DD HH:MM:SS):")
            if new_time:
                description = simpledialog.askstring("Update Meeting", "Enter new description:")
                if description:
                    try:
                        parsed_time = datetime.datetime.strptime(new_time, '%Y-%m-%d %H:%M:%S')
                        self.agent.update_meeting(meeting_id, parsed_time.strftime('%Y-%m-%d %H:%M:%S'), description)
                        self.populate_meeting_list()
                        messagebox.showinfo("Success", f"Meeting ID {meeting_id} updated!")
                    except ValueError:
                        messagebox.showerror("Error", "Invalid time format!")

    def complete_meeting(self):
        selected_meeting = self.meeting_list.get(tk.ACTIVE)
        if selected_meeting:
            meeting_id = int(selected_meeting.split(":")[0])
            self.agent.complete_meeting(meeting_id)
            self.populate_meeting_list()
            messagebox.showinfo("Success", f"Meeting ID {meeting_id} marked as completed!")

    def send_reminder(self):
        task_reminders = self.agent.check_for_upcoming_tasks()
        meeting_reminders = self.agent.check_for_upcoming_meetings()

        # If there are reminders, display them
        if task_reminders or meeting_reminders:
            reminders = task_reminders + meeting_reminders
            reminder_message = "\n".join(reminders)
            messagebox.showinfo("Reminders", reminder_message)
        else:
            # If no reminders, suggest pending tasks
            pending_tasks = self.agent.get_tasks()
            pending_task_message = "\nHere are your pending tasks:\n"

            # Display pending tasks if there are any
            if pending_tasks:
                for task in pending_tasks:
                    if not task[3]:  # If the task is not completed
                        pending_task_message += f"- {task[1]} (Deadline: {task[2]})\n"
            else:
                pending_task_message += "You have no pending tasks.\n"

            messagebox.showinfo("No Reminders", pending_task_message)


    def check_for_upcoming_events(self):
        self.root.after(60000, self.check_for_upcoming_events)  # Check every minute
        self.send_reminder()


if __name__ == "__main__":
    root = tk.Tk()
    assistant_gui = AssistantGUI(root)
    root.mainloop()
