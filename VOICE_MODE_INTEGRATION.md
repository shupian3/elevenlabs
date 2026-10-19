# Voice-Mode Integration Guide

This guide shows you how to integrate the ElevenLabs OpenAI Proxy with the [voice-mode MCP server](https://github.com/mbailey/voicemode) for Claude Code.

## What This Enables

With this integration, you can use ElevenLabs voices for text-to-speech in voice conversations with Claude Code, while keeping Whisper for speech-to-text. This gives you:

- High-quality, natural-sounding voices from ElevenLabs
- Full OpenAI API compatibility
- Automatic voice discovery and selection
- Seamless switching between local and cloud TTS providers

## Quick Setup

### 1. Start the ElevenLabs Proxy

```bash
cd elevenlabs-openai-proxy
make start
```

The proxy will start on `http://localhost:8000` by default.

### 2. Configure Voice-Mode

Add the proxy URL to your voice-mode configuration. You have two options:

#### Option A: Using Environment Variables

```bash
export VOICEMODE_TTS_BASE_URLS="http://localhost:8000/v1,http://127.0.0.1:8880/v1"
export VOICEMODE_VOICES="eve,bf_lily(3)+af_nicole(3)+bf_emma(1)"
```

#### Option B: Using Configuration File

Edit `~/.voicemode/voicemode.env`:

```bash
# TTS Provider Configuration
VOICEMODE_TTS_BASE_URLS=http://localhost:8000/v1,http://127.0.0.1:8880/v1

# Voice Preferences (voice-mode will try these in order)
VOICEMODE_VOICES=eve,bf_lily(3)+af_nicole(3)+bf_emma(1)

# Optional: Prefer local providers (ElevenLabs proxy) over cloud
VOICEMODE_PREFER_LOCAL=true
```

### 3. Test Without Restart

The proxy now supports **hot-reload** - voice configuration changes are picked up automatically! No need to restart the proxy server when you update voice mappings in `.env`.

### 4. Test the Integration

Start a voice conversation in Claude Code:

```
converse
```

Voice-mode will automatically detect the ElevenLabs proxy and use it for TTS generation!

## Voice Mapping

The proxy **dynamically discovers** voice mappings from environment variables. Any environment variable starting with `VOICE_` in the proxy's `.env` file will be automatically registered as a voice.

This means you have complete control over which voices are available and what they're called!

## Custom Voice Configuration

### Using Your Own ElevenLabs Voices

You can create custom voice mappings using environment variables:

1. Get your voice ID from [ElevenLabs Voice Lab](https://elevenlabs.io/voice-lab)

2. Configure the mapping in the proxy's `.env` file:

```bash
# Create a custom voice called "eve"
VOICE_EVE=2XA8XjaNwPD3cCxrLG5K

# Add more custom voices
VOICE_SARAH=another_voice_id_here
VOICE_JOHN=yet_another_voice_id
```

3. **No restart needed!** The proxy automatically picks up changes on the next request.

4. Use the custom voice in voice-mode:

```bash
# ~/.voicemode/voicemode.env
VOICEMODE_VOICES=eve,sarah,john
```

### Using ElevenLabs Voice IDs Directly

You can also use ElevenLabs voice IDs directly in voice-mode:

```bash
# Configure voice-mode to use specific ElevenLabs voice IDs
VOICEMODE_VOICES=2XA8XjaNwPD3cCxrLG5K,another_voice_id_here
```

The proxy will recognize these as ElevenLabs voice IDs (alphanumeric, typically 20 characters) and use them directly.

## Advanced Configuration

### Running Multiple TTS Providers

Voice-mode supports multiple TTS endpoints with automatic failover:

```bash
# Try ElevenLabs first, fall back to Kokoro
export VOICEMODE_TTS_BASE_URLS="http://localhost:8000/v1,http://localhost:8880/v1"

# Voice preferences (voice-mode picks the first available)
export VOICEMODE_VOICES="eve,bf_lily(3)+af_nicole(3)+bf_emma(1)"
```

Voice-mode will:
1. Check if ElevenLabs proxy has "eve" voice → Use it
2. If not, check if Kokoro has the blended voice → Use it

### Managing the Proxy as a Service

For production use, you may want to run the proxy as a systemd service or launchd agent.

#### macOS (launchd)

Create `~/Library/LaunchAgents/com.elevenlabs.proxy.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.elevenlabs.proxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/workspace/personal/elevenlabs-openai-proxy/venv/bin/python</string>
        <string>/Users/YOUR_USERNAME/workspace/personal/elevenlabs-openai-proxy/server.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/workspace/personal/elevenlabs-openai-proxy/server.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/workspace/personal/elevenlabs-openai-proxy/server.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ELEVENLABS_API_KEY</key>
        <string>YOUR_API_KEY_HERE</string>
    </dict>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.elevenlabs.proxy.plist
```

#### Linux (systemd)

Create `~/.config/systemd/user/elevenlabs-proxy.service`:

```ini
[Unit]
Description=ElevenLabs OpenAI Proxy
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/YOUR_USERNAME/workspace/personal/elevenlabs-openai-proxy
ExecStart=/home/YOUR_USERNAME/workspace/personal/elevenlabs-openai-proxy/venv/bin/python server.py
Restart=always
Environment="ELEVENLABS_API_KEY=YOUR_API_KEY_HERE"

[Install]
WantedBy=default.target
```

Enable and start:

```bash
systemctl --user daemon-reload
systemctl --user enable elevenlabs-proxy
systemctl --user start elevenlabs-proxy
```

## Troubleshooting

### Voice-Mode Not Using ElevenLabs

1. **Check proxy is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check voice-mode configuration**:
   ```bash
   uv tool run voice-mode config list | grep TTS
   ```

3. **Check voice-mode logs**:
   Look for "TTS Provider Selection" messages to see which provider was chosen.

### Proxy Errors

1. **Check API key**:
   ```bash
   grep ELEVENLABS_API_KEY ~/workspace/personal/elevenlabs-openai-proxy/.env
   ```

2. **Check logs**:
   ```bash
   tail -f ~/workspace/personal/elevenlabs-openai-proxy/server.log
   ```

3. **Test directly**:
   ```bash
   curl -X POST http://localhost:8000/v1/audio/speech \
     -H "Content-Type: application/json" \
     -d '{"input": "Test", "voice": "jessica"}' \
     --output test.mp3
   ```

## Performance Tips

1. **Use local proxy for low latency**: The proxy adds minimal overhead (~50-100ms) compared to calling ElevenLabs directly.

2. **Turbo model for speed**: Use `tts-1` model (maps to ElevenLabs Turbo v2.5) for faster generation.

3. **Configure voice preferences**: Put your most-used voices first in `VOICEMODE_VOICES` for faster selection.

## Contributing

Found a bug or have a suggestion? Please open an issue or PR on the [GitHub repository](https://github.com/yourusername/elevenlabs-openai-proxy).

## Related Projects

- [voice-mode](https://github.com/mbailey/voicemode) - Voice Mode MCP server for Claude Code
- [elevenlabs-python](https://github.com/elevenlabs/elevenlabs-python) - Official ElevenLabs Python SDK
