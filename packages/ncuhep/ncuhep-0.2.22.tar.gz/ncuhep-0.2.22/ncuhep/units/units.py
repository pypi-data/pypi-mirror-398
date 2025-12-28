import numpy as np
from scipy import constants as const
from itertools import permutations

TAU = 2 * const.pi  # full turn in radians (τ)

# -------------------------------------------------------------------
# Dimension / Registry core
# -------------------------------------------------------------------


def _normalize_sig(sig: dict) -> tuple:
    """Normalize a signature dict into a sorted, hashable tuple."""
    return tuple(sorted((k, int(v)) for k, v in sig.items() if v != 0))


def _add_sig(a: dict, b: dict, sgn=1) -> dict:
    """Combine dimension signatures: a + sgn*b."""
    out = dict(a)
    for k, v in b.items():
        out[k] = out.get(k, 0) + sgn * v
        if out[k] == 0:
            out.pop(k)
    return out


# The registry maps normalized signatures -> concrete classes
_DERIVED_REGISTRY = {}


def register_derived(cls):
    """Class decorator to register a derived quantity by its SIG."""
    key = _normalize_sig(cls.SIG)
    _DERIVED_REGISTRY[key] = cls
    return cls


# -------------------------------------------------------------------
# Unit base class
# -------------------------------------------------------------------


class Unit:
    """
    Stores values in SI; attribute-based set/get via a conversions dict.

    Each Unit instance carries a dimension signature (SIG) and participates in
    dimensional arithmetic. If the result's signature matches a registered
    derived class, that class is used; otherwise a GenericQuantity is returned.

    Helpful APIs:
    -------------
    - obj.available_units(...)
        With no args: list all attribute names (e.g. ['m', 'cm', ...]).
        With args: filter names whose tokens contain all requested strings.
    - dir(obj)
        Includes all unit names, so IDE tab-completion can show them
        (for tools that honor __dir__).
    """

    # override in subclasses, e.g. {'L':1}, {'T':1}, etc.
    SIG = {}

    def __init__(self, conversions: dict, si_unit: str, sig: dict = None):
        # conversions: mapping "attr_name" -> factor to SI
        self._conversions = dict(conversions)
        self._si_unit = si_unit
        # instance dimension signature (default = class SIG)
        self._sig = dict(self.SIG if sig is None else sig)
        self._Unit__value_si = 0.0  # scalar or np.ndarray

    # -------------------------
    # Unit-name resolution (incl. permutations)
    # -------------------------

    def _resolve_unit_name(self, name: str):
        """
        Try to resolve a possibly out-of-order compound unit name
        (e.g. 'count_s_m2_sr') to a known key in _conversions
        (e.g. 'count_m2_s_sr') by trying permutations of the tokens.

        Returns the canonical key if found, else None.
        """
        conv = getattr(self, "_conversions", None)
        if conv is None:
            return None

        # Exact hit?
        if name in conv:
            return name

        # Only bother if it looks compound
        if "_" not in name:
            return None

        parts = name.split("_")

        # Avoid combinatorial explosion when trying permutations
        if len(parts) > 6:
            return None

        seen = set()
        for perm in permutations(parts):
            cand = "_".join(perm)
            if cand in seen:
                continue
            seen.add(cand)
            if cand in conv:
                return cand

        return None

    # -------------------------
    # Attribute set/get for units
    # -------------------------

    def __setattr__(self, name, value):
        # Once _conversions exists, interpret matching attributes as unit setters
        if "_conversions" in self.__dict__:
            # Direct hit
            if name in self._conversions:
                arr = np.asarray(value, dtype=float)
                object.__setattr__(
                    self,
                    "_Unit__value_si",
                    arr * self._conversions[name],
                )
                return

            # Try permutations / alias resolution
            alt = self._resolve_unit_name(name)
            if alt is not None:
                arr = np.asarray(value, dtype=float)
                object.__setattr__(
                    self,
                    "_Unit__value_si",
                    arr * self._conversions[alt],
                )
                return

        # Fallback: normal attribute
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        # Only called if normal attribute lookup fails
        if "_conversions" in self.__dict__:
            # Direct hit?
            if name in self._conversions:
                return self._Unit__value_si / self._conversions[name]

            # Try permutations / alias resolution
            alt = self._resolve_unit_name(name)
            if alt is not None:
                return self._Unit__value_si / self._conversions[alt]

        raise AttributeError(f"'{self.__class__.__name__}' has no unit '{name}'")

    # Helpers

    def _get_value_si(self):
        return self._Unit__value_si

    @property
    def value(self):
        """
        Return the raw SI value (float or ndarray).
        For dimensionless quantities, this is the plain numeric value.
        """
        return self._Unit__value_si

    @property
    def unit(self):
        """
        Return a human-readable dimensional signature string,
        showing numerator/denominator units.
        """
        num = []
        den = []
        # base_syms includes 7 SI bases + our extra ones (solid angle, counts)
        base_syms = {
            'M': 'kg',
            'L': 'm',
            'T': 's',
            'I': 'A',
            'Θ': 'K',
            'n': 'mol',
            'J': 'cd',
            'Ω': 'sr',
            'N': 'count',
        }
        for k, exp in self._sig.items():
            u = base_syms.get(k, k)
            if exp > 0:
                if exp == 1:
                    num.append(u)
                else:
                    num.append(f"{u}^{exp}")
            elif exp < 0:
                if exp == -1:
                    den.append(u)
                else:
                    den.append(f"{u}^{-exp}")
        if not num:
            num = ["1"]
        if den:
            return " · ".join(num) + " / " + "·".join(den)
        else:
            return " · ".join(num)

    def available_units(self, *must_have):
        """
        Return a sorted list of unit attribute names.

        - With no arguments: return all available unit names.
        - With one or more string arguments: return only those unit names
          whose token set contains *all* of the given strings.

        Tokens are:
          - the pieces split by '_', e.g. 'kg_m2_s' -> ['kg', 'm2', 's']
          - plus the same pieces with trailing digits stripped, e.g. 'm2' -> 'm'

        Example
        -------
        Q.available_units("kg", "m")
            -> all names whose tokens include both 'kg' and 'm'
               e.g. ['kg_m', 'kg_m2', 'kg_m2_s', ...]
        """
        names = list(self._conversions.keys())

        # No filter: return everything
        if not must_have:
            return sorted(names)

        # Build a token set for each unit name
        def _tokens(name: str):
            parts = name.split("_")
            toks = set()
            for p in parts:
                if not p:
                    continue
                # full token
                toks.add(p)
                # base name with trailing digits stripped, e.g. 'm2' -> 'm'
                j = len(p)
                while j > 0 and p[j - 1].isdigit():
                    j -= 1
                if j > 0:
                    toks.add(p[:j])
            return toks

        required = tuple(str(x) for x in must_have)
        out = []
        for name in names:
            tset = _tokens(name)
            if all(r in tset for r in required):
                out.append(name)

        return sorted(out)

    def __dir__(self):
        """
        Extend dir() to include the names of all available unit attributes.

        This makes IDE tab-completion show unit names like 'm', 'cm',
        'count_m2_s_sr', 'm2_sr', etc. for tools that use dir().
        """
        base = super().__dir__()
        if hasattr(self, "_conversions"):
            return sorted(set(list(base) + list(self._conversions.keys())))
        return base

    # -------------------------
    # Common helpers
    # -------------------------

    @staticmethod
    def _is_number(x):
        return isinstance(x, (int, float, np.floating)) or isinstance(
            x, (list, tuple, np.ndarray)
        )

    def _spawn_like(self, cls, sig, si_value):
        """
        Create an instance of cls (or GenericQuantity) with given SI value & signature.
        """
        if cls is None:
            # generic fallback
            return GenericQuantity(sig, si_value)
        out = cls.__new__(cls)  # bypass __init__ to set SI directly
        # call __init__ to build conversions dicts
        cls.__init__(out)
        object.__setattr__(out, "_sig", dict(sig))
        object.__setattr__(out, "_Unit__value_si", si_value)
        return out

    # -------------------------
    # Arithmetic within same dimension (+/-) or numeric
    # -------------------------

    def __add__(self, other):
        if isinstance(other, Unit):
            if _normalize_sig(self._sig) != _normalize_sig(other._sig):
                return NotImplemented
            si = self._get_value_si() + other._get_value_si()
        elif self._is_number(other):
            si = self._get_value_si() + np.asarray(other, dtype=float)
        else:
            return NotImplemented
        return self._spawn_like(self.__class__, self._sig, si)

    def __sub__(self, other):
        if isinstance(other, Unit):
            if _normalize_sig(self._sig) != _normalize_sig(other._sig):
                return NotImplemented
            si = self._get_value_si() - other._get_value_si()
        elif self._is_number(other):
            si = self._get_value_si() - np.asarray(other, dtype=float)
        else:
            return NotImplemented
        return self._spawn_like(self.__class__, self._sig, si)

    def __radd__(self, other):
        if self._is_number(other):
            return self + other
        return NotImplemented

    def __rsub__(self, other):
        if isinstance(other, Unit):
            if _normalize_sig(self._sig) != _normalize_sig(other._sig):
                return NotImplemented
            si = other._get_value_si() - self._get_value_si()
            return self._spawn_like(self.__class__, self._sig, si)
        if self._is_number(other):
            si = np.asarray(other, dtype=float) - self._get_value_si()
            return self._spawn_like(self.__class__, self._sig, si)
        return NotImplemented

    # -------------------------
    # Dimensional multiply / divide
    # -------------------------

    def __mul__(self, other):
        if self._is_number(other):
            si = self._get_value_si() * np.asarray(other, dtype=float)
            return self._spawn_like(self.__class__, self._sig, si)
        if isinstance(other, Unit):
            new_sig = _add_sig(self._sig, other._sig, +1)
            si = self._get_value_si() * other._get_value_si()
            cls = _DERIVED_REGISTRY.get(_normalize_sig(new_sig))
            return self._spawn_like(cls, new_sig, si)
        return NotImplemented

    def __rmul__(self, other):
        if self._is_number(other):
            si = np.asarray(other, dtype=float) * self._get_value_si()
            return self._spawn_like(self.__class__, self._sig, si)
        return NotImplemented

    def __truediv__(self, other):
        if self._is_number(other):
            si = self._get_value_si() / np.asarray(other, dtype=float)
            return self._spawn_like(self.__class__, self._sig, si)
        if isinstance(other, Unit):
            new_sig = _add_sig(self._sig, other._sig, -1)
            si = self._get_value_si() / other._get_value_si()
            cls = _DERIVED_REGISTRY.get(_normalize_sig(new_sig))
            return self._spawn_like(cls, new_sig, si)
        return NotImplemented

    def __rtruediv__(self, other):
        if self._is_number(other):
            si = np.asarray(other, dtype=float) / self._get_value_si()
            inv_sig = {k: -v for k, v in self._sig.items()}
            cls = _DERIVED_REGISTRY.get(_normalize_sig(inv_sig))
            return self._spawn_like(cls, inv_sig, si)
        return NotImplemented

    # ------------------------
    # len()
    # ------------------------

    def __len__(self):
        """Return the length of the underlying array, or 1 if scalar."""
        val = self._get_value_si()
        try:
            return len(val)
        except TypeError:
            return 1


# -------------------------------------------------------------------
# Generic fallback quantity helpers
# -------------------------------------------------------------------


def _compose_unit_name(sig: dict) -> str:
    """
    Generate a simple SI-style name like 'kg_m3_s_sr' for the signature.
    """
    # Include 7 SI bases + our extras in a consistent order
    order = ['M', 'L', 'T', 'I', 'Θ', 'n', 'J', 'Ω', 'N']
    parts = []
    sym_si = {
        'M': 'kg',
        'L': 'm',
        'T': 's',
        'I': 'A',
        'Θ': 'K',
        'n': 'mol',
        'J': 'cd',
        'Ω': 'sr',
        'N': 'count',
    }
    for key in order:
        exp = sig.get(key, 0)
        if exp:
            u = sym_si[key]
            if exp > 0:
                if exp == 1:
                    parts.append(u)
                else:
                    parts.append(f"{u}{exp}")
            else:
                # for negative exponents we just note the base symbol; this only
                # affects the auto-generated GenericQuantity label.
                parts.append(u)
    return "_".join(parts) if parts else "dimensionless"


# Max number of auto-generated conversions for a GenericQuantity
MAX_GENERIC_CONVERSIONS = 4096


def _generate_conversions_from_signature(sig: dict) -> dict:
    """
    Build a conversions table for a composite signature.

    Option B (global auto-expansion):
      - Uses the base-unit conversions from Mass, Length, Time, etc.
      - For each dimension in `sig`, walks over all base-unit names and
        raises their SI factor to the appropriate exponent.
      - Joins the tokens with '_' to form attribute names (e.g. 'g_cm2_s').
      - The order of tokens in attribute access is free thanks to
        Unit._resolve_unit_name, which permutes tokens until it finds a match.

    For example, for sig = {'M': 1, 'L': 1}, you get combinations such as:
      'kg_m', 'kg_cm', 'g_m', 'g_cm', 'lb_ft', ...
    and you can access them in any order:
      Q.m_kg, Q.kg_m, Q.ft_lb, etc.
    """
    # dimensionless -> just a single empty unit
    if not sig or all(v == 0 for v in sig.values()):
        return {"": 1.0}

    # We'll refer to base-unit classes that are defined further below.
    # This function is only *called* after they exist.
    dim_base_cls = {
        'M': lambda: Mass()._conversions,
        'L': lambda: Length()._conversions,
        'T': lambda: Time()._conversions,
        'I': lambda: ElectricCurrent()._conversions,
        'Θ': lambda: Temperature()._conversions,
        'n': lambda: Amount()._conversions,
        'J': lambda: LuminousIntensity()._conversions,
        'Ω': lambda: SolidAngle()._conversions,
        'N': lambda: Counts()._conversions,
    }

    # Use a fixed dimension order for deterministic names
    dim_order = ['M', 'L', 'T', 'I', 'Θ', 'n', 'J', 'Ω', 'N']

    dim_conv_list = []
    for dim_key in dim_order:
        exp = sig.get(dim_key, 0)
        if exp == 0:
            continue
        getter = dim_base_cls.get(dim_key)
        if getter is None:
            # unknown dimension -> synthetic placeholder name with factor 1
            dim_conv_list.append((dim_key, {dim_key: 1.0}, exp))
        else:
            conv = getter()
            dim_conv_list.append((dim_key, conv, exp))

    if not dim_conv_list:
        # Fallback to a single canonical name
        return {_compose_unit_name(sig): 1.0}

    conversions = {}

    def rec(idx: int, factor: float, tokens: list):
        # Early stop if we've hit the global limit
        if len(conversions) >= MAX_GENERIC_CONVERSIONS:
            return
        if idx == len(dim_conv_list):
            name = "_".join(tokens) if tokens else _compose_unit_name(sig)
            conversions[name] = factor
            return

        dim_key, base_conv, exp = dim_conv_list[idx]
        abs_exp = abs(exp)

        for unit_name, unit_fac in base_conv.items():
            if not unit_name:
                continue
            # 'cm2', 'm3', etc. for |exp|>1; 'cm', 'm', 's' for |exp|==1
            token = unit_name if abs_exp == 1 else f"{unit_name}{abs_exp}"
            if exp > 0:
                new_factor = factor * (unit_fac ** exp)
            else:
                new_factor = factor / (unit_fac ** abs_exp)

            rec(idx + 1, new_factor, tokens + [token])

            if len(conversions) >= MAX_GENERIC_CONVERSIONS:
                break

    rec(0, 1.0, [])

    if not conversions:
        conversions = {_compose_unit_name(sig): 1.0}

    return conversions


class GenericQuantity(Unit):
    """
    A generic derived quantity with a dynamic signature.

    For any signature `sig` that does not match a registered derived class:

      - We automatically build a conversions dict by combining the base
        unit conversions for each dimension present in `sig`.
      - The attribute names are strings like 'kg_m2_s_sr', 'g_cm2_s_sr', etc.
      - Thanks to Unit._resolve_unit_name, the token order in attribute
        access is free: 'count_m2_s_sr', 's_m2_sr_count', etc. all work.
    """

    def __init__(self, sig: dict, si_value):
        conv = _generate_conversions_from_signature(sig)
        si_name = _compose_unit_name(sig)
        super().__init__(conv, si_unit=si_name, sig=sig)
        object.__setattr__(self, "_Unit__value_si", np.asarray(si_value))


# -------------------------------------------------------------------
# Signature utilities: parse, print
# -------------------------------------------------------------------

# Alias mapping for parse_signature (optional niceties)
_DIM_ALIAS = {
    "kg": "M",
    "m": "L",
    "s": "T",
    "A": "I",
    "K": "Θ",
    "mol": "n",
    "cd": "J",
    "sr": "Ω",
    "count": "N",
}


def parse_signature(expr: str) -> dict:
    """
    Parse a signature expression into a dimension dict.

    Accepts things like:
        "M L2 T-2"
        "M1 L-2 T^-2 Ω-1"
        "kg m2 s-2"  (using base-unit aliases)

    Rules
    -----
    - Split on whitespace and commas.
    - Each token is a base symbol (e.g. 'M', 'L', 'T', 'Ω')
      or alias ('kg','m','s','mol','cd','sr','count') followed by
      an optional integer exponent, with optional '^', e.g.:
         'M', 'M1', 'M^1', 'L-2', 'L^-2', 'kg2', 'm-3'
    - Exponent defaults to +1 if omitted.
    """
    sig = {}
    if not expr:
        return sig

    tokens = expr.replace(",", " ").split()
    for raw in tokens:
        token = raw.strip()
        if not token:
            continue
        token = token.replace("^", "")

        # split into leading letters and trailing digits/sign
        i = 0
        while i < len(token) and not (token[i] in "+-" or token[i].isdigit()):
            i += 1
        base = token[:i]
        exp_str = token[i:]

        if not base:
            raise ValueError(f"Could not parse base dimension from '{raw}'")

        # Map aliases (kg->M, m->L, etc.) if present
        base = _DIM_ALIAS.get(base, base)

        if exp_str == "" or exp_str == "+":
            exp = 1
        elif exp_str == "-":
            exp = -1
        else:
            try:
                exp = int(exp_str)
            except ValueError:
                raise ValueError(f"Could not parse exponent from '{raw}'") from None

        sig[base] = sig.get(base, 0) + exp

    # strip zeros
    sig = {k: v for k, v in sig.items() if v != 0}
    return sig


def signature_to_string(sig: dict) -> str:
    """
    Convert a dimension dict to a compact string like 'M L-2 T-2'.
    """
    if not sig or all(v == 0 for v in sig.values()):
        return "dimensionless"

    order = ['M', 'L', 'T', 'I', 'Θ', 'n', 'J', 'Ω', 'N']
    parts = []
    for key in order:
        exp = sig.get(key, 0)
        if exp:
            if exp == 1:
                parts.append(key)
            else:
                parts.append(f"{key}{exp}")
    return " ".join(parts)


def print_base_signatures():
    """
    Print the list of base dimensions and their symbols, to help users
    craft signatures for custom units.

    Example
    -------
        >>> print_base_signatures()
        Base dimension signatures:
          M  : Mass                 [kg]
          L  : Length               [m]
          T  : Time                 [s]
          I  : Electric current     [A]
          Θ  : Temperature          [K]
          n  : Amount of substance  [mol]
          J  : Luminous intensity   [cd]
          Ω  : Solid angle          [sr]
          N  : Counts               [count]
    """
    lines = [
        ("M", "Mass",                "kg"),
        ("L", "Length",              "m"),
        ("T", "Time",                "s"),
        ("I", "Electric current",    "A"),
        ("Θ", "Temperature",         "K"),
        ("n", "Amount of substance", "mol"),
        ("J", "Luminous intensity",  "cd"),
        ("Ω", "Solid angle",         "sr"),
        ("N", "Counts",              "count"),
    ]
    print("Base dimension signatures:")
    for sym, name, si in lines:
        print(f"  {sym:2s} : {name:<20s} [{si}]")


# -------------------------------------------------------------------
# Property attachment for IDE completion
# -------------------------------------------------------------------


def _attach_unit_properties(cls):
    """
    Attach property descriptors for each conversion key so that static
    completion engines (Pylance/Jedi/etc.) see them as real attributes.

    The properties delegate to Unit.__getattr__ / Unit.__setattr__, so
    runtime behaviour (conversion, permutations, etc.) is unchanged.
    """
    # GenericQuantity uses dynamic signatures and conversions, so there is
    # no fixed set of attributes to attach statically.
    if cls is GenericQuantity:
        return

    # Instantiate once to get the conversions dict
    dummy = cls()
    conv = getattr(dummy, "_conversions", {})

    for name in conv.keys():
        # skip empty or non-identifier keys (like the "" of Dimensionless)
        if not name or not name.isidentifier():
            continue

        # don't overwrite anything explicit on the class
        if hasattr(cls, name):
            continue

        # Use default arg to capture the current key
        def getter(self, _name=name):
            return Unit.__getattr__(self, _name)

        def setter(self, value, _name=name):
            return Unit.__setattr__(self, _name, value)

        setattr(cls, name, property(getter, setter))


# -------------------------------------------------------------------
# Base Units (including 7 SI bases + counts + solid angle)
# -------------------------------------------------------------------


class Counts(Unit):
    # Extra base dimension: counts
    SIG = {'N': 1}

    def __init__(self):
        conversions = {
            "count": 1.0, "counts": 1.0,
            "kcount": 1e3, "Mcount": 1e6, "Gcount": 1e9,
        }
        super().__init__(conversions, si_unit="count")


class Length(Unit):
    # SI base: metre
    SIG = {'L': 1}

    def __init__(self):
        conversions = {
            "m": 1.0, "dm": 0.1, "cm": 0.01, "mm": 0.001,
            "µm": 1e-6, "nm": 1e-9, "pm": 1e-12, "km": 1000.0, "fm": 1e-15,
            "angstrom": const.angstrom, "Å": const.angstrom,
            "in": 0.0254, "ft": 0.3048, "yd": 0.9144,
            "mile": 1609.344, "nmi": 1852.0,
            "mil": 2.54e-5,
            "au": const.au, "ly": const.light_year, "pc": const.parsec,
            "kpc": const.parsec * 1e3, "Mpc": const.parsec * 1e6,
            "Gpc": const.parsec * 1e9,
        }
        super().__init__(conversions, si_unit="m")


class Time(Unit):
    # SI base: second
    SIG = {'T': 1}

    def __init__(self):
        conversions = {
            "s": 1.0, "ms": 1e-3, "µs": 1e-6, "ns": 1e-9, "ps": 1e-12,
            "fs": 1e-15,
            "min": const.minute, "h": const.hour, "day": const.day,
            "week": const.week,
            "yr": const.year, "kyr": const.year * 1e3,
            "Myr": const.year * 1e6, "Gyr": const.year * 1e9,
        }
        super().__init__(conversions, si_unit="s")


class Angle(Unit):
    # dimensionless in SI, but we treat it as a separate convenience quantity
    SIG = {}

    def __init__(self):
        conversions = {
            "rad": 1.0, "mrad": 1e-3, "µrad": 1e-6,
            "deg": np.deg2rad(1.0), "arcmin": np.deg2rad(1.0 / 60.0),
            "arcsec": np.deg2rad(1.0 / 3600.0),
            "turn": TAU, "rev": TAU,
            "grad": const.pi / 200.0,
        }
        super().__init__(conversions, si_unit="rad")


class Mass(Unit):
    # SI base: kilogram
    SIG = {'M': 1}

    def __init__(self):
        conversions = {
            "kg": 1.0,
            "g": 1e-3, "mg": 1e-6, "µg": 1e-9, "ng": 1e-12,
            "pg": 1e-15, "fg": 1e-18,
            "tonne": 1000.0, "t": 1000.0,
            "kt": 1e6, "Mt": 1e9, "Gt": 1e12,
            "lb": 0.45359237, "oz": 0.028349523125, "st": 6.35029318,
            "cwt": 50.80234544, "slug": 14.59390294,
            "amu": const.atomic_mass, "Da": const.atomic_mass,
        }
        super().__init__(conversions, si_unit="kg")


class SolidAngle(Unit):
    # Not one of the 7 SI bases, but very useful (steradian)
    SIG = {'Ω': 1}

    def __init__(self):
        one_deg_in_rad = np.deg2rad(1.0)
        conversions = {
            "sr": 1.0,
            "deg2": (one_deg_in_rad ** 2),
            "arcmin2": (np.deg2rad(1.0 / 60.0) ** 2),
            "arcsec2": (np.deg2rad(1.0 / 3600.0) ** 2),
            "sphere": 4 * const.pi, "hemisphere": 2 * const.pi,
        }
        super().__init__(conversions, si_unit="sr")


# ---- Additional 4 SI base quantities ----


class ElectricCurrent(Unit):
    # SI base: ampere
    SIG = {'I': 1}

    def __init__(self):
        conversions = {
            "A": 1.0,
            "mA": 1e-3, "µA": 1e-6, "nA": 1e-9,
            "kA": 1e3,
        }
        super().__init__(conversions, si_unit="A")


class Temperature(Unit):
    # SI base: kelvin
    # NOTE: Celsius is affine (offset), so we do NOT include 'degC' here.
    SIG = {'Θ': 1}

    def __init__(self):
        conversions = {
            "K": 1.0,
            "mK": 1e-3, "µK": 1e-6,
        }
        super().__init__(conversions, si_unit="K")


class Amount(Unit):
    # SI base: mole
    SIG = {'n': 1}

    def __init__(self):
        conversions = {
            "mol": 1.0,
            "mmol": 1e-3, "µmol": 1e-6, "nmol": 1e-9,
        }
        super().__init__(conversions, si_unit="mol")


class LuminousIntensity(Unit):
    # SI base: candela
    SIG = {'J': 1}

    def __init__(self):
        conversions = {
            "cd": 1.0,
            "mcd": 1e-3, "kcd": 1e3,
        }
        super().__init__(conversions, si_unit="cd")


# -------------------------------------------------------------------
# Implemented derived types
# -------------------------------------------------------------------


@register_derived
class Density(Unit):
    # mass / volume  -> {'M':1, 'L':-3}
    SIG = {'M': 1, 'L': -3}

    def __init__(self):
        # Build conversions programmatically (mass x length^3)
        mass_units = Mass()._conversions
        length_units = Length()._conversions  # we'll use L^-3 from length units
        conversions = {}
        for m_name, m_fac in mass_units.items():
            for l_name, l_fac in length_units.items():
                name = f"{m_name}_{l_name}3"  # e.g., kg_m3, g_cm3
                conversions[name] = m_fac / (l_fac ** 3)
        super().__init__(conversions, si_unit="kg_m3")


@register_derived
class Flux(Unit):
    # counts / (area * time * solid angle) -> {'N':1,'L':-2,'T':-1,'Ω':-1}
    SIG = {'N': 1, 'L': -2, 'T': -1, 'Ω': -1}

    def __init__(self):
        count_units = Counts()._conversions
        length_units = Length()._conversions
        time_units = Time()._conversions
        omega_units = SolidAngle()._conversions
        conversions = {}
        for c_name, c_fac in count_units.items():
            for l_name, l_fac in length_units.items():
                for t_name, t_fac in time_units.items():
                    for o_name, o_fac in omega_units.items():
                        # area = l^2 -> put ^2 in name
                        name = f"{c_name}_{l_name}2_{t_name}_{o_name}"
                        conversions[name] = (
                            c_fac / ((l_fac ** 2) * t_fac * o_fac)
                        )
        super().__init__(conversions, si_unit="count_m2_s_sr")


@register_derived
class Area(Unit):
    SIG = {'L': 2}

    def __init__(self):
        conversions = {
            "m2": 1.0,
            "km2": 1e6, "cm2": 1e-4, "mm2": 1e-6,
            "µm2": 1e-12, "nm2": 1e-18,
            "ha": 1e4, "are": 100.0,
            "in2": (0.0254 ** 2), "ft2": (0.3048 ** 2), "yd2": (0.9144 ** 2),
            "mi2": (1609.344 ** 2), "acre": 4046.8564224,
        }
        super().__init__(conversions, si_unit="m2")


@register_derived
class Volume(Unit):
    SIG = {'L': 3}

    def __init__(self):
        conversions = {
            "m3": 1.0,
            "L": 1e-3, "mL": 1e-6, "cL": 1e-5, "dL": 1e-4, "cm3": 1e-6,
            "mm3": 1e-9, "µL": 1e-9, "dm3": 1e-3, "km3": 1e9,
            "in3": (0.0254 ** 3), "ft3": (0.3048 ** 3), "yd3": (0.9144 ** 3),
            "gal_us": 0.003785411784, "qt_us": 0.000946352946,
            "pt_us": 0.000473176473, "cup_us": 0.0002365882365,
            "fl_oz_us": 2.957352956e-5,
            "gal_imp": 0.00454609, "qt_imp": 0.0011365225,
            "pt_imp": 0.00056826125, "fl_oz_imp": 2.84130625e-5,
        }
        super().__init__(conversions, si_unit="m3")


@register_derived
class GeometricFactor(Unit):
    # area * solid angle  -> {'L':2, 'Ω':1}
    SIG = {'L': 2, 'Ω': 1}

    def __init__(self):
        length_units = Length()._conversions
        omega_units = SolidAngle()._conversions
        conversions = {}
        for l_name, l_fac in length_units.items():
            for o_name, o_fac in omega_units.items():
                name = f"{l_name}2_{o_name}"  # e.g. m2_sr, cm2_sr, ...
                conversions[name] = (l_fac ** 2) * o_fac
        super().__init__(conversions, si_unit="m2_sr")


@register_derived
class Dimensionless(Unit):
    SIG = {}

    def __init__(self):
        conversions = {"": 1.0}  # empty unit
        super().__init__(conversions, si_unit="")


# -------------------------------------------------------------------
# Custom derived units (smart: conversions optional)
# -------------------------------------------------------------------


def make_custom_unit(class_name, sig, conversions=None, si_unit=None):
    """
    Dynamically create a custom derived unit class with a given signature.

    Two modes
    ---------
    1) Smart / automatic (no conversions passed):
         - conversions are auto-generated from `sig` using the same
           machinery as GenericQuantity (base Mass/Length/Time/... units).
         - si_unit default is a canonical SI-style name, e.g. "kg_m2_s2".

    2) Manual:
         - if you pass a `conversions` dict explicitly, behaviour is
           exactly as before: you control the unit names & factors.

    Parameters
    ----------
    class_name : str
        Name of the new class (e.g. 'RadiationDose').
    sig : dict
        Dimension signature, e.g. {'M': 1, 'L': 2, 'T': -2}.
    conversions : dict, optional
        Mapping "attribute_name" -> factor_to_SI (float). If omitted or None,
        it is built automatically from `sig`.
    si_unit : str, optional
        Name of the SI-like attribute in this conversions dict. If omitted,
        the first key in 'conversions' is used (or a canonical SI-style name
        for the smart/automatic mode).

    Returns
    -------
    cls : type
        A new class deriving from Unit, automatically registered in the
        dimensional registry so arithmetic will produce this type when
        signatures match.
    """
    # Smart mode: auto-build conversions, like GenericQuantity
    if conversions is None:
        conversions = _generate_conversions_from_signature(sig)
        # If no explicit si_unit given, use the canonical SI-like name
        if si_unit is None:
            si_unit = _compose_unit_name(sig)

    if not conversions:
        raise ValueError("conversions must not be empty")

    if si_unit is None:
        si_unit = next(iter(conversions.keys()))

    def __init__(self, _conv=None, _si=None, _sig=None):
        Unit.__init__(
            self,
            conversions=dict(_conv if _conv is not None else conversions),
            si_unit=_si if _si is not None else si_unit,
            sig=_sig if _sig is not None else sig,
        )

    attrs = {
        "SIG": dict(sig),
        "__init__": __init__,
        "__doc__": f"Custom unit '{class_name}' with signature {sig}.",
    }
    cls = type(class_name, (Unit,), attrs)
    register_derived(cls)
    # Attach completion properties for its conversions too
    _attach_unit_properties(cls)
    return cls


def make_custom_unit_from_signature(
    class_name,
    signature_expr,
    conversions=None,
    si_unit=None,
):
    """
    Convenience wrapper around make_custom_unit that takes a human-friendly
    signature string.

    Smart usage (no conversions):
    -----------------------------
        RadiationDose = make_custom_unit_from_signature(
            "RadiationDose", "M L2 T-2"
        )

    This will:
      - parse "M L2 T-2" into {'M':1, 'L':2, 'T':-2}
      - auto-generate conversions using base Mass/Length/Time/... units
      - create a class `RadiationDose` with a rich set of unit attributes,
        e.g. 'kg_m2_s2', 'g_cm2_s2', etc., accessible in any token order
        thanks to Unit._resolve_unit_name.

    Manual usage (override conversions):
    ------------------------------------
        MyUnit = make_custom_unit_from_signature(
            "MyUnit",
            "M L-2",
            conversions={"kg_m2": 1.0, "g_cm2": 0.1},
            si_unit="kg_m2",
        )
    """
    sig = parse_signature(signature_expr)
    return make_custom_unit(
        class_name=class_name,
        sig=sig,
        conversions=conversions,
        si_unit=si_unit,
    )


# -------------------------------------------------------------------
# Attach properties for completion (static tools)
# -------------------------------------------------------------------

for _cls in (
    Counts,
    Length,
    Time,
    Angle,
    Mass,
    SolidAngle,
    ElectricCurrent,
    Temperature,
    Amount,
    LuminousIntensity,
    Density,
    Flux,
    Area,
    Volume,
    GeometricFactor,
    Dimensionless,
):
    _attach_unit_properties(_cls)


__all__ = [
    "Unit",
    "Counts",
    "Length",
    "Time",
    "Angle",
    "Mass",
    "SolidAngle",
    "ElectricCurrent",
    "Temperature",
    "Amount",
    "LuminousIntensity",
    "Density",
    "Flux",
    "Area",
    "Volume",
    "GeometricFactor",
    "Dimensionless",
    "GenericQuantity",
    "make_custom_unit",
    "make_custom_unit_from_signature",
    "parse_signature",
    "signature_to_string",
    "print_base_signatures",
]


# -------------------------------------------------------------------
# Tiny smoke test (optional)
# -------------------------------------------------------------------

if __name__ == "__main__":
    print_base_signatures()
    print()

    # ---- 1. Compute muon flux from counts, geometric factor, and live time ----

    N = Counts()
    N.counts = 2.5e4  # 25k events

    T = Time()
    T.h = 5.0  # 5 hours

    G = GeometricFactor()
    G.m2_sr = 0.20  # 0.20 m²·sr

    # flux = N / (G * T)
    F = N / (G * T)  # type: Flux

    print("Flux (SI):", F.value, F.unit)
    print("Flux (count_m2_s_sr):", F.count_m2_s_sr)
    # Order of tokens doesn't matter:
    print("Same via scrambled name:", F.s_m2_sr_count)
    print("Flux units w/ 'count','m','s','sr':", F.available_units("count", "m", "s", "sr")[:5])
    print()

    # ---- 2. GenericQuantity auto-expansion test: M * L ----
    L_ = Length()
    L_.cm = 10.0
    M_ = Mass()
    M_.g = 500.0

    Q = L_ * M_  # GenericQuantity with sig {'M':1,'L':1}
    print("Q (SI value):", Q.value, Q.unit)
    print("Sample units for Q:", Q.available_units()[:8])
    print("Q.g_cm:", Q.g_cm)      # should work
    print("Q.cm_g:", Q.cm_g)      # permuted order, also works
    print("Q.available_units('g','cm'):", Q.available_units("g", "cm"))
    print()

    # ---- 3. Custom unit: mass column density (kg/m²) with smart generation ----

    MassColumnAuto = make_custom_unit_from_signature(
        "MassColumnAuto",
        "M L-2",  # mass / area
    )

    col = MassColumnAuto()
    col.g_cm2 = 100.0  # 100 g/cm²

    print("Mass column:", col.kg_m2, "[kg/m²]")
    print("Mass column via permuted name:", col.cm2_g, "[kg/m²]")
    print("MassColumnAuto units with 'kg','m':", col.available_units("kg", "m")[:5])
    print()

    # ---- 4. Simple array usage: angle-dependent flux map ----
    image = np.random.uniform(100, 200, size=(5, 5))  # counts / (m² s sr)
    Fmap = Flux()
    Fmap.count_m2_s_sr = image  # store as array
    print("Flux map shape:", Fmap.value.shape)
    print("Flux map mean:", Fmap.count_m2_s_sr.mean())
