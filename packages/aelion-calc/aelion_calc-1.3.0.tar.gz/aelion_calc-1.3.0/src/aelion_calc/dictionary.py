import urllib.request
import json
import textwrap
from .say import say, box, loading

def define(word):
    """
    Fetches the definition, part of speech, and examples for a word.
    Usage: dictionary.define("hello")
    """
    # 1. Show loading animation because network takes time
    loading(1.5, f"Searching for '{word}'", color="cyan")
    
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    
    try:
        # 2. Fetch Data
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            
        # 3. Parse Data (The API returns a list)
        entry = data[0]
        word_text = entry.get('word', word).capitalize()
        phonetic = entry.get('phonetic', '')
        
        # Prepare content for the Box
        content = []
        if phonetic:
            content.append(f"Pronunciation: {phonetic}")
            content.append("-" * 20)
        
        # Loop through meanings (Noun, Verb, etc.)
        for meaning in entry.get('meanings', []):
            part_of_speech = meaning.get('partOfSpeech', 'unknown').upper()
            content.append(f"[{part_of_speech}]")
            
            # Get first 2 definitions to keep it clean
            for i, definition in enumerate(meaning.get('definitions', [])[:2]):
                defi = definition.get('definition', '')
                example = definition.get('example', '')
                
                # Wrap text so it fits in the box
                wrapped_def = textwrap.fill(f"{i+1}. {defi}", width=50)
                content.append(wrapped_def)
                
                if example:
                    wrapped_ex = textwrap.fill(f"   Ex: \"{example}\"", width=50)
                    content.append(wrapped_ex)
            
            content.append("") # Empty line between sections

        # 4. Display Result
        box(content, title=word_text, color="green")

    except urllib.error.HTTPError:
        say(f"Error: The word '{word}' was not found in the dictionary.", color="red")
    except Exception as e:
        say(f"Connection Error: {e}", color="red")