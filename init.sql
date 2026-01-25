-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create document_chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(384),
    tag VARCHAR(255),
    page_number INTEGER,
    chunk_id VARCHAR(255),
    source VARCHAR(255)
);

-- Create index for faster similarity search
CREATE INDEX IF NOT EXISTS embedding_idx ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
