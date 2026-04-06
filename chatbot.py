from google import genai
import os

# Set your API key in your environment or replace 'YOUR_API_KEY'
client = genai.Client(api_key="YOUR_API_KEY")

# Initialize chat session
chat = client.chats.create(model="gemini-3-flash-preview")

print("--- Gemini Free Chat (Type 'quit' to stop) ---")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit"]:
        break

    # Gemini handles history management automatically within the 'chat' object
    response = chat.send_message(user_input)
    
    print(f"Gemini: {response.text}")
