import asyncio
import signal
from typing import Any, Callable, Optional, Dict

from aas_thing.util.callback_manager import CallbackManager
from aas_thing.s3i_connection import S3IConnector
from aas_thing.aas_connection import AASConnector
from aas_thing.message_handler import I40SemanticProtocolHandler
from aas_thing.util.logger import setup_logger
from aas_thing.util.open_config_yaml import load_config_yaml_to_json


class BaseAASThing:
    """
    Base class for AAS-based Things integrating with the S³I ecosystem.

    Loads configuration, initializes connectors, and manages event loop execution
    with lifecycle callbacks.
    Basic usage:

    .. code-block:: python

        thing = BaseAASThing(config_path)
        thing.add_on_thing_start(callback)
        thing.add_on_thing_shutdown(callback)
        thing.start()  # blocks until interrupted
    """

    def __init__(
        self,
        config_path: str,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        is_logger: bool = True,
        logger_name: str = None
    ) -> None:
        # Initialize logger
        """
        Initialize the AAS-based thing with configuration and event loop.

        :param config_path: Path to the configuration file (YAML or JSON)
        :param loop: Optional event loop, defaults to asyncio.new_event_loop()
        :param is_logger: Whether to set up a logger, defaults to True
        :raises Exception: If loading the configuration fails
        """
        if is_logger:
            self._logger = setup_logger(logger_name if logger_name else __class__.__name__)

        # Load configuration
        try:
            self._config: Dict[str, Any] = load_config_yaml_to_json(config_path)
        except Exception as ex:
            self._logger.error("Failed to load config '%s': %s", config_path, ex)
            raise


        # Event loop
        self._loop = loop or asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._thing_id = self._config["s3i_connector"]["identity_provider"]["client_id"]
        # Setup connectors
        self._aas = AASConnector(config=self._config["aas_connector"], logger=self._logger)
        self._s3i = S3IConnector(
            config=self._config["s3i_connector"],
            loop=self._loop,
            logger=self._logger,
            handler=I40SemanticProtocolHandler(
                aas=self._aas.aas,
                submodels=self._aas.submodels,
                logger=self._logger
            ),
        )
        # Callback manager
        self._callback_manager = CallbackManager()
        self._ON_THING_START = "on_start"
        self._ON_THING_SHUTDOWN = "on_shutdown"

    def add_on_thing_start(
        self,
        callback: Callable[..., Any],
        one_shot: bool = False,
        is_async: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Register a callback to be invoked right when connectors start.

        The callback is called after the :meth:`start` method of the connectors are invoked.
        The callback is called with the given arguments and keyword arguments.

        :param callback: The callback to be invoked
        :param one_shot: Whether the callback should be removed after the first invocation, defaults to False
        :param is_async: Whether the callback is an asynchronous function, defaults to False
        :param args: Arguments to be passed to the callback
        :param kwargs: Keyword arguments to be passed to the callback
        """
        self._callback_manager.add(self._ON_THING_START, callback, one_shot, is_async, *args, **kwargs)

    def add_on_thing_shutdown(
        self,
        callback: Callable[..., Any],
        one_shot: bool = False,
        is_async: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Register a callback to be invoked when the thing is shutting down.

        The callback is called when the :meth:`shutdown` method is invoked.
        The callback is called with the given arguments and keyword arguments.

        :param callback: The callback to be invoked
        :param one_shot: Whether the callback should be removed after the first invocation, defaults to False
        :param is_async: Whether the callback is an asynchronous function, defaults to False
        :param args: Arguments to be passed to the callback
        :param kwargs: Keyword arguments to be passed to the callback
        """
        self._callback_manager.add(self._ON_THING_SHUTDOWN, callback, one_shot, is_async, *args, **kwargs)

    def start(self) -> None:
        """
        Start the AAS Thing.

        This method will invoke the on_start callbacks, connect to the S3I services,
        and run the event loop until termination. It also sets up graceful shutdown
        handlers for UNIX-style signals.
        """
        self._logger.info("Starting AAS Thing")

        # Invoke all registered 'on_start' callbacks
        self._callback_manager.process(self._ON_THING_START)

        # Establish connection with S3I services
        self._s3i.connect()

        # Setup graceful shutdown handlers for UNIX signals
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                self._loop.add_signal_handler(sig, self._stop)
            except NotImplementedError:
                self._logger.warning(
                    "Signal handler for shutdown is not supported on this platform for %s", sig
                )

        try:
            # Start the event loop
            self._loop.run_forever()
        except KeyboardInterrupt:
            self._logger.info("KeyboardInterrupt received")
        except Exception as exc:
            # Log any exception that occurs during the event loop execution
            self._logger.error("Error in event loop: %s", exc)
        finally:
            # Perform cleanup operations
            self._cleanup()

    def _stop(self) -> None:
        """
        Signal handler to stop the loop and trigger shutdown.

        This is a no-op if the loop is not running.
        """
        self._logger.info("Shutdown signal received")
        # Stop the loop
        self._loop.stop()

    def _stop(self) -> None:
        """
        Signal handler to stop the loop and trigger shutdown.

        This is a no-op if the loop is not running.
        """
        self._logger.info("Shutdown signal received")
        # Stop the loop
        self._loop.stop()


    def _cleanup(self) -> None:
        """
        Cleanup tasks: disconnect connectors and invoke shutdown callbacks.

        This function is called when the AAS Thing is being shut down.
        """
        # Invoke shutdown callbacks
        self._callback_manager.process(self._ON_THING_SHUTDOWN)

        # Disconnect connectors if supported
        
        self._s3i.disconnect()


        # Close the loop
        pending = asyncio.all_tasks(loop=self._loop)
        for task in pending:
            task.cancel()
        # Wait for all tasks to be cancelled
        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        # Close the loop
        self._loop.close()
        self._logger.info("AAS Thing shutdown complete")
