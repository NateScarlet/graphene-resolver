"""Using mongoose-like schema to write apollo-like resolver for graphene.  """

__version__ = '0.1.2'
from .resolver import Resolver
from . import connection, typedef
from .schema import CONFIG_PROCESSOR
from .typedef import TYPENAME_PROCESSOR
