"""


Geometry Operators
******************

:func:`attribute_add`

:func:`attribute_convert`

:func:`attribute_remove`

:func:`color_attribute_add`

:func:`color_attribute_convert`

:func:`color_attribute_duplicate`

:func:`color_attribute_remove`

:func:`color_attribute_render_set`

:func:`geometry_randomization`

"""

import typing

def attribute_add(*args, name: str = '', domain: str = 'POINT', data_type: str = 'FLOAT') -> None:

  """

  Add attribute to geometry

  """

  ...

def attribute_convert(*args, mode: str = 'GENERIC', domain: str = 'POINT', data_type: str = 'FLOAT') -> None:

  """

  Change how the attribute is stored

  """

  ...

def attribute_remove() -> None:

  """

  Remove attribute from geometry

  """

  ...

def color_attribute_add(*args, name: str = '', domain: str = 'POINT', data_type: str = 'FLOAT_COLOR', color: typing.Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)) -> None:

  """

  Add color attribute to geometry

  """

  ...

def color_attribute_convert(*args, domain: str = 'POINT', data_type: str = 'FLOAT_COLOR') -> None:

  """

  Change how the color attribute is stored

  """

  ...

def color_attribute_duplicate() -> None:

  """

  Duplicate color attribute

  """

  ...

def color_attribute_remove() -> None:

  """

  Remove color attribute from geometry

  """

  ...

def color_attribute_render_set(*args, name: str = 'Color') -> None:

  """

  Set default color attribute used for rendering

  """

  ...

def geometry_randomization(*args, value: bool = False) -> None:

  """

  Toggle geometry randomization for debugging purposes

  """

  ...
