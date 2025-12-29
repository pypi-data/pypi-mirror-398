import json
from pathlib import Path
import duckdb
import ollama
from ..mcp_logger import info_mcp, warning_mcp, log_error


class DatabasePreparation:
    """
    A class to handle DuckDB database preparation for micro_search functionality.
    This includes managing the embedding model, database directory, metadata,
    and installing necessary extensions.
    """
    
    def __init__(self):
        # Create the .contextnest directory in home directory
        self.contextnest_dir = Path.home() / '.contextnest'
        self.databases_dir = self.contextnest_dir / 'databases'
        self.metadata_file = self.contextnest_dir / 'metadata.json'
        self.current_db_name = None  # Store the current database name
        self.config = {
            "hnsw_enable_experimental_persistence": True,
        }

        # Create directories if they don't exist
        self.contextnest_dir.mkdir(exist_ok=True)
        self.databases_dir.mkdir(exist_ok=True)

        # Initialize metadata if it doesn't exist
        if not self.metadata_file.exists():
            self._initialize_metadata()
        else:
            self.metadata = self._load_metadata()
    
    def _initialize_metadata(self):
        """Initialize the metadata file with an empty structure."""
        self.metadata = {
            "databases": {}
        }
        self._save_metadata()
    
    def _load_metadata(self):
        """Load metadata from the JSON file."""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_metadata(self):
        """Save metadata to the JSON file."""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
    
    def ensure_embedding_model(self, model_name: str = "nomic-embed-text:latest"):
        """
        Check if the embedding model exists in Ollama, and pull it if it doesn't.
        
        Args:
            model_name: The name of the embedding model to ensure exists
        """
        try:
            # List existing models
            models_response = ollama.list()
            
            # Check if the model exists
            model_exists = any(
                model.get('name', '').startswith(model_name.split(':')[0])
                for model in models_response.get('models', [])
            )
            
            if not model_exists:
                info_mcp(f"Pulling Ollama model: {model_name}")
                ollama.pull(model_name)
                info_mcp(f"Successfully pulled model: {model_name}")
            else:
                info_mcp(f"Model {model_name} already exists")

        except Exception as e:
            log_error("Error ensuring embedding model", e, model_name)
            raise
    
    def install_duckdb_extensions(self, connection):
        """
        Install required DuckDB extensions: fts (Full Text Search) and vss (Vector Similarity Search).
        
        Args:
            connection: A DuckDB connection object
        """
        try:
            # Install and load FTS extension
            connection.execute("INSTALL fts;")
            connection.execute("LOAD fts;")
            info_mcp("Successfully installed and loaded FTS extension")

            # Install and load VSS extension
            connection.execute("INSTALL vss;")
            connection.execute("LOAD vss;")
            info_mcp("Successfully installed and loaded VSS extension")

        except Exception as e:
            log_error("Error installing DuckDB extensions", e)
            raise
    
    def create_database(self, db_name: str) -> duckdb.DuckDBPyConnection:
        """
        Create a new DuckDB database with the required extensions.

        Returns:
            A DuckDB connection object
        """
        
        db_path = self.databases_dir / f"{db_name}.db"
        conn = duckdb.connect(str(db_path), config=self.config)

        # Install required extensions
        self.install_duckdb_extensions(conn)

        # Add database to metadata if it doesn't exist
        if db_name not in self.metadata['databases']:
            self.metadata['databases'][db_name] = {
                "name": f"{db_name}.db",
                "links": []
            }
            self._save_metadata()

        # Set the current database name as a class attribute
        self.current_db_name = db_name

        info_mcp(f"Database created/loaded at: {db_path}")
        return conn
    
    def add_links_to_db_metadata(self, db_name: str, links: list):
        """
        Add links to the metadata for a specific database.
        
        Args:
            db_name: Name of the database
            links: List of links to add to the database metadata
        """
        if db_name in self.metadata['databases']:
            # Avoid duplicates
            current_links = set(self.metadata['databases'][db_name]['links'])
            new_links = set(links)
            all_links = list(current_links.union(new_links))

            self.metadata['databases'][db_name]['links'] = all_links
            self._save_metadata()
            info_mcp(f"Added {len(links)} links to database '{db_name}' metadata")
        else:
            warning_mcp(f"Database '{db_name}' not found in metadata")
    
    def get_database_connection(self) -> duckdb.DuckDBPyConnection:
        """
        Get a connection to an existing database, creating it if it doesn't exist.

        Args:
            db_name: Name of the database

        Returns:
            A DuckDB connection object
        """

        db_name = "micro_search"
        self.current_db_name = db_name  # Store the database name as a class attribute
        db_path = self.databases_dir / f"{db_name}.db"
        # Create database if it doesn't exist
        if not db_path.exists():
            return self.create_database(db_name)

        conn = duckdb.connect(str(db_path), config=self.config)
        self.install_duckdb_extensions(conn)

        # Ensure database entry exists in metadata
        if db_name not in self.metadata['databases']:
            self.metadata['databases'][db_name] = {
                "name": f"{db_name}.db",
                "links": []
            }
            self._save_metadata()

        return conn

    def is_url_in_database(self, url: str) -> bool:
        """
        Check if the given URL exists in the links of any database.

        Args:
            url: The URL to check for existence

        Returns:
            Boolean indicating whether the URL exists in any database links
        """
        # Reload metadata in case it was modified externally
        self.metadata = self._load_metadata()

        # Iterate through all databases in metadata
        for db_info in self.metadata['databases'].values():
            if url in db_info['links']:
                return True

        return False


# Convenience function to initialize the database preparation
def prepare_micro_search_db():
    """
    Convenience function to prepare the database environment for micro_search.
    
    Returns:
        DatabasePreparation instance
    """
    db_prep = DatabasePreparation()
    db_prep.ensure_embedding_model("nomic-embed-text:latest")
    return db_prep


def is_url_in_metadata(url: str) -> bool:
    """
    Check if the given URL exists in the metadata file.
    This is a standalone function that doesn't require a DatabasePreparation instance.

    Args:
        url: The URL to check for existence

    Returns:
        Boolean indicating whether the URL exists in any database links in metadata
    """
    metadata_file = Path.home() / '.contextnest' / 'metadata.json'
    
    # If metadata file doesn't exist, URL can't be in it
    if not metadata_file.exists():
        return False
    
    # Load and check metadata
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Check all databases for the URL
    for db_info in metadata.get('databases', {}).values():
        if url in db_info.get('links', []):
            return True
    
    return False