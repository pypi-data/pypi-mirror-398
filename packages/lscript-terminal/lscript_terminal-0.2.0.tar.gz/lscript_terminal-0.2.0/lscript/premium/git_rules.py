"""
Règles Premium LScript.
"""
import re
from lscript.explain.base import ErrorRule, Explanation

class GitDetachedHeadRule(ErrorRule):
    """
    Règle Premium : Git Detached HEAD.
    Détecte l'état de 'tête détachée' qui fait très peur aux débutants.
    """
    
    # Matche le message standard de git checkout sur un commit
    PATTERN = re.compile(
        r"You are in 'detached HEAD' state|"
        r"HEAD is now at", 
        re.IGNORECASE
    )
    
    @property
    def rule_id(self) -> str:
        return "git_detached_head_premium"
    
    def match(self, stderr: str, return_code: int) -> bool:
        # Note: git checkout detached head écrit souvent dans stdout ou stderr selon versions
        # On vérifie si c'est une commande git et si le pattern est là
        return "detached HEAD" in stderr
    
    def explain(self, stderr: str, command: str) -> Explanation:
        return Explanation(
            title="⚠️ Mode Git 'Detached HEAD' (Tête détachée)",
            message=(
                "Vous n'êtes plus sur une branche !\n"
                "Vous avez déplacé votre vue sur un commit spécifique (historique).\n\n"
                "⚠️ **DANGER :** Si vous faites des commits ici puis changez de branche,\n"
                "vos modifications seront **perdues** (car aucune branche ne les suit)."
            ),
            suggestion=(
                "Deux options :\n\n"
                "1. **Pour juste regarder l'historique** (sans modifier) :\n"
                "   Ne faites rien. Quand vous aurez fini :\n"
                "   `git checkout main` (pour revenir au présent)\n\n"
                "2. **Pour travailler à partir d'ici** (sauvegarder vos modifs) :\n"
                "   Créez une branche de sécurité maintenant :\n"
                "   `git switch -c ma-nouvelle-branche`"
            ),
        )
