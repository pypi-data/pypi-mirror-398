import math

from transformers import AutoTokenizer, PreTrainedTokenizer
from transformers.tokenization_utils_base import TextInput

from words_segmentation.pretokenizer import text_to_words, words_to_text


class WordsSegmentationTokenizer(PreTrainedTokenizer):
    """
    Custom Tokenizer implementation,
    extending PreTrainedTokenizer for basic Hugging Face ecosystem support.
    """

    def __init__(self, max_bytes: int = math.inf, **kwargs):
        super().__init__(**kwargs)
        self.max_bytes = max_bytes

    @property
    def vocab_size(self) -> float:
        return math.inf

    def add_tokens(self, *args, **kwargs):
        raise NotImplementedError("WordsSegmentationTokenizer does not support adding tokens")

    def get_vocab(self):
        return {}

    def _tokenize(self, text: TextInput, **kwargs):
        return text_to_words(text, max_bytes=self.max_bytes)

    def tokenize(self, text: TextInput, **kwargs):
        return self._tokenize(text, **kwargs)

    def _encode_plus(self, text: TextInput, **kwargs):
        raise Exception("WordsSegmentationTokenizer can not encode to ids")

    def _convert_token_to_id(self, token: str):
        raise Exception("WordsSegmentationTokenizer can not convert to ids")

    def _convert_id_to_token(self, index: int):
        raise Exception("WordsSegmentationTokenizer can not decode ids")

    def convert_tokens_to_string(self, tokens: list[str]):
        """Converts a sequence of tokens (string) in a single string."""
        return words_to_text(tokens)

    def build_inputs_with_special_tokens(self, **unused_kwargs):
        raise Exception("WordsSegmentationTokenizer does not use special tokens")

    def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None):
        return ()

    def to_dict(self):
        return {"max_bytes": self.max_bytes}


AutoTokenizer.register(WordsSegmentationTokenizer, slow_tokenizer_class=WordsSegmentationTokenizer)

if __name__ == "__main__":
    tokenizer = WordsSegmentationTokenizer()
    print(tokenizer.tokenize("hello world! 我爱北京天安门 👩‍👩‍👧‍👦", max_bytes=16))
