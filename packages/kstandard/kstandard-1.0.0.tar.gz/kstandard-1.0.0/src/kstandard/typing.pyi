"""
Module for type definitions and aliases.

This module provides various type aliases to facilitate clear and consistent
type hints. It primarily includes numerical types but may be extended to include
additional types and utilities in the future.
"""

#- Imports -----------------------------------------------------------------------------------------

from typing import Union


#- Alias: Numerics ---------------------------------------------------------------------------------

float2d_t: list[list[float]]
int2d_t  : list[list[int]]

int3d_t   : list[list[list[int]]]
float3d_t : list[list[list[float]]]

numeric_t : Union[float, int]
numeric2d_t : list[list[Union[float, int]]]
numeric3d_t : list[list[list[Union[float, int]]]]

