from .grading_dataclasses import (
    FilePath,
    FileDict,
    GradingItem,
    CopyFileItem,
    BatchGradingConfig,
    GradedResult,
)
from ..__about__ import __version__ as jupygrader_version
from ..constants import GRADED_RESULT_JSON_FILENAME
from ..notebook_operations import (
    get_test_cases_hash,
    extract_user_code_from_notebook,
)
from ..utils import download_file
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Union, Dict, Any, Tuple, TypedDict, Iterator
from pathlib import Path
import nbformat
from nbformat import NotebookNode
from nbclient import NotebookClient
import shutil
import json
import os
import tempfile
import pandas as pd
import contextlib
import hashlib
import sys
from datetime import datetime
import time
import uuid
import platform


class BatchGradingManager:
    def __init__(self, batch_config: BatchGradingConfig):
        self.verbose = batch_config.verbose
        self.batch_config = batch_config
