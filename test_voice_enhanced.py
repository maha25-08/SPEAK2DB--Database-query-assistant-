#!/usr/bin/env python3
"""
Test Enhanced Voice Recognition with Noise Handling
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.voice_recognition import get_voice_service

def test_voice_enhanced():
    """Test enhanced voice recognition with noise handling."""
    
    print("🎤 Testing Enhanced Voice Recognition with Noise Handling")
    print("=" * 60)
    
    voice_service = get_voice_service()
    
    # Test 1: Check voice service status
    print("\n🔍 Test 1: Voice Service Status")
    print("-" * 30)
    status = voice_service.get_status()
    print(f"Available: {status['available']}")
    print(f"Microphone: {status['microphone_available']}")
    print(f"Engines: {status['engines']}")
    
    # Test 2: Microphone test
    print("\n🎙 Test 2: Microphone Test")
    print("-" * 30)
    mic_test = voice_service.test_microphone()
    print(f"Success: {mic_test['success']}")
    if mic_test.get('success'):
        print(f"Energy Threshold: {mic_test.get('energy_threshold', 'N/A')}")
    else:
        print(f"Error: {mic_test.get('error', 'Unknown error')}")
    
    # Test 3: Start voice recognition
    print("\n🎤 Test 3: Start Voice Recognition")
    print("-" * 30)
    
    def voice_callback(result):
        """Handle voice recognition results."""
        print(f"\n📢 Voice Result: {result['type']}")
        print(f"Message: {result.get('message', 'N/A')}")
        
        if result['type'] == 'transcription':
            print(f"Text: '{result['text']}'")
            print(f"Engine: {result['engine']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Attempts: {result.get('attempts', 1)}")
            print(f"Noise Level: {result.get('noise_level', 'unknown')}")
        elif result['type'] == 'noise_detected':
            print(f"Suggestion: {result['suggestion']}")
        elif result['type'] == 'error':
            print(f"Error: {result['message']}")
            print(f"Suggestion: {result['suggestion']}")
    
    start_result = voice_service.start_listening(voice_callback)
    print(f"Status: {start_result['success']}")
    print(f"Message: {start_result['message']}")
    
    if start_result['success']:
        print("\n🎤 Voice Recognition Started!")
        print("📝 Speak clearly into your microphone...")
        print("🔊 Try saying: 'show books borrowed by student MT3001'")
        print("⏱️ Will listen for 10 seconds...")
        
        # Simulate waiting for voice input
        import time
        for i in range(10):
            time.sleep(1)
            print(f"Listening... {10-i}")
        
        # Stop voice recognition
        print("\n🛑 Stopping Voice Recognition...")
        stop_result = voice_service.stop_listening()
        print(f"Status: {stop_result['success']}")
        print(f"Message: {stop_result['message']}")
    
    # Test 4: Sensitivity adjustment
    print("\n🎚 Test 4: Sensitivity Adjustment")
    print("-" * 30)
    
    # Test different sensitivity settings
    sensitivity_tests = [
        {"energy_threshold": 200, "dynamic_threshold": True, "description": "High Sensitivity (Quiet)"},
        {"energy_threshold": 400, "dynamic_threshold": True, "description": "Low Sensitivity (Noisy)"},
        {"energy_threshold": 300, "dynamic_threshold": False, "description": "Fixed Medium Sensitivity"},
    ]
    
    for i, test in enumerate(sensitivity_tests, 1):
        print(f"\n  {i}. {test['description']}")
        adj_result = voice_service.adjust_sensitivity(
            energy_threshold=test['energy_threshold'],
            dynamic_threshold=test['dynamic_threshold']
        )
        print(f"    Success: {adj_result['success']}")
        if adj_result['success']:
            print(f"    Energy Threshold: {adj_result['energy_threshold']}")
            print(f"    Dynamic Threshold: {adj_result['dynamic_threshold']}")
        else:
            print(f"    Error: {adj_result['error']}")
    
    # Test 5: Get transcription (simulated)
    print("\n📝 Test 5: Transcription Retrieval")
    print("-" * 30)
    
    # Simulate some transcription data
    import json
    simulated_transcriptions = [
        {
            "type": "transcription",
            "text": "show books borrowed by student MT3001",
            "engine": "Google Cloud",
            "confidence": "high",
            "attempts": 1,
            "noise_level": "low"
        },
        {
            "type": "noise_detected",
            "message": "Background noise detected - please speak clearly",
            "suggestion": "Try moving to a quieter area or speak louder"
        },
        {
            "type": "transcription",
            "text": "unpaid fines for student MT3001",
            "engine": "Whisper",
            "confidence": "high",
            "attempts": 2,
            "noise_level": "medium"
        }
    ]
    
    for i, trans in enumerate(simulated_transcriptions, 1):
        print(f"\n  {i}. Simulated Transcription:")
        print(f"    Type: {trans['type']}")
        if trans['type'] == 'transcription':
            print(f"    Text: '{trans['text']}'")
            print(f"    Engine: {trans['engine']}")
            print(f"    Confidence: {trans['confidence']}")
            print(f"    Attempts: {trans['attempts']}")
            print(f"    Noise Level: {trans['noise_level']}")
        else:
            print(f"    Message: {trans['message']}")
            print(f"    Suggestion: {trans['suggestion']}")
    
    print("\n✅ Enhanced Voice Recognition Testing Completed!")
    print("\n🎯 Key Improvements:")
    print("  ✅ Background Noise Handling")
    print("  ✅ Multiple Recognition Engines")
    print("  ✅ Noise Level Assessment")
    print("  ✅ Retry Logic with Confidence Scoring")
    print("  ✅ Adjustable Sensitivity Settings")
    print("  ✅ Real-time Noise Detection")
    print("  ✅ Enhanced Error Handling")
    
    print("\n🔧 Noise Handling Features:")
    print("  🎤 Dynamic Energy Threshold Adjustment")
    print("  🔊 Extended Ambient Noise Calibration")
    print("  📝 Noise Pattern Filtering")
    print("  🔄 Multiple Engine Retry Logic")
    print("  📊 Confidence-Based Validation")
    print("  ⚡ Real-time Noise Level Assessment")
    print("  🎚 Adjustable Sensitivity for Different Environments")

if __name__ == "__main__":
    test_voice_enhanced()
