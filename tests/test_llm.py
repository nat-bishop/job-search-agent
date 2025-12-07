"""Tests for src/core/llm.py - LLM factory and model context detection."""

from unittest.mock import MagicMock, patch


class TestGetModelContextLength:
    """Tests for get_model_context_length() function."""

    def test_returns_context_length_from_ollama(self):
        """Successfully queries Ollama and returns context length."""
        from src.core import llm

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model_info": {"context_length": 32768}
        }

        # Clear cache before test
        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.httpx.post", return_value=mock_response) as mock_post:
            result = llm.get_model_context_length("test-model:7b")

            assert result == 32768
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "test-model:7b" in str(call_args)

    def test_returns_fallback_on_connection_error(self):
        """Falls back to default when Ollama is unreachable."""
        from src.core import llm

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.httpx.post", side_effect=Exception("Connection refused")):
            result = llm.get_model_context_length("unreachable-model")

            assert result == 131072  # Default fallback

    def test_returns_fallback_on_missing_context_length(self):
        """Falls back when response doesn't contain context_length."""
        from src.core import llm

        mock_response = MagicMock()
        mock_response.json.return_value = {"model_info": {}}  # No context_length

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.httpx.post", return_value=mock_response):
            result = llm.get_model_context_length("model-no-context")

            assert result == 131072

    def test_returns_fallback_on_empty_model_info(self):
        """Falls back when model_info is missing entirely."""
        from src.core import llm

        mock_response = MagicMock()
        mock_response.json.return_value = {}  # No model_info key

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.httpx.post", return_value=mock_response):
            result = llm.get_model_context_length("model-no-info")

            assert result == 131072

    def test_caches_results_per_model(self):
        """Results are cached per model name."""
        from src.core import llm

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model_info": {"context_length": 65536}
        }

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.httpx.post", return_value=mock_response) as mock_post:
            # First call
            result1 = llm.get_model_context_length("cached-model")
            # Second call with same model
            result2 = llm.get_model_context_length("cached-model")

            assert result1 == result2 == 65536
            # Should only call Ollama once due to caching
            assert mock_post.call_count == 1

    def test_different_models_queried_separately(self):
        """Different models are queried separately (not shared cache)."""
        from src.core import llm

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model_info": {"context_length": 4096}
        }

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.httpx.post", return_value=mock_response) as mock_post:
            llm.get_model_context_length("model-a")
            llm.get_model_context_length("model-b")

            # Each model should trigger a separate call
            assert mock_post.call_count == 2


class TestGetLlm:
    """Tests for get_llm() function."""

    def test_sets_model_profile_with_context_length(self):
        """LLM instance has profile set with max_input_tokens."""
        from src.core import llm

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.get_model_context_length", return_value=131072):
            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_instance = MagicMock()
                mock_chat.return_value = mock_instance

                result = llm.get_llm()

                assert result.profile == {"max_input_tokens": 131072}

    def test_profile_reflects_detected_context_length(self):
        """Profile uses the actual detected context length."""
        from src.core import llm

        llm.get_model_context_length.cache_clear()

        # Simulate a smaller model
        with patch("src.core.llm.get_model_context_length", return_value=8192):
            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_instance = MagicMock()
                mock_chat.return_value = mock_instance

                result = llm.get_llm()

                assert result.profile == {"max_input_tokens": 8192}

    def test_passes_temperature_to_chat_model(self):
        """Temperature parameter is passed through to ChatOpenAI."""
        from src.core import llm

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.get_model_context_length", return_value=131072):
            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_instance = MagicMock()
                mock_chat.return_value = mock_instance

                llm.get_llm(temperature=0.7)

                mock_chat.assert_called_once()
                call_kwargs = mock_chat.call_args.kwargs
                assert call_kwargs["temperature"] == 0.7

    def test_default_temperature_is_zero(self):
        """Default temperature is 0.0 for deterministic outputs."""
        from src.core import llm

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.get_model_context_length", return_value=131072):
            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_instance = MagicMock()
                mock_chat.return_value = mock_instance

                llm.get_llm()

                call_kwargs = mock_chat.call_args.kwargs
                assert call_kwargs["temperature"] == 0.0


class TestGetAgentLlm:
    """Tests for get_agent_llm() convenience function."""

    def test_returns_llm_with_default_temperature(self):
        """get_agent_llm uses temperature=0.0 by default."""
        from src.core import llm

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.get_model_context_length", return_value=131072):
            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_instance = MagicMock()
                mock_chat.return_value = mock_instance

                llm.get_agent_llm()

                call_kwargs = mock_chat.call_args.kwargs
                assert call_kwargs["temperature"] == 0.0

    def test_allows_temperature_override(self):
        """get_agent_llm allows overriding default temperature."""
        from src.core import llm

        llm.get_model_context_length.cache_clear()

        with patch("src.core.llm.get_model_context_length", return_value=131072):
            with patch("langchain_openai.ChatOpenAI") as mock_chat:
                mock_instance = MagicMock()
                mock_chat.return_value = mock_instance

                llm.get_agent_llm(temperature=0.5)

                call_kwargs = mock_chat.call_args.kwargs
                assert call_kwargs["temperature"] == 0.5
