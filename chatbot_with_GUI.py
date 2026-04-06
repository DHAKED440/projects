import customtkinter as ctk
from google import genai
import threading

# --- CONFIGURATION ---
# Get your key from https://aistudio.google.com/
API_KEY = "YOUR_API_KEY"

# Theme settings
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class GeminiChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gemini 2.5 Free Assistant")
        self.geometry("600x800")

        # Initialize Gemini Client
        try:
            self.client = genai.Client(api_key=API_KEY)
            # UPDATED MODEL: 2.5 Flash-Lite has the highest free quota in 2026
            self.chat_session = self.client.chats.create(model="gemini-2.5-flash-lite")
        except Exception as e:
            print(f"Startup Error: {e}")

        # --- UI LAYOUT ---
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header with Clear Button
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=20, pady=(10, 0), sticky="ew")
        
        self.clear_btn = ctk.CTkButton(self.header, text="Reset Memory", fg_color="#d9534f", 
                                       hover_color="#c9302c", command=self.clear_chat, width=100)
        self.clear_btn.pack(side="right")

        # Chat Display
        self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word", corner_radius=10)
        self.chat_display.grid(row=1, column=0, padx=20, pady=20, sticky="nsew")

        # Input Frame
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.user_input = ctk.CTkEntry(self.input_frame, placeholder_text="Type here...", height=45)
        self.user_input.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.user_input.bind("<Return>", lambda e: self.send_message())

        self.send_button = ctk.CTkButton(self.input_frame, text="Send", width=100, height=45, command=self.send_message)
        self.send_button.grid(row=0, column=1)

    def append_text(self, sender, text):
        self.chat_display.configure(state="normal")
        self.chat_display.insert("end", f"{sender}: {text}\n\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    def clear_chat(self):
        self.chat_display.configure(state="normal")
        self.chat_display.delete("1.0", "end")
        self.chat_display.configure(state="disabled")
        self.chat_session = self.client.chats.create(model="gemini-2.5-flash-lite")
        self.append_text("System", "Memory wiped. Ready for a new topic!")

    def send_message(self):
        msg = self.user_input.get().strip()
        if not msg: return
        
        self.append_text("You", msg)
        self.user_input.delete(0, 'end')
        self.send_button.configure(state="disabled", text="Thinking...")
        
        threading.Thread(target=self.run_api, args=(msg,), daemon=True).start()

    def run_api(self, msg):
        try:
            response = self.chat_session.send_message(msg)
            self.after(0, lambda: self.show_reply(response.text))
        except Exception as e:
            err_msg = str(e) # Capture error as string to avoid NameError
            self.after(0, lambda: self.show_reply(f"⚠️ Error: {err_msg}"))

    def show_reply(self, text):
        self.append_text("Gemini", text)
        self.send_button.configure(state="normal", text="Send")

if __name__ == "__main__":
    app = GeminiChatApp()
    app.mainloop()
#https://aistudio.google.com/api-keys?project=gen-lang-client-0476529605
    #py -m pip install -U google-genai customtkinter
