"""
Advanced Ambiguity Detection and Context Management System
Handles thousands of contexts, intents, and clarification scenarios.
"""

import re
import sqlite3
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json

class AdvancedAmbiguityDetector:
    """Sophisticated ambiguity detection with extensive context tracking."""
    
    def __init__(self):
        self.conversation_history = deque(maxlen=50)  # Last 50 interactions
        self.user_context = defaultdict(dict)  # User-specific context
        self.system_context = {
            'library_stats': {},
            'recent_queries': [],
            'user_preferences': {},
            'domain_knowledge': self._load_domain_knowledge()
        }
        self.ambiguity_patterns = self._load_ambiguity_patterns()
        self.intent_mappings = self._load_intent_mappings()
        self.entity_extractors = self._load_entity_extractors()
        
    def _load_domain_knowledge(self) -> Dict:
        """Load library domain knowledge base."""
        return {
            'book_categories': [
                'Computer Science', 'Electronics', 'Mechanical', 'Civil', 
                'Chemical', 'Electrical', 'Business', 'Mathematics',
                'Physics', 'Biology', 'Literature', 'History'
            ],
            'student_departments': [
                'Computer Science', 'Electronics', 'Mechanical', 'Civil',
                'Chemical', 'Electrical', 'Business', 'General'
            ],
            'fine_types': ['Overdue', 'Damaged', 'Lost', 'Late Return', 'Early Return'],
            'book_statuses': ['Available', 'Issued', 'Reserved', 'Maintenance', 'Lost'],
            'common_authors': [
                'Stephen King', 'John Doe', 'Jane Smith', 'Robert Martin',
                'Emily Johnson', 'Michael Brown', 'Sarah Davis', 'David Wilson'
            ]
        }
    
    def _load_ambiguity_patterns(self) -> Dict:
        """Load comprehensive ambiguity detection patterns."""
        return {
            'pronoun_ambiguity': [
                r'\b(it|they|this|that|these|those)\b.*\b(book|books|student|students?|fines?|data|information)\b',
                r'\b(we|us)\b.*\b(need|want|looking for|searching|find)\b'
            ],
            'quantifier_ambiguity': [
                r'\b(some|few|several|multiple|many|various|different)\b.*\b(books|students|data|records)\b',
                r'\b(all|every|each|any)\b.*\b(book|student|fine)\b'
            ],
            'temporal_ambiguity': [
                r'\b(recently|currently|now|today|yesterday|last week|this month)\b.*\b(issued|returned|fined|paid)\b',
                r'\b(soon|later|next|upcoming|future)\b.*\b(due|return|issue)\b'
            ],
            'scope_ambiguity': [
                r'\b(in library|system|database)\b.*\b(books|students|fines)\b',
                r'\b(my|our)\b.*\b(books|records|data)\b'
            ],
            'action_ambiguity': [
                r'\b(show|list|display|get|find|search)\b.*\b(me|details|info|information|data)\b',
                r'\b(add|create|insert|new|issue|borrow|lend)\b.*\b(book|student|fine)\b'
            ],
            'comparative_ambiguity': [
                r'\b(more|less|higher|lower|greater|cheapest|expensive|best|worst|top|bottom)\b.*\b(than|compared to)\b',
                r'\b(like|similar|related|connected|associated)\b.*\b(book|student|fine)\b'
            ]
        }
    
    def _load_intent_mappings(self) -> Dict:
        """Load comprehensive intent mappings."""
        return {
            'book_search': {
                'keywords': ['book', 'books', 'title', 'author', 'find', 'search', 'look for', 'show', 'list', 'display'],
                'patterns': [
                    r'find.*book', r'search.*book', r'look for.*book',
                    r'show.*book', r'list.*book', r'display.*book',
                    r'book.*by', r'books.*by', r'what.*book'
                ],
                'entities': ['title', 'author', 'isbn', 'category', 'price', 'available', 'publication_year']
            },
            'student_search': {
                'keywords': ['student', 'students', 'roll', 'name', 'find', 'search', 'show', 'list'],
                'patterns': [
                    r'find.*student', r'search.*student', r'look for.*student',
                    r'show.*student', r'list.*student', r'student.*by', r'student.*name'
                ],
                'entities': ['roll_number', 'name', 'branch', 'year', 'email', 'phone', 'gpa', 'attendance']
            },
            'fine_search': {
                'keywords': ['fine', 'fines', 'payment', 'unpaid', 'paid', 'amount', 'due'],
                'patterns': [
                    r'show.*fine', r'list.*fine', r'unpaid.*fine', r'fine.*payment',
                    r'fine.*amount', r'total.*fine', r'fine.*due'
                ],
                'entities': ['student_id', 'fine_amount', 'fine_type', 'status', 'issue_date', 'payment_date']
            },
            'statistical': {
                'keywords': ['count', 'total', 'number', 'how many', 'statistics', 'average'],
                'patterns': [
                    r'how many.*book', r'count.*book', r'total.*book', r'number.*book',
                    r'average.*price', r'statistics.*book'
                ],
                'entities': ['aggregate_type', 'filter_criteria', 'time_period']
            },
            'transactional': {
                'keywords': ['issue', 'return', 'borrow', 'lend', 'pay', 'add', 'create', 'delete', 'update'],
                'patterns': [
                    r'issue.*book', r'borrow.*book', r'lend.*book', r'check out.*book',
                    r'return.*book', r'give back.*book', r'check in.*book',
                    r'pay.*fine', r'add.*book', r'create.*book', r'delete.*book'
                ],
                'entities': ['action_type', 'target_type', 'target_id', 'student_id', 'book_id', 'fine_id']
            }
        }
    
    def _load_entity_extractors(self) -> Dict:
        """Load advanced entity extraction patterns."""
        return {
            'book_title': [
                r'book[s]?\s*(?:titled?|called?|named?)\s*["\']?([^"\']+)["\']?',
                r'"([^"]+)"\s*by\s+([^"]+)"',
                r'title[:\s]*([^"\']+)["\']?'
            ],
            'book_author': [
                r'by\s+([a-z\s]+(?:\s+[a-z]+)*)',
                r'author[:\s]*([a-z\s]+(?:\s+[a-z]+)*)',
                r'written\s+by\s+([a-z\s]+(?:\s+[a-z]+)*)'
            ],
            'book_price': [
                r'\$(\d+(?:\.\d+)?)',
                r'price[:\s]*\$(\d+(?:\.\d+)?)',
                r'cost[:\s]*\$(\d+(?:\.\d+)?)',
                r'(?:price|cost|worth|valued at)\s*\$?(\d+(?:\.\d+)?)'
            ],
            'student_roll': [
                r'roll\s+(?:number)?\s*([a-z0-9]+)',
                r'student[:\s]*([a-z0-9]+)',
                r'id[:\s]*([a-z0-9]+)'
            ],
            'student_name': [
                r'(?:student|name)[:\s]*\s*([a-z\s]+)',
                r'called\s+([a-z\s]+)',
                r'named\s+([a-z\s]+)'
            ],
            'fine_amount': [
                r'\$(\d+(?:\.\d+)?)',
                r'fine[:\s]*\$(\d+(?:\.\d+)?)',
                r'amount[:\s]*\$(\d+(?:\.\d+)?)',
                r'(?:owe|pay)\s*\$?(\d+(?:\.\d+)?)'
            ],
            'date_range': [
                r'(?:from|between|during)\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                r'(?:in|within|during)\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})',
                r'(?:last|past)\s*(\d+)\s*(?:days?|weeks?|months?|years?)'
            ]
        }
    
    def analyze_query_ambiguity(self, query: str, context: Dict = None) -> Dict:
        """Comprehensive ambiguity analysis with multiple detection layers."""
        query_lower = query.lower().strip()
        ambiguity_indicators = {
            'detected_patterns': [],
            'confidence_score': 100,
            'ambiguity_types': [],
            'missing_entities': [],
            'suggested_clarifications': [],
            'context_clues': []
        }
        
        # Layer 1: Pattern-based ambiguity detection
        for pattern_type, patterns in self.ambiguity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    ambiguity_indicators['detected_patterns'].append({
                        'type': pattern_type,
                        'pattern': pattern,
                        'matches': matches,
                        'severity': 'high' if len(matches) > 1 else 'medium'
                    })
                    ambiguity_indicators['confidence_score'] -= len(matches) * 5
        
        # Layer 2: Entity-based analysis
        entities = self._extract_entities_advanced(query_lower)
        if not entities.get('primary_intent') and not entities.get('book_title') and not entities.get('student_name'):
            ambiguity_indicators['ambiguity_types'].append('missing_primary_entity')
            ambiguity_indicators['confidence_score'] -= 20
        
        # Layer 3: Context analysis
        if context:
            context_clues = self._analyze_context_relevance(query, context)
            ambiguity_indicators['context_clues'].extend(context_clues)
            if context_clues:
                ambiguity_indicators['confidence_score'] += 10
        
        # Layer 4: Query structure analysis
        word_count = len(query.split())
        if word_count < 3:
            ambiguity_indicators['ambiguity_types'].append('too_short')
            ambiguity_indicators['confidence_score'] -= 15
        elif word_count > 15:
            ambiguity_indicators['ambiguity_types'].append('too_complex')
            ambiguity_indicators['confidence_score'] -= 10
        
        # Layer 5: Domain knowledge check
        domain_issues = self._check_domain_compatibility(query, entities)
        if domain_issues:
            ambiguity_indicators['ambiguity_types'].extend(domain_issues)
            ambiguity_indicators['confidence_score'] -= 25
        
        # Determine overall ambiguity level
        if ambiguity_indicators['confidence_score'] < 40:
            ambiguity_level = 'high'
        elif ambiguity_indicators['confidence_score'] < 70:
            ambiguity_level = 'medium'
        else:
            ambiguity_level = 'low'
        
        return {
            'is_ambiguous': ambiguity_indicators['confidence_score'] < 80,
            'ambiguity_level': ambiguity_level,
            'confidence_score': max(0, ambiguity_indicators['confidence_score']),
            'detected_patterns': ambiguity_indicators['detected_patterns'],
            'ambiguity_types': list(set(ambiguity_indicators['ambiguity_types'])),
            'missing_entities': ambiguity_indicators['missing_entities'],
            'suggested_clarifications': self._generate_clarifications(query, entities, ambiguity_indicators),
            'context_clues': ambiguity_indicators['context_clues'],
            'analysis_summary': self._generate_analysis_summary(ambiguity_indicators)
        }
    
    def _extract_entities_advanced(self, query: str) -> Dict:
        """Advanced entity extraction with multiple extractors."""
        entities = {
            'primary_intent': None,
            'book_title': None,
            'book_author': None,
            'book_price': None,
            'book_category': None,
            'student_roll': None,
            'student_name': None,
            'fine_amount': None,
            'fine_type': None,
            'date_range': None,
            'quantities': [],
            'comparatives': []
        }
        
        # Detect primary intent first
        for intent_name, intent_data in self.intent_mappings.items():
            if any(keyword in query for keyword in intent_data['keywords']):
                entities['primary_intent'] = intent_name
                break
        
        # Extract entities using advanced patterns
        for entity_type, patterns in self.entity_extractors.items():
            for pattern in patterns:
                match = re.search(pattern, query)
                if match:
                    if entity_type == 'book_title':
                        entities['book_title'] = match.group(1).strip()
                    elif entity_type == 'book_author':
                        entities['book_author'] = match.group(1).strip()
                    elif entity_type == 'book_price':
                        price_match = re.search(r'(\d+(?:\.\d+)?)', match.group(0))
                        if price_match:
                            entities['book_price'] = float(price_match.group(1))
                    elif entity_type == 'student_roll':
                        entities['student_roll'] = match.group(1).strip()
                    elif entity_type == 'student_name':
                        entities['student_name'] = match.group(1).strip()
                    elif entity_type == 'fine_amount':
                        amount_match = re.search(r'(\d+(?:\.\d+)?)', match.group(0))
                        if amount_match:
                            entities['fine_amount'] = float(amount_match.group(1))
        
        # Extract quantities and comparatives
        quantity_words = re.findall(r'\b(\d+|\d+|\d+)\b', query)
        if quantity_words:
            entities['quantities'] = [int(q) for q in quantity_words if q.isdigit()]
        
        comparative_words = re.findall(r'\b(more|less|higher|lower|greater|cheapest|expensive|best|worst|top|bottom)\b', query)
        if comparative_words:
            entities['comparatives'] = comparative_words
        
        return entities
    
    def _generate_clarifications(self, query: str, entities: Dict, ambiguity_indicators: Dict) -> List[str]:
        """Generate contextual clarifications based on ambiguity analysis."""
        clarifications = []
        
        if 'missing_primary_entity' in ambiguity_indicators['ambiguity_types']:
            if entities.get('primary_intent') == 'book_search':
                clarifications.extend([
                    "Which specific book are you looking for?",
                    "Do you want to search by title or author?",
                    "Are you looking for books in a particular category?",
                    "What book details do you need (title, author, price)?"
                ])
            elif entities.get('primary_intent') == 'student_search':
                clarifications.extend([
                    "Which student's information do you need?",
                    "Do you want to search by roll number or name?",
                    "Are you looking for students in a specific department?",
                    "What student details do you need (name, roll, branch)?"
                ])
            elif entities.get('primary_intent') == 'fine_search':
                clarifications.extend([
                    "Do you want to see fines for a specific student?",
                    "Are you looking for unpaid or paid fines?",
                    "What fine details do you need (amount, type, date)?"
                ])
        
        if 'too_short' in ambiguity_indicators['ambiguity_types']:
            clarifications.extend([
                "Could you provide more details about your request?",
                "What specific information are you looking for?",
                "Can you be more specific about what you need?"
            ])
        
        if 'too_complex' in ambiguity_indicators['ambiguity_types']:
            clarifications.extend([
                "Can you break down your request into smaller parts?",
                "What is the main goal of your query?",
                "Which aspect would you like to focus on first?"
            ])
        
        # Add context-aware clarifications
        context_clues = ambiguity_indicators.get('context_clues', [])
        if context_clues:
            if 'recent_book_search' in context_clues:
                clarifications.extend([
                    "Are you looking for books related to your recent search?",
                    "Do you want to modify your previous book search?"
                    "Are you looking for similar books to what you found earlier?"
                ])
            elif 'recent_student_activity' in context_clues:
                clarifications.extend([
                    "Are you continuing your work with student records?",
                    "Do you want to see more details about the students you were viewing?",
                    "Are you looking for information related to recent student transactions?"
                ])
        
        return clarifications
    
    def _analyze_context_relevance(self, query: str, context: Dict) -> List[str]:
        """Analyze how current query relates to conversation context."""
        clues = []
        
        if not context:
            return clues
        
        query_lower = query.lower()
        
        # Check for continuation patterns
        if any(word in query_lower for word in ['also', 'again', 'another', 'same', 'similar', 'related', 'different']):
            clues.append('query_continuation')
        
        # Check for refinement patterns
        if any(word in query_lower for word in ['specifically', 'exactly', 'precisely', 'particularly', 'especially']):
            clues.append('query_refinement')
        
        # Check for temporal references
        if any(word in query_lower for word in ['recently', 'currently', 'now', 'today', 'yesterday', 'before']):
            clues.append('temporal_reference')
        
        # Check for comparative patterns
        if any(word in query_lower for word in ['compare', 'versus', 'against', 'better', 'worse', 'instead', 'alternative']):
            clues.append('comparative_analysis')
        
        return clues
    
    def _check_domain_compatibility(self, query: str, entities: Dict) -> List[str]:
        """Check if query entities are compatible with library domain."""
        issues = []
        
        # Check book categories
        if entities.get('book_category'):
            category = entities['book_category'].lower()
            valid_categories = [cat.lower() for cat in self.system_context['domain_knowledge']['book_categories']]
            if category not in valid_categories:
                issues.append(f'invalid_book_category_{category}')
        
        # Check student departments
        if entities.get('student_department'):
            dept = entities['student_department'].lower()
            valid_depts = [dept.lower() for dept in self.system_context['domain_knowledge']['student_departments']]
            if dept not in valid_depts:
                issues.append(f'invalid_student_department_{dept}')
        
        # Check fine types
        if entities.get('fine_type'):
            fine_type = entities['fine_type'].lower()
            valid_types = [ft.lower() for ft in self.system_context['domain_knowledge']['fine_types']]
            if fine_type not in valid_types:
                issues.append(f'invalid_fine_type_{fine_type}')
        
        return issues
    
    def _generate_analysis_summary(self, ambiguity_indicators: Dict) -> str:
        """Generate human-readable analysis summary."""
        summary_parts = []
        
        if ambiguity_indicators['detected_patterns']:
            patterns_text = ", ".join([f"{p['type']}({p['severity']})" for p in ambiguity_indicators['detected_patterns']])
            summary_parts.append(f"Patterns: {patterns_text}")
        
        if ambiguity_indicators['ambiguity_types']:
            types_text = ", ".join(ambiguity_indicators['ambiguity_types'])
            summary_parts.append(f"Ambiguity: {types_text}")
        
        if ambiguity_indicators['missing_entities']:
            missing_text = ", ".join(ambiguity_indicators['missing_entities'])
            summary_parts.append(f"Missing: {missing_text}")
        
        if ambiguity_indicators['context_clues']:
            context_text = ", ".join(ambiguity_indicators['context_clues'])
            summary_parts.append(f"Context: {context_text}")
        
        confidence_desc = f"Confidence: {ambiguity_indicators['confidence_score']}%"
        
        summary_parts.append(confidence_desc)
        return " | ".join(summary_parts)
    
    def update_context(self, query: str, result: Dict, user_action: str = None):
        """Update system context based on query and results."""
        # Update user context
        if result.get('status') == 'success':
            if result.get('data'):
                if isinstance(result['data'], list) and result['data']:
                    for item in result['data'][:5]:  # Store first 5 items
                        if 'title' in item:
                            self.user_context['recent_books'] = self.user_context.get('recent_books', [])
                            if item['title'] not in [b['title'] for b in self.user_context['recent_books']]:
                                self.user_context['recent_books'].append(item['title'])
                
                if user_action:
                    self.user_context['last_action'] = {
                        'action': user_action,
                        'query': query,
                        'timestamp': datetime.now().isoformat(),
                        'result_status': result.get('status')
                    }
        
        # Update system context
        self.system_context['recent_queries'].append({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'result_count': len(result.get('data', [])) if isinstance(result.get('data'), list) else 0
        })
        
        # Keep only recent 20 queries
        if len(self.system_context['recent_queries']) > 20:
            self.system_context['recent_queries'] = self.system_context['recent_queries'][-20:]
    
    def get_context_for_clarification(self) -> Dict:
        """Get relevant context for generating clarifications."""
        return {
            'conversation_history': list(self.conversation_history)[-5:],
            'user_context': dict(self.user_context),
            'system_context': dict(self.system_context),
            'domain_knowledge': self.system_context['domain_knowledge']
        }
    
    def should_trigger_clarification(self, query: str, result: Dict) -> bool:
        """Determine if clarification should be triggered."""
        ambiguity_analysis = self.analyze_query_ambiguity(query)
        
        # High confidence - no clarification needed
        if ambiguity_analysis['confidence_score'] >= 80:
            return False
        
        # Successful result - no clarification needed
        if result.get('status') == 'success' and result.get('data'):
            return False
        
        # Error result - no clarification needed
        if result.get('status') == 'error':
            return False
        
        # Low confidence or high ambiguity - trigger clarification
        return True
    
    def generate_clarification_response(self, query: str, ambiguity_analysis: Dict) -> Dict:
        """Generate comprehensive clarification response."""
        context = self.get_context_for_clarification()
        
        response = {
            'status': 'clarification_needed',
            'ambiguity_level': ambiguity_analysis['ambiguity_level'],
            'confidence_score': ambiguity_analysis['confidence_score'],
            'original_query': query,
            'analysis_summary': ambiguity_analysis['analysis_summary'],
            'suggested_clarifications': ambiguity_analysis['suggested_clarifications'],
            'context_available': True,
            'clarification_options': self._generate_clarification_options(ambiguity_analysis),
            'follow_up_suggestions': self._generate_follow_up_suggestions(ambiguity_analysis, context),
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'session_id': id(query),  # Simple session ID
                'context_items': len(context['conversation_history']) + len(context['user_context']) + len(context['system_context'])
            }
        }
        
        return response
    
    def _generate_clarification_options(self, ambiguity_analysis: Dict) -> List[Dict]:
        """Generate structured clarification options."""
        options = []
        ambiguity_level = ambiguity_analysis['ambiguity_level']
        
        if ambiguity_level == 'high':
            options = [
                {
                    'id': 'specify_book_details',
                    'text': 'I need specific book information',
                    'description': 'Please provide book title and/or author',
                    'example': 'Find "Introduction to Algorithms" by "Thomas Cormen"',
                    'entities_needed': ['title', 'author']
                },
                {
                    'id': 'specify_student_details',
                    'text': 'I need specific student information',
                    'description': 'Please provide student roll number or name',
                    'example': 'Find student "MT3001" or "Alice Johnson"',
                    'entities_needed': ['roll_number', 'name']
                },
                {
                    'id': 'specify_search_criteria',
                    'text': 'I need search criteria',
                    'description': 'What filters should I apply to the search?',
                    'example': 'Search by category "Computer Science" or price range "under $100"',
                    'entities_needed': ['category', 'price_range']
                }
            ]
        
        elif ambiguity_level == 'medium':
            options = [
                {
                    'id': 'refine_search_scope',
                    'text': 'Narrow down the search',
                    'description': 'Can you be more specific about what you want?',
                    'example': 'Instead of "show books", try "show available books"',
                    'entities_needed': ['availability', 'scope']
                },
                {
                    'id': 'clarify_entity_type',
                    'text': 'What type of information?',
                    'description': 'Are you looking for books, students, or fines?',
                    'example': '"data" could mean books, students, or fine records',
                    'entities_needed': ['domain']
                }
            ]
        
        else:  # Low ambiguity
            options = [
                {
                    'id': 'confirm_understanding',
                    'text': 'Did I understand correctly?',
                    'description': 'Please confirm if I understood your request',
                    'example': 'You said "books" - did you mean all books or specific books?',
                    'entities_needed': ['confirmation']
                }
            ]
        
        return options
    
    def _generate_follow_up_suggestions(self, ambiguity_analysis: Dict, context: Dict) -> List[str]:
        """Generate contextual follow-up suggestions."""
        suggestions = []
        
        # Based on detected patterns
        for pattern in ambiguity_analysis.get('detected_patterns', []):
            if pattern['type'] == 'pronoun_ambiguity':
                suggestions.extend([
                    'Try using specific names instead of pronouns',
                    'Example: Instead of "show their books", say "show books for student MT3001"'
                ])
            elif pattern['type'] == 'quantifier_ambiguity':
                suggestions.extend([
                    'Be more specific about which items',
                    'Example: Instead of "some books", say "3 books by Computer Science"'
                ])
        
        # Based on context
        if context.get('conversation_history'):
            last_query = context['conversation_history'][-1] if context['conversation_history'] else None
            if last_query and 'book' in last_query.get('query', '').lower():
                suggestions.extend([
                    'Would you like to see more details about any of these books?',
                    'Would you like to search for books by the same author?',
                    'Would you like to check availability of these books?'
                ])
        
        return suggestions


# Global instance
advanced_detector = AdvancedAmbiguityDetector()
