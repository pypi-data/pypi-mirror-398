from __future__ import annotations

from typing import Dict, List


def build_prompt(
    query: str,
    context: List[Dict],
    top_n: int = 12,
    max_chars_per_hit: int = 420,
) -> List[Dict]:
    context = sorted(
        context,
        key=lambda x: float(
            x.get("score", 0.0),
        ),
        reverse=True,
    )[:top_n]

    def fmt(hit: Dict, i: int) -> str:
        root = hit.get("root", "")
        chunk_id = hit.get("chunk_id", -1)
        score = float(hit.get("score", 0.0))
        url = hit.get("url", "")
        text = (hit.get("text") or "").strip().replace("\n", " ")
        text = text[:max_chars_per_hit]
        url_part = f" url={url}" if url else ""
        return (
            f"[{i}] root={root} chunk_id={chunk_id}{url_part} score={score:.2f}\n{text}"
        )

    evidence = "\n\n".join(fmt(hit, i + 1) for i, hit in enumerate(context))

    content = "\n".join(
        [
            "تو یک داور دقیق برای انتخاب «بهترین root» هستی.",
            "",
            "وظیفه:",
            "1) root برنده را انتخاب کن: rootی که بیشترین ارتباط مستقیم با سؤال دارد.",
            "2) استدلال کوتاه و شفاف بده که چرا این root برنده است (فقط بر اساس evidence).",
            "3) یک متن پیشنهادی کوتاه برای پاسخ/شروع پاسخ تولید کن که بر اساس همان root باشد.",
            "",
            "قواعد:",
            "- فقط از evidence استفاده کن. چیزی را حدس نزن.",
            "- اگر چند root تقریباً برابرند، دلیل انتخاب را دقیق بگو.",
            "- اگر evidence کافی نیست، با قطعیت پایین انتخاب کن و صریح بگو «اطلاعات کافی نیست».",
            "",
            "خروجی باید دقیقاً JSON و فقط JSON باشد با این شکل:",
            '{ "winner_root": "<root>", "argument_fa": "<متن>", "generated_text_fa": "<متن>" }',
            "",
            f"سؤال کاربر:\n{query}",
            "",
            "evidence:",
            evidence,
        ]
    )

    return [
        {
            "role": "user",
            "content": content,
        },
    ]
