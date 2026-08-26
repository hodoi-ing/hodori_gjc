"""
HWPBridge: HWP/HWPX 반자동화(Semi-Automation, HITL) 통합 래퍼 클래스.

운영 원칙 (SEMI_AUTOMATION.md):
1) 내용 주입(Auto)  - 표/누름틀 구조는 그대로 두고 '값'만 채운다. 기하 구조 불변.
2) 구조 변경(게이트)- 표 병합/행 추가/셀 병합 등은 plan_structural_change()로
                      계획만 만들고, approve() 승인 전까지 문서를 변경하지 않는다.
3) 검증            - 작업 후 verify_integrity()로 손상/미치환 필드를 스스로 확인.

기술 장애물 대응: ZERO_TOUCH_CHALLENGES.md 참조.
"""

import shutil
import subprocess  # noqa: F401  # OLE 워커 서브프로세스 실행용 (예약)
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

_HWP_MAGIC = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"  # 구형 HWP = OLE2(Compound File)


def _looks_like_hwp(path: Path) -> bool:
    """확장자 대신 실제 파일 시그니처로 구형 HWP 여부를 판별한다."""
    with path.open("rb") as fh:
        return fh.read(8) == _HWP_MAGIC


def _looks_like_hwpx(path: Path) -> bool:
    """HWPX는 ZIP 기반 XML 묶음이므로 ZIP 여부로 판별한다."""
    return zipfile.is_zipfile(path)


@dataclass
class PlannedChange:
    """실행 전 사용자 승인을 기다리는 구조 변경 계획 (Approval Gate)."""

    ops: list[dict]
    target: str
    reason: str
    approved: bool = False

    def approve(self) -> None:
        """사용자 승인 → 실행 허가."""
        self.approved = True

    def reject(self) -> None:
        """사용자 거부 → 계획 폐기. 문서는 변경되지 않는다."""
        self.approved = False

    def summary(self) -> str:
        ops_text = "\n".join(f"  - {op}" for op in self.ops)
        return (
            f"[구조 변경 요청]\n"
            f"대상: {self.target}\n"
            f"작업:\n{ops_text}\n"
            f"근거: {self.reason}\n"
            f"진행할까요? (승인/거부)"
        )


class HWPBridge:
    def __init__(self, filepath: str, ole_timeout_sec: int = 60):
        self.original_path = Path(filepath)
        self.ole_timeout_sec = ole_timeout_sec
        self._detect_format()

        # 원본 훼손 방지: 복사본(_수정본)에서만 작업한다.
        self.work_path = self.original_path.with_name(
            f"{self.original_path.stem}_수정본{self.original_path.suffix}"
        )
        if not self.work_path.exists():
            shutil.copy2(self.original_path, self.work_path)

        self.pending: PlannedChange | None = None

    def _detect_format(self) -> None:
        if _looks_like_hwp(self.original_path):
            self.format = "hwp"      # OLE 전용. XML 엔진 금지.
        elif _looks_like_hwpx(self.original_path):
            self.format = "hwpx"     # XML 엔진 허용.
        else:
            raise ValueError(
                f"알 수 없는 문서 형식: {self.original_path.name} "
                "(HWP 바이너리 또는 HWPX ZIP이 아닙니다)"
            )

    # ================= 내용 주입 (기하 구조 불변) =================

    def fill_cells(self, cell_map: dict[str, str]) -> None:
        """
        타깃 문서의 표 셀/누름틀에 '값'만 채운다.
        - cell_map 예: {"sales_table.r2c1": "1,200,000", "user_name": "홍길동"}
        - 표의 행/열/병합/누름틀 위치는 절대 변경하지 않는다. (SEMI_AUTOMATION 규칙 1)
        """
        if not cell_map:
            return
        if self.format == "hwp":
            raise RuntimeError(
                "구형 HWP는 XML 치환이 불가능합니다. OLE 변환(hwp_converter) 선행 필요."
            )
        # TODO: python-hwpx-automation / hwpx-kit 으로 필드/셀 텍스트만 치환
        #   (정규식 replace 금지, <hp:t> StyleID 상속 유지)
        raise NotImplementedError(
            "XML 엔진 미구현: requirements.txt 의존성 설치 후 연결 필요"
        )

    # ================= 구조 변경 (승인 게이트 필수) =================

    def plan_structural_change(self, ops: list[dict], target: str, reason: str) -> PlannedChange:
        """
        구조 변경(표 병합·행/열 추가·셀 병합 등)은 실행하지 않고 '계획'만 만든다.
        사용자가 approve() 하기 전까지 문서는 변경되지 않는다. (SEMI_AUTOMATION 규칙 2)
        """
        self.pending = PlannedChange(ops=ops, target=target, reason=reason)
        return self.pending

    def _execute_structural_change(self, plan: PlannedChange) -> None:
        """승인된 계획만 실행한다. (OLE 엔진 사용, Windows 전용)"""
        if "win32" not in sys.platform:
            raise RuntimeError(
                "구조 변경(OLE)은 Windows + 한글(hwp.exe) 환경에서만 동작합니다."
            )
        # TODO: pyhwpx OLE 워커 실행 (표 병합/행 추가 ...)
        #   팝업 차단 + func-timeout(60s) + taskkill 방어 래퍼 적용
        raise NotImplementedError("OLE 구조 변경 워커 미구현: hwp_ole_worker.py 필요")

    # ================= 자가 검증 (거짓 성공 금지) =================

    def verify_integrity(self) -> bool:
        """
        생성된 _수정본 문서를 사람 대신 검수한다.
        - HWPX : ZIP 무결성 + 미치환 필드({{...}}) 잔여 여부를 실제로 검사.
        - HWP  : OLE 없이는 무결성 판정 불가 -> NotImplementedError.
        """
        if not self.work_path.exists():
            return False

        if self.format == "hwpx":
            try:
                with zipfile.ZipFile(self.work_path) as zf:
                    if zf.testzip() is not None:
                        return False  # 내부 XML 손상 감지
            except zipfile.BadZipFile:
                return False

            for name in self._iter_xml_members():
                with zipfile.ZipFile(self.work_path) as zf:
                    xml_text = zf.read(name).decode("utf-8", errors="ignore")
                if "{{" in xml_text:
                    return False  # 미치환 필드 잔여
            return True

        raise NotImplementedError(
            "구형 HWP의 무결성 검증은 OLE(한글 앱) 재열기 후에만 가능합니다."
        )

    def _iter_xml_members(self) -> list[str]:
        with zipfile.ZipFile(self.work_path) as zf:
            return [n for n in zf.namelist() if n.endswith(".xml")]

    def save_and_close(self) -> Path:
        """작업 완료 후 최종 산출물 경로를 반환한다."""
        return self.work_path


if __name__ == "__main__":
    # 반자동화 파이프라인 예시 (승인 게이트 포함)
    doc = HWPBridge("weekly_report_template.hwpx")
    try:
        # 1) 자동: 내용만 주입
        doc.fill_cells({"sales_table.r2c1": "1,200,000", "user_name": "홍길동"})

        # 2) 구조 변경 필요 시 → 계획만 세우고 승인 대기
        plan = doc.plan_structural_change(
            ops=["매출표 2개 병합", "상단 헤더 셀 병합 1건"],
            target="weekly_report_template.hwpx 의 sales_table",
            reason="소스 데이터가 2개 표로 분리되어 있어 1개로 합쳐야 정리 가능",
        )
        print(plan.summary())
        print(">>> 승인 대기 중: approve() 전까지 문서는 변경되지 않습니다.")

        # 사용자 승인 후에만 실행
        plan.approve()
        doc._execute_structural_change(plan)

        # 3) 검증 후 반환
        assert doc.verify_integrity(), "무인 검수 실패: 문서 손상 또는 미치환 필드 존재"
        print(f"완료: {doc.save_and_close()}")
    except NotImplementedError as exc:
        print(f"[차단] {exc} — 의존성/워커 설치 후 재시도합니다.")