"""
Système de plugins LScript.

Ce module fournit l'infrastructure pour créer
et charger des plugins qui étendent LScript.

Architecture open-core:
- Core gratuit: règles de base, UI standard
- Plugins premium: règles avancées, thèmes, analytics
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import sys

# Compatibilité Python < 3.10
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    try:
        from importlib_metadata import entry_points
    except ImportError:
        # Fallback si ni stdlib >= 3.10 ni importlib_metadata n'est présent
        # Dans ce cas, les plugins ne seront pas chargés
        def entry_points(group=None): return []

from lscript.explain.base import ErrorRule


@dataclass
class PluginInfo:
    """
    Métadonnées d'un plugin LScript.
    
    Attributes:
        id: Identifiant unique (ex: "lscript-pro-aws")
        name: Nom d'affichage (ex: "LScript Pro - AWS")
        version: Version du plugin
        description: Description courte
        author: Auteur du plugin
        homepage: URL de la page du plugin
        license: Type de licence ("MIT", "Proprietary")
        premium: True si plugin payant
        price: Prix en euros (si premium)
    """
    id: str
    name: str
    version: str
    description: str = ""
    author: str = ""
    homepage: str = ""
    license: str = "MIT"
    premium: bool = False
    price: float = 0.0
    tags: List[str] = field(default_factory=list)


class LScriptPlugin(ABC):
    """
    Interface de base pour les plugins LScript.
    
    Un plugin peut fournir:
    - Des règles d'erreurs supplémentaires
    - Des hooks sur le cycle de vie
    - Des commandes internes additionnelles
    
    Exemple d'implémentation:
    
        class AWSPlugin(LScriptPlugin):
            def get_info(self) -> PluginInfo:
                return PluginInfo(
                    id="lscript-aws",
                    name="LScript AWS",
                    version="1.0.0",
                    description="Règles pour AWS CLI",
                    premium=True,
                    price=9.99,
                )
            
            def get_rules(self) -> List[ErrorRule]:
                return [AWSCredentialsRule(), S3BucketRule(), ...]
    """
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Retourne les métadonnées du plugin."""
        pass
    
    @abstractmethod
    def get_rules(self) -> List[ErrorRule]:
        """Retourne les règles d'erreurs fournies par ce plugin."""
        pass
    
    def on_load(self) -> None:
        """Hook appelé quand le plugin est chargé."""
        pass
    
    def on_unload(self) -> None:
        """Hook appelé quand le plugin est déchargé."""
        pass
    
    def validate_license(self, license_key: str) -> bool:
        """
        Valide une clé de licence (pour plugins premium).
        
        À implémenter par les plugins premium.
        Retourne True par défaut (plugins gratuits).
        """
        return True


class PluginManager:
    """
    Gestionnaire de plugins LScript.
    
    Fonctionnalités:
    - Chargement/déchargement de plugins
    - Validation des licences premium
    - Collecte des règles de tous les plugins
    
    Usage:
        manager = PluginManager()
        manager.register(MyPlugin())
        rules = manager.get_all_rules()
    """
    
    def __init__(self):
        self._plugins: Dict[str, LScriptPlugin] = {}
        self._licenses: Dict[str, str] = {}  # plugin_id -> license_key
    
    def register(self, plugin: LScriptPlugin) -> bool:
        """
        Enregistre un plugin.
        
        Args:
            plugin: Le plugin à enregistrer
            
        Returns:
            True si le plugin a été enregistré avec succès
        """
        info = plugin.get_info()
        
        # Vérifie si déjà enregistré
        if info.id in self._plugins:
            return False
        
        # Valide la licence si premium
        if info.premium:
            license_key = self._licenses.get(info.id, "")
            if not plugin.validate_license(license_key):
                return False
        
        # Charge le plugin
        plugin.on_load()
        self._plugins[info.id] = plugin
        return True
    
    def unregister(self, plugin_id: str) -> bool:
        """
        Désenregistre un plugin.
        
        Args:
            plugin_id: L'ID du plugin à retirer
            
        Returns:
            True si le plugin a été retiré
        """
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        plugin.on_unload()
        del self._plugins[plugin_id]
        return True
    
    def set_license(self, plugin_id: str, license_key: str) -> None:
        """
        Définit une clé de licence pour un plugin.
        
        Args:
            plugin_id: L'ID du plugin
            license_key: La clé de licence
        """
        self._licenses[plugin_id] = license_key
    
    def load_installed_plugins(self) -> None:
        """
        Découvre et charge les plugins installés via les entry points.
        
        Recherche le groupe 'lscript.plugins'.
        """
        discovered = entry_points(group='lscript.plugins')
        for ep in discovered:
            try:
                # Instancie le plugin
                plugin_class = ep.load()
                plugin = plugin_class()
                
                # Tente de l'enregistrer
                if self.register(plugin):
                    # Si c'est un plugin premium, l'activation est gérée à l'enregistrement
                    # (via validate_license qui est appelée dans register)
                    pass
            except Exception as e:
                # On ne veut pas casser le shell si un plugin foireux est installé
                print(f"Erreur chargement plugin {ep.name}: {e}")
    
    def get_all_rules(self) -> List[ErrorRule]:
        """
        Collecte toutes les règles de tous les plugins.
        
        Returns:
            Liste combinée de toutes les règles
        """
        rules = []
        for plugin in self._plugins.values():
            rules.extend(plugin.get_rules())
        return rules
    
    def get_plugin(self, plugin_id: str) -> Optional[LScriptPlugin]:
        """Récupère un plugin par son ID."""
        return self._plugins.get(plugin_id)
    
    def list_plugins(self) -> List[PluginInfo]:
        """Liste les informations de tous les plugins chargés."""
        return [p.get_info() for p in self._plugins.values()]
    
    @property
    def plugin_count(self) -> int:
        """Nombre de plugins chargés."""
        return len(self._plugins)


# =============================================================================
# EXEMPLE DE PLUGIN PREMIUM (pour documentation)
# =============================================================================

class ExamplePremiumPlugin(LScriptPlugin):
    """
    Exemple de plugin premium pour démonstration.
    
    Ce plugin n'est pas actif par défaut.
    Il montre comment structurer un plugin payant.
    """
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            id="lscript-pro-example",
            name="LScript Pro Example",
            version="1.0.0",
            description="Exemple de plugin premium",
            author="LScript Team",
            homepage="https://lscript.fr/plugins/example",
            license="Proprietary",
            premium=True,
            price=9.99,
            tags=["example", "demo"],
        )
    
    def get_rules(self) -> List[ErrorRule]:
        # Les règles premium seraient définies ici
        return []
    
    def validate_license(self, license_key: str) -> bool:
        # Logique de validation de licence
        # En production: vérification serveur, signature, etc.
        return license_key.startswith("LSCRIPT-PRO-")
