"""Run directly with uv run python -m tests.browser_smoke (requires Chromium).

Uses a temporary workspace. Captures screenshots in ignored artifacts/.
"""

import re
from pathlib import Path

from tests.test_tags_themes import contrast

ROOT = Path(__file__).resolve().parents[1]


def check_card_contrast(page):
    colors = page.locator(".ticket-title").first.evaluate("""element => ({
        foreground: getComputedStyle(element).color,
        background: getComputedStyle(element.closest('.ticket-card')).backgroundColor
    })""")

    def luminance(rgb):
        channels = [int(x) / 255 for x in re.findall(r"\d+", rgb)[:3]]
        linear = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in channels]
        return sum(x * weight for x, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    values = sorted(luminance(value) for value in colors.values())
    ratio = (values[1] + 0.05) / (values[0] + 0.05)
    assert ratio >= 4.5, f"Card title contrast too low: {ratio:.2f}:1"


def check_field_contrast(page):
    values = page.get_by_label("Search work", exact=True).evaluate("""input => {
        const color = value => {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = value; ctx.fillRect(0, 0, 1, 1);
            return '#' + [...ctx.getImageData(0, 0, 1, 1).data].slice(0, 3)
                .map(x => x.toString(16).padStart(2, '0')).join('');
        };
        const field = input.closest('.q-field');
        return {
            canvas: color(getComputedStyle(document.body).backgroundColor),
            background: color(getComputedStyle(field.querySelector('.q-field__control')).backgroundColor),
            text: color(getComputedStyle(input).color),
            label: color(getComputedStyle(field.querySelector('.q-field__label')).color),
        };
    }""")
    for i in (1, 3, 5):
        assert int(values["background"][i : i + 2], 16) < int(values["canvas"][i : i + 2], 16), values
    for role in ("text", "label"):
        assert contrast(values[role], values["background"]) >= 4.5, values
