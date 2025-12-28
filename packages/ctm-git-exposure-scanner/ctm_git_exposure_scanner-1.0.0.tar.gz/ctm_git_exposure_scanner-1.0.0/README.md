# Git Exposure Scanner

**Extract sensitive information from exposed `.git` directories**

## Overview

This tool scans web applications for exposed `.git` directories and extracts sensitive information including:

- Git configuration files
- Branch information
- Commit history and logs
- Email addresses from commit logs
- Remote repository URLs
- **Sensitive secrets** like:
  - AWS Access Keys & Secret Keys
  - API Keys
  - Private Keys
  - Passwords
  - Tokens
  - Database connection strings

## Installation

```bash
pip install .
```

## Usage

### Basic Scan

```bash
git-exposure-scanner -t https://example.com
```

### With Custom Timeout

```bash
git-exposure-scanner -t https://example.com --timeout 15
```

### Using Full Package Name

```bash
CYBERTECHMIND-GIT-EXPOSURE-SCANNER -t https://example.com
```

## What It Does

1. **Detects Exposed .git Directory**
   - Checks for common .git files (HEAD, config, index, description)
   
2. **Extracts Configuration**
   - Downloads `.git/config`
   - Parses remote repository URLs
   
3. **Discovers Branches**
   - Finds current branch
   - Scans for common branches (master, main, develop, staging, production)
   - Retrieves commit hashes
   
4. **Extracts Logs**
   - Downloads git logs
   - Extracts developer email addresses
   
5. **Scans for Secrets**
   - AWS credentials
   - API keys
   - Passwords
   - Private keys
   - Database URLs
   - Authentication tokens

## Example Output

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║           Git Exposure Scanner                                    ║
║           Extract Sensitive Data from .git Directories            ║
║                                                                   ║
║           Author: Moovendhan V (CyberTechMind)                    ║
║           Version: 1.0.0                                          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

[*] Target: https://example.com
[*] Starting scan...

[*] Scanning https://example.com for exposed .git directory...
[+] Found: .git/HEAD
[+] Found: .git/config

[!] .git directory is EXPOSED!

[*] Extracting git configuration...
[+] Extracted .git/config
[*] Remote repositories found:
    https://github.com/company/secret-repo.git

[*] Discovering branches...
[+] Current branch: refs/heads/master
[+] Branch found: master (a1b2c3d4)

[*] Extracting logs...
[+] Extracted: .git/logs/HEAD
[*] Email addresses found:
    developer@example.com
    admin@example.com

[*] Scanning for secrets...
[!] AWS Access Key found: AKIAIOSFODNN7EXAMPLE...
[!] Database URL found: mongodb://admin:password123@...

======================================================================
Git Exposure Scanner Report
======================================================================

Target: https://example.com
Status: VULNERABLE

[*] Exposed Git Files:
    - .git/HEAD
    - .git/config

[*] Branches Discovered:
    - refs/heads/master
    - master

[!] Sensitive Data Found:
    [remote_url] https://github.com/company/secret-repo.git
    [email] developer@example.com
    [AWS Access Key] AKIAIOSFODNN7EXAMPLE
    [Database URL] mongodb://admin:password123@...

======================================================================

[✓] Scan completed successfully!

[!] CRITICAL: Sensitive data exposed!
[*] Total items found: 4
```

## Security Impact

Exposed `.git` directories can reveal:

- **Source Code**: Complete application source code can be reconstructed
- **Credentials**: API keys, passwords, and secrets in config files
- **Infrastructure Details**: Database URLs, server configurations
- **Developer Information**: Email addresses, commit history
- **Private Repositories**: URLs to internal/private GitHub/GitLab repos

## Remediation

If this tool finds an exposed `.git` directory:

1. **Immediately**: Block `.git` directory in web server configuration
2. **Rotate Credentials**: Change all exposed passwords, API keys, tokens
3. **Review History**: Check git history for other sensitive data
4. **Update Deployment**: Ensure `.git` is excluded from production deploys

### Apache (.htaccess)
```apache
RedirectMatch 404 /\.git
```

### Nginx
```nginx
location ~ /\.git {
    deny all;
    return 404;
}
```

## Legal Disclaimer

This tool is for **authorized security testing only**. Only use on systems you own or have explicit permission to test. Unauthorized access to computer systems is illegal.

## Author

**Moovendhan V** - CyberTechMind

## License

MIT License - See LICENSE file for details
