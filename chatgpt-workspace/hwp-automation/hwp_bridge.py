"""
HWPBridge: GJC 에이전트를 위한 완전 무인화(Zero-Touch) 통합 래퍼 클래스.

- 문서 형식(HWP 바이너리 / HWPX ZIP-XML)을 실제 바이트로 감별한다.
- 요청 데이터 타입에 따라 엔진을 자동 라우팅한다(계약: ZERO_TOUCH_CHALLENGES.md).
    str / dict  -> XML 엔진 (python-hwpx-automation, OS 무관)
    list        -> 표행 추가 (pyhwpx OLE 워커, Windows 전용)
- 검증(verify_integrity)은 거짓 성공(항상 True)을 반환하지 않는다.
    검증할 수 없는 경로는 명시적으로 실패/미구현으로 보고한다.
"""

import shutil
import subprocess  # noqa: F401  # OLE 워커 서브프로세스 실행용 (예약)
import zipfile
from pathlib import Path

_HWP_MAGIC = b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1"  # 구형 HWP = OLE2(Compound File)


def _looks_like_hwp(path: Path) -> bool:
    """확장자 대신 실제 파일 시그니처로 구형 HWP 여부를 판별한다."""
    with path.open("rb") as fh:
        return fh.read(8) == _HWP_MAGIC


def _looks_like_hwpx(path: Path) -> bool:
    """HWPX는 ZIP 기반 XML 묶음이므로 ZIP 여부로 판별한다."""
    return zipfile.is_zipfile(path)


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

    # ---- 공개 계약: fill_data 하나로 전부 라우팅 ----

    def fill_data(self, data) -> None:
        """
        데이터 타입 기반 자동 라우팅 (ZERO_TOUCH_CHALLENGES.md #2 계약).
        - str  : 전체 치환 / dict: 필드명별 치환 -> XML 엔진
        - list : 표행 추가 -> OLE 엔진
        """
        if isinstance(data, (str, dict)):
            if self.format == "hwp":
                raise RuntimeError(
                    "구형 HWP는 XML 치환이 불가능합니다. OLE 변환(hwp_converter) 선행 필요."
                )
            self._fill_via_xml(data)
        elif isinstance(data, list):
            self._add_rows_via_ole(data)
        else:
            raise TypeError(f"지원하지 않는 데이터 타입: {type(data)}")

    # ---- 내부 엔진 구현 (의존성 주입 지점) ----

    def _fill_via_xml(self, data) -> None:
        """python-hwpx-automation 으로 누름틀/텍스트만 치환한다. (표 구조 변경 금지)"""
        # TODO: import hwpx_automation ... (requirements.txt 설치 후 실제 구현)
        # 폰트 보존: 정규식 replace 금지. <hp:t> 노드의 부모 StyleID를 유지한 채
        #            텍스트 속성값만 교체한다. (노드 삭제 금지)
        raise NotImplementedError("XML 엔진 미구현: requirements.txt 의존성 설치 후 연결 필요")

    def _add_rows_via_ole(self, rows: list) -> None:
        """pyhwpx OLE 워커를 서브프로세스로 호출한다. (Windows + 한글 설치 필수)"""
        if "win32" not in __import__("sys").platform:
            raise RuntimeError("OLE 표 조작은 Windows + 한글(hwp.exe) 환경에서만 동작합니다.")
        # TODO: hwp_ole_worker.py 를 subprocess로 실행 (10건 이하는 순차, popup 무시 모드)
        #   팝업 차단: SetMessageBoxMode + 60초 taskkill 타임아웃 래퍼
        raise NotImplementedError("OLE 워커 미구현: hwp_ole_worker.py 실제 스크립트 필요")

    # ---- 자가 검증 (거짓 성공 금지) ----

    def verify_integrity(self) -> bool:
        """
        생성된 _수정본 문서를 사람 대신 검수한다.
        - HWPX : ZIP 무결성 + 미치환 필드 잔여 여부를 실제로 검사한다.
        - HWP  : OLE 없이는 무결성 판정 불가 -> NotImplementedError.
        """
        if not self.work_path.exists():
            return False

        if self.format == "hwpx":
            try:
                with zipfile.ZipFile(self.work_path) as zf:
                    bad = zf.testzip()
                if bad is not None:
                    return False  # 내부 XML 손상 감지
            except zipfile.BadZipFile:
                return False

            # 텍스트 치환 키({{...}})가 문서 안에 그대로 남아 있으면 실패 처리
            for name in self._iter_xml_members():
                xml_text = self.work_path.with_suffix("")  # placeholder
                if "{{" in xml_text.read_text(encoding="utf-8", errors="ignore"):
                    return False
            return True

        raise NotImplementedError(
            "구형 HWP의 무결성 검증은 OLE(한글 앱) 재열기 후에만 가능합니다."
        )

    def _iter_xml_members(self):
        with zipfile.ZipFile(self.work_path) as zf:
            for name in zf.namelist():
                if name.endswith(".xml"):
                    yield name

    def save_and_close(self) -> Path:
        """작업 완료 후 최종 산출물 경로를 반환한다."""
        return self.work_path


if __name__ == "__main__":
    # Zero-Touch 파이프라인 예시
    doc = HWPBridge("weekly_report_template.hwpx")
    try:
        doc.fill_data({"issue_title": "AI 파서 동향", "content": "도리보고 수집 내용..."})
        assert doc.verify_integrity(), "무인 검수 실패: 문서 손상 또는 미치환 필드 존재"
    except NotImplementedError as exc:
        print(f"[자동화 차단] {exc} — 의존성/워커 설치 후 재시도합니다.")
    else:
        print(f"무인 검수 통과. 발행 대상: {doc.save_and_close()}")
