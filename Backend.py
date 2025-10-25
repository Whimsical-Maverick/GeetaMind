#Nessecary Imports
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from pydantic import BaseModel
from google import genai
from google.genai import types
import wave
from sentence_transformers import SentenceTransformer, util
import os
import uuid
from dotenv import load_dotenv
import sqlite3

#Initializing the app
app = FastAPI()
load_dotenv()
api_key = os.getenv("Google_API_KEY")
sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
DB_PATH = os.path.join(BASE_DIR, "Complete_Results_DB.db")

EMOTION_MAP = {
    # "Simple Label (for DB)" : "Descriptive Text (for AI)"
    "admiration": "a feeling of admiration or deep respect",
    "adoration": "a feeling of deep love and adoration",
    "aesthetic appreciation": "appreciating something for its beauty",
    "amusement": "a feeling of amusement or finding something funny",
    "anger": "a feeling of anger, rage, or frustration",
    "anxiety": "a feeling of anxiety, worry, or nervousness",
    "awe": "a feeling of awe or wonder",
    "awkwardness": "a feeling of awkwardness or social discomfort",
    "boredom": "a feeling of boredom and lack of interest",
    "calmness": "a feeling of calmness, peace, or serenity",
    "confusion": "a feeling of confusion or being unsure",
    "craving": "a strong desire or craving for something",
    "disgust": "a feeling of disgust or revulsion",
    "empathic pain": "feeling pain on behalf of someone else",
    "entrancement": "a feeling of being entranced or fascinated",
    "excitement": "a feeling of excitement or anticipation",
    "fear": "a feeling of fear or being scared",
    "horror": "a feeling of horror or terror",
    "interest": "a feeling of interest or curiosity",
    "joy": "a feeling of joy, happiness, or elation",
    "nostalgia": "a feeling of nostalgia for the past",
    "relief": "a feeling of relief after a difficult situation",
    "sadness": "a feeling of sadness, grief, or depression",
    "satisfaction": "a feeling of satisfaction or contentment",
    "surprise": "a feeling of surprise or shock"
}

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def get_verses_by_emotions(emotions,number_of_verses_per_emotion) -> list:
    print(emotions)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    resultant_verses=[]
    for emotion in emotions:
        cursor.execute(f"SELECT Verse_Text FROM Verse_Db WHERE Labels LIKE '%{emotion}%' ORDER BY RANDOM() LIMIT {number_of_verses_per_emotion}")
        verses = [v[0] for v in cursor.fetchall()]
        resultant_verses.extend(verses)
    print(resultant_verses)
    conn.close()
    return resultant_verses

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
   with wave.open(filename, "wb") as wf:
      wf.setnchannels(channels)
      wf.setsampwidth(sample_width)
      wf.setframerate(rate)
      wf.writeframes(pcm)

class TextData(BaseModel):
    content:str

@app.get("/get_question_home_page")
def get_question_home_page(request: Request):
    return templates.TemplateResponse("Byquestion.html", {"request": request})


@app.post("/get-by-question")
def get_by_question(data:TextData):
   question = data.content
   print(f"Received question: {question}")
   simple_labels = list(EMOTION_MAP.keys())
   descriptive_labels = list(EMOTION_MAP.values())
   question_embedding = sbert_model.encode(question, convert_to_tensor=True)
   label_embeddings = sbert_model.encode(descriptive_labels, convert_to_tensor=True)
   cosine_scores = util.pytorch_cos_sim(question_embedding, label_embeddings)
   label_scores = list(zip(simple_labels, cosine_scores[0]))
   label_scores.sort(key=lambda x: x[1].item(), reverse=True)
   reqd_labels = []
   threshold = 0.1
   for label, score in label_scores:
        print(f"Checking label '{label}' with score {score.item():.4f}") 
        if len(reqd_labels) < 5 and score.item() > threshold:
            print(f"Semantic similarity between '{question}' and '{label}': {score:.4f}")
            reqd_labels.append(label)
        elif len(reqd_labels) >= 5:
            break
   if(len(reqd_labels) == 0):
        reqd_labels.append('Neutral')
   verses = get_verses_by_emotions(reqd_labels, 5)
   if not api_key:
        raise ValueError("API key not found. Please check your .env file.")
   client = genai.Client(api_key = api_key)
   response = client.models.generate_content(
       model = "gemini-2.5-flash",
       config= types.GenerateContentConfig(
              temperature=0.3,
              system_instruction = f"""Your Persona: You are a wise and compassionate guide, embodying the timeless wisdom of the Bhagavad Gita.

Your Task: Answer questions from a user who is seeking guidance using all the verses from the list {verses}.

Key Instructions:

Address the User: Always begin your response by addressing the user as 'My child,' or 'Dear child,' or something like that.

Source of Knowledge: Your answers must be based exclusively on the teachings, verses, and philosophy of the Bhagavad Gita.

Tone: Your tone should be patient, reassuring, and full of gentle wisdom.

Constraint: Do not give modern advice, personal opinions, or act like a generic AI. You are the serene voice of ancient scripture."""     
       ),
       contents = question)
   return {'content': response.text}

@app.post("/text-to-speech")
def text_to_speech(data:TextData):
   client = genai.Client(api_key = api_key)
   response = client.models.generate_content(
   model="gemini-2.5-flash-preview-tts",
   contents=data.content ,
   config=types.GenerateContentConfig(
      response_modalities=["AUDIO"],
      speech_config=types.SpeechConfig(
         voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
               voice_name='Zephyr',
            )
         )
      ),
   )
)
   data = response.candidates[0].content.parts[0].inline_data.data
   file_name = f"static/{uuid.uuid4()}.wav"
   wave_file(file_name, data)
   return {"filename":"/"+file_name}

@app.get("/get_emotion_home_page")
def get_emotion_home_page(request: Request):
    return templates.TemplateResponse("Byemotion.html", {"request": request})

@app.get("/get-by-emotion")
def get_by_emotion(emotion: str):
    verses = get_verses_by_emotions([emotion], 10)
    return {"verses": verses}
