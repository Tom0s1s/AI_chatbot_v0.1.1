# AI Chatbot

A Flask-based web application for chatting with local AI models using Ollama. Features include text chat, image understanding, reasoning, and more.

## Features

- **Chat with LLM**: Interactive chat using Ollama models (e.g., llama2:13b).
- **Reasoning Mode**: Use reasoning models like phi4-reasoning:14b.
- **Image Understanding**: Analyze images with llava:13b.
- **Image Generation**: Create images with ollamadiffuser.
- **Voice Input/Output**: Record audio and generate speech with Piper TTS.
- **User Management**: Cookie-based sessions and chat history logging.
- **Admin Panel**: View and manage chat transcripts.

## Setup

### Prerequisites

- Python 3.8+
- Ollama installed and running
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd AI_Chatbot
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv application/venv
   # On Windows:
   application\venv\Scripts\activate
   # On macOS/Linux:
   source application/venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r application/requirements.txt
   ```

4. Pull Ollama models:
   ```bash
   ollama pull llama2:13b
   ollama pull phi4-reasoning:14b
   ollama pull llava:13b
   ```

5. (Optional) For image generation:
   ```bash
   pip install ollamadiffuser
   ollamadiffuser pull city96/FLUX.1-schnell-gguf:Q4_K_M
   ```

6. (Optional) For TTS:
   ```bash
   pip install piper-tts
   ```

7. Set environment variables (create `application/.env`):
   ```
   FORCE_OLLAMA_CLI=1
   OLLAMA_CHAT_MODEL=llama2:13b
   HUGGINGFACE_HUB_TOKEN=your_token_here
   ```

### Running the App

From the repository root:
```bash
python -m application.app
```

Or from `application/`:
```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Usage

- Accept cookies on first visit.
- Navigate to "Bot" for chat.
- Type messages and press Enter.
- Use reasoning mode by adding `?mode=reason` to the URL or form data.

## Project Structure

- `application/`: Main Flask app
  - `app.py`: Routes and app setup
  - `functions/`: Handlers for AI, DB, cookies
  - `templates/`: HTML templates
  - `static/`: CSS/JS assets
- `run.py`: Convenience runner
- `notes.txt`: Development notes

## Contributing

1. Fork the repo.
2. Create a feature branch.
3. Commit changes.
4. Push and create a PR.

## License

MIT License