from __future__ import annotations
import ngsolve.comp
import ngsolve.fem
__all__: list[str] = ['Alternation', 'GradCF', 'GradProxy', 'KForm', 'MakeTensorField', 'MakeVectorField', 'OneForm', 'RiemannianManifold', 'ScalarField', 'TensorField', 'TensorProduct', 'ThreeForm', 'TwoForm', 'VectorField', 'Wedge', 'd', 'delta', 'star']
class Alternation(ngsolve.fem.CoefficientFunction):
    def __init__(self, cf: ngsolve.fem.CoefficientFunction, rank: int, dim: int) -> None:
        ...
    @property
    def dim(self) -> int:
        ...
    @property
    def rank(self) -> int:
        ...
class GradProxy(ngsolve.comp.ProxyFunction):
    pass
class KForm(TensorField):
    def __init__(self, cf: ngsolve.fem.CoefficientFunction, k: int, dim: int) -> None:
        ...
    def d(self) -> KForm:
        ...
    def star(self, M: RiemannianManifold, vb: ngsolve.comp.VorB = ...) -> KForm:
        ...
    def wedge(self, b: KForm) -> KForm:
        ...
    @property
    def coef(self) -> ngsolve.fem.CoefficientFunction:
        ...
    @property
    def degree(self) -> int:
        ...
    @property
    def dim_space(self) -> int:
        ...
class OneForm(KForm):
    @staticmethod
    def from_cf(cf: ngsolve.fem.CoefficientFunction) -> OneForm:
        ...
    def __init__(self, cf: ngsolve.fem.CoefficientFunction) -> None:
        ...
class RiemannianManifold:
    def Christoffel(self, second_kind: bool = False) -> ngsolve.fem.CoefficientFunction:
        """
        return the Christoffel symbol of the first or second kind
        """
    def Contraction(self, tf: ..., vf: ..., slot: int = 0) -> ...:
        """
        Contraction of TensorField with a VectorField at given slot. Default slot is the first.
        """
    def CovCurl(self, tf: ...) -> ...:
        """
        Covariant curl of a TensorField in 3D
        """
    def CovDef(self, tf: ...) -> ...:
        """
        Covariant Def (symmetric derivative) of a 1-form
        """
    def CovDeriv(self, tf: ..., vb: ngsolve.comp.VorB = ...) -> ...:
        """
        Covariant derivative of a TensorField
        """
    def CovDiv(self, tf: ..., vb: ngsolve.comp.VorB = ...) -> ...:
        """
        Covariant divergence of a TensorField
        """
    def CovEin(self, tf: ...) -> ...:
        """
        Covariant ein of a TensorField in 2D or 3D
        """
    def CovHesse(self, tf: ...) -> ...:
        """
        Covariant Hessian of a TensorField.
        """
    def CovInc(self, tf: ..., matrix: bool = False) -> ...:
        """
        Covariant inc of a TensorField. If matrix=True a scalar in 2D and matrix in 3D is returned
        """
    def CovLaplace(self, tf: ...) -> ...:
        """
        Covariant Laplace of a TensorField 
        """
    def CovRot(self, tf: ...) -> ...:
        """
        Covariant rot of a TensorField of maximal order 1 in 2D. Returns a contravariant tensor field.
        """
    def Cross(self, tf1: ..., tf2: ...) -> ...:
        """
        Cross product in 3D of two vector fields, 1-forms, or both mixed. Returns the resulting vector-field.
        """
    def InnerProduct(self, tf1: ..., tf2: ..., vb: ngsolve.comp.VorB = ...) -> ...:
        """
        InnerProduct of two TensorFields
        """
    def J(self, tf: ..., vb: ngsolve.comp.VorB = ...) -> ...:
        """
        J operator subtracting half the trace.
        """
    def KForm(self, cf: ngsolve.fem.CoefficientFunction, k: int) -> ...:
        """
        Wrap a CoefficientFunction as a k-form using the manifold dimension
        """
    def LeviCivitaSymbol(self, covariant: bool = False) -> ...:
        """
        return the Levi-Civita symbol
        """
    def LichnerowiczLaplacian(self, tf: ...) -> ...:
        """
        Lichnerowicz Laplacian of a TensorField
        """
    def Lower(self, tf: ..., index: int = 0) -> ...:
        """
        Lower a tensor index using the manifold metric
        """
    def Raise(self, tf: ..., index: int = 0) -> ...:
        """
        Raise a tensor index using the manifold metric
        """
    def S(self, tf: ..., vb: ngsolve.comp.VorB = ...) -> ...:
        """
        S operator subtracting the trace.
        """
    def Trace(self, tf: ..., vb: ngsolve.comp.VorB = ..., index1: int = 0, index2: int = 1) -> ...:
        """
        Trace of TensorField in two indices. Default are the first two.
        """
    def Transpose(self, tf: ..., index1: int = 0, index2: int = 1) -> ...:
        """
        Transpose of TensorField for given indices. Default indices are first and second.
        """
    def VolumeForm(self, vb: ngsolve.comp.VorB) -> ngsolve.fem.CoefficientFunction:
        """
        return the volume form of given dimension
        """
    def __init__(self, metric: ngsolve.fem.CoefficientFunction) -> None:
        """
        constructor
        """
    def delta(self, a: ...) -> ...:
        """
        Exterior coderivative of a k-form using the manifold metric
        """
    def star(self, a: ..., vb: ngsolve.comp.VorB = ...) -> ...:
        """
        Hodge star of a k-form using the manifold metric
        """
    @property
    def Curvature(self) -> ...:
        """
        return the curvature operator
        """
    @property
    def Einstein(self) -> ...:
        """
        return the Einstein tensor
        """
    @property
    def G(self) -> ngsolve.fem.CoefficientFunction:
        """
        return the metric tensor
        """
    @property
    def G_deriv(self) -> ngsolve.fem.CoefficientFunction:
        """
        return the derivative of the metric tensor
        """
    @property
    def G_inv(self) -> ngsolve.fem.CoefficientFunction:
        """
        return the inverse of the metric tensor
        """
    @property
    def Gauss(self) -> ...:
        """
        return the Gauss curvature in 2D
        """
    @property
    def GeodesicCurvature(self) -> ...:
        """
        return the geodesic curvature
        """
    @property
    def MeanCurvature(self) -> ...:
        """
        return the mean curvature
        """
    @property
    def Ricci(self) -> ...:
        """
        return the Ricci tensor
        """
    @property
    def Riemann(self) -> ...:
        """
        return the Riemann curvature tensor
        """
    @property
    def SFF(self) -> ...:
        """
        return the second fundamental form
        """
    @property
    def Scalar(self) -> ...:
        """
        return the scalar curvature
        """
    @property
    def dim(self) -> int:
        """
        return the manifold dimension
        """
    @property
    def normal(self) -> ...:
        """
        return the normal vector
        """
    @property
    def tangent(self) -> ...:
        """
        return the tangent vector
        """
class ScalarField(KForm):
    @staticmethod
    def from_cf(cf: ngsolve.fem.CoefficientFunction, dim: int = -1) -> ScalarField:
        ...
    def __init__(self, cf: ngsolve.fem.CoefficientFunction, dim: int = -1) -> None:
        ...
class TensorField(ngsolve.fem.CoefficientFunction):
    @staticmethod
    def from_cf(cf: ngsolve.fem.CoefficientFunction, covariant_indices: str) -> TensorField:
        ...
    def __init__(self, cf: ngsolve.fem.CoefficientFunction, covariant_indices: str) -> None:
        ...
    @property
    def coef(self) -> ngsolve.fem.CoefficientFunction:
        ...
    @property
    def covariant_indices(self) -> str:
        ...
class ThreeForm(KForm):
    @staticmethod
    def from_cf(cf: ngsolve.fem.CoefficientFunction, dim: int = -1) -> ThreeForm:
        ...
    def __init__(self, cf: ngsolve.fem.CoefficientFunction, dim: int = -1) -> None:
        ...
class TwoForm(KForm):
    @staticmethod
    def from_cf(cf: ngsolve.fem.CoefficientFunction, dim: int = -1) -> TwoForm:
        ...
    def __init__(self, cf: ngsolve.fem.CoefficientFunction, dim: int = -1) -> None:
        ...
class VectorField(TensorField):
    @staticmethod
    def from_cf(cf: ngsolve.fem.CoefficientFunction) -> VectorField:
        ...
    def __init__(self, cf: ngsolve.fem.CoefficientFunction) -> None:
        ...
def GradCF(arg0: ngsolve.fem.CoefficientFunction, arg1: int) -> ngsolve.fem.CoefficientFunction:
    """
    Create a GradientCoefficientFunction. Uses numerical differentiation to compute the gradient of a given CoefficientFunction
    """
def MakeTensorField(arg0: ngsolve.fem.CoefficientFunction, arg1: str) -> TensorField:
    ...
def MakeVectorField(arg0: ngsolve.fem.CoefficientFunction) -> VectorField:
    ...
def TensorProduct(a: TensorField, b: TensorField) -> TensorField:
    ...
def Wedge(a: KForm, b: KForm) -> KForm:
    ...
def d(a: KForm) -> KForm:
    ...
def delta(a: KForm, M: RiemannianManifold) -> KForm:
    ...
def star(a: KForm, M: RiemannianManifold, vb: ngsolve.comp.VorB = ...) -> KForm:
    ...
