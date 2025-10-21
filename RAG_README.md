# RAG (Retrieval-Augmented Generation) Utilities

This module provides utilities for implementing RAG-based chatbot functionality in the Spiritual Path Assessment application.

## Features

- **Data Loading**: Load text data from files or web pages
- **Text Chunking**: Split large texts into manageable chunks with overlap
- **Embeddings**: Generate semantic embeddings using sentence transformers
- **Semantic Search**: Find most relevant chunks based on query similarity
- **RAG Generation**: Generate context-aware responses using LLM
- **Visualization**: Visualize embeddings in 1D and 2D (t-SNE)

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Key dependencies:
- `sentence-transformers` - For generating embeddings
- `scikit-learn` - For similarity calculations and t-SNE
- `numpy` - For numerical operations
- `requests` & `beautifulsoup4` - For web scraping
- `plotly` - For visualizations

## Quick Start

### Basic Usage

```python
from rag_utils import (
    get_chunks,
    get_embeddings,
    retrieve_closest_chunk,
)

# 1. Load your text data
text_data = "Your text content here..."

# 2. Create chunks
chunks = get_chunks(text_data, chunk_size=500, overlap=50)

# 3. Generate embeddings
embeddings = get_embeddings(chunks)

# 4. Retrieve relevant chunk for a query
query = "What is Buddhism?"
chunk, similarity, idx, q_emb, similarities = retrieve_closest_chunk(
    query, chunks, embeddings
)

print(f"Most relevant chunk (similarity: {similarity:.3f}):")
print(chunk)
```

### Run the Example

```bash
python rag_example.py
```

This will:
1. Load religion data from `religions.csv`
2. Create text chunks and embeddings
3. Find the most relevant chunk for a sample question
4. Generate visualizations in the `rag_data/` directory
5. Optionally generate a RAG response (if `TOGETHER_API_KEY` is set)

## API Reference

### `load_data(file_path: str) -> str`

Load text data from a file.

**Parameters:**
- `file_path`: Path to text file

**Returns:** File contents as string

---

### `get_chunks(text: str, chunk_size: int = 500, overlap: int = 50, save_to: Optional[str] = None) -> List[str]`

Split text into overlapping chunks.

**Parameters:**
- `text`: Input text to chunk
- `chunk_size`: Maximum characters per chunk
- `overlap`: Overlapping characters between chunks
- `save_to`: Optional path to save chunks as JSON

**Returns:** List of text chunks

---

### `get_embeddings(chunks: List[str], model: str = "sentence-transformers/all-MiniLM-L6-v2", save_to: Optional[str] = None) -> np.ndarray`

Generate embeddings for text chunks.

**Parameters:**
- `chunks`: List of text chunks
- `model`: Name of sentence transformer model
- `save_to`: Optional path to save embeddings as pickle

**Returns:** NumPy array of embeddings

---

### `retrieve_closest_chunk(query: str, chunks: List[str], embeddings: np.ndarray, top_k: int = 1) -> Tuple`

Find most relevant chunk(s) for a query.

**Parameters:**
- `query`: User query string
- `chunks`: List of text chunks
- `embeddings`: Precomputed chunk embeddings
- `top_k`: Number of top chunks to retrieve

**Returns:** Tuple of (closest_chunk, similarity_score, chunk_index, query_embedding, all_similarities)

---

### `get_rag_with_chunk(query: str, chunk: str, chunk_idx: int, model_name: str = "meta-llama/Meta-Llama-3-8B-Instruct-Lite", api_key: Optional[str] = None, save_to: Optional[str] = None) -> Tuple`

Generate RAG response using retrieved chunk.

**Parameters:**
- `query`: User query
- `chunk`: Retrieved context chunk
- `chunk_idx`: Index of the chunk
- `model_name`: LLM model to use
- `api_key`: Together AI API key
- `save_to`: Optional directory to save response

**Returns:** Tuple of (response_text, chunk_content, chunk_index)

---

### `load_html_page(url: str, output_file: Optional[str] = None) -> str`

Load and parse HTML content from URL.

**Parameters:**
- `url`: URL to fetch
- `output_file`: Optional path to save text

**Returns:** Extracted text content

---

### `visualize_embeddings_1d(chunks: List[str], chunk_embeddings: np.ndarray, query: str, query_embedding: np.ndarray, title: str = "Embedding Similarity Visualization")`

Create 1D bar chart visualization of similarities.

**Returns:** Plotly figure object

---

### `visualize_embeddings_tsne(chunks: List[str], chunk_embeddings: np.ndarray, query: str, query_embedding: np.ndarray, title: str = "t-SNE Embedding Visualization", perplexity: int = 5)`

Create 2D t-SNE visualization of embeddings.

**Returns:** Plotly figure object

---

### `load_religions_from_csv(csv_path: str) -> Dict[str, Dict]`

Load religion data from CSV file.

**Parameters:**
- `csv_path`: Path to CSV file

**Returns:** Dictionary mapping religion keys to their data

---

### `prepare_religion_rag_context(religion_data: Dict, use_chunks: bool = True) -> List[str]`

Prepare RAG context from religion data.

**Parameters:**
- `religion_data`: Dictionary with religion information
- `use_chunks`: Whether to return as chunks or single string

**Returns:** List of context chunks or single string

## Integration with Flask App

The `app.py` file uses RAG utilities in the `/chat` endpoint:

```python
from rag_utils import (
    load_religions_from_csv,
    prepare_religion_rag_context,
)

# Load religion data at startup
RELIGIONS_CSV = load_religions_from_csv('religions.csv')

# In chat endpoint
@app.route("/chat", methods=["POST"])
def chat():
    # ... authentication checks ...
    
    # Prepare context using RAG utilities
    context_chunks = prepare_religion_rag_context(religion_data, use_chunks=False)
    
    # Build system prompt with context
    system_prompt = f"""You're a knowledgeable spiritual guide.
    
    {context_chunks[0]}
    
    Answer questions based on this context."""
    
    # Generate response...
```

## Advanced Usage

### Custom Chunk Size and Overlap

```python
# Smaller chunks for more granular retrieval
chunks = get_chunks(text, chunk_size=200, overlap=30)

# Larger chunks for more context
chunks = get_chunks(text, chunk_size=800, overlap=100)
```

### Using Different Embedding Models

```python
# Faster, smaller model
embeddings = get_embeddings(chunks, model="all-MiniLM-L6-v2")

# More accurate, larger model
embeddings = get_embeddings(chunks, model="all-mpnet-base-v2")
```

### Retrieving Multiple Chunks

```python
# Get top 3 most relevant chunks
chunk, sim, idx, q_emb, all_sims = retrieve_closest_chunk(
    query, chunks, embeddings, top_k=3
)

# Get indices of top k chunks
top_k_indices = all_sims.argsort()[-3:][::-1]
for i in top_k_indices:
    print(f"Chunk {i}: {chunks[i]}")
```

## Visualizations

The module generates two types of visualizations:

### 1D Similarity Visualization
- Bar chart showing similarity scores for each chunk
- Interactive hover to see chunk previews
- Saved as HTML file for viewing in browser

### t-SNE Visualization
- 2D scatter plot showing semantic relationships
- Query marked with star symbol
- Chunks colored by similarity score
- Shows clusters of related content

Open the generated HTML files in a browser to interact with them.

## Environment Variables

- `TOGETHER_API_KEY`: Required for RAG response generation

Set in `.env` file:
```
TOGETHER_API_KEY=your_api_key_here
```

## Performance Tips

1. **Cache embeddings**: Save embeddings to disk and reuse them
2. **Batch processing**: Process multiple chunks at once
3. **Adjust chunk size**: Balance between context and granularity
4. **Use appropriate models**: Smaller models are faster but less accurate

## Troubleshooting

### Import Error: sentence_transformers not found
```bash
pip install sentence-transformers
```

### Import Error: plotly not found
```bash
pip install plotly
```

### Memory issues with large datasets
- Reduce chunk size
- Process data in batches
- Use a smaller embedding model

### Low similarity scores
- Increase chunk size for more context
- Adjust overlap to capture boundary information
- Try a different embedding model

## License

Part of the Spiritual Path Assessment project.

