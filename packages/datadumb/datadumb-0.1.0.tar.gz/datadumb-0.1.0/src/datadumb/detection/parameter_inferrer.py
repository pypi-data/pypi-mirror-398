"""CSV parameter inference with confidence scoring."""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import io

from ..core.exceptions import ParameterInferenceError, format_error_message
from ..core.interfaces import ParameterInferrer
from ..core.models import FileFormat, LoadingParameters
from ..utils.logging import get_logger, log_parameter_inference_warning


logger = get_logger(__name__)


class CSVParameterInferrer(ParameterInferrer):
    """Infers CSV loading parameters through content analysis."""
    
    # Common separators to test, ordered by likelihood
    SEPARATORS = [",", ";", "\t", "|"]
    
    # Sample size for parameter inference
    SAMPLE_LINES = 20
    
    def __init__(self):
        """Initialize the CSV parameter inferrer."""
        self.confidence_threshold = 0.5
    
    def infer(self, file_path: Path, format: FileFormat) -> LoadingParameters:
        """Infer loading parameters for a CSV file.
        
        Args:
            file_path: Path to the CSV file to analyze
            format: File format (should be CSV)
            
        Returns:
            LoadingParameters with inferred CSV settings
            
        Raises:
            ParameterInferenceError: If parameters cannot be reliably inferred
        """
        if not self.supports_format(format):
            error = ParameterInferenceError(
                f"Format {format} not supported by CSV parameter inferrer",
                file_path=str(file_path)
            )
            logger.error(f"Unsupported format for CSV inference: {format}")
            raise error
        
        if not file_path.exists():
            error = ParameterInferenceError(
                format_error_message("file_not_found", file_path=file_path),
                file_path=str(file_path)
            )
            logger.error(f"File not found during parameter inference: {file_path}")
            raise error
        
        try:
            logger.debug(f"Starting CSV parameter inference for {file_path}")
            
            # Read sample content for analysis
            sample_content = self._read_sample_content(file_path)
            logger.debug(f"Read {len(sample_content)} sample lines for analysis")
            for i, line in enumerate(sample_content):
                logger.debug(f"  Line {i}: {repr(line)}")
            
            # Find the best separator by trying different approaches
            best_result = self._find_best_parameters(sample_content)
            
            # Get alternatives for logging
            alternatives = self._get_alternative_parameters(sample_content)
            
            # Log warnings for ambiguous results
            if best_result["confidence"] < 0.8:
                chosen_params = {
                    "separator": best_result["separator"],
                    "skip_rows": best_result["skip_rows"]
                }
                log_parameter_inference_warning(
                    logger,
                    str(file_path),
                    chosen_params,
                    alternatives,
                    best_result["confidence"]
                )
            
            # Add alternatives to additional params for context
            additional_params = {
                "separator_evidence": best_result["separator_evidence"],
                "validation_evidence": best_result["validation_evidence"],
                "alternatives": alternatives
            }
            
            logger.info(f"CSV parameter inference completed: separator='{best_result['separator']}', "
                       f"skip_rows={best_result['skip_rows']}, confidence={best_result['confidence']:.2f}")
            
            return LoadingParameters(
                format=FileFormat.CSV,
                separator=best_result["separator"],
                skip_rows=best_result["skip_rows"],
                encoding="utf-8",  # Default encoding
                has_header=best_result["has_header"],
                confidence_score=best_result["confidence"],
                additional_params=additional_params
            )
            
        except Exception as e:
            if isinstance(e, ParameterInferenceError):
                raise
            
            error_msg = format_error_message(
                "parameter_inference_failed",
                file_path=file_path,
                confidence=0.0
            )
            
            wrapped_error = ParameterInferenceError(
                error_msg,
                file_path=str(file_path),
                confidence_score=0.0
            )
            wrapped_error.__cause__ = e
            
            logger.error(f"Parameter inference failed for {file_path}: {e}", exc_info=True)
            raise wrapped_error
    
    def supports_format(self, format: FileFormat) -> bool:
        """Check if this inferrer supports a format."""
        return format == FileFormat.CSV
    
    def _find_best_parameters(self, lines: List[str]) -> Dict[str, Any]:
        """Find the best parameters by trying different approaches.
        
        Args:
            lines: Sample lines from the file
            
        Returns:
            Dictionary with best parameters and evidence
        """
        if not lines:
            return {
                "separator": ",",
                "skip_rows": 0,
                "confidence": 0.1,
                "has_header": True,
                "separator_evidence": {"reason": "no_content"},
                "validation_evidence": {"reason": "no_content"}
            }
        
        # Approach 1: Try to detect separator on full content first
        full_separator_result = self._detect_separator(lines)
        
        # Try the full content approach
        skip_rows = self._detect_skip_rows(lines, full_separator_result["separator"])
        validation_result = self._validate_parameters(
            lines, 
            full_separator_result["separator"], 
            skip_rows
        )
        
        full_confidence = min(full_separator_result["confidence"], validation_result["confidence"])
        
        # Score based on confidence and structural consistency
        min_cols = full_separator_result["evidence"]["best_score"]["evidence"].get("min_columns", 1)
        consistency = validation_result["evidence"].get("consistency", 0)
        full_score = full_confidence * min_cols * (1 + consistency)
        
        logger.debug(f"Full content approach: separator='{full_separator_result['separator']}', "
                    f"skip_rows={skip_rows}, confidence={full_confidence:.3f}, score={full_score:.3f}")
        
        best_result = {
            "separator": full_separator_result["separator"],
            "skip_rows": skip_rows,
            "confidence": full_confidence,
            "has_header": validation_result["has_header"],
            "separator_evidence": full_separator_result["evidence"],
            "validation_evidence": validation_result["evidence"]
        }
        best_score = full_score
        
        # Only try alternative starting points if the full content approach has low confidence
        if full_separator_result["confidence"] < 0.7:
            # Approach 2: Try to find obvious metadata lines and skip them
            potential_starts = self._find_potential_data_starts(lines)
            
            # Try each potential start point (but only if they're different from 0)
            for start_row in potential_starts:
                if start_row == 0:
                    continue  # Already tried this
                    
                data_lines = lines[start_row:]
                if len(data_lines) < 2:  # Need at least 2 lines for meaningful analysis
                    continue
                
                # Detect separator for this subset
                separator_result = self._detect_separator(data_lines)
                
                # Validate parameters across sample rows
                validation_result = self._validate_parameters(
                    data_lines, 
                    separator_result["separator"], 
                    0  # No additional skip since we already identified the start
                )
                
                # Calculate overall confidence
                overall_confidence = min(
                    separator_result["confidence"],
                    validation_result["confidence"]
                )
                
                # Score based on confidence, columns, and consistency
                min_cols = separator_result["evidence"]["best_score"]["evidence"].get("min_columns", 1)
                consistency = validation_result["evidence"].get("consistency", 0)
                score = overall_confidence * min_cols * (1 + consistency)
                
                logger.debug(f"Alternative start_row={start_row}: separator='{separator_result['separator']}', "
                           f"confidence={overall_confidence:.3f}, score_before_bonuses={score:.3f}")
                
                # Bonus for having more than 1 column (actual CSV structure)
                if min_cols >= 2:
                    score *= 1.2
                
                # Bonus for skipping obvious metadata
                if start_row > 0:
                    score *= 1.1
                
                # But penalize heavily if we're ignoring a high-confidence full analysis
                # or if the full analysis has reasonable confidence
                if full_separator_result["confidence"] > 0.3:
                    score *= 0.1  # Very heavy penalty for skipping when full analysis is decent
                
                # Additional penalty for skipping rows without strong evidence
                # Only skip if the improvement is substantial
                if start_row > 0 and score <= best_score * 2.0:
                    score *= 0.1  # Heavy penalize unless there's a major improvement
                
                logger.debug(f"Alternative start_row={start_row}: final_score={score:.3f}, "
                           f"best_score_so_far={best_score:.3f}")
                
                if score > best_score:
                    logger.debug(f"New best result: start_row={start_row}, score={score:.3f}")
                    best_score = score
                    best_result = {
                        "separator": separator_result["separator"],
                        "skip_rows": start_row,
                        "confidence": overall_confidence,
                        "has_header": validation_result["has_header"],
                        "separator_evidence": separator_result["evidence"],
                        "validation_evidence": validation_result["evidence"]
                    }
        
        return best_result
    
    def _find_potential_data_starts(self, lines: List[str]) -> List[int]:
        """Find potential starting points for actual CSV data.
        
        Args:
            lines: Sample lines from the file
            
        Returns:
            List of line indices where data might start
        """
        if not lines:
            return [0]
        
        potential_starts = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue  # Skip empty lines
            
            # Skip obvious metadata/comment lines
            if (stripped.startswith('#') or 
                stripped.startswith('//') or 
                stripped.startswith('/*') or
                stripped.lower().startswith('metadata') or
                stripped.lower().startswith('comment')):
                continue
            
            # This could be a data line
            potential_starts.append(i)
        
        # Always include 0 as a fallback
        if 0 not in potential_starts:
            potential_starts.insert(0, 0)
        
        # Limit to first few potential starts to avoid excessive computation
        return potential_starts[:5]
    
    def _read_sample_content(self, file_path: Path) -> List[str]:
        """Read sample lines from the file for analysis.
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of sample lines from the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= self.SAMPLE_LINES:
                        break
                    lines.append(line.rstrip('\n\r'))
                return lines
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= self.SAMPLE_LINES:
                        break
                    lines.append(line.rstrip('\n\r'))
                return lines
    
    def _detect_separator(self, lines: List[str]) -> Dict[str, Any]:
        """Detect the most likely separator for CSV content.
        
        Args:
            lines: Sample lines from the file
            
        Returns:
            Dictionary with separator, confidence, and evidence
        """
        if not lines:
            return {
                "separator": ",",
                "confidence": 0.1,
                "evidence": {"reason": "no_content", "default": True}
            }
        
        separator_scores = {}
        
        for separator in self.SEPARATORS:
            score = self._score_separator(lines, separator)
            separator_scores[separator] = score
        
        # Find the best separator
        best_separator = max(separator_scores.keys(), key=lambda s: separator_scores[s]["score"])
        best_score = separator_scores[best_separator]
        
        # Calculate confidence based on score difference and absolute score
        scores = [s["score"] for s in separator_scores.values()]
        scores.sort(reverse=True)
        
        if len(scores) > 1 and scores[0] > 0:
            # Confidence based on how much better the best score is
            if scores[1] > 0:
                score_ratio = scores[0] / scores[1]
                confidence = min(0.95, 0.5 + (score_ratio - 1) * 0.3)
            else:
                confidence = 0.9  # Only one separator worked
            
            # Adjust confidence based on absolute score quality
            if scores[0] >= 1.0:  # Good structural match
                confidence = max(confidence, 0.8)
            elif scores[0] < 0.3:  # Poor structural match
                confidence = min(confidence, 0.5)
                
        else:
            confidence = 0.1 if scores[0] == 0 else 0.6
        
        return {
            "separator": best_separator,
            "confidence": confidence,
            "evidence": {
                "scores": separator_scores,
                "best_score": best_score
            }
        }
    
    def _score_separator(self, lines: List[str], separator: str) -> Dict[str, Any]:
        """Score how well a separator works for the given lines.
        
        Args:
            lines: Sample lines from the file
            separator: Separator to test
            
        Returns:
            Dictionary with score and evidence
        """
        if not lines:
            return {"score": 0, "evidence": {"reason": "no_lines"}}
        
        # Filter out empty lines
        non_empty_lines = [line for line in lines if line.strip()]
        if not non_empty_lines:
            return {"score": 0, "evidence": {"reason": "no_content"}}
        
        # Count columns for each line with position weighting
        column_counts = []
        quoted_field_count = 0
        parse_errors = 0
        weighted_scores = []
        
        for i, line in enumerate(non_empty_lines):
            # Give more weight to earlier lines (headers and clean data)
            line_weight = max(0.5, 1.0 - (i * 0.1))
            
            # Clean up trailing separators that might confuse the analysis
            cleaned_line = line.rstrip()
            if cleaned_line.endswith(separator):
                cleaned_line = cleaned_line.rstrip(separator)
            
            # Handle quoted fields properly
            try:
                # Use csv.reader to properly parse the line
                reader = csv.reader(io.StringIO(cleaned_line), delimiter=separator)
                row = next(reader)
                col_count = len(row)
                column_counts.append(col_count)
                
                # Count quoted fields (fields that contain the separator)
                if separator in cleaned_line and any(separator in field for field in row):
                    quoted_field_count += 1
                
                # Score this line: prefer 2+ columns, penalize 1 column
                if col_count >= 2:
                    line_score = 1.0 * line_weight
                else:
                    line_score = 0.1 * line_weight
                
                # Bonus for proper CSV parsing (no parse errors)
                line_score *= 1.2
                    
                weighted_scores.append(line_score)
                    
            except (csv.Error, StopIteration):
                # If csv.reader fails, fall back to simple split
                cleaned_line = line.rstrip()
                if cleaned_line.endswith(separator):
                    cleaned_line = cleaned_line.rstrip(separator)
                
                parts = cleaned_line.split(separator)
                col_count = len(parts)
                column_counts.append(col_count)
                parse_errors += 1
                
                # Penalize parse errors
                line_score = 0.05 * line_weight
                weighted_scores.append(line_score)
        
        if not column_counts:
            return {"score": 0, "evidence": {"reason": "no_parseable_lines"}}
        
        # Calculate consistency score
        unique_counts = set(column_counts)
        consistency_score = 1.0 / len(unique_counts) if unique_counts else 0
        
        # Minimum column requirement (at least 2 columns for CSV)
        min_columns = min(column_counts)
        max_columns = max(column_counts)
        
        # Column score: prefer separators that give at least 2 columns
        if min_columns >= 2:
            column_score = 1.0
        elif min_columns == 1 and max_columns >= 2:
            # Some lines have multiple columns, some don't - might be metadata
            column_score = 0.5
        else:
            column_score = 0.1  # All lines have only 1 column
        
        # Bonus for handling quoted fields correctly
        quoted_bonus = 0.1 if quoted_field_count > 0 else 0
        
        # Penalty for parse errors
        parse_penalty = parse_errors / len(non_empty_lines) * 0.3
        
        # Penalty for very inconsistent column counts (but allow some variation)
        if max_columns > min_columns * 3:  # Too much variation
            consistency_score *= 0.3
        elif max_columns > min_columns * 2:
            consistency_score *= 0.7
        
        # Special bonus for separators that create consistent multi-column structure
        if min_columns >= 2 and len(unique_counts) == 1:
            consistency_score *= 1.5  # Perfect consistency bonus
        
        # Use weighted average of line scores
        avg_weighted_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0
        
        # Combine all factors
        total_score = (avg_weighted_score * consistency_score * column_score + quoted_bonus) - parse_penalty
        total_score = max(0, total_score)  # Ensure non-negative
        
        return {
            "score": total_score,
            "evidence": {
                "column_counts": column_counts,
                "unique_counts": list(unique_counts),
                "consistency_score": consistency_score,
                "column_score": column_score,
                "quoted_fields": quoted_field_count,
                "parse_errors": parse_errors,
                "min_columns": min_columns,
                "max_columns": max_columns,
                "weighted_scores": weighted_scores,
                "avg_weighted_score": avg_weighted_score
            }
        }
    
    def _detect_skip_rows(self, lines: List[str], separator: str) -> int:
        """Detect how many rows to skip before the actual data table.
        
        Args:
            lines: Sample lines from the file
            separator: Detected separator
            
        Returns:
            Number of rows to skip
        """
        if not lines:
            return 0
        
        # Look for the first row that looks like structured data
        for i, line in enumerate(lines):
            if not line.strip():
                continue  # Skip empty lines
            
            # Skip obvious metadata lines (comments, etc.)
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                continue
            
            # Check if this line has a reasonable number of columns
            try:
                reader = csv.reader(io.StringIO(line), delimiter=separator)
                row = next(reader)
                
                if len(row) >= 2:  # At least 2 columns
                    # Check if the next few lines have similar structure
                    remaining_lines = [l for l in lines[i:] if l.strip()]
                    if len(remaining_lines) >= 2 and self._has_consistent_structure(remaining_lines[:3], separator):
                        return i
                        
            except (csv.Error, StopIteration):
                continue
        
        return 0  # Default to no skip rows
    
    def _has_consistent_structure(self, lines: List[str], separator: str) -> bool:
        """Check if lines have consistent CSV structure.
        
        Args:
            lines: Lines to check
            separator: Separator to use
            
        Returns:
            True if lines have consistent structure
        """
        if len(lines) < 2:
            return False
        
        column_counts = []
        parse_errors = 0
        
        for line in lines:
            if not line.strip():
                continue
            
            try:
                reader = csv.reader(io.StringIO(line), delimiter=separator)
                row = next(reader)
                column_counts.append(len(row))
            except (csv.Error, StopIteration):
                parse_errors += 1
                # For malformed lines, try simple split as fallback
                parts = line.split(separator)
                column_counts.append(len(parts))
        
        if not column_counts:
            return False
        
        # Allow some parsing errors, but not too many
        error_rate = parse_errors / len(column_counts) if column_counts else 1.0
        if error_rate > 0.5:  # More than 50% parse errors
            return False
        
        # Check if most lines have the same number of columns and at least 2 columns
        from collections import Counter
        count_freq = Counter(column_counts)
        most_common_count, freq = count_freq.most_common(1)[0]
        
        # Require that the most common column count appears in at least 60% of lines
        # and that it's at least 2 columns
        consistency_ratio = freq / len(column_counts)
        return consistency_ratio >= 0.6 and most_common_count >= 2
    
    def _validate_parameters(self, lines: List[str], separator: str, skip_rows: int) -> Dict[str, Any]:
        """Validate detected parameters across sample rows.
        
        Args:
            lines: Sample lines from the file
            separator: Detected separator
            skip_rows: Number of rows to skip
            
        Returns:
            Dictionary with validation results and confidence
        """
        if skip_rows >= len(lines):
            return {
                "confidence": 0.1,
                "has_header": True,
                "evidence": {"reason": "skip_rows_too_large"}
            }
        
        data_lines = lines[skip_rows:]
        if not data_lines:
            return {
                "confidence": 0.1,
                "has_header": True,
                "evidence": {"reason": "no_data_lines"}
            }
        
        # Parse all data lines
        parsed_rows = []
        parse_errors = 0
        
        for line in data_lines:
            if not line.strip():
                continue
            
            try:
                reader = csv.reader(io.StringIO(line), delimiter=separator)
                row = next(reader)
                parsed_rows.append(row)
            except (csv.Error, StopIteration):
                parse_errors += 1
        
        if not parsed_rows:
            return {
                "confidence": 0.1,
                "has_header": True,
                "evidence": {"reason": "no_parseable_rows"}
            }
        
        # Check column consistency
        column_counts = [len(row) for row in parsed_rows]
        unique_counts = set(column_counts)
        consistency = 1.0 / len(unique_counts) if unique_counts else 0
        
        # Detect if first row looks like a header
        has_header = self._detect_header(parsed_rows)
        
        # Calculate confidence based on consistency and parse success
        parse_success_rate = 1.0 - (parse_errors / max(len(data_lines), 1))
        confidence = consistency * parse_success_rate
        
        return {
            "confidence": confidence,
            "has_header": has_header,
            "evidence": {
                "parsed_rows": len(parsed_rows),
                "parse_errors": parse_errors,
                "column_counts": column_counts,
                "consistency": consistency,
                "parse_success_rate": parse_success_rate
            }
        }
    
    def _detect_header(self, parsed_rows: List[List[str]]) -> bool:
        """Detect if the first row looks like a header.
        
        Args:
            parsed_rows: Parsed CSV rows
            
        Returns:
            True if first row appears to be a header
        """
        if len(parsed_rows) < 2:
            return True  # Default assumption
        
        first_row = parsed_rows[0]
        second_row = parsed_rows[1]
        
        if len(first_row) != len(second_row):
            return True  # Different column counts suggest header
        
        # Check if first row values look like column names
        header_indicators = 0
        for value in first_row:
            value = value.strip()
            if value:
                # Headers are often shorter and contain no numbers
                if len(value) < 20 and not any(char.isdigit() for char in value):
                    header_indicators += 1
        
        # If most values in first row look like headers
        return header_indicators >= len(first_row) * 0.6
    
    def _get_alternative_parameters(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Get alternative parameter combinations for logging.
        
        Args:
            lines: Sample lines from the file
            
        Returns:
            List of alternative parameter combinations
        """
        alternatives = []
        
        for separator in self.SEPARATORS:
            score_result = self._score_separator(lines, separator)
            if score_result["score"] > 0.1:
                skip_rows = self._detect_skip_rows(lines, separator)
                alternatives.append({
                    "separator": separator,
                    "skip_rows": skip_rows,
                    "score": score_result["score"]
                })
        
        # Sort by score descending
        alternatives.sort(key=lambda x: x["score"], reverse=True)
        return alternatives[:3]  # Return top 3 alternatives


class ParameterInferrerRegistry:
    """Registry for managing parameter inference strategies."""
    
    def __init__(self):
        self._inferrers: List[ParameterInferrer] = []
        self._format_support: Dict[FileFormat, List[ParameterInferrer]] = {}
        
        # Register default inferrer
        self.register(CSVParameterInferrer())
    
    def register(self, inferrer: ParameterInferrer) -> None:
        """Register a parameter inferrer.
        
        Args:
            inferrer: ParameterInferrer instance to register
        """
        if inferrer not in self._inferrers:
            self._inferrers.append(inferrer)
            
            # Update format support mapping
            for format_type in FileFormat:
                if inferrer.supports_format(format_type):
                    if format_type not in self._format_support:
                        self._format_support[format_type] = []
                    self._format_support[format_type].append(inferrer)
    
    def unregister(self, inferrer: ParameterInferrer) -> None:
        """Unregister a parameter inferrer.
        
        Args:
            inferrer: ParameterInferrer instance to unregister
        """
        if inferrer in self._inferrers:
            self._inferrers.remove(inferrer)
            
            # Update format support mapping
            for format_list in self._format_support.values():
                if inferrer in format_list:
                    format_list.remove(inferrer)
    
    def infer_parameters(self, file_path: Path, format: FileFormat) -> LoadingParameters:
        """Infer parameters using registered inferrers.
        
        Args:
            file_path: Path to the file to analyze
            format: Detected file format
            
        Returns:
            LoadingParameters with inferred settings
            
        Raises:
            ParameterInferenceError: If no suitable inferrer is found
        """
        inferrers = self._format_support.get(format, [])
        
        if not inferrers:
            # Return default parameters for unsupported formats without warnings
            # Non-CSV formats don't need parameter inference
            return LoadingParameters(
                format=format,
                separator=None,  # No separator for non-CSV formats
                skip_rows=0,
                encoding="utf-8",
                has_header=True,
                confidence_score=1.0,  # High confidence for default parameters
                additional_params={"reason": "no_inferrer_needed"}
            )
        
        # Use the first available inferrer
        # In the future, this could try multiple inferrers and pick the best result
        return inferrers[0].infer(file_path, format)
    
    def get_inferrers_for_format(self, format: FileFormat) -> List[ParameterInferrer]:
        """Get inferrers that support a specific format.
        
        Args:
            format: FileFormat to query
            
        Returns:
            List of ParameterInferrer instances supporting the format
        """
        return self._format_support.get(format, []).copy()


# Global registry instance
_registry = ParameterInferrerRegistry()


def get_parameter_inferrer() -> ParameterInferrerRegistry:
    """Get the global parameter inferrer registry.
    
    Returns:
        ParameterInferrerRegistry instance
    """
    return _registry


def infer_file_parameters(file_path: Path, format: FileFormat) -> LoadingParameters:
    """Convenience function to infer file parameters.
    
    Args:
        file_path: Path to the file to analyze
        format: Detected file format
        
    Returns:
        LoadingParameters with inferred settings
    """
    return _registry.infer_parameters(file_path, format)