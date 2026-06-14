"""Quality-augmented SkillSpector graph.

Rebuilds the upstream pipeline by importing its nodes and analyzer registry read-only,
and inserts a ``quality_scorer`` node that runs in parallel with the security analyzers.
The upstream ``report`` node is reused verbatim for the security report; ``quality_report``
simply rides along in the final state for the CLI to render.

Importing ``ANALYZER_NODE_IDS`` means new upstream analyzers are picked up automatically on
the next upstream sync — no change needed here.
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from skillspector.nodes.analyzers import ANALYZER_NODE_IDS, ANALYZER_NODES
from skillspector.nodes.build_context import build_context
from skillspector.nodes.meta_analyzer import meta_analyzer
from skillspector.nodes.report import report
from skillspector.nodes.resolve_input import resolve_input

from skillspector_quality.nodes.quality_scorer import quality_scorer
from skillspector_quality.state import QualityState


def build_graph() -> CompiledStateGraph[Any, Any, Any]:
    """Create and compile the quality-augmented workflow graph."""
    workflow = StateGraph(QualityState)

    workflow.add_node("resolve_input", resolve_input)
    workflow.add_node("build_context", build_context)
    workflow.add_node("meta_analyzer", meta_analyzer)
    workflow.add_node("report", report)
    workflow.add_node("quality_scorer", quality_scorer)

    for analyzer_id in ANALYZER_NODE_IDS:
        workflow.add_node(analyzer_id, ANALYZER_NODES[analyzer_id])

    workflow.add_edge(START, "resolve_input")
    workflow.add_edge("resolve_input", "build_context")
    for analyzer_id in ANALYZER_NODE_IDS:
        workflow.add_edge("build_context", analyzer_id)
        workflow.add_edge(analyzer_id, "meta_analyzer")

    # Quality runs off the same build_context, in parallel with the analyzers, and
    # terminates at END independently. We deliberately do NOT make `report` depend on
    # quality_scorer: giving `report` a second predecessor in a different superstep makes
    # LangGraph trigger it twice and double-write the `filtered_findings` channel. Keeping
    # `report`'s single upstream (meta_analyzer) leaves the security path byte-identical to
    # upstream; `quality_report` simply rides along in the final state.
    workflow.add_edge("build_context", "quality_scorer")
    workflow.add_edge("quality_scorer", END)

    workflow.add_edge("meta_analyzer", "report")
    workflow.add_edge("report", END)

    return workflow.compile()


graph = build_graph()
