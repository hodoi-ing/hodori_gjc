#!/usr/bin/env python3
"""
HWP Batch Processor: CSV/Excel 명단 데이터를 기반으로 HWP/HWPX 양식 문서를 일괄 생성하는 모듈.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from hwp_bridge import HWPBridge


def load_data(data_path: Path) -> list[dict[str, Any]]:
    """CSV 또는 Excel (.xlsx) 파일에서 레코드 목록을 읽어옵니다."""
    suffix = data_path.suffix.lower()
    records: list[dict[str, Any]] = []

    if suffix == ".csv" or suffix == ".tsv":
        delimiter = "\t" if suffix == ".tsv" else ","
        with data_path.open("r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            for row in reader:
                records.append({k.strip(): (v.strip() if v else "") for k, v in row.items() if k})

    elif suffix == ".xlsx":
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError("Excel(.xlsx) 파일을 읽으려면 openpyxl 라이브러리가 필요합니다.")

        wb = openpyxl.load_workbook(data_path, data_only=True)
        ws = wb.active
        headers = []
        for cell in ws[1]:
            headers.append(str(cell.value).strip() if cell.value is not None else "")

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not any(row):
                continue
            rec = {}
            for h, val in zip(headers, row):
                if h:
                    rec[h] = str(val).strip() if val is not None else ""
            records.append(rec)
    else:
        raise ValueError(f"지원하지 않는 데이터 파일 형식입니다: {suffix} (.csv, .tsv, .xlsx 지원)")

    return records


def run_batch(
    template_path: str,
    data_path: str,
    output_dir: str | None = None,
    name_pattern: str | None = None,
) -> dict:
    """
    템플릿 파일과 명단 데이터를 받아 일괄 생성을 수행합니다.
    
    :param template_path: 템플릿 HWP/HWPX 경로
    :param data_path: CSV/XLSX 데이터 파일 경로
    :param output_dir: 결과물 저장 디렉터리 (None이면 template 부모 디렉터리 하위 'batch_output')
    :param name_pattern: 생성 파일명 패턴 (예: "수료증_{성명}", 미지정 시 "문서_{index}")
    """
    tmpl_p = Path(template_path)
    data_p = Path(data_path)

    if not tmpl_p.exists():
        raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {tmpl_p}")
    if not data_p.exists():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {data_p}")

    out_p = Path(output_dir) if output_dir else tmpl_p.parent / "batch_output"
    out_p.mkdir(parents=True, exist_ok=True)

    records = load_data(data_p)
    if not records:
        return {"total": 0, "generated": 0, "failed": 0, "outputs": [], "errors": ["데이터 레코드가 비어있습니다."]}

    results = []
    errors = []
    generated_count = 0

    for idx, rec in enumerate(records, start=1):
        # 파일명 결정
        if name_pattern:
            try:
                fn_stem = name_pattern.format(index=idx, **rec)
            except KeyError as e:
                fn_stem = f"문서_{idx}_{rec.get('name', rec.get('성명', idx))}"
        else:
            fn_stem = f"{tmpl_p.stem}_{idx}"
            if "성명" in rec:
                fn_stem += f"_{rec['성명']}"
            elif "name" in rec:
                fn_stem += f"_{rec['name']}"

        # 특수문자 정리
        clean_stem = "".join(c for c in fn_stem if c.isalnum() or c in ("_", "-", " "))
        target_hwpx = out_p / f"{clean_stem}.hwpx"

        try:
            bridge = HWPBridge(str(tmpl_p))
            # HWPBridge의 work_path를 target_hwpx로 지정
            bridge.work_path = target_hwpx
            
            res = bridge.fill_fields(rec)
            generated_count += 1
            results.append({
                "index": idx,
                "file": str(target_hwpx),
                "applied_keys": res.get("applied", 0),
                "unmatched_keys": res.get("unmatched", []),
            })
        except Exception as err:
            errors.append(f"[{idx}번 레코드] 생성 실패: {err}")

    return {
        "total": len(records),
        "generated": generated_count,
        "failed": len(errors),
        "outputs": results,
        "errors": errors,
        "output_dir": str(out_p),
    }


def main():
    parser = argparse.ArgumentParser(description="HWP/HWPX 양식 문서를 CSV/Excel 데이터로 일괄 생성합니다.")
    parser.add_argument("--template", "-t", required=True, help="템플릿 HWP/HWPX 파일 경로")
    parser.add_argument("--data", "-d", required=True, help="CSV 또는 Excel (.xlsx) 데이터 파일 경로")
    parser.add_argument("--output-dir", "-o", help="생성 문서 저장 디렉터리")
    parser.add_argument("--name-pattern", "-n", help="생성 파일명 패턴 (예: '수료증_{성명}' 또는 '보고서_{index}')")

    args = parser.parse_args()

    print(f"🔄 일괄 생성 시작: 템플릿[{args.template}] + 데이터[{args.data}]...")
    res = run_batch(
        template_path=args.template,
        data_path=args.data,
        output_dir=args.output_dir,
        name_pattern=args.name_pattern,
    )

    print(f"\n✅ 일괄 생성 완료!")
    print(f"📊 총 레코드: {res['total']}개 | 성공: {res['generated']}개 | 실패: {res['failed']}개")
    print(f"📂 저장 위치: {res['output_dir']}")

    if res["errors"]:
        print("\n⚠️ 오류 내역:")
        for err in res["errors"]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
