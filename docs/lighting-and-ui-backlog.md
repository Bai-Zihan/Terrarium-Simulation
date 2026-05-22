# Lighting and Future View Backlog

These items are intentionally deferred so the current CLI simulation can stay
focused on controllable placement, survival, and visible observation.

## Window Environment Detail

The current model supports north/east/south/west windows, bottle facing angle,
a moss lamp, direct/diffuse/mixed window exposure, automatic season, and
automatic daily weather. Future window environment work should add external modifiers that
players can choose without changing the bottle itself:

- distance from the window, such as sill, nearby table, or back of room
- curtain or shade level, especially sheer curtain versus direct glass
- optional room temperature bias near windows

These should remain visible through player-facing evidence: drying pattern,
condensation timing, leaf posture, visible shade, and local moss color, rather
than hidden diagnostic readouts.

## Pseudo-3D Pixel UI View

The simulation now uses a compass angle convention: 0=N, 90=E, 180=S, 270=W.
Future UI work can use the same convention to rotate the bottle and render a
fake-3D pixel view:

- camera/view angle changes which side of the bottle is visible
- window and lamp direction cast highlights and shade lines
- hardscape top/side/crack/groove attachment surfaces can become sprite layers
- plants can lean toward light, press against hardscape, or trail over surfaces
- condensation, biofilm, mold, and dry glass can be rendered as visible overlays

The UI should consume `pseudo3d_scene()` and the placement light fields rather
than inventing a separate coordinate system.
