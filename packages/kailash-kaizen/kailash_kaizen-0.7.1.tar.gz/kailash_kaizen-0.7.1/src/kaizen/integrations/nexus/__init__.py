"""
Kaizen-Nexus Integration (Optional).

This integration is OPTIONAL and activates only when both frameworks are present.
- Kaizen works independently without Nexus
- Nexus works independently without Kaizen
- Integration provides multi-channel deployment when both present
"""

# Check Nexus availability
try:
    from nexus import Nexus

    NEXUS_AVAILABLE = True
except ImportError:
    NEXUS_AVAILABLE = False
    Nexus = None

# Export integration components only when available
if NEXUS_AVAILABLE:
    from .base import NexusDeploymentMixin
    from .connection import NexusConnection
    from .deployment import (
        deploy_as_api,
        deploy_as_cli,
        deploy_as_mcp,
        deploy_multi_channel,
        deploy_with_sessions,
    )
    from .deployment_cache import (
        DeploymentCache,
        clear_deployment_cache,
        get_deployment_cache,
    )
    from .monitoring import (
        PerformanceMetrics,
        PerformanceMonitor,
        get_global_metrics,
        reset_global_metrics,
    )
    from .parameter_mapper import ParameterMapper
    from .session_manager import CrossChannelSession, NexusSessionManager

    __all__ = [
        "NEXUS_AVAILABLE",
        "NexusConnection",
        "NexusDeploymentMixin",
        "deploy_as_api",
        "deploy_as_cli",
        "deploy_as_mcp",
        "deploy_multi_channel",
        "deploy_with_sessions",
        "ParameterMapper",
        "CrossChannelSession",
        "NexusSessionManager",
        "DeploymentCache",
        "get_deployment_cache",
        "clear_deployment_cache",
        "PerformanceMetrics",
        "PerformanceMonitor",
        "get_global_metrics",
        "reset_global_metrics",
    ]
else:
    __all__ = ["NEXUS_AVAILABLE"]

__version__ = "0.1.0"
