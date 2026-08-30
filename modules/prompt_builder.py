"""
Prompt Builder Module - Context-Aware Prompt Construction
Xây dựng prompts tối ưu cho Gemini AI với conversation context
"""

from enum import Enum
from typing import List, Dict, Any, Optional
import re


class ResponseMode(Enum):
    """AI response style modes"""
    CONCISE = "concise"
    DETAILED = "detailed"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"


class PromptBuilder:
    """
    Xây dựng prompts thông minh cho AI với conversation context và user preferences.
    
    Responsibilities:
    - Combine system prompt, conversation history, and user input
    - Format prompts according to Gemini API requirements
    - Apply token limit constraints (truncate old messages if needed)
    - Include user preferences (response style, language formality)
    - Support different response modes
    - Optimize prompt structure for cost and quality
    
    Validates: Requirements 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10, 14.11
    """
    
    def __init__(self):
        """Initialize PromptBuilder with default settings"""
        self.system_prompt: str = ""
        self.response_mode: ResponseMode = ResponseMode.CONVERSATIONAL
        self._mode_instructions: Dict[ResponseMode, str] = {
            ResponseMode.CONCISE: "Trả lời ngắn gọn, súc tích trong 1-2 câu.",
            ResponseMode.DETAILED: "Trả lời chi tiết, đầy đủ thông tin với giải thích rõ ràng.",
            ResponseMode.CONVERSATIONAL: "Trả lời tự nhiên, thân thiện như trong hội thoại.",
            ResponseMode.TECHNICAL: "Trả lời chuyên môn với thuật ngữ kỹ thuật chính xác."
        }
    
    def initialize(self, system_prompt: str) -> None:
        """
        Khởi tạo với system prompt.
        
        Args:
            system_prompt: System instructions định nghĩa personality của AI
            
        Validates: Requirement 14.1
        """
        self.system_prompt = system_prompt
    
    def build_prompt(self, context: Optional[Dict[str, Any]], user_input: str) -> str:
        """
        Xây dựng formatted prompt từ context và user input.
        
        Args:
            context: ConversationContext dictionary, ConversationContext object, hoặc None
            user_input: Current user input
            
        Returns:
            Formatted prompt string ready cho Gemini API
            
        Validates: Requirements 14.2, 14.3, 14.4
        """
        # Convert ConversationContext object to dictionary if needed
        if context and hasattr(context, 'to_dict'):
            context = context.to_dict()
        
        # Build prompt components
        prompt_parts = []
        
        # 1. System Instructions
        if self.system_prompt:
            prompt_parts.append(f"[System Instructions]\n{self.system_prompt}")
        
        # 2. Response Mode Instructions
        mode_instruction = self._mode_instructions.get(self.response_mode, "")
        if mode_instruction:
            prompt_parts.append(f"[Response Style]\n{mode_instruction}")
        
        # 3. User Preferences
        if context and context.get("user_preferences"):
            prefs = context["user_preferences"]
            pref_text = self._format_preferences(prefs)
            if pref_text:
                prompt_parts.append(f"[User Preferences]\n{pref_text}")
        
        # 4. Conversation History
        if context and context.get("messages"):
            history = self._format_conversation_history(context["messages"])
            if history:
                prompt_parts.append(f"[Conversation History]\n{history}")
                # Add interaction count
                turn_count = len([m for m in context["messages"] if m.get("role") == "user"])
                prompt_parts.append(f"[Context]\nĐây là lượt tương tác thứ {turn_count + 1} trong cuộc hội thoại.")
        
        # 5. Current User Input
        prompt_parts.append(f"[Current User Input]\nNgười dùng: {user_input}")
        
        # Join all parts
        full_prompt = "\n\n".join(prompt_parts)
        
        return full_prompt
    
    def set_response_mode(self, mode: ResponseMode) -> None:
        """
        Thay đổi response mode để điều chỉnh response style.
        
        Args:
            mode: ResponseMode enum value
            
        Validates: Requirement 14.6
        """
        if not isinstance(mode, ResponseMode):
            raise ValueError(f"Invalid mode: {mode}. Must be ResponseMode enum.")
        self.response_mode = mode
    
    def estimate_token_count(self, prompt: str) -> int:
        """
        Estimate token count cho prompt (approximate).
        
        Algorithm:
        - Tiếng Việt: ~1 token per word (sometimes 2 for compound words)
        - English: ~1.3 tokens per word
        - Punctuation/whitespace: minimal tokens
        
        Args:
            prompt: Prompt string to estimate
            
        Returns:
            Approximate token count
            
        Validates: Requirement 14.7
        """
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', prompt.strip())
        
        # Count words
        word_count = len(cleaned.split())
        
        # Estimate based on mixed Vietnamese/English content
        # Vietnamese: ~1.2 tokens/word, English: ~1.3 tokens/word
        # Use average 1.25 for mixed content
        estimated_tokens = int(word_count * 1.25)
        
        # Add overhead for special tokens and formatting
        overhead = 20  # System tokens, separators, etc.
        
        return estimated_tokens + overhead
    
    def optimize_context_window(self, messages: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """
        Truncate old messages nếu vượt token limit.
        Preserve most recent messages first.
        
        Algorithm:
        1. Estimate tokens for each message
        2. Keep adding recent messages until approaching limit
        3. Truncate oldest messages first
        
        Args:
            messages: List of message dicts với role và content
            max_tokens: Maximum token budget for history
            
        Returns:
            Optimized message list within token budget
            
        Validates: Requirements 14.8, 14.9
        """
        if not messages:
            return []
        
        # Estimate tokens per message
        messages_with_tokens = []
        for msg in messages:
            content = msg.get("content", "")
            tokens = self.estimate_token_count(content)
            messages_with_tokens.append({
                "message": msg,
                "tokens": tokens
            })
        
        # Start from most recent and work backwards
        optimized = []
        current_tokens = 0
        
        for item in reversed(messages_with_tokens):
            msg_tokens = item["tokens"]
            
            # Check if adding this message would exceed limit
            if current_tokens + msg_tokens <= max_tokens:
                optimized.insert(0, item["message"])  # Insert at beginning
                current_tokens += msg_tokens
            else:
                # Stop adding older messages
                break
        
        return optimized
    
    def _format_preferences(self, preferences: Dict[str, Any]) -> str:
        """Format user preferences into readable text"""
        pref_lines = []
        
        # Response mode preference
        if "response_mode" in preferences:
            mode = preferences["response_mode"]
            pref_lines.append(f"- Phong cách trả lời: {mode}")
        
        # Language formality
        if "language_formality" in preferences:
            formality = preferences["language_formality"]
            pref_lines.append(f"- Ngôn ngữ: {formality}")
        
        # Voice preference
        if "voice_name" in preferences:
            voice = preferences["voice_name"]
            pref_lines.append(f"- Giọng nói ưa thích: {voice}")
        
        # Max context turns
        if "max_context_turns" in preferences:
            turns = preferences["max_context_turns"]
            pref_lines.append(f"- Độ dài context: {turns} lượt")
        
        return "\n".join(pref_lines)
    
    def _format_conversation_history(self, messages: List[Dict[str, Any]]) -> str:
        """Format conversation history into readable text"""
        if not messages:
            return ""
        
        history_lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # Map role to Vietnamese labels
            role_label = {
                "user": "Người dùng",
                "assistant": "Tỷ Tỷ",
                "system": "Hệ thống"
            }.get(role, role.capitalize())
            
            history_lines.append(f"{role_label}: {content}")
        
        return "\n".join(history_lines)


# Singleton instance for global access
_prompt_builder = None


def get_prompt_builder() -> PromptBuilder:
    """Get or create PromptBuilder singleton instance"""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = PromptBuilder()
    return _prompt_builder


# Demo/Test code
if __name__ == "__main__":
    print("🧪 Testing PromptBuilder Module\n")
    
    # Test 1: Basic initialization
    print("=" * 60)
    print("Test 1: Initialize with system prompt")
    print("=" * 60)
    builder = PromptBuilder()
    system_prompt = """Bạn là Tỷ Tỷ, một trợ lý AI thông minh và thân thiện.
Bạn nói tiếng Việt tự nhiên và dễ thương.
Trả lời ngắn gọn, súc tích nhưng đầy đủ thông tin."""
    
    builder.initialize(system_prompt)
    print("✅ Initialized with system prompt")
    print(f"System prompt length: {len(system_prompt)} characters\n")
    
    # Test 2: Build simple prompt without context
    print("=" * 60)
    print("Test 2: Build simple prompt (no context)")
    print("=" * 60)
    prompt = builder.build_prompt(None, "1+1 bằng mấy?")
    print(prompt)
    print(f"\nEstimated tokens: {builder.estimate_token_count(prompt)}\n")
    
    # Test 3: Build prompt with conversation context
    print("=" * 60)
    print("Test 3: Build prompt with conversation history")
    print("=" * 60)
    context = {
        "session_id": "test-session-123",
        "messages": [
            {"role": "user", "content": "Thủ đô Việt Nam là gì?"},
            {"role": "assistant", "content": "Thủ đô Việt Nam là Hà Nội."},
            {"role": "user", "content": "Dân số bao nhiêu?"}
        ],
        "user_preferences": {
            "response_mode": "conversational",
            "language_formality": "friendly",
            "max_context_turns": 10
        }
    }
    
    prompt = builder.build_prompt(context, "Còn diện tích thì sao?")
    print(prompt)
    print(f"\nEstimated tokens: {builder.estimate_token_count(prompt)}\n")
    
    # Test 4: Response mode changes
    print("=" * 60)
    print("Test 4: Change response modes")
    print("=" * 60)
    
    modes = [ResponseMode.CONCISE, ResponseMode.DETAILED, ResponseMode.TECHNICAL]
    for mode in modes:
        builder.set_response_mode(mode)
        prompt = builder.build_prompt(None, "Giải thích trí tuệ nhân tạo")
        print(f"\nMode: {mode.value}")
        print(f"Token count: {builder.estimate_token_count(prompt)}")
        # Show just the response style section
        if "[Response Style]" in prompt:
            style_section = prompt.split("[Response Style]")[1].split("\n\n")[0]
            print(f"Style instruction: {style_section.strip()}")
    
    print()
    
    # Test 5: Context window optimization
    print("=" * 60)
    print("Test 5: Optimize context window (token limit)")
    print("=" * 60)
    
    long_messages = [
        {"role": "user", "content": "Câu hỏi đầu tiên về lịch sử Việt Nam"},
        {"role": "assistant", "content": "Đây là câu trả lời chi tiết về lịch sử Việt Nam..."},
        {"role": "user", "content": "Câu hỏi thứ hai về văn hóa"},
        {"role": "assistant", "content": "Văn hóa Việt Nam rất đa dạng và phong phú..."},
        {"role": "user", "content": "Câu hỏi thứ ba về ẩm thực"},
        {"role": "assistant", "content": "Ẩm thực Việt Nam nổi tiếng thế giới với phở, bánh mì..."},
        {"role": "user", "content": "Câu hỏi thứ tư về du lịch"},
        {"role": "assistant", "content": "Việt Nam có nhiều điểm du lịch đẹp như Hạ Long, Sapa..."},
    ]
    
    print(f"Original messages: {len(long_messages)}")
    total_tokens = sum(builder.estimate_token_count(m["content"]) for m in long_messages)
    print(f"Total tokens: {total_tokens}")
    
    # Optimize to 50 tokens max
    max_tokens = 50
    optimized = builder.optimize_context_window(long_messages, max_tokens)
    
    print(f"\nOptimized messages (max {max_tokens} tokens): {len(optimized)}")
    optimized_tokens = sum(builder.estimate_token_count(m["content"]) for m in optimized)
    print(f"Optimized tokens: {optimized_tokens}")
    print("\nPreserved messages (most recent):")
    for msg in optimized:
        print(f"  - {msg['role']}: {msg['content'][:50]}...")
    
    print()
    
    # Test 6: Token estimation accuracy
    print("=" * 60)
    print("Test 6: Token estimation for different content")
    print("=" * 60)
    
    test_strings = [
        "Xin chào",
        "1+1 bằng mấy?",
        "Thủ đô Việt Nam là Hà Nội, một thành phố có lịch sử hơn 1000 năm.",
        "The quick brown fox jumps over the lazy dog",
        "Mixed content: Tỷ Tỷ là AI assistant thông minh với natural language processing"
    ]
    
    for text in test_strings:
        tokens = builder.estimate_token_count(text)
        word_count = len(text.split())
        print(f"Text: '{text}'")
        print(f"  Words: {word_count}, Estimated tokens: {tokens}\n")
    
    print("=" * 60)
    print("✅ All PromptBuilder tests completed!")
    print("=" * 60)
