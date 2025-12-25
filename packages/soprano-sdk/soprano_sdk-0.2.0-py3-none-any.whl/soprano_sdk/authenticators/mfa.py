import requests
from typing import TypedDict, Literal, NotRequired
from soprano_sdk.core.constants import MFARestAuthorizerEnv


class MFAChallenge(TypedDict):
    value: str


class MFAState(TypedDict):
    challengeType: Literal['OTP', 'dob']
    post_payload: dict[str, str]
    otpValue: NotRequired[str]
    status: Literal['IN_PROGRESS', 'COMPLETED', 'ERRORED', 'FAILED'] | None
    message: str
    retry_count: int



def get_response(response: requests.Response):
    if response.ok:
        return response.json(), None
    else:
        return None, response.json()


def build_path(base_url: str, path: str):
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def enforce_mfa_if_required(state: dict):
    _mfa : MFAState = state['_mfa']
    if _mfa['status'] == 'COMPLETED':
        return True
    generate_token_response = requests.post(
        build_path(
            base_url=MFARestAuthorizerEnv.GENERATE_TOKEN_BASE_URL.get_from_env(),
            path=MFARestAuthorizerEnv.GENERATE_TOKEN_PATH.get_from_env()
        ), json=_mfa['post_payload'], timeout=30, headers={"Authorization": f"Bearer {state['bearer_token']}"}
    )
    _, error = get_response(generate_token_response)

    challenge_type = error['additionalData']['challengeType']
    _mfa['challengeType'] = challenge_type
    _mfa['status'] = 'IN_PROGRESS'
    _mfa['retry_count'] = 0
    _mfa['message'] = f"Please enter the {challenge_type}"
    if delivery_methods := error['additionalData'].get(f"{challenge_type.lower()}SentTo"):
        _mfa['message'] += f" sent via {','.join(delivery_methods)}"
    return False


def mfa_validate_user_input(**state: dict):
    _mfa : MFAState = state['_mfa']
    input_field_name = state['_active_input_field']
    if not state[input_field_name]:
        return False

    post_payload = _mfa['post_payload']
    challenge_field_name = f"{_mfa['challengeType'].lower()}Challenge"
    post_payload.update({challenge_field_name: {"value": state[input_field_name]}})
    validate_token_response = requests.post(
        build_path(
            base_url=MFARestAuthorizerEnv.VALIDATE_TOKEN_BASE_URL.get_from_env(),
            path=MFARestAuthorizerEnv.VALIDATE_TOKEN_PATH.get_from_env()
        ), json=post_payload, timeout=30, headers={"Authorization": f"Bearer {state['bearer_token']}"}
    )
    _mfa['retry_count'] += 1
    response, error = get_response(validate_token_response)
    if error:
        if _mfa['retry_count'] == 1:
            _mfa['status'] = 'ERRORED'
            _mfa['message'] = (
                f"You Have Entered Invalid {_mfa['challengeType']}. {_mfa['message']}"
            )
        return False

    if response and 'token' in response:
        token = response['token']
        post_payload['token'] = token

        authorize = requests.post(
            build_path(
                base_url=MFARestAuthorizerEnv.AUTHORIZE_TOKEN_BASE_URL.get_from_env(),
                path=MFARestAuthorizerEnv.AUTHORIZE_TOKEN_PATH.get_from_env()
            ),
            json=post_payload,
            timeout=30,
            headers={"Authorization": f"Bearer {state['bearer_token']}"}
        )
        if authorize.status_code == 204:
            _mfa['status'] = 'COMPLETED'
            return True
        else:
            _mfa['status'] = 'FAILED'
            return False


class MFANodeConfig:

    @classmethod
    def get_call_function_template(cls, source_node: str, next_node: str, mfa: dict):
        return dict(
            id=f"{source_node}_mfa_start",
            action="call_function",
            function="conversational_sop.authenticators.mfa.enforce_mfa_if_required",
            output=f"{source_node}_mfa_start",
            mfa=mfa,
            transitions=[
                dict(
                    condition=True,
                    next=source_node,
                ),
                dict(
                    condition=False,
                    next=next_node,
                ),
            ]
        )

    @classmethod
    def get_validate_user_input(cls, source_node: str, next_node: str, model_name: str):
        input_field_name = f"{source_node}_mfa_input"
        return dict(
            id=f"{source_node}_mfa_validate",
            action="collect_input_with_agent",
            description="Collect Input for MFA value",
            field=input_field_name,
            max_attempts=3,
            validator="conversational_sop.authenticators.mfa.mfa_validate_user_input",
            agent=dict(
                name="MFA Input Data Collector",
                model=model_name,
                initial_message="{{_mfa.message}}",
                instructions="""
                    You are an authentication value extractor. Your job is to identify and extract MFA codes from user input.

                    **Task:**
                    - Read the user's message
                    - Extract ONLY the OTP code value
                    - Output in the exact format shown below

                    **Output Format:**
                    MFA_CAPTURED:

            """),
            transitions=[
                dict(
                    pattern="MFA_CAPTURED:",
                    next=next_node
                )
            ]
        )
