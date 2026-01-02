import datetime
from typing import Any, Final

import astropy.units as u
from astropy.units import astrophys, cgs, core, misc, si
from pydantic import (
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    UUID6,
    UUID7,
    UUID8,
    AmqpDsn,
    AnyHttpUrl,
    AnyUrl,
    AnyWebsocketUrl,
    Base64Bytes,
    Base64Str,
    Base64UrlBytes,
    Base64UrlStr,
    ClickHouseDsn,
    CockroachDsn,
    DirectoryPath,
    EmailStr,
    FilePath,
    FileUrl,
    FiniteFloat,
    FtpUrl,
    GetCoreSchemaHandler,
    HttpUrl,
    IPvAnyAddress,
    KafkaDsn,
    MariaDBDsn,
    MongoDsn,
    MySQLDsn,
    NameEmail,
    NatsDsn,
    NegativeFloat,
    NegativeInt,
    NonNegativeFloat,
    NonNegativeInt,
    NonPositiveFloat,
    NonPositiveInt,
    PositiveFloat,
    PositiveInt,
    PostgresDsn,
    RedisDsn,
    SnowflakeDsn,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    WebsocketUrl,
)
from pydantic_core import core_schema

# --- Astropy Physical Types Logic ---


def create_quantity_type(name: str, target_physical_type: str):
    class QuantityType(str):
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> core_schema.CoreSchema:
            return core_schema.no_info_after_validator_function(
                cls.validate,
                core_schema.str_schema(),
            )

        @classmethod
        def validate(cls, v: str) -> str:
            try:
                q = u.Quantity(v)
                # Ensure we are comparing PhysicalType objects to handle synonyms
                assert q.unit is not None, "Quantity unit cannot be None"
                pt = q.unit.physical_type
                target_pt = u.get_physical_type(target_physical_type)

                if pt != target_pt:
                    raise ValueError(
                        f"Physical type mismatch: expected '{target_physical_type}' ({target_pt}), got '{pt}'"
                    )
            except Exception as e:
                # Wrap any astropy parsing error or our custom mismatch error
                raise ValueError(f"Invalid quantity for type '{name}': {e}") from e
            return v

    QuantityType.__name__ = name
    return QuantityType


# List provided by user
_units_and_physical_types: Final[list[tuple[core.UnitBase, str | set[str]]]] = [
    (core.dimensionless_unscaled, "dimensionless"),
    (si.m, "length"),
    (si.m**2, "area"),
    (si.m**3, "volume"),
    (si.s, "time"),
    (si.rad, "angle"),
    (si.sr, "solid angle"),
    (si.m / si.s, {"speed", "velocity"}),
    (si.m / si.s**2, "acceleration"),
    (si.Hz, "frequency"),
    (si.g, "mass"),
    (si.mol, "amount of substance"),
    (si.K, "temperature"),
    (si.W * si.m**-1 * si.K**-1, "thermal conductivity"),
    (si.J * si.K**-1, {"heat capacity", "entropy"}),
    (si.J * si.K**-1 * si.kg**-1, {"specific heat capacity", "specific entropy"}),
    (si.N, "force"),
    (si.J, {"energy", "work", "torque"}),
    (si.J * si.m**-2 * si.s**-1, {"energy flux", "irradiance"}),
    (si.Pa, {"pressure", "energy density", "stress"}),
    (si.W, {"power", "radiant flux"}),
    (si.kg * si.m**-3, "mass density"),
    (si.m**3 / si.kg, "specific volume"),
    (si.mol / si.m**3, "molar concentration"),
    (si.m**3 / si.mol, "molar volume"),
    (si.kg * si.m / si.s, {"momentum", "impulse"}),
    (si.kg * si.m**2 / si.s, {"angular momentum", "action"}),
    (si.rad / si.s, {"angular speed", "angular velocity", "angular frequency"}),
    (si.rad / si.s**2, "angular acceleration"),
    (si.rad / si.m, "plate scale"),
    (si.g / (si.m * si.s), "dynamic viscosity"),
    (si.m**2 / si.s, {"diffusivity", "kinematic viscosity"}),
    (si.m**-1, "wavenumber"),
    (si.m**-2, "column density"),
    (si.A, "electrical current"),
    (si.C, "electrical charge"),
    (si.V, "electrical potential"),
    (si.Ohm, {"electrical resistance", "electrical impedance", "electrical reactance"}),
    (si.Ohm * si.m, "electrical resistivity"),
    (si.S, "electrical conductance"),
    (si.S / si.m, "electrical conductivity"),
    (si.F, "electrical capacitance"),
    (si.C * si.m, "electrical dipole moment"),
    (si.A / si.m**2, "electrical current density"),
    (si.V / si.m, "electrical field strength"),
    (
        si.C / si.m**2,
        {"electrical flux density", "surface charge density", "polarization density"},
    ),
    (si.C / si.m**3, "electrical charge density"),
    (si.F / si.m, "permittivity"),
    (si.Wb, "magnetic flux"),
    (si.Wb**2, "magnetic helicity"),
    (si.T, "magnetic flux density"),
    (si.A / si.m, "magnetic field strength"),
    (si.m**2 * si.A, "magnetic moment"),
    (si.H / si.m, {"electromagnetic field strength", "permeability"}),
    (si.H, "inductance"),
    (si.cd, "luminous intensity"),
    (si.lm, "luminous flux"),
    (si.lx, {"luminous emittance", "illuminance"}),
    (si.W / si.sr, "radiant intensity"),
    (si.cd / si.m**2, "luminance"),
    (si.m**-3 * si.s**-1, "volumetric rate"),
    (astrophys.Jy, "spectral flux density"),
    (astrophys.Jy / si.sr, "surface brightness"),
    (si.W * si.m**2 * si.Hz**-1, "surface tension"),
    (si.J * si.m**-3 * si.s**-1, {"spectral flux density wav", "power density"}),
    (si.J * si.m**-3 * si.s**-1 * si.sr**-1, "surface brightness wav"),
    (astrophys.photon / si.Hz / si.cm**2 / si.s, "photon flux density"),
    (astrophys.photon / si.AA / si.cm**2 / si.s, "photon flux density wav"),
    (astrophys.photon / si.Hz / si.cm**2 / si.s / si.sr, "photon surface brightness"),
    (
        astrophys.photon / si.AA / si.cm**2 / si.s / si.sr,
        "photon surface brightness wav",
    ),
    (astrophys.R, "photon flux"),
    (misc.bit, "data quantity"),
    (misc.bit / si.s, "bandwidth"),
    (cgs.Franklin, "electrical charge (ESU)"),
    (cgs.statampere, "electrical current (ESU)"),
    (cgs.Biot, "electrical current (EMU)"),
    (cgs.abcoulomb, "electrical charge (EMU)"),
    (si.m * si.s**-3, {"jerk", "jolt"}),
    (si.m * si.s**-4, {"snap", "jounce"}),
    (si.m * si.s**-5, "crackle"),
    (si.m * si.s**-6, {"pop", "pounce"}),
    (si.K / si.m, "temperature gradient"),
    (si.J / si.kg, {"specific energy", "dose of ionizing radiation"}),
    (si.mol * si.m**-3 * si.s**-1, "reaction rate"),
    (si.kg * si.m**2, "moment of inertia"),
    (si.mol / si.s, "catalytic activity"),
    (si.J * si.K**-1 * si.mol**-1, "molar heat capacity"),
    (si.mol / si.kg, "molality"),
    (si.m * si.s, "absement"),
    (si.m * si.s**2, "absity"),
    (si.m**3 / si.s, "volumetric flow rate"),
    (si.s**-2, "frequency drift"),
    (si.Pa**-1, "compressibility"),
    (astrophys.electron * si.m**-3, "electron density"),
    (astrophys.electron * si.m**-2 * si.s**-1, "electron flux"),
    (si.kg / si.m**2, "surface mass density"),
    (si.W / si.m**2 / si.sr, "radiance"),
    (si.J / si.mol, "chemical potential"),
    (si.kg / si.m, "linear density"),
    (si.H**-1, "magnetic reluctance"),
    (si.W / si.K, "thermal conductance"),
    (si.K / si.W, "thermal resistance"),
    (si.K * si.m / si.W, "thermal resistivity"),
    (si.N / si.s, "yank"),
    (si.S * si.m**2 / si.mol, "molar conductivity"),
    (si.m**2 / si.V / si.s, "electrical mobility"),
    (si.lumen / si.W, "luminous efficacy"),
    (si.m**2 / si.kg, {"opacity", "mass attenuation coefficient"}),
    (si.kg * si.m**-2 * si.s**-1, {"mass flux", "momentum density"}),
    (si.m**-3, "number density"),
    (si.m**-2 * si.s**-1, "particle flux"),
]


# Generate map of astropy types
ASTROPY_TYPES = {}
for _unit, names in _units_and_physical_types:
    if isinstance(names, str):
        names_set = {names}
    else:
        names_set = names

    for name in names_set:
        ASTROPY_TYPES[name] = create_quantity_type(name, name)

# --- Standard Pydantic Types ---

STANDARD_TYPES = {
    "str": str,
    "string": str,
    "date": datetime.date,
    "datetime": datetime.datetime,
    "clocktime": datetime.time,  # Note: 'time' renamed to 'clocktime' to avoid conflict with astropy 'time' type
    "int": int,
    "float": float,
    "bool": bool,
    "path": str,
    "url": str,
    "any": Any,
    "markdown": str,
    "StrictBool": StrictBool,
    "PositiveInt": PositiveInt,
    "NegativeInt": NegativeInt,
    "NonPositiveInt": NonPositiveInt,
    "NonNegativeInt": NonNegativeInt,
    "StrictInt": StrictInt,
    "PositiveFloat": PositiveFloat,
    "NegativeFloat": NegativeFloat,
    "NonPositiveFloat": NonPositiveFloat,
    "NonNegativeFloat": NonNegativeFloat,
    "StrictFloat": StrictFloat,
    "FiniteFloat": FiniteFloat,
    "StrictStr": StrictStr,
    "UUID1": UUID1,
    "UUID3": UUID3,
    "UUID4": UUID4,
    "UUID5": UUID5,
    "UUID6": UUID6,
    "UUID7": UUID7,
    "UUID8": UUID8,
    "FilePath": FilePath,
    "DirectoryPath": DirectoryPath,
    "Base64Bytes": Base64Bytes,
    "Base64Str": Base64Str,
    "Base64UrlBytes": Base64UrlBytes,
    "Base64UrlStr": Base64UrlStr,
    "AnyUrl": AnyUrl,
    "AnyHttpUrl": AnyHttpUrl,
    "HttpUrl": HttpUrl,
    "AnyWebsocketUrl": AnyWebsocketUrl,
    "WebsocketUrl": WebsocketUrl,
    "FileUrl": FileUrl,
    "FtpUrl": FtpUrl,
    "PostgresDsn": PostgresDsn,
    "CockroachDsn": CockroachDsn,
    "AmqpDsn": AmqpDsn,
    "RedisDsn": RedisDsn,
    "MongoDsn": MongoDsn,
    "KafkaDsn": KafkaDsn,
    "NatsDsn": NatsDsn,
    "MySQLDsn": MySQLDsn,
    "MariaDBDsn": MariaDBDsn,
    "ClickHouseDsn": ClickHouseDsn,
    "SnowflakeDsn": SnowflakeDsn,
    "EmailStr": EmailStr,
    "NameEmail": NameEmail,
    "IPvAnyAddress": IPvAnyAddress,
}

# --- Unified Map ---
PRIMITIVE_TYPE_MAP = {**STANDARD_TYPES, **ASTROPY_TYPES}


class ReferenceMarker:
    def __init__(self, target: str):
        self.target = target

    def __repr__(self):
        return f"ref[{self.target}]"
