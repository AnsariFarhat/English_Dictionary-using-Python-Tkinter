import tkinter as tk
from tkinter import messagebox, scrolledtext
import requests
import pickle
import os
import pyttsx3
from nltk.corpus import wordnet
import nltk 
import os
import pickle

# Always store the cache in user's home directory
CACHE_FILE = os.path.join(os.path.expanduser("~"), "dictionary_cache.pkl")

# Load cache if available
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except:
            return {}
    return {}

# Save cache safely
def save_cache(data):
    try:
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(data, f)
    except Exception as e:
        print(f"Error saving cache: {e}")

# Ensure WordNet is available
try:
    wordnet.synsets('example')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

# Initialize TTS engine
engine = pyttsx3.init()

# Cache file for offline meanings
CACHE_FILE = "dictionary_cache.pkl"
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "rb") as f:
        word_cache = pickle.load(f)
else:
    word_cache = {}

# ---------- FUNCTIONS ----------
def speak_word():
    word = entry.get().strip()
    if word:
        engine.say(word)
        engine.runAndWait()

def get_word_data():
    word = entry.get().strip().lower()
    if not word:
        messagebox.showerror("Error", "Please enter a word.")
        return
    
    # Clear previous results
    result_text.delete(1.0, tk.END)

    # Check cache first
    if word in word_cache:
        data = word_cache[word]
        display_word_data(word, data)
        return

    # Fetch from API
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url)
        api_data = response.json()

        if isinstance(api_data, dict) and api_data.get("title") == "No Definitions Found":
            result_text.insert(tk.END, f"No meaning found for '{word}'\n\n")
            return

        # Parse API Data
        meanings = []
        examples = []

        for meaning in api_data[0]["meanings"]:
            part_of_speech = meaning.get("partOfSpeech", "")
            for definition in meaning["definitions"]:
                meanings.append(f"({part_of_speech}) {definition['definition']}")
                if "example" in definition:
                    examples.append(definition["example"])

        # Synonyms & Antonyms
        synonyms = set()
        antonyms = set()
        for syn in wordnet.synsets(word):
            for lemma in syn.lemmas():
                synonyms.add(lemma.name())
                if lemma.antonyms():
                    antonyms.add(lemma.antonyms()[0].name())

        # Store in cache
        word_cache[word] = {
            "meanings": meanings,
            "examples": examples,
            "synonyms": list(synonyms),
            "antonyms": list(antonyms)
        }
        with open(CACHE_FILE, "wb") as f:
            pickle.dump(word_cache, f)

        # Display results
        display_word_data(word, word_cache[word])

    except Exception as e:
        result_text.insert(tk.END, f"Error fetching data: {str(e)}\n\n")

def display_word_data(word, data):
    result_text.insert(tk.END, f"📖 MEANING of '{word}':\n", "bold")
    for m in data["meanings"]:
        result_text.insert(tk.END, f" - {m}\n")

    result_text.insert(tk.END, "\n📝 EXAMPLES:\n", "bold")
    if data["examples"]:
        for ex in data["examples"]:
            result_text.insert(tk.END, f" - {ex}\n")
    else:
        result_text.insert(tk.END, "No examples available.\n")

    result_text.insert(tk.END, "\n🔹 SYNONYMS:\n" , "bold")
    result_text.insert(tk.END, (", ".join(data["synonyms"]) if data["synonyms"] else "None") + "\n")
    result_text.insert(tk.END, "\n🔻 ANTONYMS:\n", "bold")
    result_text.insert(tk.END, (", ".join(data["antonyms"]) if data["antonyms"] else "None") + "\n")

# ---------- UI ----------
window = tk.Tk()
window.title("Advanced English Dictionary")
window.geometry("800x600")
window.resizable(False, False)

frame = tk.Frame(window)
frame.pack(pady=10)

tk.Label(frame, text="Enter a Word:", font=("Arial", 14)).grid(row=0, column=0, padx=5)
entry = tk.Entry(frame, font=("Arial", 14), width=25)
entry.grid(row=0, column=1, padx=5)

tk.Button(frame, text="🔍 Search", font=("Arial", 12), command=get_word_data).grid(row=0, column=2, padx=5)
#tk.Button(frame, text="🔊 Pronounce", font=("Arial", 12), command=speak_word).grid(row=0, column=3, padx=5)

result_text = scrolledtext.ScrolledText(window, font=("Arial", 12), wrap=tk.WORD, width=90, height=25)
result_text.pack(padx=10, pady=10)

window.mainloop()
