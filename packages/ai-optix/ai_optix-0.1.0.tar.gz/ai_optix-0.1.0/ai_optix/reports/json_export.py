# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

import json
import dataclasses
from ..mebs.core.stats import BenchmarkStats

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

def export_to_json(stats: BenchmarkStats, filepath: str):
    """
    Exports BenchmarkStats (including nested SystemMetrics) to a JSON file.
    """
    with open(filepath, 'w') as f:
        json.dump(stats, f, cls=EnhancedJSONEncoder, indent=2)
    print(f"Exported metrics to {filepath}")
