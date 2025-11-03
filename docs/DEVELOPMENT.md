# Development Notes

## AI Models Setup

### Required Ollama Models
```bash
ollama pull llama2:13b          # Main chat model
ollama pull phi4-reasoning:14b  # Reasoning/brains model
ollama pull llava:13b           # Image understanding model
```

### Optional Models
```bash
# Image generation (currently disabled)
pip install ollamadiffuser
ollamadiffuser pull city96/FLUX.1-schnell-gguf:Q4_K_M

# Set HuggingFace token for image generation
echo $env:HUGGINGFACE_HUB_TOKEN = "YOUR_TOKEN_HERE"
```

### TTS Setup
```bash
pip install piper-tts
# Voice models are downloaded automatically or can be placed in application/sound/
```

## Environment Variables

Create `application/.env`:
```env
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_CHAT_MODEL=llama2:13b
OLLAMA_REASON_MODEL=phi4-reasoning:14b
OLLAMA_VISION_MODEL=llava:13b
HUGGINGFACE_HUB_TOKEN=your_token_here
```

## Application Features

### Current Status
- ✅ **Text Chat**: Working with llama2:13b and phi4-reasoning:14b
- ✅ **Image Understanding**: Working with llava:13b
- ✅ **User Management**: Cookie-based UUID sessions with SQLite storage
- ✅ **Admin Panel**: View chat logs, manage users, export CSV
- ✅ **UI/UX**: Modern responsive design with avatars and accessibility
- ⚠️ **TTS**: Piper TTS implemented but may return nonsensical output
- ⚠️ **STT**: OpenAI Whisper implemented but may have issues
- ❌ **Image Generation**: OllamaDiffuser setup but disabled for focus on TTS/STT

### Database Schema
- `users` table: id (UUID), info (optional user data)
- `events` table: event_id, user_id, event_type, content, timestamp

### Cookie System
- `user_id`: UUID for session tracking (HttpOnly)
- `consent`: User cookie consent preference
- Automatic user creation on first visit with consent

## Development Commands

### Running the Application
```bash
# From repository root
python run.py

# From application directory
python app.py
# or
flask --app app run --debug
```

### Testing Routes
- `/clear_cookies` - Development helper to reset user session
- `/admin` - Admin panel (requires user session)
- `/admin/users` - JSON list of all users
- `/admin/export` - Export user chat logs as CSV

## Code Architecture

### Backend Structure
- `app.py`: Flask routes and main application logic
- `functions/AI_handler.py`: AI model interactions and processing
- `functions/db_handler.py`: Database operations and user management
- `functions/cookie_handler.py`: Cookie consent and session management

### Frontend Structure
- `templates/`: Jinja2 HTML templates (no inline JS)
- `static/js/`: Modular JavaScript files
- `static/css/`: Stylesheets
- `static/img/`: Images and favicons

### Key Design Decisions
- UUID-based user identification with cookie consent
- SQLite for simplicity and portability
- Modular JavaScript to avoid inline script clutter
- Separation of concerns between routes, handlers, and templates

## Known Issues & TODO

### Current Issues
- TTS output may be nonsensical - needs voice model verification
- STT functionality may have processing issues

### Future Enhancements
- Improve TTS voice quality and model selection
- Enhance STT accuracy and noise handling
- Implement chat export in multiple formats
- Add conversation threading/tagging

## Testing Checklist

### Core Functionality
- [ ] User creation and cookie consent flow
- [ ] Basic text chat with LLM
- [ ] Image upload and analysis
- [ ] Admin panel access and log viewing
- [ ] Data export functionality
- [ ] Voice input/output (when enabled)

### UI/UX Testing
- [ ] Responsive design on mobile/desktop
- [ ] Accessibility features (ARIA labels, keyboard navigation)
- [ ] Cookie consent banner behavior
- [ ] Error handling and user feedback

### Performance
- [ ] Chat response times
- [ ] Image processing speed
- [ ] Database query performance
- [ ] Memory usage with large chat histories