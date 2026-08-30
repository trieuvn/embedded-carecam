"""
Dialogue Controller Module - Manages multi-turn conversations with state management

This module orchestrates multi-turn conversations by:
- Parsing user input to identify intent and extract entities
- Managing dialogue state across multiple turns
- Supporting various dialogue patterns (single-turn, multi-turn, slot-filling, clarification, confirmation)
- Determining when conversation should continue vs. end
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import re


class Intent(Enum):
    """Supported conversation intents"""
    QUESTION_ANSWERING = "question_answering"
    CALCULATION = "calculation"
    WEATHER_QUERY = "weather_query"
    CAMERA_CONTROL = "camera_control"
    SMALL_TALK = "small_talk"
    CLARIFICATION_REQUEST = "clarification_request"
    UNKNOWN = "unknown"


@dataclass
class DialogueResponse:
    """Response from dialogue processing"""
    response_text: str
    should_continue: bool
    intent: Intent
    confidence: float
    requires_clarification: bool
    suggested_followups: List[str] = field(default_factory=list)


@dataclass
class DialogueState:
    """Current state of dialogue for a session"""
    current_intent: Optional[Intent] = None
    slot_values: Dict[str, Any] = field(default_factory=dict)
    confirmation_pending: bool = False
    clarification_needed: bool = False
    turn_count: int = 0


class DialogueController:
    """
    Orchestrates multi-turn conversations with state management.
    
    Supports dialogue patterns:
    - Single-turn: Simple Q&A
    - Multi-turn: Follow-up questions without wake word
    - Slot-filling: Progressive information gathering
    - Clarification: Ask for missing/ambiguous information
    - Confirmation: Verify before executing actions
    """
    
    def __init__(self):
        """Initialize DialogueController"""
        self.context_manager = None
        self._dialogue_states: Dict[str, DialogueState] = {}
        
        # Intent detection patterns
        self._intent_patterns = {
            Intent.CALCULATION: [
                r'\b\d+\s*[\+\-\*\/×÷]\s*\d+',  # Math expressions
                r'\bcộng\b', r'\btrừ\b', r'\bnhân\b', r'\bchia\b',
                r'\bbằng\s+mấy\b', r'\btính\b'
            ],
            Intent.WEATHER_QUERY: [
                r'\bthời\s+tiết\b', r'\bnắng\b', r'\bmưa\b',
                r'\bnhiệt\s+độ\b', r'\btrời\b'
            ],
            Intent.CAMERA_CONTROL: [
                r'\bcamera\b', r'\bquay\b', r'\bxoay\b',
                r'\btrái\b.*\bphải\b', r'\blên\b.*\bxuống\b',
                r'\bđi\s+đâu\b'
            ],
            Intent.SMALL_TALK: [
                r'\bchào\b', r'\bhỏi\b', r'\bcảm\s+ơn\b',
                r'\btạm\s+biệt\b', r'\bbye\b', r'\btên\s+gì\b'
            ],
            Intent.CLARIFICATION_REQUEST: [
                r'\bí\s+là\b', r'\bthế\s+nào\b', r'\bý\s+là\b',
                r'\bgiải\s+thích\b', r'\brõ\s+hơn\b'
            ]
        }
        
        # Continuation indicators
        self._continuation_patterns = [
            r'\bcòn\b', r'\bthì\s+sao\b', r'\bvậy\b',
            r'\btiếp\b', r'\bnữa\b', r'\bthế\s+còn\b'
        ]
    
    def initialize(self, context_manager) -> None:
        """
        Initialize with ConversationContextManager instance.
        
        Requirements: 13.1, 13.2
        
        Args:
            context_manager: ConversationContextManager instance for managing conversation history
        """
        self.context_manager = context_manager
        print("✅ DialogueController initialized with ConversationContextManager")
    
    def process_input(self, session_id: str, user_input: str) -> DialogueResponse:
        """
        Process user input and generate dialogue response.
        
        Requirements: 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11
        
        Args:
            session_id: Session identifier
            user_input: User's text input
            
        Returns:
            DialogueResponse with response text, intent, and continuation flag
        """
        # Get or create dialogue state
        if session_id not in self._dialogue_states:
            self._dialogue_states[session_id] = DialogueState()
        
        state = self._dialogue_states[session_id]
        state.turn_count += 1
        
        # Parse input to identify intent and extract entities
        intent, confidence, entities = self._parse_input(user_input, state)
        
        # Update dialogue state
        state.current_intent = intent
        state.slot_values.update(entities)
        
        # Determine if clarification is needed
        requires_clarification = self._needs_clarification(intent, entities, state)
        state.clarification_needed = requires_clarification
        
        # Check if this is a follow-up question
        is_followup = self._is_followup_question(user_input)
        
        # Determine if conversation should continue
        should_continue = (
            is_followup or
            requires_clarification or
            state.confirmation_pending or
            intent == Intent.CLARIFICATION_REQUEST
        )
        
        # Generate suggested follow-ups
        suggested_followups = self._generate_followups(intent, state) if not requires_clarification else []
        
        # Generate response text (placeholder - will be replaced by AI response)
        response_text = self._generate_response_placeholder(intent, requires_clarification, state)
        
        return DialogueResponse(
            response_text=response_text,
            should_continue=should_continue,
            intent=intent,
            confidence=confidence,
            requires_clarification=requires_clarification,
            suggested_followups=suggested_followups
        )
    
    def should_continue_listening(self, session_id: str) -> bool:
        """
        Determine if conversation should continue listening for follow-up.
        
        Requirements: 13.12
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if should continue listening, False otherwise
        """
        if session_id not in self._dialogue_states:
            return False
        
        state = self._dialogue_states[session_id]
        
        # Continue if waiting for clarification, confirmation, or follow-up
        return (
            state.clarification_needed or
            state.confirmation_pending or
            state.current_intent in [Intent.CLARIFICATION_REQUEST, Intent.CAMERA_CONTROL]
        )
    
    def reset_dialogue_state(self, session_id: str) -> None:
        """
        Reset dialogue state for a session.
        
        Requirements: 13.13
        
        Args:
            session_id: Session identifier
        """
        if session_id in self._dialogue_states:
            del self._dialogue_states[session_id]
            print(f"🔄 Dialogue state reset for session {session_id}")
    
    def get_dialogue_state(self, session_id: str) -> Optional[DialogueState]:
        """
        Get current dialogue state for a session.
        
        Requirements: 13.14
        
        Args:
            session_id: Session identifier
            
        Returns:
            DialogueState if exists, None otherwise
        """
        return self._dialogue_states.get(session_id)
    
    def _parse_input(self, user_input: str, state: DialogueState) -> tuple:
        """
        Parse user input to identify intent and extract entities.
        
        Requirements: 13.4, 13.5
        
        Args:
            user_input: User's text input
            state: Current dialogue state
            
        Returns:
            Tuple of (intent, confidence, entities)
        """
        user_input_lower = user_input.lower()
        
        # Check each intent pattern
        best_intent = Intent.UNKNOWN
        best_confidence = 0.3
        
        for intent, patterns in self._intent_patterns.items():
            matches = sum(1 for pattern in patterns if re.search(pattern, user_input_lower))
            if matches > 0:
                confidence = min(0.9, 0.5 + (matches * 0.2))
                if confidence > best_confidence:
                    best_intent = intent
                    best_confidence = confidence
        
        # Extract entities based on intent
        entities = self._extract_entities(user_input, best_intent)
        
        return best_intent, best_confidence, entities
    
    def _extract_entities(self, user_input: str, intent: Intent) -> Dict[str, Any]:
        """
        Extract entities from user input based on intent.
        
        Args:
            user_input: User's text input
            intent: Identified intent
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        
        if intent == Intent.CALCULATION:
            # Extract mathematical expression
            match = re.search(r'(\d+)\s*[\+\-\*\/×÷]\s*(\d+)', user_input)
            if match:
                entities['expression'] = match.group(0)
        
        elif intent == Intent.WEATHER_QUERY:
            # Extract location (if specified)
            location_match = re.search(r'\b(hà nội|sài gòn|đà nẵng|huế)\b', user_input.lower())
            if location_match:
                entities['location'] = location_match.group(1)
            
            # Extract time reference
            if re.search(r'\bhôm\s+nay\b', user_input.lower()):
                entities['time'] = 'today'
            elif re.search(r'\bngày\s+mai\b', user_input.lower()):
                entities['time'] = 'tomorrow'
        
        elif intent == Intent.CAMERA_CONTROL:
            # Extract direction
            if re.search(r'\btrái\b', user_input.lower()):
                entities['direction'] = 'left'
            elif re.search(r'\bphải\b', user_input.lower()):
                entities['direction'] = 'right'
            elif re.search(r'\blên\b', user_input.lower()):
                entities['direction'] = 'up'
            elif re.search(r'\bxuống\b', user_input.lower()):
                entities['direction'] = 'down'
        
        return entities
    
    def _needs_clarification(self, intent: Intent, entities: Dict[str, Any], 
                            state: DialogueState) -> bool:
        """
        Determine if clarification is needed.
        
        Requirements: 13.10
        
        Args:
            intent: Identified intent
            entities: Extracted entities
            state: Current dialogue state
            
        Returns:
            True if clarification needed, False otherwise
        """
        # Unknown intent needs clarification
        if intent == Intent.UNKNOWN and state.turn_count > 0:
            return True
        
        # Camera control without direction needs clarification
        if intent == Intent.CAMERA_CONTROL and 'direction' not in entities:
            return True
        
        # Low entity extraction for complex intents
        if intent in [Intent.WEATHER_QUERY, Intent.CAMERA_CONTROL] and len(entities) == 0:
            return False  # AI can handle with defaults
        
        return False
    
    def _is_followup_question(self, user_input: str) -> bool:
        """
        Check if input is a follow-up question.
        
        Requirements: 13.8
        
        Args:
            user_input: User's text input
            
        Returns:
            True if follow-up question, False otherwise
        """
        user_input_lower = user_input.lower()
        
        for pattern in self._continuation_patterns:
            if re.search(pattern, user_input_lower):
                return True
        
        return False
    
    def _generate_followups(self, intent: Intent, state: DialogueState) -> List[str]:
        """
        Generate suggested follow-up questions.
        
        Requirements: 13.3
        
        Args:
            intent: Current intent
            state: Dialogue state
            
        Returns:
            List of suggested follow-up questions
        """
        followups = []
        
        if intent == Intent.CALCULATION:
            followups = [
                "Còn phép tính khác không?",
                "Tính thêm gì nữa không?"
            ]
        elif intent == Intent.WEATHER_QUERY:
            followups = [
                "Còn hỏi thời tiết ngày khác không?",
                "Cần biết nhiệt độ không?"
            ]
        elif intent == Intent.CAMERA_CONTROL:
            followups = [
                "Điều khiển camera thêm không?",
                "Quay về vị trí ban đầu không?"
            ]
        
        return followups[:2]  # Limit to 2 suggestions
    
    def _generate_response_placeholder(self, intent: Intent, 
                                      requires_clarification: bool,
                                      state: DialogueState) -> str:
        """
        Generate placeholder response (will be replaced by AI).
        
        Args:
            intent: Identified intent
            requires_clarification: Whether clarification is needed
            state: Dialogue state
            
        Returns:
            Placeholder response text
        """
        if requires_clarification:
            if intent == Intent.UNKNOWN:
                return "Tỷ Tỷ không hiểu rõ ý bạn. Bạn nói rõ hơn được không?"
            elif intent == Intent.CAMERA_CONTROL:
                return "Bạn muốn quay camera theo hướng nào? Trái, phải, lên hay xuống?"
        
        # Default placeholder - will be replaced by AI response
        return "[AI Response]"


# Singleton instance
_dialogue_controller = None


def get_dialogue_controller() -> DialogueController:
    """Get or create DialogueController instance"""
    global _dialogue_controller
    if _dialogue_controller is None:
        _dialogue_controller = DialogueController()
    return _dialogue_controller


if __name__ == "__main__":
    # Test DialogueController
    print("🧪 Testing DialogueController\n")
    
    controller = get_dialogue_controller()
    
    # Mock context manager for testing
    class MockContextManager:
        pass
    
    controller.initialize(MockContextManager())
    
    # Test 1: Calculation intent
    print("📝 Test 1: Calculation")
    response = controller.process_input("test_session_1", "1+1 bằng mấy?")
    print(f"Intent: {response.intent}")
    print(f"Confidence: {response.confidence}")
    print(f"Should continue: {response.should_continue}")
    print(f"Requires clarification: {response.requires_clarification}")
    print(f"Suggested followups: {response.suggested_followups}\n")
    
    # Test 2: Follow-up question
    print("📝 Test 2: Follow-up question")
    response = controller.process_input("test_session_1", "còn 2+2 thì sao?")
    print(f"Intent: {response.intent}")
    print(f"Should continue: {response.should_continue}\n")
    
    # Test 3: Weather query
    print("📝 Test 3: Weather query")
    response = controller.process_input("test_session_2", "thời tiết hôm nay ở Hà Nội")
    print(f"Intent: {response.intent}")
    print(f"Confidence: {response.confidence}")
    state = controller.get_dialogue_state("test_session_2")
    print(f"Extracted entities: {state.slot_values}\n")
    
    # Test 4: Camera control
    print("📝 Test 4: Camera control")
    response = controller.process_input("test_session_3", "quay camera sang trái")
    print(f"Intent: {response.intent}")
    state = controller.get_dialogue_state("test_session_3")
    print(f"Extracted entities: {state.slot_values}")
    print(f"Should continue listening: {controller.should_continue_listening('test_session_3')}\n")
    
    # Test 5: Small talk
    print("📝 Test 5: Small talk")
    response = controller.process_input("test_session_4", "chào Tỷ Tỷ")
    print(f"Intent: {response.intent}")
    print(f"Confidence: {response.confidence}\n")
    
    # Test 6: Unknown intent (needs clarification)
    print("📝 Test 6: Unknown intent")
    controller.process_input("test_session_5", "xin chào")  # First turn
    response = controller.process_input("test_session_5", "ádfadfads")  # Gibberish
    print(f"Intent: {response.intent}")
    print(f"Requires clarification: {response.requires_clarification}")
    print(f"Response: {response.response_text}\n")
    
    # Test 7: Reset dialogue state
    print("📝 Test 7: Reset dialogue state")
    print(f"State before reset: {controller.get_dialogue_state('test_session_1')}")
    controller.reset_dialogue_state("test_session_1")
    print(f"State after reset: {controller.get_dialogue_state('test_session_1')}\n")
    
    print("✅ All tests completed!")
