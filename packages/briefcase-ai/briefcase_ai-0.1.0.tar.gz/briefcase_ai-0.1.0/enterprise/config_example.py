"""
Enterprise Configuration Example

This file shows how to configure enterprise features for integration
with the OSS core. Copy this to your application configuration and
modify as needed.
"""

# Example configuration for enterprise features
ENTERPRISE_CONFIG = {
    "enterprise": {
        "enabled": True,
        "license_key": "your-enterprise-license-key",

        # Authentication & Authorization
        "auth": {
            "rbac": {
                "enabled": True,
                "default_roles": ["viewer", "developer", "admin"],
                "auto_assign_roles": {"new_users": "viewer"}
            },
            "sso": {
                "enabled": True,
                "provider_url": "https://your-idp.com/sso",
                "entity_id": "briefcase-enterprise",
                "certificate_path": "/path/to/saml.crt",
                "attribute_mapping": {
                    "user_id": "NameID",
                    "email": "email",
                    "first_name": "givenName",
                    "last_name": "surname",
                    "roles": "roles"
                }
            }
        },

        # Compliance & Audit
        "compliance": {
            "audit": {
                "enabled": True,
                "storage_backend": "database",
                "retention_days": 2555,  # 7 years
                "real_time_alerts": True
            },
            "reporting": {
                "enabled": True,
                "auto_schedule": {
                    "soc2": "monthly",
                    "gdpr": "quarterly"
                },
                "recipients": ["compliance@company.com"]
            },
            "retention": {
                "enabled": True,
                "enforce_automatically": True,
                "notification_days_before": 30
            }
        },

        # Hosted Infrastructure
        "hosted": {
            "replay": {
                "enabled": True,
                "provider": "aws",
                "region": "us-east-1",
                "instance_types": ["m5.large", "m5.xlarge"],
                "auto_scaling": True,
                "min_instances": 1,
                "max_instances": 20
            },
            "tenant": {
                "enabled": True,
                "multi_tenancy": True,
                "default_tier": "professional",
                "billing_integration": True
            },
            "scaling": {
                "enabled": True,
                "metrics": ["cpu_utilization", "queue_length"],
                "scale_up_threshold": 70.0,
                "scale_down_threshold": 30.0,
                "cooldown_minutes": 5
            }
        },

        # Analytics & Insights
        "analytics": {
            "metrics": {
                "enabled": True,
                "collection_interval": 60,  # seconds
                "retention_days": 90,
                "export_to": ["prometheus", "datadog"]
            },
            "insights": {
                "enabled": True,
                "ai_recommendations": True,
                "anomaly_detection": True,
                "alert_thresholds": {
                    "high_cpu": 80.0,
                    "high_error_rate": 5.0,
                    "low_success_rate": 95.0
                }
            },
            "dashboards": {
                "enabled": True,
                "default_dashboards": ["system_overview", "security"],
                "custom_dashboards": True
            }
        }
    }
}

# Environment-specific overrides
DEVELOPMENT_OVERRIDES = {
    "enterprise": {
        "auth": {
            "sso": {"enabled": False},  # Disable SSO in dev
        },
        "hosted": {
            "replay": {"max_instances": 2},  # Limit scaling in dev
        },
        "compliance": {
            "audit": {"storage_backend": "memory"}  # In-memory for dev
        }
    }
}

PRODUCTION_OVERRIDES = {
    "enterprise": {
        "analytics": {
            "metrics": {
                "export_to": ["prometheus", "datadog", "cloudwatch"]
            }
        },
        "compliance": {
            "audit": {
                "storage_backend": "secure_database",
                "encryption": True,
                "backup_enabled": True
            }
        }
    }
}

def get_config(environment="development"):
    """Get configuration for specific environment"""
    base_config = ENTERPRISE_CONFIG.copy()

    if environment == "development":
        # Merge development overrides
        _merge_config(base_config, DEVELOPMENT_OVERRIDES)
    elif environment == "production":
        # Merge production overrides
        _merge_config(base_config, PRODUCTION_OVERRIDES)

    return base_config

def _merge_config(base, override):
    """Recursively merge configuration dictionaries"""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _merge_config(base[key], value)
        else:
            base[key] = value