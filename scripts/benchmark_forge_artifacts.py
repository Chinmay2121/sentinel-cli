"""Run bounded Slither detection benchmarking over the FORGE manifest."""
import argparse, json, os, shutil, subprocess, time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

def solc_for(versions):
    roots = [Path.home()/".solc-select/artifacts", Path.home()/".foundry/bin"]
    text = " ".join(versions)
    for root in roots:
        if root.is_dir():
            for candidate in root.rglob("solc*"):
                if candidate.is_file() and os.access(candidate, os.X_OK) and any(v in candidate.name for v in ("0.8.25", "0.8.20", "0.8.19", "0.8.18")):
                    return candidate
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,default=Path("datasets/manifests/forge-artifacts.json"))
    p.add_argument("--dataset",type=Path,default=Path("datasets/forge-artifacts"))
    p.add_argument("--limit",type=int,default=10)
    p.add_argument("--timeout",type=int,default=45)
    p.add_argument("--output",type=Path,default=Path("reports/forge-benchmark"))
    a=p.parse_args(); manifest=json.loads(a.manifest.read_text()); slither=shutil.which("slither")
    if not slither: raise SystemExit("slither is required on PATH")
    rows=[]
    for case in manifest["cases"][:a.limit]:
        root=a.dataset/case["source_root"]; sources=sorted(root.rglob("*.sol"))
        row={"id":case["id"],"source_root":case["source_root"],"expected_findings":len(case["expected_findings"]),"status":""}
        if not sources: row["status"]="skipped_no_sources"; rows.append(row); continue
        solc=solc_for(case["compiler_versions"])
        if not solc: row["status"]="skipped_compiler_unavailable"; rows.append(row); continue
        started=time.monotonic()
        try:
            run=subprocess.run([slither,str(sources[0]),"--json","-"],cwd=root,env={**os.environ,"SOLC":str(solc)},text=True,capture_output=True,timeout=a.timeout)
            doc=json.loads(run.stdout); detectors=doc.get("results",{}).get("detectors",[]) if isinstance(doc,dict) else []
            row.update(status="completed",scanner_findings=len(detectors),duration_seconds=round(time.monotonic()-started,2))
        except subprocess.TimeoutExpired: row.update(status="timed_out",duration_seconds=round(time.monotonic()-started,2))
        except (OSError,json.JSONDecodeError) as exc:
            row.update(status="failed",duration_seconds=round(time.monotonic()-started,2),diagnostic=str(exc)[:400])
        rows.append(row)
    completed=[r for r in rows if r["status"]=="completed"]
    detected=sum(1 for r in completed if r.get("scanner_findings",0)>0)
    report={"dataset":"FORGE Artifacts","mode":"case-level detection coverage","cases_requested":len(rows),"completed":len(completed),"detected_positive_cases":detected,"recall_on_completed_positive_cases":round(detected/len(completed),4) if completed else None,"precision":None,"precision_note":"FORGE manifest contains audit-positive cases; add labeled clean controls before reporting precision or F1.","status_counts":dict(Counter(r["status"] for r in rows)),"cases":rows}
    a.output.mkdir(parents=True,exist_ok=True); stamp=datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out=a.output/f"forge-benchmark-{stamp}.json"; out.write_text(json.dumps(report,indent=2)+"\n")
    md=out.with_suffix(".md"); md.write_text("# FORGE Detection Benchmark\n\n"+"\n".join(f"- {k.replace('_',' ')}: **{v}**" for k,v in report.items() if k not in {"cases","precision_note"})+f"\n- Precision/F1: not reported — {report['precision_note']}\n")
    print(f"Benchmark report: {out}")
if __name__=="__main__": main()
