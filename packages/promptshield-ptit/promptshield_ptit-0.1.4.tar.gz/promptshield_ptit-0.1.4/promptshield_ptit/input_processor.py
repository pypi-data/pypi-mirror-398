import re
from typing import List

def split_into_sentences(text: str) -> List[str]:
    sentences = re.split(r'(?<=[.!?])(?:\s+|$)|(?<=[.!?])(?=[A-Z])|\n+', text)
    return [s.strip() for s in sentences if s.strip()]


def process_input(prompt: str) -> str:

    sentences = split_into_sentences(prompt)
    return " ".join(sentences)