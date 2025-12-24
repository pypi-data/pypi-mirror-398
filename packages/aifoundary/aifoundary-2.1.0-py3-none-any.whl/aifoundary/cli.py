import argparse
import json
from pathlib import Path

from aifoundary.rag.secure_rag import validate_rag
from aifoundary.audit import verify_chain


def run_rag_check(prompt_path: Path, context_path: Path, json_mode: bool):
    prompt = prompt_path.read_text()
    context = context_path.read_text()
    contexts = [context]

    verdict = validate_rag(prompt, contexts)

    if json_mode:
        print(json.dumps(verdict))
        return

    print("RAG Compliance Verdict")
    print("----------------------")
    print(f"Allowed: {verdict['allowed']}")
    print(f"Reason: {verdict['reason']}")


def main():
    parser = argparse.ArgumentParser(prog="aifoundary")
    sub = parser.add_subparsers(dest="cmd", required=True)

    rag = sub.add_parser("rag-check", help="Validate RAG prompt + context")
    rag.add_argument("prompt")
    rag.add_argument("context")
    rag.add_argument("--json", action="store_true")

    sub.add_parser("audit-verify", help="Verify tamper-evident audit chain")

    args = parser.parse_args()

    if args.cmd == "rag-check":
        run_rag_check(Path(args.prompt), Path(args.context), args.json)

    elif args.cmd == "audit-verify":
        ok, msg = verify_chain()
        if ok:
            print("AUDIT OK:", msg)
        else:
            print("AUDIT FAILED:", msg)
            raise SystemExit(1)


if __name__ == "__main__":
    main()
