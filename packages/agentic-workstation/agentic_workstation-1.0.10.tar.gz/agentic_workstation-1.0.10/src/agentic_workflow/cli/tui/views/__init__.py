"""
View components for data presentation.

This package contains view classes that handle formatting and
displaying data to the user.
"""

from .base_views import BaseView
from .project_views import ProjectListView, ProjectStatusView, ProjectSummaryView
from .system_views import SystemInfoView
from .dashboard_view import DashboardView
from .artifact_view import ArtifactListView, ArtifactContentView
from .error_view import ErrorView

__all__ = [
    'BaseView',
    'ProjectListView',
    'ProjectStatusView',
    'ProjectSummaryView',
    'SystemInfoView',
    'ErrorView'
]