from importlib.metadata import version

from .error import UnicatError  # noqa: F401
from .transform import UnicatTransform  # noqa: F401
from .unicat import Unicat  # noqa: F401

__version__ = version("unicat")
