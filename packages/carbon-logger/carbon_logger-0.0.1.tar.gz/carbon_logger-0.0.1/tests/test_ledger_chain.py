import os
from pathlib import Path

from carbon_logger.decorator import track_carbon, verify_ledger


def test_ledger_chain(tmp_path: Path) -> None:
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        @track_carbon(project="t", task="x")
        def f():
            return {"llm_tokens": 1000}

        f()
        assert verify_ledger() is True
    finally:
        os.chdir(cwd)
