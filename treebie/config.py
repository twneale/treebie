

# ---------------------------------------------------------------------------
# Configure logging module.
# ---------------------------------------------------------------------------
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': "%(asctime)s %(levelname)s %(name)s: %(message)s",
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'default': {'level': 'DEBUG',
                    'class': 'treebie.log_config.ColorizingStreamHandler',
                    'formatter': 'standard'},
    },
    'loggers': {
        'treebie': {
            'handlers': ['default'], 'level': 'DEBUG', 'propagate': False
        },
    },
}