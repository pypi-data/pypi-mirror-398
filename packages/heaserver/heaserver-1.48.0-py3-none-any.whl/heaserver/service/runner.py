"""
Starts a HEA microservice.
"""
import asyncio
import logging.config
import argparse
from aiohttp import web, TCPConnector, ClientResponseError
import os.path
from heaserver.service import appproperty, appfactory
from heaserver.service import wstl
from heaserver.service.aiohttp import client_session
from typing import Callable, Iterable, Optional, Union, AsyncIterator, Type, cast
from yarl import URL

from heaserver.service.logging import DEBUG_LOG_CONFIG, PROD_LOG_CONFIG, ScrubbingLogger

from .config import Configuration
from .db.database import MicroserviceDatabaseManager

from .defaults import DEFAULT_LOG_LEVEL, DEFAULT_PORT, DEFAULT_BASE_URL, DEFAULT_REGISTRY_URL
from ..service import client
from asyncio import create_task, wait_for, CancelledError, TimeoutError
from .backgroundtasks import BackgroundTasks
from cachetools import TTLCache
from enum import Enum

routes = web.RouteTableDef()


def init(port: Union[int, str] = DEFAULT_PORT,
         base_url: Union[URL, str] = DEFAULT_BASE_URL,
         config_file: Optional[str] = None,
         config_string: Optional[str] = None,
         logging_level: Optional[str] = None) -> Configuration:
    """
    Sets a logging level and python's "basic" logging config, and it returns a new Configuration object. To customize
    logging further, use the heaserver.service.logging module to set up logging before calling this function and
    omit the logging_level argument. Alternatively, instead of calling this function, use the
    heaserver.service.runner.init_cmd_line() function to configure logging from command line arguments.

    :param port: the port the service will listen to. If omitted, the DEFAULT_PORT is used.
    :param base_url: the service's base URL. If omitted, the DEFAULT_BASE_URL is used.
    :param config_file:
    :param config_string:
    :param logging_level: configure the logging level. If omitted, logging will not be configured.
    :return: a Configuration object.
    """
    if logging_level is not None:
        logging.basicConfig(level=logging_level)
    config = Configuration(base_url=base_url,
                           port=port,
                           config_file=config_file,
                           config_str=config_string)
    return config


def init_cmd_line(description: str = 'A HEA microservice', default_port: int = DEFAULT_PORT) -> Configuration:
    """
    Parses command line arguments and configures the service accordingly. Must be called before anything else, if you
    want to use command line arguments to configure the service. It exits the program if any command line arguments are
    invalid. It configures logging according to the command line arguments, or uses the default logging configuration
    for the specified environment, or uses the default logging configuration if no logging configuration file or
    environment is specified.

    :param description: optional description that will appear when the script is passed the -h or --help option.
    :param default_port: the optional port on which to listen if none is specified by command line argument. If omitted
    and no port is specified by command line argument, port 8080 is used.
    :return: a Configuration object.
    :raises ValueError: if any arguments are invalid.

    The following command line arguments are accepted:
        -b or --baseurl, which optionally sets the base URL of the service. If unspecified, the default is
        http://localhost:<port>, where port is the 8080 or the port number set by the --port argument.
        -p or --port, which optionally sets the port the microservice will listen on. The default is 8080.
        -f or --configuration, which optionally sets an INI file to use for additional configuration.
        -l or --logging, which optionally sets a standard logging configuration INI file. If unspecified, the
            DEFAULT_LOG_LEVEL variable will be used to set the default log level.
        -e or --env, which optionally sets the runtime environment (development, staging, or production). Parsing is
            case-insensitive. When unspecified, the default value is development. It currently impacts logging
            configuration, and only if no logging configuration file is specified.

    Microservices must not call logging.getLogger until init has been called, or logging will not be configured
    properly.

    The INI configuration file is parsed by the built-in configparser module and may contain the following settings:

    ;Base URL for the HEA registry service (default is http://localhost:8080/heaserver-server-registry)
    Registry = url of the HEA registry service

    ;See the documentation for the db object that you passed in for the config file properties that it expects.
    """
    assert default_port is not None

    parser = argparse.ArgumentParser(description)
    parser.add_argument('-b', '--baseurl',
                        metavar='baseurl',
                        type=str,
                        default=str(DEFAULT_BASE_URL),
                        help='The base URL of the service')
    parser.add_argument('-p', '--port',
                        metavar='port',
                        type=int,
                        default=default_port,
                        help='The port on which the server will listen for connections')
    parser.add_argument('-f', '--configuration',
                        metavar='configuration',
                        type=str,
                        help='Path to a HEA configuration file in INI format')
    parser.add_argument('-l', '--logging',
                        metavar='logging',
                        type=str,
                        help='Standard logging configuration file')
    parser.add_argument('-e', '--env',
                        metavar='env',
                        type=str, choices=['development', 'staging', 'production'],
                        help='The runtime environment (development, staging, or production). Parsing is case-insensitive. When unspecified, the default value is development. It currently impacts logging configuration, and only if no logging configuration file is specified.')
    args = parser.parse_args()

    _configure_logging_from_args(args)

    baseurl_ = args.baseurl
    return Configuration(base_url=baseurl_[:-1] if baseurl_.endswith('/') else baseurl_,
                         config_file=args.configuration,
                         port=args.port)


def start(package_name: str | None = None,
          db: Optional[Type[MicroserviceDatabaseManager]] = None,
          wstl_builder_factory: Optional[Callable] = None,
          cleanup_ctx: Optional[Iterable[Callable[[web.Application], AsyncIterator[None]]]] = None,
          config: Optional[Configuration] = None) -> None:
    """
    Starts the microservice. It calls get_application() to get the AioHTTP app
    object, sets up a global HTTP client session object in the appproperty.HEA_CLIENT_SESSION property, and then calls
    AioHTTP's aiohttp.web.run_app() method with it to launch the service. It sets the
    application and request properties described in the documentation for get_application(). It sets uvloop as the
    event loop on platforms that uvloop supports. The service listens on all available network interfaces (IP address
    0.0.0.0), and the port is set by passing a heaserver.service.config.Configuration object with the desired port
    attribute. If the port is unset, the service listens on port 8080. Limiting the network interfaces that the service
    listens on is not supported but can be achieved with firewall rules, Docker, or other network configuration tools.

    :param package_name: the microservice's distribution package name. The HEA server framework uses this argument to
    register metadata about the microservice in the HEA registry service. Omit this argument if you do not want this
    microservice to register metadata about itself using this mechanism. For example, the registry service has to
    register itself using its own mechanism.
    :param db: a database manager type from the heaserver.server.db package, if database connectivity is needed. Sets
    the appproperty.HEA_DB application property to a database object created by this database manager.
    :param wstl_builder_factory: a zero-argument callable that will return a design-time WeSTL document. Optional if
    this service has no actions.
    :param cleanup_ctx: an iterable of asynchronous iterators that will be passed into the aiohttp cleanup context.
    The iterator should have a single yield statement that separates code to be run upon startup and code to be
    run upon shutdown. The shutdown code will run only if the startup code did not raise any exceptions. The startup
    code will run in sequential order. The shutdown code will run in reverse order.
    :param config: a Configuration instance.
    :raises ValueError: if registering the externally facing URL with the registry service failed.

    This function must be called after init.

    A 'registry' property is set in the application context with the registry service's base URL.
    """
    _logger = logging.getLogger(__name__)
    if config is None:
        config_ = init()
    else:
        config_ = config
    db_ = db() if db is not None else None

    app = get_application(package_name, db=db_, wstl_builder_factory=wstl_builder_factory,
                          cleanup_ctx=cleanup_ctx, config=config_)
    app.cleanup_ctx.append(client_session_cleanup_ctx)
    try:
        import uvloop  # type:ignore[import-not-found]
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        _logger.debug('Running uvloop event loop')
    except:
        _logger.debug('Running default event loop')
    web.run_app(app, port=config_.port if config_.port else DEFAULT_PORT)


def get_application(package_name: str | None = None,
                    db: Optional[MicroserviceDatabaseManager] = None,
                    wstl_builder_factory: Optional[Callable[[], wstl.RuntimeWeSTLDocumentBuilder]] = None,
                    cleanup_ctx: Optional[Iterable[Callable[[web.Application], AsyncIterator[None]]]] = None,
                    config: Optional[Configuration] = None) -> web.Application:
    """
    Gets the aiohttp application object for this microservice. It is called by start() during normal operations, and
    by test cases when running tests.

    It registers cleanup context iterators that set the following application properties:
    HEA_DB: a database object from the heaserver.server.db package.
    HEA_CLIENT_SESSION: a aiohttp.web.ClientSession HTTP client object. This property is only set if the testing
    argument is False. If running test cases, testing should be set to True, and the HEAAioHTTPTestCase class will
    handle creating and destroying HTTP clients instead.
    HEA_REGISTRY: The base URL for the registry service.
    HEA_COMPONENT: This service's base URL.
    HEA_WSTL_BUILDER_FACTORY: the wstl_builder_factory argument.

    :param package_name: the microservice's distribution package name. If None, the service will not register its
    externally facing base URL with the registry service. This may be what you want in testing scenarios in which no
    registry service is running.
    :param db: a database object from the heaserver.server.db package, if database connectivity is needed.
    :param wstl_builder_factory: a zero-argument callable that will return a RuntimeWeSTLDocumentBuilder. Optional if
    this service has no actions. Typically, you will use the heaserver.service.wstl.get_builder_factory function to
    get a factory object.
    :param cleanup_ctx: an iterable of asynchronous iterators that will be passed into the aiohttp cleanup context.
    The iterators should have a single yield statement that separates code to be run upon startup and code to be
    run upon shutdown. The shutdown code will run only if the startup code did not raise any exceptions. Cleanup
    context iterators cannot assume that any of the above application properties are available.
    :param config: a Configuration instance.
    :return: an aiohttp application object.
    :raises ValueError: if registering the externally facing URL with the registry service failed.

    This function must be called after init, and it is called by start.

    A 'registry' property is set in the application context with the registry service's base URL.
    """
    logger = logging.getLogger(__name__)

    logger.info('Starting HEA')

    app = appfactory.new_app()

    if hasattr(asyncio, 'eager_task_factory'):
        async def _set_eager_task_factory(app: web.Application) -> AsyncIterator[None]:
            loop = asyncio.get_running_loop()
            try:
                loop.set_task_factory(asyncio.eager_task_factory)   # type: ignore[attr-defined]
                logger.debug('Eager task factory is turned on')
            except AttributeError:
                pass
            yield
        app.cleanup_ctx.append(_set_eager_task_factory)
    else:
        logger.debug('Using default task factory because eager task factory is not supported by this version of python')

    if db:
        async def _db(app: web.Application) -> AsyncIterator[None]:
            if db:
                async with db.database() as database:
                    app[appproperty.HEA_DB] = database
                    yield
            else:
                app[appproperty.HEA_DB] = None
        if config:
            db.config = config
        app.cleanup_ctx.append(_db)

    def gen_hea_registry_app_property():
        registry_url = config.parsed_config['DEFAULT'].get('Registry', DEFAULT_REGISTRY_URL) if config else None
        app[appproperty.HEA_REGISTRY] = registry_url
    gen_hea_registry_app_property()

    # Instance of heaserver.service.crypt.EncryptionDecryptionKeyGetter. We currently use only one key for attribute
    # encryption and decryption, as well as configuration property decryption.
    app[appproperty.HEA_ATTRIBUTE_ENCRYPTION_KEY_GETTER] = config

    async def _hea_component(app: web.Application) -> AsyncIterator[None]:
        external_base_url = str(config.base_url) if config else None
        app[appproperty.HEA_COMPONENT] = external_base_url
        if package_name is not None:
            # Needs its own client session because the main client session has not started yet.
            logger.info('Registering external URL %s for component %s with HEA registry service at %s...',
                        external_base_url, package_name, app[appproperty.HEA_REGISTRY])
            async with client_session(connector=TCPConnector(), connector_owner=True, raise_for_status=True) as session:
                logger.debug('Created temporary client session to register component %s with HEA registry service',
                             package_name)
                # Consults the registry service as the system|none user, so the heaserver-people service does not need
                # to be consulted for permissions information.
                component = await client.get_component_by_name(app, package_name, client_session=session)
                if component is not None:
                    logger.debug('Found component %r in registry service to register external URL', component)
                    component.external_base_url = external_base_url
                    logger.info('Registering external URL %s for component %s...', external_base_url, package_name,)
                    try:
                        assert component.id is not None, 'component has a None id'
                        await client.put(app, URL(app[appproperty.HEA_REGISTRY]) / 'components' / component.id, component, client_session=session)
                        logger.info('Successfully registered external URL for component %s.', package_name)
                    except ClientResponseError as e:
                        raise ValueError(f'Failed to register external URL for component {package_name}') from e
                else:
                    logger.warning('The external URL for component %s is not registered with the HEA registry service.', package_name)
        else:
            logger.info('Skipping registration of the external URL for component %s with the HEA registry service.', external_base_url)
        yield

    app.cleanup_ctx.append(_hea_component)

    async def _background_tasks(app: web.Application) -> AsyncIterator[None]:
        logger.info('Starting background tasks...')
        background_tasks = BackgroundTasks(app)
        app[appproperty.HEA_BACKGROUND_TASKS] = background_tasks
        async def background_tasks_coro():
            await background_tasks.auto_join()
        task = create_task(background_tasks_coro(), name='background_tasks')
        logger.info('Background tasks started.')
        yield
        logger.info('Shutting down background tasks...')
        task.cancel()
        try:
            await wait_for(task, timeout=30)
        except CancelledError:
            pass
        except TimeoutError:
            logger.warning('Timed out trying to end background tasks: %s', background_tasks)
        finally:
            await background_tasks.clear()
        logger.info('Background tasks shut down.')

    app.cleanup_ctx.append(_background_tasks)

    async def _cache(app: web.Application) -> AsyncIterator[None]:
        cache: TTLCache = TTLCache(maxsize=128, ttl=30)
        app[appproperty.HEA_CACHE] = cache
        yield
        app[appproperty.HEA_CACHE] = None


    app.cleanup_ctx.append(_cache)

    app.add_routes(routes)

    async def _hea_wstl_builder_factory(app: web.Application) -> AsyncIterator[None]:
        if wstl_builder_factory is None:
            logger.debug('No design-time WeSTL loader was provided.')
            wstl_builder_factory_ = wstl.builder_factory()
        else:
            wstl_builder_factory_ = wstl_builder_factory

        app[appproperty.HEA_WSTL_BUILDER_FACTORY] = wstl_builder_factory_
        yield

    app.cleanup_ctx.append(_hea_wstl_builder_factory)

    if cleanup_ctx is not None:
        for cb in cleanup_ctx:
            app.cleanup_ctx.append(cb)
    return app


async def client_session_cleanup_ctx(app: web.Application) -> AsyncIterator[None]:
    """
    Manages the global HTTP client session, to be added to the cleanup context.

    :param app: the AioHTTP Application object.
    :return: an async iterator.
    """
    _logger = logging.getLogger(__name__)
    _logger.debug('Starting client session')
    async with client_session(connector=TCPConnector(), connector_owner=True, raise_for_status=True) as session:
        app[appproperty.HEA_CLIENT_SESSION] = session
        _logger.debug('Client session started')
        yield
        _logger.debug('Closing client session')


def scheduled_cleanup_ctx(coro, delay: int) -> Callable[[web.Application], AsyncIterator[None]]:
    """
    A cleanup context factory for scheduling recurring background tasks with a delay

    :param coro: The coroutine to be scheduled
    :param delay: The delay in seconds before scheduling the coroutine. The delay and scheduling will repeat
    indefinitely.
    :return: a callable that can be added to the cleanup context.
    """
    logger = logging.getLogger(__name__)
    async def scheduler(app: web.Application) -> AsyncIterator[None]:
        async def loop():
            while True:
                await asyncio.sleep(delay)
                if (tasks := cast(BackgroundTasks, app.get(appproperty.HEA_BACKGROUND_TASKS))) is not None:
                    await tasks.add(coro)
                else:
                    logger.warning('No background tasks manager found; skipping scheduled task execution. The '
                                   'background tasks manager may just not have been initialized yet. If this keeps '
                                   'happening, however, there may be a problem.')

        task = asyncio.create_task(loop())
        yield
        task.cancel()
        await task
    return scheduler

def wait_on_coro_cleanup_ctx(coro, delay: int = 0):
    """
    A producer to schedules reoccurring background tasks to be awaited before adding another

    :param coro: The coroutine to be scheduled
    :param delay: The delay in seconds to run the reoccurring coroutine
    """
    logger = logging.getLogger(__name__)
    async def scheduler(app: web.Application):

        async def loop():
            while True:
                await asyncio.sleep(delay)
                if (tasks := cast(BackgroundTasks, app.get(appproperty.HEA_BACKGROUND_TASKS))) is not None:
                    task_name = await tasks.add(coro)
                    await tasks.join(task_name)
                    if tasks.failed(task_name):
                        logger.debug('One background tasks failed. continuing...')
                else:
                    logger.warning('No background tasks manager found; skipping scheduled task execution. The '
                                   'background tasks manager may just not have been initialized yet. If this keeps '
                                   'happening, however, there may be a problem.')

        task = asyncio.create_task(loop())
        yield
        task.cancel()
        await task
    return scheduler

scheduled_cleanup_ctx_factory = scheduled_cleanup_ctx


def _configure_logging_from_args(args: argparse.Namespace) -> None:
    """
    Configures logging according to command line arguments. It looks for args.logging and args.env to determine how
    to configure logging. If neither is specified, it uses the default logging configuration. If both are specified,
    args.logging takes precedence and reads from the specified logging configuration file. If only args.env is
    specified, it uses the logging configuration from the heaserver.service.logging module for the specified
    environment.

    :param args: the argparse.Namespace object returned by parsing command line arguments.
    """
    class LoggingConfigType(Enum):
        """Types of logging configuration sources."""
        FILE = 10
        ENV = 20
        DEFAULT = 30

    logging.setLoggerClass(ScrubbingLogger)
    logging_config_type = LoggingConfigType.DEFAULT
    if args.logging and os.path.isfile(args.logging):
        logging_config_type = LoggingConfigType.FILE
        logging.config.fileConfig(args.logging, disable_existing_loggers=False)
    elif args.env:
        logging_config_type = LoggingConfigType.ENV
        env = args.env.lower()
        if env == 'development':
            logging.config.dictConfig(DEBUG_LOG_CONFIG)
        elif env in ('staging', 'production'):
            logging.config.dictConfig(PROD_LOG_CONFIG)
        else:
            raise RuntimeError(f'Unreachable condition: unknown environment {args.env}')
    else:
        logging.config.dictConfig(DEBUG_LOG_CONFIG)

    logger = logging.getLogger(__name__)

    match logging_config_type:
        case LoggingConfigType.FILE:
            logger.info('Using logging configuration file %s', args.logging)
        case LoggingConfigType.ENV:
            logger.info('Using %s logging configuration', args.env)
        case LoggingConfigType.DEFAULT:
            logger.info('Using default logging configuration')

    if args.configuration:
        logger.info('Parsing HEA config file %s', args.configuration)
    else:
        logger.info('No HEA config file found')

    if args.logging and os.path.isfile(args.logging):
        logger.info('Parsing logging config file %s', args.logging)
    else:
        logger.info('No logging config file found')
