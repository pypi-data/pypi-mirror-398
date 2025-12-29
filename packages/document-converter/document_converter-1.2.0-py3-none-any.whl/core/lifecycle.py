import signal
import logging
import sys
from typing import List, Protocol, Any

logger = logging.getLogger(__name__)

class Shutdownable(Protocol):
    def shutdown(self, wait: bool = True) -> Any:
        ...

class LifecycleManager:
    """
    Manages application lifecycle and signal handling for graceful shutdown.
    """
    
    def __init__(self):
        self._components: List[Shutdownable] = []
        self._is_shutting_down = False
        
    def register_component(self, component: Shutdownable):
        """
        Register a component to be shut down gracefully.
        
        Args:
            component: An object with a shutdown method.
        """
        self._components.append(component)
        
    def start(self):
        """
        Setup signal handlers.
        """
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
        logger.info("LifecycleManager started. Listening for SIGINT/SIGTERM.")

    def handle_signal(self, signum, frame):
        """
        Handle received signals.
        """
        if self._is_shutting_down:
            logger.warning("Shutdown already in progress. Forcing exit.")
            sys.exit(1)
            
        self._is_shutting_down = True
        sig_name = signal.Signals(signum).name
        logger.info(f"Received signal {sig_name}. Initiating graceful shutdown...")
        self.shutdown()
        sys.exit(0)

    def shutdown(self):
        """
        Shutdown all registered components.
        """
        logger.info("Shutting down components...")
        # Shutdown in reverse order of registration (LIFO)
        for component in reversed(self._components):
            try:
                logger.info(f"Shutting down {component.__class__.__name__}...")
                component.shutdown(wait=True)
            except Exception as e:
                logger.error(f"Error shutting down {component.__class__.__name__}: {e}")
        logger.info("Graceful shutdown complete.")
