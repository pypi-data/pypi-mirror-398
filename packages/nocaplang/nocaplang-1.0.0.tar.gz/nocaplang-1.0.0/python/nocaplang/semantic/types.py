"""Type system for NoCapLang.

This module defines the type hierarchy and type operations for NoCapLang,
including type equality, compatibility checking, and type inference.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


# ============================================================================
# Base Type Class
# ============================================================================

class Type(ABC):
    """Base class for all types in NoCapLang."""
    
    @abstractmethod
    def __eq__(self, other) -> bool:
        """Check if two types are equal."""
        pass
    
    @abstractmethod
    def __hash__(self) -> int:
        """Return hash for type (needed for using types as dict keys)."""
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        """Return string representation of the type."""
        pass
    
    @abstractmethod
    def is_compatible_with(self, other: 'Type') -> bool:
        """Check if this type is compatible with another type.
        
        Compatibility is more permissive than equality - it allows for
        subtyping, type coercion, and generic type matching.
        """
        pass
    
    def is_subtype_of(self, other: 'Type') -> bool:
        """Check if this type is a subtype of another type."""
        return self.is_compatible_with(other)


# ============================================================================
# Primitive Types
# ============================================================================

@dataclass(frozen=True)
class PrimitiveType(Type):
    """Represents primitive types: text, digits, tf, void, ghost."""
    
    name: str  # "text", "digits", "tf", "void", "ghost"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, PrimitiveType):
            return False
        return self.name == other.name
    
    def __hash__(self) -> int:
        return hash(("PrimitiveType", self.name))
    
    def __str__(self) -> str:
        return self.name
    
    def is_compatible_with(self, other: Type) -> bool:
        """Check compatibility with another type.
        
        - ghost is compatible with any type (null can be assigned to anything)
        - Any type is compatible with itself
        """
        # ghost is compatible with any type
        if self.name == "ghost":
            return True
        
        if isinstance(other, PrimitiveType):
            # Any type is compatible with ghost
            if other.name == "ghost":
                return True
            return self.name == other.name
        return False


# Singleton instances for common primitive types
TEXT_TYPE = PrimitiveType("text")
DIGITS_TYPE = PrimitiveType("digits")
TF_TYPE = PrimitiveType("tf")
VOID_TYPE = PrimitiveType("void")
GHOST_TYPE = PrimitiveType("ghost")


# ============================================================================
# Collection Types
# ============================================================================

@dataclass(frozen=True)
class ArrayType(Type):
    """Represents lineup (array) types: lineup<T>."""
    
    element_type: Type
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ArrayType):
            return False
        return self.element_type == other.element_type
    
    def __hash__(self) -> int:
        return hash(("ArrayType", self.element_type))
    
    def __str__(self) -> str:
        return f"lineup<{self.element_type}>"
    
    def is_compatible_with(self, other: Type) -> bool:
        """Check compatibility with another type.
        
        Arrays are compatible if their element types are compatible.
        """
        if isinstance(other, ArrayType):
            return self.element_type.is_compatible_with(other.element_type)
        return False


@dataclass(frozen=True)
class MapType(Type):
    """Represents bag (map/dictionary) types: bag<K, V>."""
    
    key_type: Type
    value_type: Type
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, MapType):
            return False
        return (self.key_type == other.key_type and 
                self.value_type == other.value_type)
    
    def __hash__(self) -> int:
        return hash(("MapType", self.key_type, self.value_type))
    
    def __str__(self) -> str:
        return f"bag<{self.key_type}, {self.value_type}>"
    
    def is_compatible_with(self, other: Type) -> bool:
        """Check compatibility with another type.
        
        Maps are compatible if their key and value types are compatible.
        """
        if isinstance(other, MapType):
            return (self.key_type.is_compatible_with(other.key_type) and
                    self.value_type.is_compatible_with(other.value_type))
        return False


# ============================================================================
# Function Types
# ============================================================================

@dataclass(frozen=True)
class FunctionType(Type):
    """Represents function types: (param_types) -> return_type."""
    
    param_types: tuple[Type, ...]  # Use tuple for immutability
    return_type: Type
    is_async: bool = False
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, FunctionType):
            return False
        return (self.param_types == other.param_types and
                self.return_type == other.return_type and
                self.is_async == other.is_async)
    
    def __hash__(self) -> int:
        return hash(("FunctionType", self.param_types, self.return_type, self.is_async))
    
    def __str__(self) -> str:
        params = ", ".join(str(p) for p in self.param_types)
        async_prefix = "chill " if self.is_async else ""
        return f"{async_prefix}({params}) -> {self.return_type}"
    
    def is_compatible_with(self, other: Type) -> bool:
        """Check compatibility with another type.
        
        Functions are compatible if:
        - They have the same number of parameters
        - Parameter types are compatible (contravariant)
        - Return types are compatible (covariant)
        - Async status matches
        """
        if isinstance(other, FunctionType):
            if len(self.param_types) != len(other.param_types):
                return False
            if self.is_async != other.is_async:
                return False
            
            # Check parameter types (contravariant)
            for self_param, other_param in zip(self.param_types, other.param_types):
                if not other_param.is_compatible_with(self_param):
                    return False
            
            # Check return type (covariant)
            return self.return_type.is_compatible_with(other.return_type)
        return False


# ============================================================================
# Class Types
# ============================================================================

@dataclass
class ClassType(Type):
    """Represents user-defined class types."""
    
    name: str
    fields: Dict[str, Type]
    methods: Dict[str, FunctionType]
    parent: Optional['ClassType'] = None
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, ClassType):
            return False
        # Classes are equal if they have the same name
        # (nominal typing, not structural)
        return self.name == other.name
    
    def __hash__(self) -> int:
        return hash(("ClassType", self.name))
    
    def __str__(self) -> str:
        if self.parent:
            return f"{self.name} vibes_with {self.parent.name}"
        return self.name
    
    def is_compatible_with(self, other: Type) -> bool:
        """Check compatibility with another type.
        
        A class is compatible with another if:
        - They are the same class
        - This class is a subclass of the other
        - Other is a TypeVariable with the same name
        """
        if isinstance(other, ClassType):
            # Check if same class
            if self.name == other.name:
                return True
            
            # Check if this is a subclass of other
            current = self.parent
            while current is not None:
                if current.name == other.name:
                    return True
                current = current.parent
            
            return False
        
        # Check if other is a TypeVariable with matching name
        if isinstance(other, TypeVariable):
            return self.name == other.name
        
        return False
    
    def get_field(self, name: str) -> Optional[Type]:
        """Get the type of a field, checking parent classes if needed."""
        if name in self.fields:
            return self.fields[name]
        if self.parent:
            return self.parent.get_field(name)
        return None
    
    def get_method(self, name: str) -> Optional[FunctionType]:
        """Get a method, checking parent classes if needed."""
        if name in self.methods:
            return self.methods[name]
        if self.parent:
            return self.parent.get_method(name)
        return None
    
    def has_circular_inheritance(self) -> bool:
        """Check if this class has circular inheritance."""
        visited = set()
        current = self
        while current is not None:
            if current.name in visited:
                return True
            visited.add(current.name)
            current = current.parent
        return False


# ============================================================================
# Union Types
# ============================================================================

@dataclass(frozen=True)
class UnionType(Type):
    """Represents union types for pattern matching: T1 | T2 | ... | Tn."""
    
    types: tuple[Type, ...]  # Use tuple for immutability
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, UnionType):
            return False
        # Union types are equal if they contain the same types (order doesn't matter)
        return set(self.types) == set(other.types)
    
    def __hash__(self) -> int:
        return hash(("UnionType", frozenset(self.types)))
    
    def __str__(self) -> str:
        return " | ".join(str(t) for t in self.types)
    
    def is_compatible_with(self, other: Type) -> bool:
        """Check compatibility with another type.
        
        A union type is compatible with another type if:
        - The other type is a union and all types in this union are compatible
          with at least one type in the other union
        - The other type is not a union and all types in this union are
          compatible with it
        """
        if isinstance(other, UnionType):
            # All types in self must be compatible with at least one type in other
            for self_type in self.types:
                if not any(self_type.is_compatible_with(other_type) 
                          for other_type in other.types):
                    return False
            return True
        else:
            # All types in self must be compatible with other
            return all(t.is_compatible_with(other) for t in self.types)
    
    def contains_type(self, type_to_check: Type) -> bool:
        """Check if this union contains a specific type."""
        return any(t == type_to_check for t in self.types)


# ============================================================================
# Generic Type Variables
# ============================================================================

@dataclass
class TypeVariable(Type):
    """Represents a generic type variable (e.g., T in lineup<T>)."""
    
    name: str
    constraints: Optional[List[Type]] = None  # Optional type constraints
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, TypeVariable):
            return False
        return self.name == other.name
    
    def __hash__(self) -> int:
        return hash(("TypeVariable", self.name))
    
    def __str__(self) -> str:
        if self.constraints:
            constraints_str = " | ".join(str(c) for c in self.constraints)
            return f"{self.name}: {constraints_str}"
        return self.name
    
    def is_compatible_with(self, other: Type) -> bool:
        """Check compatibility with another type.
        
        A type variable is compatible with:
        - Another type variable with the same name
        - Any type if no constraints
        - Any type that satisfies the constraints
        """
        if isinstance(other, TypeVariable):
            return self.name == other.name
        
        # If no constraints, compatible with any type
        if not self.constraints:
            return True
        
        # Check if other satisfies any constraint
        return any(other.is_compatible_with(constraint) 
                  for constraint in self.constraints)


# ============================================================================
# Type Utilities
# ============================================================================

class TypeUnifier:
    """Handles type unification for generic types."""
    
    def __init__(self):
        self.substitutions: Dict[str, Type] = {}
    
    def unify(self, type1: Type, type2: Type) -> bool:
        """Attempt to unify two types, updating substitutions.
        
        Returns True if unification succeeds, False otherwise.
        """
        # If types are equal, unification succeeds
        if type1 == type2:
            return True
        
        # Handle type variables
        if isinstance(type1, TypeVariable):
            return self._unify_variable(type1, type2)
        if isinstance(type2, TypeVariable):
            return self._unify_variable(type2, type1)
        
        # Handle array types
        if isinstance(type1, ArrayType) and isinstance(type2, ArrayType):
            return self.unify(type1.element_type, type2.element_type)
        
        # Handle map types
        if isinstance(type1, MapType) and isinstance(type2, MapType):
            return (self.unify(type1.key_type, type2.key_type) and
                   self.unify(type1.value_type, type2.value_type))
        
        # Handle function types
        if isinstance(type1, FunctionType) and isinstance(type2, FunctionType):
            if len(type1.param_types) != len(type2.param_types):
                return False
            if type1.is_async != type2.is_async:
                return False
            
            # Unify parameter types
            for p1, p2 in zip(type1.param_types, type2.param_types):
                if not self.unify(p1, p2):
                    return False
            
            # Unify return type
            return self.unify(type1.return_type, type2.return_type)
        
        # Types cannot be unified
        return False
    
    def _unify_variable(self, var: TypeVariable, type_: Type) -> bool:
        """Unify a type variable with a type."""
        # Check if variable already has a substitution
        if var.name in self.substitutions:
            return self.unify(self.substitutions[var.name], type_)
        
        # Check if type is a type variable with a substitution
        if isinstance(type_, TypeVariable) and type_.name in self.substitutions:
            return self.unify(var, self.substitutions[type_.name])
        
        # Check constraints
        if var.constraints:
            if not any(type_.is_compatible_with(constraint) 
                      for constraint in var.constraints):
                return False
        
        # Check for occurs check (prevent infinite types)
        if self._occurs_in(var, type_):
            return False
        
        # Add substitution
        self.substitutions[var.name] = type_
        return True
    
    def _occurs_in(self, var: TypeVariable, type_: Type) -> bool:
        """Check if a type variable occurs in a type (occurs check)."""
        if isinstance(type_, TypeVariable):
            if var.name == type_.name:
                return True
            if type_.name in self.substitutions:
                return self._occurs_in(var, self.substitutions[type_.name])
            return False
        
        if isinstance(type_, ArrayType):
            return self._occurs_in(var, type_.element_type)
        
        if isinstance(type_, MapType):
            return (self._occurs_in(var, type_.key_type) or
                   self._occurs_in(var, type_.value_type))
        
        if isinstance(type_, FunctionType):
            for param_type in type_.param_types:
                if self._occurs_in(var, param_type):
                    return True
            return self._occurs_in(var, type_.return_type)
        
        return False
    
    def apply_substitutions(self, type_: Type) -> Type:
        """Apply all substitutions to a type."""
        if isinstance(type_, TypeVariable):
            if type_.name in self.substitutions:
                return self.apply_substitutions(self.substitutions[type_.name])
            return type_
        
        if isinstance(type_, ArrayType):
            return ArrayType(self.apply_substitutions(type_.element_type))
        
        if isinstance(type_, MapType):
            return MapType(
                self.apply_substitutions(type_.key_type),
                self.apply_substitutions(type_.value_type)
            )
        
        if isinstance(type_, FunctionType):
            return FunctionType(
                tuple(self.apply_substitutions(p) for p in type_.param_types),
                self.apply_substitutions(type_.return_type),
                type_.is_async
            )
        
        return type_


def parse_type_annotation(annotation: str) -> Type:
    """Parse a type annotation string into a Type object.
    
    Examples:
        "text" -> PrimitiveType("text")
        "lineup<digits>" -> ArrayType(PrimitiveType("digits"))
        "bag<text, digits>" -> MapType(PrimitiveType("text"), PrimitiveType("digits"))
    """
    annotation = annotation.strip()
    
    # Handle primitive types
    if annotation in ("text", "digits", "tf", "void", "ghost"):
        return PrimitiveType(annotation)
    
    # Handle generic types
    if "<" in annotation:
        base_type = annotation[:annotation.index("<")]
        generic_part = annotation[annotation.index("<") + 1:annotation.rindex(">")]
        
        if base_type == "lineup":
            element_type = parse_type_annotation(generic_part)
            return ArrayType(element_type)
        
        elif base_type == "bag":
            # Split by comma, handling nested generics
            parts = _split_generic_params(generic_part)
            if len(parts) != 2:
                raise ValueError(f"bag type requires exactly 2 type parameters, got {len(parts)}")
            key_type = parse_type_annotation(parts[0])
            value_type = parse_type_annotation(parts[1])
            return MapType(key_type, value_type)
    
    # If we can't parse it, treat it as a type variable or class name
    # This will be resolved during semantic analysis
    return TypeVariable(annotation)


def _split_generic_params(params: str) -> List[str]:
    """Split generic parameters by comma, respecting nested brackets."""
    result = []
    current = []
    depth = 0
    
    for char in params:
        if char == '<':
            depth += 1
            current.append(char)
        elif char == '>':
            depth -= 1
            current.append(char)
        elif char == ',' and depth == 0:
            result.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    
    if current:
        result.append(''.join(current).strip())
    
    return result
