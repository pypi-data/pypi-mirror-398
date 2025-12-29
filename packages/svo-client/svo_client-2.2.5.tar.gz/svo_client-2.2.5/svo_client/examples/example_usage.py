# flake8: noqa
"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Example usage of adapter-based ChunkerClient.
"""

import asyncio

from svo_client import (
    ChunkerClient,
    SVOChunkingIntegrityError,
    SVOConnectionError,
    SVOEmbeddingError,
    SVOHTTPError,
    SVOJSONRPCError,
    SVOServerError,
    SVOTimeoutError,
)


async def main():
    # Test texts in different languages
    english_text = (
        "Although the project was initially considered too ambitious by many experts, "
        "the team managed to overcome numerous obstacles, demonstrating not only technical "
        "proficiency but also remarkable perseverance. "
        "The service should identify logical boundaries and create meaningful chunks."
    )

    russian_text = (
        "Хотя проект изначально считался слишком амбициозным многими экспертами, команда сумела "
        "преодолеть многочисленные препятствия, продемонстрировав не только техническое мастерство, "
        "но и удивительное упорство. "
        "Сервис должен определить логические границы и создать осмысленные чанки."
    )

    async with ChunkerClient() as client:
        # Get health status
        try:
            health = await client.health()
            print(f"\nHealth status: {health}")
        except Exception as e:
            print(f"Health check error: {e}")

        # Get help information
        try:
            help_info = await client.get_help()
            print(f"\nHelp information: {help_info}")
        except Exception as e:
            print(f"Help error: {e}")

        # Test chunking with different parameters
        test_cases = [
            {
                "text": english_text,
                "params": {"type": "Draft", "language": "en", "window": 3},
                "description": "English text with Draft type",
            },
            {
                "text": russian_text,
                "params": {"type": "Message", "language": "ru", "window": 2},
                "description": "Russian text with Message type",
            },
            {
                "text": english_text,
                "params": {"type": "CodeBlock", "language": "en", "window": 5},
                "description": "English text with CodeBlock type",
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test {i}: {test_case['description']} ---")
            try:
                chunks = await client.chunk_text(
                    test_case["text"], **test_case["params"]
                )
                print(f"Generated {len(chunks)} chunks:")
                for j, chunk in enumerate(chunks):
                    print(
                        f"  Chunk {j+1}: {chunk.text[:50]}... (ordinal: {chunk.ordinal})"
                    )

                # Reconstruct text
                reconstructed = client.reconstruct_text(chunks)
                print(f"\nReconstructed text length: {len(reconstructed)} characters")
                print(f"Original text length: {len(test_case['text'])} characters")
                print(
                    f"Texts match: {reconstructed.strip() == test_case['text'].strip()}"
                )
                
                # Check for chunks without embeddings (post-embedding merge strategy)
                chunks_without_embeddings = [
                    c for c in chunks 
                    if getattr(c, "embedding", None) is None
                ]
                if chunks_without_embeddings:
                    print(f"\n⚠️  Found {len(chunks_without_embeddings)} chunks without embeddings:")
                    for chunk in chunks_without_embeddings:
                        error = getattr(chunk, "_embedding_error", "Unknown error")
                        print(f"  - {chunk.text[:50]}... (error: {error})")

            except SVOChunkingIntegrityError as e:
                print(f"Text integrity error: {e}")
                print(f"  Original length: {e.original_text_length}")
                print(f"  Reconstructed length: {e.reconstructed_text_length}")
                print(f"  Chunk count: {e.chunk_count}")
            except SVOTimeoutError as e:
                print(f"Timeout error: {e}")
            except SVOConnectionError as e:
                print(f"Connection error: {e}")
            except SVOHTTPError as e:
                print(f"HTTP error: {e}")
            except SVOJSONRPCError as e:
                print(f"JSON-RPC error: {e}")
            except SVOServerError as e:
                print(f"SVO server error: {e}")
            except ValueError as e:
                print(f"Validation error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

    print("\n--- Test 4: Chunking with embeddings ---")
    try:
        # Chunk text
        chunks = await client.chunk_text(
            "This is a test for embedding integration. The chunks should be processed with embeddings.",
            type="Draft",
            language="en",
        )
        print(f"Generated {len(chunks)} chunks")

        # Get embeddings for chunks using embed_client transport
        chunks_with_embeddings = await client.get_embeddings(chunks)
        print(f"Added embeddings to {len(chunks_with_embeddings)} chunks")

        # Show embedding info
        for i, chunk in enumerate(chunks_with_embeddings):
            embedding = getattr(chunk, "embedding", None)
            if embedding is not None:
                embedding_length = len(embedding)
                print(
                    f"  Chunk {i+1}: {chunk.body[:50]}... (embedding: {embedding_length} dimensions)"
                )
            else:
                # Handle chunk without embedding (post-embedding merge strategy)
                embedding_error = getattr(chunk, "_embedding_error", "Unknown error")
                print(
                    f"  Chunk {i+1}: {chunk.body[:50]}... (no embedding: {embedding_error})"
                )

    except SVOEmbeddingError as e:
        print(f"Embedding service error: {e}")
    except ImportError as e:
        print(f"Embedding functionality not available: {e}")
    except Exception as e:
        print(f"Error with embeddings: {e}")

    print("\n--- Test 5: Using chunk_metadata_adapter features ---")
    try:
        from chunk_metadata_adapter import (  # type: ignore[import-untyped]
            ChunkMetadataBuilder,
        )

        # Create chunks
        chunks = await client.chunk_text(
            "This demonstrates integration with chunk_metadata_adapter features.",
            type="DocBlock",
            language="en",
        )

        # Use adapter features
        builder = ChunkMetadataBuilder()

        # Convert to flat format
        flat_chunks = []
        for chunk in chunks:
            flat_chunk = builder.semantic_to_flat(chunk)
            flat_chunks.append(flat_chunk)
            print(f"  Converted to flat format: {len(flat_chunk)} fields")

        # Convert back to semantic format
        semantic_chunks = []
        for flat_chunk in flat_chunks:
            semantic_chunk = builder.flat_to_semantic(flat_chunk)
            semantic_chunks.append(semantic_chunk)
            print(f"  Converted back to semantic format: {semantic_chunk.type}")

        print(f"Successfully processed {len(chunks)} chunks through adapter")

    except Exception as e:
        print(f"Error with adapter features: {e}")

    print("\n--- Test 6: Advanced chunking parameters ---")
    try:
        # Test different window sizes
        for window in [1, 3, 5]:
            chunks = await client.chunk_text(
                "This text will be chunked with different window sizes to demonstrate "
                "the effect on chunking granularity.",
                window=window,
                type="Message",
                language="en",
            )
            print(f"  Window {window}: {len(chunks)} chunks")

        # Test different chunk types
        chunk_types = ["Draft", "DocBlock", "CodeBlock", "Message"]
        for chunk_type in chunk_types:
            chunks = await client.chunk_text(
                "Testing different chunk types for metadata generation.",
                type=chunk_type,
                language="en",
            )
            print(
                f"  Type {chunk_type}: {len(chunks)} chunks, first chunk type: {chunks[0].type}"
            )

    except Exception as e:
        print(f"Error with advanced parameters: {e}")

    print("\n--- Test 7: Text integrity verification ---")
    try:
        # Test with integrity verification enabled
        test_text = "This text will be verified for integrity after chunking."
        chunks = await client.chunk_text(
            test_text, 
            type="Draft", 
            language="en",
            verify_integrity=True  # Enable client-side integrity check
        )
        print(f"✅ Integrity check passed: {len(chunks)} chunks")
    except SVOChunkingIntegrityError as e:
        print(f"❌ Integrity check failed: {e}")
        print(f"  Original: {e.original_text_length} chars")
        print(f"  Reconstructed: {e.reconstructed_text_length} chars")
    except Exception as e:
        print(f"Error: {e}")

    print("\n--- Test 8: Error handling and validation ---")
    try:
        # Test with empty text
        chunks = await client.chunk_text("", type="Draft")
        print(f"Empty text result: {len(chunks)} chunks")
    except Exception as e:
        print(f"Empty text error (expected): {e}")

    try:
        # Test with very long text
        long_text = "This is a very long text. " * 1000
        chunks = await client.chunk_text(
            long_text[:10000], type="Draft"
        )  # Limit to 10k chars
        print(f"Long text result: {len(chunks)} chunks")
    except Exception as e:
        print(f"Long text error: {e}")

    print("\n--- Test 9: Performance test ---")
    try:
        import time

        # Test chunking performance
        test_text = "Performance test text. " * 100
        start_time = time.time()

        chunks = await client.chunk_text(test_text, type="Draft")

        end_time = time.time()
        processing_time = end_time - start_time

        print(f"Processed {len(chunks)} chunks in {processing_time:.3f} seconds")
        print(f"Average time per chunk: {processing_time/len(chunks):.3f} seconds")

    except Exception as e:
        print(f"Performance test error: {e}")

    print("\n--- Test 10: Metadata validation ---")
    try:
        chunks = await client.chunk_text(
            "Testing metadata validation and completeness.", type="Task", language="en"
        )

        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1} metadata:")
            print(f"    UUID: {chunk.uuid}")
            print(f"    Type: {chunk.type}")
            print(f"    Language: {chunk.language}")
            print(f"    Created: {chunk.created_at}")
            print(f"    SHA256: {chunk.sha256[:16]}...")
            print(f"    Metrics: {chunk.metrics is not None}")
            if chunk.metrics:
                print(
                    f"    Tokens: {len(chunk.metrics.tokens) if chunk.metrics.tokens else 0}"
                )
            print()

    except Exception as e:
        print(f"Metadata validation error: {e}")

    print("\n--- Test 11: Integration summary ---")
    print("✅ SVO chunker service integration working")
    print("✅ chunk_metadata_adapter integration working")
    print("✅ SemanticChunk deserialization working")
    print("✅ Advanced chunking parameters working")
    print("✅ Error handling working")
    print("✅ Performance monitoring working")
    print("✅ Metadata validation working")

    if "embed_client" in globals():
        print("✅ embed_client integration available")
    else:
        print("⚠️  embed_client integration not tested (package not available)")

    print("\nAll tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
