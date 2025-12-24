from .main import add
from .main import remove
from .main import e
from .main import pi
from .main import sqrt
from .main import pow
from .geometry import squareArea
from .geometry import rectArea
from .geometry import circleArea
from .geometry import triangleArea
from .main import dot
from .main import divide
from .main import multiply
from .main import zeta
from .main import sigma
from .main import sigma_range
from .main import y
from .main import l
from .main import k
from .main import g
from .main import delta
from .main import a
from .main import value
from .rands import rand
randfloat=rand.randfloat
randint=rand.randint
randnp = rand.randnp
__version__ = "0.0.8"
__all__ = ["add","remove","e","pi","zeta","k","l","g","a",
           "delta","value","y","sigma_range","sigma","sqrt",
           "pow","circleArea","rectArea","squareArea","dot","divide",
           "multiply","rand","randfloat","randint","randnp","triangleArea"
           ]