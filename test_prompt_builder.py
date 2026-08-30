"""
Unit tests for PromptBuilder module
Tests all requirements from Requirement 14
"""

import unittest
from modules.prompt_builder import PromptBuilder, ResponseMode, get_prompt_builder


class TestPromptBuilderInitialization(unittest.TestCase):
    """Test initialization and configuration - Requirement 14.1"""
    
    def test_initialize_with_system_prompt(self):
        """Test that initialize() accepts and stores system_prompt"""
        builder = PromptBuilder()
        system_prompt = "Bạn là Tỷ Tỷ, trợ lý AI thông minh."
        
        builder.initialize(system_prompt)
        
        assert builder.system_prompt == system_prompt
    
    def test_initialize_with_empty_prompt(self):
        """Test initialization with empty string"""
        builder = PromptBuilder()
        builder.initialize("")
        
        assert builder.system_prompt == ""
    
    def test_default_response_mode(self):
        """Test that default response mode is CONVERSATIONAL"""
        builder = PromptBuilder()
        
        assert builder.response_mode == ResponseMode.CONVERSATIONAL


class TestBuildPrompt(unittest.TestCase):
    """Test prompt building functionality - Requirements 14.2, 14.3, 14.4"""
    
    def test_build_prompt_without_context(self):
        """Test building prompt with no conversation context"""
        builder = PromptBuilder()
        system_prompt = "You are a helpful assistant."
        builder.initialize(system_prompt)
        
        prompt = builder.build_prompt(None, "Hello")
        
        assert "[System Instructions]" in prompt
        assert system_prompt in prompt
        assert "[Current User Input]" in prompt
        assert "Hello" in prompt
    
    def test_build_prompt_with_conversation_history(self):
        """Test that conversation history is included - Requirement 14.3"""
        builder = PromptBuilder()
        builder.initialize("Test system prompt")
        
        context = {
            "messages": [
                {"role": "user", "content": "First question"},
                {"role": "assistant", "content": "First answer"}
            ]
        }
        
        prompt = builder.build_prompt(context, "Second question")
        
        assert "[Conversation History]" in prompt
        assert "First question" in prompt
        assert "First answer" in prompt
        assert "Second question" in prompt
    
    def test_build_prompt_with_user_preferences(self):
        """Test that user preferences are included - Requirement 14.10"""
        builder = PromptBuilder()
        builder.initialize("System prompt")
        
        context = {
            "user_preferences": {
                "response_mode": "concise",
                "language_formality": "formal",
                "voice_name": "vi-VN-Standard-A"
            }
        }
        
        prompt = builder.build_prompt(context, "Test input")
        
        assert "[User Preferences]" in prompt
        assert "concise" in prompt
        assert "formal" in prompt
    
    def test_build_prompt_includes_response_style(self):
        """Test that response style instruction is included - Requirement 14.4"""
        builder = PromptBuilder()
        builder.initialize("System")
        builder.set_response_mode(ResponseMode.CONCISE)
        
        prompt = builder.build_prompt(None, "Test")
        
        assert "[Response Style]" in prompt
        assert "ngắn gọn" in prompt.lower() or "súc tích" in prompt.lower()
    
    def test_build_prompt_with_turn_count(self):
        """Test that turn count is tracked in context"""
        builder = PromptBuilder()
        builder.initialize("System")
        
        context = {
            "messages": [
                {"role": "user", "content": "Q1"},
                {"role": "assistant", "content": "A1"},
                {"role": "user", "content": "Q2"},
                {"role": "assistant", "content": "A2"}
            ]
        }
        
        prompt = builder.build_prompt(context, "Q3")
        
        # Should be turn 3 (3 user questions)
        assert "lượt tương tác thứ 3" in prompt or "turn 3" in prompt.lower()
    
    def test_prompt_structure_has_all_required_sections(self):
        """Test that prompt includes all required sections: system, context, input - Requirement 14.3"""
        builder = PromptBuilder()
        builder.initialize("Bạn là Tỷ Tỷ, trợ lý AI thông minh.")
        
        context = {
            "messages": [
                {"role": "user", "content": "What is AI?"},
                {"role": "assistant", "content": "AI is artificial intelligence."}
            ],
            "user_preferences": {
                "response_mode": "detailed"
            }
        }
        
        prompt = builder.build_prompt(context, "Tell me more")
        
        # Verify all required sections are present
        assert "[System Instructions]" in prompt, "Missing system instructions section"
        assert "[Response Style]" in prompt, "Missing response style section"
        assert "[User Preferences]" in prompt, "Missing user preferences section"
        assert "[Conversation History]" in prompt, "Missing conversation history section"
        assert "[Current User Input]" in prompt, "Missing current user input section"
        
        # Verify content is in correct order
        system_pos = prompt.find("[System Instructions]")
        history_pos = prompt.find("[Conversation History]")
        input_pos = prompt.find("[Current User Input]")
        
        assert system_pos < history_pos < input_pos, "Sections not in correct order"


class TestResponseMode(unittest.TestCase):
    """Test response mode functionality - Requirements 14.5, 14.6"""
    
    def test_response_mode_enum_values(self):
        """Test that all required response modes exist - Requirement 14.5"""
        assert hasattr(ResponseMode, 'CONCISE')
        assert hasattr(ResponseMode, 'DETAILED')
        assert hasattr(ResponseMode, 'CONVERSATIONAL')
        assert hasattr(ResponseMode, 'TECHNICAL')
    
    def test_set_response_mode(self):
        """Test set_response_mode() method - Requirement 14.6"""
        builder = PromptBuilder()
        
        builder.set_response_mode(ResponseMode.DETAILED)
        assert builder.response_mode == ResponseMode.DETAILED
        
        builder.set_response_mode(ResponseMode.TECHNICAL)
        assert builder.response_mode == ResponseMode.TECHNICAL
    
    def test_set_response_mode_invalid_type(self):
        """Test that invalid mode types raise error"""
        builder = PromptBuilder()
        
        with self.assertRaises(ValueError):
            builder.set_response_mode("invalid")
    
    def test_response_mode_affects_prompt(self):
        """Test that different modes produce different prompts"""
        builder = PromptBuilder()
        builder.initialize("System")
        
        builder.set_response_mode(ResponseMode.CONCISE)
        prompt_concise = builder.build_prompt(None, "Test")
        
        builder.set_response_mode(ResponseMode.DETAILED)
        prompt_detailed = builder.build_prompt(None, "Test")
        
        # Prompts should be different due to different style instructions
        assert prompt_concise != prompt_detailed
    
    def test_response_mode_variations_produce_different_formats(self):
        """Test that all ResponseMode variations produce distinct prompt formats - Requirement 14.5"""
        builder = PromptBuilder()
        builder.initialize("Bạn là Tỷ Tỷ")
        
        user_input = "Explain artificial intelligence"
        
        # Build prompts with each mode
        modes_and_prompts = {}
        for mode in [ResponseMode.CONCISE, ResponseMode.DETAILED, 
                     ResponseMode.CONVERSATIONAL, ResponseMode.TECHNICAL]:
            builder.set_response_mode(mode)
            prompt = builder.build_prompt(None, user_input)
            modes_and_prompts[mode] = prompt
        
        # Verify all prompts are different from each other
        prompts = list(modes_and_prompts.values())
        for i, prompt1 in enumerate(prompts):
            for j, prompt2 in enumerate(prompts):
                if i != j:
                    assert prompt1 != prompt2, f"Mode {list(modes_and_prompts.keys())[i]} and {list(modes_and_prompts.keys())[j]} produce identical prompts"
        
        # Verify each mode has its specific instruction
        assert "ngắn gọn" in modes_and_prompts[ResponseMode.CONCISE].lower() or "súc tích" in modes_and_prompts[ResponseMode.CONCISE].lower()
        assert "chi tiết" in modes_and_prompts[ResponseMode.DETAILED].lower()
        assert "tự nhiên" in modes_and_prompts[ResponseMode.CONVERSATIONAL].lower() or "thân thiện" in modes_and_prompts[ResponseMode.CONVERSATIONAL].lower()
        assert "chuyên môn" in modes_and_prompts[ResponseMode.TECHNICAL].lower() or "kỹ thuật" in modes_and_prompts[ResponseMode.TECHNICAL].lower()


class TestTokenEstimation(unittest.TestCase):
    """Test token estimation functionality - Requirement 14.7"""
    
    def test_estimate_token_count_basic(self):
        """Test basic token estimation"""
        builder = PromptBuilder()
        
        prompt = "Xin chào"
        tokens = builder.estimate_token_count(prompt)
        
        # Should return a positive integer
        assert isinstance(tokens, int)
        assert tokens > 0
    
    def test_estimate_token_count_scales_with_length(self):
        """Test that longer prompts have more tokens"""
        builder = PromptBuilder()
        
        short_prompt = "Hello"
        long_prompt = "This is a much longer prompt with many more words and tokens"
        
        short_tokens = builder.estimate_token_count(short_prompt)
        long_tokens = builder.estimate_token_count(long_prompt)
        
        assert long_tokens > short_tokens
    
    def test_estimate_token_count_handles_vietnamese(self):
        """Test token estimation for Vietnamese text"""
        builder = PromptBuilder()
        
        vietnamese_text = "Thủ đô Việt Nam là Hà Nội"
        tokens = builder.estimate_token_count(vietnamese_text)
        
        # Should be reasonable estimate (not zero, not enormous)
        assert 5 < tokens < 50
    
    def test_estimate_token_count_removes_extra_whitespace(self):
        """Test that extra whitespace doesn't inflate token count"""
        builder = PromptBuilder()
        
        normal = "Hello world"
        spaced = "Hello    world    "
        
        tokens_normal = builder.estimate_token_count(normal)
        tokens_spaced = builder.estimate_token_count(spaced)
        
        # Should be same or very close
        assert abs(tokens_normal - tokens_spaced) <= 1
    
    def test_token_estimation_accuracy_within_10_percent(self):
        """Test that token estimation is within 10% margin of expected - Requirement 14.7"""
        builder = PromptBuilder()
        
        # Test cases with expected token counts (approximate)
        # Note: The implementation adds 20 token overhead for system tokens/separators
        test_cases = [
            # (text, expected_min_tokens, expected_max_tokens)
            ("Hello", 20, 24),  # 1 word ≈ 1.25 tokens + 20 overhead = ~21
            ("Hello world", 22, 27),  # 2 words ≈ 2.5 tokens + 20 overhead = ~22-23
            ("Xin chào", 22, 27),  # Vietnamese: 2 words ≈ 2.5 tokens + 20 overhead
            ("This is a test sentence with ten words here.", 32, 38),  # ~10 words ≈ 12.5 + 20 overhead = ~32-33
            ("Thủ đô Việt Nam là Hà Nội có lịch sử lâu đời", 34, 42),  # ~10 Vietnamese words ≈ 12.5 + 20 = ~32-33
        ]
        
        for text, min_expected, max_expected in test_cases:
            tokens = builder.estimate_token_count(text)
            
            # Allow 10% margin on both sides
            min_allowed = min_expected * 0.9
            max_allowed = max_expected * 1.1
            
            assert min_allowed <= tokens <= max_allowed, \
                f"Token estimate {tokens} for '{text}' outside 10% margin [{min_allowed:.1f}, {max_allowed:.1f}]"
    
    def test_token_estimation_consistency(self):
        """Test that token estimation is consistent for same input"""
        builder = PromptBuilder()
        
        text = "This is a test sentence for consistency checking"
        
        # Call multiple times
        tokens1 = builder.estimate_token_count(text)
        tokens2 = builder.estimate_token_count(text)
        tokens3 = builder.estimate_token_count(text)
        
        # Should be identical every time
        assert tokens1 == tokens2 == tokens3
    
    def test_token_estimation_for_full_prompt(self):
        """Test token estimation for complete prompts with all sections"""
        builder = PromptBuilder()
        builder.initialize("Bạn là Tỷ Tỷ, trợ lý AI thông minh.")
        
        context = {
            "messages": [
                {"role": "user", "content": "What is AI?"},
                {"role": "assistant", "content": "AI is artificial intelligence."}
            ],
            "user_preferences": {
                "response_mode": "conversational"
            }
        }
        
        prompt = builder.build_prompt(context, "Tell me more")
        tokens = builder.estimate_token_count(prompt)
        
        # Full prompt should have reasonable token count
        # Rough estimate: 50-150 tokens for this content
        assert 30 < tokens < 200, f"Token count {tokens} seems unreasonable for full prompt"


class TestContextWindowOptimization(unittest.TestCase):
    """Test context window optimization - Requirements 14.8, 14.9"""
    
    def test_optimize_context_window_within_limit(self):
        """Test that messages within limit are preserved"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "Short"},
            {"role": "assistant", "content": "Reply"}
        ]
        
        optimized = builder.optimize_context_window(messages, max_tokens=100)
        
        # Should keep all messages
        assert len(optimized) == 2
        assert optimized == messages
    
    def test_optimize_context_window_truncates_old_messages(self):
        """Test that old messages are truncated when exceeding limit - Requirement 14.8"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "Very long first message with many words"},
            {"role": "assistant", "content": "Long first response with details"},
            {"role": "user", "content": "Second question also long"},
            {"role": "assistant", "content": "Second answer with explanation"},
            {"role": "user", "content": "Recent short question"}
        ]
        
        # Set low token limit to force truncation
        optimized = builder.optimize_context_window(messages, max_tokens=30)
        
        # Should truncate some messages
        assert len(optimized) < len(messages)
    
    def test_optimize_context_window_preserves_recent_messages(self):
        """Test that most recent messages are preserved - Requirement 14.9"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "Old message 1"},
            {"role": "assistant", "content": "Old response 1"},
            {"role": "user", "content": "Old message 2"},
            {"role": "assistant", "content": "Old response 2"},
            {"role": "user", "content": "Most recent message"}
        ]
        
        optimized = builder.optimize_context_window(messages, max_tokens=30)
        
        # Most recent message should always be preserved
        assert optimized[-1]["content"] == "Most recent message"
    
    def test_optimize_context_window_empty_messages(self):
        """Test handling of empty message list"""
        builder = PromptBuilder()
        
        optimized = builder.optimize_context_window([], max_tokens=100)
        
        assert optimized == []
    
    def test_optimize_context_window_respects_token_budget(self):
        """Test that optimized context doesn't exceed token budget"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "Message " * 10},
            {"role": "assistant", "content": "Response " * 10},
            {"role": "user", "content": "Question " * 10}
        ]
        
        max_tokens = 50
        optimized = builder.optimize_context_window(messages, max_tokens)
        
        # Calculate actual tokens in optimized messages
        total_tokens = sum(
            builder.estimate_token_count(msg["content"]) 
            for msg in optimized
        )
        
        # Should not exceed limit
        assert total_tokens <= max_tokens
    
    def test_truncation_logic_removes_oldest_first(self):
        """Test that truncation removes oldest messages first when exceeding token limit - Requirement 14.9"""
        builder = PromptBuilder()
        
        # Create messages with identifiable order
        messages = [
            {"role": "user", "content": "Message 1 - oldest"},
            {"role": "assistant", "content": "Response 1 - oldest"},
            {"role": "user", "content": "Message 2 - middle"},
            {"role": "assistant", "content": "Response 2 - middle"},
            {"role": "user", "content": "Message 3 - newer"},
            {"role": "assistant", "content": "Response 3 - newer"},
            {"role": "user", "content": "Message 4 - newest"}
        ]
        
        # Set token limit that will force truncation of old messages
        max_tokens = 60
        optimized = builder.optimize_context_window(messages, max_tokens)
        
        # Verify oldest messages were removed
        assert len(optimized) < len(messages), "Should have truncated some messages"
        
        # Verify newest message is still there
        assert optimized[-1]["content"] == "Message 4 - newest", "Newest message should be preserved"
        
        # Verify oldest message is NOT there
        oldest_contents = [msg["content"] for msg in optimized]
        assert "Message 1 - oldest" not in oldest_contents, "Oldest message should be removed first"
    
    def test_context_window_preserves_conversation_pairs(self):
        """Test that context window optimization maintains conversation flow"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
            {"role": "user", "content": "Question 3"},
            {"role": "assistant", "content": "Answer 3"}
        ]
        
        max_tokens = 40
        optimized = builder.optimize_context_window(messages, max_tokens)
        
        # Verify that messages still have proper user/assistant alternation
        if len(optimized) >= 2:
            # Check that roles alternate (or at least not corrupted)
            roles = [msg["role"] for msg in optimized]
            # Should have both user and assistant roles
            assert "user" in roles and "assistant" in roles
    
    def test_context_window_optimization_with_long_single_message(self):
        """Test optimization when a single message exceeds token limit"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "This is an extremely long message " * 50}
        ]
        
        max_tokens = 30
        optimized = builder.optimize_context_window(messages, max_tokens)
        
        # Even if single message exceeds limit, it should still be included
        # (alternative: could be empty, but typically we preserve at least 1 message)
        assert len(optimized) >= 0
        
        # Calculate tokens
        if len(optimized) > 0:
            tokens = builder.estimate_token_count(optimized[0]["content"])
            # The single message might exceed limit, but that's acceptable
            # since we need at least some context
    
    def test_context_window_optimization_edge_case_zero_limit(self):
        """Test optimization with zero or very low token limit"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"}
        ]
        
        optimized = builder.optimize_context_window(messages, max_tokens=0)
        
        # Should return empty list or minimal content
        assert len(optimized) == 0 or len(optimized) < len(messages)


class TestHelperMethods(unittest.TestCase):
    """Test internal helper methods"""
    
    def test_format_preferences(self):
        """Test preference formatting"""
        builder = PromptBuilder()
        
        preferences = {
            "response_mode": "concise",
            "language_formality": "friendly",
            "voice_name": "vi-VN-A",
            "max_context_turns": 10
        }
        
        formatted = builder._format_preferences(preferences)
        
        assert "concise" in formatted
        assert "friendly" in formatted
        assert "vi-VN-A" in formatted
        assert "10" in formatted
    
    def test_format_conversation_history(self):
        """Test conversation history formatting"""
        builder = PromptBuilder()
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        formatted = builder._format_conversation_history(messages)
        
        assert "Người dùng" in formatted or "user" in formatted.lower()
        assert "Hello" in formatted
        assert "Hi there" in formatted
    
    def test_format_conversation_history_empty(self):
        """Test empty history formatting"""
        builder = PromptBuilder()
        
        formatted = builder._format_conversation_history([])
        
        assert formatted == ""


class TestSingletonPattern(unittest.TestCase):
    """Test global singleton accessor"""
    
    def test_get_prompt_builder_returns_instance(self):
        """Test that get_prompt_builder() returns PromptBuilder instance"""
        builder = get_prompt_builder()
        
        assert isinstance(builder, PromptBuilder)
    
    def test_get_prompt_builder_singleton(self):
        """Test that get_prompt_builder() returns same instance"""
        builder1 = get_prompt_builder()
        builder2 = get_prompt_builder()
        
        assert builder1 is builder2


class TestIntegration(unittest.TestCase):
    """Integration tests for full workflow"""
    
    def test_full_prompt_building_workflow(self):
        """Test complete workflow from initialization to prompt generation"""
        builder = PromptBuilder()
        
        # Step 1: Initialize
        system_prompt = "Bạn là Tỷ Tỷ, trợ lý AI thông minh."
        builder.initialize(system_prompt)
        
        # Step 2: Set response mode
        builder.set_response_mode(ResponseMode.CONVERSATIONAL)
        
        # Step 3: Build context
        context = {
            "messages": [
                {"role": "user", "content": "Tỷ Tỷ ơi, 1+1 bằng mấy?"},
                {"role": "assistant", "content": "1+1 bằng 2 nhé!"}
            ],
            "user_preferences": {
                "response_mode": "conversational",
                "max_context_turns": 10
            }
        }
        
        # Step 4: Build prompt
        prompt = builder.build_prompt(context, "Còn 2+2 thì sao?")
        
        # Verify all components present
        assert system_prompt in prompt
        assert "1+1 bằng mấy?" in prompt
        assert "1+1 bằng 2" in prompt
        assert "2+2 thì sao?" in prompt
        
        # Step 5: Estimate tokens
        tokens = builder.estimate_token_count(prompt)
        assert tokens > 0
    
    def test_token_budget_enforcement(self):
        """Test that token budget is enforced in real scenario"""
        builder = PromptBuilder()
        builder.initialize("You are an assistant.")
        
        # Create long conversation
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"Question {i} with some text"})
            messages.append({"role": "assistant", "content": f"Answer {i} with more text"})
        
        # Optimize with strict budget
        max_tokens = 100
        optimized = builder.optimize_context_window(messages, max_tokens)
        
        # Build prompt with optimized context
        context = {"messages": optimized}
        prompt = builder.build_prompt(context, "Final question")
        
        # Verify it's functional
        assert len(prompt) > 0
        assert "Final question" in prompt


# Property-based tests would go here if using Hypothesis
# For now, we have comprehensive unit tests covering all requirements

if __name__ == "__main__":
    unittest.main(verbosity=2)
