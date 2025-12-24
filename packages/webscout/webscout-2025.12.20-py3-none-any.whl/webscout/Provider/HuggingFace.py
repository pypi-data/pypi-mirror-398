from curl_cffi.requests import Session
from curl_cffi import CurlError
import json
from typing import Any, Dict, Optional, Generator, Union, List
from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class HuggingFace(Provider):
    """
    A class to interact with the Hugging Face Router API with LitAgent user-agent.
    Follows the DeepInfra standalone provider pattern.
    """
    required_auth = True
    AVAILABLE_MODELS = []

    @classmethod
    def get_models(cls, api_key: str = None) -> List[str]:
        """Fetch available text-generation models from Hugging Face."""
        url = "https://router.huggingface.co/v1/models"
        try:
            temp_session = Session()
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            response = temp_session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    return [model['id'] for model in data['data'] if 'id' in model]
                return [model['id'] for model in data if 'id' in model]
            return cls.AVAILABLE_MODELS
        except Exception:
            return cls.AVAILABLE_MODELS

    @classmethod
    def update_available_models(cls, api_key: str = None):
        """Update the available models list from Hugging Face API dynamically."""
        try:
            models = cls.get_models(api_key)
            if models and len(models) > 0:
                cls.AVAILABLE_MODELS = models
        except Exception:
            pass

    def __init__(
        self,
        api_key: str,
        is_conversation: bool = True,
        max_tokens: int = 2049,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "meta-llama/Llama-3.3-70B-Instruct",
        system_prompt: str = "You are a helpful assistant.",
        temperature: float = 0.7,
        top_p: float = 0.9,
        browser: str = "chrome"
    ):
        """Initializes the Hugging Face API client."""
        # Dynamic model fetching
        self.update_available_models(api_key)

        if model not in self.AVAILABLE_MODELS:
            # We allow it but warn if it's not in the detected list
            pass

        self.url = "https://router.huggingface.co/v1/chat/completions"

        self.agent = LitAgent()
        self.fingerprint = self.agent.generate_fingerprint(browser)
        self.api = api_key
        self.headers = {
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Origin": "https://huggingface.co",
            "Pragma": "no-cache",
            "Referer": "https://huggingface.co/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": self.fingerprint.get("user_agent", ""),
            "Sec-CH-UA": self.fingerprint.get("sec_ch_ua", ""),
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self.fingerprint.get("platform", "")}"',
            "X-Forwarded-For": self.fingerprint.get("x-forwarded-for", ""),
            "X-Real-IP": self.fingerprint.get("x-real-ip", ""),
            "X-Client-IP": self.fingerprint.get("x-client-ip", ""),
            "Forwarded": self.fingerprint.get("forwarded", ""),
            "X-Forwarded-Proto": self.fingerprint.get("x-forwarded-proto", ""),
            "X-Request-Id": self.fingerprint.get("x-request-id", ""),
        }
        if self.api is not None:
            self.headers["Authorization"] = f"Bearer {self.api}"

        self.session = Session()
        self.session.headers.update(self.headers)
        self.session.proxies = proxies
        self.system_prompt = system_prompt
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.timeout = timeout
        self.last_response = {}
        self.model = model
        self.temperature = temperature
        self.top_p = top_p

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        Conversation.intro = (
            AwesomePrompts().get_act(
                act, raise_not_found=True, default=None, case_insensitive=True
            )
            if act
            else intro or Conversation.intro
        )

        self.conversation = Conversation(
            is_conversation, self.max_tokens_to_sample, filepath, update_file
        )
        self.conversation.history_offset = history_offset

    def refresh_identity(self, browser: str = None):
        """
        Refreshes the browser identity fingerprint.

        Args:
            browser: Specific browser to use for the new fingerprint
        """
        browser = browser or self.fingerprint.get("browser_type", "chrome")
        self.fingerprint = self.agent.generate_fingerprint(browser)

        self.headers.update({
            "Accept": self.fingerprint["accept"],
            "Accept-Language": self.fingerprint["accept_language"],
        })

        self.session.headers.update(self.headers)

        return self.fingerprint

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> Union[Dict[str, Any], Generator]:
        """
        Sends a prompt to the Hugging Face Router API and returns the response.
        
        Args:
            prompt: The prompt to send to the API
            stream: Whether to stream the response
            raw: If True, returns unprocessed response chunks without any 
                processing or sanitization. Useful for debugging or custom
                processing pipelines. Defaults to False.
            optimizer: Optional prompt optimizer name
            conversationally: Whether to use conversation context
            
        Returns:
            When raw=False: Dict with 'text' key (non-streaming) or 
                Generator yielding dicts (streaming)
            When raw=True: Raw string response (non-streaming) or 
                Generator yielding raw string chunks (streaming)
                
        Examples:
            >>> hf = HuggingFace(api_key="your-key")
            >>> # Get processed response
            >>> response = hf.ask("Hello")
            >>> print(response["text"])
            
            >>> # Get raw response
            >>> raw_response = hf.ask("Hello", raw=True)
            >>> print(raw_response)
            
            >>> # Stream raw chunks
            >>> for chunk in hf.ask("Hello", stream=True, raw=True):
            ...     print(chunk, end='', flush=True)
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(f"Optimizer is not one of {self.__available_optimizers}")

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": conversation_prompt},
            ],
            "stream": stream,
            "max_tokens": self.max_tokens_to_sample,
            "temperature": self.temperature,
            "top_p": self.top_p
        }

        def for_stream():
            streaming_text = "" 
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    stream=True,
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value="data:",
                    to_json=True,
                    skip_markers=["[DONE]"],
                    content_extractor=lambda x: x.get("choices", [{}])[0].get("delta", {}).get("content") or x.get("choices", [{}])[0].get("delta", {}).get("reasoning_content") if isinstance(x, dict) else None,
                    yield_raw_on_error=False,
                    raw=raw
                )

                for content_chunk in processed_stream:
                    if isinstance(content_chunk, bytes):
                        content_chunk = content_chunk.decode('utf-8', errors='ignore')
                    
                    if raw:
                        yield content_chunk
                    else:
                        if content_chunk and isinstance(content_chunk, str):
                            streaming_text += content_chunk
                            yield dict(text=content_chunk)

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {str(e)}") from e
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {str(e)}") from e
            finally:
                if not raw and streaming_text:
                    self.last_response = {"text": streaming_text}
                    self.conversation.update_chat_history(prompt, streaming_text)


        def for_non_stream():
            try:
                response = self.session.post(
                    self.url,
                    data=json.dumps(payload),
                    timeout=self.timeout,
                    impersonate="chrome110"
                )
                response.raise_for_status()

                if raw:
                    return response.text

                # Use sanitize_stream to parse the non-streaming JSON response
                processed_stream = sanitize_stream(
                    data=response.text,
                    to_json=True,
                    intro_value=None,
                    content_extractor=lambda chunk: chunk.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(chunk, dict) else None,
                    yield_raw_on_error=False,
                    raw=raw
                )
                # Extract the single result
                content = next(processed_stream, None)
                if raw:
                    return content
                content = content if isinstance(content, str) else ""

                self.last_response = {"text": content}
                self.conversation.update_chat_history(prompt, content)
                return self.last_response if not raw else content

            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}") from e
            except Exception as e:
                err_text = getattr(e, 'response', None) and getattr(e.response, 'text', '')
                raise exceptions.FailedToGenerateResponseError(f"Request failed ({type(e).__name__}): {e} - {err_text}") from e


        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        raw: bool = False,
        conversationally: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """
        Generates a chat response from the Hugging Face Router API.
        """
        def for_stream_chat():
            gen = self.ask(
                prompt, stream=True, raw=raw,
                optimizer=optimizer, conversationally=conversationally
            )
            for response_dict in gen:
                if raw:
                    yield response_dict
                else:
                    yield self.get_message(response_dict)

        def for_non_stream_chat():
            response_data = self.ask(
                prompt, stream=False, raw=raw,
                optimizer=optimizer, conversationally=conversationally
            )
            if raw:
                return response_data
            else:
                return self.get_message(response_data)

        return for_stream_chat() if stream else for_non_stream_chat()

    def get_message(self, response: dict) -> str:
        """Retrieves message from response dict."""
        assert isinstance(response, dict), "Response should be of dict data-type only"
        return response.get("text", "")

if __name__ == "__main__":
    hf = HuggingFace(api_key="")
    models = hf.AVAILABLE_MODELS
    print(models)
    for chunk in hf.chat("Hi!", stream=True):
        print(chunk, end="", flush=True)
