from dataclasses import dataclass
import pandas as pd
from typing import Optional

@dataclass(frozen=True)
class FileContentReturn:
    file_path: str
    data: Optional[pd.DataFrame]
    error: Optional[str] = None