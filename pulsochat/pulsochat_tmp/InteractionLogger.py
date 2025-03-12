from datetime import datetime
import os

class InteractionLogger:
    """Handles logging of user messages and AI responses."""

    def __init__(self, log_path):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file_name = os.path.join(log_path, f"chat_logs_{timestamp}.txt")

    def log_interaction(self, message, response):
        """Logs user message and AI response to the log file."""
        with open(self.log_file_name, "a", encoding="utf-8") as log_file:
            log_file.write(f"User: {message}\n")
            log_file.write(f"AI: {response}\n")
            log_file.write("=" * 50 + "\n")
