import numpy as np
from PIL import Image
import sentence_transformers
from sentence_transformers import SentenceTransformer


def main():
    # Verify imports
    _ = np.__version__
    _ = Image.__version__
    _ = sentence_transformers.__version__

    print("Initializing clip-ViT-B-32 model...")
    model = SentenceTransformer('clip-ViT-B-32')

    print("Running dummy inference...")
    embedding = model.encode("apple")

    if isinstance(embedding, np.ndarray) and embedding.size > 0:
        print("Vision Environment is Ready!")


if __name__ == "__main__":
    main()
