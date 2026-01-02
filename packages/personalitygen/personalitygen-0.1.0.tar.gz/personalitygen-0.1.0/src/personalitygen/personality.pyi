from dataclasses import dataclass
from enum import Enum
from personalitygen.enums import LifeStage as LifeStage, PriorityLevel as PriorityLevel
from personalitygen.randomness import RandomSource as RandomSource
from personalitygen.traits import BigFiveAgreeableness as BigFiveAgreeableness, BigFiveConscientiousness as BigFiveConscientiousness, BigFiveExtraversion as BigFiveExtraversion, BigFiveNeuroticism as BigFiveNeuroticism, BigFiveOpenness as BigFiveOpenness
from typing import Self

class BigFiveConflictResolutionStyle(str, Enum):
    AVOIDING = 'avoiding'
    OBLIGING = 'obliging'
    INTEGRATING = 'integrating'
    DOMINATING = 'dominating'
    COMPROMISING = 'compromising'
    @classmethod
    def random(cls, trait_configuration: BigFiveTraitConfiguration, *, rng: RandomSource | None = None) -> Self: ...

@dataclass(frozen=True, slots=True)
class BigFiveTraitConfiguration:
    openness: BigFiveOpenness
    conscientiousness: BigFiveConscientiousness
    extraversion: BigFiveExtraversion
    agreeableness: BigFiveAgreeableness
    neuroticism: BigFiveNeuroticism
    @classmethod
    def random(cls, life_stage: LifeStage, *, rng: RandomSource | None = None) -> Self: ...

@dataclass(frozen=True, slots=True)
class BigFiveConflictResolutionConfiguration:
    conflict_resolution_style: BigFiveConflictResolutionStyle
    concern_for_self: PriorityLevel
    concern_for_others: PriorityLevel
    @classmethod
    def random(cls, trait_configuration: BigFiveTraitConfiguration, *, rng: RandomSource | None = None) -> Self: ...

@dataclass(frozen=True, slots=True)
class BigFivePersonality:
    trait_configuration: BigFiveTraitConfiguration
    conflict_resolution_configuration: BigFiveConflictResolutionConfiguration
    @classmethod
    def random(cls, life_stage: LifeStage, *, rng: RandomSource | None = None) -> Self: ...
