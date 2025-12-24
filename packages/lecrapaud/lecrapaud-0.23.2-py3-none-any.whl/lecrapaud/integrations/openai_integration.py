import re
from openai import OpenAI
import tiktoken
from lecrapaud.utils import logger
from lecrapaud.config import OPENAI_API_KEY

# OpenAI’s max tokens per request for embeddings
MAX_TOKENS = 8192
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPEN_AI_MODEL = "gpt-4o-2024-08-06"
OPEN_AI_TOKENIZER = "cl100k_base"
OPEN_AI_EMBEDDING_DIM = 1536  # 3072 if embedding model is text-embedding-3-large
TPM_LIMIT = 5000000
TPR_LIMIT = 300_000  # known empirically because of a error message
MAX_LENGHT_ARRAY_FOR_BULK_EMBEDDINGS = 2048


def get_openai_client():
    if not OPENAI_API_KEY:
        raise ValueError(
            "Please set an OPENAI_API_KEY environment variable to use embeddings"
        )
    return OpenAI(api_key=OPENAI_API_KEY)


def get_openai_embedding(document: str | dict) -> list[float]:
    """embed a string into a vector using latest openai model, text-embedding-3-small

    :param document: the string to be embedded
    :return: the embedded vector
    """
    client = get_openai_client()

    if isinstance(document, dict):
        document = dict_to_markdown_headers_nested(document)
    if not isinstance(document, str):
        raise ValueError("document must be a string or dict")

    try:
        res = client.embeddings.create(input=document, model=OPENAI_EMBEDDING_MODEL)
    except Exception as e:
        if f"This model's maximum context length is {MAX_TOKENS} tokens" in str(e):
            raise Exception(
                f"get_embedding: the document is too long to be vectorized, it is longer than {MAX_TOKENS} tokens"
            )
        else:
            raise Exception(e)

    return res.data[0].embedding


def get_openai_embeddings(
    documents: list[str | dict], dimensions=None
) -> list[list[float]]:
    """embed a string into a vector using latest openai model, text-embedding-3-small

    :param document: an array of documents
    :return: a array of embedded vector
    """
    _documents = documents.copy()
    client = get_openai_client()
    dimensions = dimensions or OPEN_AI_EMBEDDING_DIM

    if not isinstance(documents, list):
        raise ValueError("documents must be a list")

    for i, doc in enumerate(documents):
        if isinstance(doc, dict):
            doc = dict_to_markdown_headers_nested(doc)
            _documents[i] = doc
        if not isinstance(doc, str):
            raise ValueError("documents must be a list of strings or dict")

    try:
        max_token = min(max_number_of_tokens(_documents), MAX_TOKENS)
        docs_per_batch = min(
            TPM_LIMIT // max_token,
            TPR_LIMIT // max_token,
            MAX_LENGHT_ARRAY_FOR_BULK_EMBEDDINGS,
        )  # TODO: un peu plus de marge ?

        embeddings = []
        for i, chunk in enumerate(
            [
                _documents[i : i + docs_per_batch]
                for i in range(0, len(_documents), docs_per_batch)
            ]
        ):
            logger.debug(f"Embedding chunk {i+1} with {len(chunk)} documents...")
            res = client.embeddings.create(
                input=[doc for doc in chunk],
                model=OPENAI_EMBEDDING_MODEL,
                dimensions=dimensions,
            )
            chunk_embeddings = [data.embedding for data in res.data]
            embeddings.extend(chunk_embeddings)

        return embeddings

    except Exception as e:
        if f"This model's maximum context length is {MAX_TOKENS} tokens" in str(e):
            raise Exception(
                f"get_embedding: the document is too long to be vectorized, it is longer than {MAX_TOKENS} tokens"
            )
        else:
            raise Exception(e)


def max_number_of_tokens(list):
    return max([num_tokens_from_string(str(item)) for item in list])


def num_tokens_from_string(string: str, encoding_name: str = OPEN_AI_TOKENIZER) -> int:
    """Count the number of token in string

    :param string: the string
    :param encoding_name: the encoding model
    :return: the number of tokens
    """
    if not string:
        return 0
    tokenizer = tiktoken.get_encoding(encoding_name)
    num_tokens = len(tokenizer.encode(string))
    return num_tokens


def chunk_text_words(text, max_tokens=MAX_TOKENS):
    """Splits text into chunks of max_tokens or less."""
    words = text.split()

    chunks = []
    current_chunk = []
    current_tokens = 0

    for word in words:
        word_tokens = num_tokens_from_string(word)  # Count tokens for word
        if current_tokens + word_tokens > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_tokens = 0

        current_chunk.append(word)
        current_tokens += word_tokens

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def chunk_text_sentences(text, max_tokens=MAX_TOKENS):
    # Sentence-split using regex (can also use nltk.sent_tokenize if preferred)
    # TODO: should we do a sliding window for chunking ?
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    current_chunk = ""
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = num_tokens_from_string(sentence)

        if current_tokens + sentence_tokens <= max_tokens:
            current_chunk += " " + sentence if current_chunk else sentence
            current_tokens += sentence_tokens
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Sentence too long to fit, need to split it
            if sentence_tokens > max_tokens:
                words = sentence.split()
                sub_chunk = ""
                sub_tokens = 0
                for word in words:
                    word_tokens = num_tokens_from_string(word + " ")
                    if sub_tokens + word_tokens > max_tokens:
                        chunks.append(sub_chunk.strip())
                        sub_chunk = word
                        sub_tokens = word_tokens
                    else:
                        sub_chunk += " " + word if sub_chunk else word
                        sub_tokens += word_tokens
                if sub_chunk:
                    chunks.append(sub_chunk.strip())
                current_chunk = ""
                current_tokens = 0
            else:
                current_chunk = sentence
                current_tokens = sentence_tokens

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def truncate_text(text, max_tokens=MAX_TOKENS):
    """Limits text to max_tokens or less by truncating."""
    words = text.split()
    truncated_text = []
    current_length = 0

    for word in words:
        token_length = num_tokens_from_string(word)  # Count tokens for word
        if current_length + token_length > max_tokens:
            break  # Stop once limit is reached

        truncated_text.append(word)
        current_length += token_length

    return " ".join(truncated_text)


def dict_to_markdown_headers_nested(d: dict, level: int = 1) -> str:
    lines = []
    for key, value in d.items():
        header = "#" * level + f" {key}"
        if isinstance(value, dict):
            lines.append(header)
            lines.append(dict_to_markdown_headers_nested(value, level + 1))
        else:
            lines.append(header)
            lines.append(str(value).strip())
        lines.append("")  # Blank line between sections
    return "\n".join(lines)
