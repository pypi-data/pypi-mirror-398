"""
Insertion module for the micro search functionality.
Handles document processing, chunking, embedding, and database insertion.
"""
from ..mcp_logger import info_mcp, debug_mcp, warning_mcp, log_error
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..micro_search.database import get_database
import ollama
from google import genai
from google.genai import types
import numpy as np
from tqdm import tqdm


class DocumentInserter:
    """
    Class responsible for inserting documents into the database after
    processing them through chunking and embedding.
    """

    def __init__(self, max_characters: int = 2000):
        """
        Initialize the DocumentInserter.

        Args:
            max_characters: Maximum number of characters per chunk
        """
        self.max_characters = max_characters
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size = self.max_characters,
            chunk_overlap = 500,
            length_function=len,
        )
        self.gemini_client = genai.Client()

    def split_content(self, content: str) -> list[str]:
        """
        Split content into chunks using MarkdownSplitter.

        Args:
            content: The content to split

        Returns:
            List of content chunks
        """
        chunks = self.splitter.split_text(content)
        debug_mcp(f"Content split into {len(chunks)} chunks")
        return chunks

    def _get_ollama_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as a list of floats
        """
        response = ollama.embeddings(
            model="nomic-embed-text:latest",
            prompt=text
        )
        embedding = response.get('embedding')
        if embedding is None:
            raise ValueError(f"No embedding returned for text: {text[:50]}...")

        debug_mcp(f"Generated Ollama embedding of length {len(embedding)} for text chunk")
        return embedding

    def _get_gemini_embedding(self, text: str) -> list[float]:
        """
        Generate embedding for text using Gemini.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as a list of floats
        """
        response = self.gemini_client.models.embed_content(
            model="gemini-embedding-exp-03-07",
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="RETRIEVAL_DOCUMENT"
            )
        )
        embedding = np.array(response.embeddings[0].values)
        normed_embedding = embedding / np.linalg.norm(embedding)
        normed_embedding = normed_embedding.tolist()
        if normed_embedding is None:
            raise ValueError(f"No embedding returned from Gemini for text: {text[:50]}...")

        debug_mcp(f"Generated Gemini embedding of length {len(normed_embedding)} for text chunk")
        return normed_embedding

    def get_embedding(self, text: str, local_model: bool = False) -> list[float]:
        """
        Generate embedding for text using either Gemini or Ollama.

        Args:
            text: Text to embed
            local_model: If True, use Ollama (local). If False (default), use Gemini with Ollama fallback.

        Returns:
            Embedding vector as a list of floats
        """
        try:
            if local_model:
                # Use Ollama directly when local_model is True
                info_mcp("Using Ollama for embedding")
                return self._get_ollama_embedding(text)
            else:
                # Use Gemini by default, with fallback to Ollama on error
                info_mcp("Using Gemini for embedding")
                try:
                    return self._get_gemini_embedding(text)
                except Exception as gemini_error:
                    warning_mcp(f"Gemini embedding failed: {gemini_error}. Falling back to Ollama.")
                    return self._get_ollama_embedding(text)
        except Exception as e:
            log_error("get_embedding", e)
            raise

    def insert_document_chunks(self, url: str, title: str, content: str):
        """
        Process and insert a document into the database by splitting it into chunks,
        generating embeddings, and storing in the database.

        Args:
            url: URL of the document
            title: Title of the document
            content: Content of the document
        """

        # Get database instance
        db = get_database()

        # add the link to the metadata...
        if not db.db_prep.is_url_in_database(url):
            db.db_prep.add_links_to_db_metadata(
                db_name = db.db_prep.current_db_name,
                links = [url]
            )
            try:
                # Split content into chunks
                chunks = self.split_content(content)
                info_mcp(f"Processing document '{title}' with {len(chunks)} chunks")
                
                # Process each chunk
                for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
                    debug_mcp(f"Processing chunk {i+1}/{len(chunks)} for document '{title}'")

                    # Generate embedding for the chunk
                    embedding = self.get_embedding(chunk)

                    # Insert the chunk into the database
                    chunk_title = f"{title} - Chunk {i+1}"
                    db.insert_document(url=url, title=chunk_title, content=chunk, embedding=embedding)

                    debug_mcp(f"Inserted chunk {i+1}/{len(chunks)} for document '{title}'")

                info_mcp(f"Successfully processed and inserted document '{title}' with {len(chunks)} chunks")
            except Exception as e:
                log_error("insert_document_chunks", e)
                raise
        else:
            warning_mcp(f"Document '{url}' already exists in the database")
        db.close()


def insert_document(url: str, title: str, content: str):
    """
    Convenience function to insert a document into the database.

    Args:
        url: URL of the document
        title: Title of the document
        content: Content of the document
    """
    inserter = DocumentInserter()
    inserter.insert_document_chunks(url, title, content)