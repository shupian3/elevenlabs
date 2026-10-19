#!/usr/bin/env python3
"""
ElevenLabs OpenAI-Compatible TTS Proxy Server

This server provides an OpenAI-compatible /v1/audio/speech endpoint
that proxies requests to ElevenLabs TTS API.
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

import httpx
from dotenv import load_dotenv
from elevenlabs.client import AsyncElevenLabs
from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Path to .env file for dynamic reloading
ENV_FILE = Path(__file__).parent / ".env"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("elevenlabs-openai-proxy")

# Initialize FastAPI app
app = FastAPI(
    title="ElevenLabs OpenAI-Compatible TTS Proxy",
    description="OpenAI-compatible /v1/audio/speech endpoint backed by ElevenLabs",
    version="0.1.0"
)

# Get configuration from environment
def get_api_key():
    """Dynamically load API key from environment."""
    load_dotenv(ENV_FILE, override=True)
    return os.getenv("ELEVENLABS_API_KEY")

ELEVENLABS_API_KEY = get_api_key()
if not ELEVENLABS_API_KEY:
    logger.warning("ELEVENLABS_API_KEY not set. The proxy will not work without it.")


def get_voice_mapping():
    """Dynamically load voice mapping from environment variables."""
    load_dotenv(ENV_FILE, override=True)

    # Scan all environment variables for VOICE_* entries
    voice_mapping = {}
    for key, value in os.environ.items():
        if key.startswith("VOICE_") and value:
            # Extract voice name (e.g., VOICE_EVE -> eve)
            voice_name = key[6:].lower()  # Remove "VOICE_" prefix
            voice_mapping[voice_name] = value
            logger.debug(f"Loaded voice mapping: {voice_name} -> {value}")

    return voice_mapping


def get_default_voice_id():
    """Dynamically load default voice ID."""
    load_dotenv(ENV_FILE, override=True)
    return os.getenv("ELEVENLABS_DEFAULT_VOICE_ID", os.getenv("VOICE_EVE", "2XA8XjaNwPD3cCxrLG5K"))


class TTSRequest(BaseModel):
    """OpenAI-compatible TTS request model."""
    input: str = Field(..., description="The text to convert to speech")
    model: str = Field(default="tts-1", description="TTS model to use")
    voice: str = Field(default="jessica", description="Voice to use (configured via VOICE_* env vars)")
    response_format: Optional[str] = Field(default="mp3", description="Audio format")
    speed: Optional[float] = Field(default=1.0, ge=0.25, le=4.0, description="Playback speed")


class ModelsResponse(BaseModel):
    """OpenAI-compatible models list response."""
    object: str = "list"
    data: list


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "ElevenLabs OpenAI-Compatible TTS Proxy",
        "version": "0.1.0",
        "endpoints": [
            "/v1/audio/speech",
            "/v1/models",
            "/health"
        ],
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")

    return {
        "status": "healthy",
        "service": "elevenlabs-openai-proxy",
        "elevenlabs_configured": bool(api_key)
    }


@app.get("/v1/models")
@app.post("/v1/models")
async def list_models():
    """List available TTS models (OpenAI-compatible endpoint)."""
    return ModelsResponse(
        data=[
            {
                "id": "tts-1",
                "object": "model",
                "created": 1699046015,
                "owned_by": "elevenlabs-proxy",
            },
            {
                "id": "tts-1-hd",
                "object": "model",
                "created": 1699046015,
                "owned_by": "elevenlabs-proxy",
            },
        ]
    )


def get_elevenlabs_voice_id(openai_voice: str) -> str:
    """Map OpenAI voice name to ElevenLabs voice ID (dynamically loaded)."""
    # Check if it's already an ElevenLabs voice ID (alphanumeric, typically 20 chars)
    if len(openai_voice) > 15 and openai_voice.isalnum():
        return openai_voice

    # Dynamically load voice mapping
    voice_mapping = get_voice_mapping()
    default_voice = get_default_voice_id()

    # Map OpenAI voice name to ElevenLabs voice ID
    voice_id = voice_mapping.get(openai_voice.lower(), default_voice)
    logger.info(f"Mapped OpenAI voice '{openai_voice}' to ElevenLabs voice ID: {voice_id}")
    return voice_id


def get_elevenlabs_output_format(openai_format: str) -> str:
    """Map OpenAI audio format to ElevenLabs format."""
    # ElevenLabs supports: mp3_44100_64, mp3_44100_96, mp3_44100_128,
    #                      mp3_44100_192, pcm_16000, pcm_22050, pcm_24000,
    #                      pcm_44100, ulaw_8000
    # Note: PCM formats require Pro tier, so we ALWAYS use MP3 for compatibility
    # Force MP3 format for all requests to avoid Pro tier requirement
    logger.info(f"Input format '{openai_format}' mapped to mp3_44100_128 (forced for free tier)")
    return "mp3_44100_128"


@app.post("/v1/audio/speech")
async def create_speech(
    request: TTSRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate speech from text using ElevenLabs (OpenAI-compatible endpoint).

    This endpoint mimics OpenAI's /v1/audio/speech API but uses ElevenLabs
    as the TTS provider.
    """
    # Dynamically load API key
    api_key = get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ELEVENLABS_API_KEY not configured"
        )

    logger.info(f"TTS request: voice={request.voice}, model={request.model}, format={request.response_format}")

    try:
        # Initialize ElevenLabs client
        client = AsyncElevenLabs(api_key=api_key)

        # Map voice and format
        voice_id = get_elevenlabs_voice_id(request.voice)
        output_format = get_elevenlabs_output_format(request.response_format or "mp3")

        # ElevenLabs stability and similarity_boost settings
        # These can be tuned for different voice characteristics
        voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }

        # Call ElevenLabs TTS API
        logger.info(f"Calling ElevenLabs TTS API with voice_id={voice_id}, output_format={output_format}")

        audio_stream = client.text_to_speech.stream(
            voice_id=voice_id,
            text=request.input,
            model_id="eleven_turbo_v2_5" if request.model == "tts-1" else "eleven_multilingual_v2",
            output_format=output_format,
            voice_settings=voice_settings
        )

        # Determine content type and handle format conversion
        requested_format = request.response_format or "mp3"

        # Stream the audio response with optional transcoding
        async def stream_audio():
            # If client requested PCM, we need to transcode MP3 -> PCM using ffmpeg
            if requested_format in ["pcm", "wav"]:
                logger.info("Transcoding MP3 to PCM using ffmpeg")

                # Start ffmpeg process to convert MP3 to PCM (async version)
                # Output: 16-bit PCM, 24kHz sample rate (OpenAI compatible)
                ffmpeg_process = await asyncio.create_subprocess_exec(
                    'ffmpeg',
                    '-i', 'pipe:0',  # Read MP3 from stdin
                    '-f', 's16le',    # Output format: signed 16-bit little-endian PCM
                    '-acodec', 'pcm_s16le',  # PCM codec
                    '-ar', '24000',   # Sample rate: 24kHz (OpenAI default)
                    '-ac', '1',       # Mono audio
                    'pipe:1',         # Write to stdout
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                async def write_to_ffmpeg():
                    """Write MP3 data to ffmpeg stdin."""
                    try:
                        async for chunk in audio_stream:
                            ffmpeg_process.stdin.write(chunk)
                            await ffmpeg_process.stdin.drain()
                        ffmpeg_process.stdin.close()
                        await ffmpeg_process.stdin.wait_closed()
                    except Exception as e:
                        logger.error(f"Error writing to ffmpeg: {e}")
                        ffmpeg_process.kill()

                # Start writing MP3 data to ffmpeg in background
                write_task = asyncio.create_task(write_to_ffmpeg())

                # Read PCM data from ffmpeg stdout (async)
                try:
                    while True:
                        pcm_chunk = await ffmpeg_process.stdout.read(4096)
                        if not pcm_chunk:
                            break
                        yield pcm_chunk
                finally:
                    # Ensure ffmpeg process is cleaned up
                    await write_task
                    await ffmpeg_process.wait()
            else:
                # Client requested MP3 - stream directly
                async for chunk in audio_stream:
                    yield chunk

        # Set content type based on what we're actually returning
        if requested_format in ["pcm", "wav"]:
            content_type = "audio/pcm"
            file_extension = "pcm"
        else:
            content_type = "audio/mpeg"
            file_extension = "mp3"

        return StreamingResponse(
            stream_audio(),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=speech.{file_extension}"
            }
        )

    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate speech: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting ElevenLabs OpenAI-Compatible TTS Proxy on {host}:{port}")
    logger.info(f"API Documentation available at http://{host}:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
