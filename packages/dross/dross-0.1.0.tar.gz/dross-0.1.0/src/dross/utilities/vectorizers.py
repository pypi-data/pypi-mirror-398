"""Feature extraction and vectorization utilities."""

from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTfidfVectorizer


class TfidfVectorizer(SklearnTfidfVectorizer):
    """Wrapper around scikit-learn TfidfVectorizer for text feature extraction.

    Simplifies common usage patterns for ML pipelines.
    """

    def __init__(self, **kwargs):
        """Initialize TF-IDF vectorizer with sensible defaults.

        Args:
            **kwargs: Arguments passed to sklearn.feature_extraction.text.TfidfVectorizer

        """
        defaults = {
            "max_features": 5000,
            "lowercase": True,
            "stop_words": "english",
        }
        defaults.update(kwargs)
        super().__init__(**defaults)
