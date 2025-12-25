#!/usr/bin/env python3
"""
Backfill question_documents pivot table from existing database data.

This script populates the new question_documents table by extracting
document-question relationships from:
1. scored_documents → review_checkpoints (documents that were scored)
2. search_sessions with natural_language_query (documents found in searches)

Run this once after upgrading to populate the pivot table with legacy data.

Usage:
    python scripts/backfill_question_documents.py
"""

import logging
import sqlite3
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bmlibrarian_lite import LiteConfig
from bmlibrarian_lite.storage import LiteStorage, compute_question_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def backfill_from_scored_documents(storage: LiteStorage) -> int:
    """
    Backfill from scored_documents via review_checkpoints.

    Each scored document has a checkpoint_id, and each checkpoint
    has a research_question. This gives us document-question pairs.

    Returns:
        Number of associations added
    """
    added = 0

    with storage._sqlite_connection() as conn:
        # Get all unique document-question pairs from scored documents
        cursor = conn.execute(
            """
            SELECT DISTINCT
                sd.document_id,
                rc.research_question
            FROM scored_documents sd
            JOIN review_checkpoints rc ON sd.checkpoint_id = rc.id
            WHERE rc.research_question IS NOT NULL
              AND sd.document_id IS NOT NULL
            """
        )

        pairs = list(cursor)
        logger.info(f"Found {len(pairs)} document-question pairs from scored_documents")

        for doc_id, question in pairs:
            try:
                question_hash = compute_question_hash(question)
                conn.execute(
                    """
                    INSERT OR IGNORE INTO question_documents
                    (question_hash, document_id)
                    VALUES (?, ?)
                    """,
                    (question_hash, doc_id),
                )
                if conn.total_changes > 0:
                    added += 1
            except Exception as e:
                logger.warning(f"Failed to add {doc_id}: {e}")

        conn.commit()

    return added


def backfill_from_search_sessions(storage: LiteStorage) -> int:
    """
    Backfill from search_sessions by matching documents in ChromaDB.

    This is less precise since we can't directly link documents to
    sessions, but we can use the natural_language_query as the question.

    Note: This only works if documents are still in ChromaDB.

    Returns:
        Number of associations added
    """
    added = 0

    # Get all documents from ChromaDB
    try:
        collection = storage.get_documents_collection()
        all_docs = collection.get()
        doc_ids = set(all_docs.get("ids", []))
        logger.info(f"Found {len(doc_ids)} documents in ChromaDB")
    except Exception as e:
        logger.warning(f"Could not access ChromaDB: {e}")
        return 0

    with storage._sqlite_connection() as conn:
        # Get all unique questions from search sessions
        cursor = conn.execute(
            """
            SELECT DISTINCT natural_language_query
            FROM search_sessions
            WHERE natural_language_query IS NOT NULL
              AND natural_language_query != ''
            """
        )

        questions = [row["natural_language_query"] for row in cursor]
        logger.info(f"Found {len(questions)} unique questions from search_sessions")

        # For each question, find which documents might be associated
        # This is approximate - we associate all known documents with
        # questions that have scored documents for those doc IDs

        for question in questions:
            question_hash = compute_question_hash(question)

            # Find documents scored for this question
            cursor = conn.execute(
                """
                SELECT DISTINCT sd.document_id
                FROM scored_documents sd
                JOIN review_checkpoints rc ON sd.checkpoint_id = rc.id
                WHERE rc.research_question = ?
                """,
                (question,),
            )

            scored_doc_ids = {row["document_id"] for row in cursor}

            for doc_id in scored_doc_ids:
                if doc_id in doc_ids:  # Verify doc exists in ChromaDB
                    try:
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO question_documents
                            (question_hash, document_id)
                            VALUES (?, ?)
                            """,
                            (question_hash, doc_id),
                        )
                        if conn.total_changes > 0:
                            added += 1
                    except Exception:
                        pass

        conn.commit()

    return added


def backfill_all_chromadb_documents(storage: LiteStorage) -> int:
    """
    Backfill ALL documents from ChromaDB for each research question.

    This associates all documents in ChromaDB with research questions
    that have had searches run for them. This is necessary because
    documents may have been retrieved but not yet scored.

    Returns:
        Number of associations added
    """
    added = 0

    # Get all documents from ChromaDB
    try:
        collection = storage.get_documents_collection()
        all_docs = collection.get()
        all_doc_ids = set(all_docs.get("ids", []))
        logger.info(f"Found {len(all_doc_ids)} total documents in ChromaDB")
    except Exception as e:
        logger.warning(f"Could not access ChromaDB: {e}")
        return 0

    if not all_doc_ids:
        return 0

    with storage._sqlite_connection() as conn:
        # Get all unique questions from review_checkpoints (most reliable source)
        cursor = conn.execute(
            """
            SELECT DISTINCT research_question
            FROM review_checkpoints
            WHERE research_question IS NOT NULL
              AND research_question != ''
            """
        )

        questions = [row["research_question"] for row in cursor]
        logger.info(f"Found {len(questions)} unique research questions")

        for question in questions:
            question_hash = compute_question_hash(question)

            # Associate ALL documents in ChromaDB with this question
            # This is aggressive but ensures no documents are missed
            for doc_id in all_doc_ids:
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO question_documents
                        (question_hash, document_id)
                        VALUES (?, ?)
                        """,
                        (question_hash, doc_id),
                    )
                    if conn.total_changes > 0:
                        added += 1
                except Exception:
                    pass

        conn.commit()

    return added


def show_stats(storage: LiteStorage) -> None:
    """Show current statistics for the pivot table."""
    with storage._sqlite_connection() as conn:
        # Count total entries
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM question_documents")
        total = cursor.fetchone()["cnt"]

        # Count unique questions
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT question_hash) as cnt FROM question_documents"
        )
        questions = cursor.fetchone()["cnt"]

        # Count unique documents
        cursor = conn.execute(
            "SELECT COUNT(DISTINCT document_id) as cnt FROM question_documents"
        )
        documents = cursor.fetchone()["cnt"]

    logger.info(f"question_documents table stats:")
    logger.info(f"  Total entries: {total}")
    logger.info(f"  Unique questions: {questions}")
    logger.info(f"  Unique documents: {documents}")


def main() -> None:
    """Run the backfill process."""
    logger.info("Starting question_documents backfill...")

    # Load config and create storage
    config = LiteConfig.load()
    storage = LiteStorage(config)

    # Show initial stats
    logger.info("Before backfill:")
    show_stats(storage)

    # Run backfill from scored documents (most reliable source)
    logger.info("\nBackfilling from scored_documents...")
    added_scored = backfill_from_scored_documents(storage)
    logger.info(f"Added {added_scored} associations from scored_documents")

    # Run backfill from search sessions (supplementary)
    logger.info("\nBackfilling from search_sessions...")
    added_sessions = backfill_from_search_sessions(storage)
    logger.info(f"Added {added_sessions} associations from search_sessions")

    # Run aggressive backfill to catch ALL documents in ChromaDB
    logger.info("\nBackfilling ALL ChromaDB documents...")
    added_all = backfill_all_chromadb_documents(storage)
    logger.info(f"Added {added_all} associations from ChromaDB documents")

    # Show final stats
    logger.info("\nAfter backfill:")
    show_stats(storage)

    total_added = added_scored + added_sessions + added_all
    logger.info(f"\nBackfill complete! Added {total_added} total associations.")


if __name__ == "__main__":
    main()
