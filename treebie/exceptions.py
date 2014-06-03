class ChainMapUsageError(Exception):
    '''Raised if the ChainMap is used wrong.
    '''

class ConfigurationError(Exception):
    '''The user-defined ast models were screwed up.
    '''


class AmbiguousNodeNameError(Exception):
    '''Raised if the user was silly and used an
    ambiguous string reference to a node class.
    '''