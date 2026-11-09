#!/usr/bin/env python3
"""Read-only wording check for the four prose fields in a question table."""

import argparse
import html
import re
import sys
from pathlib import Path


FIELDS = ("题目-文字", "考点rubric", "作答思路", "标准答案-文本")
TERMS = (
    "不得", "不能", "不是", "不代表", "不等于", "不意味着", "不构成",
    "不应", "禁止", "不要", "切勿", "严禁", "并非", "而非",
    "不要求", "不支持", "不作为", "不保证", "不承诺", "仅供参考",
)
PATTERN = re.compile("|".join(map(re.escape, TERMS)))
BREAK = re.compile(r"<br\s*/?>", re.IGNORECASE)


def read_fields(path):
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = line.strip().split("|")
        if len(cells) < 3 or cells[1].strip() not in FIELDS:
            continue
        name = cells[1].strip()
        if len(cells) != 4 or cells[0].strip() or cells[-1].strip():
            raise ValueError(f"{name}：需要两列表格行，单元格内竖线请转义。")
        if name in fields:
            raise ValueError(f"字段重复：{name}")
        fields[name] = cells[2].strip()
    missing = [name for name in FIELDS if not fields.get(name)]
    if missing:
        raise ValueError("缺少或留空字段：" + "、".join(missing))
    return fields


def template_rule():
    path = Path(__file__).resolve().parents[1] / "assets" / "题目模板.md"
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = line.split("|")
        if len(cells) == 4 and cells[1].strip() == "考点rubric":
            return BREAK.split(cells[2].strip(), maxsplit=1)[0]
    raise ValueError("题目模板缺少评分规则，检查技能文件。")


def find_hits(fields, rule):
    hits = []
    for name in FIELDS:
        paragraphs = BREAK.split(fields[name])
        for index, paragraph in enumerate(paragraphs, 1):
            if name == "考点rubric" and index == 1 and paragraph == rule:
                continue
            visible = html.unescape(re.sub(r"<[^>]+>", "", paragraph))
            for match in PATTERN.finditer(visible):
                start = max(0, match.start() - 35)
                end = min(len(visible), match.end() + 55)
                context = visible[start:end]
                hits.append((name, index, match.group(), context))
    return hits


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", type=Path, help="本轮题目.md的实际路径")
    args = parser.parse_args()
    try:
        fields = read_fields(args.question)
        hits = find_hits(fields, template_rule())
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"检查入口错误：{exc}", file=sys.stderr)
        return 2
    for field, paragraph, term, context in hits:
        print(f"{field} / 第{paragraph}段 / {term}：{context}")
    if hits:
        print(f"共{len(hits)}处待改写。修改原文件后重新检查。")
        return 1
    print("四个文字字段扫描零命中。接续完成逐段审读和改后实质条件核对。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
