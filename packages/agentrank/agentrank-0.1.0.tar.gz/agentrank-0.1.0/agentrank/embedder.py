"""
AgentRank Embedding Model

The first embedding model specialized for AI agent memory retrieval.

Novel features:
1. Temporal position embeddings (when memory was created)
2. Memory type embeddings (episodic/semantic/procedural)
3. Importance prediction head (auxiliary task)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import AutoModel, AutoTokenizer
from typing import Dict, List, Optional


class AgentRankEmbedder(nn.Module):
    """
    AgentRank Embedding Model
    
    Novel features vs generic embedders:
    1. Temporal position embeddings - understands when memory was created
    2. Memory type embeddings - distinguishes episodic/semantic/procedural
    3. Importance prediction head - predicts memory importance (auxiliary task)
    """
    
    def __init__(
        self,
        model_name: str = "answerdotai/ModernBERT-base",
        pooling: str = "cls",
        temporal_buckets: int = 10,
        memory_types: int = 4,
        hidden_dim: Optional[int] = None,
    ):
        """
        Initialize AgentRank embedder.
        
        Args:
            model_name: Base model to use (e.g., ModernBERT, MiniLM)
            pooling: Pooling strategy ('cls' or 'mean')
            temporal_buckets: Number of temporal embedding buckets
            memory_types: Number of memory type embeddings
            hidden_dim: Override hidden dimension (auto-detected if None)
        """
        super().__init__()
        
        self.encoder = AutoModel.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.pooling = pooling
        
        # Auto-detect hidden dimension from encoder
        if hidden_dim is None:
            hidden_dim = self.encoder.config.hidden_size
        self.hidden_dim = hidden_dim
        
        # Novel: Temporal embeddings
        # Buckets: 0-1 day, 1-3 days, 3-7 days, 7-30 days, 30-90 days, etc.
        self.temporal_embeddings = nn.Embedding(
            num_embeddings=temporal_buckets,
            embedding_dim=hidden_dim
        )
        
        # Novel: Memory type embeddings
        # Types: episodic=0, semantic=1, procedural=2, unknown=3
        self.memory_type_embeddings = nn.Embedding(
            num_embeddings=memory_types,
            embedding_dim=hidden_dim
        )
        
        # Novel: Importance prediction head (auxiliary task)
        # Predicts importance score 0-1 for each memory
        self.importance_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid()
        )
        
        # Projection layer for final embeddings
        self.projection = nn.Linear(hidden_dim, hidden_dim)
        
        # Memory type mapping
        self.memory_type_map = {
            "episodic": 0,
            "semantic": 1,
            "procedural": 2,
            "unknown": 3,
        }
    
    def get_temporal_bucket(self, days_ago: int) -> int:
        """Map days ago to temporal bucket ID."""
        if days_ago <= 1:
            return 0  # Today/yesterday
        elif days_ago <= 3:
            return 1  # Last few days
        elif days_ago <= 7:
            return 2  # This week
        elif days_ago <= 14:
            return 3  # Last 2 weeks
        elif days_ago <= 30:
            return 4  # This month
        elif days_ago <= 60:
            return 5  # Last 2 months
        elif days_ago <= 90:
            return 6  # Last quarter
        elif days_ago <= 180:
            return 7  # Last 6 months
        elif days_ago <= 365:
            return 8  # Last year
        else:
            return 9  # Older
    
    def get_memory_type_id(self, memory_type: str) -> int:
        """Map memory type string to ID."""
        return self.memory_type_map.get(memory_type, 3)
    
    def pool(
        self, 
        hidden_states: torch.Tensor, 
        attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """Pool hidden states to get sentence embedding."""
        if self.pooling == "cls":
            return hidden_states[:, 0]
        elif self.pooling == "mean":
            # Mean pooling with attention mask
            mask = attention_mask.unsqueeze(-1).expand(hidden_states.size()).float()
            sum_embeddings = torch.sum(hidden_states * mask, dim=1)
            sum_mask = torch.clamp(mask.sum(dim=1), min=1e-9)
            return sum_embeddings / sum_mask
        else:
            raise ValueError(f"Unknown pooling strategy: {self.pooling}")
    
    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        temporal_bucket: Optional[torch.Tensor] = None,
        memory_type: Optional[torch.Tensor] = None,
        return_importance: bool = False,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            input_ids: Token IDs [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            temporal_bucket: Optional temporal bucket IDs [batch_size]
            memory_type: Optional memory type IDs [batch_size]
            return_importance: Whether to also return importance predictions
            
        Returns:
            Dictionary with:
            - embeddings: [batch_size, hidden_dim]
            - importance: [batch_size, 1] (if return_importance=True)
        """
        # Get base embeddings from encoder
        outputs = self.encoder(input_ids, attention_mask=attention_mask)
        hidden_states = outputs.last_hidden_state
        
        # Pool to sentence embedding
        pooled = self.pool(hidden_states, attention_mask)
        
        # Add temporal information if provided
        # We use a small coefficient to not overwhelm the base representation
        if temporal_bucket is not None:
            temporal_emb = self.temporal_embeddings(temporal_bucket)
            pooled = pooled + 0.1 * temporal_emb
        
        # Add memory type information if provided
        if memory_type is not None:
            type_emb = self.memory_type_embeddings(memory_type)
            pooled = pooled + 0.1 * type_emb
        
        # Project
        embeddings = self.projection(pooled)
        
        # L2 normalize for cosine similarity
        embeddings = F.normalize(embeddings, p=2, dim=-1)
        
        result = {"embeddings": embeddings}
        
        # Predict importance if requested (auxiliary task)
        if return_importance:
            importance = self.importance_head(pooled)
            result["importance"] = importance
        
        return result
    
    def encode(
        self,
        texts: List[str],
        temporal_info: Optional[List[int]] = None,
        memory_types: Optional[List[str]] = None,
        batch_size: int = 32,
        show_progress: bool = True,
        max_length: int = 512,
    ) -> torch.Tensor:
        """
        Encode texts to embeddings (inference mode).
        
        Args:
            texts: List of texts to encode
            temporal_info: Optional list of days_ago values for each text
            memory_types: Optional list of memory type strings
            batch_size: Batch size for encoding
            show_progress: Whether to show progress bar
            max_length: Maximum sequence length
            
        Returns:
            Embeddings tensor [n_texts, hidden_dim]
        """
        self.eval()
        all_embeddings = []
        
        # Convert temporal info and memory types to IDs
        temporal_buckets = None
        if temporal_info is not None:
            temporal_buckets = [self.get_temporal_bucket(d) for d in temporal_info]
        
        memory_type_ids = None
        if memory_types is not None:
            memory_type_ids = [self.get_memory_type_id(t) for t in memory_types]
        
        iterator = range(0, len(texts), batch_size)
        if show_progress:
            try:
                from tqdm import tqdm
                iterator = tqdm(iterator, desc="Encoding")
            except ImportError:
                pass
        
        device = next(self.parameters()).device
        
        with torch.no_grad():
            for i in iterator:
                batch_texts = texts[i:i + batch_size]
                
                # Tokenize
                encoded = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=max_length,
                    return_tensors="pt"
                )
                
                input_ids = encoded["input_ids"].to(device)
                attention_mask = encoded["attention_mask"].to(device)
                
                # Get temporal and type tensors if provided
                temporal = None
                mtype = None
                
                if temporal_buckets is not None:
                    batch_temporal = temporal_buckets[i:i + batch_size]
                    temporal = torch.tensor(batch_temporal, device=device)
                
                if memory_type_ids is not None:
                    batch_types = memory_type_ids[i:i + batch_size]
                    mtype = torch.tensor(batch_types, device=device)
                
                # Encode
                outputs = self(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    temporal_bucket=temporal,
                    memory_type=mtype,
                )
                
                all_embeddings.append(outputs["embeddings"].cpu())
        
        return torch.cat(all_embeddings, dim=0)
    
    def save_pretrained(self, path: str):
        """Save model to directory."""
        import os
        os.makedirs(path, exist_ok=True)
        
        # Save encoder
        self.encoder.save_pretrained(path)
        self.tokenizer.save_pretrained(path)
        
        # Save custom components
        torch.save({
            "temporal_embeddings": self.temporal_embeddings.state_dict(),
            "memory_type_embeddings": self.memory_type_embeddings.state_dict(),
            "importance_head": self.importance_head.state_dict(),
            "projection": self.projection.state_dict(),
            "config": {
                "pooling": self.pooling,
                "hidden_dim": self.hidden_dim,
            }
        }, os.path.join(path, "agentrank_components.pt"))
    
    @classmethod
    def from_pretrained(cls, path: str, **kwargs):
        """Load model from directory."""
        import os
        
        # Load config
        components = torch.load(os.path.join(path, "agentrank_components.pt"))
        config = components["config"]
        
        # Create model
        model = cls(
            model_name=path,
            pooling=config["pooling"],
            hidden_dim=config["hidden_dim"],
            **kwargs
        )
        
        # Load custom components
        model.temporal_embeddings.load_state_dict(components["temporal_embeddings"])
        model.memory_type_embeddings.load_state_dict(components["memory_type_embeddings"])
        model.importance_head.load_state_dict(components["importance_head"])
        model.projection.load_state_dict(components["projection"])
        
        return model


# Factory functions for different model sizes
def agentrank_small():
    """Create AgentRank-Small (33M params, MiniLM base)."""
    return AgentRankEmbedder(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        pooling="mean",
        hidden_dim=384,
    )


def agentrank_base():
    """Create AgentRank-Base (110M params, ModernBERT base)."""
    return AgentRankEmbedder(
        model_name="answerdotai/ModernBERT-base",
        pooling="cls",
        hidden_dim=768,
    )
