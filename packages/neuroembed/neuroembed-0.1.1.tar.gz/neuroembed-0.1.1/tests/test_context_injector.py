# tests/test_context_injector.py
import numpy as np
from neuroembed.context import ContextInjector

def test_enrich_with_none_context():
    injector = ContextInjector(alpha=0.7)

    base = np.random.rand(384)
    base = base / np.linalg.norm(base)

    result = injector.enrich(base, None)

    assert np.allclose(result, base), "Embedding should remain unchanged when context is None"

def test_enrich_with_empty_context():
    injector = ContextInjector(alpha=0.7)

    base = np.random.rand(384)
    base = base / np.linalg.norm(base)

    empty_context = np.array([])

    result = injector.enrich(base, empty_context)

    assert np.allclose(result, base), "Embedding should remain unchanged for empty context"

def test_enrich_with_valid_context_changes_embedding():
    injector = ContextInjector(alpha=0.5)

    base = np.random.rand(384)
    base = base / np.linalg.norm(base)

    context = np.random.rand(3, 384)
    context = context / np.linalg.norm(context, axis=1, keepdims=True)

    result = injector.enrich(base, context)

    assert result.shape == base.shape
    assert not np.allclose(result, base), "Embedding should change when context is provided"
    assert np.isclose(np.linalg.norm(result), 1.0, atol=1e-6)
