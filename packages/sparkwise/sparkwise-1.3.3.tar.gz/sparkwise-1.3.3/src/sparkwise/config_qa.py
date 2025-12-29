"""Configuration Q&A module - interactive documentation assistant."""

from typing import Dict, Any, List, Optional
from pathlib import Path
import yaml
import json
from rich.console import Console


class ConfigurationAssistant:
    """Interactive assistant for Spark/Delta/Fabric configuration questions."""
    
    def __init__(self, knowledge_base_path: Optional[str] = None) -> None:
        """Initialize with knowledge base."""
        if knowledge_base_path is None:
            # Default to package knowledge base (sparkwise/knowledge_base/)
            package_dir = Path(__file__).parent
            knowledge_base_path = package_dir / "knowledge_base"
        
        self.kb_path = Path(knowledge_base_path)
        self.console = Console()
        self.configs = self._load_knowledge_base()
    
    def _load_knowledge_base(self) -> Dict[str, Dict[str, Any]]:
        """Load all configuration knowledge from YAML files."""
        configs = {}
        
        kb_files = [
            "spark_configs.yaml",
            "delta_configs.yaml", 
            "fabric_configs.yaml",
            "fabric_runtime_1.2_configs.yaml"
        ]
        
        try:
            for kb_file in kb_files:
                kb_path = self.kb_path / kb_file
                if kb_path.exists():
                    with open(kb_path, 'r', encoding='utf-8') as f:
                        loaded = yaml.safe_load(f)
                        if loaded:
                            configs.update(loaded)
                            print(f"✓ Loaded {kb_file}: {len(loaded)} configs")
                else:
                    print(f"⚠ Warning: {kb_file} not found at {kb_path}")
        
        except Exception as e:
            print(f"❌ Error loading knowledge base: {e}")
            import traceback
            traceback.print_exc()
        
        self.console.print(f"📚 Total configurations loaded: {len(configs)}")
        return configs
    
    def config(self, config_name: str) -> None:
        """
        Explain a configuration parameter.
        
        Args:
            config_name: Full configuration name (e.g., 'spark.sql.shuffle.partitions')
        """
        if config_name in self.configs:
            self._print_config_details(config_name, self.configs[config_name])
        else:
            # Try fuzzy search
            matches = self._fuzzy_search(config_name)
            
            if matches:
                print(f"📚 Did you mean one of these?\n")
                for match in matches[:5]:
                    print(f"   • {match}")
                print(f"\nTry: ask.config('{matches[0]}')")
            else:
                print(f"❌ Configuration '{config_name}' not found in knowledge base")
                print("   Try searching with a partial name or keyword")
    
    def search(self, keyword: str) -> List[str]:
        """
        Search for configurations by keyword.
        
        Args:
            keyword: Search term
            
        Returns:
            List of matching configuration names
        """
        keyword_lower = keyword.lower()
        matches = []
        
        for config_name, config_data in self.configs.items():
            # Search in name
            if keyword_lower in config_name.lower():
                matches.append(config_name)
                continue
            
            # Search in description
            description = config_data.get("description", "")
            if keyword_lower in description.lower():
                matches.append(config_name)
                continue
            
            # Search in tags
            tags = config_data.get("tags", [])
            if any(keyword_lower in tag.lower() for tag in tags):
                matches.append(config_name)
        
        if matches:
            print(f"📚 Found {len(matches)} configuration(s) matching '{keyword}':\n")
            for match in matches[:10]:
                desc = self.configs[match].get("description", "")[:80]
                print(f"   • {match}")
                print(f"     {desc}...")
            
            if len(matches) > 10:
                print(f"\n   ... and {len(matches) - 10} more")
        else:
            print(f"❌ No configurations found matching '{keyword}'")
        
        return matches
    
    def _fuzzy_search(self, query: str) -> List[str]:
        """Fuzzy search for configuration names."""
        query_lower = query.lower()
        matches = []
        
        for config_name in self.configs.keys():
            # Simple fuzzy matching - check if query parts are in config name
            query_parts = query_lower.replace(".", " ").split()
            config_parts = config_name.lower().replace(".", " ").split()
            
            if any(part in config_parts for part in query_parts):
                matches.append(config_name)
        
        return matches
    
    def _print_config_details(self, name: str, data: Dict[str, Any]) -> None:
        """Print formatted configuration details."""
        self.console.print(f"\n📚 [bold]{name}[/bold]\n")
        self.console.print("─" * 70)
        
        # Default value
        default = data.get("default", "N/A")
        self.console.print(f"\n[cyan]Default:[/cyan] {default}")
        
        # Scope
        scope = data.get("scope", "session")
        self.console.print(f"[cyan]Scope:[/cyan] {scope}")
        
        # Description
        description = data.get("description", "No description available")
        self.console.print(f"\n[cyan]What it does:[/cyan]")
        self.console.print(f"{description}")
        
        # Recommendations
        recommendations = data.get("recommendations", {})
        if recommendations:
            self.console.print(f"\n[cyan]Recommendations for your workload:[/cyan]")
            for scenario, value in recommendations.items():
                self.console.print(f"  • {scenario}: {value}")
        
        # Formula (if applicable)
        formula = data.get("formula")
        if formula:
            self.console.print(f"\n[cyan]Formula:[/cyan] {formula}")
        
        # Fabric-specific notes
        fabric_notes = data.get("fabric_specific")
        if fabric_notes:
            self.console.print(f"\n[cyan]Fabric-specific notes:[/cyan]")
            self.console.print(f"{fabric_notes}")
        
        # Related configs
        related = data.get("related", [])
        if related:
            self.console.print(f"\n[cyan]Related configurations:[/cyan]")
            for rel in related:
                self.console.print(f"  • {rel}")
        
        # Examples
        examples = data.get("examples", [])
        if examples:
            self.console.print(f"\n[cyan]Examples:[/cyan]")
            for example in examples:
                self.console.print(f"  {example}")
        
        self.console.print("\n" + "─" * 70 + "\n")


# Create singleton instance
ask = ConfigurationAssistant()
