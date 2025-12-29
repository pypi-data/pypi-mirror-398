"""
Base plugin system for output formats
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, List, Type
from dataclasses import dataclass


@dataclass
class PluginInfo:
    """Information about a plugin"""
    name: str
    description: str
    version: str
    dependencies: List[str]
    file_extensions: List[str]
    enabled: bool = True


class OutputPlugin(ABC):
    """Base class for output format plugins"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.info = self.get_info()
    
    @abstractmethod
    def get_info(self) -> PluginInfo:
        """Get plugin information"""
        pass
    
    @abstractmethod
    def convert(
        self,
        xml_path: Path,
        output_path: Path,
        intermediate_data: Optional[Dict] = None
    ) -> bool:
        """
        Convert XML to output format
        
        Args:
            xml_path: Path to XML file
            output_path: Path for output file
            intermediate_data: Optional intermediate data from other plugins
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def check_dependencies(self) -> tuple[bool, Optional[str]]:
        """
        Check if plugin dependencies are available
        
        Returns:
            (is_available, error_message)
        """
        pass


class PluginRegistry:
    """Registry for managing output format plugins"""
    
    def __init__(self):
        self._plugins: Dict[str, Type[OutputPlugin]] = {}
        self._plugin_instances: Dict[str, OutputPlugin] = {}
    
    def register(self, name: str, plugin_class: Type[OutputPlugin]):
        """Register a plugin class"""
        self._plugins[name] = plugin_class
    
    def get_plugin(self, name: str, config: Optional[Dict] = None) -> Optional[OutputPlugin]:
        """Get plugin instance"""
        if name not in self._plugins:
            return None
        
        if name not in self._plugin_instances:
            self._plugin_instances[name] = self._plugins[name](config)
        
        return self._plugin_instances[name]
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all registered plugins with their info"""
        plugins_info = []
        for name, plugin_class in self._plugins.items():
            try:
                instance = plugin_class()
                # Check if dependencies are available
                available, error = instance.check_dependencies()
                plugin_info = instance.info
                plugin_info.enabled = available
                if not available and error:
                    plugin_info.description += f" ({error})"
                plugins_info.append(plugin_info)
            except Exception as e:
                # Plugin might not be available due to missing dependencies
                plugins_info.append(PluginInfo(
                    name=name,
                    description=f"Plugin not available: {str(e)}",
                    version="unknown",
                    dependencies=[],
                    file_extensions=[],
                    enabled=False
                ))
        return plugins_info
    
    def get_available_plugins(self) -> List[str]:
        """Get list of available plugin names"""
        return list(self._plugins.keys())
    
    def is_plugin_available(self, name: str) -> tuple[bool, Optional[str]]:
        """Check if plugin is available (dependencies installed)"""
        if name not in self._plugins:
            return False, f"Plugin '{name}' not found"
        
        try:
            plugin = self._plugins[name]()
            return plugin.check_dependencies()
        except Exception as e:
            return False, str(e)

