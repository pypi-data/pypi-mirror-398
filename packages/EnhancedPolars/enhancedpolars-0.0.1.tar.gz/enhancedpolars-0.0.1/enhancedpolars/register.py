import inspect
import polars as pl
from typing import Callable, Iterable, Union, cast, Any

Obj = Union[pl.DataFrame, pl.LazyFrame]

from .merging import PolarsMerging
from .indexing import UniversalPolarsDataFrameIndexingExtension
from .io import PolarsIO
from .epl import EnhancedPolars
from .ml_pipeline import PolarsMLPipeline
from .interpolation import PolarsDataFrameInterpolationExtension
from .groupby import UniversalPolarsDataFrameGroupByExtension
from .Stats import PolarsStatsTests
from .series import * # Ensure series extensions are registered # type: ignore[import]
from .cohorts import PolarsCohorts
from .to_sql import PolarsSQLExtension


epl = EnhancedPolars()

def build_namespace(name: str, parts: Iterable[type]) -> type:
    """
    Create a namespace class by copying public callables and properties from parts.

    Methods receive `self._df` as the DataFrame/LazyFrame to operate on.
    Later parts override earlier ones on name conflicts.

    Parameters
    ----------
    name : str
        Name for the namespace (used for class naming).
    parts : iterable of type
        Collection of classes whose methods and properties will be combined
        into the namespace.

    Returns
    -------
    type
        A dynamically created namespace class containing methods and properties
        from all provided parts.

    Notes
    -----
    - Public methods and properties are copied from each class in parts
    - Static methods are excluded from the namespace
    - Later classes in the parts iterable override earlier ones for naming conflicts
    - All methods are wrapped to operate on self._df
    """
    namespace_dict = {}
    
    # Store the classes for initialization
    namespace_dict['_part_classes'] = parts

    def _wrap(func: Callable) -> Callable:
        def method(self, *args, **kwargs):
            # Find which class this function belongs to and call it on the proper instance
            for cls in parts:
                if hasattr(cls, func.__name__):
                    # Create a temporary instance of the specific class to call the method
                    temp_instance = cls(self._df)
                    return getattr(temp_instance, func.__name__)(*args, **kwargs)
            # Fallback: call the function directly on self
            return func(self, *args, **kwargs)
        method.__name__ = func.__name__
        method.__doc__ = func.__doc__
        return method
    
    def _wrap_property(cls, prop_name, prop: property) -> property:
        def getter(self):
            # Create a temporary instance to access the property
            temp_instance = cls(self._df)
            return getattr(temp_instance, prop_name)
        
        if prop.fset:
            def setter(self, value):
                temp_instance = cls(self._df)
                setattr(temp_instance, prop_name, value)
                self._df = temp_instance._data
            return property(getter, setter, prop.fdel, prop.__doc__)
        else:
            return property(getter, prop.fset, prop.fdel, prop.__doc__)

    for cls in parts:
        # Copy only instance methods (skip static methods)
        for name, member in inspect.getmembers(cls, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            
            # Check if it's a static method - if so, skip it
            class_attr = cls.__dict__.get(name)
            if isinstance(class_attr, staticmethod):
                # Skip static methods - they don't belong in DataFrame namespace
                continue
            else:
                # For instance methods, wrap normally
                namespace_dict[name] = _wrap(member)
        
        # Copy properties
        for prop_name, member in inspect.getmembers(cls, predicate=lambda x: isinstance(x, property)):
            if prop_name.startswith("_"):
                continue
            namespace_dict[prop_name] = _wrap_property(cls, prop_name, member)

    def __init__(self, df: Any):
        self._df = df
        
        # Initialize indexing accessors from PolarsIndexing
        from .indexing import LocAccessor, ILocAccessor, AtAccessor, IatAccessor
        self.loc = LocAccessor(self._df, namespace=self)
        self.iloc = ILocAccessor(self._df, namespace=self)
        self.at = AtAccessor(self._df, namespace=self)
        self.iat = IatAccessor(self._df, namespace=self)

    namespace_dict["__init__"] = __init__
    return type("EPLNamespace", (), namespace_dict)


EPLNamespace = build_namespace("epl", [PolarsDataFrameInterpolationExtension, UniversalPolarsDataFrameIndexingExtension, PolarsMerging, UniversalPolarsDataFrameGroupByExtension, PolarsIO, PolarsMLPipeline, PolarsStatsTests, PolarsCohorts, PolarsSQLExtension])

@pl.api.register_dataframe_namespace("epl")
@pl.api.register_lazyframe_namespace("epl")
class EPL(EPLNamespace):
    pass