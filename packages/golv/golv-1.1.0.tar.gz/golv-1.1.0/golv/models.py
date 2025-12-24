from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

class CommandSecurityLevel(str, Enum):
    """Niveaux de sécurité pour les commandes"""
    LOW = "low"      # Commandes basiques (echo, ls, cat)
    MEDIUM = "medium" # Développement (python, git, npm)
    HIGH = "high"    # Administration limitée
    AI = "ai"        # Mode spécial pour IA (toutes commandes sécurisées)

class VMType(str, Enum):
    """Types de VMs disponibles"""
    UBUNTU = "ubuntu"
    DEBIAN = "debian"
    PYTHON_DEV = "python-dev"
    NODEJS = "nodejs"
    DOCKER_HOST = "docker-host"
    WORDPRESS = "wordpress"

@dataclass
class VMConfig:
    """Configuration d'une VM"""
    vm_id: Optional[str] = None
    vm_type: VMType = VMType.UBUNTU
    version: str = "22.04 LTS"
    name: Optional[str] = None
    is_public: bool = False
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.name and self.vm_id:
            self.name = f"VM-{self.vm_id[:8]}"
@dataclass
class CommandRequest:
    """Représente une commande à envoyer"""
    command: str
    vm_id: Optional[str] = None
    timeout: int = 30
    working_dir: Optional[str] = None

@dataclass
class VMStatus:
    """Statut de la VM"""
    vm_id: str
    status: str
    uptime: Optional[str] = None
    ip_address: Optional[str] = None
@dataclass
class CommandResult:
    """Résultat d'exécution de commande"""
    success: bool
    stdout: str
    stderr: str
    return_code: int
    vm_id: str
    command: str
    duration_ms: int
    executed_at: str
    
    def __str__(self):
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return f"{status} [{self.duration_ms}ms] {self.command}\n{self.stdout}"
    
    @property
    def output(self):
        """Retourne la sortie principale"""
        return self.stdout if self.success else self.stderr

@dataclass
class AgentConfig:
    """Configuration de l'agent IA"""
    api_key: str
    vm_config: VMConfig
    timeout: int = 100
    use_command: bool = True
    security_level: CommandSecurityLevel = CommandSecurityLevel.AI
    allowed_commands: List[str] = field(default_factory=list)
    max_command_length: int = 500
    
    def __post_init__(self):
        # Commandes autorisées par niveau de sécurité
        self.allowed_commands = self._get_allowed_commands()
    
    def _get_allowed_commands(self) -> List[str]:
        """Retourne les commandes autorisées selon le niveau"""
        base_commands = ["pwd", "ls", "echo", "cat"]
        
        if self.security_level == CommandSecurityLevel.LOW:
            return base_commands
        
        dev_commands = base_commands + [
            "python3", "python", "pip", "node", "npm", "git",
            "mkdir", "touch", "find", "grep"
        ]
        
        if self.security_level == CommandSecurityLevel.MEDIUM:
            return dev_commands
        
        admin_commands = dev_commands + [
            "curl", "wget", "df", "du", "date",
            "whoami", "uname", "hostname"
        ]
        
        if self.security_level == CommandSecurityLevel.HIGH:
            return admin_commands
        
        # Mode AI - toutes les commandes sécurisées
        return admin_commands + [
            "cd", "head", "tail", "wc", "sort", "uniq"
        ]
