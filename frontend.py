import tkinter as tk
from tkinter import scrolledtext
import tkinter.messagebox as messagebox
from chatbot_backend import ChatbotBackend  # Import backend logic


class ChatbotInterface:
    def __init__(self, root):
        self.root = root
        self.backend = ChatbotBackend()  # Initialize backend
        self.chat_history_file = "chat_history.json"  # File to store chat history

        self.buttons_added = False  # Track if extra buttons are already added

        # Set up the UI components
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI components."""
        # Frame for the greeting message
        self.greeting_frame = tk.Frame(self.root, bg="#34495e", height=100)
        self.greeting_frame.pack(side=tk.TOP, fill=tk.X)

        # Greeting message label
        self.greeting_label = tk.Label(
            self.greeting_frame, text="Hello! Please enter your name to begin:", font=("Arial", 16, "bold"), bg="#34495e", fg="white"
        )
        self.greeting_label.pack(pady=20)

        # Name input field
        self.name_entry = tk.Entry(self.greeting_frame, width=40, font=("Arial", 14), justify="center")
        self.name_entry.pack(pady=5)

        # Button to start chat
        self.start_button = tk.Button(
            self.greeting_frame, text="Start Chat", command=self.start_conversation, font=("Arial", 12), bg="green", fg="white", relief=tk.RAISED
        )
        self.start_button.pack(pady=10)

        # Chat display area (initially hidden)
        self.chat_area = scrolledtext.ScrolledText(
            self.root,
            state="disabled",
            wrap=tk.WORD,
            font=("Arial", 12),
            bg="#ecf0f1",
            fg="#2c3e50",
            bd=1
        )
        self.chat_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.chat_area.pack_forget()

        # Input frame for typing messages (initially hidden)
        self.input_frame = tk.Frame(self.root, bg="#ecf0f1")
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)
        self.input_frame.pack_forget()

        # User input field
        self.input_field = tk.Entry(self.input_frame, width=60, font=("Arial", 14), bg="white", fg="#2c3e50")
        self.input_field.grid(row=0, column=0, padx=5, sticky="we")
        self.input_field.bind("<Return>", self.handle_input)

        # Send button
        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            command=self.handle_input,
            font=("Arial", 12),
            bg="#3498db",
            fg="white",
            relief=tk.RAISED
        )
        self.send_button.grid(row=0, column=1, padx=5)

        # Adjust column sizes
        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.columnconfigure(1, weight=0)

    def start_conversation(self):
        """Start the chat session with the backend."""
        user_name = self.name_entry.get().strip()
        if not user_name:
            self.greeting_label.config(text="Please enter your name first!", fg="red")
            return

        # Start the chat session with the backend
        greeting_message = self.backend.initiate_chat(user_name)
        self.greeting_label.config(text=greeting_message, fg="white")
        self.name_entry.pack_forget()
        self.start_button.pack_forget()
        self.chat_area.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.input_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Add history, delete history, and help buttons (once per session)
        if not self.buttons_added:
            self.history_button = tk.Button(
                self.greeting_frame, text="History", command=self.show_history, font=("Arial", 12), bg="lightblue", fg="black", relief=tk.RAISED
            )
            self.history_button.pack(pady=10)

            self.delete_history_button = tk.Button(
                self.greeting_frame, text="Delete History", command=self.delete_history, font=("Arial", 12), bg="lightcoral", fg="black", relief=tk.RAISED
            )
            self.delete_history_button.pack(pady=10)

            self.help_button = tk.Button(
                self.greeting_frame, text="Help", command=self.display_help, font=("Arial", 12), bg="lightgreen", fg="black", relief=tk.RAISED
            )
            self.help_button.place(x=self.root.winfo_width() - 150, y=20)  # Position help button top-right

            self.buttons_added = True  # Mark buttons as added

    def handle_input(self, event=None):
        """Handle the user input and generate a chatbot response."""
        user_input = self.input_field.get().strip()

        if not user_input:
            self.add_to_chat(f"{self.backend.selected_agent}: Please enter something to ask!")
            return

        # Clear the input field
        self.input_field.delete(0, tk.END)

        # Display user's message in the chat
        self.add_to_chat(f"You: {user_input}")

        # Get the chatbot's response
        chatbot_response = self.backend.handle_user_input(user_input)

        # If the response contains "Goodbye", end the session after a short delay
        if "Goodbye" in chatbot_response:
            self.add_to_chat(f"{chatbot_response}")
            self.root.after(3000, self.end_session)  # Wait for 3 seconds before closing
        else:
            self.add_to_chat(f"{self.backend.selected_agent}: {chatbot_response}")

    def add_to_chat(self, message):
        """Display a message in the chat area."""
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state="disabled")

    def show_history(self):
        """Display the conversation history in a new window."""
        user_name = self.name_entry.get().strip()
        if not user_name:
            return  # Don't show history if no username is set

        # Create a new window for the history
        history_window = tk.Toplevel(self.root)
        history_window.title("Conversation History")

        history_text = scrolledtext.ScrolledText(history_window, wrap=tk.WORD, width=50, height=20, state='normal')
        history_text.grid(row=0, column=0, padx=10, pady=10)

        # Fetch and display the user's history
        user_history = self.backend.display_history()

        if user_history:
            history_text.insert(tk.END, user_history)
        else:
            history_text.insert(tk.END, "No previous conversations found.")

        history_text.config(state='disabled')  # Make history text non-editable

    def delete_history(self):
        """Delete the current user's chat history and prompt to continue or quit."""
        user_name = self.name_entry.get().strip()
        if not user_name:
            return  # Don't delete if no username is set

        # Call backend to delete the history
        self.backend.delete_chat_history(user_name)

        # Confirm deletion and prompt the user to continue
        self.add_to_chat("Chat history successfully deleted.")
        self.ask_continue()

    def ask_continue(self):
        """Ask if the user wants to continue the chat."""
        response = messagebox.askquestion("Continue Chat", "Would you like to continue chatting?")

        if response == 'yes':
            # Restart chat session
            self.start_conversation()
        else:
            # End session
            self.add_to_chat(f"Thanks for chatting, {self.backend.current_user}. Have a great day!")
            self.root.quit()  # Close the application

    def display_help(self):
        help_text = """Welcome to the chatbot! Here are some instructions:

1. Type your message and press 'Send' or hit Enter.
2. To view your conversation history, click 'History'.
3. You can delete your chat history using the 'Delete History' button.
4. To exit, simply type 'Bye'.

Enjoy chatting with the bot!"""

        # Create a window for help content
        help_window = tk.Toplevel(self.root)
        help_window.title("Help")

        help_display = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, width=50, height=20, state='normal')
        help_display.grid(row=0, column=0, padx=2, pady=2)

        help_display.insert(tk.END, help_text)
        help_display.config(state='disabled')  # Make help text non-editable

    def end_session(self):
        """End the session and close the application."""
        self.root.quit()

# Run the chatbot application
if __name__ == "__main__":
    root = tk.Tk()
    root.title("University of Poppleton Chatbot")
    root.geometry("500x600")

    app = ChatbotInterface(root)
    root.protocol("WM_DELETE_WINDOW", app.end_session)  # Close session on window close
    root.mainloop()
