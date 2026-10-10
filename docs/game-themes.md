# Game-inspired styles - 2026-10-10

Gary explicitly selected strong game-inspired character and game names as selector labels. He then
expanded the authorized pair (Halo and World of Warcraft) to include all four supplied examples.
There are six new presets, bringing the catalog to 50 families / 100 Light-Dark combinations.
They extend the existing Preferences selector and preview; the saved/default palette is unchanged.

| Name and inspiration | Implementation |
| --- | --- |
| [Persona 5](https://persona.atlus.com/p5r/) | Crimson contrast, Impact headings, hard card edges, offset shadows, diagonal header accent. |
| [Destiny 2](https://www.bungie.net/7/en/Destiny) | Slate inventory framing, spaced light-weight headings, concentric outlines, circular stat framing. |
| [Alien: Isolation](https://www.alienisolation.com/) | Green terminal accents, Consolas text, sharp bordered panels, no shadows. |
| [The Division](https://www.ubisoft.com/en-us/game/the-division/the-division-2) | Orange HUD rails, technical headings, glass outer layers, opaque reading surfaces. |
| [Halo](https://www.halowaypoint.com/) | Cyan/navy tactical grid, angular corner framing, Bahnschrift headings, technical lane labels. |
| [World of Warcraft](https://worldofwarcraft.blizzard.com/) | Parchment/stone, bronze bevels, double-line journal framing, Georgia headings. |

The CSS and assets are original adaptations, not official game UI kits or copied game resources.
System font stacks use fallbacks; no fonts or assets download at runtime. Color roles are in
`organizer/game_themes.py`; independent stylesheets are in `organizer/game_styles/`. Only the selected
style is included in the replaceable theme stylesheet, so reverting to a standard palette clears it.

Implementation choices: keep cards horizontal and task titles visible; preserve normal pointers,
keyboard focus and project/Feature bands. Avoid full-screen wipes, continuous flicker, scanlines and
text blur in the working app. Limited hover transitions respect reduced-motion preferences. Decorative
corner brackets do not receive pointer events. Light modes are authored companions to dark inspirations.
These choices apply the supplied flavor-versus-usability guidance, not a claim to exactly copy a game.

The research reference for Alien blocked automated retrieval; its proposed vocabulary comes from
Gary's supplied example. [Halo settings](https://support.halowaypoint.com/hc/en-us/articles/4407649252116-Guide-to-Halo-Infinite-Game-Settings)
and [Bungie's accessibility notes](https://www.bungie.net/7/en/News/Article/destiny-2-accessibility-set)
inform preserving presentation controls and semantic color meanings. User acceptance of the final
rendered presets remains separate from automated checks. See development-status.md for evidence.
