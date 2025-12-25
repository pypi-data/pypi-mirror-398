"""
#exonware/xwlazy/src/exonware/xwlazy/loading/adaptive_utils.py

Adaptive learning utilities for pattern-based optimization.

Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com

Generation Date: 19-Nov-2025

This module provides adaptive learning for ADAPTIVE mode.
"""

import time
import threading
from typing import Optional
from collections import defaultdict, deque

# Logger not used in this module, removed to avoid circular dependency

class AdaptiveLearner:
    """Learns import patterns and optimizes loading strategy."""
    
    def __init__(self, learning_window: int = 100, prediction_depth: int = 3):
        """
        Initialize adaptive learner.
        
        Args:
            learning_window: Number of imports to track for learning
            prediction_depth: Depth of sequence predictions
        """
        self._learning_window = learning_window
        self._prediction_depth = prediction_depth
        self._import_sequences: deque = deque(maxlen=learning_window)
        self._access_times: dict[str, list[float]] = defaultdict(list)
        self._import_chains: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._module_scores: dict[str, float] = {}
        self._lock = threading.RLock()
    
    def record_import(self, module_name: str, import_time: float) -> None:
        """Record an import event."""
        current_time = time.time()
        
        # Lock-free append to deque (thread-safe for appends)
        self._import_sequences.append((module_name, current_time, import_time))
        
        with self._lock:
            self._access_times[module_name].append(current_time)
            
            # Update import chains (what imports after what)
            if len(self._import_sequences) > 1:
                prev_name, _, _ = self._import_sequences[-2]
                self._import_chains[prev_name][module_name] += 1
            
            # Update module score (frequency * recency) - defer heavy computation
            if len(self._access_times[module_name]) % 5 == 0:  # Update every 5th access
                self._update_module_score(module_name)
    
    def _update_module_score(self, module_name: str) -> None:
        """Update module priority score."""
        with self._lock:
            accesses = self._access_times[module_name]
            if not accesses:
                return
            
            # Frequency component
            recent_accesses = [t for t in accesses if time.time() - t < 3600]  # Last hour
            frequency = len(recent_accesses)
            
            # Recency component (more recent = higher score)
            if accesses:
                last_access = accesses[-1]
                recency = 1.0 / (time.time() - last_access + 1.0)
            else:
                recency = 0.0
            
            # Chain component (if often imported after another module)
            chain_weight = sum(self._import_chains.get(prev, {}).get(module_name, 0) 
                             for prev in self._access_times.keys()) / max(len(self._import_sequences), 1)
            
            # Combined score
            self._module_scores[module_name] = frequency * 0.4 + recency * 1000 * 0.4 + chain_weight * 0.2
    
    def predict_next_imports(self, current_module: Optional[str] = None, limit: int = 5) -> list[str]:
        """Predict likely next imports based on patterns."""
        # Lock-free check first
        if not self._import_sequences:
            return []
        
        with self._lock:
            candidates: dict[str, float] = {}
            
            # Predict based on current module chain (lock-free read of dict)
            if current_module:
                chain_candidates = self._import_chains.get(current_module, {})
                for module, count in chain_candidates.items():
                    candidates[module] = candidates.get(module, 0.0) + count * 2.0
            
            # Add high-scoring modules (lock-free read of dict)
            for module, score in self._module_scores.items():
                candidates[module] = candidates.get(module, 0.0) + score * 0.5
            
            # Sort by score
            sorted_candidates = sorted(candidates.items(), key=lambda x: x[1], reverse=True)
            return [module for module, _ in sorted_candidates[:limit]]
    
    def get_priority_modules(self, limit: int = 10) -> list[str]:
        """Get modules that should be preloaded based on scores."""
        with self._lock:
            sorted_modules = sorted(
                self._module_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return [module for module, _ in sorted_modules[:limit]]
    
    def get_stats(self) -> Dict:
        """Get learning statistics."""
        with self._lock:
            return {
                'sequences_tracked': len(self._import_sequences),
                'unique_modules': len(self._access_times),
                'chains_tracked': sum(len(chains) for chains in self._import_chains.values()),
                'top_modules': self.get_priority_modules(5),
            }

__all__ = ['AdaptiveLearner']

