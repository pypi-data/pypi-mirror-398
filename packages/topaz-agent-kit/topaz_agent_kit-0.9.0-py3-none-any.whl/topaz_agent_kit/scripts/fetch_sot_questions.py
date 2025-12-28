#!/usr/bin/env python3
"""Fetch SQL-of-Thought Questions Script.

Selects random questions from Spider 1.0 dev dataset and saves them to
questions_to_process.json for pipeline processing.

Usage:
    uv run -m topaz_agent_kit.scripts.fetch_sot_questions --project-dir projects/ensemble --count 3 --seed 42
    uv run -m topaz_agent_kit.scripts.fetch_sot_questions --project-dir projects/ensemble --count 20 --output-file custom_questions.json
"""

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from topaz_agent_kit.utils.path_resolver import resolve_script_path, detect_project_name
from topaz_agent_kit.utils.logger import Logger

logger = Logger("FetchSOTQuestions")


def load_dev_data(dev_json_path: Path) -> List[Dict[str, Any]]:
    """Load dev.json file."""
    if not dev_json_path.exists():
        logger.error("dev.json not found at: {}", dev_json_path)
        raise FileNotFoundError(f"dev.json not found at: {dev_json_path}")
    
    try:
        with open(dev_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info("Loaded {} examples from dev.json", len(data))
        return data
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in dev.json: {}", e)
        raise
    except Exception as e:
        logger.error("Failed to load dev.json: {}", e)
        raise


def group_by_difficulty(examples: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group examples by difficulty/hardness level."""
    grouped = {}
    
    # Check for 'hardness' or 'difficulty' field (Spider dataset uses 'hardness')
    difficulty_field = None
    if examples:
        first_example = examples[0]
        if "hardness" in first_example:
            difficulty_field = "hardness"
        elif "difficulty" in first_example:
            difficulty_field = "difficulty"
    
    if not difficulty_field:
        logger.info("No difficulty/hardness field found in examples. Will use random selection.")
        return {}
    
    for example in examples:
        difficulty = example.get(difficulty_field, "unknown")
        if difficulty not in grouped:
            grouped[difficulty] = []
        grouped[difficulty].append(example)
    
    logger.info("Grouped examples by {}: {}", difficulty_field, {k: len(v) for k, v in grouped.items()})
    return grouped


def select_random_questions(
    examples: List[Dict[str, Any]], 
    count: int, 
    seed: Optional[int] = None,
    balance_by_difficulty: bool = True
) -> List[Dict[str, Any]]:
    """Select random questions from examples, optionally balanced by difficulty."""
    if seed is not None:
        random.seed(seed)
        logger.info("Using random seed: {}", seed)
    
    if count > len(examples):
        logger.warning(
            "Requested {} questions but only {} available. Using all {} questions.",
            count, len(examples), len(examples)
        )
        count = len(examples)
    
    # Try to balance by difficulty if requested and field exists
    if balance_by_difficulty:
        grouped = group_by_difficulty(examples)
        if grouped:
            # Calculate target count per difficulty (30% each, with remainder distributed)
            difficulty_levels = sorted(grouped.keys())
            per_level_count = count // len(difficulty_levels)
            remainder = count % len(difficulty_levels)
            
            selected = []
            for i, difficulty in enumerate(difficulty_levels):
                available = grouped[difficulty]
                # Add 1 extra question to first 'remainder' levels to handle uneven division
                target = per_level_count + (1 if i < remainder else 0)
                
                if target > len(available):
                    logger.warning(
                        "Difficulty '{}' has only {} questions, but {} requested. Using all {}.",
                        difficulty, len(available), target, len(available)
                    )
                    target = len(available)
                
                if target > 0:
                    level_selected = random.sample(available, target)
                    selected.extend(level_selected)
                    logger.info(
                        "Selected {} questions from difficulty '{}' (target: {})",
                        len(level_selected), difficulty, target
                    )
            
            # If we didn't get enough questions, fill remainder randomly from all examples
            if len(selected) < count:
                remaining_needed = count - len(selected)
                remaining_examples = [ex for ex in examples if ex not in selected]
                if remaining_examples:
                    additional = random.sample(remaining_examples, min(remaining_needed, len(remaining_examples)))
                    selected.extend(additional)
                    logger.info("Added {} additional questions to reach target count", len(additional))
            
            # Shuffle to mix difficulty levels
            random.shuffle(selected)
            logger.info("Selected {} questions balanced by difficulty", len(selected))
            return selected
    
    # Fallback to simple random selection
    selected = random.sample(examples, count)
    logger.info("Selected {} random questions", len(selected))
    return selected


def format_questions(selected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format questions for pipeline processing."""
    formatted = []
    for idx, example in enumerate(selected):
        formatted.append({
            "index": idx,
            "original_index": selected.index(example) if example in selected else None,
            "db_id": example.get("db_id"),
            "question": example.get("question"),
            "gold_sql": example.get("query"),  # "query" field contains the gold SQL
            "question_toks": example.get("question_toks", []),
            # Include difficulty if available
            "difficulty": example.get("hardness") or example.get("difficulty"),
        })
    return formatted


def save_questions(questions: List[Dict[str, Any]], output_path: Path) -> None:
    """Save questions to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "total_count": len(questions),
        "questions_list": questions
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logger.success("Saved {} questions to {}", len(questions), output_path)
    except Exception as e:
        logger.error("Failed to save questions: {}", e)
        raise


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch random questions from Spider 1.0 dev dataset"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of questions to select (default: 3)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible selection"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default="questions_to_process.json",
        help="Output file name (relative to project_dir/data/sot/)"
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default="projects/ensemble",
        help="Project directory path (default: projects/ensemble)"
    )
    
    args = parser.parse_args()
    
    try:
        # Use provided project directory
        project_dir = Path(args.project_dir).resolve()
        if not project_dir.exists():
            logger.error("Project directory does not exist: {}", project_dir)
            raise FileNotFoundError(f"Project directory does not exist: {project_dir}")
        
        logger.info("Project directory: {}", project_dir)
        
        # Paths
        sot_data_dir = project_dir / "data" / "sot" 
        spider_data_dir = project_dir / "data" / "sot" / "spider_data"
        dev_json_path = spider_data_dir / "dev.json"
        output_path = sot_data_dir / args.output_file
        
        # Load dev data
        logger.info("Loading dev.json from {}", dev_json_path)
        examples = load_dev_data(dev_json_path)
        
        # Select random questions (balanced by difficulty by default)
        selected = select_random_questions(examples, args.count, args.seed, balance_by_difficulty=True)
        
        # Format questions
        formatted = format_questions(selected)
        
        # Save to file
        save_questions(formatted, output_path)
        
        # Print summary
        print("\n" + "=" * 70)
        print("Question Selection Summary")
        print("=" * 70)
        print(f"Total examples in dev.json: {len(examples)}")
        print(f"Questions selected: {len(formatted)}")
        print(f"Output file: {output_path}")
        print(f"Unique databases: {len(set(q['db_id'] for q in formatted))}")
        
        # Show difficulty distribution if available
        difficulty_counts = {}
        for q in formatted:
            diff = q.get("difficulty")
            if diff:
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        if difficulty_counts:
            print(f"Difficulty distribution:")
            for diff, count in sorted(difficulty_counts.items()):
                pct = (count / len(formatted)) * 100
                print(f"  {diff}: {count} ({pct:.1f}%)")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n⚠ Selection interrupted by user")
        return 1
    except Exception as e:
        logger.error("Selection failed: {}", e)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

