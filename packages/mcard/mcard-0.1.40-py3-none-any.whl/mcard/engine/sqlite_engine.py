import sqlite3
from typing import Optional, Union
import logging
import os
from mcard.model.card import MCard, MCardFromData
from mcard.model.pagination import Page
from mcard.engine.base import StorageEngine, DatabaseConnection
from mcard.config.settings import settings
# DEFAULT_PAGE_SIZE is used in function signatures, so we fetch it once or define a local constant
# However, usually we can access settings.pagination.default_page_size if it's constant.
# For function signatures, we can't use dynamic properties easily if they change.
# But settings are generally static after init.
# To avoid "argument default is mutable" or weirdness, we can grab the value.
DEFAULT_PAGE_SIZE = settings.pagination.default_page_size

logger = logging.getLogger(__name__)

class SQLiteConnection(DatabaseConnection):
    def __init__(self, db_path: str):
        if db_path == ":memory:":
            self.db_path = ":memory:"
        else:
            self.db_path = os.path.abspath(db_path)  # Ensure it's an absolute path
        self.conn: Optional[sqlite3.Connection] = None
        self.setup_database()  # Call the setup method during initialization

    def setup_database(self):
        """Check if the database file exists; if not, create it."""
        try:
            if self.db_path == ":memory:":
                # Connect to in-memory database
                self.conn = sqlite3.connect(":memory:")
            else:
                # Resolve the absolute path for the database
                if not os.path.isabs(self.db_path):
                    # Get the absolute path of the project's base directory
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    self.db_path = os.path.normpath(os.path.join(base_dir, self.db_path))

                # Ensure the directory exists
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

                # Connect to the database (creates the file if it doesn't exist)
                self.conn = sqlite3.connect(self.db_path)

            # Check if the card table exists
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='card'
            """)

            # Only create tables if they don't exist
            if not cursor.fetchone():
                logger.debug(f"Creating new database schema at {self.db_path}")
                from mcard.schema import MCardSchema
                cursor.execute(MCardSchema.get_instance().get_table('card'))
                self.conn.commit()
            else:
                logger.debug(f"Using existing database at {self.db_path}")

        except PermissionError as e:
            logger.error(f"Permission error: {e}")
            logger.error(f"Unable to access or create database at {self.db_path}")
            raise
        except sqlite3.Error as e:
            logger.error(f"SQLite error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error setting up database: {e}")
            raise

    def connect(self) -> None:
        logger.debug(f"Connecting to database at {self.db_path}")
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            logger.debug(f"Connection established to {self.db_path}")
            logger.debug(f"Database connection details: {self.conn}")
            # Check if the database is empty and initialize schema if necessary
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            if not tables:
                # Drop existing tables and triggers
                self.conn.execute("DROP TABLE IF EXISTS card")
                self.conn.execute("DROP TABLE IF EXISTS documents")
                
                # Use unified schema from singleton
                from mcard.schema import MCardSchema
                schema = MCardSchema.get_instance()
                
                # Create the card table from unified schema
                card_schema = schema.get_table('card')
                if card_schema:
                    logging.info(f"Executing SQL: {card_schema}")
                    self.conn.execute(card_schema)
                
                # Create legacy documents FTS table for trigger compatibility
                # This is needed because existing triggers reference 'documents'
                self.conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(content)")
                self.conn.commit()
                logger.debug("Database schema created successfully")
                
                # Use triggers from settings (legacy, references documents table)
                triggers = settings.database.triggers
                for trigger in triggers:
                    logging.info(f"Executing SQL: {trigger}")
                    self.conn.execute(trigger)
                    self.conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Database error connecting to {self.db_path}: {e}")
            raise

    def disconnect(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def commit(self) -> None:
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        if self.conn:
            self.conn.rollback()

class SQLiteEngine(StorageEngine):
    def __init__(self, connection: SQLiteConnection):
        self.connection = connection
        self.connection.connect()

    def __del__(self):
        self.connection.disconnect()

    def add(self, card: MCard) -> str:
        hash_value = str(card.hash)
        try:
            cursor = self.connection.conn.cursor()
            # Ensure content is bytes
            content_bytes = card.content if isinstance(card.content, bytes) else card.content.encode('utf-8')
            cursor.execute(
                "INSERT INTO card (hash, content, g_time) VALUES (?, ?, ?)",
                (hash_value, content_bytes, str(card.g_time))
            )
            self.connection.commit()
            logger.debug(f"Added card with hash {hash_value}")
            return hash_value
        except sqlite3.IntegrityError:
            raise ValueError(f"Card with hash {hash_value} and {str(card.g_time)} already exists, \n Content: {card.content[:20]}")


    def get(self, hash_value: str) -> Optional[MCard]:
        cursor = self.connection.conn.cursor()
        cursor.execute("SELECT content, g_time, hash FROM card WHERE hash = ?", (str(hash_value),))
        row = cursor.fetchone()

        if not row:
            return None

        content, g_time, hash = row
        # Make sure content is bytes
        if not isinstance(content, bytes):
            logger.warning(f"Content from database is not bytes but {type(content)}: {content[:20]}...")
            content_bytes = content.encode('utf-8') if isinstance(content, str) else bytes(content)
        else:
            content_bytes = content

        card = MCardFromData(content_bytes, hash, g_time) 
        return card

    def delete(self, hash_value: str) -> bool:
        cursor = self.connection.conn.cursor()
        cursor.execute("DELETE FROM card WHERE hash = ?", (str(hash_value),))
        self.connection.commit()
        return cursor.rowcount > 0

    def get_page(self, page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
        """Get a page of cards from the database.
        
        This is a convenience method that calls get_cards_by_page() with the same arguments.
        It's maintained for backward compatibility.
        
        Args:
            page_number: The page number (1-based).
            page_size: Number of items per page.
            
        Returns:
            A Page object containing the requested cards.
            
        Raises:
            ValueError: If page_number < 1 or page_size < 1
        """
        return self.get_cards_by_page(page_number, page_size)



    def search_by_string(self, search_string: str, page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
        """Search for cards by string in content, hash, or g_time"""
        if page_number < 1:
            raise ValueError("Page number must be >= 1")
        if page_size < 1:
            raise ValueError("Page size must be >= 1")

        offset = (page_number - 1) * page_size
        cursor = self.connection.conn.cursor()

        # Get total count of matching items
        cursor.execute("""
            SELECT COUNT(*) FROM card 
            WHERE hash LIKE ? OR g_time LIKE ? OR content LIKE ?
        """, (f"%{search_string}%", f"%{search_string}%", f"%{search_string}%"))
        total_items = cursor.fetchone()[0]

        # Get the actual items for the current page
        cursor.execute("""
            SELECT content, g_time, hash FROM card 
            WHERE hash LIKE ? OR g_time LIKE ? OR content LIKE ?
            ORDER BY g_time DESC LIMIT ? OFFSET ?
        """, (f"%{search_string}%", f"%{search_string}%", f"%{search_string}%", page_size, offset))

        items = []
        for row in cursor.fetchall():
            content, g_time, hash = row  # Assuming the row contains these values
            # Make sure content is bytes
            if not isinstance(content, bytes):
                logger.warning(f"Content from database is not bytes but {type(content)}: {content[:20]}...")
                content_bytes = content.encode('utf-8') if isinstance(content, str) else bytes(content)
            else:
                content_bytes = content

            card = MCardFromData(content_bytes, hash, g_time) 
            items.append(card)

        has_next = total_items > (page_number * page_size)
        has_previous = page_number > 1

        return Page(
            items=items,
            total_items=total_items,
            page_number=page_number,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous, total_pages=(total_items + page_size - 1) // page_size if page_size > 0 else 0
        )

    def search_by_content(self, search_string: Union[str, bytes], page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
        """Search for cards by string or binary pattern in content.
        
        Args:
            search_string: The string or binary pattern to search for
            page_number: The page number (1-based)
            page_size: Number of items per page
            
        Returns:
            A Page object containing the matching cards
        """
        if page_number < 1:
            raise ValueError("Page number must be >= 1")
        if page_size < 1:
            raise ValueError("Page size must be >= 1")

        if not search_string:
            raise ValueError("Search string cannot be empty")

        offset = (page_number - 1) * page_size
        cursor = self.connection.conn.cursor()

        # Convert search string to bytes if it's a string
        if isinstance(search_string, str):
            search_bytes = search_string.encode('utf-8')
        else:
            search_bytes = search_string

        # For binary search, we need to use the INSTR function to find the pattern
        cursor.execute("""
            SELECT COUNT(*) FROM card 
            WHERE INSTR(content, ?) > 0
        """, (search_bytes,))
        total_items = cursor.fetchone()[0]

        # Get the actual items for the current page
        cursor.execute("""
            SELECT content, g_time, hash FROM card 
            WHERE INSTR(content, ?) > 0
            ORDER BY g_time DESC
            LIMIT ? OFFSET ?
        """, (search_bytes, page_size, offset))

        items = []
        for row in cursor.fetchall():
            content, g_time, hash = row  # Assuming the row contains these values
            content_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
            card = MCardFromData(content_bytes, hash, g_time) 
            items.append(card)

        has_next = total_items > (page_number * page_size)
        has_previous = page_number > 1

        return Page(
            items=items,
            total_items=total_items,
            page_number=page_number,
            page_size=page_size,
            has_next=has_next,
            has_previous=has_previous, total_pages=(total_items + page_size - 1) // page_size if page_size > 0 else 0
        )

    def clear(self) -> None:
        cursor = self.connection.conn.cursor()
        cursor.execute("DELETE FROM card")
        self.connection.commit()

    def count(self) -> int:
        cursor = self.connection.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM card")
        return cursor.fetchone()[0]

    def get_all_cards(self) -> Page:
        """Get all cards from the database in a single page.
        
        Returns:
            A Page object containing all cards.
        """
        cursor = self.connection.conn.cursor()
        cursor.execute("SELECT content, hash, g_time FROM card")
        rows = cursor.fetchall()

        items = []
        for content, hash, g_time in rows:
            content_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
            card = MCardFromData(content_bytes, hash, g_time)
            items.append(card)

        # Return a single page with all items
        return Page(
            items=items,
            total_items=len(items),
            page_number=1,
            page_size=len(items) if items else 1,
            has_next=False,
            has_previous=False,
            total_pages=1
        )

    def get_cards_by_page(self, page_number: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Page:
        """Get a page of cards from the database.
        
        Args:
            page_number: The page number (1-based).
            page_size: Number of items per page.
            
        Returns:
            A Page object containing the requested cards.
            
        Raises:
            ValueError: If page_number < 1 or page_size < 1
        """
        if page_number < 1:
            raise ValueError("Page number must be >= 1")
        if page_size < 1:
            raise ValueError("Page size must be >= 1")

        cursor = self.connection.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM card")
        total_items = cursor.fetchone()[0]

        offset = (page_number - 1) * page_size
        cursor.execute(
            "SELECT content, g_time, hash FROM card ORDER BY g_time DESC LIMIT ? OFFSET ?",
            (page_size, offset)
        )

        items = []
        for row in cursor.fetchall():
            content, g_time, hash = row
            content_bytes = content if isinstance(content, bytes) else content.encode('utf-8')
            card = MCardFromData(content_bytes, hash, g_time)
            items.append(card)

        return Page(
            items=items,
            total_items=total_items,
            page_number=page_number,
            page_size=page_size,
            has_next=offset + len(items) < total_items,
            has_previous=page_number > 1,
            total_pages=(total_items + page_size - 1) // page_size if page_size > 0 else 0
        )

    # ========== Handle Operations ==========

    def ensure_handle_tables(self) -> None:
        """Ensure the handle_registry and handle_history tables exist."""
        from mcard.schema import MCardSchema
        schema = MCardSchema.get_instance()
        cursor = self.connection.conn.cursor()
        cursor.execute(schema.get_table('handle_registry'))
        cursor.execute(schema.get_table('handle_history'))
        cursor.execute(schema.get_index('idx_handle_current_hash'))
        self.connection.commit()
        logger.debug("Handle tables ensured.")

    def register_handle(self, handle: str, hash_value: str) -> bool:
        """Register a new handle pointing to a hash.
        
        Args:
            handle: The handle string (will be validated).
            hash_value: The MCard hash to point to.
            
        Returns:
            True if registration was successful.
            
        Raises:
            HandleValidationError: If the handle string is invalid.
            ValueError: If the handle already exists.
        """
        from mcard.model.handle import validate_handle
        from datetime import datetime, timezone
        
        self.ensure_handle_tables()
        validated = validate_handle(handle)
        now = datetime.now(timezone.utc).isoformat()
        
        try:
            cursor = self.connection.conn.cursor()
            cursor.execute(
                "INSERT INTO handle_registry (handle, current_hash, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (validated, hash_value, now, now)
            )
            self.connection.commit()
            logger.info(f"Registered handle '{validated}' -> {hash_value[:8]}...")
            return True
        except sqlite3.IntegrityError:
            raise ValueError(f"Handle '{validated}' already exists.")

    def update_handle(self, handle: str, new_hash: str) -> str:
        """Update an existing handle to point to a new hash.
        
        Args:
            handle: The handle string (will be validated).
            new_hash: The new MCard hash to point to.
            
        Returns:
            The previous hash (for history tracking).
            
        Raises:
            HandleValidationError: If the handle string is invalid.
            ValueError: If the handle does not exist.
        """
        from mcard.model.handle import validate_handle
        from datetime import datetime, timezone
        
        self.ensure_handle_tables()
        validated = validate_handle(handle)
        now = datetime.now(timezone.utc).isoformat()
        cursor = self.connection.conn.cursor()
        
        # Get current hash for history
        cursor.execute("SELECT current_hash FROM handle_registry WHERE handle = ?", (validated,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Handle '{validated}' not found.")
        
        previous_hash = row[0]
        
        # Update the handle
        cursor.execute(
            "UPDATE handle_registry SET current_hash = ?, updated_at = ? WHERE handle = ?",
            (new_hash, now, validated)
        )
        
        # Record history
        cursor.execute(
            "INSERT INTO handle_history (handle, previous_hash, changed_at) VALUES (?, ?, ?)",
            (validated, previous_hash, now)
        )
        self.connection.commit()
        logger.info(f"Updated handle '{validated}': {previous_hash[:8]}... -> {new_hash[:8]}...")
        return previous_hash

    def resolve_handle(self, handle: str) -> Optional[str]:
        """Resolve a handle to its current hash.
        
        Args:
            handle: The handle string (will be validated).
            
        Returns:
            The current hash, or None if the handle does not exist.
        """
        from mcard.model.handle import validate_handle
        
        self.ensure_handle_tables()
        validated = validate_handle(handle)
        cursor = self.connection.conn.cursor()
        cursor.execute("SELECT current_hash FROM handle_registry WHERE handle = ?", (validated,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_by_handle(self, handle: str) -> Optional[MCard]:
        """Get the MCard currently pointed to by a handle.
        
        Args:
            handle: The handle string (will be validated).
            
        Returns:
            The MCard, or None if the handle does not exist.
        """
        hash_value = self.resolve_handle(handle)
        if hash_value:
            return self.get(hash_value)
        return None

    def get_handle_history(self, handle: str) -> list:
        """Get the version history for a handle.
        
        Args:
            handle: The handle string (will be validated).
            
        Returns:
            A list of dicts with 'previous_hash' and 'changed_at' keys, ordered newest first.
        """
        from mcard.model.handle import validate_handle
        
        self.ensure_handle_tables()
        validated = validate_handle(handle)
        cursor = self.connection.conn.cursor()
        cursor.execute(
            "SELECT previous_hash, changed_at FROM handle_history WHERE handle = ? ORDER BY id DESC",
            (validated,)
        )
        return [{'previous_hash': row[0], 'changed_at': row[1]} for row in cursor.fetchall()]

    def prune_handle_history(self, handle: str, older_than: Optional[str] = None, delete_all: bool = False) -> int:
        """Prune version history for a handle.

        Args:
            handle: The handle string.
            older_than: Timestamp string (ISO format). If provided, delete entries older than this.
            delete_all: If True, delete all history for this handle.

        Returns:
            Number of rows deleted.
        """
        from mcard.model.handle import validate_handle
        
        self.ensure_handle_tables()
        validated = validate_handle(handle)
        cursor = self.connection.conn.cursor()
        
        if delete_all:
            cursor.execute("DELETE FROM handle_history WHERE handle = ?", (validated,))
        elif older_than:
            cursor.execute(
                "DELETE FROM handle_history WHERE handle = ? AND changed_at < ?",
                (validated, older_than)
            )
        else:
            return 0
            
        count = cursor.rowcount
        self.connection.commit()
        return count

