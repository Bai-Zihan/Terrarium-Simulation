# Future Predator, Pest-Control, and Food-Web Plan

Small predators are intentionally not active in the current CLI crafting loop.
They should wait until the survival simulation has explicit prey populations,
outbreak pressure, and escape-risk handling. In a 1L closed bottle, adding
predators too early can make the system feel arbitrary because their food web
effects are strong while their bodies are easy to overlook.

The same delay applies to the fuller food-web model. The current simulation
only needs lightweight visible interactions: decomposers reduce mold/litter,
small consumers graze films, and risky consumers may mark tender plants when
food is scarce. More detailed predator/prey pressure, disease, competition,
parasites, and multi-stage outbreaks belong with the predator system instead
of the current basic survival loop.

## Candidate Future Animals

- Predatory mite: could suppress soil mites, springtails, and fungus gnat larvae.
- Rove beetle larva: useful in larger vivaria, but probably too disruptive for 1L.
- Pseudoscorpion: interesting micro-predator, needs tiny crevices and stable prey.
- Micro flatworm: possible wet-film predator, but can be invasive and hard to model.
- Tiny centipede: visually clear predator, but likely too large for the default bottle.

## Rules Before Activation

- Predators should require an established prey group rather than being generally addable.
- They should increase stress if prey becomes scarce.
- They should have low maximum counts and high oxygen sensitivity.
- They should not reproduce unless prey density, cover, and free volume are all favorable.
- They should be optional and never required for basic terrarium survival.

## Deferred Food-Web Scope

- Explicit prey preference and predator selectivity.
- Visible outbreak pressure, such as mites clustering, larvae feeding lines, or prey hiding.
- Competition between consumers using the same biofilm, fungi, or detritus layer.
- Disease or parasite pressure only after there are visible symptoms the player can observe.
- Juvenile/adult stages for animals whose population changes should not happen instantly.
- Predator starvation, migration to refuges, and failed control when prey hides in cracks.

## Activation Gates

1. Animal movement is implemented enough that prey and predator can occupy different refuges.
2. Hardscape cracks, grooves, underside cover, and damp litter pockets affect access to prey.
3. The UI can show visible evidence of pressure without requiring numeric diagnosis.
4. Long-running bottles have been balanced without predators first.
5. Predators can be paused or excluded from basic play without breaking the ecosystem model.
