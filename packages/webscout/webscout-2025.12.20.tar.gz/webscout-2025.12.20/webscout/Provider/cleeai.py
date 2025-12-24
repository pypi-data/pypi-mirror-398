import requests
import json
from uuid import uuid4
from typing import Union, Dict, Any, Generator

from webscout.AIutel import Optimizers
from webscout.AIutel import Conversation
from webscout.AIutel import AwesomePrompts, sanitize_stream
from webscout.AIbase import Provider
from webscout import exceptions
import webscout

class Cleeai(Provider):
    """
    A class to interact with the Cleeai.com API.
    """
    required_auth = False
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
    ) -> None:
        """Instantiates Cleeai

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
        self.session = requests.Session()
        self.is_conversation = is_conversation
        self.max_tokens_to_sample = max_tokens
        self.api_endpoint = "https://qna-api.cleeai.com/open_research"
        self.stream_chunk_size = 64
        self.timeout = timeout
        self.last_response = {}
        self.headers = {
            "accept": "*/*",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-US,en;q=0.9,en-IN;q=0.8",
            "content-type": "application/json",
            "dnt": "1",
            "origin": "https://www.cleeai.com",
            "priority": "u=1, i",
            "referer": "https://www.cleeai.com/",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": webscout.LitAgent().random()
        }

        self.__available_optimizers = (
            method
            for method in dir(Optimizers)
            if callable(getattr(Optimizers, method)) and not method.startswith("__")
        )
        self.session.headers.update(self.headers)
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
        self.session.proxies = proxies

    def ask(
        self,
        prompt: str,
        stream: bool = False,
        raw: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
    ) -> dict:
        """Chat with AI

        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            raw (bool, optional): Stream back raw response as received. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
        Returns:
           dict : {}
        ```json
        {
           "text" : "How may I assist you today?"
        }
        ```
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
            "data": {
                "question": conversation_prompt,
                "question_id": 69237,
                "query_id": uuid4().hex,
                "source_list": [],
                "followup_qas": [],
                "with_upload": True,
            }
        }

        def for_stream():
            response = self.session.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=self.timeout,
            )
            if not response.ok:
                raise exceptions.FailedToGenerateResponseError(
                    f"Failed to generate response - ({response.status_code}, {response.reason}) - {response.text}"
                )

            full_response = ''
            # Use sanitize_stream for processing
            processed_stream = sanitize_stream(
                data=response.iter_content(chunk_size=self.stream_chunk_size),
                intro_value=None,
                to_json=False,
                yield_raw_on_error=True,
                raw=raw
            )

            for content_chunk in processed_stream:
                if content_chunk:
                    # Decode if bytes
                    if isinstance(content_chunk, bytes):
                        content_chunk = content_chunk.decode('utf-8', errors='ignore')
                    if raw:
                        yield content_chunk
                    else:
                        full_response += content_chunk
                        yield dict(text=content_chunk)

            self.last_response = {"text": full_response}
            self.conversation.update_chat_history(prompt, full_response)

        def for_non_stream():
            for _ in for_stream():
                pass
            return self.last_response if not raw else json.dumps(self.last_response)

        return for_stream() if stream else for_non_stream()

    def chat(
        self,
        prompt: str,
        stream: bool = False,
        optimizer: str = None,
        conversationally: bool = False,
        raw: bool = False,
    ) -> Union[str, Generator[str, None, None]]:
        """Generate response `str`
        Args:
            prompt (str): Prompt to be send.
            stream (bool, optional): Flag for streaming response. Defaults to False.
            optimizer (str, optional): Prompt optimizer name - `[code, shell_command]`. Defaults to None.
            conversationally (bool, optional): Chat conversationally when using optimizer. Defaults to False.
            raw (bool, optional): Return raw response chunks. Defaults to False.
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
        return response["text"]


if __name__ == "__main__":
    from rich import print
    ai = Cleeai(timeout=5000)
    response = ai.chat("tell me about Abhay koul, HelpingAI", stream=True)
    for chunk in response:
        print(chunk, end="", flush=True)