"""
Compliance Reporting

Generates compliance reports for various standards (SOC2, GDPR, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import json


class ReportType(Enum):
    """Types of compliance reports"""

    # Security compliance
    SOC2_TYPE_I = "soc2_type_i"
    SOC2_TYPE_II = "soc2_type_ii"
    ISO27001 = "iso27001"

    # Privacy compliance
    GDPR = "gdpr"
    CCPA = "ccpa"
    PIPEDA = "pipeda"

    # Industry specific
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    FERPA = "ferpa"

    # Internal reports
    SECURITY_SUMMARY = "security_summary"
    ACCESS_REPORT = "access_report"
    AUDIT_SUMMARY = "audit_summary"


@dataclass
class ReportMetrics:
    """Metrics included in compliance reports"""

    total_users: int = 0
    active_users_30d: int = 0
    failed_logins_30d: int = 0
    data_access_events_30d: int = 0
    security_incidents_30d: int = 0
    policy_violations_30d: int = 0
    data_retention_compliance: float = 0.0  # Percentage
    encryption_coverage: float = 0.0  # Percentage
    backup_success_rate: float = 0.0  # Percentage


@dataclass
class ComplianceReport:
    """Represents a compliance report"""

    report_type: ReportType
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    metrics: ReportMetrics
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    compliance_score: float  # 0.0 to 1.0
    status: str  # "compliant", "non_compliant", "partial"

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary"""
        return {
            "report_type": self.report_type.value,
            "generated_at": self.generated_at.isoformat(),
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "metrics": self.metrics.__dict__,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "compliance_score": self.compliance_score,
            "status": self.status
        }


class ComplianceReporter(ABC):
    """
    Abstract base class for compliance reporting.

    This interface allows OSS core to generate compliance reports
    without depending on enterprise implementation details.
    """

    @abstractmethod
    async def generate_report(
        self,
        report_type: ReportType,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """Generate compliance report for specified period"""
        pass

    @abstractmethod
    async def get_available_reports(self) -> List[ReportType]:
        """Get list of available report types"""
        pass

    @abstractmethod
    async def schedule_report(
        self,
        report_type: ReportType,
        frequency: str,  # daily, weekly, monthly, quarterly
        recipients: List[str]
    ) -> bool:
        """Schedule automated report generation"""
        pass


class DefaultComplianceReporter(ComplianceReporter):
    """
    Default compliance reporter implementation
    """

    def __init__(self, audit_logger=None, data_source=None):
        self.audit_logger = audit_logger
        self.data_source = data_source
        self.scheduled_reports: List[Dict[str, Any]] = []

    async def generate_report(
        self,
        report_type: ReportType,
        start_date: datetime,
        end_date: datetime
    ) -> ComplianceReport:
        """Generate compliance report for specified period"""

        # Collect metrics for the period
        metrics = await self._collect_metrics(start_date, end_date)

        # Generate findings based on report type
        findings = await self._generate_findings(report_type, metrics)

        # Generate recommendations
        recommendations = self._generate_recommendations(report_type, findings)

        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(report_type, metrics, findings)

        # Determine status
        status = self._determine_status(compliance_score)

        return ComplianceReport(
            report_type=report_type,
            generated_at=datetime.utcnow(),
            period_start=start_date,
            period_end=end_date,
            metrics=metrics,
            findings=findings,
            recommendations=recommendations,
            compliance_score=compliance_score,
            status=status
        )

    async def get_available_reports(self) -> List[ReportType]:
        """Get list of available report types"""
        return [
            ReportType.SOC2_TYPE_I,
            ReportType.SOC2_TYPE_II,
            ReportType.GDPR,
            ReportType.SECURITY_SUMMARY,
            ReportType.ACCESS_REPORT,
            ReportType.AUDIT_SUMMARY
        ]

    async def schedule_report(
        self,
        report_type: ReportType,
        frequency: str,
        recipients: List[str]
    ) -> bool:
        """Schedule automated report generation"""
        schedule = {
            "report_type": report_type,
            "frequency": frequency,
            "recipients": recipients,
            "created_at": datetime.utcnow(),
            "next_run": self._calculate_next_run(frequency)
        }
        self.scheduled_reports.append(schedule)
        return True

    async def _collect_metrics(self, start_date: datetime, end_date: datetime) -> ReportMetrics:
        """Collect metrics for the reporting period"""
        # In production, this would query actual data sources
        # For now, return sample metrics

        return ReportMetrics(
            total_users=150,
            active_users_30d=120,
            failed_logins_30d=5,
            data_access_events_30d=1250,
            security_incidents_30d=0,
            policy_violations_30d=2,
            data_retention_compliance=98.5,
            encryption_coverage=100.0,
            backup_success_rate=99.8
        )

    async def _generate_findings(self, report_type: ReportType, metrics: ReportMetrics) -> List[Dict[str, Any]]:
        """Generate findings based on report type and metrics"""
        findings = []

        if report_type in [ReportType.SOC2_TYPE_I, ReportType.SOC2_TYPE_II]:
            # SOC2 specific findings
            if metrics.failed_logins_30d > 10:
                findings.append({
                    "category": "Security",
                    "severity": "Medium",
                    "description": f"High number of failed login attempts: {metrics.failed_logins_30d}",
                    "control": "CC6.1 - Logical and Physical Access Controls"
                })

            if metrics.backup_success_rate < 99.0:
                findings.append({
                    "category": "Availability",
                    "severity": "High",
                    "description": f"Backup success rate below threshold: {metrics.backup_success_rate}%",
                    "control": "CC7.1 - System Monitoring"
                })

        elif report_type == ReportType.GDPR:
            # GDPR specific findings
            if metrics.data_retention_compliance < 95.0:
                findings.append({
                    "category": "Data Protection",
                    "severity": "High",
                    "description": f"Data retention compliance below requirement: {metrics.data_retention_compliance}%",
                    "article": "Article 5(1)(e) - Storage limitation"
                })

        return findings

    def _generate_recommendations(self, report_type: ReportType, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []

        for finding in findings:
            if "failed login" in finding["description"].lower():
                recommendations.append("Implement account lockout policy after multiple failed attempts")
                recommendations.append("Enable multi-factor authentication for all users")

            if "backup" in finding["description"].lower():
                recommendations.append("Review and enhance backup monitoring procedures")
                recommendations.append("Implement automated backup failure alerts")

            if "data retention" in finding["description"].lower():
                recommendations.append("Implement automated data retention policies")
                recommendations.append("Conduct regular data retention compliance audits")

        return recommendations

    def _calculate_compliance_score(
        self,
        report_type: ReportType,
        metrics: ReportMetrics,
        findings: List[Dict[str, Any]]
    ) -> float:
        """Calculate overall compliance score"""
        base_score = 1.0

        # Deduct points for findings
        for finding in findings:
            severity = finding.get("severity", "Low")
            if severity == "High":
                base_score -= 0.1
            elif severity == "Medium":
                base_score -= 0.05
            elif severity == "Low":
                base_score -= 0.02

        # Adjust based on metrics
        if metrics.encryption_coverage < 100.0:
            base_score -= 0.05

        if metrics.data_retention_compliance < 95.0:
            base_score -= 0.1

        return max(0.0, base_score)

    def _determine_status(self, compliance_score: float) -> str:
        """Determine compliance status based on score"""
        if compliance_score >= 0.95:
            return "compliant"
        elif compliance_score >= 0.80:
            return "partial"
        else:
            return "non_compliant"

    def _calculate_next_run(self, frequency: str) -> datetime:
        """Calculate next report run time"""
        now = datetime.utcnow()
        if frequency == "daily":
            return now + timedelta(days=1)
        elif frequency == "weekly":
            return now + timedelta(weeks=1)
        elif frequency == "monthly":
            return now + timedelta(days=30)
        elif frequency == "quarterly":
            return now + timedelta(days=90)
        else:
            return now + timedelta(days=1)


# Factory function for OSS integration
def create_compliance_reporter(config: Optional[Dict[str, Any]] = None) -> ComplianceReporter:
    """
    Factory function to create compliance reporter.

    This function can be called by OSS core to get a compliance reporter
    without importing enterprise-specific classes.
    """
    return DefaultComplianceReporter()