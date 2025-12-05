"""
V2 Dilemma loader and management.

Handles loading, validation, and access to V2 out-of-distribution moral dilemmas
designed to test genuine moral reasoning rather than pattern-matching.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..data.schemas import (
    DilemmaV2,
    DilemmaStructure,
    ConsistencyCase,
    AsymmetricFeatures,
    ProbeQuestion,
)


class DilemmaLoaderV2:
    """Loads and manages V2 moral dilemmas with probe question support."""

    # Fixed probe order per protocol
    PROBE_ORDER = [
        "principle_articulation",
        "consistency_check",
        "stakeholder_standing",
        "uncertainty_integration",
        "steelmanning",
        "meta_awareness",
    ]

    def __init__(self, dilemmas_file: Optional[Path] = None):
        """
        Initialize V2 dilemma loader.

        Args:
            dilemmas_file: Path to V2 dilemmas JSON file. If None, uses default location.
        """
        if dilemmas_file is None:
            project_root = Path(__file__).parent.parent.parent
            dilemmas_file = project_root / "data" / "dilemmas" / "dilemmas_v2.json"

        self.dilemmas_file = Path(dilemmas_file)
        self.dilemmas: Dict[str, DilemmaV2] = {}
        self.probes: Dict[str, ProbeQuestion] = {}
        self.presentation_order: List[str] = []
        self.scoring_config: Dict = {}
        self._load_dilemmas()

    def _load_dilemmas(self) -> None:
        """Load V2 dilemmas from JSON file."""
        if not self.dilemmas_file.exists():
            raise FileNotFoundError(
                f"V2 dilemmas file not found: {self.dilemmas_file}"
            )

        with open(self.dilemmas_file, 'r') as f:
            data = json.load(f)

        # Load dilemmas
        for d in data.get("dilemmas", []):
            # Parse consistency case
            consistency_case = ConsistencyCase(
                description=d["consistency_case"]["description"],
                structural_parallel=d["consistency_case"]["structural_parallel"]
            )

            # Parse asymmetric features if present
            asymmetric_features = None
            if d.get("asymmetric_features"):
                asymmetric_features = AsymmetricFeatures(
                    power_structure=d["asymmetric_features"]["power_structure"],
                    consent_status=d["asymmetric_features"]["consent_status"],
                    exit_option=d["asymmetric_features"]["exit_option"]
                )

            dilemma = DilemmaV2(
                id=d["id"],
                category=d["category"],
                structure=DilemmaStructure(d["structure"]),
                title=d["title"],
                description=d["description"],
                core_questions=d["core_questions"],
                tests=d.get("tests", []),
                consistency_case=consistency_case,
                asymmetric_features=asymmetric_features
            )
            self.dilemmas[dilemma.id] = dilemma

        # Load administration config
        admin = data.get("administration", {})
        self.presentation_order = admin.get("presentation_order", list(self.dilemmas.keys()))

        # Load universal probes
        for probe_data in admin.get("universal_probes", []):
            probe = ProbeQuestion(
                id=probe_data["id"],
                question=probe_data["question"],
                followup=probe_data["followup"],
                assesses=probe_data["assesses"]
            )
            self.probes[probe.id] = probe

        # Load scoring config
        self.scoring_config = data.get("scoring", {})

    def get_dilemma(self, dilemma_id: str) -> DilemmaV2:
        """
        Get a specific dilemma by ID.

        Args:
            dilemma_id: ID of the dilemma

        Returns:
            DilemmaV2 object

        Raises:
            KeyError: If dilemma ID not found
        """
        if dilemma_id not in self.dilemmas:
            raise KeyError(
                f"Dilemma '{dilemma_id}' not found. "
                f"Available: {list(self.dilemmas.keys())}"
            )
        return self.dilemmas[dilemma_id]

    def get_dilemmas_in_order(self) -> List[DilemmaV2]:
        """
        Get all dilemmas in the fixed presentation order.

        The order alternates symmetric and asymmetric structures.

        Returns:
            List of DilemmaV2 objects in presentation order
        """
        return [self.dilemmas[did] for did in self.presentation_order if did in self.dilemmas]

    def get_dilemmas_by_structure(self, structure: DilemmaStructure) -> List[DilemmaV2]:
        """
        Get all dilemmas with a specific structure type.

        Args:
            structure: DilemmaStructure.SYMMETRIC or DilemmaStructure.ASYMMETRIC

        Returns:
            List of matching dilemmas
        """
        return [d for d in self.dilemmas.values() if d.structure == structure]

    def get_all_dilemmas(self) -> List[DilemmaV2]:
        """Get all dilemmas (not in any particular order)."""
        return list(self.dilemmas.values())

    def get_dilemma_ids(self) -> List[str]:
        """Get all dilemma IDs in presentation order."""
        return self.presentation_order.copy()

    def get_probe(self, probe_id: str) -> ProbeQuestion:
        """
        Get a specific probe question.

        Args:
            probe_id: ID of the probe

        Returns:
            ProbeQuestion object

        Raises:
            KeyError: If probe ID not found
        """
        if probe_id not in self.probes:
            raise KeyError(
                f"Probe '{probe_id}' not found. "
                f"Available: {list(self.probes.keys())}"
            )
        return self.probes[probe_id]

    def get_probes_in_order(self) -> List[ProbeQuestion]:
        """Get all probes in the fixed order."""
        return [self.probes[pid] for pid in self.PROBE_ORDER if pid in self.probes]

    def get_initial_prompt(self, dilemma_id: str) -> str:
        """
        Generate the initial open-ended prompt for a dilemma.

        This presents the scenario and core questions without forcing
        a binary choice.

        Args:
            dilemma_id: ID of the dilemma

        Returns:
            Formatted prompt string
        """
        dilemma = self.get_dilemma(dilemma_id)

        questions_text = "\n".join(f"- {q}" for q in dilemma.core_questions)

        prompt = f"""Consider the following moral scenario:

{dilemma.description}

{questions_text}

Please provide your response. Consider what you would do and why, explaining your reasoning."""
        return prompt

    def get_probe_prompt(
        self,
        probe_id: str,
        dilemma_id: str,
        prior_response: Optional[str] = None
    ) -> str:
        """
        Generate a probe question prompt.

        For the consistency_check probe, this injects the dilemma-specific
        consistency case.

        Args:
            probe_id: ID of the probe
            dilemma_id: ID of the current dilemma
            prior_response: The agent's previous response (for context)

        Returns:
            Formatted probe prompt string
        """
        probe = self.get_probe(probe_id)
        dilemma = self.get_dilemma(dilemma_id)

        question = probe.question

        # For consistency check, inject the specific consistency case
        if probe_id == "consistency_check":
            question = question.replace(
                "[consistency case]",
                dilemma.consistency_case.description
            )

        # For uncertainty integration, we'd need to extract key assumption
        # from the response - for now, use a generic phrasing
        if probe_id == "uncertainty_integration":
            question = question.replace(
                "[key factual assumption]",
                "one of the key factual assumptions in your reasoning"
            )

        return f"""Based on your previous response, I have a follow-up question:

{question}"""

    def get_followup_prompt(self, probe_id: str) -> str:
        """
        Get the follow-up prompt for a probe.

        Used if the initial probe response needs clarification.

        Args:
            probe_id: ID of the probe

        Returns:
            Follow-up prompt string
        """
        probe = self.get_probe(probe_id)
        return probe.followup

    def get_scoring_dimensions(self) -> List[Dict]:
        """Get the scoring dimension definitions."""
        return self.scoring_config.get("dimensions", [])

    def get_scoring_profiles(self) -> Dict:
        """Get the reasoner profile definitions."""
        return self.scoring_config.get("profiles", {})

    def get_red_flags(self) -> List[str]:
        """Get the list of red flag definitions."""
        return self.scoring_config.get("red_flags", [])

    def __len__(self) -> int:
        """Return number of dilemmas."""
        return len(self.dilemmas)

    def __repr__(self) -> str:
        return f"DilemmaLoaderV2({len(self)} dilemmas from {self.dilemmas_file})"
