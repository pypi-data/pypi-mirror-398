"""
Build index command - Build RAG index
"""

from argparse import Namespace
from pathlib import Path

from ...utils.logger import get_logger
from .base import BaseCommand

logger = get_logger("docgen")


class BuildIndexCommand(BaseCommand):
    """RAGインデックス構築コマンド"""

    def execute(self, args: Namespace, project_root: Path) -> int:
        """
        Build RAG index

        Args:
            args: Command line arguments
            project_root: Project root directory

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        # Get config from args if available
        config = getattr(args, "config_dict", {})

        try:
            from ...rag.chunker import CodeChunker
            from ...rag.embedder import Embedder
            from ...rag.indexer import VectorIndexer

            logger.info("Starting RAG index construction...")

            # Get RAG config
            rag_config = config.get("rag", {})

            # 1. Chunk codebase
            logger.info("Step 1/3: Chunking codebase...")
            chunker = CodeChunker(rag_config)
            chunks = chunker.chunk_codebase(project_root)

            if not chunks:
                logger.warning("No chunks found")
                return 1

            logger.info(f"✓ Created {len(chunks)} chunks")

            # 2. Generate embeddings
            logger.info("Step 2/3: Generating embeddings...")
            embedder = Embedder(rag_config)

            # Extract text from chunks
            texts = [chunk["text"] for chunk in chunks]

            # Generate embeddings in batch
            embeddings = embedder.embed_batch(texts, batch_size=32)

            logger.info(f"✓ Generated {len(embeddings)} embeddings")

            # 3. Build index
            logger.info("Step 3/3: Building index...")
            index_dir = project_root / "docgen" / "index"
            indexer = VectorIndexer(
                index_dir=index_dir,
                embedding_dim=embedder.embedding_dim,
                config=rag_config,
            )

            # Build index
            indexer.build(embeddings, chunks)

            # Save
            indexer.save()

            logger.info(f"✓ Saved index: {index_dir}")
            logger.info("=" * 60)
            logger.info("RAG index construction completed!")
            logger.info("=" * 60)
            logger.info(f"Index directory: {index_dir}")
            logger.info(f"Chunk count: {len(chunks)}")
            logger.info(f"Embedding dim: {embedder.embedding_dim}")
            logger.info("")
            logger.info("Generate docs with RAG using:")
            logger.info("  uv run python -m docgen.docgen --use-rag")

            return 0

        except ImportError as e:
            logger.error(
                f"Failed to import RAG modules: {e}\n"
                "Please install RAG dependencies: uv sync --extra rag"
            )
            return 1
        except Exception as e:
            logger.error(f"Error building index: {e}", exc_info=True)
            return 1
