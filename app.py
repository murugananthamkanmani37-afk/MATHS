import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import GENERATION_SETTINGS, MAX_HISTORY_MESSAGES, MAX_MESSAGE_LENGTH, MODEL_NAME, SYSTEM_PROMPT

load_dotenv()

app = Flask(__name__)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def build_contents(history, message):
    contents = []
    for item in history[-MAX_HISTORY_MESSAGES:]:
        role = "model" if item.get("role") == "model" else "user"
        text = str(item.get("text", "")).strip()
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))
    return contents


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    history = data.get("history", [])

    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"Message is too long (max {MAX_MESSAGE_LENGTH} characters)."}), 400

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=build_contents(history, message),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                **GENERATION_SETTINGS,
            ),
        )
        return jsonify({"reply": response.text or "I could not generate a response. Please try again."})
    except Exception:
        return jsonify({"error": "Something went wrong while contacting the AI. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=True)
