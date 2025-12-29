E1 - Dataset instructions

This folder should contain a JSONL file `edgar_subset.jsonl` with financial documents for E1.
Each line should be a JSON object with fields:
- id: unique id
- filename: source filename
- text: full document text

Example line:
{ "id": "doc-0001", "filename": "10-K-0001.txt", "text": "Full text of filing..." }

Notes:
- Use a representative sample (~200 documents) for initial experiments.
- Keep data private or anonymized if required by license.
- Provide a `splits/` folder with `train.jsonl`, `dev.jsonl`, `test.jsonl` if running downstream QA evals.
