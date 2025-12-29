"""
Gestion des notifications (logs ou alertes)
"""

class NotificationService:
    """
    Service pour envoyer des notifications simples
    """

    def __init__(self):
        self._log: list[str] = []

    def notify(self, message: str):
        """
        Enregistre et affiche la notification
        """
        self._log.append(message)
        print(f"[NOTIFICATION] {message}\n")

    def get_log(self) -> list[str]:
        """
        Retourne l'historique des notifications
        """
        return self._log
