import os
import json
import time
import faiss
import numpy as np
from pathlib import Path
from utils.summarizer import generate_embeddings

class VectorDB:
    """Vector database for storing and retrieving knowledge."""
    
    def __init__(self, profile="default"):
        """
        Initialize the vector database.
        
        Args:
            profile (str): User profile name
        """
        self.profile = profile
        self.data_dir = Path(f"data/{profile}")
        self.data_dir.mkdir(exist_ok=True)
        
        self.index_path = self.data_dir / "faiss_index.bin"
        self.metadata_path = self.data_dir / "metadata.json"
        
        # Initialize or load the index and metadata
        if self.index_path.exists() and self.metadata_path.exists():
            self.index = faiss.read_index(str(self.index_path))
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            # Create a new index - 64 is the dimension for our simplified embedding model
            self.index = faiss.IndexFlatL2(64)
            self.metadata = []
            
    def save(self):
        """Save the index and metadata to disk."""
        faiss.write_index(self.index, str(self.index_path))
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f)
            
    def add(self, topic, content, source="", embeddings=None):
        """
        Add content to the vector database.
        
        Args:
            topic (str): Topic or title of the content
            content (str): The actual content text
            source (str): Source of the content (URL, PDF name, etc.)
            embeddings (numpy.ndarray): Pre-computed embeddings (optional)
            
        Returns:
            int: ID of the added item
        """
        # Generate embeddings if not provided
        if embeddings is None:
            embeddings = generate_embeddings(content)
            
        # Convert embeddings to expected format
        embeddings_array = np.array([embeddings]).astype('float32')
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Get the ID (index position)
        idx = len(self.metadata)
        
        # Add metadata
        self.metadata.append({
            "id": idx,
            "topic": topic,
            "content": content,
            "source": source,
            "date": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Save to disk
        self.save()
        
        return idx
        
    def search(self, query, top_k=5):
        """
        Search the vector database for relevant content.
        
        Args:
            query (str): Search query
            top_k (int): Number of results to return
            
        Returns:
            list: List of dictionaries with search results
        """
        if len(self.metadata) == 0:
            return []
            
        # Get query embeddings
        query_vector = generate_embeddings(query)
        query_vector = np.array([query_vector]).astype('float32')
        
        # Set the number of results to return (limited by available items)
        k = min(top_k, len(self.metadata))
        
        # Search
        distances, indices = self.index.search(query_vector, k)
        
        # Format results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.metadata):  # Ensure index is valid
                # Calculate a similarity score (1 - normalized distance)
                # Lower distance means higher similarity
                max_distance = max(distances[0]) if len(distances[0]) > 0 else 1
                similarity = 1 - (distances[0][i] / max_distance) if max_distance > 0 else 0
                
                # Add result with metadata and similarity score
                result = self.metadata[idx].copy()
                result["score"] = float(similarity)
                results.append(result)
                
        return results
        
    def get_all_topics(self):
        """
        Get all topics in the database.
        
        Returns:
            list: List of topic strings
        """
        return list(set(item["topic"] for item in self.metadata))
        
    def get_by_topic(self, topic):
        """
        Get all content for a specific topic.
        
        Args:
            topic (str): Topic to retrieve
            
        Returns:
            list: List of content items for the topic
        """
        return [item for item in self.metadata if item["topic"] == topic]
        
    def delete_by_topic(self, topic):
        """
        Delete all content for a specific topic.
        
        Args:
            topic (str): Topic to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        # This is a simplified implementation - in a real-world scenario,
        # we would need to rebuild the index after deletion
        
        # Save the items we want to keep
        keep_items = [item for item in self.metadata if item["topic"] != topic]
        
        # If no items were removed, return False
        if len(keep_items) == len(self.metadata):
            return False
            
        # Rebuild the index and metadata
        new_index = faiss.IndexFlatL2(64)
        new_metadata = []
        
        for i, item in enumerate(keep_items):
            embeddings = generate_embeddings(item["content"])
            embeddings_array = np.array([embeddings]).astype('float32')
            new_index.add(embeddings_array)
            
            new_item = item.copy()
            new_item["id"] = i
            new_metadata.append(new_item)
            
        # Update the instance variables
        self.index = new_index
        self.metadata = new_metadata
        
        # Save to disk
        self.save()
        
        return True

def create_or_load_vector_db(profile="default"):
    """
    Create or load a vector database for the specified profile.
    
    Args:
        profile (str): User profile name
        
    Returns:
        VectorDB: Vector database instance
    """
    return VectorDB(profile=profile)

def add_to_vector_db(db, topic, content, source="", profile="default"):
    """
    Add content to the vector database.
    
    Args:
        db (VectorDB): Vector database instance
        topic (str): Topic or title of the content
        content (str): The actual content text
        source (str): Source of the content
        profile (str): User profile name
        
    Returns:
        int: ID of the added item
    """
    return db.add(topic, content, source)

def search_vector_db(db, query, top_k=5, exact_match=False):
    """
    Search the vector database for relevant content.
    
    Args:
        db (VectorDB): Vector database instance
        query (str): Search query
        top_k (int): Number of results to return
        exact_match (bool): If True, only return exact topic matches
        
    Returns:
        list: List of dictionaries with search results
    """
    if exact_match:
        return db.get_by_topic(query)
    else:
        return db.search(query, top_k=top_k)

def get_all_topics(db):
    """
    Get all topics in the database.
    
    Args:
        db (VectorDB): Vector database instance
        
    Returns:
        list: List of topic strings
    """
    return db.get_all_topics()
