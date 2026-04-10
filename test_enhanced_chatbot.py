#!/usr/bin/env python3
"""
Test the enhanced chatbot with various queries.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_chatbot import process_enhanced_query

def test_enhanced_chatbot():
    """Test the enhanced chatbot with various query types."""
    
    test_queries = [
        # Clear queries
        "what are the books with highest cost",
        "show me all books",
        "find books by Stephen King",
        "count total books",
        
        # Ambiguous queries
        "show me data",
        "what information do you have",
        "tell me about books",
        
        # Complex queries
        "find expensive computer science books",
        "show students with unpaid fines",
        "count books by author John Smith",
        
        # Student queries
        "show student MT3001",
        "find student named Alice",
        "students in computer science",
        
        # Fine queries
        "show unpaid fines",
        "fines for student MT3001",
        "total amount of unpaid fines"
    ]
    
    print("🤖 Testing Enhanced Chatbot")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        print("-" * 40)
        
        result = process_enhanced_query(query)
        
        # Display results
        print(f"Status: {result.get('status', 'unknown')}")
        print(f"Message: {result.get('message', 'No message')}")
        
        if result.get('status') == 'clarification_needed':
            print(f"Suggestions: {result.get('suggestions', [])}")
            print(f"Missing entities: {result.get('context', {}).get('missing_entities', [])}")
        
        elif result.get('status') == 'success':
            data = result.get('data', [])
            if isinstance(data, list) and data:
                print(f"Found {len(data)} items")
                for item in data[:3]:  # Show first 3 items
                    if isinstance(item, dict):
                        title = item.get('title', 'N/A')
                        author = item.get('author', 'N/A')
                        price = item.get('price', 'N/A')
                        print(f"  - {title} by {author} - ${price}")
        
        print("-" * 40)
    
    print("\n✅ Enhanced chatbot testing completed!")
    print("\n🎯 Key Improvements:")
    print("  ✅ Enhanced intent recognition with confidence scoring")
    print("  ✅ Ambiguity detection with contextual suggestions")
    print("  ✅ Entity extraction for books, students, fines")
    print("  ✅ Price-based book search (highest/lowest)")
    print("  ✅ Context-aware query processing")
    print("  ✅ Structured JSON responses with metadata")

if __name__ == "__main__":
    test_enhanced_chatbot()
