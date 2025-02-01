from datetime import datetime

reminders = []

def set_reminder(reminder_text, reminder_time):
    reminders.append((reminder_text, reminder_time))
    return f"Reminder set for {reminder_time}."

def check_reminders():
    current_time = datetime.now()
    due_reminders = [reminder for reminder in reminders if reminder[1] <= current_time]
    for reminder in due_reminders:
        print(f"Reminder: {reminder[0]}")
    reminders[:] = [reminder for reminder in reminders if reminder[1] > current_time]