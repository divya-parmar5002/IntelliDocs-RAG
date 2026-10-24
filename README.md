#IntelliDocs — Local AI Document Q&A using RAG

IntelliDocs is an AI-powered document question-answering application. Users can upload documents, create separate workspaces, and ask questions in natural language.

Instead of manually searching exact keywords in large PDFs, IntelliDocs uses Retrieval-Augmented Generation (RAG) to retrieve semantically relevant document content and generate an answer grounded in that context.

This is an academic customization of the open-source Quivr project, adapted for a local Ollama-based RAG workflow.

Table of Contents
Problem Statement
Key Features
Architecture
RAG Workflow
Tech Stack
Workspace Isolation
Prerequisites
Local Setup
Manual Docker Start
Important Notes
Author
Problem Statement

Traditional document search often requires users to know the exact keyword and manually read through long documents.

IntelliDocs helps users ask questions such as:

text
What is cloud computing?
What are the types of grid computing?
Explain token-based authentication.

The system searches relevant uploaded-document chunks and uses them as context for the answer.

Key Features
Upload and query documents through a web interface.
Natural-language document question answering.
Semantic search using text embeddings instead of only exact keyword matching.
Workspace-based document isolation using brain_id.
Local answer generation using Ollama and Llama 3.2.
Local embedding generation using nomic-embed-text.
Docker-based local setup.
Streaming answer support in the chat interface.
Retry handling for temporary embedding-service failures.
Redis and Celery support for background processing.
Architecture
text
User
  ↓
React / Next.js Frontend
  ↓
FastAPI Backend
  ↓
Question Embedding — nomic-embed-text via Ollama
  ↓
pgvector Similarity Search — filtered by brain_id
  ↓
Relevant Document Chunks
  ↓
Question + Retrieved Context
  ↓
Llama 3.2 via Ollama
  ↓
Generated Answer in Chat UI
RAG Workflow
1. Document ingestion
text
Document upload
  → Text extraction
  → Chunking
  → Chunk embeddings
  → Storage in Supabase PostgreSQL with pgvector
2. Question answering
text
User question
  → Question embedding
  → Semantic similarity search
  → Workspace-scoped retrieval using brain_id
  → Relevant chunks added to prompt
  → Llama 3.2 generates an answer
Tech Stack
Layer	Technology
Frontend	React / Next.js
Backend	Python / FastAPI
LLM runtime	Ollama
Chat model	Llama 3.2 (llama3.2:3b)
Embedding model	nomic-embed-text
Database	Supabase PostgreSQL
Vector search	pgvector
Background processing	Celery + Redis
Containerization	Docker Compose
Workspace Isolation

Each workspace is represented by a brain_id.

When a user asks a question, vector retrieval is scoped to the selected brain_id. This helps ensure that documents from one workspace are not mixed with documents from another workspace.

text
Selected workspace
  → brain_id filter
  → Search only that workspace's document chunks
  → Generate answer from relevant context
Prerequisites

Install the following before starting:

Docker Desktop
Ollama for Windows
Git
At least 8 GB RAM recommended for local model execution

Pull the required local models:

powershell
ollama pull nomic-embed-text
ollama pull llama3.2:3b
Local Setup

Clone the repository:

powershell
git clone https://github.com/divya-parmar5002/IntelliDocs-RAG.git
cd IntelliDocs-RAG

Create your local environment file:

powershell
Copy-Item .env.example .env

Ensure Ollama is configured in .env:

env
OLLAMA_API_BASE_URL=http://host.docker.internal:11434

Start the application:

powershell
.\Start-IntelliDocs.cmd

Then open:

text
http://localhost:3000

Backend health check:

text
http://localhost:5050/healthz
Manual Docker Start

If needed, start the services manually:

powershell
docker compose up -d

Check running containers:

powershell
docker compose ps

Check backend logs:

powershell
docker logs backend-core --tail 100
Important Notes
Do not upload .env to GitHub.
Local CPU-only inference can be slower than cloud/GPU models.
Answer quality depends on document text extraction, chunking, retrieval quality, and the local LLM.
If a document does not contain the requested information, the system may not provide a reliable answer.
LICENSE is retained because this project is derived from the open-source Quivr project.
Author

Divya Parmar

Academic project: IntelliDocs — Local AI-Powered Document Question Answering using RAG.
