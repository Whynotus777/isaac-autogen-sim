"""
Pipeline orchestration for the autonomous simulation platform.

Phase 1: Sequential workflow (JSON → SceneGraph → Physics → USD)
Phase 3: Optimization loop (USD → Simulate → Gradients → Optimize → Repeat)
"""

from .phase1_pipeline import Phase1Pipeline
from .phase3_pipeline import Phase3Pipeline

__all__ = ["Phase1Pipeline", "Phase3Pipeline"]
