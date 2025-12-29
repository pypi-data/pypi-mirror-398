"""
Ollama AI Service - Local LLM integration
Handles chat and text generation using Ollama models
"""

import httpx
import json
import logging
from typing import AsyncGenerator, Optional

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_HOST = "http://ollama:11434"  # Inside Docker network
OLLAMA_MODEL = "qwen2.5:0.5b"  # Default model
OLLAMA_TIMEOUT = 120  # 2 minutes timeout for long responses


class OllamaError(Exception):
    """Custom exception for Ollama errors"""

    pass


async def chat_with_ollama(
    prompt: str,
    model: str = OLLAMA_MODEL,
    temperature: float = 0.7,
    top_p: float = 0.9,
    stream: bool = False,
) -> str:
    """
    Send a prompt to Ollama and get a response.

    Args:
        prompt: The user's prompt/question
        model: Model to use (default: qwen2.5:0.5b)
        temperature: Creativity level (0-1, default 0.7)
        top_p: Diversity parameter (0-1, default 0.9)
        stream: Whether to stream response

    Returns:
        Generated text response from Ollama

    Raises:
        OllamaError: If Ollama is unavailable or request fails
    """
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            response = await client.post(
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,  # Don't stream for single response
                    "temperature": temperature,
                    "top_p": top_p,
                },
            )

            if response.status_code != 200:
                raise OllamaError(
                    f"Ollama request failed with status {response.status_code}: {response.text}"
                )

            data = response.json()
            return data.get("response", "").strip()

    except httpx.ConnectError:
        logger.error("Failed to connect to Ollama. Is it running?")
        raise OllamaError("Ollama service is not available. Make sure it's running.")
    except httpx.TimeoutException:
        logger.error(f"Ollama request timed out after {OLLAMA_TIMEOUT}s")
        raise OllamaError("Ollama request timed out. Try a simpler prompt.")
    except Exception as e:
        logger.error(f"Ollama error: {str(e)}")
        raise OllamaError(f"Error communicating with Ollama: {str(e)}")


async def chat_stream_ollama(
    prompt: str,
    model: str = OLLAMA_MODEL,
    temperature: float = 0.7,
    top_p: float = 0.9,
) -> AsyncGenerator[str, None]:
    """
    Stream a response from Ollama token by token.

    Args:
        prompt: The user's prompt/question
        model: Model to use (default: qwen2.5:0.5b)
        temperature: Creativity level (0-1, default 0.7)
        top_p: Diversity parameter (0-1, default 0.9)

    Yields:
        Response tokens as they're generated

    Raises:
        OllamaError: If Ollama is unavailable or request fails
    """
    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_HOST}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": True,  # Enable streaming
                    "temperature": temperature,
                    "top_p": top_p,
                },
            ) as response:
                if response.status_code != 200:
                    raise OllamaError(
                        f"Ollama request failed with status {response.status_code}"
                    )

                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            token = data.get("response", "")
                            if token:
                                yield token
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON line from Ollama: {line}")
                            continue

    except httpx.ConnectError:
        logger.error("Failed to connect to Ollama. Is it running?")
        raise OllamaError("Ollama service is not available.")
    except httpx.TimeoutException:
        logger.error(f"Ollama request timed out after {OLLAMA_TIMEOUT}s")
        raise OllamaError("Ollama request timed out.")
    except Exception as e:
        logger.error(f"Ollama streaming error: {str(e)}")
        raise OllamaError(f"Error with Ollama: {str(e)}")


async def list_available_models() -> list[str]:
    """
    Get list of available models in Ollama.

    Returns:
        List of model names

    Raises:
        OllamaError: If Ollama is unavailable
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{OLLAMA_HOST}/api/tags")

            if response.status_code != 200:
                raise OllamaError(f"Failed to fetch models: {response.text}")

            data = response.json()
            models = data.get("models", [])
            return [model.get("name", "") for model in models if model.get("name")]

    except httpx.ConnectError:
        logger.error("Cannot connect to Ollama")
        raise OllamaError("Ollama is not running")
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        raise OllamaError(f"Error listing models: {str(e)}")


async def check_ollama_health() -> bool:
    """
    Check if Ollama is running and responding.

    Returns:
        True if Ollama is healthy, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.head(f"{OLLAMA_HOST}")
            return response.status_code == 200
    except Exception:
        return False


async def generate_summary(text: str, max_length: int = 150) -> str:
    """
    Generate a summary of provided text using Ollama.

    Args:
        text: Text to summarize
        max_length: Maximum length of summary

    Returns:
        Summary of the text
    """
    prompt = f"""Please provide a concise summary of the following text in {max_length} words or less:

{text}

Summary:"""

    return await chat_with_ollama(prompt, temperature=0.5)


async def answer_question(question: str, context: str = "") -> str:
    """
    Answer a question, optionally using provided context.

    Args:
        question: The question to answer
        context: Optional context for answering

    Returns:
        Answer to the question
    """
    if context:
        prompt = f"""Answer the following question based on the provided context. If the answer is not in the context, say so but try to be helpful.

Context:
{context}

Question: {question}

Answer:"""
    else:
        prompt = f"""Answer the following question:

{question}

Answer:"""

    return await chat_with_ollama(prompt)


async def code_generation(description: str) -> str:
    """
    Generate code based on description.

    Args:
        description: Description of what code should do

    Returns:
        Generated code
    """
    prompt = f"""Generate Python code that does the following:

{description}

Provide only the code, without explanations or markdown formatting:"""

    return await chat_with_ollama(prompt, temperature=0.3)
