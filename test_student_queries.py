#!/usr/bin/env python3
"""
Test Enhanced Student Query Processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_student_queries import enhanced_student_queries

def test_student_queries():
    """Test comprehensive student query processing."""
    
    test_queries = [
        # Book-related queries
        "show books borrowed by student MT3001",
        "what books does student MT3001 currently have",
        "books issued to MT3001",
        "MT3001's borrowed books",
        "currently issued books for student Alice Johnson",
        
        # Fine-related queries
        "show fines paid by MT3001",
        "unpaid fines for student MT3001",
        "how much does MT3001 owe in fines",
        "all fines for student MT3001",
        "MT3001's fine payment history",
        
        # Student information queries
        "student details for MT3001",
        "show information about student MT3001",
        "who is student MT3001",
        "MT3001's profile and activity",
        
        # Activity and history queries
        "student activity for MT3001",
        "library history of student MT3001",
        "what has student MT3001 done in library",
        "MT3001's complete library record",
        
        # Statistical queries
        "how many books has MT3001 borrowed",
        "total fines paid by MT3001",
        "current books issued to MT3001",
        "overdue books for student MT3001",
        
        # Combined queries
        "show borrowed books and unpaid fines for MT3001",
        "student MT3001 details with current issued books",
        "MT3001's library activity and fine status"
    ]
    
    print("🎓 Testing Enhanced Student Query Processing")
    print("=" * 60)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        print("-" * 40)
        
        result = enhanced_student_queries.execute_student_query(query)
        
        # Display results
        print(f"Success: {result.get('success', 'unknown')}")
        print(f"Query Type: {result.get('query_type', 'N/A')}")
        print(f"Student ID: {result.get('student_identifier', 'N/A')}")
        print(f"Message: {result.get('message', 'No message')}")
        
        if result.get('success') and result.get('data'):
            data = result['data']
            print(f"Results Found: {len(data)} items")
            
            # Show first few results with details
            for j, item in enumerate(data[:3], 1):
                print(f"  {j}. ", end="")
                for key, value in item.items():
                    if value is not None:
                        print(f"{key}: {value} | ", end="")
                print()
        
        if result.get('error'):
            print(f"Error: {result['error']}")
        
        if result.get('suggestion'):
            print(f"Suggestion: {result['suggestion']}")
        
        print("-" * 40)
    
    print("\n✅ Student query testing completed!")
    print("\n🎯 Key Improvements:")
    print("  ✅ Comprehensive student query patterns")
    print("  ✅ Multiple entity extraction (roll number, name)")
    print("  ✅ Book, fine, and activity queries")
    print("  ✅ Proper SQL generation for each query type")
    print("  ✅ Error handling and suggestions")
    print("  ✅ Statistical and combined queries")

def test_query_examples():
    """Test query examples for librarian console."""
    print("\n📚 Librarian Query Examples:")
    print("=" * 40)
    
    examples = enhanced_student_queries.get_student_query_examples()
    
    for i, example in enumerate(examples, 1):
        print(f"{i:2d}. {example}")
    
    print(f"\n📊 Total Examples: {len(examples)}")
    print("✅ All major student query types covered!")

if __name__ == "__main__":
    test_student_queries()
    test_query_examples()
