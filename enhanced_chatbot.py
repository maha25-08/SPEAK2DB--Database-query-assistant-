"""
Enhanced Chatbot with Advanced Intent Recognition and Context Management
"""

import re
import sqlite3
from typing import Dict, List, Optional, Tuple
from db.connection import get_db_connection, MAIN_DB
from advanced_ambiguity import advanced_detector

class EnhancedChatbot:
    """Advanced chatbot with intent recognition and context awareness."""
    
    def __init__(self):
        self.context = {}
        self.intent_history = []
        self.current_session = {}
        self.ambiguity_detector = advanced_detector
    
    def process_query(self, query: str) -> Dict:
        """Main method to process user queries with advanced ambiguity detection."""
        print(f"🤖 Processing query: '{query}'")
        
        # Step 1: Detect intent with confidence
        intent_data = self._detect_enhanced_intent(query)
        
        print(f"🎯 Detected intent: {intent_data['intent']} (confidence: {intent_data['confidence']})")
        
        # Step 2: Advanced ambiguity analysis
        ambiguity_analysis = self.ambiguity_detector.analyze_query_ambiguity(query, self.context)
        
        print(f"🔍 Ambiguity analysis: {ambiguity_analysis['ambiguity_level']} (confidence: {ambiguity_analysis['confidence_score']}%)")
        
        # Step 3: Check if clarification is needed
        if self.ambiguity_detector.should_trigger_clarification(query, {'status': 'processing'}):
            clarification_response = self.ambiguity_detector.generate_clarification_response(query, ambiguity_analysis)
            
            print(f"❓ Clarification needed: {len(clarification_response['suggested_clarifications'])} suggestions")
            print(f"📋 Ambiguity types: {ambiguity_analysis['ambiguity_types']}")
            
            # Update context
            self.ambiguity_detector.update_context(query, clarification_response, 'clarification_triggered')
            
            return clarification_response
        
        # Step 4: Extract entities
        entities = self.ambiguity_detector._extract_entities_advanced(query)
        
        print(f"📋 Extracted entities: {entities}")
        
        # Step 5: Execute query
        result = self._execute_query(intent_data["intent"], entities)
        
        # Step 6: Update context with results
        self.ambiguity_detector.update_context(query, result, intent_data["intent"])
        
        # Add context information
        result["context"] = {
            "intent": intent_data["intent"],
            "entities": entities,
            "confidence": intent_data["confidence"],
            "query_complexity": intent_data["analysis"],
            "ambiguity_analysis": ambiguity_analysis,
            "clarification_triggered": False
        }
        
        print(f"✅ Query executed: {result['status']}")
        return result


# Global chatbot instance
enhanced_chatbot = EnhancedChatbot()


def process_enhanced_query(query: str) -> Dict:
    """Main entry point for enhanced query processing."""
    return enhanced_chatbot.process_query(query)
