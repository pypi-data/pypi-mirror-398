"""
Configuration management for AI Project OS MCP Server.
"""

import os
import yaml

class Config:
    """
    MCP Server Configuration
    """
    
    def __init__(self):
        self.project_root = os.getenv("MCP_PROJECT_ROOT", ".")
        self.config_path = os.getenv("MCP_CONFIG_PATH", "config.yaml")
        self.policy_path = os.getenv("MCP_POLICY_PATH", "policy.yaml")
        self.log_level = os.getenv("MCP_LOG_LEVEL", "INFO")
        self.environment = os.getenv("MCP_ENVIRONMENT", "development")
        
        # Load defaults
        self.name = "ai-project-os-mcp"
        self.version = "0.1"
        self.rules = {
            "R1": "AI MUST query current stage before any action",
            "R2": "AI MUST NOT generate code unless stage == S5",
            "R3": "AI MUST abort on architecture violation",
            "R4": "AI MUST submit audit for every S5 task",
            "R5": "AI MUST respect src guard and lock status"
        }
        self.violation_policy = "hard_refusal"
        self.audit_required_stage = "S5"
        
        # Dependency Guard
        self.dependency_whitelist = []
        self.dependency_blacklist = []
        
        # Policy Configuration
        self.policies = {
            "dependency_governance": {
                "enabled": True,
                "max_violations": 0,
                "allowed_sources": ["pypi", "conda-forge"]
            },
            "audit_policy": {
                "required_fields": ["sub_task_id", "layer", "files_changed", "correctness_assertion", "architecture_compliance", "reviewer"],
                "retention_days": 365,
                "auto_approval": False
            },
            "architecture_compliance": {
                "enabled": True,
                "max_violations": 0,
                "allowed_layer_dependencies": {
                    "core": [],
                    "tools": ["core"],
                    "adapters": ["core", "tools"],
                    "server": ["core", "tools", "adapters"]
                }
            },
            "testing_policy": {
                "coverage_requirement": 80,
                "required": True,
                "skip_allowed": ["documentation_only", "dependency_update"]
            },
            "security_policy": {
                "code_scanning": True,
                "sensitive_data_detection": True,
                "dependency_vulnerability_check": True
            },
            "stage_management": {
                "require_approval_for_advance": True,
                "allowed_transitions": {
                    "S1": ["S2"],
                    "S2": ["S3"],
                    "S3": ["S4"],
                    "S4": ["S5"],
                    "S5": ["S1"]
                }
            }
        }
        
        self.permissions = {
            "allowed_modifications": [
                "dependency_governance.max_violations",
                "dependency_governance.allowed_sources",
                "audit_policy.retention_days",
                "testing_policy.coverage_requirement",
                "testing_policy.skip_allowed"
            ],
            "prohibited_modifications": [
                "version",
                "policies.*.enabled",
                "policies.architecture_compliance.allowed_layer_dependencies",
                "policies.stage_management.allowed_transitions",
                "permissions"
            ]
        }
        
        # Load from files if exists
        self._load_from_file()
        self._load_policy()
    
    def _load_policy(self):
        """
        Load policy configuration from YAML file
        """
        if os.path.exists(self.policy_path):
            try:
                with open(self.policy_path, "r", encoding="utf-8") as f:
                    policy_data = yaml.safe_load(f)
                    if policy_data:
                        self._update_policy_from_dict(policy_data)
            except Exception as e:
                print(f"Warning: Failed to load policy file: {e}")
    
    def _load_from_file(self):
        """
        Load configuration from YAML file
        """
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        self._update_from_dict(config_data)
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")
    
    def _update_from_dict(self, data):
        """
        Update configuration from dictionary
        """
        if "server" in data:
            self.name = data["server"].get("name", self.name)
        if "mcp_version" in data:
            self.version = data.get("mcp_version", self.version)
        if "rules" in data:
            # Convert list of dicts to dict if needed, or just replace
            if isinstance(data["rules"], list):
                self.rules = {r["id"]: r["description"] for r in data["rules"]}
            elif isinstance(data["rules"], dict):
                self.rules = data["rules"]
        if "enforcement" in data:
            self.violation_policy = data["enforcement"].get("violation_policy", self.violation_policy)
            self.audit_required_stage = data["enforcement"].get("audit_required_stage", self.audit_required_stage)
            
        if "dependencies" in data:
            self.dependency_whitelist = data["dependencies"].get("whitelist", self.dependency_whitelist)
            self.dependency_blacklist = data["dependencies"].get("blacklist", self.dependency_blacklist)
    
    def _update_policy_from_dict(self, policy_data):
        """
        Update policy configuration from dictionary
        
        Args:
            policy_data: Policy data dictionary
        """
        if "version" in policy_data:
            # Version is read-only, just log a warning
            print(f"Warning: policy version is read-only: {policy_data['version']}")
        
        # Update policies
        if "policies" in policy_data:
            for policy_name, policy_config in policy_data["policies"].items():
                if policy_name in self.policies:
                    # Update existing policy
                    self.policies[policy_name].update(policy_config)
                else:
                    # Add new policy
                    self.policies[policy_name] = policy_config
        
        # Update permissions
        if "permissions" in policy_data:
            self.permissions.update(policy_data["permissions"])
        
        # Apply environment-specific configurations
        if "environments" in policy_data:
            env_config = policy_data["environments"].get(self.environment, {})
            if "policies" in env_config:
                for policy_name, policy_config in env_config["policies"].items():
                    if policy_name in self.policies:
                        # Update existing policy with environment-specific config
                        self.policies[policy_name].update(policy_config)
    
    def get_policy(self, policy_name, default=None):
        """
        Get a specific policy
        
        Args:
            policy_name: Policy name
            default: Default value if policy not found
            
        Returns:
            dict or default: Policy configuration or default value
        """
        return self.policies.get(policy_name, default)
    
    def is_policy_enabled(self, policy_name):
        """
        Check if a policy is enabled
        
        Args:
            policy_name: Policy name
            
        Returns:
            bool: True if policy is enabled, False otherwise
        """
        policy = self.get_policy(policy_name, {})
        return policy.get("enabled", False)
    
    def get_permissions(self):
        """
        Get permissions configuration
        
        Returns:
            dict: Permissions configuration
        """
        return self.permissions.copy()

# Global config instance
config = Config()
