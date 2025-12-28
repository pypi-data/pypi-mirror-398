from pygeai.core.embeddings.managers import EmbeddingsManager
from pygeai.core.embeddings.models import EmbeddingConfiguration
from pygeai.core.services.llm.model import Model
from pygeai.core.services.llm.providers import Provider

manager = EmbeddingsManager()

inputs = [
    "Help me with Globant Enterprise AI",
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAAEElEQVR4nGK6HcwNCAAA//8DTgE8HuxwEQAAAABJRU5ErkJggg=="
]


configuration = EmbeddingConfiguration(
    inputs=inputs,
    model=f"{Provider.AWS_BEDROCK}/{Model.AWSBedrock.AMAZON_TITAN_EMBED_IMAGE_V1}",
    encoding_format=None,
    dimensions=None,
    user=None,
    input_type=None,
    timeout=600,
    cache=False
)

embeddings = manager.generate_embeddings(configuration)
print(embeddings)