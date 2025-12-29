"""Tests for tokenizer wrapper."""

import pytest


class TestTokenizerWrapper:
    """Tests for TokenizerWrapper."""

    def test_max_length_sanity(self):
        """Test that absurd max_length values are capped."""
        from clara.tokenizer import TokenizerWrapper

        class MockTokenizer:
            model_max_length = 10**30  # Absurdly large
            bos_token_id = 1
            eos_token_id = 2
            pad_token_id = 0

            def __len__(self):
                return 50000

        wrapper = TokenizerWrapper(MockTokenizer())
        assert wrapper.max_length <= 32768

    def test_max_length_explicit(self):
        """Test explicit max_length override."""
        from clara.tokenizer import TokenizerWrapper

        class MockTokenizer:
            model_max_length = 4096
            bos_token_id = 1
            eos_token_id = 2
            pad_token_id = 0

            def __len__(self):
                return 50000

        wrapper = TokenizerWrapper(MockTokenizer(), max_length=1024)
        assert wrapper.max_length == 1024

    def test_max_length_normal(self):
        """Test normal max_length values are preserved."""
        from clara.tokenizer import TokenizerWrapper

        class MockTokenizer:
            model_max_length = 2048
            bos_token_id = 1
            eos_token_id = 2
            pad_token_id = 0

            def __len__(self):
                return 50000

        wrapper = TokenizerWrapper(MockTokenizer())
        assert wrapper.max_length == 2048

    def test_properties(self):
        """Test tokenizer properties."""
        from clara.tokenizer import TokenizerWrapper

        class MockTokenizer:
            model_max_length = 512
            bos_token_id = 100
            eos_token_id = 200
            pad_token_id = 50  # Non-zero to avoid eos fallback

            def __len__(self):
                return 50000

        wrapper = TokenizerWrapper(MockTokenizer())
        assert wrapper.bos_token_id == 100
        assert wrapper.eos_token_id == 200
        assert wrapper.pad_token_id == 50
        assert wrapper.vocab_size == 50000

    def test_pad_token_fallback(self):
        """Test that pad_token_id falls back to eos when 0 or None."""
        from clara.tokenizer import TokenizerWrapper

        class MockTokenizer:
            model_max_length = 512
            bos_token_id = 100
            eos_token_id = 200
            pad_token_id = 0  # Falsy, should fallback to eos

            def __len__(self):
                return 50000

        wrapper = TokenizerWrapper(MockTokenizer())
        # 0 is falsy, so falls back to eos_token_id
        assert wrapper.pad_token_id == 200
