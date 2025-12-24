"""Auto-fix examples: add default provider and model_url to local_llm agents missing them.
Runs in-place on files under `examples/`.

This uses a conservative heuristic to avoid changing already-configured agents.
"""
from pathlib import Path
import re

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
DEFAULT_MODEL_URL = "http://localhost:1234"
DEFAULT_PROVIDER = "lm_studio"

def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    changed = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"\s*-\s*id:\s+", line):
            # start of an agent block, capture block lines until next '- id:' or end
            start = i
            j = i+1
            while j < len(lines) and not re.match(r"\s*-\s*id:\s+", lines[j]):
                j += 1
            block = "\n".join(lines[start:j])
            if "type: local_llm" in block:
                # look for model under 'params:' or at top-level
                if "params:" in block:
                    # Find params section and model inside it
                    m_params = re.search(r"params:\n(\s+[^\n]+\n)+", block)
                    if m_params:
                        params_block = m_params.group(0)
                        if re.search(r"\n\s*model_url:\s*", params_block) is None or re.search(r"\n\s*provider:\s*", params_block) is None:
                            # insert model_url and provider after the model line inside params
                            params_lines = params_block.splitlines()
                            for k, pl in enumerate(params_lines):
                                if re.search(r"\bmodel:\s*", pl):
                                    indent = re.match(r"(\s*)", pl).group(1)
                                    insert_lines = []
                                    if not re.search(r"\n\s*model_url:\s*", params_block):
                                        insert_lines.append(f"{indent}model_url: {DEFAULT_MODEL_URL}")
                                    if not re.search(r"\n\s*provider:\s*", params_block):
                                        insert_lines.append(f"{indent}provider: {DEFAULT_PROVIDER}")
                                    if insert_lines:
                                        params_lines[k+1:k+1] = insert_lines
                                        new_params_block = "\n".join(params_lines)
                                        block = block.replace(params_block, new_params_block)
                                        lines[start:j] = block.splitlines()
                                        changed += 1
                                    break
                else:
                    # look for top-level model line in the block
                    for k, bl in enumerate(lines[start:j]):
                        if re.search(r"\bmodel:\s*", bl):
                            # check within next 6 lines for provider/model_url
                            window = "\n".join(lines[k+1+start:min(j, k+7+start)])
                            to_insert = []
                            if re.search(r"\bmodel_url:\s*", window) is None:
                                to_insert.append(f"{re.match(r'(\s*)', bl).group(1)}model_url: {DEFAULT_MODEL_URL}")
                            if re.search(r"\bprovider:\s*", window) is None:
                                to_insert.append(f"{re.match(r'(\s*)', bl).group(1)}provider: {DEFAULT_PROVIDER}")
                            if to_insert:
                                insert_pos = k+1+start
                                lines[insert_pos:insert_pos] = to_insert
                                changed += 1
                            break
            i = j
        else:
            i += 1

    if changed:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def main():
    total = 0
    for p in sorted(EXAMPLES_DIR.rglob("*.yml")):
        changed = process_file(p)
        if changed:
            print(f"Patched {p.relative_to(EXAMPLES_DIR.parent)}: inserted {changed} entries")
            total += changed
    if total == 0:
        print("No changes necessary - all local_llm agents have provider and model_url set.")
    else:
        print(f"Done - total insertions: {total}")

if __name__ == '__main__':
    main()
