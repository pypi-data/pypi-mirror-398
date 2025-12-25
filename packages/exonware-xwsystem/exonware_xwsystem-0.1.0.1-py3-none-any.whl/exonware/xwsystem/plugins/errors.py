#exonware/xwsystem/plugins/errors.py
"""
Company: eXonware.com
Author: Eng. Muhammad AlShehri
Email: connect@exonware.com
Version: 0.1.0.1
Generation Date: September 04, 2025

Plugin-specific error classes for XSystem plugin system.
"""

from typing import Any, Optional


class PluginError(Exception):
    """Base exception for all plugin-related errors."""
    
    def __init__(self, message: str, plugin_name: Optional[str] = None, 
                 plugin_version: Optional[str] = None, context: Optional[dict[str, Any]] = None, 
                 original_error: Optional[Exception] = None):
        super().__init__(message)
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version
        self.context = context or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.plugin_name:
            base_msg = f"[Plugin: {self.plugin_name}] {base_msg}"
        if self.plugin_version:
            base_msg = f"{base_msg} (Version: {self.plugin_version})"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base_msg = f"{base_msg} (Context: {context_str})"
        return base_msg


class PluginNotFoundError(PluginError):
    """Error when a requested plugin is not found."""
    
    def __init__(self, plugin_name: str, available_plugins: Optional[list[str]] = None, **kwargs):
        message = f"Plugin '{plugin_name}' not found"
        if available_plugins:
            message += f". Available plugins: {', '.join(available_plugins)}"
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.available_plugins = available_plugins or []


class PluginLoadError(PluginError):
    """Error when plugin loading fails."""
    
    def __init__(self, message: str, plugin_name: str, plugin_path: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.plugin_path = plugin_path


class PluginImportError(PluginLoadError):
    """Error when plugin import fails."""
    
    def __init__(self, message: str, plugin_name: str, module_name: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.module_name = module_name


class PluginDependencyError(PluginLoadError):
    """Error when plugin dependencies are not met."""
    
    def __init__(self, message: str, plugin_name: str, missing_dependencies: Optional[list[str]] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.missing_dependencies = missing_dependencies or []


class PluginVersionError(PluginLoadError):
    """Error when plugin version is incompatible."""
    
    def __init__(self, message: str, plugin_name: str, required_version: Optional[str] = None, 
                 actual_version: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.required_version = required_version
        self.actual_version = actual_version


class PluginRegistrationError(PluginError):
    """Error when plugin registration fails."""
    
    def __init__(self, message: str, plugin_name: str, plugin_class: Optional[type] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.plugin_class = plugin_class


class PluginDuplicateError(PluginRegistrationError):
    """Error when trying to register a duplicate plugin."""
    
    def __init__(self, message: str, plugin_name: str, existing_version: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.existing_version = existing_version


class PluginValidationError(PluginRegistrationError):
    """Error when plugin validation fails."""
    
    def __init__(self, message: str, plugin_name: str, validation_errors: Optional[list[str]] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.validation_errors = validation_errors or []


class PluginInitializationError(PluginError):
    """Error when plugin initialization fails."""
    
    def __init__(self, message: str, plugin_name: str, plugin_version: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, plugin_version=plugin_version, **kwargs)


class PluginConfigurationError(PluginInitializationError):
    """Error when plugin configuration is invalid."""
    
    def __init__(self, message: str, plugin_name: str, config_key: Optional[str] = None, 
                 config_value: Optional[Any] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.config_key = config_key
        self.config_value = config_value


class PluginResourceError(PluginInitializationError):
    """Error when plugin resource allocation fails."""
    
    def __init__(self, message: str, plugin_name: str, resource_type: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.resource_type = resource_type


class PluginExecutionError(PluginError):
    """Error when plugin execution fails."""
    
    def __init__(self, message: str, plugin_name: str, plugin_version: Optional[str] = None, 
                 operation: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, plugin_version=plugin_version, **kwargs)
        self.operation = operation


class PluginMethodError(PluginExecutionError):
    """Error when plugin method execution fails."""
    
    def __init__(self, message: str, plugin_name: str, method_name: str, **kwargs):
        super().__init__(message, plugin_name=plugin_name, operation=method_name, **kwargs)
        self.method_name = method_name


class PluginTimeoutError(PluginExecutionError):
    """Error when plugin operation times out."""
    
    def __init__(self, message: str, plugin_name: str, timeout_duration: float, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.timeout_duration = timeout_duration


class PluginPermissionError(PluginExecutionError):
    """Error when plugin lacks required permissions."""
    
    def __init__(self, message: str, plugin_name: str, required_permission: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.required_permission = required_permission


class PluginCleanupError(PluginError):
    """Error when plugin cleanup fails."""
    
    def __init__(self, message: str, plugin_name: str, plugin_version: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, plugin_version=plugin_version, **kwargs)


class PluginUnloadError(PluginCleanupError):
    """Error when plugin unloading fails."""
    
    def __init__(self, message: str, plugin_name: str, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)


class PluginRegistryError(PluginError):
    """Error related to plugin registry operations."""
    
    def __init__(self, message: str, registry_operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.registry_operation = registry_operation


class PluginRegistryFullError(PluginRegistryError):
    """Error when plugin registry is full."""
    
    def __init__(self, message: str, max_plugins: int, current_count: int, **kwargs):
        super().__init__(message, registry_operation="register", **kwargs)
        self.max_plugins = max_plugins
        self.current_count = current_count


class PluginRegistryLockError(PluginRegistryError):
    """Error when plugin registry is locked."""
    
    def __init__(self, message: str, registry_operation: str, **kwargs):
        super().__init__(message, registry_operation=registry_operation, **kwargs)


class PluginManagerError(PluginError):
    """Error related to plugin manager operations."""
    
    def __init__(self, message: str, manager_operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.manager_operation = manager_operation


class PluginManagerNotInitializedError(PluginManagerError):
    """Error when plugin manager is not initialized."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, manager_operation="initialize", **kwargs)


class PluginManagerShutdownError(PluginManagerError):
    """Error when plugin manager shutdown fails."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, manager_operation="shutdown", **kwargs)


class PluginDiscoveryError(PluginError):
    """Error when plugin discovery fails."""
    
    def __init__(self, message: str, discovery_path: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.discovery_path = discovery_path


class PluginEntryPointError(PluginDiscoveryError):
    """Error when plugin entry point is invalid."""
    
    def __init__(self, message: str, entry_point: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.entry_point = entry_point


class PluginMetadataError(PluginError):
    """Error when plugin metadata is invalid."""
    
    def __init__(self, message: str, plugin_name: str, metadata_key: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.metadata_key = metadata_key


class PluginInterfaceError(PluginError):
    """Error when plugin interface is invalid."""
    
    def __init__(self, message: str, plugin_name: str, interface_name: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.interface_name = interface_name


class PluginLifecycleError(PluginError):
    """Error when plugin lifecycle operation fails."""
    
    def __init__(self, message: str, plugin_name: str, lifecycle_stage: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.lifecycle_stage = lifecycle_stage


class PluginStateError(PluginLifecycleError):
    """Error when plugin is in invalid state for operation."""
    
    def __init__(self, message: str, plugin_name: str, current_state: str, required_state: str, **kwargs):
        super().__init__(message, plugin_name=plugin_name, lifecycle_stage=current_state, **kwargs)
        self.current_state = current_state
        self.required_state = required_state


class PluginHookError(PluginError):
    """Error when plugin hook execution fails."""
    
    def __init__(self, message: str, plugin_name: str, hook_name: str, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.hook_name = hook_name


class PluginEventError(PluginError):
    """Error when plugin event handling fails."""
    
    def __init__(self, message: str, plugin_name: str, event_name: str, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.event_name = event_name


class PluginCommunicationError(PluginError):
    """Error when plugin communication fails."""
    
    def __init__(self, message: str, plugin_name: str, target_plugin: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.target_plugin = target_plugin


class PluginSecurityError(PluginError):
    """Error when plugin security check fails."""
    
    def __init__(self, message: str, plugin_name: str, security_violation: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.security_violation = security_violation


class PluginSandboxError(PluginSecurityError):
    """Error when plugin sandbox operation fails."""
    
    def __init__(self, message: str, plugin_name: str, sandbox_operation: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, security_violation="sandbox", **kwargs)
        self.sandbox_operation = sandbox_operation


class PluginCapabilityError(PluginError):
    """Error when plugin capability is insufficient."""
    
    def __init__(self, message: str, plugin_name: str, required_capability: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.required_capability = required_capability


class PluginCompatibilityError(PluginError):
    """Error when plugin compatibility check fails."""
    
    def __init__(self, message: str, plugin_name: str, system_version: Optional[str] = None, 
                 plugin_version: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, plugin_version=plugin_version, **kwargs)
        self.system_version = system_version


class PluginConflictError(PluginError):
    """Error when plugin conflicts with another plugin."""
    
    def __init__(self, message: str, plugin_name: str, conflicting_plugin: str, 
                 conflict_type: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.conflicting_plugin = conflicting_plugin
        self.conflict_type = conflict_type


class PluginPriorityError(PluginError):
    """Error when plugin priority is invalid."""
    
    def __init__(self, message: str, plugin_name: str, priority: Optional[int] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.priority = priority


class PluginDependencyCycleError(PluginError):
    """Error when plugin dependency cycle is detected."""
    
    def __init__(self, message: str, plugin_name: str, dependency_cycle: Optional[list[str]] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.dependency_cycle = dependency_cycle or []


class PluginHotReloadError(PluginError):
    """Error when plugin hot reload fails."""
    
    def __init__(self, message: str, plugin_name: str, reload_reason: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.reload_reason = reload_reason


class PluginBackupError(PluginError):
    """Error when plugin backup/restore fails."""
    
    def __init__(self, message: str, plugin_name: str, backup_operation: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.backup_operation = backup_operation


class PluginMigrationError(PluginError):
    """Error when plugin migration fails."""
    
    def __init__(self, message: str, plugin_name: str, from_version: Optional[str] = None, 
                 to_version: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.from_version = from_version
        self.to_version = to_version


class PluginMonitoringError(PluginError):
    """Error when plugin monitoring fails."""
    
    def __init__(self, message: str, plugin_name: str, monitoring_metric: Optional[str] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.monitoring_metric = monitoring_metric


class PluginPerformanceError(PluginError):
    """Error when plugin performance is below threshold."""
    
    def __init__(self, message: str, plugin_name: str, performance_metric: Optional[str] = None, 
                 threshold: Optional[float] = None, actual_value: Optional[float] = None, **kwargs):
        super().__init__(message, plugin_name=plugin_name, **kwargs)
        self.performance_metric = performance_metric
        self.threshold = threshold
        self.actual_value = actual_value
