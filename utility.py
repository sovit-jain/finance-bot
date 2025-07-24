import speech_recognition as sr
from google.cloud import translate

def list_languages():
    languages = [
        ("en", "English"),
        ("hi", "Hindi"),
        ("bn", "Bengali"),
        ("ta", "Tamil"),
        ("te", "Telugu"),
        ("ml", "Malayalam"),
        ("mr", "Marathi"),
        ("gu", "Gujarati"),
        ("kn", "Kannada"),
        ("pa", "Punjabi"),
        ("ur", "Urdu"),
        ("or", "Odia"),
    ]
    print("Select your preferred language for the recommendation:")
    for i, (code, name) in enumerate(languages, start=1):
        print(f"{i}. {name} ({code})")
    return languages

def get_input_with_mode(mode, prompt):
    """
    Get input based on selected mode "text" or "voice".
    For voice, retries 3 times before fallback.
    """
    if mode == "text":
        return input(prompt)
    elif mode == "voice":
        for _ in range(3):  # attempt 3 times
            spoken = get_voice_input(prompt)
            if spoken:
                return spoken
            print("Please try again.")
        print("Fallback to text input.")
        return input(prompt)
    else:
        return input(prompt)
    
def get_voice_input(prompt="Please say your input after the beep:"):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print(prompt)
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text.lower()
    except sr.UnknownValueError:
        print("Sorry, could not understand audio.")
        return None
    except sr.RequestError:
        print("Speech recognition service error.")
        return None
    
def translate_text(text, target_language_code, project_id):
    client = translate.TranslationServiceClient()
    parent = f"projects/{project_id}/locations/global"
    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",
            "target_language_code": target_language_code,
        }
    )
    return response.translations[0].translated_text

def get_language_choice(languages, input_mode):
    prompt = "Enter the number or language code (e.g., '1' or 'hi'): "
    choice = get_input_with_mode(input_mode, prompt).strip().lower()
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(languages):
            return languages[idx][0]
    for code, _ in languages:
        if choice == code:
            return code
    print("Invalid choice, defaulting to English ('en').")
    return "en"

