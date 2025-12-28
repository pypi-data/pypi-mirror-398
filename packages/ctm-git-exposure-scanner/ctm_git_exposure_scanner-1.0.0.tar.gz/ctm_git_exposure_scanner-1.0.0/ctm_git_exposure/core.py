#!/usr/bin/env python3
"""
Git Exposure Scanner - Core Module
Finds and extracts sensitive information from exposed .git directories
"""

import requests
import re
import os
from typing import Tuple, Dict, List, Optional
from urllib.parse import urljoin, urlparse

# =========================
# Theme & Branding
# =========================

class Theme:
    """ANSI Color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'


class Signature:
    """Tool metadata and branding"""
    WEBSITE = "www.cybertechmind.com"
    TOOL_NAME = "Git Exposure Scanner"
    AUTHOR = "Moovendhan V"
    PROFILE = "profile.cybertechmind.com"
    VERSION = "1.0.0"


# =========================
# Scanner Engine
# =========================

class GitExposureScanner:
    """Scanner for exposed .git directories"""
    
    def __init__(self, target_url: str, timeout: int = 10):
        self.target_url = self.normalize_url(target_url)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.findings = {
            'exposed': False,
            'files_found': [],
            'config': None,
            'branches': [],
            'commits': [],
            'sensitive_data': []
        }
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize URL by adding scheme if missing"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url.rstrip('/')
    
    def check_git_exposure(self) -> bool:
        """Check if .git directory is exposed"""
        git_checks = [
            {
                'path': '.git/HEAD',
                'validators': [
                    lambda content: 'ref:' in content or len(content) == 40,  # SHA-1 hash
                    lambda content: not content.strip().startswith('<'),  # Not HTML
                ]
            },
            {
                'path': '.git/config',
                'validators': [
                    lambda content: '[core]' in content or '[remote' in content,
                    lambda content: not content.strip().startswith('<'),  # Not HTML
                    lambda content: 'repositoryformatversion' in content or 'filemode' in content,
                ]
            },
            {
                'path': '.git/index',
                'validators': [
                    lambda content: content.startswith(b'DIRC') if isinstance(content, bytes) else False,
                    lambda content: not (isinstance(content, str) and content.strip().startswith('<')),
                ]
            },
        ]
        
        for check in git_checks:
            url = urljoin(self.target_url, check['path'])
            try:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=False)
                
                # Check status code
                if response.status_code != 200:
                    continue
                
                # Check content-type (git files shouldn't be HTML)
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    continue
                
                # Validate content
                content = response.text if 'text' in content_type else response.content
                
                # Run validators
                is_valid = False
                for validator in check['validators']:
                    try:
                        if validator(content):
                            is_valid = True
                            break
                    except:
                        continue
                
                if is_valid:
                    self.findings['exposed'] = True
                    self.findings['files_found'].append(check['path'])
                    print(f"{Theme.OKGREEN}[+] Found: {check['path']}{Theme.ENDC}")
                    return True
                    
            except requests.RequestException:
                continue
        
        return False
    
    def extract_git_config(self) -> Optional[str]:
        """Extract .git/config file"""
        url = urljoin(self.target_url, '.git/config')
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                config = response.text
                self.findings['config'] = config
                print(f"{Theme.OKGREEN}[+] Extracted .git/config{Theme.ENDC}")
                
                # Parse remote URLs
                remotes = re.findall(r'url\s*=\s*(.+)', config)
                if remotes:
                    print(f"{Theme.WARNING}[*] Remote repositories found:{Theme.ENDC}")
                    for remote in remotes:
                        print(f"{Theme.OKCYAN}    {remote}{Theme.ENDC}")
                        self.findings['sensitive_data'].append({
                            'type': 'remote_url',
                            'value': remote
                        })
                
                return config
        except requests.RequestException as e:
            print(f"{Theme.FAIL}[-] Failed to extract config: {e}{Theme.ENDC}")
        
        return None
    
    def extract_branches(self) -> List[str]:
        """Extract branch information"""
        branches = []
        
        # Try to get HEAD ref
        head_url = urljoin(self.target_url, '.git/HEAD')
        try:
            response = self.session.get(head_url, timeout=self.timeout)
            if response.status_code == 200:
                head_content = response.text.strip()
                match = re.search(r'ref:\s*(.+)', head_content)
                if match:
                    current_branch = match.group(1)
                    branches.append(current_branch)
                    print(f"{Theme.OKGREEN}[+] Current branch: {current_branch}{Theme.ENDC}")
        except requests.RequestException:
            pass
        
        # Try common branches
        common_branches = ['master', 'main', 'develop', 'dev', 'staging', 'production']
        for branch in common_branches:
            ref_path = f'.git/refs/heads/{branch}'
            url = urljoin(self.target_url, ref_path)
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    commit_hash = response.text.strip()
                    branches.append(branch)
                    print(f"{Theme.OKGREEN}[+] Branch found: {branch} ({commit_hash[:8]}){Theme.ENDC}")
                    self.findings['commits'].append({
                        'branch': branch,
                        'hash': commit_hash
                    })
            except requests.RequestException:
                continue
        
        self.findings['branches'] = branches
        return branches
    
    def extract_logs(self) -> List[str]:
        """Extract git logs"""
        logs = []
        log_paths = [
            '.git/logs/HEAD',
            '.git/logs/refs/heads/master',
            '.git/logs/refs/heads/main'
        ]
        
        for path in log_paths:
            url = urljoin(self.target_url, path)
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    log_content = response.text
                    logs.append(log_content)
                    print(f"{Theme.OKGREEN}[+] Extracted: {path}{Theme.ENDC}")
                    
                    # Extract email addresses from logs
                    emails = re.findall(r'<([^>]+@[^>]+)>', log_content)
                    if emails:
                        print(f"{Theme.WARNING}[*] Email addresses found:{Theme.ENDC}")
                        for email in set(emails):
                            print(f"{Theme.OKCYAN}    {email}{Theme.ENDC}")
                            self.findings['sensitive_data'].append({
                                'type': 'email',
                                'value': email
                            })
            except requests.RequestException:
                continue
        
        return logs
    
    def extract_contributors(self) -> List[Dict]:
        """Extract contributor information from git logs"""
        contributors = []
        
        log_content = ""
        for path in ['.git/logs/HEAD', '.git/logs/refs/heads/master', '.git/logs/refs/heads/main']:
            url = urljoin(self.target_url, path)
            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    log_content += response.text
            except requests.RequestException:
                continue
        
        if log_content:
            # Extract name and email patterns from logs
            # Format: hash hash Name <email@domain.com> timestamp message
            pattern = r'([A-Za-z\s]+)\s*<([^>]+@[^>]+)>'
            matches = re.findall(pattern, log_content)
            
            contributor_map = {}
            for name, email in matches:
                name = name.strip()
                if email not in contributor_map:
                    contributor_map[email] = {
                        'name': name,
                        'email': email,
                        'commits': 1
                    }
                else:
                    contributor_map[email]['commits'] += 1
            
            contributors = list(contributor_map.values())
            
            if contributors:
                print(f"\n{Theme.OKCYAN}[*] Contributors found:{Theme.ENDC}")
                for contrib in sorted(contributors, key=lambda x: x['commits'], reverse=True):
                    print(f"{Theme.OKBLUE}  - {contrib['name']} <{contrib['email']}> ({contrib['commits']} commits){Theme.ENDC}")
                    self.findings['sensitive_data'].append({
                        'type': 'contributor',
                        'value': f"{contrib['name']} <{contrib['email']}>"
                    })
        
        return contributors
    
    def extract_deployment_info(self) -> Dict:
        """Extract deployment and environment information"""
        deployment_info = {
            'environments': [],
            'servers': [],
            'services': [],
            'deployment_keys': []
        }
        
        if not self.findings['config']:
            return deployment_info
        
        config = self.findings['config']
        
        # Look for environment indicators in config
        env_patterns = {
            'staging': r'staging|stage|stg',
            'production': r'production|prod|live',
            'development': r'development|dev|local',
            'testing': r'testing|test|qa',
        }
        
        for env_name, pattern in env_patterns.items():
            if re.search(pattern, config, re.IGNORECASE):
                deployment_info['environments'].append(env_name)
        
        # Extract server/host information
        server_patterns = [
            r'(?:server|host|hostname)\s*=\s*([^\s\n]+)',
            r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}):',  # git@server.com:
            r'//([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/',  # https://server.com/
        ]
        
        for pattern in server_patterns:
            matches = re.findall(pattern, config, re.IGNORECASE)
            for match in matches:
                if match and match not in deployment_info['servers']:
                    deployment_info['servers'].append(match)
        
        # Extract service/application names
        service_patterns = [
            r'name\s*=\s*([a-zA-Z0-9_-]+)',
            r'application\s*=\s*([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in service_patterns:
            matches = re.findall(pattern, config, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 2 and match not in deployment_info['services']:
                    deployment_info['services'].append(match)
        
        # Report findings
        if deployment_info['environments']:
            print(f"\n{Theme.WARNING}[*] Environments detected: {', '.join(deployment_info['environments'])}{Theme.ENDC}")
        
        if deployment_info['servers']:
            print(f"{Theme.WARNING}[*] Servers/Hosts found:{Theme.ENDC}")
            for server in deployment_info['servers']:
                print(f"{Theme.OKCYAN}    {server}{Theme.ENDC}")
                self.findings['sensitive_data'].append({
                    'type': 'server',
                    'value': server
                })
        
        return deployment_info
    
    def scan_for_secrets(self) -> List[Dict]:
        """Scan for common secrets in configuration"""
        secrets = []
        
        if not self.findings['config']:
            return secrets
        
        # Comprehensive secret patterns
        patterns = {
            'AWS Access Key': r'AKIA[0-9A-Z]{16}',
            'AWS Secret Key': r'(?i)aws(.{0,20})?[\'\"][0-9a-zA-Z\/+]{40}[\'\"]',
            'API Key': r'(?i)api[_-]?key[\'\"]?\s*[:=]\s*[\'\"]?([a-zA-Z0-9_\-]{20,})[\'\"]?',
            'Private Key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
            'SSH Key': r'ssh-rsa\s+[A-Za-z0-9+/=]+',
            'Password': r'(?i)password[\'\"]?\s*[:=]\s*[\'\"]?([^\s\'\";]{8,})[\'\"]?',
            'Token': r'(?i)token[\'\"]?\s*[:=]\s*[\'\"]?([a-zA-Z0-9_\-\.]{20,})[\'\"]?',
            'Bearer Token': r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
            'Database URL': r'(?i)(mongodb|mysql|postgresql|postgres|redis|mariadb)://[^\s\'"]+',
            'GitHub Token': r'gh[pousr]_[A-Za-z0-9_]{36,}',
            'Slack Token': r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}',
            'Slack Webhook': r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+',
            'Google API Key': r'AIza[0-9A-Za-z\-_]{35}',
            'Stripe Key': r'(?i)(sk|pk)_(test|live)_[0-9a-zA-Z]{24,}',
            'Twilio Key': r'SK[0-9a-fA-F]{32}',
            'SendGrid Key': r'SG\.[a-zA-Z0-9_\-]{22}\.[a-zA-Z0-9_\-]{43}',
            'MailChimp Key': r'[0-9a-f]{32}-us[0-9]{1,2}',
            'JWT Token': r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*',
            'Docker Auth': r'(?i)docker(?:hub)?[_-]?(?:password|token)',
            'NPM Token': r'npm_[A-Za-z0-9]{36}',
            'PyPI Token': r'pypi-AgEIcHlwaS5vcmc[A-Za-z0-9\-_]{50,}',
            'OAuth Client Secret': r'(?i)client[_-]?secret[\'\"]?\s*[:=]\s*[\'\"]?([a-zA-Z0-9_\-]{20,})[\'\"]?',
            'S3 Bucket URL': r's3://[a-z0-9][a-z0-9\-]*[a-z0-9]',
            'Heroku API Key': r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
            'Firebase URL': r'.*\.firebaseio\.com',
            'RSA Private Key File': r'-----BEGIN RSA PRIVATE KEY-----[\s\S]+-----END RSA PRIVATE KEY-----',
        }
        
        config_text = self.findings['config']
        
        for secret_type, pattern in patterns.items():
            matches = re.findall(pattern, config_text)
            if matches:
                for match in matches:
                    value = match if isinstance(match, str) else match[0] if match else ''
                    if value and len(str(value)) > 3:  # Filter out very short matches
                        secrets.append({
                            'type': secret_type,
                            'value': value
                        })
                        # Truncate long values for display
                        display_value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                        print(f"{Theme.FAIL}[!] {secret_type} found: {display_value}{Theme.ENDC}")
        
        return secrets
    
    def dump_repository(self, output_dir: str) -> bool:
        """
        Download entire .git directory to reconstruct repository
        Returns True if successful
        """
        import os
        from pathlib import Path
        
        try:
            # Create output directory
            git_dir = Path(output_dir) / ".git"
            git_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"{Theme.OKBLUE}[*] Downloading .git directory structure...{Theme.ENDC}")
            
            # Essential files and directories to download
            essential_paths = [
                'HEAD',
                'config',
                'description',
                'index',
                'packed-refs',
            ]
            
            # Download essential files
            for path in essential_paths:
                url = urljoin(self.target_url, f'.git/{path}')
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    if response.status_code == 200:
                        file_path = git_dir / path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_bytes(response.content)
                        print(f"{Theme.OKGREEN}  [+] {path}{Theme.ENDC}")
                except requests.RequestException:
                    continue
            
            # Download refs
            print(f"{Theme.OKBLUE}[*] Downloading refs...{Theme.ENDC}")
            ref_paths = []
            for branch in self.findings['branches']:
                if 'refs/heads/' in branch:
                    ref_paths.append(branch)
                else:
                    ref_paths.append(f'refs/heads/{branch}')
            
            for ref_path in ref_paths:
                url = urljoin(self.target_url, f'.git/{ref_path}')
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    if response.status_code == 200:
                        file_path = git_dir / ref_path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(response.text)
                        print(f"{Theme.OKGREEN}  [+] {ref_path}{Theme.ENDC}")
                except requests.RequestException:
                    continue
            
            # Download logs
            print(f"{Theme.OKBLUE}[*] Downloading logs...{Theme.ENDC}")
            log_paths = [
                'logs/HEAD',
                'logs/refs/heads/master',
                'logs/refs/heads/main',
            ]
            
            for log_path in log_paths:
                url = urljoin(self.target_url, f'.git/{log_path}')
                try:
                    response = self.session.get(url, timeout=self.timeout)
                    if response.status_code == 200:
                        file_path = git_dir / log_path
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_bytes(response.content)
                        print(f"{Theme.OKGREEN}  [+] {log_path}{Theme.ENDC}")
                except requests.RequestException:
                    continue
            
            # Try to download objects (if index is available)
            print(f"{Theme.OKBLUE}[*] Attempting to download git objects...{Theme.ENDC}")
            
            # Extract commit hashes from findings
            commit_hashes = []
            for commit in self.findings['commits']:
                if 'hash' in commit:
                    commit_hashes.append(commit['hash'])
            
            # Download objects for known hashes
            objects_downloaded = 0
            for commit_hash in commit_hashes:
                if len(commit_hash) == 40:  # Valid SHA-1
                    obj_path = f'objects/{commit_hash[:2]}/{commit_hash[2:]}'
                    url = urljoin(self.target_url, f'.git/{obj_path}')
                    try:
                        response = self.session.get(url, timeout=self.timeout)
                        if response.status_code == 200:
                            file_path = git_dir / obj_path
                            file_path.parent.mkdir(parents=True, exist_ok=True)
                            file_path.write_bytes(response.content)
                            objects_downloaded += 1
                    except requests.RequestException:
                        continue
            
            if objects_downloaded > 0:
                print(f"{Theme.OKGREEN}  [+] Downloaded {objects_downloaded} objects{Theme.ENDC}")
            else:
                print(f"{Theme.WARNING}  [-] No objects downloaded (index may be corrupted or unavailable){Theme.ENDC}")
            
            print(f"\n{Theme.OKGREEN}[+] Repository structure downloaded successfully{Theme.ENDC}")
            print(f"{Theme.OKCYAN}[*] Location: {output_dir}{Theme.ENDC}")
            
            return True
            
        except Exception as e:
            print(f"{Theme.FAIL}[-] Dump failed: {e}{Theme.ENDC}")
            return False
    
    def generate_report(self) -> str:
        """Generate a detailed report"""
        report_lines = [
            "\n" + "="*70,
            f"{Theme.OKCYAN}{Theme.BOLD}Git  Exposure Scanner Report{Theme.ENDC}",
            "="*70,
            f"\n{Theme.OKBLUE}Target: {self.target_url}{Theme.ENDC}",
            f"{Theme.BOLD}Status: {'VULNERABLE' if self.findings['exposed'] else 'NOT VULNERABLE'}{Theme.ENDC}",
        ]
        
        if self.findings['exposed']:
            report_lines.append(f"\n{Theme.WARNING}[*] Exposed Git Files:{Theme.ENDC}")
            for file in self.findings['files_found']:
                report_lines.append(f"    - {file}")
            
            if self.findings['branches']:
                report_lines.append(f"\n{Theme.WARNING}[*] Branches Discovered:{Theme.ENDC}")
                for branch in self.findings['branches']:
                    report_lines.append(f"    - {branch}")
            
            if self.findings['sensitive_data']:
                report_lines.append(f"\n{Theme.FAIL}[!] Sensitive Data Found:{Theme.ENDC}")
                for item in self.findings['sensitive_data']:
                    report_lines.append(f"{Theme.FAIL}    [{item['type']}] {item['value']}{Theme.ENDC}")
        
        report_lines.append("\n" + "="*70)
        
        return "\n".join(report_lines)
    
    def scan(self) -> Tuple[bool, str, Dict]:
        """
        Perform complete scan
        Returns: (success, message, findings)
        """
        print(f"\n{Theme.OKCYAN}[*] Scanning {self.target_url} for exposed .git directory...{Theme.ENDC}")
        
        # Check if .git is exposed
        if not self.check_git_exposure():
            msg = "No exposed .git directory found"
            print(f"\n{Theme.WARNING}[-] {msg}{Theme.ENDC}")
            return False, msg, self.findings
        
        print(f"\n{Theme.FAIL}{Theme.BOLD}[!] .git directory is EXPOSED!{Theme.ENDC}")
        
        # Extract information
        print(f"\n{Theme.OKCYAN}[*] Extracting git configuration...{Theme.ENDC}")
        self.extract_git_config()
        
        print(f"\n{Theme.OKCYAN}[*] Discovering branches...{Theme.ENDC}")
        self.extract_branches()
        
        print(f"\n{Theme.OKCYAN}[*] Extracting logs...{Theme.ENDC}")
        self.extract_logs()
        
        print(f"\n{Theme.OKCYAN}[*] Analyzing contributors...{Theme.ENDC}")
        self.extract_contributors()
        
        print(f"\n{Theme.OKCYAN}[*] Extracting deployment information...{Theme.ENDC}")
        self.extract_deployment_info()
        
        print(f"\n{Theme.OKCYAN}[*] Scanning for secrets...{Theme.ENDC}")
        secrets = self.scan_for_secrets()
        if secrets:
            self.findings['sensitive_data'].extend(secrets)
        
        # Generate report
        report = self.generate_report()
        print(report)
        
        return True, "Git exposure found - sensitive data extracted", self.findings


# =========================
# UI / Banner
# =========================

class BannerDisplay:
    """Display banners and output formatting"""
    
    @staticmethod
    def show_header():
        """Display ASCII art banner"""
        print(f"""
{Theme.FAIL}{Theme.BOLD}
!      ░██████  ░██   ░██         ░██████                                    
!     ░██   ░██       ░██        ░██   ░██                                   
!    ░██        ░██░████████    ░██          ░███████   ░██████   ░████████  
!    ░██  █████ ░██   ░██        ░████████  ░██    ░██       ░██  ░██    ░██ 
!    ░██     ██ ░██   ░██               ░██ ░██         ░███████  ░██    ░██ 
!     ░██  ░███ ░██   ░██        ░██   ░██  ░██    ░██ ░██   ░██  ░██    ░██ 
!      ░█████░█ ░██    ░████      ░██████    ░███████   ░█████░██ ░██    ░██ 
!                                                                            
!                                                                            
{Theme.ENDC}
{Theme.OKCYAN}{Theme.BOLD}[{Signature.TOOL_NAME}]{Theme.ENDC}
{Theme.OKBLUE}Extract Sensitive Data from Exposed .git Directories{Theme.ENDC}
{Theme.OKGREEN}Author  : {Signature.AUTHOR}{Theme.ENDC}
{Theme.OKBLUE}Website : {Signature.WEBSITE}{Theme.ENDC}
{Theme.OKBLUE}Version : {Signature.VERSION}{Theme.ENDC}
""")
    
    @staticmethod
    def show_config(target: str):
        """Show scan configuration"""
        print(f"\n{Theme.OKBLUE}[*] SCAN PARAMETERS{Theme.ENDC}")
        print(f"{Theme.OKCYAN}TARGET  : {target}{Theme.ENDC}\n")
    
    @staticmethod
    def show_success(findings: Dict):
        """Show success message with findings"""
        print(f"\n{Theme.OKGREEN}{Theme.BOLD}[+] SCAN COMPLETED SUCCESSFULLY{Theme.ENDC}")
        
        if findings.get('sensitive_data'):
            print(f"\n{Theme.FAIL}{Theme.BOLD}[!] CRITICAL: Sensitive data exposed!{Theme.ENDC}")
            print(f"{Theme.WARNING}[*] Total items found: {len(findings['sensitive_data'])}{Theme.ENDC}")
    
    @staticmethod
    def show_failure(status: str, data: Dict):
        """Show failure message"""
        print(f"\n{Theme.WARNING}[-] {status}{Theme.ENDC}")
        if not data.get('exposed'):
            print(f"{Theme.OKGREEN}[✓] Target appears secure (no .git exposure){Theme.ENDC}")
