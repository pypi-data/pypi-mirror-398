"""
High-level API für Espresso-Minimierung.
"""

import sys
from typing import List, Tuple, Optional
from sympy.logic.boolalg import And, Or, Not, to_dnf, BooleanFunction
from sympy import Symbol

try:
    from . import _espresso
    ESPRESSO_AVAILABLE = True
except ImportError:
    ESPRESSO_AVAILABLE = False


def to_cubes(expr: BooleanFunction, bvars) -> Tuple[List[Symbol], List[Tuple[str, int]]]:
    """
    Konvertiert SymPy Boolean Expression zu Cube-Liste.
    
    Args:
        expr: BooleanFunction (And/Or/Not/Symbol/True/False)
    
    Returns:
        (symbols, cubes) wo cubes = Liste von ("10-01", 1) tuples
    """
    
    # Zu DNF normalisieren
    expr = to_dnf(expr)

    print(expr)

    # Symbole extrahieren (sortiert für Konsistenz)
    symbols = sorted(expr.free_symbols, key=str)
    n_vars = len(symbols)

    print(expr.args)
    print(bvars)
    
    
    
    if n_vars == 0:
        # Konstante
        if expr is True:
            return symbols, [("-" * 0, 1)]  # Dummy
        else:
            return symbols, []
    
    cubes = []
    
    # DNF ist OR von AND-terms
    if isinstance(expr, Or):
        terms = expr.args
    else:
        terms = (expr,)
    
    for term in terms:
        # Extrahiere Literale aus AND-term
        if isinstance(term, And):
            lits = term.args
        elif isinstance(term, Symbol) or isinstance(term, Not):
            lits = (term,)
        else:
            continue
        
        # Baue Bit-String
        bits = ["-"] * n_vars
        for lit in lits:
            if isinstance(lit, Symbol):
                idx = symbols.index(lit)
                bits[idx] = "1"
            elif isinstance(lit, Not) and isinstance(lit.args, Symbol):
                idx = symbols.index(lit.args)
                bits[idx] = "0"
        
        cubes.append(("".join(bits), 1))
    sys.exit()
    
    return symbols, cubes


def from_cubes(symbols: List[Symbol], cubes: List[Tuple[str, int]]) -> BooleanFunction:
    """
    Konvertiert Cube-Liste zurück zu SymPy Expression.
    """
    
    terms = []
    for bits, output in cubes:
        if output != 1:
            continue
        
        lits = []
        for sym, bit in zip(symbols, bits):
            if bit == "1":
                lits.append(sym)
            elif bit == "0":
                lits.append(Not(sym))
            # "-" = don't care, weglassen
        
        if lits:
            terms.append(And(*lits))
    
    if not terms:
        return False
    
    return Or(*terms) if len(terms) > 1 else terms


def espresso_simplify(expr: BooleanFunction) -> BooleanFunction:
    """
    Minimiert einen Boolean-Ausdruck mit Espresso.
    
    Args:
        expr: SymPy Boolean Expression (And/Or/Not/Symbol)
    
    Returns:
        Minimierte Expression
    
    Raises:
        ImportError: Wenn Espresso-Extension nicht verfügbar
        TypeError: Wenn Ausdruck nicht unterstützt wird
    """
    if not ESPRESSO_AVAILABLE:
        raise ImportError(
            "Espresso minimizer not available. "
            "Install with: uv sync && uv build"
        )
    
    symbols, cubes = to_cubes(expr)
    
    if not cubes:
        return False
    
    # Rufe C-Extension auf
    cubes_min = _espresso.minimize(cubes, verbosity=0)
    
    # Konvertiere zurück
    return from_cubes(symbols, cubes_min)

