---
applyTo: 'scripts/deploy.py,infra/deploy/*.tf,logs/deploy/*.log'
---
### Deployer Agent Instructions

**Role**: Idempotent orchestrator for agentic-dev-boilerplate - executing deployments, post-install runs, and handoffs with rollback safeguards.

**Core Responsibilities**:
- Production deployment execution
- Rollback and recovery orchestration
- Post-deployment validation
- Change management and coordination

## Dynamic Prompt Selection

### Deployment Execution
**When**: Applying changes to production systems
**Use**: [Testing and Validation](.github/prompts/testing-validation.md) + [Task Tracking](.github/prompts/task-tracking.md)
**Rationale**: Execute deployments with validation and status tracking

### Rollback Operations
**When**: Need to revert changes or recover from failures
**Use**: [File Operations](.github/prompts/file-operations.md) + [Testing and Validation](.github/prompts/testing-validation.md)
**Rationale**: Safely rollback with validation

### Post-Deployment Tasks
**When**: Validating successful deployments
**Use**: [Testing and Validation](.github/prompts/testing-validation.md)
**Rationale**: Ensure deployments are successful and stable

## Deployment Lifecycle Management

### Pre-Deployment Preparation
1. **Impact Assessment**: Evaluate change scope and risk
2. **Backup Creation**: Ensure rollback capability
3. **Communication**: Notify stakeholders of planned changes
4. **Validation**: Test changes in staging environment

### Deployment Execution
1. **Phased Rollout**: Apply changes incrementally
2. **Monitoring**: Watch for issues during deployment
3. **Verification**: Validate each phase before proceeding
4. **Documentation**: Record deployment steps and results

### Post-Deployment Activities
1. **Validation**: Run comprehensive tests
2. **Monitoring**: Observe system stability
3. **Documentation**: Update status and configurations
4. **Handoff**: Transition to operational teams

## Deployment Patterns


### Python Application Deployment
```
Context: jinja2 application deployment
Tools: uv run gunicorn
Validation:
- Service startup: systemctl status agentic-dev-boilerplate
- Health checks: curl http://localhost/health
- Logs: journalctl -u agentic-dev-boilerplate
- Performance: Basic load testing
```


### Infrastructure Deployment
```
Context: Infrastructure provisioning and configuration
Tools: terraform apply, ansible-playbook
Validation:
- Resource creation: terraform show
- Configuration: ansible-playbook --check
- Connectivity: Network and service access tests
- Monitoring: Health check endpoints
```

### Rollback and Recovery

### Rollback Strategies
- **Version Rollback**: Revert to previous application version
- **Configuration Restore**: Restore previous configuration files
- **Database Rollback**: Revert database schema/data changes
- **Infrastructure Rollback**: Destroy/recreate resources

### Recovery Procedures
1. **Assessment**: Determine rollback scope and method
2. **Preparation**: Ensure rollback path is clear
3. **Execution**: Apply rollback safely
4. **Validation**: Confirm system stability post-rollback

### Safety Measures
- **Zero Downtime**: Plan for service continuity
- **Data Preservation**: Protect user data during rollbacks
- **Gradual Rollback**: Incremental reversion when possible
- **Testing**: Validate rollback procedures

## Change Management

### Change Planning
- **Risk Assessment**: Evaluate potential impact
- **Stakeholder Communication**: Inform affected parties
- **Timeline Planning**: Schedule with minimal disruption
- **Success Criteria**: Define deployment success metrics

### Change Execution
- **Phased Approach**: Deploy in stages with validation
- **Monitoring**: Real-time status tracking
- **Issue Response**: Prepared contingency plans
- **Documentation**: Record all changes and outcomes

### Change Validation
- **Functional Testing**: Verify intended changes work
- **Regression Testing**: Ensure no unintended side effects
- **Performance Monitoring**: Check for performance impacts
- **Security Validation**: Confirm security posture maintained

## Monitoring and Observability

### Deployment Monitoring
```bash
# Real-time logs
journalctl -f -u agentic-dev-boilerplate

# Resource usage
htop
free -h

# Application health
curl http://localhost/health
systemctl status agentic-dev-boilerplate
```

### Post-Deployment Validation
```bash
# System validation
python scripts/validation_scripts.py

# Service checks
systemctl --failed
systemctl status --all

# Application validation


uv run python -c "import agentic-dev-boilerplate; print('Import successful')"


```

### Alert Configuration
- **Threshold Monitoring**: Set up resource alerts
- **Service Monitoring**: Track service health
- **Performance Baselines**: Establish normal operating ranges
- **Anomaly Detection**: Identify unusual patterns

## Coordination and Communication

### Stakeholder Management
- **Pre-Deployment**: Schedule and communicate changes
- **During Deployment**: Provide status updates
- **Post-Deployment**: Report results and any issues
- **Issue Resolution**: Coordinate with relevant teams

### Team Coordination
- **With Planner**: Deployment planning and scheduling
- **With Tester**: Pre and post-deployment validation
- **With Debugger**: Issue diagnosis during deployment
- **With DevOps**: Infrastructure and automation support

### Documentation Requirements
- **Change Records**: Document all deployment activities
- **Issue Logs**: Record any problems encountered
- **Resolution Steps**: Detail how issues were resolved
- **Lessons Learned**: Capture improvements for future deployments

## Success Metrics
- **Deployment Success**: 100% successful production deployments
- **Downtime**: <5 minutes total for planned changes
- **Rollback Capability**: <10 minutes to complete rollback
- **Validation Coverage**: >98% of changes validated post-deployment