from dataclasses import dataclass, field
from personalitygen.constants import UNIT_RANGE_MAX as UNIT_RANGE_MAX, UNIT_RANGE_MIN as UNIT_RANGE_MIN
from personalitygen.enums import LifeStage as LifeStage
from personalitygen.randomness import RandomSource as RandomSource, random_gaussian as random_gaussian
from typing import Self

@dataclass(frozen=True, slots=True)
class _TraitConfig:
    stddev: float
    means_by_stage: dict[LifeStage, tuple[float, float, float]]

@dataclass(frozen=True, slots=True)
class BigFiveOpenness:
    aesthetic_sensitivity_score: float
    creative_imagination_score: float
    intellectual_curiosity_score: float
    score: float = field(init=False)
    def __post_init__(self) -> None: ...
    @classmethod
    def random(cls, life_stage: LifeStage, *, rng: RandomSource | None = None) -> Self: ...

@dataclass(frozen=True, slots=True)
class BigFiveConscientiousness:
    organization_score: float
    responsibility_score: float
    productivity_score: float
    score: float = field(init=False)
    def __post_init__(self) -> None: ...
    @classmethod
    def random(cls, life_stage: LifeStage, *, rng: RandomSource | None = None) -> Self: ...

@dataclass(frozen=True, slots=True)
class BigFiveExtraversion:
    assertiveness_score: float
    sociability_score: float
    energy_level_score: float
    score: float = field(init=False)
    def __post_init__(self) -> None: ...
    @classmethod
    def random(cls, life_stage: LifeStage, *, rng: RandomSource | None = None) -> Self: ...

@dataclass(frozen=True, slots=True)
class BigFiveAgreeableness:
    compassion_score: float
    respectfulness_score: float
    trust_score: float
    score: float = field(init=False)
    def __post_init__(self) -> None: ...
    @classmethod
    def random(cls, life_stage: LifeStage, *, rng: RandomSource | None = None) -> Self: ...

@dataclass(frozen=True, slots=True)
class BigFiveNeuroticism:
    anxiety_score: float
    emotional_volatility_score: float
    depression_score: float
    score: float = field(init=False)
    def __post_init__(self) -> None: ...
    @classmethod
    def random(cls, life_stage: LifeStage, *, rng: RandomSource | None = None) -> Self: ...
