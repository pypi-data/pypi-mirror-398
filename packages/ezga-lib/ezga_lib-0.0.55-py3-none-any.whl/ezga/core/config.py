from __future__ import annotations
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Sequence, Tuple, List, Dict, Union, Callable, Literal, Annotated

from pydantic import (
    BaseModel,
    Field,
    PositiveInt,
    NonNegativeInt,
    field_validator,
    model_validator,
    ConfigDict,
)

# -----------------------------------------------------------------------------
# Small helper aliases for common constraints
# -----------------------------------------------------------------------------
Prob = Annotated[float, Field(ge=0.0, le=1.0)]
NonNegFloat = Annotated[float, Field(ge=0.0)]
PosFloat = Annotated[float, Field(gt=0.0)]


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------
class SelectionMethod(str, Enum):
    BOLTZMANN = "boltzmann"
    BOLTZMANN_BIGDATA = "boltzmann_bigdata"
    GREEDY = "greedy"
    ROULETTE = "roulette"
    TOURNAMENT = "tournament"
    NSGA3 = "nsga3"
    NS = "nondominated_sorted"


class HashMethod(str, Enum):
    RDF = "rdf"
    TSF = "tsf"
    RBF = "rbf"


class RepulsionMode(str, Enum):
    MIN = "min"
    SUM = "sum"


class SimulatorMode(str, Enum):
    SAMPLING = "sampling"
    RELAXATION = "relaxation"


class ResumeMode(str, Enum):
    FOLDERS_ALL = "folders_all"
    FOLDERS = "folders"
    SNAPSHOT = "snapshot"


# -----------------------------------------------------------------------------
# Sub-models
# -----------------------------------------------------------------------------
class HiSEParams(BaseModel):
    """Hierarchical Supercell Escalation (HiSE) coarse-to-fine settings."""

    model_config = ConfigDict(extra="forbid")

    supercells: List[Tuple[int, int, int]] = Field(
        ..., description="Sequence of supercells, e.g. [[1,1,1],[2,1,1],[2,2,1]]"
    )

    # I/O
    input_from: Literal["final_dataset", "latest_generation"] = Field(
        "final_dataset",
        description=(
            "Where to read previous stage input from: final_dataset (root config.xyz) "
            "or latest_generation (scan generation/*/config.xyz)."
        ),
    )
    stage_dir_pattern: str = Field(
        "supercell_{a}_{b}_{c}",
        description="Subdirectory name per stage under GAConfig.output_path.",
    )
    restart: bool = Field(
        True, description="Skip stages already complete; resume partial if possible."
    )

    # Stage-specific overrides (e.g., foreigners, thermostat, etc.).
    overrides: Optional[Dict[str, List[Any]]] = Field(
        None,
        description=(
            "Stage-specific overrides by key path (dot-notation) → list of values per stage."
        ),
    )

    # Carry semantics
    carry: Literal["pareto", "elites", "all"] = "all"
    reseed_fraction: Prob = 1.0
    lift_method: Literal["tile"] = "tile"

    @field_validator("supercells")
    @classmethod
    def _validate_supercells(cls, v: List[Tuple[int, int, int]]):
        if not v:
            raise ValueError("supercells must be a non-empty list")
        clean: List[Tuple[int, int, int]] = []
        for t in v:
            if len(t) != 3 or any(int(x) < 1 for x in t):
                raise ValueError(f"Invalid supercell {t!r}")
            clean.append(tuple(int(x) for x in t))
        return clean

    @model_validator(mode="after")
    def _validate_overrides_length(self):
        if self.overrides is None:
            return self
        n = len(self.supercells)
        for key, values in self.overrides.items():
            if not isinstance(values, list) or len(values) != n:
                raise ValueError(
                    f"overrides['{key}'] must be a list of length {n} (one per stage)"
                )
        return self


class PopulationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_path: Optional[Path] = None  # e.g., 'config.xyz'
    template_path: Optional[Path] = None
    db_path: Optional[Path] = None
    db_ro_path: Optional[Path] = None

    filter_duplicates: bool = True
    size_limit: Optional[int] = None
    constraints: Optional[List[Union[Callable[..., bool], Dict[str, Any]]]] = None

    ef_bounds: Optional[Tuple[float, float]] = None
    collision_factor: Optional[NonNegFloat] = 0.80
    blacklist: Optional[List[str]] = None
    fetch_limit: Optional[int] = None  # fixed: stray trailing comma made a tuple default


class ThermostatParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    initial_temperature: NonNegFloat = 1.0
    decay_rate: NonNegFloat = 0.005
    period: PositiveInt = 30
    temperature_bounds: Tuple[NonNegFloat, NonNegFloat] = (0.0, 1.1)
    max_stall_offset: NonNegFloat = 1.0
    stall_growth_rate: NonNegFloat = 0.01
    constant_temperature: bool = False

    @model_validator(mode="after")
    def _validate_temperatures(self):
        low, high = self.temperature_bounds
        if low > high:
            raise ValueError("temperature_bounds must be (low ≤ high)")
        if not (low <= self.initial_temperature <= high):
            raise ValueError(
                "initial_temperature must lie within temperature_bounds"
            )
        return self


class EvaluatorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    features_funcs: Any = None
    objectives_funcs: Any = None
    debug: bool = False


class SelectionParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    size: PositiveInt = 256
    weights: Optional[Sequence[float]] = None
    repulsion_weight: NonNegFloat = 1.0
    repetition_penalty: bool = True
    objective_temperature: PosFloat = 1.0
    repulsion_mode: RepulsionMode = RepulsionMode.MIN
    composition_repulsion_weight: NonNegFloat = 0.0  # β strength for composition multiplicity penalty
    composition_decimals: Annotated[int, Field(ge=0)] = 0  # rounding for float features when comparing compositions
    metric: Literal["euclidean", "cosine", "manhattan"] = "euclidean"
    random_seed: Optional[int] = None
    steepness: PosFloat = 10.0
    max_count: PositiveInt = 50
    cooling_rate: Prob = 0.1
    counts: Optional[List[int]] = None
    normalize_objectives: bool = False
    sampling_temperature: PosFloat = 1.0
    selection_method: SelectionMethod = SelectionMethod.BOLTZMANN
    divisions: PositiveInt = 12  # used by NSGA-III reference points

    @model_validator(mode="after")
    def _validate_counts(self):
        if self.counts is not None and any(c < 0 for c in self.counts):
            raise ValueError("counts must be non-negative integers")
        return self


class VariationParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    initial_mutation_rate: PosFloat = 2.0
    min_mutation_rate: PosFloat = 1.0
    max_prob: Prob = 0.95
    min_prob: Prob = 0.01
    use_magnitude_scaling: bool = True
    alpha: NonNegFloat = 0.01
    crossover_probability: Prob = 0.1

    @model_validator(mode="after")
    def _validate_ranges(self):
        if self.min_prob > self.max_prob:
            raise ValueError("min_prob must be ≤ max_prob")
        if self.min_mutation_rate > self.initial_mutation_rate:
            raise ValueError(
                "min_mutation_rate must be ≤ initial_mutation_rate"
            )
        return self


class SimulatorParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: SimulatorMode = SimulatorMode.SAMPLING
    calculator: Optional[Any] = [ lambda x : 1 ]


class ConvergenceParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective_threshold: NonNegFloat = 0.01
    feature_threshold: NonNegFloat = 0.01
    stall_threshold: PositiveInt = int(1e5)
    information_driven: bool = False
    detailed_record: bool = True
    convergence_type: Literal["and", "or"] = "and"


class AgenticParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hash_name: str = "sha256"
    shared_dir: Optional[Path] = None
    shard_width: PositiveInt = 2
    persist_seen: bool = False
    poll_interval: PosFloat = 2.0
    max_buffer: PositiveInt = 7
    max_retained: Optional[PositiveInt] = None
    auto_publish: bool = True
    fetch_every: PositiveInt = 7


class PhysicalModelCfg(BaseModel):
    model_config = ConfigDict(extra="forbid")

    T_mode: Literal["canonical", "grand_canonical", "microcanonical"]
    # Keep as Any for user-provided objects; allow arbitrary types at top-level GAConfig
    calculator: Any


# --- Per-method hash configs -------------------------------------------------
class _HashBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TSFHashCfg(_HashBase):
    method: Literal["tsf"] = "tsf"
    kmax: PositiveInt = 3
    modes: Optional[List[Tuple[int, int, int]]] = None
    per_species: bool = True
    ps_grid: PosFloat = 1e-1
    lattice_grid: PosFloat = 2e-2
    e_grid: PosFloat = 1e-3
    v_grid: PosFloat = 1e-2
    include_energy: bool = True
    include_volume: bool = True
    use_spglib: bool = False
    symprec: PosFloat = 1e-3
    angle_tolerance: float = -1.0  # spglib default for "auto"
    chunk_size: PositiveInt = 50_000
    debug: bool = False

    @field_validator("modes")
    @classmethod
    def _modes_or_none_nonempty(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("modes must be None or a non-empty list")
        return v


class RDFHashCfg(_HashBase):
    method: Literal["rdf"] = "rdf"
    r_max: PosFloat = 10.0
    bin_width: PosFloat = 0.02
    density_grid: PosFloat = 1e-4
    e_grid: PosFloat = 1e-2
    v_grid: PosFloat = 1e-2
    symprec: PosFloat = 1e-3
    debug: bool = False


class RBFHashCfg(_HashBase):
    method: Literal["rbf"] = "rbf"
    number_of_bins: PositiveInt = 200
    bin_volume_normalize: bool = False
    number_of_atoms_normalize: bool = False
    density_normalize: bool = False
    e_grid: PosFloat = 1e-2
    v_grid: PosFloat = 1e-2
    symprec: PosFloat = 1e-3
    debug: bool = False


# Discriminated union by "method"
HashMapConfig = Annotated[
    Union[RDFHashCfg, TSFHashCfg, RBFHashCfg],
    Field(discriminator="method"),
]


# -----------------------------------------------------------------------------
# Top-level configuration
# -----------------------------------------------------------------------------
class GAConfig(BaseModel):
    """Top-level configuration for BANS-GA (validated via Pydantic v2).

    This model is intentionally strict (extra=forbid) to catch typos early, but
    remains assignment-validating to support programmatic modification during
    experiments.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,  # calculators, callables, etc.
    )

    # Global GA controls
    initial_generation: NonNegativeInt = 0
    max_generations: PositiveInt = 100
    min_size_for_filter: PositiveInt = 10
    foreigners: NonNegativeInt = 0

    save_logs: bool = True
    output_path: Path = Path(".")
    resume: bool = True
    resume_mode: ResumeMode = ResumeMode.FOLDERS_ALL

    # Subsystems
    population: PopulationParams = Field(default_factory=PopulationParams)
    thermostat: ThermostatParams = Field(default_factory=ThermostatParams)
    evaluator: EvaluatorParams = Field(default_factory=EvaluatorParams)

    multiobjective: SelectionParams = Field(default_factory=SelectionParams)

    variation: VariationParams = Field(default_factory=VariationParams)
    mutation_funcs: List[Callable[..., Any]] = Field(default_factory=list)
    crossover_funcs: List[Callable[..., Any]] = Field(default_factory=list)

    simulator: SimulatorParams = Field(default_factory=SimulatorParams)
    convergence: ConvergenceParams = Field(default_factory=ConvergenceParams)

    hashmap: HashMapConfig = Field(default_factory=TSFHashCfg)

    agentic: AgenticParams = Field(default_factory=AgenticParams)

    hise: Optional[HiSEParams] = Field(
        default=None,
        description="Hierarchical Supercell Escalation (coarse-to-fine) settings.",
    )
    generative_model: Any = None

    # extras “legacy”
    initial_population: Optional[List[Any]] = None

    debug: bool = False
    rng: Optional[int] = None

    @field_validator("foreigners", mode="before")
    @classmethod
    def cast_foreigners_int(cls, v):
        return int(v) if v is not None else 0

    @model_validator(mode="after")
    def check_relationships(self):
        m = self.multiobjective.size
        if self.min_size_for_filter < m:
            # keep strictness by adjusting upward while notifying via ValueError would be harsh
            # so we auto-correct and rely on logs by raising a warning-equivalent exception type
            self.min_size_for_filter = m
        return self
