"""Big Five trait models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Self

from personalitygen.constants import UNIT_RANGE_MAX, UNIT_RANGE_MIN
from personalitygen.enums import LifeStage
from personalitygen.randomness import RandomSource, random_gaussian


def _validate_unit_range(*values: float) -> None:
    for value in values:
        if not (UNIT_RANGE_MIN <= value <= UNIT_RANGE_MAX):
            raise ValueError(
                "All trait components must be in the range 0.0...1.0"
            )


def _format_score(value: float) -> str:
    return format(value, ".2g")


_TRAIT_SAMPLE_MIN = 0.01


@dataclass(frozen=True, slots=True)
class _TraitConfig:
    stddev: float
    means_by_stage: dict[LifeStage, tuple[float, float, float]]


def _sample_trait(
    life_stage: LifeStage,
    config: _TraitConfig,
    *,
    rng: RandomSource | None = None,
) -> tuple[float, float, float]:
    means = config.means_by_stage.get(life_stage)
    if means is None:
        raise ValueError(f"Unsupported life stage: {life_stage}")

    mean_a, mean_b, mean_c = means
    return (
        random_gaussian(
            stddev=config.stddev,
            mean=mean_a,
            max_value=UNIT_RANGE_MAX,
            min_value=_TRAIT_SAMPLE_MIN,
            rng=rng,
        ),
        random_gaussian(
            stddev=config.stddev,
            mean=mean_b,
            max_value=UNIT_RANGE_MAX,
            min_value=_TRAIT_SAMPLE_MIN,
            rng=rng,
        ),
        random_gaussian(
            stddev=config.stddev,
            mean=mean_c,
            max_value=UNIT_RANGE_MAX,
            min_value=_TRAIT_SAMPLE_MIN,
            rng=rng,
        ),
    )


_OPENNESS_CONFIG = _TraitConfig(
    stddev=0.16,
    means_by_stage={
        LifeStage.CHILD: (0.80, 0.85, 0.85),
        LifeStage.YOUNG_ADULT: (0.70, 0.75, 0.75),
        LifeStage.ADULT: (0.60, 0.65, 0.65),
    },
)

_CONSCIENTIOUSNESS_CONFIG = _TraitConfig(
    stddev=0.22,
    means_by_stage={
        LifeStage.CHILD: (0.50, 0.55, 0.50),
        LifeStage.YOUNG_ADULT: (0.60, 0.65, 0.60),
        LifeStage.ADULT: (0.70, 0.75, 0.70),
    },
)

_EXTRAVERSION_CONFIG = _TraitConfig(
    stddev=0.27,
    means_by_stage={
        LifeStage.CHILD: (0.72, 0.70, 0.72),
        LifeStage.YOUNG_ADULT: (0.62, 0.60, 0.62),
        LifeStage.ADULT: (0.52, 0.50, 0.52),
    },
)

_AGREEABLENESS_CONFIG = _TraitConfig(
    stddev=0.18,
    means_by_stage={
        LifeStage.CHILD: (0.55, 0.55, 0.40),
        LifeStage.YOUNG_ADULT: (0.65, 0.65, 0.50),
        LifeStage.ADULT: (0.75, 0.75, 0.60),
    },
)

_NEUROTICISM_CONFIG = _TraitConfig(
    stddev=0.32,
    means_by_stage={
        LifeStage.CHILD: (0.70, 0.60, 0.55),
        LifeStage.YOUNG_ADULT: (0.60, 0.50, 0.45),
        LifeStage.ADULT: (0.50, 0.40, 0.35),
    },
)


@dataclass(frozen=True, slots=True)
class BigFiveOpenness:
    aesthetic_sensitivity_score: float
    creative_imagination_score: float
    intellectual_curiosity_score: float
    score: float = field(init=False)

    def __post_init__(self) -> None:
        _validate_unit_range(
            self.aesthetic_sensitivity_score,
            self.creative_imagination_score,
            self.intellectual_curiosity_score,
        )
        object.__setattr__(
            self,
            "score",
            (
                self.aesthetic_sensitivity_score
                + self.creative_imagination_score
                + self.intellectual_curiosity_score
            )
            / 3,
        )

    @classmethod
    def random(
        cls, life_stage: LifeStage, *, rng: RandomSource | None = None
    ) -> Self:
        (
            aesthetic_sensitivity,
            creative_imagination,
            intellectual_curiosity,
        ) = _sample_trait(life_stage, _OPENNESS_CONFIG, rng=rng)
        return cls(
            aesthetic_sensitivity_score=aesthetic_sensitivity,
            creative_imagination_score=creative_imagination,
            intellectual_curiosity_score=intellectual_curiosity,
        )

    def __str__(self) -> str:
        return (
            f"{_format_score(self.score)} "
            f"{{A:{_format_score(self.aesthetic_sensitivity_score)} "
            f"C:{_format_score(self.creative_imagination_score)} "
            f"I:{_format_score(self.intellectual_curiosity_score)}}}"
        )


@dataclass(frozen=True, slots=True)
class BigFiveConscientiousness:
    organization_score: float
    responsibility_score: float
    productivity_score: float
    score: float = field(init=False)

    def __post_init__(self) -> None:
        _validate_unit_range(
            self.organization_score,
            self.responsibility_score,
            self.productivity_score,
        )
        object.__setattr__(
            self,
            "score",
            (
                self.organization_score
                + self.responsibility_score
                + self.productivity_score
            )
            / 3,
        )

    @classmethod
    def random(
        cls, life_stage: LifeStage, *, rng: RandomSource | None = None
    ) -> Self:
        organization, responsibility, productivity = _sample_trait(
            life_stage, _CONSCIENTIOUSNESS_CONFIG, rng=rng
        )
        return cls(
            organization_score=organization,
            responsibility_score=responsibility,
            productivity_score=productivity,
        )

    def __str__(self) -> str:
        return (
            f"{_format_score(self.score)} "
            f"{{O:{_format_score(self.organization_score)} "
            f"R:{_format_score(self.responsibility_score)} "
            f"P:{_format_score(self.productivity_score)}}}"
        )


@dataclass(frozen=True, slots=True)
class BigFiveExtraversion:
    assertiveness_score: float
    sociability_score: float
    energy_level_score: float
    score: float = field(init=False)

    def __post_init__(self) -> None:
        _validate_unit_range(
            self.assertiveness_score,
            self.sociability_score,
            self.energy_level_score,
        )
        object.__setattr__(
            self,
            "score",
            (
                self.assertiveness_score
                + self.sociability_score
                + self.energy_level_score
            )
            / 3,
        )

    @classmethod
    def random(
        cls, life_stage: LifeStage, *, rng: RandomSource | None = None
    ) -> Self:
        assertiveness, sociability, energy_level = _sample_trait(
            life_stage, _EXTRAVERSION_CONFIG, rng=rng
        )
        return cls(
            assertiveness_score=assertiveness,
            sociability_score=sociability,
            energy_level_score=energy_level,
        )

    def __str__(self) -> str:
        return (
            f"{_format_score(self.score)} "
            f"{{A:{_format_score(self.assertiveness_score)} "
            f"S:{_format_score(self.sociability_score)} "
            f"E:{_format_score(self.energy_level_score)}}}"
        )


@dataclass(frozen=True, slots=True)
class BigFiveAgreeableness:
    compassion_score: float
    respectfulness_score: float
    trust_score: float
    score: float = field(init=False)

    def __post_init__(self) -> None:
        _validate_unit_range(
            self.compassion_score,
            self.respectfulness_score,
            self.trust_score,
        )
        object.__setattr__(
            self,
            "score",
            (
                self.compassion_score
                + self.respectfulness_score
                + self.trust_score
            )
            / 3,
        )

    @classmethod
    def random(
        cls, life_stage: LifeStage, *, rng: RandomSource | None = None
    ) -> Self:
        compassion, respectfulness, trust = _sample_trait(
            life_stage, _AGREEABLENESS_CONFIG, rng=rng
        )
        return cls(
            compassion_score=compassion,
            respectfulness_score=respectfulness,
            trust_score=trust,
        )

    def __str__(self) -> str:
        return (
            f"{_format_score(self.score)} "
            f"{{C:{_format_score(self.compassion_score)} "
            f"R:{_format_score(self.respectfulness_score)} "
            f"T:{_format_score(self.trust_score)}}}"
        )


@dataclass(frozen=True, slots=True)
class BigFiveNeuroticism:
    anxiety_score: float
    emotional_volatility_score: float
    depression_score: float
    score: float = field(init=False)

    def __post_init__(self) -> None:
        _validate_unit_range(
            self.anxiety_score,
            self.emotional_volatility_score,
            self.depression_score,
        )
        object.__setattr__(
            self,
            "score",
            (
                self.anxiety_score
                + self.emotional_volatility_score
                + self.depression_score
            )
            / 3,
        )

    @classmethod
    def random(
        cls, life_stage: LifeStage, *, rng: RandomSource | None = None
    ) -> Self:
        anxiety, emotional_volatility, depression = _sample_trait(
            life_stage, _NEUROTICISM_CONFIG, rng=rng
        )
        return cls(
            anxiety_score=anxiety,
            emotional_volatility_score=emotional_volatility,
            depression_score=depression,
        )

    def __str__(self) -> str:
        return (
            f"{_format_score(self.score)} "
            f"{{A:{_format_score(self.anxiety_score)} "
            f"E:{_format_score(self.emotional_volatility_score)} "
            f"D:{_format_score(self.depression_score)}}}"
        )
