from pathlib import Path
from pypdf import PdfWriter

def merge_pdfs(folder, output):
    files = sorted(
        Path(folder).glob("*.pdf")
    )
    with PdfWriter() as writer:
        for pdf in files:
            writer.append(pdf)
        writer.write(output)
    return len(files)


# The lesson above is the exact function called below. The CLI adds safeguards.
def main():
    import argparse
    import hashlib
    import json
    import os
    import shutil
    import tempfile
    from pypdf import PdfReader

    parser = argparse.ArgumentParser(description="Merge lowercase .pdf files in filename order.")
    parser.add_argument("folder", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        folder = args.folder.resolve()
        output = args.output.resolve()
        if not folder.is_dir():
            raise ValueError("Input folder does not exist.")
        if output.suffix.lower() != ".pdf" or output.exists():
            raise ValueError("Choose a new output filename ending in .pdf.")
        if args.report and (args.report.exists() or args.report.resolve() == output):
            raise ValueError("Choose a separate, new report filename.")
        files = sorted(folder.glob("*.pdf"))
        if not files:
            raise ValueError("No lowercase .pdf files found.")
        records = []
        for pdf in files:
            digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
            with PdfReader(pdf, strict=True) as reader:
                if reader.is_encrypted or not reader.pages:
                    raise ValueError(f"Encrypted or empty PDF: {pdf.name}")
                for page in reader.pages:
                    content = page.get_contents()
                    if content is not None:
                        content.get_data()
                records.append({"file": pdf.name, "pages": len(reader.pages), "sha256": digest})
        expected = sum(record["pages"] for record in records)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="mel-pdf-", dir=output.parent) as tmp:
            staged = Path(tmp) / "merged.pdf"
            count = merge_pdfs(folder, staged)
            if count != len(records) or any(hashlib.sha256(pdf.read_bytes()).hexdigest() != record["sha256"] for pdf, record in zip(files, records)):
                raise ValueError("Inputs changed during merging. Retry with a stable folder.")
            with PdfReader(staged, strict=True) as reader:
                if len(reader.pages) != expected:
                    raise ValueError("Output page count failed verification.")
                for page in reader.pages:
                    content = page.get_contents()
                    if content is not None:
                        content.get_data()
            created = False
            try:
                with output.open("xb") as dest, staged.open("rb") as source:
                    created = True
                    shutil.copyfileobj(source, dest)
                    dest.flush()
                    os.fsync(dest.fileno())
                with PdfReader(output, strict=True) as reader:
                    if len(reader.pages) != expected:
                        raise ValueError("Final PDF verification failed.")
            except Exception:
                if created:
                    output.unlink(missing_ok=True)
                raise
        result = {"documents": count, "pages": expected, "processed": records,
                  "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(), "verified_readable": True}
        if args.report:
            with args.report.open("x", encoding="utf-8") as report:
                json.dump(result, report, indent=2)
        print(f"Merged {count} PDFs into {output.name}")
        print(f"Verified {expected} pages. Original files unchanged.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
