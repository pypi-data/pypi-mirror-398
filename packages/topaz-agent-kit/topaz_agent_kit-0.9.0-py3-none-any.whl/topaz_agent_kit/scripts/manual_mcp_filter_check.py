import asyncio
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

from topaz_agent_kit.core.configuration_engine import ConfigurationEngine
from topaz_agent_kit.agents.agent_factory import AgentFactory
from topaz_agent_kit.agents.base import (
    AgnoBaseAgent,
    LangGraphBaseAgent,
    CrewAIBaseAgent,
    ADKBaseAgent,
    SKBaseAgent,
    OAKBaseAgent,
    MAFBaseAgent,
)


PROJECT_DIR = Path("/Users/Nishoo/Developer/topaz-agent-kit/projects/ensemble")
AGENT_ID = "rag_query"


FRAMEWORKS: List[tuple[str, Any]] = [
    ("agno", AgnoBaseAgent),            # Working
    ("langgraph", LangGraphBaseAgent),  # Working
    ("crewai", CrewAIBaseAgent),        # Working
    ("adk", ADKBaseAgent),              # Working
    ("sk", SKBaseAgent),                # Working
    ("oak", OAKBaseAgent),              # Working
    ("maf", MAFBaseAgent),              # Working
]


TEST_CASES: List[Dict[str, Any]] = [
    {
        "name": "all_tools",
        "tools": ["*"],
        "expected_count": 74,  # All tools from MCP server
    },
    {
        "name": "doc_rag_only",
        "tools": ["doc_rag.*"],
        "expected_count": 2,  # doc_rag_list_documents, doc_rag_query_document
    },
    {
        "name": "doc_rag_and_math_only",
        "tools": ["doc_rag.*", "math.*"],
        "expected_count": 20,  # 2 doc_rag + 18 math tools
    },
    {
        "name": "math_few_tools_only",
        "tools": ["math_evaluate_expression", "math_sanitize_expression"],
        "expected_count": 2,
    },
    {
        "name": "math_and_dog_rag_few_tools_only",
        "tools": ["math_evaluate_expression", "math_sanitize_expression", "doc_rag_list_documents"],
        "expected_count": 3,  # 2 math + 1 doc_rag
    },
    {
        "name": "math_all_tools_and_doc_rag_few_tools_only",
        "tools": ["math.*", "doc_rag_list_documents"],
        "expected_count": 19,  # 18 math + 1 doc_rag
    },
    {
        "name": "no_match",
        "tools": ["nonexistent_*"],
        "expected_count": 0,  # No tools should match
    },
]


async def _extract_tool_names(agent) -> List[str]:
    # CrewAI stores filtered individual tools separately when using native wrapper
    if hasattr(agent, "_filtered_individual_tools") and getattr(agent, "_filtered_individual_tools") is not None:
        items = getattr(agent, "_filtered_individual_tools")
        names = []
        for t in items:
            if hasattr(t, "name") and isinstance(getattr(t, "name"), str):
                names.append(t.name)
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # Agno: tools are wrapper objects with functions dict
    if agent.framework_type == "agno":
        items = getattr(agent, "tools", []) or []
        names = []
        for t in items:
            # Agno MCPTools wrapper has .functions dict containing actual tool functions
            if hasattr(t, "functions") and isinstance(t.functions, dict):
                names.extend(list(t.functions.keys()))
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # ADK: tools are McpToolset wrapper objects, need to call get_tools() to get filtered tools
    if agent.framework_type == "adk":
        items = getattr(agent, "tools", []) or []
        names = []
        for t in items:
            if hasattr(t, "get_tools") and callable(t.get_tools):
                try:
                    # get_tools() is async and applies tool_filter automatically
                    tools_list = await t.get_tools()
                    if tools_list:
                        for tool_item in tools_list:
                            if hasattr(tool_item, 'name'):
                                names.append(tool_item.name)
                            elif hasattr(tool_item, '__name__'):
                                names.append(tool_item.__name__)
                            else:
                                names.append(str(tool_item))
                except Exception:
                    # If get_tools fails, fallback to type name
                    names.append(type(t).__name__)
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # SK, OAK, MAF: use stored filtered tool names from _filter_mcp_tools
    if agent.framework_type in ["sk", "oak", "maf"]:
        items = getattr(agent, "tools", []) or []
        names = []
        for t in items:
            tool_id = id(t)
            if hasattr(agent, "_filtered_mcp_tool_names") and tool_id in agent._filtered_mcp_tool_names:
                # Use stored filtered tool names
                names.extend(agent._filtered_mcp_tool_names[tool_id])
            elif isinstance(t, dict) and 'name' in t:
                names.append(t['name'])
            elif hasattr(t, 'name'):
                names.append(t.name)
            else:
                names.append(type(t).__name__)
        return sorted(set(names))

    # Default path: agent.tools after filtering (LangGraph)
    items = getattr(agent, "tools", []) or []
    names = []
    for t in items:
        if hasattr(t, "name") and isinstance(getattr(t, "name"), str):
            names.append(t.name)
        else:
            names.append(type(t).__name__)
    return sorted(set(names))


async def _init_mcp_only(agent) -> None:
    # Minimal context with project_dir so prompt loader paths resolve if needed downstream
    context = {"project_dir": str(PROJECT_DIR)}
    # Directly initialize MCP tools (skip LLM and full initialize)
    await agent._initialize_mcp_tools(context)


async def run_case(framework_key: str, framework_cls: Any, base_agent_config: Dict[str, Any], tools_patterns: List[str]) -> List[str]:
    agent_config = deepcopy(base_agent_config)
    agent_config["type"] = framework_key

    # Apply tool filter patterns to each configured server
    mcp = agent_config.get("mcp", {})
    servers = mcp.get("servers", [])
    for server in servers:
        server["tools"] = tools_patterns

    # Create a minimal concrete subclass to satisfy abstract methods
    def make_concrete(cls):
        class Concrete(cls):
            # def _log_tool_details(self) -> None:
            #     return None
            # def _setup_environment(self):
            #     return None
            # def _create_agent(self):
            #     return None
            def get_agent_variables(self, context: Dict[str, Any]) -> Dict[str, Any]:
                return {}
            # def _execute_agent(self, *args, **kwargs):
            #     return {}
            # def _initialize_agent(self):
            #     return None
        return Concrete

    ConcreteAgent = make_concrete(framework_cls)
    agent = ConcreteAgent(AGENT_ID, agent_config=agent_config)

    # Initialize MCP tools only
    await _init_mcp_only(agent)

    # Extract filtered tool names (async for ADK)
    names = await _extract_tool_names(agent)

    # Cleanup resources
    await agent.cleanup()

    return names


async def main() -> None:
    print("Loading configuration...")
    engine = ConfigurationEngine(PROJECT_DIR)
    config_result = engine.load_and_validate()
    if not config_result.is_valid:
        print("Config invalid:")
        for e in config_result.errors:
            print(f"  - {e}")
        raise SystemExit(1)

    factory = AgentFactory(config_result)
    base_agent_config = factory.get_agent_config(AGENT_ID)
    if not base_agent_config:
        print(f"Agent config not found for id '{AGENT_ID}'")
        raise SystemExit(1)

    total_failures = 0
    # Store results for summary: {framework: {test_case: {"status": "PASS"/"FAIL", "count": int, "expected": int}}}
    results_summary: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for framework_key, framework_cls in FRAMEWORKS:
        print(f"\n=== Framework: {framework_key} ===")
        results_summary[framework_key] = {}

        # Run baseline first to get all tools reference
        all_tools_case = TEST_CASES[0]
        all_names = await run_case(framework_key, framework_cls, base_agent_config, all_tools_case["tools"])
        all_count = len(all_names)
        expected_all = all_tools_case.get("expected_count")
        if expected_all is not None:
            all_ok = all_count == expected_all
            status = "PASS" if all_ok else "FAIL"
            if not all_ok:
                total_failures += 1
            print(f"{all_tools_case['name']}: count={all_count} (expected={expected_all}) [{status}]")
            results_summary[framework_key][all_tools_case['name']] = {
                "status": status,
                "count": all_count,
                "expected": expected_all
            }
        else:
            print(f"{all_tools_case['name']}: count={all_count}")
            results_summary[framework_key][all_tools_case['name']] = {
                "status": "INFO",
                "count": all_count,
                "expected": None
            }

        # Run all other test cases
        for case in TEST_CASES[1:]:
            case_names = await run_case(framework_key, framework_cls, base_agent_config, case["tools"])
            case_count = len(case_names)
            expected_count = case.get("expected_count")
            
            # Validate count and subset relationship
            count_ok = True
            subset_ok = True
            
            if expected_count is not None:
                count_ok = case_count == expected_count
            
            # Verify subset relationship (except for no_match which should be 0)
            if case["name"] != "no_match":
                subset_ok = set(case_names).issubset(set(all_names))
            
            # Overall status
            overall_ok = count_ok and subset_ok
            status = "PASS" if overall_ok else "FAIL"
            
            if not overall_ok:
                total_failures += 1
                details = []
                if not count_ok:
                    details.append(f"count={case_count} expected={expected_count}")
                if not subset_ok:
                    unexpected = sorted(set(case_names) - set(all_names))
                    details.append(f"unexpected_tools={unexpected}")
                detail_str = f" ({', '.join(details)})" if details else ""
                print(f"{case['name']}: count={case_count} [{status}]{detail_str}")
            else:
                expected_str = f" (expected={expected_count})" if expected_count is not None else ""
                print(f"{case['name']}: count={case_count}{expected_str} [{status}]")
            
            results_summary[framework_key][case['name']] = {
                "status": status,
                "count": case_count,
                "expected": expected_count
            }

    # Print summary table
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    # Get all test case names
    test_case_names = [case["name"] for case in TEST_CASES]
    
    # Print header
    header = f"{'Framework':<15}"
    for test_name in test_case_names:
        # Truncate long names for display
        display_name = test_name[:20] if len(test_name) > 20 else test_name
        header += f"{display_name:>25}"
    print(header)
    print("-" * 80)
    
    # Print results for each framework
    for framework_key in sorted(results_summary.keys()):
        row = f"{framework_key:<15}"
        for test_name in test_case_names:
            if test_name in results_summary[framework_key]:
                result = results_summary[framework_key][test_name]
                status = result["status"]
                count = result["count"]
                expected = result["expected"]
                
                if status == "PASS":
                    status_symbol = "✓"
                    color_start = ""
                    color_end = ""
                elif status == "FAIL":
                    status_symbol = "✗"
                    color_start = ""
                    color_end = ""
                else:
                    status_symbol = "•"
                    color_start = ""
                    color_end = ""
                
                if expected is not None:
                    cell = f"{status_symbol} {count}/{expected}"
                else:
                    cell = f"{status_symbol} {count}"
                
                row += f"{cell:>25}"
            else:
                row += f"{'N/A':>25}"
        print(row)
    
    # Print statistics
    print("-" * 80)
    total_tests = len(FRAMEWORKS) * len(TEST_CASES)
    total_passed = sum(
        1 for framework_results in results_summary.values()
        for result in framework_results.values()
        if result["status"] == "PASS"
    )
    total_failed = sum(
        1 for framework_results in results_summary.values()
        for result in framework_results.values()
        if result["status"] == "FAIL"
    )
    
    print(f"\nTotal: {total_tests} tests | Passed: {total_passed} | Failed: {total_failed}")
    print("=" * 80)

    if total_failures:
        print(f"\nCompleted with {total_failures} failure(s).")
        raise SystemExit(1)
    print("\nAll PASS")


if __name__ == "__main__":
    asyncio.run(main())


