from .species import Species
from .co import CO
from .h2o import H2O
from .co2 import CO2
from .h2 import H2
from .c2h4 import C2H4
from .ch4 import CH4
from .n2 import N2
from .nh3 import NH3
from .ar import Ar
from .inert import Inert
from .o2 import O2
from .graphite import Graphite
from .ch3oh import CH3OH
from .c2h6 import C2H6
from .c3h6 import C3H6
from .c3h8 import C3H8
from .c4h10 import C4H10
from .c4h8 import C4H8
from .c5h10 import C5H10
from .c5h12 import C5H12
from .dme import DME

# Build a case-insensitive mapping of class names to class objects for only those imported here
import inspect

CLASS_MAP = {}
for name, obj in list(locals().items()):
    if inspect.isclass(obj):
        CLASS_MAP[name.lower()] = obj


def get_dict_from_list(comp_list):
    return {comp_id: CLASS_MAP[comp_id] for comp_id in comp_list}
