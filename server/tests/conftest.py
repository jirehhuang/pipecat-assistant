"""Configure shared test fixtures."""

from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).resolve().parents[1]
dotenv_file = (
    env_path / ".env.test"
    if (env_path / ".env.test").exists()
    else env_path / ".env"
)
load_dotenv(dotenv_file, override=True)
