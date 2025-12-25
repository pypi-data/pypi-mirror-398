"""JSON reporter for evaluation results."""

import json
from pathlib import Path
from typing import List, Union, Dict, Any
from evalview.core.types import EvaluationResult


class JSONReporter:
    """Generates JSON reports from evaluation results."""

    @staticmethod
    def save(results: List[EvaluationResult], output_path: Union[str, Path]) -> None:
        """
        Save evaluation results to JSON file.

        Args:
            results: List of evaluation results
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict for JSON serialization
        results_dict = [result.model_dump(mode="json") for result in results]

        with open(output_path, "w") as f:
            json.dump(results_dict, f, indent=2, default=str)

    @staticmethod
    def load(input_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Load evaluation results from JSON file.

        Args:
            input_path: Path to JSON file

        Returns:
            List of result dictionaries
        """
        with open(input_path, "r") as f:
            return json.load(f)

    @staticmethod
    def load_as_results(input_path: Union[str, Path]) -> List[EvaluationResult]:
        """
        Load evaluation results from JSON file as EvaluationResult objects.

        Args:
            input_path: Path to JSON file

        Returns:
            List of EvaluationResult objects
        """
        data = JSONReporter.load(input_path)
        return [EvaluationResult.model_validate(item) for item in data]

    @staticmethod
    def get_latest_results(results_dir: Union[str, Path]) -> Union[List[EvaluationResult], None]:
        """
        Get the most recent results from the results directory.

        Args:
            results_dir: Path to results directory (e.g., .evalview/results)

        Returns:
            List of EvaluationResult objects from the most recent run, or None
        """
        results_dir = Path(results_dir)
        if not results_dir.exists():
            return None

        # Find all JSON files sorted by name (timestamp-based naming)
        json_files = sorted(results_dir.glob("*.json"), reverse=True)
        if not json_files:
            return None

        # Return the most recent (skip the current run which hasn't been saved yet)
        # Since files are named with timestamps, the second-most-recent is the "last run"
        if len(json_files) >= 1:
            try:
                return JSONReporter.load_as_results(json_files[0])
            except Exception:
                return None
        return None
