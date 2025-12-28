"""
Module d'explication d'erreurs LScript.

Ce module fournit le système de règles pour analyser
les erreurs et générer des explications humaines.
"""

from lscript.explain.base import ErrorRule, Explanation
from lscript.explain.rules import (
    RuleRegistry,
    create_default_registry,
    # Règles génériques
    CommandNotFoundRule,
    PermissionDeniedRule,
    FileNotFoundRule,
    SyntaxErrorRule,
    # npm
    NpmNotFoundRule,
    NpmInstallErrorRule,
    # git
    GitNotFoundRule,
    GitNotRepoRule,
    GitMergeConflictRule,
    GitPushRejectedRule,
    # python
    PythonNotFoundRule,
    PythonModuleNotFoundRule,
    PythonSyntaxErrorRule,
    # docker
    DockerNotFoundRule,
    DockerDaemonNotRunningRule,
    # réseau
    NetworkUnreachableRule,
    PortInUseRule,
    # disque
    DiskFullRule,
    # fallback
    FallbackRule,
)

__all__ = [
    # Base
    "ErrorRule",
    "Explanation",
    "RuleRegistry",
    "create_default_registry",
    # Règles
    "CommandNotFoundRule",
    "PermissionDeniedRule",
    "FileNotFoundRule",
    "SyntaxErrorRule",
    "NpmNotFoundRule",
    "NpmInstallErrorRule",
    "GitNotFoundRule",
    "GitNotRepoRule",
    "GitMergeConflictRule",
    "GitPushRejectedRule",
    "PythonNotFoundRule",
    "PythonModuleNotFoundRule",
    "PythonSyntaxErrorRule",
    "DockerNotFoundRule",
    "DockerDaemonNotRunningRule",
    "NetworkUnreachableRule",
    "PortInUseRule",
    "DiskFullRule",
    "FallbackRule",
]
