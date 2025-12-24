"""Feature flags for Trustwise SDK."""


# Set of features that are currently in beta
BETA_FEATURES: set[str] = {
    "guardrails",
}

# Set of features that are deprecated
DEPRECATED_FEATURES: set[str] = {
    "v3_metrics",
}

def is_beta_feature(feature_name: str) -> bool:
    """
    Check if a feature is currently in beta.
    
    Args:
        feature_name: Name of the feature to check
        
    Returns:
        bool: True if the feature is in beta, False otherwise
    """
    return feature_name.lower() in BETA_FEATURES

def is_deprecated_feature(feature_name: str) -> bool:
    """
    Check if a feature is currently deprecated.
    
    Args:
        feature_name: Name of the feature to check
        
    Returns:
        bool: True if the feature is deprecated, False otherwise
    """
    return feature_name.lower() in DEPRECATED_FEATURES

def get_beta_features() -> set[str]:
    """
    Get the set of all features currently in beta.
    
    Returns:
        Set[str]: Set of feature names that are in beta
    """
    return BETA_FEATURES.copy()

def get_deprecated_features() -> set[str]:
    """
    Get the set of all features currently deprecated.
    
    Returns:
        Set[str]: Set of feature names that are deprecated
    """
    return DEPRECATED_FEATURES.copy() 