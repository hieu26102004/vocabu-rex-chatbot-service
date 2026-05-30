"""FAISS RAG Service implementation using Gemini Embeddings"""
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ...domain.services.rag_service import RAGService
from ...shared.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton instance
_rag_service_instance: Optional["FAISSRAGService"] = None


class FAISSRAGService(RAGService):
    """RAG service implementation using FAISS vectorstore and Gemini embeddings"""
    
    def __init__(
        self,
        pdf_dir: str,
        vectorstore_dir: str,
        api_key: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        top_k: int = 4
    ):
        self.pdf_dir = Path(pdf_dir)
        self.vectorstore_dir = Path(vectorstore_dir)
        self.api_key = api_key
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=self.api_key,
            task_type="retrieval_document"
        )
        
        self.vectorstore: Optional[FAISS] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the vectorstore - load existing or create new"""
        try:
            if self._try_load_vectorstore():
                logger.info("✅ Loaded existing FAISS vectorstore from disk")
            else:
                logger.info("📄 Building new FAISS vectorstore from PDF documents...")
                await self._build_vectorstore()
                logger.info("✅ FAISS vectorstore built and saved successfully")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG service: {e}")
            self._initialized = False
    
    async def retrieve(self, query: str, top_k: int = None) -> List[str]:
        """Retrieve relevant document chunks for a query"""
        if not self._initialized or self.vectorstore is None:
            logger.warning("RAG service not initialized, skipping retrieval")
            return []
        
        k = top_k or self.top_k
        
        try:
            # Run FAISS similarity search in thread pool to avoid blocking async loop
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None,
                lambda: self.vectorstore.similarity_search(query, k=k)
            )
            
            results = []
            for doc in docs:
                source = doc.metadata.get("source", "Unknown")
                source_name = Path(source).name if source != "Unknown" else source
                results.append(
                    f"[Nguồn: {source_name}]\n{doc.page_content}"
                )
            
            logger.info(f"RAG retrieved {len(results)} chunks for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return []
    
    async def is_available(self) -> bool:
        """Check if RAG service is initialized and ready"""
        return self._initialized and self.vectorstore is not None
    
    def _try_load_vectorstore(self) -> bool:
        """Try to load an existing vectorstore from disk"""
        index_file = self.vectorstore_dir / "index.faiss"
        if index_file.exists():
            try:
                self.vectorstore = FAISS.load_local(
                    str(self.vectorstore_dir),
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                return True
            except Exception as e:
                logger.warning(f"Failed to load existing vectorstore: {e}")
        return False
    
    async def _build_vectorstore(self) -> None:
        """Build vectorstore from PDF documents"""
        # Load PDF documents
        documents = self._load_documents()
        if not documents:
            logger.warning("No PDF documents found, RAG will be unavailable")
            return
        
        logger.info(f"📄 Loaded {len(documents)} pages from PDF documents")
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
        chunks = text_splitter.split_documents(documents)
        logger.info(f"✂️ Split into {len(chunks)} chunks")
        
        # Create FAISS vectorstore (run in thread pool - embedding calls are blocking)
        loop = asyncio.get_event_loop()
        self.vectorstore = await loop.run_in_executor(
            None,
            lambda: FAISS.from_documents(chunks, self.embeddings)
        )
        
        # Save to disk
        self.vectorstore_dir.mkdir(parents=True, exist_ok=True)
        self.vectorstore.save_local(str(self.vectorstore_dir))
        logger.info(f"💾 Vectorstore saved to {self.vectorstore_dir}")
    
    def _load_documents(self) -> list:
        """Load all PDF documents from the configured directory"""
        docs = []
        if not self.pdf_dir.exists():
            logger.warning(f"PDF directory not found: {self.pdf_dir}")
            return docs
        
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {self.pdf_dir}")
            return docs
        
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                loaded = loader.load()
                docs.extend(loaded)
                logger.info(f"  ✅ Loaded {pdf_file.name} ({len(loaded)} pages)")
            except Exception as e:
                logger.error(f"  ❌ Failed to load {pdf_file.name}: {e}")
        
        return docs
    
    async def rebuild_vectorstore(self) -> bool:
        """Force rebuild the vectorstore from current PDF documents"""
        try:
            logger.info("🔄 Rebuilding vectorstore...")
            await self._build_vectorstore()
            self._initialized = self.vectorstore is not None
            return self._initialized
        except Exception as e:
            logger.error(f"Failed to rebuild vectorstore: {e}")
            return False


async def initialize_rag_service() -> Optional[FAISSRAGService]:
    """Initialize the global RAG service instance at application startup"""
    global _rag_service_instance
    
    if not settings.rag_enabled:
        logger.info("RAG is disabled via configuration")
        return None
    
    try:
        _rag_service_instance = FAISSRAGService(
            pdf_dir=settings.rag_pdf_dir,
            vectorstore_dir=settings.rag_vectorstore_dir,
            api_key=settings.gemini_api_key,
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            top_k=settings.rag_top_k
        )
        await _rag_service_instance.initialize()
        return _rag_service_instance
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG service: {e}")
        _rag_service_instance = None
        return None


def get_rag_service() -> Optional[FAISSRAGService]:
    """Get the global RAG service instance (returns None if not initialized)"""
    return _rag_service_instance
