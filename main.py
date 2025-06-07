import os
from flask import Flask, render_template, request, jsonify, Response, stream_with_context, send_file, url_for, send_from_directory
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI
import json
import time
import io
from pathlib import Path
import random

# Load environment variables
load_dotenv()

# Initialise OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialise Flask
app = Flask(__name__, 
    static_url_path='/static',
    static_folder='static'
)

# Load question bank
print("[Debug] Loading question bank...")
with open('ks2_question_bank.json', 'r') as f:
    question_bank = json.load(f)
print(f"[Debug] Question bank loaded with topics: {list(question_bank.keys())}")
print(f"[Debug] Number of questions in Image Questions: {len(question_bank.get('Image Questions', []))}")

# Add debug route for static files
@app.route('/debug/static/<path:filename>')
def debug_static(filename):
    print(f"[Debug] Attempting to serve static file: {filename}")
    return send_from_directory(app.static_folder, filename)

# Mindy's voice settings
MINDY_VOICE = "sage"  # Using sage voice as it's more cheerful
MINDY_INSTRUCTIONS = """Affect/personality: A warm and encouraging maths helper for children
Tone: Friendly, clear, and reassuring, making the student feel confident and comfortable
Pronunciation: Clear, articulate, and steady, ensuring each explanation is easily understood
Pause: Brief, purposeful pauses after key points to allow time for the student to process the information
Emotion: Warm and supportive, conveying empathy and care, ensuring the student feels guided and safe"""

def get_random_question(topic):
    """Get a random question from the specified topic."""
    print(f"[Debug] Looking for topic: '{topic}'")
    print(f"[Debug] Available topics: {list(question_bank.keys())}")
    if topic in question_bank:
        questions = question_bank[topic]
        print(f"[Debug] Found {len(questions)} questions for topic '{topic}'")
        if len(questions) > 0:
            print(f"[Debug] First question in list: {questions[0]}")
            question = random.choice(questions)
            print(f"[Debug] Selected question: {question}")
            if isinstance(question, dict):
                print(f"[Debug] Question has image: {question.get('image')}")
                print(f"[Debug] Question text: {question.get('question')}")
            return question
        else:
            print(f"[Debug] No questions found in topic '{topic}'")
            return None
    print(f"[Debug] Topic not found in question bank")
    return None

@app.route("/speak", methods=["POST"])
def speak():
    try:
        data = request.get_json()
        text = data.get("text")
        if not text:
            print("[Mindy Voice] No text provided in request")
            return jsonify({"error": "No text provided"}), 400

        print(f"[Mindy Voice] Attempting to generate speech for: {text[:50]}...")
        
        # Create a temporary file path
        speech_file_path = Path("temp_speech.mp3")
        
        # Generate and save the speech
        with client.audio.speech.with_streaming_response.create(
            model="gpt-4o-mini-tts",
            voice=MINDY_VOICE,
            input=text,
            instructions=MINDY_INSTRUCTIONS,
        ) as response:
            response.stream_to_file(speech_file_path)
        
        print("[Mindy Voice] Speech generated successfully")
        
        # Send the file
        return send_file(
            speech_file_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='response.mp3'
        )

    except Exception as e:
        print(f"[Mindy Voice Error] {str(e)}")
        print(f"[Mindy Voice Error] Full error details: {type(e).__name__}")
        return jsonify({"error": str(e)}), 500

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/solve", methods=["POST"])
def solve():
    data = request.get_json()
    conversation = data.get("conversation", [])
    topic = data.get("topic", "")
    
    print(f"[Debug] Received topic: '{topic}'")
    print(f"[Debug] Conversation length: {len(conversation)}")

    def generate():
        try:
            # Send thinking state
            yield json.dumps({"type": "thinking", "content": "Thinking..."}) + "\n"
            
            # If this is a topic selection, get a random question
            if topic and len(conversation) == 1:
                print(f"[Debug] Getting question for topic: '{topic}'")
                # Always use the question bank for Image Questions
                if topic == "Image Questions":
                    question = get_random_question(topic)
                    print(f"[Debug] Question returned: {question}")
                    if question and isinstance(question, dict):
                        question_text = question["question"]
                        image_url = question.get("image_url")
                        print(f"[Debug] Image URL: {image_url}")
                        response_text = f"Here's a question about {topic}:\n\n"
                        if image_url:
                            image_url = url_for('static', filename=image_url).replace(' ', '%20')
                            response_text += f"![Question Image]({image_url})\n\n"
                            print(f"[Debug] Final image URL: {image_url}")
                        response_text += f"**{question_text}**\n\nWould you like to try and answer this one, or do you need more help?"
                    else:
                        response_text = f"I'm sorry, I don't have any image questions prepared yet. Would you like to try a different topic?"
                else:
                    question = get_random_question(topic)
                    if question:
                        if isinstance(question, dict):
                            question_text = question["question"]
                            image_url = question.get("image_url")
                            response_text = f"Here's a question about {topic}:\n\n"
                            if image_url:
                                image_url = url_for('static', filename=image_url).replace(' ', '%20')
                                response_text += f"![Question Image]({image_url})\n\n"
                            response_text += f"**{question_text}**\n\nWould you like to try and answer this one, or do you need more help?"
                        else:
                            response_text = f"Here's a question about {topic}:\n\n**{question}**\n\nWould you like to try and answer this one, or do you need more help?"
                    else:
                        response_text = f"I'm sorry, I don't have any questions prepared for {topic} yet. Would you like to try a different topic?"
            else:
                # For non-topic selection or follow-up questions, use the AI
                response = client.responses.create(
                    model="gpt-4.1",
                    instructions=(
                        "You are Mindy Maths Bot, a warm and encouraging maths helper for a 9-year-old UK student. "
                        "You never give the final answer directly. Instead, you help the user work it out through hints and questions. "
                        "If the student gives a correct answer, celebrate warmly — then offer to try another question or move on. "
                        "Avoid asking for the answer again once it has been correctly given.\n\n"
                        "Format your responses in a clear, easy-to-read way:\n"
                        "- Add **two newlines** between bullet points or steps\n"
                        "- Use bullet points (•) for steps or hints\n"
                        "- Keep paragraphs short (1–2 sentences max)\n"
                        "- Use 🌟 for praise and 💡 for hints, but not in every sentence\n"
                        "- Use bold for numbers or key words"
                    ),
                    input=conversation
                )
                response_text = response.output_text.strip()

            # Send the full response for voice generation first
            yield json.dumps({"type": "full_hint", "content": response_text}) + "\n"
            
            # Add a small delay to allow voice generation to start
            time.sleep(0.2)  # Reduced delay
            
            # Stream the text word by word
            words = response_text.split()
            for word in words:
                yield json.dumps({"type": "word", "content": word}) + "\n"
                time.sleep(0.1)  # Reduced delay for better synchronization
            
            # Send completion signal
            yield json.dumps({"type": "complete"}) + "\n"

        except Exception as e:
            print(f"[Mindy Voice Error] {str(e)}")
            print(f"[Mindy Voice Error] Full error details: {type(e).__name__}")
            yield json.dumps({"type": "error", "content": f"Oops, something went wrong: {e}"}) + "\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)
