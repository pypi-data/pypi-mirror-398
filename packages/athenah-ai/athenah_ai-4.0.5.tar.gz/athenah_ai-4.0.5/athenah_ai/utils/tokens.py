#!/usr/bin/env python
# coding: utf-8

import openai
from athenah_ai.config import config

openai.api_key = config.llm.openai_api_key


def get_token_total(prompt: str) -> int:
    import tiktoken

    openai_model = config.llm.token_counter_model
    encoding = tiktoken.encoding_for_model(openai_model)
    # print(
    #     "\033[37m" + str(len(encoding.encode(prompt))) + " tokens\033[0m" + " in prompt"
    # )
    return len(encoding.encode(prompt))
