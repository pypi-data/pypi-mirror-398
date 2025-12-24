
import re
from typing import Optional, Union, Any, AsyncGenerator, Dict
from curl_cffi.requests import Session
from curl_cffi import CurlError

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream # Import sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions
from webscout.litagent import LitAgent

class TurboSeek(Provider):
    """
    This class provides methods for interacting with the TurboSeek API.
    """
    required_auth = False
    AVAILABLE_MODELS = ["Llama 3.1 70B"]

    def __init__(
        self,
        is_conversation: bool = True,
        max_tokens: int = 600,
        timeout: int = 30,
        intro: str = None,
        filepath: str = None,
        update_file: bool = True,
        proxies: dict = {},
        history_offset: int = 10250,
        act: str = None,
        model: str = "Llama 3.1 70B" # Note: model parameter is not used by the API endpoint
    ):
        """Instantiates TurboSeek

        Args:
            is_conversation (bool, optional): Flag for chatting conversationally. Defaults to True.
            max_tokens (int, optional): Maximum number of tokens to be generated upon completion. Defaults to 600.
            timeout (int, optional): Http request timeout. Defaults to 30.
            intro (str, optional): Conversation introductory prompt. Defaults to None.
            filepath (str, optional): Path to file containing conversation history. Defaults to None.
            update_file (bool, optional): Add new prompts and responses to the file. Defaults to True.
            proxies (dict, optional): Http request proxies. Defaults to {}.
            history_offset (int, optional): Limit conversation history to this number of last texts. Defaults to 10250.
            act (str|int, optional): Awesome prompt key or index. (Used as intro). Defaults to None.
        """
        # Initialize curl_cffi Session
        self.session = Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.chat_endpoint = "https://www.turboseek.io/api/getAnswer"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.turboseek.io",
            "priority": "u=1, i",
            "referer": "https://www.turboseek.io/",
            "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Microsoft Edge";v="140"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": LitAgent().random(),
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        # Update curl_cffi session headers and proxies
        self.session.headers.update(self.headers)
        self.session.proxies = proxies # Assign proxies directly
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

    @staticmethod
    def _html_to_markdown(text: str) -> str:
        """Convert basic HTML tags to Markdown."""
        if not text:
            return ""
        
        # Unescape HTML entities first
        import html
        text = html.unescape(text)

        # Headers
        text = re.sub(r'<h[1-6][^>]*>(.*?)</h[1-6]>', r'\n# \1\n', text)
        
        # Lists
        text = re.sub(r'<li[^>]*>(.*?)</li>', r'\n* \1', text)
        text = re.sub(r'<(ul|ol)[^>]*>', r'\n', text)
        text = re.sub(r'</(ul|ol)>', r'\n', text)
        
        # Paragraphs and Breaks
        text = re.sub(r'</p>', r'\n\n', text)
        text = re.sub(r'<p[^>]*>', r'\n', text)
        text = re.sub(r'<br\s*/?>', r'\n', text)
        
        # Bold and Italic
        text = re.sub(r'<(strong|b)[^>]*>(.*?)</\1>', r'**\2**', text)
        text = re.sub(r'<(em|i)[^>]*>(.*?)</\1>', r'*\2*', text)
        
        # Remove structural tags
        text = re.sub(r'</?(section|div|span|article|header|footer)[^>]*>', '', text, flags=re.IGNORECASE)
        
        # Final cleanup of remaining tags
        text = re.sub(r'<[^>]*>', '', text)
        
        return text

    @staticmethod
    def _turboseek_extractor(chunk: Any) -> Optional[str]:
        """Extracts content from TurboSeek stream."""
        if isinstance(chunk, str):
            # The API now returns raw HTML chunks
            return chunk
        return None

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI
        """
        conversation_prompt = self.conversation.gen_complete_prompt(prompt)
        if optimizer:
            if optimizer in self.__available_optimizers:
                conversation_prompt = getattr(Optimizers, optimizer)(
                    conversation_prompt if conversationally else prompt
                )
            else:
                raise Exception(
                    f"Optimizer is not one of {self.__available_optimizers}"
                )

        payload = {
            "question": conversation_prompt,
            "sources": []
        }

        def for_stream():
            try:
                response = self.session.post(
                    self.chat_endpoint, 
                    json=payload, 
                    stream=True, 
                    timeout=self.timeout,
                    impersonate="chrome120"
                )
                if not response.ok:
                    raise exceptions.FailedToGenerateResponseError(
                        f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                    )
                
                streaming_text = ""
                # The API returns raw HTML chunks now, no "data:" prefix
                processed_stream = sanitize_stream(
                    data=response.iter_content(chunk_size=None),
                    intro_value=None, 
                    to_json=False,
                    strip_chars='', # Disable default lstrip to preserve spacing
                    content_extractor=self._turboseek_extractor,
                    yield_raw_on_error=True,
                    raw=raw
                )
                
                for content_chunk in processed_stream:
                    if content_chunk is None:
                        continue
                    
                    if raw:
                        yield content_chunk
                    else:
                        if isinstance(content_chunk, str):
                            # In streaming mode, stripping HTML incrementally is hard.
                            # We'll just yield the chunk but clean it slightly.
                            # For full Markdown conversion, use non-streaming or aggregate it.
                            clean_chunk = re.sub(r'<[^>]*>', '', content_chunk)
                            if clean_chunk:
                                streaming_text += clean_chunk
                                self.last_response.update(dict(text=streaming_text))
                                yield dict(text=clean_chunk)
                
                if not raw and streaming_text:
                    self.conversation.update_chat_history(
                        prompt, streaming_text
                    )
            except CurlError as e:
                raise exceptions.FailedToGenerateResponseError(f"Request failed (CurlError): {e}")
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"An unexpected error occurred ({type(e).__name__}): {e}")

        def for_non_stream():
            full_html = ""
            try:
                # Iterate over the stream in raw mode to get full HTML
                # We use ask(..., raw=True) internally or just the local for_stream
                # Actually, let's just make a sub-call
                response = self.session.post(
                    self.chat_endpoint, 
                    json=payload, 
                    timeout=self.timeout,
                    impersonate="chrome120"
                )
                full_html = response.text
            except Exception as e:
                raise exceptions.FailedToGenerateResponseError(f"Failed to get non-stream response: {e}") from e
            
            # Convert full HTML to Markdown
            final_text = self._html_to_markdown(full_html).strip()
            self.last_response = {"text": final_text}
            return self.last_response

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        raw: bool = False,  # Added raw parameter
    ) -> str:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
            str: Response generated
        """

        def for_stream():
            for response in self.ask(
                prompt, True, raw=raw, optimizer=optimizer, conversationally=conversationally
            ):
                if raw:
                    yield response
                else:
                    yield self.get_message(response)
        def for_non_stream():
            result = self.ask(
                prompt,
                False,
                raw=raw,
                optimizer=optimizer,
                conversationally=conversationally,
            )
            if raw:
                return result
            else:
                return self.get_message(result)
        return for_stream() if stream else for_non_stream()

    def get_message(self, response: dict) -> str:
        """Retrieves message only from response

        Args:
            response (dict): Response generated by `self.ask`

        Returns:
            str: Message extracted
        """
        assert isinstance(response, dict), "Response should be of dict data-type only"
        # Unicode escapes are handled by json.loads within sanitize_stream
        return response.get("text", "") 

if __name__ == '__main__':
    import sys
    ai = TurboSeek(timeout=60)
    
    # helper for safe printing on windows
    def safe_print(text, end="\n"):
        try:
            sys.stdout.write(text + end)
        except UnicodeEncodeError:
            sys.stdout.write(text.encode('ascii', 'ignore').decode('ascii') + end)
        sys.stdout.flush()

    safe_print("\n=== Testing Non-Streaming ===")
    response = ai.chat("How can I get a 6 pack in 3 months?", stream=False)
    safe_print(response)
    
    safe_print("\n=== Testing Streaming ===")
    for chunk in ai.chat("How can I get a 6 pack in 3 months?", stream=True):
        safe_print(chunk, end="")
    safe_print("")