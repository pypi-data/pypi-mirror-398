import os
import tiktoken
import numpy as np
from itertools import islice
from openai import OpenAI, BadRequestError
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_not_exception_type

from inoopa_utils.custom_types.openai import OpenAIModels


EMBEDDING_MODEL = 'text-embedding-3-small'
EMBEDDING_CTX_LENGTH = 8191
EMBEDDING_ENCODING = 'cl100k_base'
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
# Declare the encoder as a global variable to avoid loading it every time
encoder = tiktoken.get_encoding(EMBEDDING_ENCODING)


def get_number_of_tokens(text: str) -> int:
    """
    Get the number of tokens in a text.

    :param text: The text to count the tokens of.
    """
    return len(encoder.encode(text))

def get_len_safe_embedding(
    text: str, model: str = EMBEDDING_MODEL, max_tokens: int = EMBEDDING_CTX_LENGTH
) -> list[float] | None:
    """
    Get the embedding of a text, chunked into smaller parts if necessary.

    The code here is a bit complicated, it comes from an official OpenAI example:
    Code: https://github.com/openai/openai-cookbook/blob/main/examples/Embedding_long_inputs.ipynb
    Article: https://cookbook.openai.com/examples/embedding_long_inputs

    I simplified it a bit and added some comments and types. Could be refactored to make it clearer.

    :param text: The text to embed.
    :param model: The OpenAI model to use for embedding.
    :param max_tokens: The maximum number of tokens to pass to the OpenAI API.
    :param encoder_name: The name of the tokenizer to use.
    """
    chunk_embeddings = []
    chunk_lens = []

    # Chunk the text into smaller parts if it is too long
    for chunk in _chunked_tokens(text, chunk_length=max_tokens):
        chunk_embeddings.append(_get_embedding(chunk, model=model))
        chunk_lens.append(len(chunk))

    # Average the embeddings of the chunks, weighted by the number of tokens in each chunk
    chunk_embeddings = np.average(chunk_embeddings, axis=0, weights=chunk_lens)
    chunk_embeddings = chunk_embeddings / np.linalg.norm(chunk_embeddings)  # normalizes length to 1
    chunk_embeddings = chunk_embeddings.tolist()

    return chunk_embeddings

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6), retry=retry_if_not_exception_type(BadRequestError))
def _get_embedding(text_or_tokens, model: str = EMBEDDING_MODEL):
    return client.embeddings.create(input=text_or_tokens, model=model).data[0].embedding

def _batch_text(text: str, n: int):
    """Batch data into tuples of length n. The last batch may be shorter."""
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(text)
    while (batch := tuple(islice(it, n))):
        yield batch

def _chunked_tokens(text: str, chunk_length: int):
    tokens = encoder.encode(text)
    chunks_iterator = _batch_text(tokens, chunk_length)
    yield from chunks_iterator

def ask_gpt(prompt: str, model: OpenAIModels, system_message: str) -> str | None:
    """
    Function to ask a prompt to the OpenAI API.

    :param prompt: The prompt to ask.
    :param model: The OpenAI model to use.
    :param system_message: The system message to show before the prompt. Describe what we expect from the model.
    :return: The response from the OpenAI API or None.
    """
    response = client.chat.completions.create(
        model=model.value,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Testing purposes
    long_text = "This is a long text that we want to embed. We will use the OpenAI API to get the embeddings. " * 100
    average_embedding_vector = get_len_safe_embedding(long_text)
