import requests
import json
from typing import Optional, Dict, Any, List
from .models import VMConfig, CommandResult
from .exceptions import GoLVError, AuthError, VMNotFoundError

class GoLVClient:
    """Client pour l'API GoLV"""
    
    def __init__(self, base_url: str = "https://golv.onrender.com", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            })
    
    def authenticate(self, username: str, password: str) -> str:
        """Authentification et récupération du token"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json={"username": username, "password": password}
            )
            response.raise_for_status()
            data = response.json()
            self.api_key = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            return self.api_key
        except requests.exceptions.RequestException as e:
            raise AuthError(f"Erreur d'authentification: {e}")
    
    def create_vm(self, config: VMConfig) -> Dict[str, Any]:
        """Créer une nouvelle VM"""
        try:
            payload = {
                "name": config.name or f"VM-{config.vm_type}",
                "vm_type": config.vm_type.value,
                "version": config.version,
                "is_public": config.is_public,
                "tags": config.tags
            }
            
            response = self.session.post(
                f"{self.base_url}/api/vms",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise GoLVError(f"Erreur création VM: {e}")
    
    def execute_command(self, vm_id: str, command: str, 
                       timeout: int = 30, working_dir: Optional[str] = None) -> CommandResult:
        """Exécuter une commande dans une VM"""
        try:
            payload = {
                "command": command,
                "timeout": timeout
            }
            
            if working_dir:
                payload["working_dir"] = working_dir
            
            response = self.session.post(
                f"{self.base_url}/api/vms/{vm_id}/execute",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                cmd_data = data["data"]
                return CommandResult(
                    success=cmd_data["success"],
                    stdout=cmd_data["stdout"],
                    stderr=cmd_data["stderr"],
                    return_code=cmd_data.get("return_code", 0),
                    vm_id=vm_id,
                    command=command,
                    duration_ms=cmd_data["duration_ms"],
                    executed_at=cmd_data["executed_at"]
                )
            else:
                raise GoLVError(f"Échec exécution: {data}")
                
        except requests.exceptions.RequestException as e:
            if e.response and e.response.status_code == 404:
                raise VMNotFoundError(f"VM {vm_id} non trouvée")
            raise GoLVError(f"Erreur exécution commande: {e}")
    
    def execute_predefined(self, vm_id: str, command_type: str) -> CommandResult:
        """Exécuter une commande pré-définie"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/vms/{vm_id}/execute/predefined",
                json=command_type
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("success"):
                cmd_data = data["data"]
                return CommandResult(
                    success=cmd_data["success"],
                    stdout=cmd_data["stdout"],
                    stderr=cmd_data["stderr"],
                    return_code=cmd_data.get("return_code", 0),
                    vm_id=vm_id,
                    command=f"Predefined: {command_type}",
                    duration_ms=cmd_data["duration_ms"],
                    executed_at=cmd_data["executed_at"]
                )
            else:
                raise GoLVError(f"Échec commande pré-définie: {data}")
                
        except requests.exceptions.RequestException as e:
            raise GoLVError(f"Erreur commande pré-définie: {e}")
    
    def get_vm_status(self, vm_id: str) -> Dict[str, Any]:
        """Récupérer le statut d'une VM"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/vms/{vm_id}/status"
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise GoLVError(f"Erreur statut VM: {e}")
    
    def list_vms(self, public_only: bool = False) -> List[Dict[str, Any]]:
        """Lister les VMs"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/vms",
                params={"public_only": public_only}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except requests.exceptions.RequestException as e:
            raise GoLVError(f"Erreur liste VMs: {e}")
    
    def generate_api_key(self, name: str, expires_in: int = 30) -> str:
        """Générer une nouvelle clé API"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/api-key/generate",
                json={"name": name, "expires_in": expires_in}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("api_key", "")
        except requests.exceptions.RequestException as e:
            raise GoLVError(f"Erreur génération clé API: {e}")
