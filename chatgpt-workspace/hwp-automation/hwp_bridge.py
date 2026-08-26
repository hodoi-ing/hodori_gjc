#!/usr/bin/env python3
"""
HWPBridge: 실제 동작하는 HWPX 반자동화(Semi-Automation) 래퍼 (전 기능 XML 기반, WSL2/Linux OK).

- 내용 주입  = 표 셀은 hwpx.table_patch.fill_cells, 일반 문단은 hwpx.paragraph_patch (둘 다 바이트 보존 → 구조 불변)
- 읽기       = hwpx.TextExtractor
- 검증       = hwpx.validate_editor_open_safety + 미치환 {{...}} 잔여 검사
- 구조 변경  = hwpx.table_patch.apply_table_ops (행 추가/삭제, 표 병합/분리, 셀 채우기) — 승인 게이트 필수

사용법(CLI):
  python3 hwp_bridge.py --read   <문서.hwpx>
  python3 hwp_bridge.py --fill   <문서.hwpx> '{"user_name":"홍길동"}'
  python3 hwp_bridge.py --verify <문서.hwpx>
  python3 hwp_bridge.py --tables <문서.hwpx>
  python3 hwp_bridge.py --plan   <문서.hwpx> '[{"op":"merge_table","table_index":0}]'
  python3 hwp_bridge.py --apply  <문서.hwpx> '[{"op":"insert_row_by_clone","table_index":0,"ref_row":1,"count":1}]'
"""

from __future__ import annotations

import json
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from hwpx import (
    ParagraphTextPatch,
    TextExtractor,
    paragraph_patch,
    validate_editor_open_safety,
)
from hwpx.table_patch import apply_table_ops, fill_cells, table_summary

_HWP_MAGIC = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"  # 구형 HWP = OLE2(Compound File)


def _looks_like_hwp(path: Path) -> bool:
    with path.open("rb") as fh:
        return fh.read(8) == _HWP_MAGIC


def _looks_like_hwpx(path: Path) -> bool:
    return zipfile.is_zipfile(path)


def _idx(hierarchy: tuple[str, ...], prefix: str) -> int | None:
    """hierarchy에서 'tr[1]' 같은 요소의 숫자 인덱스를 뽑는다."""
    for h in hierarchy:
        if h.startswith(prefix) and h.endswith("]") and "[" in h:
            return int(h[h.index("[") + 1 : h.index("]")])
    return None


@dataclass
class PlannedChange:
    """실행 전 사용자 승인을 기다리는 구조 변경 계획 (Approval Gate)."""

    ops: list[dict]
    target: str
    reason: str
    transcript: tuple = ()
    approved: bool = False

    def approve(self) -> None:
        self.approved = True

    def reject(self) -> None:
        self.approved = False

    def summary(self) -> str:
        ops_text = "\n".join(f"  - {op}" for op in self.ops)
        tr_text = "\n".join(
            f"  · {t}" for t in self.transcript
        ) if self.transcript else "  (dry-run transcript 없음)"
        return (
            f"[구조 변경 요청]\n대상: {self.target}\n작업:\n{ops_text}\n"
            f"검증 근거(dry-run):\n{tr_text}\n"
            f"근거: {self.reason}\n진행할까요? (승인/거부)"
        )


class HWPBridge:
    def __init__(self, filepath: str):
        self.original_path = Path(filepath)
        self._detect_format()
        self.work_path = self.original_path.with_name(
            f"{self.original_path.stem}_수정본{self.original_path.suffix}"
        )
        self.pending: PlannedChange | None = None

    def _detect_format(self) -> None:
        if _looks_like_hwp(self.original_path):
            self.format = "hwp"
        elif _looks_like_hwpx(self.original_path):
            self.format = "hwpx"
        else:
            raise ValueError(
                f"알 수 없는 문서 형식: {self.original_path.name} "
                "(HWP 바이너리 또는 HWPX ZIP이 아닙니다)"
            )

    # ---------------- 읽기 ----------------

    def _extract(self, source: Path) -> list[dict]:
        ext = TextExtractor(source)
        return [
            {
                "section": p.section.name,
                "index": p.index,
                "nested": p.is_nested,
                "hierarchy": p.hierarchy,
                "text": p.text(),
            }
            for p in ext.iter_document_paragraphs()
        ]

    def read_paragraphs(self) -> list[dict]:
        return self._extract(self.original_path)

    def read_text(self) -> str:
        return "\n".join(
            p["text"] for p in self.read_paragraphs() if p["text"].strip()
        )

    # ---------------- 내용 주입 (기하 구조 불변) ----------------

    def fill_fields(self, mapping: dict[str, str]) -> dict:
        """
        원본 템플릿의 {{key}} 플레이스홀더를 값으로 치환해 _수정본으로 저장.
        - 표 셀: fill_cells(셀 주소) → 구조/서식 불변
        - 일반 문단: paragraph_patch → 구조/서식 불변
        매 실행마다 원본 템플릿 기준이므로 재채우기(반복) 가능.
        """
        if self.format == "hwp":
            raise RuntimeError(
                "구형 HWP는 XML 치환이 불가능합니다. OLE 변환 후 진행하세요."
            )
        if not mapping:
            return {
                "applied": 0, "skipped": 0, "unmatched": list(mapping),
                "output": str(self.work_path), "verified": False,
            }

        matched: set[str] = set()
        cell_specs: list[dict] = []
        para_patches: list[ParagraphTextPatch] = []
        wrapper_to_ti: dict[str, int] = {}
        next_ti = 0

        def _apply(text: str) -> str:
            new = text
            for k, v in mapping.items():
                token = "{{" + k + "}}"
                if token in new:
                    new = new.replace(token, str(v))
                    matched.add(k)
            return new

        for p in self._extract(self.original_path):
            text = p["text"]
            if "{{" not in text:
                continue
            new_text = _apply(text)
            if new_text == text:
                continue

            if p["nested"]:
                # 표 셀: (table_index, row, col) 로 매핑
                hier = p["hierarchy"]
                wrapper = next((h for h in hier if h.startswith("p[")), None)
                row = _idx(hier, "tr[")
                col = _idx(hier, "tc[")
                if wrapper is None or row is None or col is None:
                    continue
                if wrapper not in wrapper_to_ti:
                    wrapper_to_ti[wrapper] = next_ti
                    next_ti += 1
                cell_specs.append({
                    "table_index": wrapper_to_ti[wrapper],
                    "row": row, "col": col, "text": new_text,
                })
            else:
                para_patches.append(
                    ParagraphTextPatch(p["section"], p["index"], new_text)
                )

        # 1) 일반 문단 먼저
        intermediate = self.original_path.read_bytes()
        applied = 0
        if para_patches:
            r = paragraph_patch(self.original_path, para_patches)
            intermediate = r.data
            applied += len(r.applied)

        # 2) 표 셀
        skipped = 0
        if cell_specs:
            fr = fill_cells(intermediate, cell_specs)
            intermediate = fr.data
            applied += len(fr.applied)
            skipped += len(fr.skipped)

        self.work_path.write_bytes(intermediate)
        return {
            "applied": applied,
            "skipped": skipped,
            "unmatched": [k for k in mapping if k not in matched],
            "output": str(self.work_path),
            "verified": self._verify(self.work_path),
        }

    def fill_cells_direct(self, cells: list[dict]) -> dict:
        """(table_index,row,col,text) 명시 목록으로 표 셀만 정밀하게 채운다."""
        if self.format == "hwp":
            raise RuntimeError("구형 HWP는 XML 치환이 불가능합니다.")
        fr = fill_cells(self.original_path, cells)
        self.work_path.write_bytes(fr.data)
        return {
            "applied": len(fr.applied),
            "skipped": len(fr.skipped),
            "output": str(self.work_path),
            "verified": self._verify(self.work_path),
        }

    # ---------------- 표 구조 변경 (승인 게이트) ----------------

    def list_tables(self) -> list[dict]:
        return table_summary(self.original_path)

    def plan_structural_change(
        self, ops: list[dict], target: str, reason: str
    ) -> PlannedChange:
        """계획만 세우고 dry_run transcript를 확보한다. 실행은 하지 않는다."""
        if self.format == "hwp":
            raise RuntimeError("구형 HWP 바이너리는 구조 변경 불가. .hwpx 변환 필요.")
        dry = apply_table_ops(self.original_path, ops, dry_run=True)
        self.pending = PlannedChange(
            ops=ops, target=target, reason=reason,
            transcript=dry.transcript, approved=False,
        )
        return self.pending

    def _execute_structural_change(self, plan: PlannedChange) -> dict:
        """승인된 구조 변경 계획을 XML 레벨에서 실행한다. (WSL2/Linux에서 동작)"""
        if self.format == "hwp":
            raise RuntimeError("구형 HWP 바이너리는 구조 변경 불가. .hwpx 변환 필요.")
        if not plan.approved:
            raise RuntimeError("승인되지 않은 구조 변경은 실행할 수 없습니다.")
        result = apply_table_ops(
            self.original_path, plan.ops, output_path=self.work_path
        )
        if not result.ok:
            raise RuntimeError(f"구조 변경 실패: {[s.to_dict() for s in result.skipped]}")
        return {
            "ok": True,
            "transcript": list(result.transcript),
            "output": str(self.work_path),
            "verified": self._verify(self.work_path, check_placeholders=False),
        }

    # ---------------- 검증 ----------------

    def _verify(self, path: Path, check_placeholders: bool = True) -> bool:
        if not path.exists():
            return False
        if self.format == "hwp":
            raise NotImplementedError(
                "구형 HWP의 무결성 검증은 OLE(한글 앱) 재열기 후에만 가능합니다."
            )
        safety = validate_editor_open_safety(path)
        if not safety.reopen_ok:
            return False
        if check_placeholders:
            for p in self._extract(path):
                if "{{" in p["text"]:
                    return False
        return True

    def verify_integrity(self) -> bool:
        return self._verify(self.original_path)

    def save_and_close(self) -> Path:
        return self.work_path


# ---------------- CLI ----------------

def _main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "Usage:\n"
            "  hwp_bridge.py --read   <file>\n"
            "  hwp_bridge.py --fill   <file> '<json>'\n"
            "  hwp_bridge.py --verify <file>\n"
            "  hwp_bridge.py --tables <file>\n"
            "  hwp_bridge.py --plan   <file> '<ops>'\n"
            "  hwp_bridge.py --apply  <file> '<ops>'"
        )
        return 2

    cmd, path = argv[1], argv[2]
    try:
        doc = HWPBridge(path)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    try:
        if cmd == "--read":
            print(json.dumps(doc.read_paragraphs(), ensure_ascii=False, indent=2))
        elif cmd == "--fill":
            mapping = json.loads(argv[3]) if len(argv) > 3 else {}
            print(json.dumps(doc.fill_fields(mapping), ensure_ascii=False, indent=2))
        elif cmd == "--verify":
            print(json.dumps({"verified": doc.verify_integrity()}, ensure_ascii=False))
        elif cmd == "--tables":
            print(json.dumps(doc.list_tables(), ensure_ascii=False, indent=2))
        elif cmd == "--plan":
            ops = json.loads(argv[3]) if len(argv) > 3 else []
            plan = doc.plan_structural_change(ops, path, "구조 변경 계획")
            print(json.dumps({
                "dry_run": True,
                "transcript": list(plan.transcript),
                "summary": plan.summary(),
            }, ensure_ascii=False, indent=2))
        elif cmd == "--apply":
            ops = json.loads(argv[3]) if len(argv) > 3 else []
            plan = doc.plan_structural_change(ops, path, "구조 변경 실행")
            plan.approve()
            print(json.dumps(doc._execute_structural_change(plan), ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": f"알 수 없는 명령: {cmd}"}, ensure_ascii=False))
            return 2
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
