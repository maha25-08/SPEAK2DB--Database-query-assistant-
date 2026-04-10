#!/usr/bin/env python3
"""
Test Comprehensive Student Query Processing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_student_queries import enhanced_student_queries

def test_comprehensive_student_queries():
    """Test all comprehensive student query types."""
    
    print("Testing Comprehensive Student Query Processing")
    print("=" * 60)
    
    # Test all new query types
    query_tests = [
        # Academic queries
        ("attendance for student MT3001", "student_attendance"),
        ("MT3001's attendance percentage", "student_attendance"),
        ("gpa for student MT3001", "student_gpa"),
        ("what are MT3001's grades", "student_gpa"),
        
        # Contact queries
        ("contact information for student MT3001", "student_contact"),
        ("what is MT3001's email", "student_contact"),
        ("phone number for student MT3001", "student_contact"),
        
        # Branch/Year queries
        ("branch for student MT3001", "student_branch"),
        ("what branch is MT3001 in", "student_branch"),
        ("which year is MT3001 studying", "student_branch"),
        
        # Statistics queries
        ("library statistics for student MT3001", "student_stats"),
        ("MT3001's reading summary", "student_stats"),
        ("how many books has MT3001 borrowed", "student_stats"),
        
        # Recent activity queries
        ("recent activity for student MT3001", "student_recent"),
        ("what did MT3001 do recently", "student_recent"),
        
        # Due dates queries
        ("due dates for student MT3001", "student_duedates"),
        ("when are MT3001's books due", "student_duedates"),
        
        # Payment history queries
        ("payment history for student MT3001", "student_payments"),
        ("what fines did MT3001 pay", "student_payments"),
        
        # Personal queries
        ("show my fines", "personal_query"),
        ("my borrowed books", "personal_query"),
        ("my attendance", "personal_query"),
        ("my gpa", "personal_query"),
    ]
    
    for i, (query, expected_type) in enumerate(query_tests, 1):
        print(f"\nTest {i}: '{query}'")
        print(f"Expected: {expected_type}")
        print("-" * 40)
        
        # Test query type detection
        detected_type = enhanced_student_queries.detect_student_query_type(query)
        print(f"Detected: {detected_type}")
        
        # Test query execution
        if detected_type:
            # For personal queries, use current student ID
            current_student_id = 1 if detected_type == 'personal_query' else None
            result = enhanced_student_queries.execute_student_query(query, current_student_id)
            
            print(f"Success: {result.get('success', 'unknown')}")
            print(f"Query Type: {result.get('query_type', 'N/A')}")
            print(f"Student ID: {result.get('student_identifier', 'N/A')}")
            print(f"Identifier Type: {result.get('identifier_type', 'N/A')}")
            print(f"Message: {result.get('message', 'No message')}")
            
            if result.get('error'):
                print(f"Error: {result['error']}")
        else:
            print("Query type not detected")
        
        print("-" * 40)
    
    print("\n" + "=" * 60)
    print("COMPREHENSIVE STUDENT QUERY TESTING COMPLETED!")
    print("=" * 60)
    
    # Show all query examples
    print("\nAll Available Query Examples:")
    print("-" * 40)
    
    examples = enhanced_student_queries.get_student_query_examples()
    
    categories = {
        "Book-related": [],
        "Fine-related": [],
        "Student Information": [],
        "Academic": [],
        "Contact": [],
        "Branch/Year": [],
        "Statistics": [],
        "Activity": [],
        "Due Dates": [],
        "Payments": [],
        "Personal": [],
        "Combined": []
    }
    
    for example in examples:
        if "book" in example.lower():
            categories["Book-related"].append(example)
        elif "fine" in example.lower() or "payment" in example.lower():
            categories["Fine-related"].append(example)
        elif "student details" in example.lower() or "information" in example.lower() or "profile" in example.lower():
            categories["Student Information"].append(example)
        elif "attendance" in example.lower() or "gpa" in example.lower() or "grade" in example.lower():
            categories["Academic"].append(example)
        elif "contact" in example.lower() or "email" in example.lower() or "phone" in example.lower():
            categories["Contact"].append(example)
        elif "branch" in example.lower() or "department" in example.lower() or "year" in example.lower():
            categories["Branch/Year"].append(example)
        elif "statistics" in example.lower() or "summary" in example.lower() or "how many" in example.lower():
            categories["Statistics"].append(example)
        elif "activity" in example.lower() or "history" in example.lower() or "recent" in example.lower():
            categories["Activity"].append(example)
        elif "due" in example.lower() or "return" in example.lower():
            categories["Due Dates"].append(example)
        elif "my" in example.lower():
            categories["Personal"].append(example)
        elif "and" in example.lower():
            categories["Combined"].append(example)
        else:
            categories["Fine-related"].append(example)  # Default
    
    for category, queries in categories.items():
        if queries:
            print(f"\n{category}:")
            for query in queries:
                print(f"  - {query}")
    
    total_examples = sum(len(queries) for queries in categories.values())
    print(f"\nTotal Query Examples: {total_examples}")
    
    print("\n" + "=" * 60)
    print("KEY IMPROVEMENTS:")
    print("=" * 60)
    print("  Academic Queries: Attendance, GPA, Grades")
    print("  Contact Queries: Email, Phone, Details")
    print("  Branch/Year Queries: Department, Class, Year")
    print("  Statistics: Library summary, counts, totals")
    print("  Recent Activity: Last 30 days activity")
    print("  Due Dates: Return deadlines, overdue status")
    print("  Payment History: Paid fines, transactions")
    print("  Personal Queries: 'my' queries for logged-in students")
    print("  Combined Queries: Multiple data types")
    print("=" * 60)

if __name__ == "__main__":
    test_comprehensive_student_queries()
