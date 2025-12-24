from typing import Optional
from .client import GoLVClient
from .models import VMConfig, VMType, AgentConfig
from .agent import GoLVAgent
from .exceptions import GoLVError, AuthError, VMNotFoundError, SecurityError

class GoLVSetup:
    """
    Point d'entrée principal du SDK GoLV.
    Permet :
    - Authentification
    - Création de VMConfig
    - Création d'un agent IA
    - Accès au client API
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://golv.onrender.com",
    ):
        self.base_url = base_url
        self.api_key = api_key

        # Client API interne
        self.client = GoLVClient(
            base_url=self.base_url,
            api_key=self.api_key
        )

    # ---------- AUTHENTIFICATION ----------

    def login(self, username: str, password: str) -> str:
        """
        Authentifie l'utilisateur et stocke la clé API.
        """
        token = self.client.authenticate(username, password)
        self.api_key = token
        return token

    # ---------- CONFIGURATION VM ----------

    def create_vm_config(
        self,
        name: Optional[str] = None,
        vm_type: VMType = VMType.UBUNTU,
        version: str = "22.04 LTS",
        is_public: bool = False,
    ) -> VMConfig:
        """
        Crée une configuration de VM prête à l'emploi.
        """
        return VMConfig(
            name=name,
            vm_type=vm_type,
            version=version,
            is_public=is_public
        )

    def create_default_vm(self, name: Optional[str] = None) -> VMConfig:
        """
        Crée une VM Ubuntu par défaut.
        """
        return self.create_vm_config(name=name)

    # ---------- CREATION AGENT ----------

    def create_agent(
        self,
        vm_config: Optional[VMConfig] = None,
        allowed_commands: Optional[list[str]] = None,
        max_command_length: int = 200,
        timeout: int = 30,
        security_level=None,
        api_key: Optional[str] = None
    ) -> GoLVAgent:
        """
        Crée un agent GoLV sécurisé.
        """
        agent_config = AgentConfig(
            vm_config=vm_config or self.create_default_vm(),
            allowed_commands=allowed_commands or [],
            max_command_length=max_command_length,
            timeout=timeout,
            security_level=security_level,
            api_key=api_key or self.api_key
        )
        return GoLVAgent(config=agent_config)

    # ---------- ACCÈS AU CLIENT ----------

    def get_client(self) -> GoLVClient:
        """
        Retourne le client API configuré.
        """
        return self.client

    def __repr__(self) -> str:
        auth_state = "authenticated" if self.api_key else "unauthenticated"
        return f"<GoLVSetup base_url={self.base_url!r} state={auth_state}>"
