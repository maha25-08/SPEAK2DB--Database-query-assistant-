"""
Voice Recognition Routes for Query Console
Handles voice input, microphone control, and speech-to-text conversion.
"""

import logging
from flask import Blueprint, request, jsonify, session
from services.voice_recognition import get_voice_service, is_voice_available

logger = logging.getLogger(__name__)

voice_bp = Blueprint("voice", __name__)


@voice_bp.route("/voice/status", methods=["GET"])
def voice_status():
    """Get current voice recognition status."""
    try:
        voice_service = get_voice_service()
        status = voice_service.get_status()
        
        return jsonify({
            "success": True,
            "status": status
        })
    except Exception as e:
        logger.error(f"Error getting voice status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@voice_bp.route("/voice/start", methods=["POST"])
def start_voice():
    """Start voice recognition."""
    try:
        if not is_voice_available():
            return jsonify({
                "success": False,
                "error": "Voice recognition not available",
                "message": "Please install SpeechRecognition library"
            }), 400
        
        voice_service = get_voice_service()
        
        # Define callback for voice recognition results
        def voice_callback(result):
            """Handle voice recognition results."""
            if result.get("type") == "transcription":
                # Store transcription in session for query processing
                session["voice_transcription"] = result.get("text")
                session["voice_confidence"] = result.get("confidence")
                session["voice_engine"] = result.get("engine")
                
                logger.info(f"Voice transcription: {result.get('text')}")
                
            elif result.get("type") == "error":
                logger.warning(f"Voice recognition error: {result.get('message')}")
                session["voice_error"] = result.get("message")
                session["voice_suggestion"] = result.get("suggestion")
        
        result = voice_service.start_listening(voice_callback)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting voice recognition: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@voice_bp.route("/voice/stop", methods=["POST"])
def stop_voice():
    """Stop voice recognition."""
    try:
        voice_service = get_voice_service()
        result = voice_service.stop_listening()
        
        # Clear voice session data
        session.pop("voice_transcription", None)
        session.pop("voice_confidence", None)
        session.pop("voice_engine", None)
        session.pop("voice_error", None)
        session.pop("voice_suggestion", None)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error stopping voice recognition: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@voice_bp.route("/voice/test", methods=["POST"])
def test_voice():
    """Test microphone functionality."""
    try:
        voice_service = get_voice_service()
        result = voice_service.test_microphone()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error testing voice: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@voice_bp.route("/voice/adjust", methods=["POST"])
def adjust_voice():
    """Adjust voice recognition sensitivity."""
    try:
        data = request.get_json() or {}
        energy_threshold = data.get("energy_threshold")
        dynamic_threshold = data.get("dynamic_threshold")
        
        voice_service = get_voice_service()
        result = voice_service.adjust_sensitivity(
            energy_threshold=energy_threshold,
            dynamic_threshold=dynamic_threshold
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adjusting voice: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@voice_bp.route("/voice/transcription", methods=["GET"])
def get_transcription():
    """Get latest voice transcription."""
    try:
        transcription = session.get("voice_transcription")
        confidence = session.get("voice_confidence")
        engine = session.get("voice_engine")
        error = session.get("voice_error")
        suggestion = session.get("voice_suggestion")
        
        response = {
            "success": True,
            "transcription": transcription,
            "confidence": confidence,
            "engine": engine,
            "error": error,
            "suggestion": suggestion
        }
        
        # Clear transcription after retrieval
        session.pop("voice_transcription", None)
        session.pop("voice_confidence", None)
        session.pop("voice_engine", None)
        session.pop("voice_error", None)
        session.pop("voice_suggestion", None)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting transcription: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def register_voice_routes(app):
    """Register voice recognition routes."""
    if is_voice_available():
        app.register_blueprint(voice_bp)
        logger.info("Voice recognition routes registered")
    else:
        logger.warning("Voice recognition routes not registered - SpeechRecognition not available")
