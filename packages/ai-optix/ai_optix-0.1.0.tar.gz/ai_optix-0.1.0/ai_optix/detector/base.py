# SPDX-FileCopyrightText: 2025 ai-foundation-software
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Dict, Any, List

class Issue:
    def __init__(self, name: str, severity: str, evidence: str, suggestion: str):
        self.name = name
        self.severity = severity # "high", "medium", "low"
        self.evidence = evidence
        self.suggestion = suggestion

    def to_dict(self) -> Dict[str, str]:
        return {
            "issue": self.name,
            "severity": self.severity,
            "evidence": self.evidence,
            "suggestion": self.suggestion
        }

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, metrics: List[Dict[str, Any]]) -> List[Issue]:
        """ Analyze metrics and return list of issues. """
        pass
