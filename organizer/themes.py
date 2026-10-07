"""Local theme tokens, adapted from palette families. No external theme assets required."""

FAMILIES = {
    "organize": {
        "name": "Organize",
        "description": "The original violet workspace.",
        "source": "Original",
        "url": "",
        "colors": ["#8b70ef", "#24a99a", "#d99a30", "#ed7d75", "#6299e8"],
        "light": [
            "#f6f5f2",
            "#ffffff",
            "#f1f0f6",
            "#282738",
            "#656477",
            "#dedde7",
            "#7053c1",
            "#ede8fa",
            "#7053c1",
        ],
        "dark": [
            "#171922",
            "#20232f",
            "#292d3b",
            "#f0eff7",
            "#b0b2c5",
            "#3c4053",
            "#c3adff",
            "#35304b",
            "#7053c1",
        ],
    },
    "shiny-mint": {
        "name": "Shiny Mint",
        "description": "Fresh green surfaces, inspired by Minty and Darkly.",
        "source": "bslib / Bootswatch",
        "url": "https://rstudio.github.io/bslib/articles/theming/index.html",
        "colors": ["#7a69bd", "#339a83", "#d79a37", "#e78183", "#60a2c5"],
        "light": [
            "#f1f8f5",
            "#ffffff",
            "#e5f1eb",
            "#233b32",
            "#52685f",
            "#cbded3",
            "#246e59",
            "#d9eee3",
            "#246e59",
        ],
        "dark": [
            "#19231f",
            "#23322c",
            "#2c3e35",
            "#edf6ef",
            "#b5c8bd",
            "#4e6357",
            "#94d5b4",
            "#304b3d",
            "#28694f",
        ],
    },
    "viridis": {
        "name": "Viridis",
        "description": "Purple, blue, teal, and gold from the ggplot2 palette family.",
        "source": "ggplot2 / viridisLite",
        "url": "https://ggplot2.tidyverse.org/reference/scale_viridis.html",
        "colors": ["#7a4988", "#21918c", "#9c9f26", "#5ec962", "#3b528b"],
        "light": [
            "#f4f7f6",
            "#ffffff",
            "#e8efed",
            "#253638",
            "#52656a",
            "#cddcda",
            "#276c71",
            "#dcefed",
            "#276c71",
        ],
        "dark": [
            "#191b2a",
            "#242638",
            "#303449",
            "#f2f3f7",
            "#bac4cd",
            "#4f566f",
            "#7bd4c7",
            "#2b484b",
            "#29646a",
        ],
    },
    "brewer": {
        "name": "Brewer Garden",
        "description": "Balanced categorical accents inspired by ColorBrewer Set2.",
        "source": "ggplot2 / ColorBrewer",
        "url": "https://ggplot2.tidyverse.org/reference/scale_brewer.html",
        "colors": ["#b676a4", "#429e84", "#c79a30", "#da895b", "#7b91bd"],
        "light": [
            "#faf6ef",
            "#fffdf8",
            "#f0eadd",
            "#343329",
            "#686356",
            "#ddd5c4",
            "#526c37",
            "#e6ecd9",
            "#526c37",
        ],
        "dark": [
            "#20231d",
            "#2b3026",
            "#373e31",
            "#f1f1e5",
            "#c0c5b3",
            "#555e49",
            "#bbd691",
            "#3e4c2f",
            "#50663a",
        ],
    },
    "material": {
        "name": "Material Blue",
        "description": "Tonal blue surfaces, inspired by Google Material color roles.",
        "source": "Google Material 3",
        "url": "https://m3.material.io/styles/color/roles",
        "colors": ["#8c77be", "#399778", "#c59823", "#ce6c65", "#5b91d9"],
        "light": [
            "#f7f9ff",
            "#ffffff",
            "#edf1f9",
            "#202a3a",
            "#586477",
            "#d1dbea",
            "#255eaa",
            "#deebff",
            "#255eaa",
        ],
        "dark": [
            "#151c28",
            "#1f2938",
            "#2b374a",
            "#eaf0fc",
            "#b6c5db",
            "#485c77",
            "#a8c9ff",
            "#2b4465",
            "#2a5d9b",
        ],
    },
}
TOKEN_NAMES = (
    "canvas",
    "surface",
    "surface-soft",
    "text",
    "muted",
    "line",
    "accent",
    "accent-soft",
    "button",
)


def css(family):
    theme = FAMILIES[family]
    result = []
    for mode in ("light", "dark"):
        tokens = dict(zip(TOKEN_NAMES, theme[mode]))
        tokens.update(
            {
                "focus": tokens["accent"],
                "on-button": "#ffffff",
                "positive": "#08745f" if mode == "light" else "#74d9b9",
                "warning": "#895812" if mode == "light" else "#f3c178",
                "negative": "#b04447" if mode == "light" else "#ffa3a3",
                "shadow": "0 3px 12px #29243b06" if mode == "light" else "0 3px 12px #00000012",
                "q-primary": tokens["button"],
            }
        )
        for index, color in enumerate(theme["colors"]):
            tokens[f"palette-{index}"] = color
        declarations = ";".join(f"--{name}:{value}" for name, value in tokens.items())
        selector = "body" if mode == "light" else "body.body--dark"
        result.append(f"{selector}{{{declarations}}}")
    return "\n".join(result)


def project_colors(family):
    return dict(zip(("Violet", "Teal", "Amber", "Coral", "Blue"), FAMILIES[family]["colors"]))
