# Security Guidelines - AI-System-DocAI V5I

## Overview

AI-System-DocAI V5I is designed for deployment in internal LAN environments with security features appropriate for this use case. This document outlines security considerations and best practices.

## Security Features

### 1. Offline Operation

- **CPU-only architecture**: No GPU dependencies means no CUDA/GPU driver vulnerabilities
- **No telemetry**: Application does not send any usage data to external servers
- **Local processing**: All document processing and indexing happens on local machine
- **No cloud dependencies**: Core functionality works without internet connection

### 2. Data Privacy

- **Local storage only**: All indexes, documents, and logs stored locally
- **No external API calls** (except when explicitly using cloud LLM backends)
- **Encrypted configuration**: API keys stored in config file (see recommendations below)
- **Audit logging**: Comprehensive logs of all operations for security review

### 3. Internal LAN Security

- **IP filtering**: Optional IP whitelist/blacklist for LAN access
- **Rate limiting**: Configurable rate limits per IP address
- **Session management**: Timeout settings for inactive sessions
- **Input validation**: Sanitization of user inputs to prevent injection attacks

## Security Considerations

### API Key Management

**Problem**: API keys are stored in plain text in config files

**Recommendations**:
1. Use environment variables instead of config files for sensitive keys
2. Set appropriate file permissions on config files:
   - Windows: Restrict access to user account only
   - Linux: `chmod 600 ~/.config/AI-System-DocAI/config.toml`
3. Never commit config files with API keys to version control
4. Use separate API keys for different environments
5. Rotate API keys regularly

### File System Security

**Document Access**:
- Application requires read access to document folders
- Indexed documents remain in original locations
- Consider using encrypted file systems for sensitive documents

**Index Security**:
- FAISS indexes contain vector embeddings (not full document text)
- Metadata files (meta.jsonl) contain document snippets and paths
- Protect index directories from unauthorized access

**Log Security**:
- Logs may contain document filenames and query text
- Rotate logs regularly (30-day retention by default)
- Consider log file encryption for sensitive environments

### Network Security

**Internal LAN Deployment**:
```toml
[security]
internal_lan_mode = true
allowed_ips = ["192.168.1.0/24"]  # Restrict to specific subnet
require_auth = false  # Enable if needed
audit_logging = true
rate_limit_per_ip = 100  # queries per hour
```

**Recommendations**:
1. Deploy behind firewall (no direct internet exposure)
2. Use VPN for remote access
3. Monitor audit logs for suspicious activity
4. Implement network segmentation

### Application Updates

**Update Process**:
1. Download updates only from official sources
2. Verify file hashes/signatures
3. Test updates in staging environment first
4. Backup configuration and indexes before updating

**Automatic Updates**:
- Disabled by default
- Enable only if update source is trusted and secured

## Security Best Practices

### 1. Installation

- Install in directory with restricted permissions
- Run as non-privileged user (not root/Administrator)
- Disable automatic admin elevation
- Verify Python installation source

### 2. Configuration

- Review `config.toml` after installation
- Disable unused LLM backends
- Set appropriate rate limits
- Enable audit logging

### 3. Operation

- Monitor logs regularly for errors/warnings
- Review audit logs for unusual activity
- Limit document access to need-to-know basis
- Use "No LLM" mode when external API calls are not needed

### 4. Maintenance

- Keep Python and dependencies updated
- Review and clean up old indexes
- Rotate and archive logs
- Backup configuration regularly

## Vulnerability Reporting

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Contact your security team or system administrator
3. Provide detailed description and reproduction steps
4. Allow time for assessment and patching

## Compliance Considerations

### Data Residency

- All data processing occurs on local machine
- No data transferred to cloud (except when using cloud LLM APIs)
- Suitable for environments with data residency requirements

### GDPR/Privacy Regulations

- Application does not collect personal data
- Document content remains under user control
- Audit logs may contain document metadata (review retention policies)

### Industry Standards

- Follows OWASP secure coding guidelines
- Input validation and sanitization implemented
- Logging follows security logging best practices

## Security Checklist

Before deployment:

- [ ] Review and update `config.toml`
- [ ] Set appropriate file permissions
- [ ] Configure IP filtering (if needed)
- [ ] Enable audit logging
- [ ] Set rate limits
- [ ] Test authentication (if enabled)
- [ ] Review log retention policies
- [ ] Document API key management process
- [ ] Establish backup procedures
- [ ] Define incident response plan

During operation:

- [ ] Monitor logs daily
- [ ] Review audit logs weekly
- [ ] Update dependencies monthly
- [ ] Rotate API keys quarterly
- [ ] Test backup restoration quarterly
- [ ] Review access controls annually

## Known Limitations

1. **API Keys in Config**: Stored in plain text (use environment variables)
2. **No Built-in Encryption**: Indexes stored unencrypted (use encrypted filesystem)
3. **No Authentication**: Optional feature (implement if needed)
4. **Local Attack Surface**: Application runs with user privileges (use dedicated user)
5. **Python Dependencies**: Rely on PyPI packages (audit dependencies)

## Recommendations for High-Security Environments

1. **Isolate the System**: Run on dedicated machine or VM
2. **Encrypt Storage**: Use full-disk encryption
3. **Air-Gap Deployment**: No network connection (use "No LLM" mode)
4. **Audit Everything**: Enable all logging, monitor continuously
5. **Minimal Installation**: Remove unused LLM backends and dependencies
6. **Code Review**: Review source code before deployment
7. **Security Scanning**: Scan for vulnerabilities regularly

## Support

For security questions or concerns:
- Contact your IT security team
- Review logs in `logs/` directory
- Check documentation in `docs/` directory

## Disclaimer

This application is provided as-is for internal use. Users are responsible for:
- Securing their deployment environment
- Managing API keys and credentials
- Monitoring and maintaining the system
- Compliance with applicable regulations

The publishers assume no liability for security breaches or data loss.

