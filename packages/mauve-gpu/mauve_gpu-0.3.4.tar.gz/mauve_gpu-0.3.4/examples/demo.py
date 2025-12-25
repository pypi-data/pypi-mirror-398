import logging
from pathlib import Path

import pandas as pd

from sentence_transformers import SentenceTransformer

# Import from the installed package instead of src
from mauve-gpu import MauveScorer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Determine project root to locate data regardless of where script is run
project_root = Path(__file__).resolve().parent.parent
data_dir = project_root / "examples" / "data"

# 1. Loading + Embedding datasets
logger.info("Loading embedding model...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

logger.info("Loading and embedding AAPL data...")
aapl_path = data_dir / "bsky_aapl.csv"
aapl_df = pd.read_csv(aapl_path)
aapl_embeddings = embedding_model.encode(aapl_df["text"].astype(str).tolist())
logger.info(f"AAPL embeddings shape: {aapl_embeddings.shape}")

logger.info("Loading and embedding MSFT data...")
msft_path = data_dir / "bsky_msft.csv"
msft_df = pd.read_csv(msft_path)
msft_embeddings = embedding_model.encode(msft_df["text"].astype(str).tolist())
logger.info(f"MSFT embeddings shape: {msft_embeddings.shape}")

# 2. Calculate MAUVE
logger.info("Initializing MAUVE Scorer...")
scorer = MauveScorer(
    pca_components=50,
    kmeans_clusters=500,
    num_kmeans_runs=10,  # Use robust K-Means
    verbose=True         # Enable library logging
)

logger.info("Computing MAUVE score...")
score = scorer.compute(aapl_embeddings, msft_embeddings)
logger.info(f"MAUVE Score: {score:.4f}")