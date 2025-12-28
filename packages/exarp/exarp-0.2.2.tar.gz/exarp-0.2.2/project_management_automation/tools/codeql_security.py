"""
CodeQL Security Integration for Exarp Scorecard.

Checks CodeQL configuration, parses SARIF results, and optionally
fetches security alerts from GitHub API.

[HINT: CodeQL security. Workflow status, SARIF alerts, GitHub security tab integration.]
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from ..utils import find_project_root


def get_codeql_status(project_root: Optional[Path] = None) -> dict[str, Any]:
    """
    Get comprehensive CodeQL security status for the project.

    Returns:
        Dictionary with CodeQL configuration status, alerts, and recommendations.
    """
    if project_root is None:
        project_root = find_project_root()

    result = {
        'configured': False,
        'workflow_exists': False,
        'config_exists': False,
        'languages': [],
        'alerts': {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'source': None,  # 'sarif', 'github_api', or None
        },
        'last_scan': None,
        'sarif_files': [],
        'recommendations': [],
    }

    # Check for CodeQL workflow
    workflow_path = project_root / '.github' / 'workflows' / 'codeql.yml'
    codeql_analysis_path = project_root / '.github' / 'workflows' / 'codeql-analysis.yml'

    if workflow_path.exists():
        result['workflow_exists'] = True
        result['workflow_path'] = str(workflow_path)
        result['languages'] = _parse_codeql_languages(workflow_path)
    elif codeql_analysis_path.exists():
        result['workflow_exists'] = True
        result['workflow_path'] = str(codeql_analysis_path)
        result['languages'] = _parse_codeql_languages(codeql_analysis_path)

    # Check for CodeQL config
    config_paths = [
        project_root / '.github' / 'codeql' / 'codeql-config.yml',
        project_root / '.github' / 'codeql' / 'codeql-config.yaml',
        project_root / 'codeql-config.yml',
    ]
    for config_path in config_paths:
        if config_path.exists():
            result['config_exists'] = True
            result['config_path'] = str(config_path)
            break

    result['configured'] = result['workflow_exists']

    # Try to get alerts from SARIF files (local CodeQL runs)
    sarif_alerts = _parse_sarif_results(project_root)
    if sarif_alerts['total'] > 0:
        result['alerts'] = sarif_alerts
        result['alerts']['source'] = 'sarif'

    # Try GitHub API if token available and no SARIF results
    if sarif_alerts['total'] == 0:
        github_alerts = _fetch_github_security_alerts(project_root)
        if github_alerts:
            result['alerts'] = github_alerts
            result['alerts']['source'] = 'github_api'

    # Generate recommendations
    result['recommendations'] = _generate_recommendations(result)

    return result


def _parse_codeql_languages(workflow_path: Path) -> list[str]:
    """Parse languages from CodeQL workflow file."""
    try:
        content = workflow_path.read_text()
        # Look for language matrix
        lang_match = re.search(r"language:\s*\[([^\]]+)\]", content)
        if lang_match:
            langs = lang_match.group(1)
            return [l.strip().strip("'\"") for l in langs.split(',')]

        # Look for single language
        lang_match = re.search(r"languages:\s*['\"]?(\w+)['\"]?", content)
        if lang_match:
            return [lang_match.group(1)]

        # Check for Python-specific patterns
        if 'python' in content.lower():
            return ['python']
    except Exception:
        pass
    return []


def _parse_sarif_results(project_root: Path) -> dict[str, Any]:
    """
    Parse SARIF (Static Analysis Results Interchange Format) files.

    CodeQL outputs results in SARIF format. Look for:
    - results/*.sarif
    - .github/codeql/*.sarif
    - codeql-results/*.sarif
    """
    alerts = {
        'total': 0,
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0,
        'details': [],
    }

    sarif_locations = [
        project_root / 'results',
        project_root / '.github' / 'codeql',
        project_root / 'codeql-results',
        project_root,
    ]

    sarif_files = []
    for location in sarif_locations:
        if location.exists():
            sarif_files.extend(location.glob('*.sarif'))
            sarif_files.extend(location.glob('*.sarif.json'))

    for sarif_file in sarif_files:
        try:
            with open(sarif_file) as f:
                sarif_data = json.load(f)

            for run in sarif_data.get('runs', []):
                for result in run.get('results', []):
                    alerts['total'] += 1

                    # Map SARIF severity to our categories
                    level = result.get('level', 'warning')
                    severity = _map_sarif_severity(level, result)
                    alerts[severity] += 1

                    # Store alert details (limited)
                    if len(alerts['details']) < 20:
                        alerts['details'].append({
                            'rule_id': result.get('ruleId', 'unknown'),
                            'message': result.get('message', {}).get('text', '')[:200],
                            'severity': severity,
                            'location': _get_sarif_location(result),
                        })
        except Exception:
            continue

    return alerts


def _map_sarif_severity(level: str, result: dict) -> str:
    """Map SARIF level to severity category."""
    # Check for security-severity in rule properties
    properties = result.get('properties', {})
    security_severity = properties.get('security-severity', '')

    if security_severity:
        try:
            score = float(security_severity)
            if score >= 9.0:
                return 'critical'
            elif score >= 7.0:
                return 'high'
            elif score >= 4.0:
                return 'medium'
            else:
                return 'low'
        except ValueError:
            pass

    # Fall back to SARIF level
    level_map = {
        'error': 'high',
        'warning': 'medium',
        'note': 'low',
        'none': 'low',
    }
    return level_map.get(level.lower(), 'medium')


def _get_sarif_location(result: dict) -> str:
    """Extract location from SARIF result."""
    locations = result.get('locations', [])
    if locations:
        physical = locations[0].get('physicalLocation', {})
        artifact = physical.get('artifactLocation', {})
        uri = artifact.get('uri', '')
        region = physical.get('region', {})
        line = region.get('startLine', 0)
        if uri and line:
            return f"{uri}:{line}"
        return uri
    return ''


def _fetch_github_security_alerts(project_root: Path) -> Optional[dict[str, Any]]:
    """
    Fetch security alerts from GitHub API.

    Requires GITHUB_TOKEN environment variable with repo scope.
    """
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        return None

    # Try to get repo info from git remote
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=5
        )
        if result.returncode != 0:
            return None

        remote_url = result.stdout.strip()

        # Parse owner/repo from URL
        match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', remote_url)
        if not match:
            return None

        owner, repo = match.groups()
        repo = repo.replace('.git', '')

        # Fetch code scanning alerts
        import urllib.error
        import urllib.request

        url = f"https://api.github.com/repos/{owner}/{repo}/code-scanning/alerts?state=open"
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {github_token}')
        req.add_header('Accept', 'application/vnd.github+json')
        req.add_header('X-GitHub-Api-Version', '2022-11-28')

        with urllib.request.urlopen(req, timeout=10) as response:
            alerts_data = json.loads(response.read().decode())

        alerts = {
            'total': len(alerts_data),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'details': [],
        }

        for alert in alerts_data:
            severity = alert.get('rule', {}).get('security_severity_level', 'medium')
            severity = severity.lower() if severity else 'medium'

            if severity in ['critical']:
                alerts['critical'] += 1
            elif severity in ['high']:
                alerts['high'] += 1
            elif severity in ['medium']:
                alerts['medium'] += 1
            else:
                alerts['low'] += 1

            if len(alerts['details']) < 20:
                alerts['details'].append({
                    'rule_id': alert.get('rule', {}).get('id', 'unknown'),
                    'message': alert.get('rule', {}).get('description', '')[:200],
                    'severity': severity,
                    'location': alert.get('most_recent_instance', {}).get('location', {}).get('path', ''),
                    'html_url': alert.get('html_url', ''),
                })

        return alerts

    except Exception:
        return None


def _generate_recommendations(status: dict) -> list[dict]:
    """Generate recommendations based on CodeQL status."""
    recommendations = []

    if not status['workflow_exists']:
        recommendations.append({
            'priority': 'high',
            'action': 'Enable CodeQL by adding .github/workflows/codeql.yml',
            'impact': 'Automated security vulnerability detection',
        })

    if status['workflow_exists'] and not status['config_exists']:
        recommendations.append({
            'priority': 'low',
            'action': 'Add .github/codeql/codeql-config.yml for custom query configuration',
            'impact': 'Fine-tune security scanning scope and rules',
        })

    alerts = status['alerts']
    if alerts['critical'] > 0:
        recommendations.append({
            'priority': 'critical',
            'action': f"Fix {alerts['critical']} critical security vulnerabilities immediately",
            'impact': 'Prevent potential security breaches',
        })

    if alerts['high'] > 0:
        recommendations.append({
            'priority': 'high',
            'action': f"Address {alerts['high']} high-severity security issues",
            'impact': 'Reduce attack surface significantly',
        })

    if not status['languages']:
        recommendations.append({
            'priority': 'medium',
            'action': 'Verify CodeQL is configured for project languages',
            'impact': 'Ensure comprehensive code analysis',
        })

    return recommendations


def calculate_codeql_score(status: dict) -> float:
    """
    Calculate a security score based on CodeQL status.

    Scoring:
    - Workflow exists: 40 points base
    - Config exists: +10 points
    - No critical alerts: +25 points (or -25 per critical)
    - No high alerts: +15 points (or -10 per high)
    - No medium alerts: +10 points (or -2 per medium)

    Returns: Score from 0-100
    """
    score = 0.0

    # Base score for having CodeQL configured
    if status['workflow_exists']:
        score += 40

    if status['config_exists']:
        score += 10

    alerts = status['alerts']

    # Deduct for alerts (cap deductions)
    if alerts['critical'] == 0:
        score += 25
    else:
        score -= min(25, alerts['critical'] * 25)

    if alerts['high'] == 0:
        score += 15
    else:
        score -= min(15, alerts['high'] * 10)

    if alerts['medium'] == 0:
        score += 10
    else:
        score -= min(10, alerts['medium'] * 2)

    # Ensure score is in valid range
    return max(0, min(100, score))


# Convenience function for scorecard integration
def get_codeql_security_metrics() -> dict[str, Any]:
    """
    Get CodeQL metrics formatted for scorecard integration.

    Returns dict with:
    - score: 0-100 CodeQL security score
    - checks: dict of boolean checks for scorecard
    - alerts: alert counts by severity
    - configured: whether CodeQL is set up
    """
    status = get_codeql_status()
    score = calculate_codeql_score(status)

    return {
        'score': score,
        'configured': status['configured'],
        'checks': {
            'codeql_workflow': status['workflow_exists'],
            'codeql_config': status['config_exists'],
            'no_critical_alerts': status['alerts']['critical'] == 0,
            'no_high_alerts': status['alerts']['high'] == 0,
        },
        'alerts': {
            'total': status['alerts']['total'],
            'critical': status['alerts']['critical'],
            'high': status['alerts']['high'],
            'medium': status['alerts']['medium'],
            'low': status['alerts']['low'],
            'source': status['alerts']['source'],
        },
        'languages': status['languages'],
        'recommendations': status['recommendations'],
    }

