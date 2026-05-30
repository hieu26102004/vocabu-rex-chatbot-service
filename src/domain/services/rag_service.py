"""RAG Service interface for document retrieval"""
from abc import ABC, abstractmethod
from typing import List


class RAGService(ABC):
    """Abstract interface for RAG (Retrieval-Augmented Generation) service"""
    
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 4) -> List[str]:
        """Retrieve relevant document chunks for a query
        
        Args:
            query: The search query text
            top_k: Number of top relevant chunks to retrieve
            
        Returns:
            List of relevant text chunks from the knowledge base
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """Check if RAG service is initialized and ready"""
        pass
