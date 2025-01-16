import random
import json
import time
import re
import logging
import os


def load_configuration():
    """Load configuration settings from the config file."""
    try:
        # Attempt to open and load the config file
        with open('config.json', 'r') as file:
            config_data = json.load(file)
            print("Configuration Loaded Successfully:", config_data)  # Debug print
            return config_data
    except (FileNotFoundError, json.JSONDecodeError) as error:
        logging.error(f"Error while loading the config: {error}")
        return {}  # Returning an empty dictionary if config load fails

class ChatbotBackend:
    def __init__(self):
        """Set up chatbot with necessary settings and default values."""
        self.configuration = load_configuration()

        # Debug print to verify configuration loading
        if not self.configuration:
            logging.error("No configuration loaded. Check the config.json file.")
            raise ValueError("Configuration not found!")

        # Using fallback values if the configuration is missing keys
        self.agent_names = self.configuration.get("agents", [])
        self.responses = self.configuration.get("responses", {"keywords": {}, "multi_word_responses": {}, "random_responses": []})
        self.exit_commands = set(self.configuration.get("exit_commands", ["bye", "exit", "quit"]))  # Default exit commands

        # Debug print to verify if agents are loaded
        if not self.agent_names:
            logging.error("No agent names found in the configuration.")
            raise ValueError("No agent names found in the configuration.")
        print("Agent Names Found:", self.agent_names)  # Debug print
        
        self.selected_agent = random.choice(self.agent_names)  # Select a random agent from the list

        self.current_user = None
        self.history_directory = "chat_histories"  # Folder to store chat history files

        # Ensure history folder exists
        if not os.path.exists(self.history_directory):
            os.makedirs(self.history_directory)

    def get_chat_history(self, user):
        """Retrieve chat history from a file."""
        history_file_path = f"{self.history_directory}/{user}_history.json"
        
        try:
            with open(history_file_path, "r") as file:
                history_data = json.load(file)
                
            # If history is not a list, return an empty list
            if not isinstance(history_data, list):
                return []
            return history_data
            
        except FileNotFoundError:
            logging.warning(f"History file for {user} not found.")
            return []
        
        except json.JSONDecodeError:
            logging.warning(f"Error decoding the history file for {user}. It may be corrupted.")
            return []
        
        except Exception as error:
            logging.error(f"Error while loading chat history for {user}: {str(error)}")
            return []

    def save_chat_history(self, user, history_data):
        """Save the conversation history for a user."""
        history_file_path = f"{self.history_directory}/{user}_history.json"
        
        # Ensure history is a list before saving
        if not isinstance(history_data, list):
            history_data = []
        
        try:
            logging.debug(f"Saving chat history for {user}: {history_data}")
            with open(history_file_path, "w") as file:
                json.dump(history_data, file, indent=4)
            
            logging.debug(f"Chat history saved successfully for {user}")
        
        except Exception as error:
            logging.error(f"Error while saving chat history for {user}: {error}")

    def add_to_global_history(self, entry):
        """Append an entry to the global chat history file."""
        global_history_path = "history.json"
        
        try:
            with open(global_history_path, 'r') as file:
                global_history = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            global_history = []

        global_history.append(entry)
        
        try:
            with open(global_history_path, 'w') as file:
                json.dump(global_history, file, indent=4)
        except Exception as error:
            logging.error(f"Error while saving to global chat history: {error}")

    def initiate_chat(self, user_name):
        """Start a new chat session with the user."""
        self.current_user = user_name.strip()
        if not self.current_user:
            return "Please provide your name!"

        greeting_message = f"Hello {self.current_user}! Chat with {self.selected_agent}. Type 'bye' to exit."
        self.record_chat(self.current_user, "System", greeting_message)  # Log the greeting message
        return greeting_message

    def handle_user_input(self, user_input):
        """Process the user's input and generate an appropriate response."""
        user_input = user_input.strip().lower()  

        # Simulate random disconnection (10% chance)
        if random.random() < 0.1:
            disconnection_message = f"{self.selected_agent}: Oops! We seem to have lost the connection. Please try again later."
            logging.warning(f"Disconnection occurred for user '{self.current_user}' at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            self.record_chat(self.current_user, self.selected_agent, disconnection_message)  # Log the disconnection
            return disconnection_message

        # If user input is empty
        if not user_input:
            response = f"{self.selected_agent}: You haven't said anything. Please ask a question!"
            self.record_chat(self.current_user, "You", user_input)  # Log the empty input
            self.record_chat(self.current_user, self.selected_agent, response)  # Log the response
            return response

        # Exit if the user input matches any exit command
        if user_input in self.exit_commands:
            response = f"{self.selected_agent}: Goodbye {self.current_user}!"
            self.record_chat(self.current_user, "You", user_input)  # Log the exit message
            self.record_chat(self.current_user, self.selected_agent, response)  # Log the exit response
            return response

        # Process the input and generate a response
        response = self.simulate_delay_and_respond(user_input)

        # Log the conversation only if it's not a disconnection message
        if "Oops! We seem to have lost the connection" not in response:
            self.record_chat(self.current_user, "You", user_input)  # Log the user's input
            self.record_chat(self.current_user, self.selected_agent, response)  # Log the agent's response

        return response

    def simulate_delay_and_respond(self, user_input):
        """Introduce a random delay before generating a response."""
        time.sleep(random.uniform(1, 2))  # Random delay (1-2 seconds)
        return self.generate_response(user_input)

    def generate_response(self, user_input):
        """Generate a response based on the user's input."""
        user_input = user_input.lower()

        responses = []
        multi_word_responses = self.responses.get("multi_word_responses", {})
        for phrase, response in multi_word_responses.items():
            if re.search(rf'\b{re.escape(phrase)}\b', user_input):  # Check if the exact multi-word phrase is present
                responses.append(response)
                break  
        if responses:
            return "\n".join(responses)
        # Check for specific keywords and add relevant responses
        if "hello" in user_input or "hi" in user_input:
            responses.append(f"Hello, {self.current_user}! How can I assist you today?")

        if "how are you" in user_input:
            responses.append(f"I'm doing well, {self.current_user}. How about you?")

        # Handle cafe-related queries
        if "cafe" in user_input:
            if "direction" in user_input:
                responses.append(random.choice(self.responses["keywords"]["cafe"]["directions"]))
            else:
                responses.append(random.choice(self.responses["keywords"]["cafe"]["general"]))

        # Handle library-related queries
        if "library" in user_input:
            if "direction" in user_input:
                responses.append(random.choice(self.responses["keywords"]["library"]["directions"]))
            else:
                responses.append(random.choice(self.responses["keywords"]["library"]["general"]))

        # Handle book-related queries
        if "book" in user_input:
            responses.append(random.choice(self.responses["keywords"]["book"]["general"]))

        # Handle study-related queries
        if "study" in user_input:
            responses.append(random.choice(self.responses["keywords"]["study"]["general"]))

        # Handle programming-related queries
        if "programming" in user_input:
            responses.append(random.choice(self.responses["keywords"]["programming"]["general"]))

        if "python" in user_input:
            responses.append(random.choice(self.responses["keywords"]["programming"]["python"]))

        if "javascript" in user_input:
            responses.append(random.choice(self.responses["keywords"]["programming"]["javascript"]))

        if "java" in user_input:
            responses.append(random.choice(self.responses["keywords"]["programming"]["java"]))

        if "c++" in user_input:
            responses.append(random.choice(self.responses["keywords"]["programming"]["c++"]))



        # If no specific keyword is matched, return a random response
        if not responses:
            random_response = random.choice(self.responses.get("random_responses", []))
            # Replace {username} with the actual user's name
            random_response = random_response.format(username=self.current_user)
            responses.append(random_response)


        # Combine and return all responses as a single string
        return "\n".join(responses)

    def record_chat(self, user_name, speaker, message):
        """Log the conversation between the user and the chatbot."""
        if not user_name:
            return

        # Skip logging disconnection messages
        if "Oops! We seem to have lost the connection" in message:
            return

        speaker_name = user_name if speaker == "You" else self.selected_agent

        # Load existing history and append the new message
        history = self.get_chat_history(user_name)
        history.append({"speaker": speaker_name, "message": message})

        self.save_chat_history(user_name, history)
        self.add_to_global_history({"speaker": speaker_name, "message": message})

    def display_history(self):
        """Display the entire chat history for the user."""
        if not self.current_user:
            return "Please start a conversation first."

        user_history = self.get_chat_history(self.current_user)

        if not user_history:
            return "No previous chat history found."

        formatted_history = ""
        for entry in user_history:
            speaker = entry.get('speaker', 'Unknown')
            message = entry.get('message', ' ')
            formatted_history += f"{speaker}: {message}\n"
        
        return formatted_history.strip()
    def delete_chat_history(self, user_name):
        """Delete the chat history for a specific user."""
        history_file_path = f"{self.history_directory}/{user_name}_history.json"

        try:
            # Check if the history file exists
            if os.path.exists(history_file_path):
                os.remove(history_file_path)
                logging.info(f"Chat history for {user_name} has been deleted.")
                return f"Chat history for {user_name} has been deleted."
            else:
                logging.warning(f"No chat history found for {user_name}.")
                return f"No chat history found for {user_name}."
        except Exception as error:
            logging.error(f"Error while deleting chat history for {user_name}: {error}")
            return f"An error occurred while deleting chat history for {user_name}. Please try again later."
