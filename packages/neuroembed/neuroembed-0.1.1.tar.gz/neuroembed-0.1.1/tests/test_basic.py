from neuroembed.core import NeuroEmbed
from neuroembed.encoders.sentence_transformer import SentenceTransformerEncoder

def test_neuroembed_runs():
    encoder = SentenceTransformerEncoder()
    ne = NeuroEmbed(encoder)

    emb = ne.embed("hello world", ["greeting", "english language"])
    assert emb.shape[0] > 0
