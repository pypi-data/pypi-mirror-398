import logging
import os


class EnergyBaseFilter(logging.Filter):
    BASE_DIR = os.getcwd()

    def filter(self, record):
        sp = '/site-packages/'
        path = record.pathname

        if record.pathname.startswith(str(self.BASE_DIR)):
            path = record.pathname[len(str(self.BASE_DIR)):]
        elif sp in path:
            path = path[path.index(sp, 0) + len(sp):]

        path = path.replace('/', '.')
        path = path.removeprefix('.')
        record.path = path
        return record


class EnergyBaseLogging:
    enable_file = int(os.environ.get('LOGGING_FILE', False))
    enable_console_info = int(os.environ.get('LOGGING_CONSOLE_INFO', True))
    enable_db_debug = int(os.environ.get('LOGGING_DB_DEBUG', False))
    enable_loki = int(os.environ.get('LOGGING_LOKI', True))
    enable_loki_debug = int(os.environ.get('LOGGING_LOKI_DEBUG', False))

    logger = logging.getLogger('main')

    format = '[%(asctime)s] %(levelname)s [%(path)s:%(lineno)s] [%(funcName)s] %(message)s'

    __LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'filters': {
            'trim_path': {
                '()': 'energy_base.logging.EnergyBaseFilter',
            },
        },
        'formatters': {
            'simple': {
                'format': format,
                'datefmt': '%Y-%m-%d %H:%M:%S',
            },
            'loki': {
                'class': 'django_loki.LokiFormatter',  # required
                'format': format,  # optional, default is logging.BASIC_FORMAT
                'datefmt': '%Y-%m-%d %H:%M:%S',  # optional, default is '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'file': {
                'level': 'ERROR',
                'class': 'logging.FileHandler',
                'filename': 'logs/django-error.log',
                'formatter': 'simple',
                'filters': ['trim_path'],
            },
            'console_info': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'filters': ['trim_path'],
            },
            'console_debug': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
                'filters': ['trim_path'],
            },
            'loki': {
                'level': os.environ.get('LOKI_LEVEL', 'ERROR'),  # required
                'class': 'django_loki.LokiHttpHandler',  # required
                'host': os.environ.get('LOKI_HOST', os.environ.get('DB_HOST')),
                # required, your grafana/Loki server host, e.g:192.168.25.30
                'formatter': 'loki',  # required, loki formatter,
                'port': int(os.environ.get('LOKI_PORT', 3100)),
                # optional, your grafana/Loki server port, default is 3100
                'timeout': float(os.environ.get('LOKI_TIMEOUT', 0.5)),
                # optional, request Loki-server by http or https time out, default is 0.5
                'protocol': os.environ.get('LOKI_PROTOCOL', 'http'),
                # optional, Loki-server protocol, default is http
                'source': os.environ.get('LOKI_SOURCE', 'Loki'),  # optional, label name for Loki, default is Loki
                'src_host': os.environ.get('LOKI_SRC_HOST', 'localhost'),
                # optional, label name for Loki, default is localhost
                'tz': 'Asia/Tashkent',
                # optional, timezone for formatting timestamp, default is UTC, e.g:Asia/Shanghai
                'filters': ['trim_path'],
            },
        },
        'loggers': {
            'django': {
                'handlers': [],
                'level': 'DEBUG',
                'propagate': True,
            },
            'django.db.backends': {
                'handlers': [],
                'level': 'DEBUG',
                'propagate': True,
            },
            'main': {
                'handlers': [],
                'level': 'DEBUG',
                'propagate': True,
            }
        },
    }

    # noinspection PyUnresolvedReferences
    @classmethod
    def logging(cls):
        _logging = cls.__LOGGING.copy()

        if cls.enable_file:
            _logging['loggers']['django']['handlers'].append('file')
        if cls.enable_console_info:
            _logging['loggers']['django']['handlers'].append('console_info')
        if cls.enable_db_debug:
            _logging['loggers']['django.db.backends']['handlers'].append('console_debug')
        if cls.enable_loki:
            _logging['loggers']['django']['handlers'].append('loki')
        if cls.enable_loki_debug:
            _logging['handlers']['loki_debug'] = _logging['handlers']['loki'].copy()
            _logging['handlers']['loki_debug']['level'] = 'DEBUG'
            _logging['loggers']['main']['handlers'].append('loki_debug')
            _logging['loggers']['main']['handlers'].append('console_debug')

        return _logging


LOGGING = EnergyBaseLogging.logging()
logger = EnergyBaseLogging.logger
