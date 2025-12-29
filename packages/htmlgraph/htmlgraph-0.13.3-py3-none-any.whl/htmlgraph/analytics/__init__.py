"""
Analytics modules for HtmlGraph.

Provides work type analysis, dependency analytics, and CLI analytics.
"""

from htmlgraph.analytics.work_type import Analytics
from htmlgraph.analytics.dependency import DependencyAnalytics

__all__ = [
    "Analytics",
    "DependencyAnalytics",
]
