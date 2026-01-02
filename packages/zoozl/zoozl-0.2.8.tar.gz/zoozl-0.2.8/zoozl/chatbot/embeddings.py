"""Retrieve and manipulate embeddings of different supported models."""

from abc import ABC, abstractmethod
import string

from scipy import spatial
from openai import OpenAI


def get_cosine_similarity(x, y):
    """Get cosine similarity of two embeddings."""
    return 1 - spatial.distance.cosine(x, y)


class Lookup:
    """Lookup embeddings for the given text."""

    def __init__(self, memory, embedder):
        """Initialise lookup.

        :param memory: memory bank to store embeddings
        :param embedder: external embedder to use when embedding is not in memory
        """
        self.memory = memory
        if not isinstance(embedder, AbstractExternalEmbedder):
            raise TypeError("Embedder should be instance of AbstractExternalEmbedder")
        self.embedder = embedder

    def load(self):
        """Load instance."""
        self.external_query = self.embedder()

    def clear(self):
        """Safely clear and close instance."""

    def get(self, text):
        """Get embedding of the text."""
        return self.embedder.get(text)


class AbstractExternalEmbedder(ABC):
    """Abstract class for external embedder."""

    @abstractmethod
    def get(self, text):
        """Get embedding of the text."""


class OpenAIEmbedder(AbstractExternalEmbedder):
    """OpenAI embedder."""

    def __init__(self, conf, model="text-embedding-3-small"):
        """Initialise OpenAI embedder.

        :param conf: configuration to use
        :param model: model to use
        """
        self.client = OpenAI(api_key=conf["api_key"])
        self.model = model

    def get(self, text):
        """Get embedding of the text."""
        return (
            self.client.embeddings.create(input=text, model=self.model)
            .data[0]
            .embedding
        )


class CharEmbedder(AbstractExternalEmbedder):
    """Dumbest embedder that works locally without any dependencies.

    This embedder is used as a fallback when no external embedder is available.
    """

    def get(self, text):
        """Get embedding of the text."""
        text = text.lower()
        vector = [0] * (len(string.ascii_lowercase) + 3)
        for c in text:
            if c in string.ascii_lowercase:
                vector[string.ascii_lowercase.index(c)] += 1
            elif c in string.whitespace or c in string.punctuation:
                vector[-3] += 1
            elif c in string.digits:
                vector[-2] += 1
            else:
                vector[-1] += 1
        return vector
