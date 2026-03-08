"""
Auth Stack - Cognito User Pool and App Client
Implements Requirements 9.1, 9.3, 9.4, 19.6
"""
from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_cognito as cognito,
)
from constructs import Construct


class AuthStack(Stack):
    """Stack for authentication resources"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        env_name: str,
        env_config: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        self.env_config = env_config

        # Create Cognito User Pool
        self.user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name=f"ai-builder-copilot-{env_name}",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=False
            ),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True
            ),
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            mfa=cognito.Mfa.OPTIONAL if env_config.get("enableMfa", False) else cognito.Mfa.OFF,
            mfa_second_factor=cognito.MfaSecondFactor(
                sms=False,
                otp=True
            ) if env_config.get("enableMfa", False) else None,
            removal_policy=RemovalPolicy.RETAIN if env_name == "prod" else RemovalPolicy.DESTROY
        )

        # Create App Client
        self.user_pool_client = self.user_pool.add_client(
            "AppClient",
            user_pool_client_name=f"ai-builder-copilot-client-{env_name}",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True
            ),
            generate_secret=False,
            access_token_validity=Duration.hours(1),
            id_token_validity=Duration.hours(1),
            refresh_token_validity=Duration.days(30),
            prevent_user_existence_errors=True
        )
