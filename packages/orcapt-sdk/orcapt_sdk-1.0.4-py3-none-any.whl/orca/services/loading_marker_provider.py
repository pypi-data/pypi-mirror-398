"""
Loading Marker Provider Service
================================

Provides loading markers and aliases for UI feedback.
Follows Single Responsibility Principle (SRP).
"""

import logging
from typing import Dict, Optional
from ..domain.interfaces import ILoadingMarkerProvider
from ..config import LoadingKind, LOADING_MARKERS

logger = logging.getLogger(__name__)


class LoadingMarkerProvider(ILoadingMarkerProvider):
    """
    Provides standardized loading markers for various UI states.
    
    Responsibilities:
    - Generate loading markers (start/end)
    - Map semantic aliases to markers
    - Validate loading marker kinds
    
    Uses centralized configuration from config module.
    """
    
    SUPPORTED_KINDS = tuple(kind.value for kind in LoadingKind)
    DEFAULT_KIND = LoadingKind.THINKING.value
    
    def __init__(self):
        self._aliases: Dict[str, str] = self._build_aliases()
        logger.debug(f"LoadingMarkerProvider initialized with {len(self._aliases)} aliases")
    
    def get_marker(self, kind: str, action: str) -> str:
        """
        Get loading marker for given kind and action.
        
        Args:
            kind: Type of loading (general, image, video, card, thinking, etc.)
            action: Action type (start or end)
            
        Returns:
            Formatted loading marker string
            - For "general": [orca.loading.start] (no kind)
            - For others: [orca.loading.{kind}.start] (with kind)
        """
        kind_norm = self._normalize_kind(kind)
        action_norm = "start" if action == "start" else "end"
        
        # Special case: "general" uses format without kind (matching Orca Components)
        if kind_norm == LoadingKind.GENERAL.value:
            marker = f"[orca.loading.{action_norm}]\n\n"
        else:
            marker = f"[orca.loading.{kind_norm}.{action_norm}]\n\n"
        
        logger.debug(f"Generated marker: {marker.strip()}")
        return marker
    
    def get_marker_by_alias(self, alias: str) -> Optional[str]:
        """
        Get loading marker by semantic alias.
        
        Args:
            alias: Semantic alias (e.g., 'show image load')
            
        Returns:
            Loading marker string or None if alias not found
        """
        normalized_alias = alias.strip().lower()
        marker = self._aliases.get(normalized_alias)
        
        if marker:
            logger.debug(f"Resolved alias '{alias}' to marker")
        else:
            logger.debug(f"No marker found for alias '{alias}'")
        
        return marker
    
    def _normalize_kind(self, kind: str) -> str:
        """
        Normalize and validate loading kind.
        
        Args:
            kind: Kind of loading marker
            
        Returns:
            Normalized kind (defaults to 'thinking' if invalid)
        """
        kind_norm = (kind or '').strip().lower()
        
        if kind_norm not in self.SUPPORTED_KINDS:
            logger.debug(f"Unknown kind '{kind}', defaulting to '{self.DEFAULT_KIND}'")
            return self.DEFAULT_KIND
        
        return kind_norm
    
    def _build_aliases(self) -> Dict[str, str]:
        """
        Build semantic alias mapping.
        
        Returns:
            Dict mapping aliases to marker strings
        """
        aliases = {}
        
        for kind in self.SUPPORTED_KINDS:
            # Special format for "general" (no kind in marker, matching Orca Components)
            if kind == LoadingKind.GENERAL.value:
                # Start aliases
                aliases[f'show {kind} load'] = f"[orca.loading.start]\n\n"
                aliases[f'start {kind} load'] = f"[orca.loading.start]\n\n"
                aliases['show load'] = f"[orca.loading.start]\n\n"
                aliases['start load'] = f"[orca.loading.start]\n\n"
                
                # End aliases
                aliases[f'end {kind} load'] = f"[orca.loading.end]\n\n"
                aliases[f'hide {kind} load'] = f"[orca.loading.end]\n\n"
                aliases[f'stop {kind} load'] = f"[orca.loading.end]\n\n"
                aliases['end load'] = f"[orca.loading.end]\n\n"
                aliases['hide load'] = f"[orca.loading.end]\n\n"
                aliases['stop load'] = f"[orca.loading.end]\n\n"
            else:
                # Start aliases (with kind)
                aliases[f'show {kind} load'] = f"[orca.loading.{kind}.start]\n\n"
                aliases[f'start {kind} load'] = f"[orca.loading.{kind}.start]\n\n"
                
                # End aliases (with kind)
                aliases[f'end {kind} load'] = f"[orca.loading.{kind}.end]\n\n"
                aliases[f'hide {kind} load'] = f"[orca.loading.{kind}.end]\n\n"
                aliases[f'stop {kind} load'] = f"[orca.loading.{kind}.end]\n\n"
        
        return aliases
    
    def get_supported_kinds(self) -> tuple:
        """
        Get list of supported loading kinds.
        
        Returns:
            Tuple of supported kinds
        """
        return self.SUPPORTED_KINDS
    
    def get_aliases(self) -> Dict[str, str]:
        """
        Get all available aliases.
        
        Returns:
            Dict of all semantic aliases
        """
        return self._aliases.copy()

