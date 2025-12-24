from typing import Optional, List, Dict, Any
from .client import GoLVClient
from .models import VMConfig, AgentConfig, CommandSecurityLevel, CommandResult
from .exceptions import SecurityError

class GoLVAgent:
    """Agent sécurisé pour l'exécution de commandes par IA"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = GoLVClient(api_key=config.api_key)
        
        # Initialiser ou créer la VM
        if config.vm_config.vm_id:
            self.vm_id = config.vm_config.vm_id
        else:
            self._create_vm()
    
    def _create_vm(self):
        """Créer une nouvelle VM selon la configuration"""
        vm_data = self.client.create_vm(self.config.vm_config)
        self.vm_id = vm_data.get("vm_id")
        print(f"✅ VM créée: {self.vm_id}")
    
    def _validate_command(self, command: str) -> bool:
        """Valider une commande pour la sécurité"""
        # Longueur maximale
        if len(command) > self.config.max_command_length:
            raise SecurityError(f"Commande trop longue ({len(command)} > {self.config.max_command_length})")
        
        # Commandes bannies
        banned_patterns = [
            "rm -rf", "shutdown", "reboot", "dd", "mkfs", 
            ":(){", "chmod 777", "> /dev/sda", "mkfifo"
        ]
        
        for banned in banned_patterns:
            if banned in command.lower():
                raise SecurityError(f"Commande bannie détectée: {banned}")
        
        # Vérifier si la commande est autorisée
        if self.config.use_command:
            first_word = command.split()[0] if command.split() else ""
            
            # Toujours autoriser echo et python
            if first_word in ["echo", "python", "python3"]:
                return True
            
            # Vérifier dans la liste des commandes autorisées
            if first_word not in self.config.allowed_commands:
                raise SecurityError(f"Commande non autorisée: {first_word}")
        
        return True
    
    def execute(self, command: str, timeout: Optional[int] = None) -> CommandResult:
        """Exécuter une commande de manière sécurisée"""
        try:
            # Validation de sécurité
            self._validate_command(command)
            
            # Exécution
            result = self.client.execute_command(
                vm_id=self.vm_id,
                command=command,
                timeout=timeout or self.config.timeout
            )
            
            # Journalisation
            self._log_execution(command, result)
            
            return result
            
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Erreur sécurité: {str(e)}",
                return_code=1,
                vm_id=self.vm_id,
                command=command,
                duration_ms=0,
                executed_at=""
            )
    
    def execute_safe(self, command: str) -> str:
        """Exécuter une commande et retourner seulement la sortie"""
        result = self.execute(command)
        return result.stdout if result.success else f"Erreur: {result.stderr}"
    
    def execute_python(self, code: str) -> CommandResult:
        """Exécuter du code Python"""
        # Échapper les guillemets
        escaped_code = code.replace('"', '\\"').replace("'", "\\'")
        command = f'python3 -c "{escaped_code}"'
        return self.execute(command)
    
    def execute_git(self, git_command: str) -> CommandResult:
        """Exécuter une commande Git"""
        if "git" not in self.config.allowed_commands:
            raise SecurityError("Commandes Git non autorisées")
        
        command = f"git {git_command}"
        return self.execute(command)
    
    def predefined(self, command_type: str) -> CommandResult:
        """Exécuter une commande pré-définie"""
        return self.client.execute_predefined(self.vm_id, command_type)
    
    def get_status(self) -> Dict[str, Any]:
        """Récupérer le statut de la VM"""
        return self.client.get_vm_status(self.vm_id)
    
    def _log_execution(self, command: str, result: CommandResult):
        """Journaliser l'exécution (peut être étendu)"""
        status = "✅" if result.success else "❌"
        print(f"{status} [{result.duration_ms}ms] {command[:50]}...")
    
    def interactive_session(self):
        """Session interactive pour débogage"""
        print(f"🔧 Session interactive GoLV Agent")
        print(f"VM ID: {self.vm_id}")
        print(f"Sécurité: {self.config.security_level.value}")
        print(f"Commandes autorisées: {len(self.config.allowed_commands)}")
        print("Tapez 'exit' pour quitter")
        print("-" * 50)
        
        while True:
            try:
                cmd = input(f"golv:{self.vm_id[:8]} $ ")
                if cmd.lower() in ['exit', 'quit', 'q']:
                    break
                if not cmd.strip():
                    continue
                
                result = self.execute(cmd)
                print(result.output)
                
            except KeyboardInterrupt:
                print("\nInterrompu")
                break
            except Exception as e:
                print(f"Erreur: {e}")
