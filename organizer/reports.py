"""Portable, script-free reports. Escape every value originating in project data."""

from html import escape

from .store import EFFORT, now, progress, ticket


def html_report(items, effort_scale="T-shirt"):
    def esc(value):
        return escape(str(value), quote=True)

    done, total = progress(items)
    cards = []
    by_id = {x["id"]: x for x in items}
    for item in items:
        effort = (
            EFFORT[item["effort"]]
            if effort_scale == "T-shirt" or item["effort"] is None
            else str(item["effort"])
        )
        parent = by_id.get(item["parent_id"])
        parent_text = f" · Under {esc(ticket(parent))}" if parent else ""
        cards.append(f"""<article><p class="meta">{esc(ticket(item))} · {esc(item["kind"])}{parent_text}</p>
            <h2>{esc(item["title"])}</h2><p>{esc(item["status"])} · Effort: {effort}</p>
            <p class="description">{esc(item["description"])}</p>
            {('<p>Repository: <a href="' + esc(item["repository_url"]) + '">' + esc(item["repository_url"]) + "</a></p>") if item["repository_url"] else ""}
            <p>{" · ".join(esc(tag) for tag in item["tags"])}</p>
            {("<p>Blocked: " + esc(item["blocked"]) + "</p>") if item["blocked"] else ""}</article>""")
    return f"""<!doctype html><html lang="en"><meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
        <title>Organize — progress report</title><style>
        body{{font:16px/1.6 system-ui,sans-serif;background:#f6f5f2;color:#252737;max-width:1000px;margin:40px auto;padding:0 24px}}
        article{{background:white;border:1px solid #dcdce6;border-left:4px solid #7357cc;border-radius:12px;padding:18px 24px;margin:16px 0;break-inside:avoid}}
        h2{{font-size:20px;margin:4px 0}}.meta{{color:#5d6070;font-size:13px}}.description{{white-space:pre-wrap;overflow-wrap:anywhere}}
        @media print{{body{{background:white;margin:0}}article{{box-shadow:none}}}}
        </style><h1>Project progress</h1><p>Read-only snapshot · {esc(now())}</p>
        <p><strong>{done} of {total} committed leaf items completed</strong></p>
        <p>Parents are not counted again. Ideas and cancelled work are excluded. This report does not update automatically.</p>
        {"".join(cards)}</html>"""
