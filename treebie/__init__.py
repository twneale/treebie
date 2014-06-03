"""Basic regex lexer implementation"""
# :copyright: (c) 2009 - 2012 Thom Neale and individual contributors,
#                 All rights reserved.
# :license:   BSD (3 Clause), see LICENSE for more details.
import logging.config

from treebie import config


VERSION = (0, 0, 0, '')
__version__ = '.'.join(str(p) for p in VERSION[0:3]) + ''.join(VERSION[3:])
__author__ = 'Thom Neale'
__contact__ = 'twneale@gmail.com'
__homepage__ = 'http://github.com/twneale/treebie'
__docformat__ = 'restructuredtext'


# Configure logging.
logging.config.dictConfig(config.LOGGING_CONFIG)


from treebie.node import Node
