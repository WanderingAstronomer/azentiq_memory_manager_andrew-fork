def test_generate_prompt(self):
    """Test prompt generation with token budget manager integration."""
    # Set up mocks for methods called by generate_prompt
    short_term_memories = [self.test_memory]
    working_memories = []
    
    # Mock the get_recent_turns method
    self.manager.get_recent_turns = MagicMock(return_value=short_term_memories)
    
    # Mock the _search_by_metadata_in_tier method
    self.manager._search_by_metadata_in_tier = MagicMock(return_value=working_memories)
    
    # Set up mock to return prompt tuple
    expected_prompt = ("Generated prompt with memories", {"tokens": 100})
    self.token_budget_mock.construct_prompt_with_memories.return_value = expected_prompt
    
    # Generate prompt
    prompt, stats = self.manager.generate_prompt(
        session_id=self.test_session_id,
        user_query="Test query",
        system_message="System message"
    )
    
    # Verify prompt was returned
    self.assertEqual(prompt, "Generated prompt with memories")
    
    # Verify get_recent_turns was called
    self.manager.get_recent_turns.assert_called_with(self.test_session_id, n_turns=10)
    
    # Verify _search_by_metadata_in_tier was called with correct parameters
    self.manager._search_by_metadata_in_tier.assert_called_with(
        {"session_id": self.test_session_id, "type": "session_context"}, 
        MemoryTier.WORKING, 
        limit=50
    )
    
    # Verify token budget manager was called with the right parameters
    self.token_budget_mock.construct_prompt_with_memories.assert_called_with(
        system_message="System message",
        user_query="Test query",
        short_term_memories=short_term_memories,
        working_memories=working_memories,
        long_term_memories=[]
    )
