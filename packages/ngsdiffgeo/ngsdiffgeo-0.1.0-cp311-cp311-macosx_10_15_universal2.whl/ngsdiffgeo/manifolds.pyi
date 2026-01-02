from __future__ import annotations
from ngsdiffgeo.wrappers import TensorField
import ngsolve as ngsolve
from ngsolve.fem import Einsum
__all__: list = ['EuclideanMetric', 'Sphere2', 'Sphere3', 'PoincareDisk', 'HyperbolicH2', 'HyperbolicH3', 'Heisenberg', 'CigarSoliton', 'WarpedProduct', 'TestMetric']
class CigarSoliton:
    """
    
        Cigar soliton metric on R^2.
        
    """
    def __init__(self, t = 0):
        ...
class EuclideanMetric:
    """
    
        Euclidean metric on R^dim.
        
    """
    def __init__(self, dim = 2):
        ...
class Heisenberg:
    """
    
        Heisenberg metric on R^3. Has non-zero Ricci curvature.
        
    """
    def __init__(self):
        ...
class HyperbolicH2:
    """
    
        Hyperbolic metric on H2={(x,y) in R^2 : y > 0}. Has constant negative curvature.
        
    """
    def __init__(self):
        ...
class HyperbolicH3:
    """
    
        Hyperbolic metric on H3={(x,y,z) in R^3 : z > 0}. Has constant negative curvature.
        
    """
    def __init__(self):
        ...
class PoincareDisk:
    """
    
        Hyperbolic metric on the Poincare Disk B_1(0)= {(x,y) in R^2 : x^2+y^2 < 1}. Has constant negative curvature.
        
    """
    def __init__(self):
        ...
class Sphere2:
    """
    
        Standard metric on sphere S^2. x and y are interpreted as angles; x in [0,pi], y in [0,2*pi). Has constant positive curvature.
        
    """
    def __init__(self):
        ...
class Sphere3:
    """
    
        Standard metric on sphere S^3. x, y, and z are interpreted as angles; x in [0,pi], y in [0,pi], z in [0,2*pi). Has constant positive curvature.
        
    """
    def __init__(self):
        ...
class WarpedProduct:
    """
    
        Warped product metric on R^3.
        
    """
    def __init__(self):
        ...
def TestMetric(dim, order = 4):
    ...
