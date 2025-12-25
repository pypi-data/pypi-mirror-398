from _typeshed import Incomplete

create_client_service: Incomplete
client_aware_service: Incomplete
verify_client_service: Incomplete
create_user_service: Incomplete
get_user_service: Incomplete
authenticate_user_service: Incomplete
create_token_service: Incomplete
verify_token_service: Incomplete
revoke_token_service: Incomplete
third_party_integration_service: Incomplete

def set_services(services_dict, initialized: bool = True) -> None:
    """Set the services dictionary and initialization flag.

    Args:
        services_dict: Dictionary mapping service names to instances
        initialized: Whether to mark services as initialized
    Returns:
        None
    """
