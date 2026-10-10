# Palette sources and decisions

## 2026-10-10: Sprig 1.0.1

Explicit request: remove the workspace stars decoration; add the referenced ggplot gray/pastel look,
shinythemes, Apple HIG, Microsoft Fluent and Carbon palettes. Implementation choice: include all 16
families listed on the shinythemes page, with Light and Dark adaptations of each, plus one family for
each other source. Retain all existing choices, the default, typography, compact layout and live preview.
This yields 44 families / 88 variants. No new navigation or theme controls.

| Selector entry | Source | Adaptation |
| --- | --- | --- |
| GGplot Gray Pastel | [ggplot2 theme_gray](https://ggplot2.tidyverse.org/reference/ggtheme.html) | Gray/white surfaces; custom soft red, blue and green accents. Plot themes control non-data appearance, not the categorical color scale. The pastel colors are authored for this request. |
| Shiny Cerulean, Cosmo, Cyborg, Darkly, Flatly, Journal, Lumen, Paper, Readable, Sandstone, Simplex, Slate, Spacelab, Superhero, United, Yeti | [shinythemes gallery](https://rstudio.github.io/shinythemes/) and [bundled Bootswatch 3 CSS](https://github.com/rstudio/shinythemes/tree/main/inst/shinythemes/css) | Use each source's accent colors, retain characteristic dark foundations where applicable, and author a complementary mode. No Bootstrap CSS is bundled. |
| Apple HIG | [Apple color guidance](https://developer.apple.com/design/human-interface-guidelines/color) | Neutral layers, blue actions and multicolor accents. Static web adaptation, not Apple's dynamic native colors, glass materials or accessibility settings. |
| Microsoft Fluent | [Fluent 2 color](https://fluent2.microsoft.design/color) | Neutral surfaces and restrained blue actions, with separate foreground and selected-state tokens. No Fluent components or full system conformance implied. |
| IBM Carbon | [Carbon color](https://carbondesignsystem.com/guidelines/color/overview/) | Gray 10 light and Gray 100 dark foundations, layered neutrals and blue actions. Preserves Sprig's existing control surfaces and card geometry. |

The Shiny source palettes originate in Bootswatch by Thomas Park (MIT licensed), as credited by
shinythemes. Only palette values inform these authored tokens; no upstream stylesheet, font, icon or
script is bundled. Names identify inspirations, not affiliation or certification.

Implementation constants live in `organizer/theme_catalog.py`, registered by `organizer/themes.py`.
The nine roles remain canvas, surface, soft surface, text, muted text, border, accent, accent container
and button. Bright colors remain available on decorative bands; foreground and button colors are
adjusted independently to retain readable text. Dark adaptations brighten foregrounds rather than
inverting the page. Named statuses and keyboard focus remain independent of palette identity.

Validation uses the existing token-contrast and Chromium suites across every mode, including card
text, field labels, source placement, persistent selection and the mounted Preferences preview.
Automated checks do not establish a full accessibility audit or user acceptance of every palette.
