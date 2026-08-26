#!/usr/bin/env python3
"""
HWPBridge: 실제 동작하는 HWPX 반자동화(Semi-Automation) 래퍼.

- 내용 주입 = hwpx.paragraph_patch (바이트 보존 텍스트 치환 → 표/틀 구조 불변)
- 읽기     = hwpx.TextExtractor (파일을 그대로 읽음, 복사본 안 만듦)
- 검증     = hwpx.validate_editor_open_safety (재열기 가능) + 미치환 {{...}} 잔여 검사
- 구조 변경 = 승인 게이트(PlannedChange). OLE는 Windows 전용 → WSL2/Linux에선 명시적 실패.

사용법(CLI):
  python3 hwp_bridge.py --read  <문서.hwpx>
  python3 hwp_bridge.py --fill  <문서.hwpx> '{"user_name":"홍길동","date":"2026-08-26"}'
  python3 hwp_bridge.py --verify <문서.hwpx>
"""

from __future__ import annotations

import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path

from hwpx import (
    ParagraphTextPatch,
    TextExtractor,
    paragraph_patch,
    validate_editor_open_safety,
)

_HWP_MAGIC = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"  # 구형 HWP = OLE2(Compound File)


def _looks_like_hwp(path: Path) -> bool:
    with path.open("rb") as fh:
        return fh.read(8) == _HWP_MAGIC


def _looks_like_hwpx(path: Path) -> bool:
    return zipfile.is_zipfile(path)


@dataclass
class PlannedChange:
    """실행 전 사용자 승인을 기다리는 구조 변경 계획 (Approval Gate)."""

    ops: list[dict]
    target: str
    reason: str
    approved: bool = False

    def approve(self) -> None:
        self.approved = True

    def reject(self) -> None:
        self.approved = False

    def summary(self) -> str:
        ops_text = "\n".join(f"  - {op}" for op in self.ops)
        return (
            f"[구조 변경 요청]\n대상: {self.target}\n작업:\n{ops_text}\n"
            f"근거: {self.reason}\n진행할까요? (승인/거부)"
        )


class HWPBridge:
    def __init__(self, filepath: str):
        self.original_path = Path(filepath)
        self._detect_format()
        # 작업 산출물은 항상 원본과 별개 파일로만 생성된다. (원본 불변)
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

    # ---------------- 읽기 (파일 그대로, 복사본 없음) ----------------

    def _extract(self, source: Path) -> list[dict]:
        ext = TextExtractor(source)
        return [
            {
                "section": p.section.name,
                "index": p.index,
                "nested": p.is_nested,
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
        원본 템플릿의 {{key}} 플레이스홀더를 값으로 치환해 _수정본으로 저장한다.
        - 표/누름틀 구조(행·열·병합·위치)는 절대 바뀌지 않는다.
        - 매 실행마다 원본 템플릿을 기준으로 다시 채우므로 반복 실행(재채우기) 가능.
        반환: {"applied", "skipped", "unmatched", "output", "verified"}
        """
        if self.format == "hwp":
            raise RuntimeError(
                "구형 HWP는 XML 치환이 불가능합니다. OLE 변환 후 진행하세요."
            )
        if not mapping:
            return {
                "applied": 0,
                "skipped": 0,
                "unmatched": list(mapping),
                "output": str(self.work_path),
                "verified": False,
            }

        patches: list[ParagraphTextPatch] = []
        matched_keys: set[str] = set()

        for p in self._extract(self.original_path):
            text = p["text"]
            if "{{" not in text:
                continue
            new_text = text
            for key, value in mapping.items():
                token = "{{" + key + "}}"
                if token in new_text:
                    new_text = new_text.replace(token, str(value))
                    matched_keys.add(key)
            if new_text != text:
                patches.append(
                    ParagraphTextPatch(p["section"], p["index"], new_text)
                )

        result = (
            paragraph_patch(self.original_path, patches) if patches else None
        )
        if result is not None:
            self.work_path.write_bytes(result.data)

        return {
            "applied": len(getattr(result, "applied", ())),
            "skipped": len(getattr(result, "skipped", ())),
            "unmatched": [k for k in mapping if k not in matched_keys],
            "output": str(self.work_path),
            "verified": self._verify(self.work_path),
        }

    def fill_cells(self, cell_map: dict[str, str]) -> dict:
        """fill_fields와 동일: 표 셀 문단도 값만 치환한다."""
        return self.fill_fields(cell_map)

    # ---------------- 구조 변경 (승인 게이트) ----------------

    def plan_structural_change(
        self, ops: list[dict], target: str, reason: str
    ) -> PlannedChange:
        """계획만 생성. approve() 전까지 문서는 변경되지 않는다."""
        self.pending = PlannedChange(ops=ops, target=target, reason=reason)
        return self.pending

    def _execute_structural_change(self, plan: PlannedChange) -> None:
        if "win32" not in sys.platform:
            raise RuntimeError(
                "구조 변경(OLE)은 Windows + 한글(hwp.exe) 환경에서만 동작합니다. "
                "현재 환경(WSL2/Linux)에서는 구조 변경을 실행할 수 없습니다."
            )
        # TODO: Windows에서 pyhwpx OLE 워커 실행 (팝업 차단 + 타임아웃 래퍼)
        raise NotImplementedError("OLE 구조 변경 워커 미구현")

    # ---------------- 검증 ----------------

    def _verify(self, path: Path) -> bool:
        if not path.exists():
            return False
        if self.format == "hwp":
            raise NotImplementedError(
                "구형 HWP의 무결성 검증은 OLE(한글 앱) 재열기 후에만 가능합니다."
            )
        safety = validate_editor_open_safety(path)
        if not safety.reopen_ok:
            return False
        for p in self._extract(path):
            if "{{" in p["text"]:
                return False
        return True

    def verify_integrity(self) -> bool:
        """입력 파일(원본)을 그대로 검증한다."""
        return self._verify(self.original_path)

    def save_and_close(self) -> Path:
        return self.work_path


# ---------------- CLI ----------------

def _main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(
            "Usage:\n"
            "  python3 hwp_bridge.py --read  <문서.hwpx>\n"
            "  python3 hwp_bridge.py --fill  <문서.hwpx> '<json>'\n"
            "  python3 hwp_bridge.py --verify <문서.hwpx>"
        )
        return 2

    cmd, path = argv[1], argv[2]
    try:
        doc = HWPBridge(path)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 1

    if cmd == "--read":
        print(json.dumps(doc.read_paragraphs(), ensure_ascii=False, indent=2))
        return 0

    if cmd == "--fill":
        mapping = json.loads(argv[3]) if len(argv) > 3 else {}
        try:
            result = doc.fill_fields(mapping)
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["verified"] else 3

    if cmd == "--verify":
        try:
            ok = doc.verify_integrity()
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
            return 1
        print(json.dumps({"verified": ok}, ensure_ascii=False))
        return 0 if ok else 3

    print(json.dumps({"error": f"알 수 없는 명령: {cmd}"}, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
