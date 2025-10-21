"""
RAG (Retrieval-Augmented Generation) Utilities
Provides functions for loading data, chunking, embedding, retrieval, and visualization
"""

import os
import json
import pickle
import re
from typing import List, Dict, Tuple, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import requests
from bs4 import BeautifulSoup


def load_data(file_path: str) -> str:
    """
    Load text data from a file
    
    Args:
        file_path: Path to the text file
        
    Returns:
        String containing the file contents
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = f.read()
        print(f"✅ Loaded data from {file_path} ({len(data)} characters)")
        return data
    except Exception as e:
        print(f"⚠️ Error loading data from {file_path}: {e}")
        return ""


def get_chunks(
    text: str, 
    chunk_size: int = 500, 
    overlap: int = 50,
    save_to: Optional[str] = None
) -> List[str]:
    """
    Split text into overlapping chunks
    
    Args:
        text: Input text to chunk
        chunk_size: Maximum size of each chunk in characters
        overlap: Number of overlapping characters between chunks
        save_to: Optional path to save chunks as JSON
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = chunk.rfind('.')
            last_newline = chunk.rfind('\n')
            break_point = max(last_period, last_newline)
            
            if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                chunk = chunk[:break_point + 1]
                end = start + break_point + 1
        
        chunks.append(chunk.strip())
        start = end - overlap
    
    print(f"✅ Created {len(chunks)} chunks (size: {chunk_size}, overlap: {overlap})")
    
    if save_to:
        try:
            with open(save_to, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved chunks to {save_to}")
        except Exception as e:
            print(f"⚠️ Error saving chunks: {e}")
    
    return chunks


def get_embeddings(
    chunks: List[str],
    model: str = "sentence-transformers/all-MiniLM-L6-v2",
    save_to: Optional[str] = None
) -> np.ndarray:
    """
    Generate embeddings for text chunks using a sentence transformer model
    
    Args:
        chunks: List of text chunks
        model: Name of the sentence transformer model
        save_to: Optional path to save embeddings as pickle
        
    Returns:
        Numpy array of embeddings
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        print(f"🔄 Loading model: {model}")
        embedding_model = SentenceTransformer(model)
        
        print(f"🔄 Generating embeddings for {len(chunks)} chunks...")
        embeddings = embedding_model.encode(chunks, show_progress_bar=True)
        
        print(f"✅ Generated embeddings with shape {embeddings.shape}")
        
        if save_to:
            try:
                with open(save_to, 'wb') as f:
                    pickle.dump(embeddings, f)
                print(f"✅ Saved embeddings to {save_to}")
            except Exception as e:
                print(f"⚠️ Error saving embeddings: {e}")
        
        return embeddings
        
    except ImportError:
        print("⚠️ sentence-transformers not installed. Install with: pip install sentence-transformers")
        return np.array([])
    except Exception as e:
        print(f"⚠️ Error generating embeddings: {e}")
        return np.array([])


def retrieve_closest_chunk(
    query: str,
    chunks: List[str],
    embeddings: np.ndarray,
    top_k: int = 1
) -> Tuple[str, float, int, np.ndarray, np.ndarray]:
    """
    Retrieve the most relevant chunk(s) for a query
    
    Args:
        query: User query string
        chunks: List of text chunks
        embeddings: Precomputed chunk embeddings
        top_k: Number of top chunks to retrieve
        
    Returns:
        Tuple of (closest_chunk, similarity_score, chunk_index, query_embedding, all_similarities)
    """
    try:
        from sentence_transformers import SentenceTransformer
        
        # Generate query embedding
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = model.encode([query])[0]
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], embeddings)[0]
        
        # Get top result
        top_idx = np.argmax(similarities)
        
        return (
            chunks[top_idx],
            float(similarities[top_idx]),
            int(top_idx),
            query_embedding,
            similarities
        )
        
    except Exception as e:
        print(f"⚠️ Error retrieving chunk: {e}")
        return ("", 0.0, 0, np.array([]), np.array([]))


def get_rag_with_chunk(
    query: str,
    chunk: str,
    chunk_idx: int,
    model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct-Lite",
    api_key: Optional[str] = None,
    save_to: Optional[str] = None
) -> Tuple[str, str, int]:
    """
    Generate a RAG response using the retrieved chunk as context
    
    Args:
        query: User query
        chunk: Retrieved context chunk
        chunk_idx: Index of the chunk
        model_name: LLM model to use
        api_key: API key for Together AI
        save_to: Optional directory to save the response
        
    Returns:
        Tuple of (response_text, chunk_content, chunk_index)
    """
    try:
        from together import Together
        
        if not api_key:
            api_key = os.getenv("TOGETHER_API_KEY")
        
        if not api_key:
            print("⚠️ No API key provided for RAG generation")
            return ("", chunk, chunk_idx)
        
        client = Together(api_key=api_key)
        
        # Create RAG prompt
        system_prompt = f"""You are a helpful assistant. Use the following context to answer the question.
        
CONTEXT:
{chunk}

Answer the question based on the context above. Be concise and accurate."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=200,
            temperature=0.7,
        )
        
        rag_response = response.choices[0].message.content
        
        if save_to:
            try:
                os.makedirs(save_to, exist_ok=True)
                response_file = os.path.join(save_to, "rag_response.txt")
                with open(response_file, 'w', encoding='utf-8') as f:
                    f.write(f"Query: {query}\n\n")
                    f.write(f"Context (Chunk {chunk_idx}):\n{chunk}\n\n")
                    f.write(f"Response:\n{rag_response}")
                print(f"✅ Saved RAG response to {response_file}")
            except Exception as e:
                print(f"⚠️ Error saving response: {e}")
        
        return (rag_response, chunk, chunk_idx)
        
    except Exception as e:
        print(f"⚠️ Error generating RAG response: {e}")
        return ("", chunk, chunk_idx)


def load_html_page(url: str, output_file: Optional[str] = None) -> str:
    """
    Load and parse HTML content from a URL
    
    Args:
        url: URL to fetch
        output_file: Optional path to save extracted text
        
    Returns:
        Extracted text content
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        print(f"✅ Loaded {len(text)} characters from {url}")
        
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"✅ Saved content to {output_file}")
            except Exception as e:
                print(f"⚠️ Error saving content: {e}")
        
        return text
        
    except Exception as e:
        print(f"⚠️ Error loading HTML page: {e}")
        return ""


def visualize_embeddings_1d(
    chunks: List[str],
    chunk_embeddings: np.ndarray,
    query: str,
    query_embedding: np.ndarray,
    title: str = "Embedding Similarity Visualization"
):
    """
    Create 1D visualization of embedding similarities
    
    Args:
        chunks: List of text chunks
        chunk_embeddings: Chunk embeddings
        query: Query string
        query_embedding: Query embedding
        title: Plot title
        
    Returns:
        Plotly figure object
    """
    try:
        import plotly.graph_objects as go
        
        # Calculate similarities
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        
        # Create figure
        fig = go.Figure()
        
        # Add bar chart for similarities
        fig.add_trace(go.Bar(
            x=list(range(len(chunks))),
            y=similarities,
            text=[f"{s:.3f}" for s in similarities],
            textposition='auto',
            hovertext=[f"Chunk {i}: {chunk[:100]}..." for i, chunk in enumerate(chunks)],
            marker=dict(
                color=similarities,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Similarity")
            )
        ))
        
        fig.update_layout(
            title=f"{title}<br><sub>Query: {query}</sub>",
            xaxis_title="Chunk Index",
            yaxis_title="Cosine Similarity",
            showlegend=False,
            height=500
        )
        
        return fig
        
    except ImportError:
        print("⚠️ plotly not installed. Install with: pip install plotly")
        return None
    except Exception as e:
        print(f"⚠️ Error creating visualization: {e}")
        return None


def visualize_embeddings_tsne(
    chunks: List[str],
    chunk_embeddings: np.ndarray,
    query: str,
    query_embedding: np.ndarray,
    title: str = "t-SNE Embedding Visualization",
    perplexity: int = 5
):
    """
    Create t-SNE visualization of embeddings in 2D space
    
    Args:
        chunks: List of text chunks
        chunk_embeddings: Chunk embeddings
        query: Query string
        query_embedding: Query embedding
        title: Plot title
        perplexity: t-SNE perplexity parameter
        
    Returns:
        Plotly figure object
    """
    try:
        import plotly.graph_objects as go
        from sklearn.manifold import TSNE
        
        # Combine query and chunk embeddings
        all_embeddings = np.vstack([query_embedding, chunk_embeddings])
        
        # Apply t-SNE
        print(f"🔄 Running t-SNE with perplexity={perplexity}...")
        tsne = TSNE(n_components=2, perplexity=min(perplexity, len(chunks)), random_state=42)
        embeddings_2d = tsne.fit_transform(all_embeddings)
        
        # Split back into query and chunks
        query_2d = embeddings_2d[0]
        chunks_2d = embeddings_2d[1:]
        
        # Calculate similarities for coloring
        similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
        
        # Create figure
        fig = go.Figure()
        
        # Add chunks
        fig.add_trace(go.Scatter(
            x=chunks_2d[:, 0],
            y=chunks_2d[:, 1],
            mode='markers+text',
            name='Chunks',
            text=[str(i) for i in range(len(chunks))],
            textposition='top center',
            marker=dict(
                size=12,
                color=similarities,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Similarity"),
                line=dict(width=1, color='white')
            ),
            hovertext=[f"Chunk {i} (sim: {similarities[i]:.3f}): {chunk[:100]}..." 
                      for i, chunk in enumerate(chunks)]
        ))
        
        # Add query
        fig.add_trace(go.Scatter(
            x=[query_2d[0]],
            y=[query_2d[1]],
            mode='markers+text',
            name='Query',
            text=['Q'],
            textposition='top center',
            marker=dict(
                size=20,
                color='red',
                symbol='star',
                line=dict(width=2, color='white')
            ),
            hovertext=[f"Query: {query}"]
        ))
        
        fig.update_layout(
            title=f"{title}<br><sub>Query: {query}</sub>",
            xaxis_title="t-SNE Dimension 1",
            yaxis_title="t-SNE Dimension 2",
            showlegend=True,
            height=600,
            hovermode='closest'
        )
        
        return fig
        
    except ImportError:
        print("⚠️ Required packages not installed. Install with: pip install plotly scikit-learn")
        return None
    except Exception as e:
        print(f"⚠️ Error creating t-SNE visualization: {e}")
        return None


def load_religions_from_csv(csv_path: str) -> Dict[str, Dict]:
    """
    Load religion data from CSV file
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        Dictionary mapping religion keys to their data
    """
    try:
        import csv
        religions = {}
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                religions[row['key']] = row
        print(f"✅ Loaded {len(religions)} religions from CSV")
        return religions
    except Exception as e:
        print(f"⚠️ Error loading religions CSV: {e}")
        return {}


def prepare_religion_rag_context(religion_data: Dict, use_chunks: bool = True) -> List[str]:
    """
    Prepare RAG context from religion data
    
    Args:
        religion_data: Dictionary containing religion information
        use_chunks: Whether to return as chunks or single string
        
    Returns:
        List of context chunks or single string
    """
    context_parts = []
    
    if 'description' in religion_data:
        context_parts.append(f"Description: {religion_data['description']}")
    
    if 'practices' in religion_data:
        context_parts.append(f"Practices: {religion_data['practices']}")
    
    if 'core_beliefs' in religion_data:
        context_parts.append(f"Core Beliefs: {religion_data['core_beliefs']}")
    
    if 'common_curiosities' in religion_data:
        context_parts.append(f"Common Questions & Facts: {religion_data['common_curiosities']}")
    
    if use_chunks:
        return context_parts
    else:
        return ['\n\n'.join(context_parts)]

