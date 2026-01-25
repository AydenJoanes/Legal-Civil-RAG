"""
PostgreSQL Vector Store - Repository Pattern Implementation

This module implements the Repository pattern, abstracting database
operations behind a clean interface. The business logic doesn't need
to know about PostgreSQL or pgvector specifics.

Design Pattern: Repository
SOLID Principle: 
    - Single Responsibility (only handles data persistence)
    - Dependency Inversion (implements IVectorStore interface)

Exception Handling:
    - Connection failure → DatabaseConnectionError
    - Query failure → DatabaseQueryError
"""
from typing import List, Dict, Optional
import psycopg2

from app.domain.interfaces.vector_store import IVectorStore
from app.db.models import get_connection
from app.core.logging import logger
from app.core.exceptions import DatabaseConnectionError, DatabaseQueryError


class PostgresVectorStore(IVectorStore):
    """
    PostgreSQL + pgvector implementation of vector store.
    
    Implements IVectorStore interface, allowing future swap to
    other vector databases (Pinecone, Chroma, Weaviate, etc.)
    
    Handles edge cases: connection failures, query errors, timeouts.
    """
    
    def _get_connection(self):
        """
        Get database connection with error handling.
        
        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            return get_connection()
        except psycopg2.OperationalError as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseConnectionError(str(e))
        except Exception as e:
            logger.error(f"Unexpected database connection error: {e}")
            raise DatabaseConnectionError(str(e))
    
    def add(self, records: List[Dict]) -> None:
        """
        Store document chunks with embeddings in PostgreSQL.
        
        Args:
            records: List of dicts with text, embedding, and metadata
            
        Raises:
            DatabaseConnectionError: If connection fails
            DatabaseQueryError: If insert fails
        """
        # Edge case: Empty records
        if not records:
            logger.warning("No records to add")
            return
        
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            for r in records:
                cur.execute(
                    """
                    INSERT INTO document_chunks
                    (content, embedding, tag, page_number, chunk_id, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        r["text"],
                        r["embedding"],
                        r["metadata"].get("tag"),
                        r["metadata"].get("page"),
                        r["metadata"].get("chunk_id"),
                        r["metadata"].get("source"),
                    ),
                )
            
            conn.commit()
            logger.debug(f"Stored {len(records)} chunks in database")
            
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Failed to store records: {e}")
            raise DatabaseQueryError("store documents", str(e))
        except Exception as e:
            conn.rollback()
            logger.error(f"Unexpected error storing records: {e}")
            raise DatabaseQueryError("store documents", str(e))
        finally:
            cur.close()
            conn.close()
    
    def search(
        self,
        query_embedding: Optional[List[float]] = None,
        tag: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Search for similar documents using pgvector.
        
        Args:
            query_embedding: Vector to search for (None for wildcard)
            tag: Optional tag filter
            top_k: Number of results to return
            
        Returns:
            List of matching documents with content and metadata
            
        Raises:
            DatabaseConnectionError: If connection fails
            DatabaseQueryError: If search fails
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Wildcard: return all documents (optionally filtered by tag)
            if query_embedding is None:
                if tag:
                    cur.execute(
                        """
                        SELECT content, tag, page_number, chunk_id, source
                        FROM document_chunks
                        WHERE tag = %s
                        ORDER BY page_number, chunk_id
                        """,
                        (tag,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT content, tag, page_number, chunk_id, source
                        FROM document_chunks
                        ORDER BY page_number, chunk_id
                        """
                    )
            
            # Semantic search using cosine distance
            else:
                if tag:
                    cur.execute(
                        """
                        SELECT content, tag, page_number, chunk_id, source
                        FROM document_chunks
                        WHERE tag = %s
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s
                        """,
                        (tag, query_embedding, top_k),
                    )
                else:
                    cur.execute(
                        """
                        SELECT content, tag, page_number, chunk_id, source
                        FROM document_chunks
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s
                        """,
                        (query_embedding, top_k),
                    )
            
            rows = cur.fetchall()
            
            return [
                {
                    "content": r[0],
                    "tag": r[1],
                    "page": r[2],
                    "chunk_id": r[3],
                    "source": r[4],
                }
                for r in rows
            ]
        
        except psycopg2.Error as e:
            logger.error(f"Database search failed: {e}")
            raise DatabaseQueryError("search documents", str(e))
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise DatabaseQueryError("search documents", str(e))
        finally:
            cur.close()
            conn.close()
    
    def delete_by_tag(self, tag: str) -> int:
        """
        Delete all documents with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            Number of deleted records
            
        Raises:
            DatabaseConnectionError: If connection fails
            DatabaseQueryError: If delete fails
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(
                """
                DELETE FROM document_chunks
                WHERE tag = %s
                """,
                (tag,),
            )
            
            deleted_count = cur.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted_count} chunks with tag '{tag}'")
            
            return deleted_count
            
        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Failed to delete records: {e}")
            raise DatabaseQueryError("delete documents", str(e))
        except Exception as e:
            conn.rollback()
            logger.error(f"Unexpected error deleting records: {e}")
            raise DatabaseQueryError("delete documents", str(e))
        finally:
            cur.close()
            conn.close()
