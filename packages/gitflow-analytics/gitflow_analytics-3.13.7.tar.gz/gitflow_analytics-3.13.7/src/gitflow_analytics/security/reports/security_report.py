"""Generate security analysis reports."""

import json
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from ..security_analyzer import SecurityAnalysis


class SecurityReportGenerator:
    """Generate various format reports for security findings."""

    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize report generator.

        Args:
            output_dir: Directory for report output
        """
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_reports(self, analyses: List[SecurityAnalysis], summary: Dict[str, Any]) -> Dict[str, Path]:
        """Generate all report formats.

        Args:
            analyses: List of security analyses
            summary: Summary statistics

        Returns:
            Dictionary of report type to file path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports = {}

        # Generate Markdown report
        md_path = self.output_dir / f"security_report_{timestamp}.md"
        self._generate_markdown_report(analyses, summary, md_path)
        reports["markdown"] = md_path

        # Generate JSON report
        json_path = self.output_dir / f"security_findings_{timestamp}.json"
        self._generate_json_report(analyses, summary, json_path)
        reports["json"] = json_path

        # Generate CSV report
        csv_path = self.output_dir / f"security_issues_{timestamp}.csv"
        self._generate_csv_report(analyses, csv_path)
        reports["csv"] = csv_path

        # Generate SARIF report if requested
        if any(a.total_findings > 0 for a in analyses):
            sarif_path = self.output_dir / f"security_sarif_{timestamp}.json"
            self._generate_sarif_report(analyses, sarif_path)
            reports["sarif"] = sarif_path

        return reports

    def _generate_markdown_report(self, analyses: List[SecurityAnalysis], summary: Dict, path: Path) -> None:
        """Generate comprehensive Markdown security report."""
        with open(path, 'w') as f:
            # Header
            f.write("# 🔒 Security Analysis Report\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Executive Summary
            f.write("## 📊 Executive Summary\n\n")
            f.write(f"- **Commits Analyzed**: {summary['total_commits']}\n")
            f.write(f"- **Commits with Issues**: {summary['commits_with_issues']}\n")
            f.write(f"- **Total Findings**: {summary['total_findings']}\n")
            f.write(f"- **Risk Level**: **{summary['risk_level']}** (Score: {summary['average_risk_score']})\n\n")

            # Risk Assessment
            self._write_risk_assessment(f, summary)

            # Severity Distribution
            f.write("## 🎯 Severity Distribution\n\n")
            severity = summary['severity_distribution']
            if severity['critical'] > 0:
                f.write(f"- 🔴 **Critical**: {severity['critical']}\n")
            if severity['high'] > 0:
                f.write(f"- 🟠 **High**: {severity['high']}\n")
            if severity['medium'] > 0:
                f.write(f"- 🟡 **Medium**: {severity['medium']}\n")
            if severity['low'] > 0:
                f.write(f"- 🟢 **Low**: {severity['low']}\n")
            f.write("\n")

            # Top Issues
            if summary['top_issues']:
                f.write("## 🔝 Top Security Issues\n\n")
                f.write("| Issue Type | Severity | Occurrences | Affected Files |\n")
                f.write("|------------|----------|-------------|----------------|\n")
                for issue in summary['top_issues']:
                    f.write(f"| {issue['type']} | {issue['severity'].upper()} | "
                           f"{issue['occurrences']} | {issue['affected_files']} |\n")
                f.write("\n")

            # Detailed Findings by Category
            self._write_detailed_findings(f, analyses)

            # LLM Insights
            if 'llm_insights' in summary and summary['llm_insights']:
                f.write("## 🤖 AI Security Insights\n\n")
                f.write(summary['llm_insights'])
                f.write("\n\n")

            # Recommendations
            f.write("## 💡 Recommendations\n\n")
            for rec in summary['recommendations']:
                f.write(f"- {rec}\n")
            f.write("\n")

            # Appendix - All Findings
            f.write("## 📋 Detailed Findings\n\n")
            self._write_all_findings(f, analyses)

    def _write_risk_assessment(self, f, summary: Dict) -> None:
        """Write risk assessment section."""
        risk_level = summary['risk_level']
        score = summary['average_risk_score']

        f.write("## ⚠️ Risk Assessment\n\n")

        if risk_level == "CRITICAL":
            f.write("### 🚨 CRITICAL RISK DETECTED\n\n")
            f.write("Immediate action required. Critical security vulnerabilities have been identified "
                   "that could lead to severe security breaches.\n\n")
        elif risk_level == "HIGH":
            f.write("### 🔴 High Risk\n\n")
            f.write("Significant security issues detected that should be addressed urgently.\n\n")
        elif risk_level == "MEDIUM":
            f.write("### 🟡 Medium Risk\n\n")
            f.write("Moderate security concerns identified that should be addressed in the near term.\n\n")
        else:
            f.write("### 🟢 Low Risk\n\n")
            f.write("Minor security issues detected. Continue with regular security practices.\n\n")

        # Risk score visualization
        f.write("**Risk Score Breakdown**:\n")
        f.write("```\n")
        bar_length = 50
        filled = int(score / 100 * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        f.write(f"[{bar}] {score:.1f}/100\n")
        f.write("```\n\n")

    def _write_detailed_findings(self, f, analyses: List[SecurityAnalysis]) -> None:
        """Write detailed findings by category."""
        # Aggregate findings
        all_secrets = []
        all_vulnerabilities = []
        all_dependencies = []
        all_llm = []

        for analysis in analyses:
            all_secrets.extend(analysis.secrets)
            all_vulnerabilities.extend(analysis.vulnerabilities)
            all_dependencies.extend(analysis.dependency_issues)
            all_llm.extend(analysis.llm_findings)

        # Secrets Section
        if all_secrets:
            f.write("## 🔑 Exposed Secrets\n\n")
            f.write(f"**Total**: {len(all_secrets)} potential secrets detected\n\n")

            # Group by secret type
            by_type = {}
            for secret in all_secrets:
                secret_type = secret.get('secret_type', 'unknown')
                if secret_type not in by_type:
                    by_type[secret_type] = []
                by_type[secret_type].append(secret)

            for secret_type, secrets in sorted(by_type.items()):
                f.write(f"### {secret_type.replace('_', ' ').title()}\n")
                for s in secrets[:5]:  # Show first 5 of each type
                    f.write(f"- **File**: `{s.get('file', 'unknown')}`\n")
                    f.write(f"  - Line: {s.get('line', 'N/A')}\n")
                    f.write(f"  - Pattern: `{s.get('match', 'N/A')}`\n")
                if len(secrets) > 5:
                    f.write(f"  - *... and {len(secrets) - 5} more*\n")
                f.write("\n")

        # Vulnerabilities Section
        if all_vulnerabilities:
            f.write("## 🛡️ Code Vulnerabilities\n\n")
            f.write(f"**Total**: {len(all_vulnerabilities)} vulnerabilities detected\n\n")

            # Group by vulnerability type
            by_type = {}
            for vuln in all_vulnerabilities:
                vuln_type = vuln.get('vulnerability_type', 'unknown')
                if vuln_type not in by_type:
                    by_type[vuln_type] = []
                by_type[vuln_type].append(vuln)

            for vuln_type, vulns in sorted(by_type.items()):
                f.write(f"### {vuln_type.replace('_', ' ').title()}\n")
                for v in vulns[:5]:
                    f.write(f"- **File**: `{v.get('file', 'unknown')}:{v.get('line', 'N/A')}`\n")
                    f.write(f"  - Tool: {v.get('tool', 'N/A')}\n")
                    f.write(f"  - Message: {v.get('message', 'N/A')}\n")
                if len(vulns) > 5:
                    f.write(f"  - *... and {len(vulns) - 5} more*\n")
                f.write("\n")

        # Dependencies Section
        if all_dependencies:
            f.write("## 📦 Vulnerable Dependencies\n\n")
            f.write(f"**Total**: {len(all_dependencies)} vulnerable dependencies\n\n")

            for dep in all_dependencies[:10]:
                f.write(f"- **{dep.get('package', 'unknown')}** @ {dep.get('version', 'unknown')}\n")
                f.write(f"  - File: `{dep.get('file', 'unknown')}`\n")
                if dep.get('cve'):
                    f.write(f"  - CVE: {dep['cve']}\n")
                f.write(f"  - Message: {dep.get('message', 'N/A')}\n")
            if len(all_dependencies) > 10:
                f.write(f"\n*... and {len(all_dependencies) - 10} more vulnerable dependencies*\n")
            f.write("\n")

    def _write_all_findings(self, f, analyses: List[SecurityAnalysis]) -> None:
        """Write all findings in detail."""
        for analysis in analyses:
            if analysis.total_findings == 0:
                continue

            f.write(f"### Commit: `{analysis.commit_hash[:8]}`\n")
            f.write(f"**Time**: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Files Changed**: {len(analysis.files_changed)}\n")
            f.write(f"**Risk Score**: {analysis.risk_score:.1f}\n\n")

            if analysis.secrets:
                f.write("**Secrets**:\n")
                for s in analysis.secrets:
                    f.write(f"- {s.get('secret_type', 'unknown')}: {s.get('file', 'N/A')}\n")

            if analysis.vulnerabilities:
                f.write("**Vulnerabilities**:\n")
                for v in analysis.vulnerabilities:
                    f.write(f"- {v.get('vulnerability_type', 'unknown')}: {v.get('file', 'N/A')}\n")

            f.write("\n---\n\n")

    def _generate_json_report(self, analyses: List[SecurityAnalysis], summary: Dict, path: Path) -> None:
        """Generate JSON report with all findings."""
        report = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "summary": summary,
            "analyses": []
        }

        for analysis in analyses:
            report["analyses"].append({
                "commit_hash": analysis.commit_hash,
                "timestamp": analysis.timestamp.isoformat(),
                "files_changed": analysis.files_changed,
                "risk_score": analysis.risk_score,
                "findings": {
                    "secrets": analysis.secrets,
                    "vulnerabilities": analysis.vulnerabilities,
                    "dependency_issues": analysis.dependency_issues,
                    "llm_findings": analysis.llm_findings
                },
                "metrics": {
                    "total": analysis.total_findings,
                    "critical": analysis.critical_count,
                    "high": analysis.high_count,
                    "medium": analysis.medium_count,
                    "low": analysis.low_count
                }
            })

        with open(path, 'w') as f:
            json.dump(report, f, indent=2)

    def _generate_csv_report(self, analyses: List[SecurityAnalysis], path: Path) -> None:
        """Generate CSV report of all findings."""
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'commit_hash', 'timestamp', 'type', 'severity',
                'category', 'file', 'line', 'message', 'tool', 'confidence'
            ])
            writer.writeheader()

            for analysis in analyses:
                # Write all findings
                for finding in (analysis.secrets + analysis.vulnerabilities +
                              analysis.dependency_issues + analysis.llm_findings):
                    writer.writerow({
                        'commit_hash': analysis.commit_hash[:8],
                        'timestamp': analysis.timestamp.isoformat(),
                        'type': finding.get('type', 'unknown'),
                        'severity': finding.get('severity', 'medium'),
                        'category': finding.get('vulnerability_type',
                                              finding.get('secret_type', 'unknown')),
                        'file': finding.get('file', ''),
                        'line': finding.get('line', ''),
                        'message': finding.get('message', ''),
                        'tool': finding.get('tool', finding.get('source', '')),
                        'confidence': finding.get('confidence', '')
                    })

    def _generate_sarif_report(self, analyses: List[SecurityAnalysis], path: Path) -> None:
        """Generate SARIF format report for GitHub Security tab integration."""
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "GitFlow Analytics Security",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/yourusername/gitflow-analytics"
                    }
                },
                "results": []
            }]
        }

        for analysis in analyses:
            for finding in (analysis.secrets + analysis.vulnerabilities):
                result = {
                    "ruleId": finding.get('vulnerability_type',
                                        finding.get('secret_type', 'unknown')),
                    "level": self._severity_to_sarif_level(finding.get('severity', 'medium')),
                    "message": {
                        "text": finding.get('message', 'Security issue detected')
                    },
                    "locations": [{
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.get('file', 'unknown')
                            },
                            "region": {
                                "startLine": finding.get('line', 1)
                            }
                        }
                    }]
                }
                sarif["runs"][0]["results"].append(result)

        with open(path, 'w') as f:
            json.dump(sarif, f, indent=2)

    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level."""
        mapping = {
            "critical": "error",
            "high": "error",
            "medium": "warning",
            "low": "note"
        }
        return mapping.get(severity.lower(), "warning")