# personalitygen

![personalitygen social preview](.github/social%20preview/personalitygen_social_preview.jpg)

`personalitygen` generates and manages simulated human-like personalities based on the Big Five (OCEAN) model. It is designed for
simulation, storytelling, and testing scenarios where you want plausible, varied personality profiles without running surveys.

## Intent and scope

- Generate full Big Five profiles with sub-trait components and aggregate scores.
- Bias outputs by life stage using tuned Gaussian distributions (child, young adult, adult).
- Derive a conflict-resolution style from trait weights, plus mapped concern-for-self/others.
- Support deterministic generation by accepting a seeded random source.
- Stay lightweight and dependency-free (pure Python).

This package is not a clinical assessment tool and does not implement questionnaires or scoring rubrics.

## Model overview

- Big Five traits: openness, conscientiousness, extraversion, agreeableness, neuroticism.
- Each trait is composed of three sub-traits and a weighted aggregate score.
- Life stage influences distribution means and standard deviations for sampling.
- Conflict-resolution style is selected from avoiding, obliging, integrating, dominating, or compromising based on trait scores.

## Usage

```python
from personalitygen import BigFivePersonality, LifeStage

personality = BigFivePersonality.random(LifeStage.ADULT)
print(personality.trait_configuration)
print(personality.conflict_resolution_configuration)
```

If you want deterministic output, pass a seeded random number generator:

```python
import random
from personalitygen import BigFiveTraitConfiguration, LifeStage

rng = random.Random(42)
traits = BigFiveTraitConfiguration.random(LifeStage.YOUNG_ADULT, rng=rng)
print(traits)
```

## Development

```bash
pdm install --group dev
pdm run test
```
