from __future__ import annotations

import json
import logging
import os
import re
from typing import Dict, Generator, Iterable, List, Optional

import requests
from llama_index.readers.web import SimpleWebPageReader


logger = logging.getLogger(__name__)


class HuggingFaceService:
    """Thin wrapper around the Hugging Face chat completions API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        *,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        timeout: int = 60,
    ) -> None:
        """Initialize HuggingFaceService.

        Args:
            api_key: Hugging Face API key. If not given, reads HUGGINGFACE_API_KEY env var.
            model: Optional model name override.
            max_tokens: Default max tokens for generations.
            temperature: Default temperature.
            top_p: Default top_p.
            timeout: Default request timeout in seconds.
        """
        env_key = os.getenv("HUGGINGFACE_API_KEY")
        self.api_key: Optional[str] = api_key or env_key
        if not self.api_key:
            raise ValueError(
                "Hugging Face API key is required. "
                "Set HUGGINGFACE_API_KEY or pass api_key to HuggingFaceService."
            )

        # Default model is kept for backward compatibility
        self.model: str = model or "Qwen/Qwen3-235B-A22B-Instruct-2507"
        self.api_url: str = "https://router.huggingface.co/v1/chat/completions"

        # Default generation settings
        self.max_tokens: int = max_tokens
        self.temperature: float = temperature
        self.top_p: float = top_p
        self.timeout: int = timeout

        # Reuse HTTP session for performance
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_default_system_prompt(self) -> str:
        return (
            "You are a helpful AI assistant designed to answer questions "
            "based on provided context.\n"
            "Your role is to:\n"
            "1. Provide accurate, helpful information based on the context provided\n"
            "2. Be concise, clear, and professional\n"
            "3. If you don't know something, say so rather than making up information\n"
            "4. Focus on being helpful and informative"
        )

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _handle_api_error(self, error: Exception) -> str:
        error_msg = str(error)

        if hasattr(error, "response") and getattr(error, "response") is not None:
            try:
                error_data = error.response.json()  # type: ignore[union-attr]
                if "error" in error_data:
                    error_msg = error_data["error"]
                    if isinstance(error_msg, dict):
                        error_msg = error_msg.get("message", str(error_msg))
            except (ValueError, KeyError, TypeError):
                logger.debug("Failed to parse error response JSON", exc_info=True)

        lower_msg = error_msg.lower()
        if "loading" in lower_msg:
            return "The AI model is loading. Please try again in a moment."
        if "rate limit" in lower_msg:
            return "Rate limit reached. Please wait a moment and try again."
        if "quota" in lower_msg:
            return "API quota exceeded. Please check your Hugging Face API key."
        return f"I apologize, but I encountered an error: {error_msg}"

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def clean_markdown_formatting(self, content: str) -> str:
        """Remove markdown formatting from the model output."""
        if not content:
            return content

        # Remove markdown headers (# at start of lines)
        content = re.sub(r"^#+\s*", "", content, flags=re.MULTILINE)

        # Remove bold markdown (**text** -> text)
        content = re.sub(r"\*\*(.*?)\*\*", r"\1", content)

        # Remove italic markdown (*text* -> text) while avoiding other stars
        content = re.sub(
            r"(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)", r"\1", content
        )

        # Clean up any remaining double asterisks
        content = re.sub(r"\*\*", "", content)

        return content.strip()

    # ------------------------------------------------------------------
    # Core API calls
    # ------------------------------------------------------------------
    def generate_response(
        self,
        messages: Iterable[Dict[str, str]],
        system_prompt: Optional[str] = None,
        *,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> str:
        """Call Hugging Face chat completions and return a single response string."""
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        formatted_messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if not role or not content:
                raise ValueError("Each message must have 'role' and 'content' keys")
            formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": top_p if top_p is not None else self.top_p,
            "stream": False,
        }

        logger.debug("Sending non-streaming HF request")

        try:
            response = self.session.post(
                self.api_url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            choices = result.get("choices") or []
            if not choices:
                return "I apologize, but I couldn't generate a response. Please try again."

            message = choices[0].get("message", {})
            content = (message.get("content") or "").strip()
            if not content:
                return "I apologize, but I couldn't generate a response. Please try again."

            cleaned = self.clean_markdown_formatting(content)
            logger.debug("Successfully generated response")
            return cleaned

        except requests.exceptions.Timeout:
            logger.warning("HF request timed out")
            return "I apologize, but the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            logger.warning("HF request failed", exc_info=True)
            return self._handle_api_error(e)

    def generate_response_stream(
        self,
        messages: Iterable[Dict[str, str]],
        system_prompt: Optional[str] = None,
        *,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
    ) -> Generator[str, None, None]:
        """Call Hugging Face chat completions and stream the response chunks."""
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        formatted_messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt}
        ]
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            if not role or not content:
                raise ValueError("Each message must have 'role' and 'content' keys")
            formatted_messages.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
            "top_p": top_p if top_p is not None else self.top_p,
            "stream": True,
        }

        logger.debug("Sending streaming HF request")

        try:
            response = self.session.post(
                self.api_url,
                headers=self._build_headers(),
                json=payload,
                timeout=self.timeout,
                stream=True,
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if not line:
                    continue

                decoded = line.decode("utf-8")
                if not decoded.strip() or decoded.startswith(":"):
                    # Skip comments / empty lines in SSE stream
                    continue

                if not decoded.startswith("data: "):
                    continue

                data_str = decoded[6:]
                if data_str.strip() == "[DONE]":
                    break

                try:
                    data_obj = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = data_obj.get("choices") or []
                if not choices:
                    continue

                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    yield content

        except requests.exceptions.Timeout:
            logger.warning("HF streaming request timed out")
            yield "I apologize, but the request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            logger.warning("HF streaming request failed", exc_info=True)
            yield self._handle_api_error(e)

    def summarize_text(self, text: str, max_lines: int) -> str:
        """Summarize text to the given number of lines or fewer."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if not text.strip():
            return "No text provided to summarize."
        if max_lines < 1:
            raise ValueError("max_lines must be at least 1")

        system_prompt = (
            "You are a text summarization assistant. Your task is to summarize the "
            f"given text into exactly {max_lines} lines or fewer. The summary should "
            "be concise, clear, and preserve the most important information from the "
            "original text. Make sure the summary is well-formatted and readable."
        )

        user_prompt = (
            f"Please summarize the following text into {max_lines} lines or fewer:\n\n{text}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        return self.generate_response(messages)


class WebNexa:
    """High level helper for website Q&A and summarization."""

    def __init__(self, hf_token: Optional[str] = None, model: Optional[str] = None):
        """Initialize WebNexa with Hugging Face.

        Args:
            hf_token: Optional Hugging Face token. If not given, reads env var.
            model: Optional model name override.
        """
        self.hf_service = HuggingFaceService(api_key=hf_token, model=model)
        self.context_documents: List = []
        self.context_text: str = ""

    def load_website(self, url: str) -> None:
        """Load website content and build context for Q&A."""
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")

        reader = SimpleWebPageReader()
        documents = reader.load_data(urls=[url])
        self.context_documents = documents
        self.context_text = "\n\n".join(doc.text for doc in documents)

    def ask(self, question: str, use_streaming: bool = False):
        """Ask a question about the loaded website.

        Returns:
            String answer, or a generator of string chunks if streaming.
        """
        if not self.context_documents:
            raise ValueError("No website loaded. Call load_website() first.")

        if not isinstance(question, str) or not question.strip():
            raise ValueError("question must be a non-empty string")

        context = self.context_text
        system_prompt = (
            "You are a helpful AI assistant that answers questions based on the "
            "provided website content.\n\n"
            "Website Content:\n"
            f"{context}\n\n"
            "Your task is to:\n"
            "1. Answer questions based ONLY on the provided website content\n"
            "2. If the answer is not in the content, say \"I couldn't find that "
            "information in the provided content\"\n"
            "3. Be accurate, concise, and helpful\n"
            "4. Cite specific information from the content when possible"
        )

        messages = [
            {
                "role": "user",
                "content": (
                    "Based on the website content provided, please answer: " f"{question}"
                ),
            }
        ]

        if use_streaming:
            return self.hf_service.generate_response_stream(
                messages, system_prompt=system_prompt
            )

        return self.hf_service.generate_response(messages, system_prompt=system_prompt)

    def summarize(self, max_lines: int = 5) -> str:
        """Summarize the loaded website content."""
        if not self.context_documents:
            raise ValueError("No website loaded. Call load_website() first.")

        return self.hf_service.summarize_text(self.context_text, max_lines)
