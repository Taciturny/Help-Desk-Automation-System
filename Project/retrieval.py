"""
Optimized Knowledge Retrieval System with Higher Confidence
"""
# Fix for Streamlit Cloud sqlite3 version issue
import sys
__import__('pysqlite3')
import pysqlite3
sys.modules['sqlite3'] = sys.modules['pysqlite3']

# Now import chromadb and other modules
import os
import logging
from typing import List, Dict, Any
import cohere
from chromadb.config import Settings
import chromadb

from data_models import RetrievalResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """Enhanced knowledge retrieval system with improved confidence scoring."""

    def __init__(self, cohere_api_key: str, collection_name: str = "helpdesk_kb"):
        self.cohere_client = cohere.Client(cohere_api_key)

        # Ensure the persistence directory exists
        self.persist_dir = "/tmp/chroma"
        os.makedirs(self.persist_dir, exist_ok=True)

        try:
            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    chroma_db_impl="duckdb+parquet",
                    anonymized_telemetry=False
                )
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise

        self.collection_name = collection_name
        self._setup_collection()

        # Enhanced keyword mapping for better retrieval
        self.keyword_categories = {
            "password": [
                "password",
                "login",
                "authenticate",
                "reset",
                "forgot",
                "locked",
                "access",
            ],
            "wifi": [
                "wifi",
                "wireless",
                "network",
                "internet",
                "connection",
                "connect",
            ],
            "software": [
                "install",
                "software",
                "application",
                "app",
                "download",
                "setup",
            ],
            "email": ["email", "outlook", "mail", "smtp", "imap", "exchange"],
            "hardware": [
                "hardware",
                "computer",
                "laptop",
                "printer",
                "monitor",
                "device",
            ],
        }

    def _setup_collection(self):
        """Setup ChromaDB collection with optimized settings."""
        try:
            # Try to get existing collection
            self.collection = self.chroma_client.get_collection(self.collection_name)
            logger.info(f"Using existing collection '{self.collection_name}'")
        except Exception as e:
            logger.info(f"No existing collection found, creating new one: {str(e)}")

            # Create a fresh collection
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={
                    "hnsw:space": "cosine",
                    "embedding_dimension": 1024,
                }
            )
            logger.info(f"Created new collection '{self.collection_name}'")
            logger.info("Created new collection with 1024-dimensional embeddings.")

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings with retry logic."""
        try:
            response = self.cohere_client.embed(
                texts=texts,
                model="embed-english-v3.0",  # More accurate model
                input_type="search_document",
                truncate="END",
            )
            return response.embeddings
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            # Fallback to lighter model
            response = self.cohere_client.embed(
                texts=texts,
                model="embed-english-light-v3.0",
                input_type="search_document",
            )
            return response.embeddings

    def _get_query_embedding(self, query: str) -> List[float]:
        """Get embedding for search query with query expansion."""
        # Expand query with related terms
        expanded_query = self._expand_query(query)

        response = self.cohere_client.embed(
            texts=[expanded_query],
            model="embed-english-v3.0",
            input_type="search_query",
        )
        return response.embeddings[0]

    def _expand_query(self, query: str) -> str:
        """Expand query with related keywords for better matching."""
        query_lower = query.lower()
        expanded_terms = []

        for _, keywords in self.keyword_categories.items():
            if any(keyword in query_lower for keyword in keywords):
                expanded_terms.extend(keywords[:3])  # Add top 3 related terms

        if expanded_terms:
            return f"{query} {' '.join(set(expanded_terms))}"
        return query

    def _calculate_confidence(
        self, distances: List[float], query: str, documents: List[str]
    ) -> List[float]:
        """Enhanced confidence calculation with multiple factors."""
        base_confidences = [1.0 / (1.0 + dist) for dist in distances]

        # Keyword matching boost
        query_words = set(query.lower().split())
        enhanced_confidences = []

        for confidence, doc in zip(base_confidences, documents):
            doc_words = set(doc.lower().split())
            keyword_overlap = len(query_words.intersection(doc_words)) / len(
                query_words
            )

            # Boost confidence based on keyword overlap
            keyword_boost = min(0.3, keyword_overlap * 0.5)
            enhanced_confidence = min(1.0, confidence + keyword_boost)
            enhanced_confidences.append(enhanced_confidence)

        return enhanced_confidences

    def _process_content_with_chunks(
        self, content: str, source: str, doc_type: str, category: str
    ) -> List[Dict]:
        """Split large content into meaningful chunks for better retrieval."""
        docs = []

        # Split by sections (double newlines or numbered steps)
        sections = []
        if "\n\n" in content:
            sections = [s.strip() for s in content.split("\n\n") if s.strip()]
        elif any(f"{i}." in content for i in range(1, 6)):
            # Handle numbered lists
            import re

            sections = re.split(r"\n(?=\d+\.)", content)
        else:
            sections = [content]

        for i, section in enumerate(sections):
            if len(section) > 50:  # Only meaningful chunks
                chunk_source = f"{source}_chunk_{i}" if len(sections) > 1 else source
                docs.append(
                    {
                        "content": section,
                        "source": chunk_source,
                        "type": doc_type,
                        "category": category,
                    }
                )

        return docs

    def load_knowledge_base(self, documents_path: str = "./"):
        """Load knowledge base with enhanced processing."""
        all_documents = []

        files = {
            "installation_guides.json": self._process_installation_guides,
            "troubleshooting_database.json": self._process_troubleshooting,
            "categories.json": self._process_categories,
            "company_it_policies.md": self._process_markdown,
            "knowledge_base.md": self._process_markdown,
        }

        for filename, processor in files.items():
            filepath = os.path.join(documents_path, filename)
            if os.path.exists(filepath):
                try:
                    documents = processor(filepath)
                    all_documents.extend(documents)
                    logger.info(f"Loaded {len(documents)} chunks from {filename}")
                except Exception as e:
                    logger.error(f"Error loading {filename}: {e}")

        if all_documents:
            self._add_to_db(all_documents)

        return len(all_documents)

    def _process_installation_guides(self, filepath: str) -> List[Dict]:
        """Enhanced processing of installation guides."""
        with open(filepath) as f:
            data = json.load(f)

        docs = []
        for app, guide in data.get("software_guides", {}).items():
            # Create main guide document
            content = f"Software Installation: {app}\n{guide['title']}\n"
            content += f"Application: {app}\nType: Installation Guide\n\n"
            content += "Installation Steps:\n"
            content += "\n".join(
                [f"{i+1}. {step}" for i, step in enumerate(guide["steps"])]
            )

            # Add system requirements if available
            if "requirements" in guide:
                content += f"\n\nSystem Requirements: {guide['requirements']}"

            docs.extend(
                self._process_content_with_chunks(
                    content, f"installation#{app}", "installation", app
                )
            )

        return docs

    def _process_troubleshooting(self, filepath: str) -> List[Dict]:
        """Enhanced processing of troubleshooting guides."""
        with open(filepath) as f:
            data = json.load(f)

        docs = []
        for issue, details in data.get("troubleshooting_steps", {}).items():
            content = f"Troubleshooting Guide: {issue}\n"
            content += f"Problem: {issue}\nCategory: {details['category']}\n\n"
            content += "Troubleshooting Steps:\n"
            content += "\n".join(
                [f"{i+1}. {step}" for i, step in enumerate(details["steps"])]
            )

            # Add common symptoms
            if "symptoms" in details:
                content += f"\n\nCommon Symptoms: {', '.join(details['symptoms'])}"

            docs.extend(
                self._process_content_with_chunks(
                    content,
                    f"troubleshooting#{issue}",
                    "troubleshooting",
                    details["category"],
                )
            )

        return docs

    def _process_categories(self, filepath: str) -> List[Dict]:
        """Process categories with enhanced metadata."""
        with open(filepath) as f:
            data = json.load(f)

        docs = []
        for cat, info in data.get("categories", {}).items():
            content = f"Support Category: {cat}\n"
            content += f"Description: {info['description']}\n"
            content += f"Typical Resolution Time: {info['typical_resolution_time']}\n"

            if "common_issues" in info:
                content += f"Common Issues: {', '.join(info['common_issues'])}"

            docs.append(
                {
                    "content": content,
                    "source": f"categories#{cat}",
                    "type": "category",
                    "category": cat,
                }
            )

        return docs

    def _process_markdown(self, filepath: str) -> List[Dict]:
        """Enhanced markdown processing with better section detection."""
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        docs = []
        # Split by headers (## or ### or #)
        import re

        sections = re.split(r"\n(#{1,3})\s+", content)

        current_section = ""
        for i, part in enumerate(sections):
            if part.startswith("#"):
                continue
            elif i > 0 and sections[i - 1].startswith("#"):
                # This is a header
                current_section = part.strip()
            else:
                # This is content
                if current_section and part.strip():
                    full_content = f"# {current_section}\n\n{part.strip()}"
                    docs.extend(
                        self._process_content_with_chunks(
                            full_content,
                            f"{os.path.basename(filepath)}#{current_section}",
                            "policy",
                            current_section,
                        )
                    )

        # Fallback: If no sections found, process entire content
        if not docs and content.strip():
            docs.extend(
                self._process_content_with_chunks(
                    content, os.path.basename(filepath), "policy", "general"
                )
            )

        return docs

    def _add_to_db(self, documents: List[Dict]):
        """Add documents to ChromaDB with batch processing."""
        batch_size = 10  # Process in smaller batches

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            contents = [doc["content"] for doc in batch]

            try:
                embeddings = self._get_embeddings(contents)

                ids = [f"doc_{i + j}" for j in range(len(batch))]
                metadatas = [
                    {
                        "source": doc["source"],
                        "type": doc["type"],
                        "category": doc["category"],
                        "content_length": len(doc["content"]),
                    }
                    for doc in batch
                ]

                self.collection.add(
                    embeddings=embeddings,
                    documents=contents,
                    metadatas=metadatas,
                    ids=ids,
                )
            except Exception as e:
                logger.error(f"Error adding batch {i}: {e}")

    def search_knowledge(self, query: str, n_results: int = 3) -> List[RetrievalResult]:
        """Enhanced search with reranking and confidence boosting."""
        try:
            # Get more initial results for reranking
            initial_results = min(n_results * 2, 20)
            query_embedding = self._get_query_embedding(query)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=initial_results,
                include=["documents", "metadatas", "distances"],
            )

            if not results["documents"][0]:
                return []

            # Enhanced confidence calculation
            confidence_scores = self._calculate_confidence(
                results["distances"][0], query, results["documents"][0]
            )

            # Create retrieval results
            retrieval_results = []
            for i in range(len(results["documents"][0])):
                retrieval_results.append(
                    RetrievalResult(
                        content=results["documents"][0][i],
                        source=results["metadatas"][0][i]["source"],
                        relevance_score=confidence_scores[i],
                        metadata=results["metadatas"][0][i],
                    )
                )

            # Sort by confidence and return top results
            sorted_results = sorted(
                retrieval_results, key=lambda x: x.relevance_score, reverse=True
            )
            return sorted_results[:n_results]

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get detailed collection statistics."""
        try:
            count = self.collection.count()
            return {
                "document_count": count,
                "collection_name": self.collection_name,
                "status": "healthy" if count > 0 else "empty",
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}


if __name__ == "__main__":
    API_KEY = os.getenv("COHERE_API_KEY", "your-api-key-here")

    if API_KEY == "your-api-key-here":
        print("Set COHERE_API_KEY environment variable")
        exit()

    retriever = KnowledgeRetriever(API_KEY)

    # Load knowledge base
    doc_count = retriever.load_knowledge_base()
    print(f"Loaded {doc_count} document chunks")

    # Test search with various queries
    test_queries = [
        "How do I reset my password?",
        "My WiFi won't connect",
        "Install Slack application",
        "What is the password policy?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = retriever.search_knowledge(query, n_results=3)

        for i, result in enumerate(results):
            print(f"{i+1}. Confidence: {result.relevance_score:.3f}")
            print(f"   Source: {result.source}")
            print(f"   Preview: {result.content[:100]}...")
            print(f"   Type: {result.metadata.get('type', 'unknown')}")
