class GoLVError(Exception):
    """Exception de base pour GoLV"""
    pass

class AuthError(GoLVError):
    """Erreur d'authentification"""
    pass

class VMNotFoundError(GoLVError):
    """VM non trouvée"""
    pass

class SecurityError(GoLVError):
    """Erreur de sécurité"""
    pass

class CommandTimeoutError(GoLVError):
    """Timeout de commande"""
    pass
