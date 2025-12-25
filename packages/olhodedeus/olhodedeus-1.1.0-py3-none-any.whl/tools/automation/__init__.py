#!/usr/bin/env python3
"""
Automation Tools - Ferramentas de automação
Parte do toolkit Olho de Deus
"""

from .report_generator import (
    ReportGenerator,
    Finding,
    ReportMetadata,
    MarkdownReportGenerator,
    HTMLReportGenerator,
    JSONReportGenerator,
    interactive_menu as report_generator_menu
)

from .recon_automation import (
    ReconAutomation,
    ReconTask,
    ReconPipeline,
    ReconModules,
    interactive_menu as recon_automation_menu
)

from .credential_manager import (
    CredentialStore,
    Credential,
    PasswordGenerator,
    SimpleCrypto,
    interactive_menu as credential_manager_menu
)

from .scheduler import (
    TaskScheduler,
    ScheduledTask,
    TaskResult,
    TaskExecutor,
    TaskStore,
    interactive_menu as scheduler_menu
)

from .dashboard import (
    Dashboard,
    SystemCollector,
    SecurityChecker,
    SecurityMetric,
    ActivityLogger,
    interactive_menu as dashboard_menu
)

__all__ = [
    # Report Generator
    'ReportGenerator',
    'Finding',
    'ReportMetadata',
    'MarkdownReportGenerator',
    'HTMLReportGenerator',
    'JSONReportGenerator',
    'report_generator_menu',
    
    # Recon Automation
    'ReconAutomation',
    'ReconTask',
    'ReconPipeline',
    'ReconModules',
    'recon_automation_menu',
    
    # Credential Manager
    'CredentialStore',
    'Credential',
    'PasswordGenerator',
    'SimpleCrypto',
    'credential_manager_menu',
    
    # Scheduler
    'TaskScheduler',
    'ScheduledTask',
    'TaskResult',
    'TaskExecutor',
    'TaskStore',
    'scheduler_menu',
    
    # Dashboard
    'Dashboard',
    'SystemCollector',
    'SecurityChecker',
    'SecurityMetric',
    'ActivityLogger',
    'dashboard_menu',
]
