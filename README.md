# VocabuRex Chatbot Service

🤖 AI-powered vocabulary learning chatbot service built with FastAPI and Google Gemini API.

## Features

- **Real AI Integration**: Uses Google Gemini API (NO MOCK DATA)
- **Clean Architecture**: Maintainable and scalable code structure  
- **Deep Link Support**: Seamless integration with Flutter app
- **Vocabulary-Focused**: Specialized prompts for English learning
- **Conversation Management**: Persistent chat sessions with context
- **Docker Ready**: Easy deployment and scaling

## Quick Start

### Prerequisites

- Python 3.8+
- Docker (optional)
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### 1. Environment Setup

```bash
# Clone and navigate
cd vocabu-rex-chatbot-service

# Copy environment template
cp .env.example .env

# Edit .env file and add your Gemini API key
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m uvicorn src.main:app --host 0.0.0.0 --port 3006 --reload

# API Documentation available at: http://localhost:8000/docs
```

### 3. Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Check service health
curl http://localhost:8000/api/v1/chat/health
```

## API Endpoints

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/chat/start` | Start new conversation |
| POST | `/api/v1/chat/message` | Send message and get AI response |
| GET | `/api/v1/chat/conversation/{id}/history` | Get conversation history |
| GET | `/api/v1/chat/health` | Health check |

### Deep Link Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/deeplink/vocabulary` | Handle vocabulary word assistance |
| POST | `/api/v1/deeplink/process` | Process general deep links |

## Usage Examples

### 1. Start a Conversation

```bash
curl -X POST "http://localhost:8000/api/v1/chat/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "initial_message": "Hello! I need help learning vocabulary."
  }'
```

### 2. Send a Message

```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What does the word '\''serendipity'\'' mean?",
    "conversation_id": "conversation-uuid",
    "context": {
      "learning_level": "intermediate"
    }
  }'
```

### 3. Vocabulary Deep Link

```bash
curl -X POST "http://localhost:8000/api/v1/deeplink/vocabulary" \
  -H "Content-Type: application/json" \
  -d '{
    "word": "magnificent",
    "definition": "extremely beautiful or impressive",
    "user_question": "Can you give me more examples and help me remember this word?",
    "difficulty_level": "advanced"
  }'
```

## Flutter Integration

### Deep Link Configuration

Add to your Flutter app's `android/app/src/main/AndroidManifest.xml`:

```xml
<activity
    android:name=".MainActivity"
    android:exported="true">
    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="vocaburex" 
              android:host="chatbot" />
    </intent-filter>
</activity>
```

### Flutter Code Example

```dart
// Send user to chatbot with vocabulary word
String deepLink = "vocaburex://chatbot/vocabulary?word=beautiful&question=pronunciation";
if (await canLaunchUrl(Uri.parse(deepLink))) {
  await launchUrl(Uri.parse(deepLink));
}

// Handle API calls
Future<Map<String, dynamic>> sendMessage(String message) async {
  final response = await http.post(
    Uri.parse('http://localhost:8000/api/v1/chat/message'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'message': message,
      'user_id': 'current_user_id',
    }),
  );
  return jsonDecode(response.body);
}
```

## Architecture

```
src/
├── domain/          # Business entities & repository interfaces
│   ├── entities/    # Message, Conversation entities
│   └── repositories/ # Repository abstractions
├── application/     # Use cases & DTOs
│   ├── dtos/        # Request/Response models
│   └── use_cases/   # Business logic
├── infrastructure/  # External dependencies
│   ├── external/    # Gemini AI service
│   └── repositories/ # In-memory implementations
├── presentation/    # FastAPI controllers
│   └── controllers/ # Chat & Deep Link endpoints
├── core/           # Exceptions & shared logic
└── shared/         # Configuration & utilities
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | **Required** Google Gemini API key | - |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |
| `SERVICE_PORT` | Service port | `8000` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000,http://localhost:8080` |

## Production Deployment

### 1. Docker Production

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  chatbot-service:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    restart: unless-stopped
```

### 2. Health Monitoring

```bash
# Check service status
curl http://localhost:8000/api/v1/chat/health

# Expected response:
{
  "status": "healthy",
  "service": "vocabu-rex-chatbot-service",
  "version": "1.0.0",
  "gemini_api_status": "healthy"
}
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Code Quality

```bash
# Format code
black src/

# Sort imports
isort src/

# Lint
flake8 src/
```

## Troubleshooting

### Common Issues

1. **Gemini API Key Error**
   ```
   GeminiAPIException: Gemini API key not configured
   ```
   **Solution**: Set `GEMINI_API_KEY` in `.env` file

2. **Import Error**
   ```
   ModuleNotFoundError: No module named 'google.generativeai'
   ```
   **Solution**: `pip install google-generativeai`

3. **CORS Error**
   ```
   Access to fetch blocked by CORS policy
   ```
   **Solution**: Update `ALLOWED_ORIGINS` in `.env`

### Logs

```bash
# Docker logs
docker-compose logs -f chatbot-service

# Local development logs appear in console
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Contributing

1. Follow Clean Architecture principles
2. Add tests for new features
3. Update documentation
4. Use conventional commit messages

## License

This project is part of the VocabuRex ecosystem.