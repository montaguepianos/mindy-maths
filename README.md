# Mindy Maths Bot

A friendly and interactive maths helper bot for Key Stage 2 students (Years 5 & 6). Mindy provides engaging maths questions with visual aids and step-by-step guidance.

## Features

- Interactive chat interface
- Voice responses using OpenAI's text-to-speech
- Visual questions with images
- Topic-based question selection
- Step-by-step problem-solving guidance
- Warm and encouraging teaching style

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mindy-maths.git
cd mindy-maths
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

5. Run the application:
```bash
python main.py
```

The application will be available at http://127.0.0.1:5050

## Project Structure

- `main.py`: Flask application and OpenAI integration
- `templates/index.html`: Frontend interface
- `static/images/`: Question images
- `KS2_question_bank.json`: Question database
- `requirements.txt`: Python dependencies

## Contributing

Feel free to submit issues and enhancement requests! 