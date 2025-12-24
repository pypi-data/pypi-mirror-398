"""


gpu_extras submodule (gpu_extras.presets)
*****************************************

:func:`draw_circle_2d`

:func:`draw_texture_2d`

"""

import typing

import mathutils

import gpu

def draw_circle_2d(position: typing.Any, color: typing.Any, radius: float, *args, segments: int = None) -> None:

  """

  Draw a circle.

  """

  ...

def draw_texture_2d(texture: gpu.types.GPUTexture, position: mathutils.Vector, width: float, height: float, is_scene_linear_with_rec709_srgb_target: bool = False) -> None:

  """

  Draw a 2d texture.

  """

  ...
