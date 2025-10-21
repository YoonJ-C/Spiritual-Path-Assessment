"""
Example script demonstrating RAG utilities usage
Similar to the reference code provided
"""

import os
from rag_utils import (
    load_data,
    get_chunks,
    get_embeddings,
    retrieve_closest_chunk,
    get_rag_with_chunk,
    visualize_embeddings_tsne,
    visualize_embeddings_1d,
    load_html_page,
    load_religions_from_csv,
)

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    base_path = "rag_data"
    os.makedirs(base_path, exist_ok=True)
    
    # Set your question here
    user_question = "What are the core practices in Buddhism?"
    
    print("\n" + "=" * 80)
    print("## USER QUESTION")
    print("-" * 80)
    print(f"Question: {user_question}")
    print("Searching for relevant information...")
    print("\n")
    
    # Optional: Load from external source
    # healthbc_website = load_html_page(
    #     url="https://en.wikipedia.org/wiki/Buddhism",
    #     output_file=f"{base_path}/buddhism_wiki.txt",
    # )
    
    # Load religions data and create a text corpus
    religions = load_religions_from_csv('religions.csv')
    
    # Create a text file from religions data for demonstration
    data_txt = ""
    for key, religion in religions.items():
        data_txt += f"\n\n{'='*60}\n"
        data_txt += f"Religion: {religion.get('name', key)}\n"
        data_txt += f"{'='*60}\n\n"
        data_txt += f"Description: {religion.get('description', '')}\n\n"
        data_txt += f"Practices: {religion.get('practices', '')}\n\n"
        data_txt += f"Core Beliefs: {religion.get('core_beliefs', '')}\n\n"
        if 'common_curiosities' in religion:
            data_txt += f"Common Questions: {religion.get('common_curiosities', '')}\n\n"
    
    # Save the corpus
    corpus_file = f"{base_path}/religions_corpus.txt"
    with open(corpus_file, 'w', encoding='utf-8') as f:
        f.write(data_txt)
    
    print(f"✅ Created corpus with {len(data_txt)} characters")
    
    # LOAD AND PROCESS DATA
    # ----------------------
    chunks = get_chunks(data_txt, chunk_size=300, overlap=50, save_to=f"{base_path}/chunks.json")
    
    print("\n🔄 Generating embeddings (this may take a moment)...")
    embeddings = get_embeddings(chunks, save_to=f"{base_path}/embeddings.pkl")
    
    if len(embeddings) == 0:
        print("⚠️ Could not generate embeddings. Please install sentence-transformers:")
        print("   pip install sentence-transformers")
        exit(1)
    
    # RETRIEVE CLOSEST CHUNK
    # -----------------------
    closest_chunk, similarity, chunk_idx, query_embedding, all_similarities = (
        retrieve_closest_chunk(user_question, chunks, embeddings)
    )
    
    # Save closest chunk to file
    with open(f"{base_path}/closest_chunk.txt", "w") as f:
        f.write(closest_chunk)
    
    print("\n" + "=" * 80)
    print("## SIMILARITY SCORES")
    print("-" * 80)
    
    # Show top 5 most similar chunks
    top_indices = all_similarities.argsort()[-5:][::-1]
    print("Top 5 most relevant chunks:")
    for idx in top_indices:
        print(f"Chunk {idx} (similarity: {all_similarities[idx]:.3f}): {chunks[idx][:80]}...")
        print()
    
    # GENERATE RAG RESPONSE
    # ---------------------
    print("\n" + "=" * 80)
    print("## RAG RESPONSE")
    print("-" * 80)
    
    if os.getenv("TOGETHER_API_KEY"):
        rag_output, chunk_content, chunk_index = get_rag_with_chunk(
            user_question, 
            closest_chunk, 
            chunk_idx,
            save_to=base_path
        )
        print(f"Response:\n{rag_output}")
        print(f"\nSource: Chunk {chunk_index} (similarity: {similarity:.3f})")
        print(f"Chunk Preview: {chunk_content[:100]}...")
    else:
        print("⚠️ TOGETHER_API_KEY not set. Skipping RAG response generation.")
        print(f"Most relevant chunk (similarity: {similarity:.3f}):")
        print(closest_chunk)
    
    # VISUALIZATION
    # --------------
    print("\n" + "=" * 80)
    print("## VISUALIZATION")
    print("-" * 80)
    
    # Create 1D similarity visualization
    print("Creating 1D similarity visualization...")
    fig_1d = visualize_embeddings_1d(
        chunks=chunks,
        chunk_embeddings=embeddings,
        query=user_question,
        query_embedding=query_embedding,
        title="Religion Data Embeddings - 1D Similarity",
    )
    
    if fig_1d:
        fig_1d.write_html(f"{base_path}/1d_similarity_visualization.html")
        print(f"✅ 1D visualization saved to {base_path}/1d_similarity_visualization.html")
    
    # Optional: Create t-SNE visualization (slower but shows relationships)
    if len(chunks) >= 3:  # t-SNE needs at least 3 samples
        print("\nCreating t-SNE visualization (this may take a moment)...")
        fig_tsne = visualize_embeddings_tsne(
            chunks=chunks,
            chunk_embeddings=embeddings,
            query=user_question,
            query_embedding=query_embedding,
            title="Religion Data Embeddings - t-SNE",
            perplexity=min(5, len(chunks) - 1)
        )
        
        if fig_tsne:
            fig_tsne.write_html(f"{base_path}/tsne_visualization.html")
            print(f"✅ t-SNE visualization saved to {base_path}/tsne_visualization.html")
    
    print("\n" + "=" * 80)
    print("## SUMMARY")
    print("-" * 80)
    print(f"✅ Processed {len(chunks)} chunks")
    print(f"✅ Found most relevant chunk with {similarity:.1%} similarity")
    print(f"✅ Visualizations saved to {base_path}/")
    print("=" * 80)

