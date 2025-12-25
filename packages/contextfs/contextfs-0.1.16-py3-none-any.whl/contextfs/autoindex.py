"""
Auto-indexing module for ContextFS.

DEPRECATED: This module has been moved to contextfs.indexing.
This file provides backward compatibility - import from contextfs.indexing instead.
"""

# Re-export everything from the new location for backward compatibility
from contextfs.indexing import (
    DEFAULT_IGNORE_PATTERNS,
    DEFAULT_INDEX_EXTENSIONS,
    FRAMEWORK_DETECTORS,
    LANGUAGE_DETECTORS,
    PROJECT_CONTAINER_NAMES,
    TYPE_INDICATORS,
    WORKSPACE_CONFIG_FILES,
    AutoIndexer,
    FrameworkDetector,
    IndexMode,
    IndexStatus,
    LanguageDetector,
    RepoInfo,
    TypeIndicator,
    create_codebase_summary,
    discover_git_repos,
)

__all__ = [
    # Core classes
    "AutoIndexer",
    "IndexMode",
    "IndexStatus",
    # Discovery
    "RepoInfo",
    "LanguageDetector",
    "FrameworkDetector",
    "TypeIndicator",
    "discover_git_repos",
    "create_codebase_summary",
    # Constants
    "DEFAULT_IGNORE_PATTERNS",
    "DEFAULT_INDEX_EXTENSIONS",
    "LANGUAGE_DETECTORS",
    "FRAMEWORK_DETECTORS",
    "TYPE_INDICATORS",
    "PROJECT_CONTAINER_NAMES",
    "WORKSPACE_CONFIG_FILES",
]
