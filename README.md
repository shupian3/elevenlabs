# ElevenLabs OpenAI-Compatible TTS Proxy

A FastAPI-based proxy server that provides an OpenAI-compatible `/v1/audio/speech` endpoint backed by ElevenLabs text-to-speech API. This allows you to use ElevenLabs voices in any application that supports the OpenAI TTS API format.

## Features

- **OpenAI API Compatibility**: Drop-in replacement for OpenAI's `/v1/audio/speech` endpoint
- **✨ Free Tier PCM Support**: Automatic real-time MP3→PCM transcoding using ffmpeg for free/starter tier compatibility
- **Dynamic Voice Mapping**: Automatically discovers and maps custom voices from environment variables
- **Hot-Reload Configuration**: Voice mappings update automatically without server restart
- **Custom Voice Support**: Use any ElevenLabs voice ID directly
- **Streaming Audio**: Efficient async streaming response for real-time playback
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Voice Mode Compatible**: Works seamlessly with voice-mode MCP server and other OpenAI-compatible clients

## Why This Proxy?

**The Problem**: ElevenLabs free and starter tiers only support MP3 audio output, but many voice applications (like voice-mode, voice assistants, and real-time streaming clients) require PCM format for low-latency playback.

**The Solution**: This proxy automatically transcodes MP3 to PCM in real-time using async ffmpeg streaming when clients request PCM format, making ElevenLabs free tier compatible with any OpenAI TTS client.

**Key Benefits**:
- ✅ Use ElevenLabs voices with free tier in PCM-only clients
- ✅ Zero configuration - automatic format detection and transcoding
- ✅ Low latency - async streaming architecture
- ✅ Seamless fallback - MP3 requests stream directly without transcoding

## Quick Start

### Prerequisites

- Python 3.9 or higher
- ElevenLabs API key ([Get one here](https://elevenlabs.io/))
- ffmpeg (for PCM transcoding) - install via: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dotCipher/elevenlabs-openai-proxy.git
   cd elevenlabs-openai-proxy
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your ELEVENLABS_API_KEY
   ```

4. **Run the server**:
   ```bash
   # Development mode (with auto-reload)
   make dev

   # Or production mode (background)
   make start
   ```

The server will start on `http://localhost:8000`. Visit `http://localhost:8000/docs` for interactive API documentation.

### Management Commands

```bash
make help       # Show all available commands
make start      # Start server in background
make stop       # Stop running server
make restart    # Restart server
make dev        # Run in development mode with auto-reload
make clean      # Clean up temporary files
```

## Usage

### Basic Example

Using `curl`:

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello! This is a test of the ElevenLabs OpenAI proxy.",
    "voice": "jessica",
    "model": "tts-1"
  }' \
  --output speech.mp3
```

### Using with OpenAI Python SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy-key",  # Not used but required by SDK
    base_url="http://localhost:8000/v1"
)

response = client.audio.speech.create(
    model="tts-1",
    voice="jessica",
    input="Hello! This is a test of the ElevenLabs OpenAI proxy."
)

response.stream_to_file("output.mp3")
```

### Using with Voice-Mode MCP Server

Add the proxy URL to your voice-mode configuration:

```bash
# Add to your ~/.voicemode/voicemode.env
VOICEMODE_TTS_BASE_URLS=http://localhost:8000/v1,http://127.0.0.1:8880/v1
VOICEMODE_VOICES=jessica,bf_lily(3)+af_nicole(3)+bf_emma(1)
```

Now voice-mode will automatically use ElevenLabs for TTS when the selected voice is available!

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ELEVENLABS_API_KEY` | Your ElevenLabs API key | Required |
| `HOST` | Server host address | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `ELEVENLABS_DEFAULT_VOICE_ID` | Default voice ID when no mapping found | First `VOICE_*` variable or jessica's ID |
| `VOICE_*` | Custom voice mappings (e.g., `VOICE_SARAH=voice_id`) | Dynamically discovered |

### Voice Mapping

The proxy **dynamically discovers** voice mappings from environment variables. Any environment variable starting with `VOICE_` will be automatically registered as a voice.

**Example: Adding a custom voice**

In your `.env` file:

```bash
# Map custom voice name "sarah" to your ElevenLabs voice ID
VOICE_SARAH=your_elevenlabs_voice_id_here
```

Now you can use it:

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello!",
    "voice": "sarah",
    "model": "tts-1"
  }' \
  --output speech.mp3
```

**Multiple voices**:

```bash
VOICE_SARAH=your_voice_id_here
VOICE_ALICE=another_voice_id_here
VOICE_JOHN=yet_another_voice_id
```

**Hot-reload**: Changes to `.env` are picked up automatically on the next request - **no server restart needed!**

**Direct voice IDs**: You can also pass an ElevenLabs voice ID directly in the API request:

```bash
curl -X POST http://localhost:8000/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "input": "Hello!",
    "voice": "your_elevenlabs_voice_id_here",
    "model": "tts-1"
  }' \
  --output speech.mp3
```

## Docker Deployment

### Using Docker

```bash
docker build -t elevenlabs-openai-proxy .
docker run -p 8000:8000 -e ELEVENLABS_API_KEY=your_key_here elevenlabs-openai-proxy
```

### Using Docker Compose

```bash
# Edit docker-compose.yml with your API key
docker-compose up -d
```

## API Endpoints

### POST /v1/audio/speech

Generate speech from text (OpenAI-compatible).

**Request Body**:
```json
{
  "input": "Text to convert to speech",
  "voice": "jessica",
  "model": "tts-1",
  "response_format": "mp3",
  "speed": 1.0
}
```

**Parameters**:
- `input` (string, required): The text to convert to speech
- `voice` (string, optional): Voice to use (configured via `VOICE_*` env vars or direct voice ID)
- `model` (string, optional): Model to use (default: "tts-1")
  - `tts-1`: Uses ElevenLabs Turbo v2.5 (faster)
  - `tts-1-hd`: Uses ElevenLabs Multilingual v2 (higher quality)
- `response_format` (string, optional): Audio format (default: "mp3")
  - Supported: `mp3`, `wav`, `pcm`
- `speed` (float, optional): Playback speed 0.25-4.0 (default: 1.0)

**Response**: Audio file stream

### GET /v1/models

List available models (OpenAI-compatible).

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "tts-1",
      "object": "model",
      "created": 1699046015,
      "owned_by": "elevenlabs-proxy"
    },
    {
      "id": "tts-1-hd",
      "object": "model",
      "created": 1699046015,
      "owned_by": "elevenlabs-proxy"
    }
  ]
}
```

### GET /health

Health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "service": "elevenlabs-openai-proxy",
  "elevenlabs_configured": true
}
```

## Integration Examples

### Open WebUI

1. Go to Settings → Audio
2. Set TTS API Base URL: `http://localhost:8000/v1`
3. Set API Key: `dummy-key` (not used but required)
4. Select voice and test!

### Voice-Mode MCP Server

Add to your voice-mode configuration:

```bash
# ~/.voicemode/voicemode.env
VOICEMODE_TTS_BASE_URLS=http://localhost:8000/v1,http://127.0.0.1:8880/v1
VOICEMODE_VOICES=jessica,bf_lily(3)+af_nicole(3)+bf_emma(1)
```

Voice-mode will automatically discover and use ElevenLabs voices!

### Custom Applications

Any application that supports OpenAI's TTS API can use this proxy by simply changing the `base_url`:

```python
# Before: OpenAI
client = OpenAI(api_key="sk-...", base_url="https://api.openai.com/v1")

# After: ElevenLabs via proxy
client = OpenAI(api_key="dummy", base_url="http://localhost:8000/v1")
```

## Development

### Running Tests

```bash
pytest tests/
```

### Linting

```bash
ruff check .
black .
```

## Performance

- **Latency**: ~1-2 seconds for first audio chunk (depending on text length)
- **Streaming**: Audio chunks streamed as they're generated for low latency playback
- **Throughput**: Limited by ElevenLabs API rate limits

## How PCM Transcoding Works

When a client requests PCM format but ElevenLabs only supports MP3 (free/starter tier):

1. **Detection**: Proxy detects PCM format request
2. **ElevenLabs Call**: Fetches MP3 audio from ElevenLabs API
3. **Async Transcoding**: Spawns async ffmpeg process to transcode MP3→PCM
4. **Streaming**: Streams PCM data to client in real-time as transcoding happens
5. **Zero Latency**: Client starts receiving audio immediately, no buffering required

**Technical Details**:
- Output format: 16-bit signed PCM, little-endian
- Sample rate: 24kHz (OpenAI compatible)
- Channels: Mono
- Transcoding: Async subprocess with streaming I/O

## Limitations

- Requires ffmpeg for PCM transcoding (MP3 is native and requires no dependencies)
- Speed parameter is passed through but may have limited effect
- Some OpenAI-specific parameters (like `voice_instructions`) are not supported

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [ElevenLabs](https://elevenlabs.io/)
- Inspired by [Voice-Mode MCP Server](https://github.com/mbailey/voicemode)

## Support

- Issues: [GitHub Issues](https://github.com/dotCipher/elevenlabs-openai-proxy/issues)
- Discussions: [GitHub Discussions](https://github.com/dotCipher/elevenlabs-openai-proxy/discussions)

## Related Projects

- [voice-mode](https://github.com/mbailey/voicemode) - Voice conversations for Claude Code
- [openai-edge-tts](https://github.com/travisvn/openai-edge-tts) - OpenAI-compatible TTS using Microsoft Edge
