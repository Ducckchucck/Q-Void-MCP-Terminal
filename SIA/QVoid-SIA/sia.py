# sia.py
from textblob import TextBlob
from modules.voice_manager import tts_manager

def detect_emotion(text):
    text = text.lower()
    # Urgent cues
    if any(word in text for word in ["asap", "quick", "urgent", "now", "immediately", "hurry"]):
        return "urgent"
    # Confused cues
    if any(word in text for word in ["don't get", "don't understand", "confused", "what do you mean", "too complicated"]):
        return "confused"
    # Positive cues
    if any(word in text for word in ["amazing", "awesome", "thank you", "great", "nice work", "love it", "that was fire", "very helpful", "good answer"]):
        return "positive"
    if any(x in text for x in ["why is this", "your behavior is weird", "what's wrong with this"]):
        return "confused"

    
    # Fallback to polarity
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # type: ignore
    if polarity > 0.4:
        return "positive"
    elif polarity < -0.2:
        return "confused"
    else:
        return "neutral"

def tune_response_by_tone(response, tone):
    if response.lower().startswith("sia:"):
        response = response[4:].strip()
    
    if tone in ("urgent", "confused"):
        response = response.split(".")[0] + "."
    
    if tone == "positive" and "glad" in response.lower():
        return response

    elif tone == "urgent":
        short_response = response.split('.')[0] + "."
        return f"⚠️ Here's a quick answer: {short_response}"

    elif tone == "confused":
        simplified = "Let me try again, simply:\n\n" + response.split('.')[0] + "."
        return f"🤔 {simplified}"

    else:
        return response

import asyncio
from modules.real_stt import recognize_speech
from modules.real_gemini import generate_response
from modules.google_search import perform_google_search
from collections import deque
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from modules.tone_memory import save_tone_training_data, load_tone_training_data

class SIAState:
    def __init__(self):
        self.current_mode = "normal"
        self.conversation_history = []
        self.last_command = None
        self.user_preferences = {}
        self.tone_training_data = deque(maxlen=100)  # Stores (text, tone)

class SIA:
    def __init__(self):
        self.state = SIAState()
        self.state.tone_training_data = load_tone_training_data()
        self.state.tone_training_data.extend([
        ("that was amazing", "positive"),
        ("i loved that", "positive"),
        ("this is great", "positive"),
        ("quick! tell me", "urgent"),
        ("i need this now", "urgent"),
        ("hurry please", "urgent"),
        ("i don’t understand", "confused"),
        ("this is too hard", "confused"),
        ("what do you mean?", "confused"),
        ("what is gravity", "neutral"),
        ("tell me about dogs", "neutral"),
        ])
        self.listening = True
        self.classifier = None
        self.last_response = None
        self.COMMAND_HANDLERS = {
            "search": {
                "triggers": ["search for", "look up", "find"],
                "handler": "_handle_search"
            },
            "exit": {
                "triggers": ["exit", "quit", "stop", "goodbye"],
                "handler": "_handle_exit"
            },
            "repeat": {
                "triggers": ["repeat", "say that again"],
                "handler": "_handle_repeat"
            },
            "preference": {
                "triggers": ["call me", "my name is"],
                "handler": "_handle_preference"
            },
            "stop_speaking": {
                "triggers": ["stop speaking", "skip that", "cut it"],
                "handler": "_handle_stop_speaking"
            },
            "error_fix": {
                "triggers": [
                    "fix error", "analyze bug", "python error", "debug this", 
                    "exception fix", "i got an error", "can you fix", "debug code", 
                    "code is crashing", "crash", "stack trace", "traceback"
                ],
                "handler": "_handle_error_fix"
            }
        }
 
    async def run(self):
        print("🧠 SIA is ready. Listening for input...\n")
        await self._greet_user()
        
        while self.listening:
            user_input = recognize_speech()
            if not user_input:
                continue
                
            await self._process_input(user_input.lower())

    async def _greet_user(self):
        if "name" in self.state.user_preferences:
            greeting = f"Hello {self.state.user_preferences['name']}! How can I help you?"
        else:
            greeting = "Hello! How can I help you today?"
        tts_manager.speak(greeting)

    async def _process_input(self, user_input):
        command_handler = self._identify_command(user_input)
        if command_handler:
            await getattr(self, command_handler)(user_input)
        elif user_input.strip() in ["repeat", "say that again"]:
            await self._handle_repeat(user_input)
        elif user_input.strip() in ["cancel", "skip", "nevermind"]:
            tts_manager.speak("Okay, cancelled. Please say your next command or question.")
        elif user_input.strip().startswith("switch to offline voice"):
            tts_manager.switch_engine('pyttsx3')
            tts_manager.speak("Switched to offline voice.")
        elif user_input.strip().startswith("switch to natural voice") or user_input.strip().startswith("switch to online voice"):
            tts_manager.switch_engine('gtts')
            tts_manager.speak("Switched to natural voice.")
        elif not user_input.strip():
            tts_manager.speak("I didn't catch that. Please repeat your question or command.")
        else:
            try:
                await self._handle_conversation(user_input)
            except Exception as e:
                print(f"⚠️ Error in conversation: {e}")
                tts_manager.speak("Sorry, I couldn't process that. Please try again.")

    def _identify_command(self, input_text):
        for command, config in self.COMMAND_HANDLERS.items():
            for trigger in config["triggers"]:
                if trigger in input_text:  # changed from .startswith() to in
                    return config["handler"]
        return None


    async def _handle_conversation(self, user_input):
        self.state.conversation_history.append(("user", user_input))
    
        if self.classifier:
            try:
                tone = self.classifier.predict([user_input])[0]
                source = "classifier" if self.classifier else "textblob"
                print(f"[Tone: {tone} | Source: {source}]")
            except:
                tone = detect_emotion(user_input)
        else:
            tone = detect_emotion(user_input)

        self.state.user_preferences["tone"] = tone

        prompt = self._build_conversation_prompt()
        response = await generate_response(prompt)
        
        if response.lower().startswith("sia:"):
            response = response[4:].strip()
            
        if self.classifier and len(self.state.tone_training_data) >= 10:
            tone = self.classifier.predict([user_input])[0]
        else:
            tone = detect_emotion(user_input)
    
        tuned_response = tune_response_by_tone(response, tone)

        self.last_response = tuned_response
        self.state.conversation_history.append(("sia", tuned_response))
        self.state.tone_training_data.append((user_input, tone))
        self._train_tone_classifier()
        tts_manager.speak(tuned_response)


    def _build_conversation_prompt(self):
        prompt = "Current conversation:\n"
        for speaker, text in self.state.conversation_history[-5:]:
            prompt += f"{speaker.capitalize()}: {text}\n"
        prompt += "SIA:"
        return prompt

    async def _handle_search(self, user_input):
        query = user_input.split("search for")[-1].strip()
        tts_manager.speak(f"Searching for {query}...")
    
        results = perform_google_search(query)
    
        if isinstance(results, list):
            response = "\n".join(results[:2])
        else:
            response = str(results)
    
        tts_manager.speak(response)

    async def _handle_repeat(self, user_input):
        if self.last_response:
            tts_manager.speak(self.last_response)
        else:
            tts_manager.speak("I don't have anything to repeat yet.")

    async def _handle_exit(self, user_input):
        tts_manager.speak("Goodbye! Have a nice day.")
        self.listening = False

    async def _handle_preference(self, user_input):
        if "call me" in user_input:
            name = user_input.split("call me")[-1].strip()
            self.state.user_preferences["name"] = name
            tts_manager.speak(f"Okay, I'll call you {name}")
        elif "my name is" in user_input:
            name = user_input.split("my name is")[-1].strip()
            self.state.user_preferences["name"] = name
            tts_manager.speak(f"Nice to meet you, {name}!")

    async def _confirm_action(self, prompt):
        tts_manager.speak(f"{prompt} Please say yes or no.")
        response = recognize_speech()
        return response and "yes" in response.lower()
    
    def _train_tone_classifier(self):
        if len(self.state.tone_training_data) < 10:
            return  # Not enough data yet

        texts, tones = zip(*self.state.tone_training_data)
        self.classifier = make_pipeline(
            TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=1000),
            LogisticRegression(max_iter=500, class_weight='balanced')
        )
        self.classifier.fit(texts, tones)
        save_tone_training_data(self.state.tone_training_data)
    
    async def _handle_error_fix(self, user_input):
        from error_fix_handler import get_error_input_gui, call_gemini, extract_code, offer_fix_application

        tts_manager.speak("Opening a text box. Paste your error or problem there.")
    
        error_text = get_error_input_gui()

        if not error_text:
            tts_manager.speak("No input received. Cancelled.")
            return

        tts_manager.speak("Analyzing your error, please wait...")

        try:
            response = await call_gemini(error_text)
        except Exception as e:
            print(f"⚠️ Gemini error: {e}")
            tts_manager.speak("Gemini failed to analyze it. Try again later.")
            return

        tts_manager.speak("Here’s what I found.")
        print("\n📋 Gemini Response:\n", response)

        fixed_code = extract_code(response)
        if fixed_code:
            print("\n✅ Suggested Fix:\n", fixed_code)
            offer_fix_application(fixed_code)
            tts_manager.speak("I found a fix and printed it to the terminal.")
        else:
            tts_manager.speak("I couldn’t extract any clear fix from the response.")

    async def _handle_stop_speaking(self, user_input):
        tts_manager.stop()
        tts_manager.speak("Okay, I’ll stop talking.")

