"""
Integration test for conversation management components
Tests conversation context maintenance across multiple turns
"""

import unittest
from modules.context_manager import ConversationContextManager, Role
from modules.dialogue_controller import DialogueController, Intent
from modules.prompt_builder import PromptBuilder, ResponseMode


class TestConversationIntegration(unittest.TestCase):
    """Test integration of Context Manager, Dialogue Controller, and Prompt Builder"""
    
    def setUp(self):
        """Set up test components"""
        self.context_manager = ConversationContextManager(
            max_context_turns=10,
            persistence_enabled=False
        )
        self.dialogue_controller = DialogueController()
        self.dialogue_controller.initialize(self.context_manager)
        self.prompt_builder = PromptBuilder()
        self.prompt_builder.initialize("Bạn là Tỷ Tỷ, trợ lý AI thông minh")
    
    def test_multi_turn_conversation_context_preserved(self):
        """
        Test that conversation context is maintained across multiple turns
        This validates Requirements 12 (Context Manager) and 13 (Dialogue Controller)
        """
        # Create a session
        session_id = self.context_manager.create_session(user_id="test_user")
        
        # Turn 1: User asks a math question
        user_input_1 = "1+1 bằng mấy?"
        self.context_manager.add_message(session_id, Role.USER, user_input_1)
        response_1 = self.dialogue_controller.process_input(session_id, user_input_1)
        
        # Verify intent detection
        self.assertEqual(response_1.intent, Intent.CALCULATION)
        
        # Add assistant response to context
        assistant_response_1 = "1+1 bằng 2"
        self.context_manager.add_message(session_id, Role.ASSISTANT, assistant_response_1)
        
        # Turn 2: Follow-up question without wake word
        user_input_2 = "còn 2+2 thì sao?"
        self.context_manager.add_message(session_id, Role.USER, user_input_2)
        response_2 = self.dialogue_controller.process_input(session_id, user_input_2)
        
        # Verify continuation is detected
        self.assertTrue(response_2.should_continue)
        self.assertEqual(response_2.intent, Intent.CALCULATION)
        
        # Add assistant response
        assistant_response_2 = "2+2 bằng 4"
        self.context_manager.add_message(session_id, Role.ASSISTANT, assistant_response_2)
        
        # Verify context contains all messages
        context = self.context_manager.get_context(session_id)
        self.assertEqual(len(context.messages), 4)  # 2 user + 2 assistant
        
        # Verify message order is preserved
        self.assertEqual(context.messages[0].content, user_input_1)
        self.assertEqual(context.messages[1].content, assistant_response_1)
        self.assertEqual(context.messages[2].content, user_input_2)
        self.assertEqual(context.messages[3].content, assistant_response_2)
        
        # Verify turn count
        dialogue_state = self.dialogue_controller.get_dialogue_state(session_id)
        self.assertEqual(dialogue_state.turn_count, 2)
    
    def test_prompt_builder_uses_conversation_context(self):
        """
        Test that Prompt Builder generates valid prompts with conversation history
        This validates Requirement 14 (Context-Aware Prompt Builder)
        """
        # Create session with conversation history
        session_id = self.context_manager.create_session()
        self.context_manager.add_message(session_id, Role.USER, "1+1 bằng mấy?")
        self.context_manager.add_message(session_id, Role.ASSISTANT, "1+1 bằng 2")
        self.context_manager.add_message(session_id, Role.USER, "còn 2+2 thì sao?")
        
        # Get context
        context = self.context_manager.get_context(session_id)
        
        # Build prompt
        prompt = self.prompt_builder.build_prompt(context, "còn 2+2 thì sao?")
        
        # Verify prompt structure
        self.assertIn("[System Instructions]", prompt)
        self.assertIn("Bạn là Tỷ Tỷ", prompt)
        self.assertIn("[Conversation History]", prompt)
        self.assertIn("1+1 bằng mấy?", prompt)
        self.assertIn("1+1 bằng 2", prompt)
        self.assertIn("[Current User Input]", prompt)
        self.assertIn("còn 2+2 thì sao?", prompt)
        
        # Verify prompt is valid (non-empty, reasonable length)
        self.assertGreater(len(prompt), 100)
        self.assertLess(len(prompt), 5000)
    
    def test_context_sliding_window_with_prompt_builder(self):
        """
        Test that sliding window works correctly with prompt builder
        """
        # Create session
        session_id = self.context_manager.create_session()
        
        # Add many messages to exceed window
        for i in range(15):
            self.context_manager.add_message(session_id, Role.USER, f"Question {i}")
            self.context_manager.add_message(session_id, Role.ASSISTANT, f"Answer {i}")
        
        # Get context with sliding window (default max_turns=10, so 20 messages)
        context = self.context_manager.get_context(session_id, max_turns=5)
        
        # Verify only last 5 turns (10 messages) are included
        self.assertEqual(len(context.messages), 10)
        
        # Verify most recent messages are preserved
        self.assertIn("Question 14", context.messages[-2].content)
        self.assertIn("Answer 14", context.messages[-1].content)
        
        # Build prompt with truncated context
        prompt = self.prompt_builder.build_prompt(context, "Final question")
        
        # Verify old messages are not in prompt
        self.assertNotIn("Question 0", prompt)
        self.assertNotIn("Answer 0", prompt)
        
        # Verify recent messages are in prompt
        self.assertIn("Question 14", prompt)
        self.assertIn("Answer 14", prompt)
    
    def test_different_response_modes(self):
        """Test that different response modes affect prompt generation"""
        session_id = self.context_manager.create_session()
        self.context_manager.add_message(session_id, Role.USER, "Hello")
        context = self.context_manager.get_context(session_id)
        
        # Test CONCISE mode
        self.prompt_builder.set_response_mode(ResponseMode.CONCISE)
        prompt_concise = self.prompt_builder.build_prompt(context, "Hello")
        # Check for Vietnamese concise instruction
        self.assertTrue("ngắn gọn" in prompt_concise or "súc tích" in prompt_concise)
        
        # Test DETAILED mode
        self.prompt_builder.set_response_mode(ResponseMode.DETAILED)
        prompt_detailed = self.prompt_builder.build_prompt(context, "Hello")
        # Check for Vietnamese detailed instruction
        self.assertTrue("chi tiết" in prompt_detailed)
        
        # Verify prompts are different
        self.assertNotEqual(prompt_concise, prompt_detailed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
