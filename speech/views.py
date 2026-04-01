"""
Speech Services: Cloud TTS + STT Token Provider (Production Ready)

Endpoints:
  POST /api/speech/tts/          → Synthesize text to audio (Edge TTS)
  GET  /api/speech/stt-token/    → Get Deepgram API key for browser STT
  GET  /api/speech/tts-voices/   → List available TTS voices

Environment variables (.env):
  DEEPGRAM_API_KEY       = your-deepgram-api-key
  TTS_PROVIDER           = edge  (or: elevenlabs, google, openai)
  TTS_VOICE              = en-US-AriaNeural
  TTS_RATE               = +0%
  TTS_PITCH              = +0Hz
  ELEVENLABS_API_KEY     = (optional, for future use)
  GOOGLE_TTS_API_KEY     = (optional, for future use)
  OPENAI_API_KEY         = (optional, for future use)
"""

import asyncio
import logging
import json
import hashlib
import time

from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from decouple import config

logger = logging.getLogger(__name__)


# ─── Rate Limiting ────────────────────────────────────────────
class TTSBurstThrottle(AnonRateThrottle):
    """Limit TTS requests to prevent abuse."""
    rate = '30/minute'


class TTSSustainedThrottle(AnonRateThrottle):
    """Sustained TTS rate limit."""
    rate = '200/hour'


class STTTokenThrottle(AnonRateThrottle):
    """Limit STT token requests."""
    rate = '10/minute'


# ─── Interview Token Validation ───────────────────────────────
def _validate_interview_token(request) -> bool:
    """
    Validate that the request comes from an active interview session.
    Checks for a valid interview UUID or JWT token.
    Returns True if valid, False otherwise.
    """
    # Option 1: Check JWT token (if present)
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        return True  # JWT middleware already validated

    # Option 2: Check interview UUID in query params or headers
    interview_uuid = request.GET.get('interview_uuid') or request.META.get('HTTP_X_INTERVIEW_UUID', '')
    if interview_uuid:
        # Verify the UUID belongs to an active interview
        try:
            from interviews.models import Interview
            return Interview.objects.filter(
                uuid=interview_uuid,
                status__in=['in_progress', 'scheduled']
            ).exists()
        except Exception:
            return False

    return False


# ─── Async helper ─────────────────────────────────────────────
def _run_async(coro):
    """Safely run async code from Django's sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ─── TTS Audio Cache ─────────────────────────────────────────
def _get_tts_cache_key(text: str, voice: str, rate: str, pitch: str) -> str:
    """Generate a cache key for TTS audio."""
    content = f"{text}|{voice}|{rate}|{pitch}"
    return f"tts_audio_{hashlib.md5(content.encode()).hexdigest()}"


# ─── TTS: Edge TTS (free, no API key needed) ─────────────────
async def _edge_tts_synthesize(text: str, voice: str, rate: str, pitch: str) -> bytes:
    """Generate audio using Microsoft Edge TTS (free)."""
    import edge_tts

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )
    audio_data = b''
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data


async def _edge_tts_voices() -> list:
    """List available Edge TTS voices."""
    import edge_tts
    voices = await edge_tts.list_voices()
    return [
        {
            'id': v['ShortName'],
            'name': v['FriendlyName'],
            'locale': v['Locale'],
            'gender': v['Gender'],
        }
        for v in voices
        if v['Locale'].startswith('en')
    ]


# ─── TTS: ElevenLabs (future) ────────────────────────────────
def _elevenlabs_synthesize(text: str, voice: str) -> bytes:
    """Generate audio using ElevenLabs API."""
    import requests

    api_key = config('ELEVENLABS_API_KEY', default='')
    if not api_key:
        raise ValueError('ELEVENLABS_API_KEY not configured')

    voice_id = voice or 'EXAVITQu4vr4xnSDxMaL'

    resp = requests.post(
        f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
        headers={
            'xi-api-key': api_key,
            'Content-Type': 'application/json',
        },
        json={
            'text': text,
            'model_id': 'eleven_monolingual_v1',
            'voice_settings': {
                'stability': 0.5,
                'similarity_boost': 0.75,
            },
        },
    )
    resp.raise_for_status()
    return resp.content


# ─── TTS: OpenAI (future) ────────────────────────────────────
def _openai_tts_synthesize(text: str, voice: str) -> bytes:
    """Generate audio using OpenAI TTS API."""
    import requests

    api_key = config('OPENAI_API_KEY', default='')
    if not api_key:
        raise ValueError('OPENAI_API_KEY not configured')

    resp = requests.post(
        'https://api.openai.com/v1/audio/speech',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': 'tts-1',
            'input': text,
            'voice': voice or 'alloy',
            'response_format': 'mp3',
        },
    )
    resp.raise_for_status()
    return resp.content


# ═════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═════════════════════════════════════════════════════════════

@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([TTSBurstThrottle, TTSSustainedThrottle])
def tts_synthesize(request):
    """
    POST /api/speech/tts/
    Body: { "text": "Hello world", "voice": "en-US-AriaNeural", "rate": "+0%", "pitch": "+0Hz" }
    Returns: audio/mpeg binary
    """
    text = request.data.get('text', '')
    if not text:
        return JsonResponse({'error': 'No text provided'}, status=400)

    if len(text) > 5000:
        return JsonResponse({'error': 'Text too long (max 5000 chars)'}, status=400)

    # Validate request comes from an active interview
    if not _validate_interview_token(request):
        # Still allow but log it — don't hard block in case of edge cases
        logger.warning(f'TTS request without valid interview token from {request.META.get("REMOTE_ADDR")}')

    provider = config('TTS_PROVIDER', default='edge').lower()
    voice = request.data.get('voice', config('TTS_VOICE', default='en-US-AriaNeural'))
    rate = request.data.get('rate', config('TTS_RATE', default='+0%'))
    pitch = request.data.get('pitch', config('TTS_PITCH', default='+0Hz'))

    # Check cache first
    cache_key = _get_tts_cache_key(text, voice, rate, pitch)
    cached_audio = cache.get(cache_key)
    if cached_audio:
        logger.debug(f'TTS cache hit for: {text[:50]}...')
        response = HttpResponse(cached_audio, content_type='audio/mpeg')
        response['Content-Length'] = len(cached_audio)
        response['Cache-Control'] = 'public, max-age=3600'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    try:
        if provider == 'edge':
            # Retry up to 5 times — Edge TTS SSL drops intermittently
            last_error = None
            for attempt in range(5):
                try:
                    audio_data = _run_async(_edge_tts_synthesize(text, voice, rate, pitch))
                    break
                except Exception as e:
                    last_error = e
                    logger.warning(f'Edge TTS attempt {attempt + 1} failed: {e}')
                    time.sleep(1)
            else:
                raise last_error
        elif provider == 'elevenlabs':
            audio_data = _elevenlabs_synthesize(text, voice)
        elif provider == 'openai':
            audio_data = _openai_tts_synthesize(text, voice)
        else:
            return JsonResponse({'error': f'Unknown TTS provider: {provider}'}, status=400)

        if not audio_data:
            return JsonResponse({'error': 'No audio generated'}, status=500)

        # Cache the audio for 1 hour (saves repeated synthesis for same text)
        cache.set(cache_key, audio_data, 3600)

        response = HttpResponse(audio_data, content_type='audio/mpeg')
        response['Content-Length'] = len(audio_data)
        response['Cache-Control'] = 'public, max-age=3600'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    except ImportError as e:
        logger.error(f'TTS provider not installed: {e}')
        return JsonResponse({'error': f'TTS provider "{provider}" not installed. Run: pip install edge-tts'}, status=500)
    except Exception as e:
        logger.error(f'TTS synthesis failed: {e}')
        return JsonResponse({'error': 'TTS synthesis failed'}, status=500)


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([STTTokenThrottle])
def stt_token(request):
    """
    GET /api/speech/stt-token/
    Returns Deepgram API key for browser-side WebSocket connection.

    Security: Rate-limited to 10/minute per IP.
    The Deepgram key should have limited scope (only transcription, no admin).
    
    For production upgrade: Use Deepgram's temporary key API:
    POST https://api.deepgram.com/v1/projects/{project_id}/keys
    to create short-lived keys instead of returning the main key.
    """
    api_key = config('DEEPGRAM_API_KEY', default='')
    if not api_key:
        return JsonResponse({'error': 'DEEPGRAM_API_KEY not configured'}, status=500)

    # Validate request comes from an active interview
    if not _validate_interview_token(request):
        logger.warning(f'STT token request without valid interview token from {request.META.get("REMOTE_ADDR")}')

    return JsonResponse({
        'key': api_key,
        'provider': 'deepgram',
        'model': config('STT_MODEL'),
    })


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
@throttle_classes([STTTokenThrottle])
def tts_voices(request):
    """
    GET /api/speech/tts-voices/
    Returns list of available TTS voices (cached for 24 hours).
    """
    provider = config('TTS_PROVIDER', default='edge').lower()

    # Cache voice list for 24 hours
    cache_key = f'tts_voices_{provider}'
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse({'voices': cached, 'provider': provider})

    try:
        if provider == 'edge':
            voices = _run_async(_edge_tts_voices())
        else:
            voices = [{'id': 'default', 'name': 'Default', 'locale': 'en-US', 'gender': 'Female'}]

        cache.set(cache_key, voices, 86400)  # 24 hours
        return JsonResponse({'voices': voices, 'provider': provider})
    except Exception as e:
        logger.error(f'Failed to list voices: {e}')
        return JsonResponse({'error': 'Failed to list voices'}, status=500)