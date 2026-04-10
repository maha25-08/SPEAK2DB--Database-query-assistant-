#!/usr/bin/env python3
"""
Debug script to find problematic regex patterns
"""

import re
import sys
sys.path.append('.')

def test_patterns():
    try:
        from enhanced_student_queries import enhanced_student_queries
        
        # Get all patterns
        all_patterns = enhanced_student_queries.student_query_patterns
        
        print("Testing all regex patterns...")
        
        for query_type, config in all_patterns.items():
            patterns = config.get('patterns', [])
            print(f"\nTesting {query_type}:")
            
            for i, pattern in enumerate(patterns):
                try:
                    re.compile(pattern)
                    print(f"  Pattern {i+1}: OK")
                except Exception as e:
                    print(f"  Pattern {i+1}: ERROR - {e}")
                    print(f"    Pattern: {pattern}")
                    return pattern, query_type, i+1
        
        print("All patterns are valid!")
        return None, None, None
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == "__main__":
    bad_pattern, query_type, pattern_num = test_patterns()
    if bad_pattern:
        print(f"\nFound problematic pattern:")
        print(f"Query Type: {query_type}")
        print(f"Pattern Number: {pattern_num}")
        print(f"Pattern: {bad_pattern}")
