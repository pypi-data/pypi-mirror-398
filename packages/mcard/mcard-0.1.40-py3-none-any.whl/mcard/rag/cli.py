#!/usr/bin/env python3
"""
MCard RAG CLI

Command-line interface for RAG operations.

Usage:
    mcard-rag index              # Index all MCards
    mcard-rag search "query"     # Semantic search
    mcard-rag query "question"   # RAG query with LLM
    mcard-rag status             # Show indexing status
    mcard-rag clear              # Clear vector index
"""

import argparse
import json
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def cmd_status(args):
    """Show RAG system status."""
    from mcard.rag import get_indexer
    from mcard.rag.embeddings import OllamaEmbeddingProvider
    
    print("=" * 60)
    print("MCard RAG System Status")
    print("=" * 60)
    
    # Check embedding provider
    provider = OllamaEmbeddingProvider()
    available = provider.validate_connection()
    print(f"\n📦 Embedding Model: {provider.model_name}")
    print(f"   Status: {'✅ Available' if available else '❌ Not available'}")
    print(f"   Dimensions: {provider.dimensions}")
    
    # Get indexer stats
    indexer = get_indexer()
    stats = indexer.get_stats()
    
    print(f"\n📊 Vector Index:")
    print(f"   Database: {stats['vector_db_path']}")
    print(f"   Indexed MCards: {stats['unique_mcards']}")
    print(f"   Total Vectors: {stats['vector_count']}")
    print(f"   sqlite-vec: {'✅' if stats['has_vec_extension'] else '❌ (fallback mode)'}")
    print(f"   Hybrid Search: {'✅' if stats['hybrid_search_enabled'] else '❌'}")
    
    # Show MCard collection count
    from mcard import default_collection
    total_mcards = default_collection.count()
    indexed = stats['unique_mcards']
    pending = total_mcards - indexed
    
    print(f"\n📁 Collection:")
    print(f"   Total MCards: {total_mcards}")
    print(f"   Indexed: {indexed}")
    print(f"   Pending: {pending}")
    
    if pending > 0:
        print(f"\n💡 Run 'mcard-rag index' to index {pending} pending cards")


def cmd_index(args):
    """Index all MCards."""
    from mcard.rag import get_indexer
    
    print("=" * 60)
    print("Indexing MCards")
    print("=" * 60)
    
    indexer = get_indexer()
    
    def progress(current, total):
        pct = (current / total) * 100 if total > 0 else 0
        print(f"\r  Progress: {current}/{total} ({pct:.1f}%)", end='', flush=True)
    
    print("\n📊 Starting index...")
    stats = indexer.index_all(force=args.force, progress_callback=progress)
    
    print(f"\n\n✅ Indexing Complete:")
    print(f"   Indexed: {stats['indexed']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Total: {stats['total']}")


def cmd_search(args):
    """Semantic search."""
    from mcard.rag import semantic_search
    
    print("=" * 60)
    print(f"Semantic Search: {args.query}")
    print("=" * 60)
    
    results = semantic_search(args.query, k=args.k)
    
    if not results:
        print("\n❌ No results found")
        return
    
    print(f"\n📋 Results ({len(results)} found):\n")
    
    for i, result in enumerate(results):
        print(f"[{i+1}] Score: {result.score:.4f}")
        print(f"    Hash: {result.hash}")
        if result.chunk_text:
            preview = result.chunk_text[:200].replace('\n', ' ')
            print(f"    Preview: {preview}...")
        print()


def cmd_query(args):
    """RAG query with LLM."""
    from mcard.rag import MCardRAGEngine, RAGConfig, get_indexer
    
    print("=" * 60)
    print(f"RAG Query: {args.question}")
    print("=" * 60)
    
    # Use persistent indexer's vector store
    indexer = get_indexer()
    
    # Create engine with indexer's vector store
    from mcard.rag.engine import MCardRAGEngine
    rag = MCardRAGEngine(vector_db_path=indexer.vector_db_path)
    rag.vector_store = indexer.vector_store
    
    print("\n🔍 Searching for context...")
    response = rag.query(
        args.question,
        k=args.k,
        model=args.model
    )
    
    print(f"\n💬 Answer:\n{response.answer}")
    print(f"\n📊 Confidence: {response.confidence:.2%}")
    print(f"📚 Sources: {[h[:8] for h in response.sources]}")
    
    if args.verbose:
        print("\n📝 Source Chunks:")
        for i, chunk in enumerate(response.source_chunks):
            if chunk:
                print(f"  [{i+1}] {chunk[:150]}...")


def cmd_clear(args):
    """Clear vector index."""
    from mcard.rag import get_indexer
    
    if not args.yes:
        confirm = input("Are you sure you want to clear the vector index? [y/N]: ")
        if confirm.lower() != 'y':
            print("Cancelled")
            return
    
    indexer = get_indexer()
    indexer.clear()
    print("✅ Vector index cleared")


def main():
    parser = argparse.ArgumentParser(
        description="MCard RAG CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show RAG system status')
    status_parser.set_defaults(func=cmd_status)
    
    # Index command
    index_parser = subparsers.add_parser('index', help='Index all MCards')
    index_parser.add_argument('--force', '-f', action='store_true',
                             help='Re-index existing cards')
    index_parser.set_defaults(func=cmd_index)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Semantic search')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('-k', type=int, default=5,
                              help='Number of results (default: 5)')
    search_parser.set_defaults(func=cmd_search)
    
    # Query command
    query_parser = subparsers.add_parser('query', help='RAG query with LLM')
    query_parser.add_argument('question', help='Question to answer')
    query_parser.add_argument('-k', type=int, default=5,
                             help='Number of context chunks (default: 5)')
    query_parser.add_argument('--model', '-m', default='gemma3:latest',
                             help='LLM model (default: gemma3:latest)')
    query_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Show source chunks')
    query_parser.set_defaults(func=cmd_query)
    
    # Clear command
    clear_parser = subparsers.add_parser('clear', help='Clear vector index')
    clear_parser.add_argument('--yes', '-y', action='store_true',
                             help='Skip confirmation')
    clear_parser.set_defaults(func=cmd_clear)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    try:
        args.func(args)
    except Exception as e:
        logger.error(f"Error: {e}")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
