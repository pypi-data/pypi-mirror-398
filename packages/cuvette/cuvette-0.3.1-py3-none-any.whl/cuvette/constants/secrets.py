from pathlib import Path

SECRETS_ROOT = Path(__file__).parent.parent.parent / "secrets"

GENERAL_FILE_SECRETS = [
    {"name": "ssh-key", "type": "file", "path": ".ssh/id_rsa"},
    {"name": "aws-creds", "type": "file", "path": ".aws/credentials"},
    {"name": "AWS_CREDENTIALS", "type": "file", "path": ".aws/credentials"},
    {"name": "aws-config", "type": "file", "path": ".aws/config"},
    {"name": "AWS_CONFIG", "type": "file", "path": ".aws/config"},
    {"name": "gcp-creds", "type": "file", "path": ".gcp/service-account.json"},
    {"name": "kaggle-creds", "type": "file", "path": ".kaggle/kaggle.json"},
]

GENERAL_ENV_SECRETS = [
    {"name": "HF_TOKEN", "type": "env", "env": "HF_TOKEN"},
    {"name": "HF_TOKEN_READ_ONLY", "type": "env", "env": "HF_TOKEN"},
    {"name": "OPENAI_API_KEY", "type": "env", "env": "OPENAI_API_KEY"},
    {"name": "openai_api_key", "type": "env", "env": "OPENAI_API_KEY"},
    {"name": "ANTHROPIC_API_KEY", "type": "env", "env": "ANTHROPIC_API_KEY"},
    {"name": "BEAKER_TOKEN", "type": "env", "env": "BEAKER_TOKEN"},
    {"name": "WANDB_API_KEY", "type": "env", "env": "WANDB_API_KEY"},
    {"name": "COMET_API_KEY", "type": "env", "env": "COMET_API_KEY"},
    {"name": "AWS_SECRET_ACCESS_KEY", "type": "env", "env": "AWS_SECRET_ACCESS_KEY"},
    {"name": "AWS_ACCESS_KEY_ID", "type": "env", "env": "AWS_ACCESS_KEY_ID"},
    {"name": "GOOGLE_API_KEY", "type": "env", "env": "GOOGLE_API_KEY"},
    {"name": "WEKA_ENDPOINT_URL", "type": "env", "env": "WEKA_ENDPOINT_URL"},
    {"name": "R2_ENDPOINT_URL", "type": "env", "env": "R2_ENDPOINT_URL"},
    {"name": "WEKA_PROFILE", "type": "env", "env": "WEKA_PROFILE"},
    {"name": "S3_PROFILE", "type": "env", "env": "S3_PROFILE"},
    {"name": "SLACK_WEBHOOK_URL", "type": "env", "env": "SLACK_WEBHOOK_URL"},
    {"name": "GITHUB_TOKEN", "type": "env", "env": "GITHUB_TOKEN"},
    {"name": "R2_SECRET_ACCESS_KEY", "type": "env", "env": "R2_SECRET_ACCESS_KEY"},
    {"name": "R2_ACCESS_KEY_ID", "type": "env", "env": "R2_ACCESS_KEY_ID"},
    {"name": "lambda_AWS_ACCESS_KEY_ID", "type": "env", "env": "lambda_AWS_ACCESS_KEY_ID"},
    {"name": "lambda_AWS_SECRET_ACCESS_KEY", "type": "env", "env": "lambda_AWS_SECRET_ACCESS_KEY"},
    {"name": "DOCKERHUB_USERNAME", "type": "env", "env": "DOCKERHUB_USERNAME"},
    {"name": "DOCKERHUB_TOKEN", "type": "env", "env": "DOCKERHUB_TOKEN"},
    {"name": "DOCENT_API_KEY", "type": "env", "env": "DOCENT_API_KEY"},
    {"name": "TINKER_API_KEY", "type": "env", "env": "TINKER_API_KEY"},
]


USER_FILE_SECRETS = [
    {"name": "davidh-ssh-key", "type": "file", "path": ".ssh/id_rsa"},
    {"name": "davidh-aws-creds", "type": "file", "path": ".aws/credentials"},
    {"name": "davidh_AWS_CREDENTIALS", "type": "file", "path": ".aws/credentials"},
    {"name": "davidh-aws-config", "type": "file", "path": ".aws/config"},
    {"name": "davidh_AWS_CONFIG", "type": "file", "path": ".aws/config"},
    {"name": "davidh-gcp-creds", "type": "file", "path": ".gcp/service-account.json"},
    {"name": "davidh-kaggle-creds", "type": "file", "path": ".kaggle/kaggle.json"},
]


USER_ENV_SECRETS = [
    {"name": "davidh_HF_TOKEN", "type": "env", "env": "HF_TOKEN"},
    {"name": "davidh_HF_TOKEN_READ_ONLY", "type": "env", "env": "HF_TOKEN"},
    {"name": "davidh_OPENAI_API_KEY", "type": "env", "env": "OPENAI_API_KEY"},
    {"name": "davidh_ANTHROPIC_API_KEY", "type": "env", "env": "ANTHROPIC_API_KEY"},
    {"name": "davidh_BEAKER_TOKEN", "type": "env", "env": "BEAKER_TOKEN"},
    {"name": "davidh_WANDB_API_KEY", "type": "env", "env": "WANDB_API_KEY"},
    {"name": "DAVIDH_WANDB_API_KEY", "type": "env", "env": "WANDB_API_KEY"},
    {"name": "davidh_COMET_API_KEY", "type": "env", "env": "COMET_API_KEY"},
    {"name": "DAVIDH_COMET_API_KEY", "type": "env", "env": "COMET_API_KEY"},
    {"name": "davidh_AWS_SECRET_ACCESS_KEY", "type": "env", "env": "AWS_SECRET_ACCESS_KEY"},
    {"name": "DAVIDH_AWS_SECRET_ACCESS_KEY", "type": "env", "env": "AWS_SECRET_ACCESS_KEY"},
    {"name": "davidh_AWS_ACCESS_KEY_ID", "type": "env", "env": "AWS_ACCESS_KEY_ID"},
    {"name": "DAVIDH_AWS_ACCESS_KEY_ID", "type": "env", "env": "AWS_ACCESS_KEY_ID"},
    {"name": "davidh_R2_SECRET_ACCESS_KEY", "type": "env", "env": "R2_SECRET_ACCESS_KEY"},
    {"name": "DAVIDH_R2_SECRET_ACCESS_KEY", "type": "env", "env": "R2_SECRET_ACCESS_KEY"},
    {"name": "davidh_R2_ACCESS_KEY_ID", "type": "env", "env": "R2_ACCESS_KEY_ID"},
    {"name": "DAVIDH_R2_ACCESS_KEY_ID", "type": "env", "env": "R2_ACCESS_KEY_ID"},
    {"name": "davidh_GOOGLE_API_KEY", "type": "env", "env": "GOOGLE_API_KEY"},
    {"name": "davidh_GITHUB_TOKEN", "type": "env", "env": "GITHUB_TOKEN"},
    {"name": "DAVIDH_GITHUB_TOKEN", "type": "env", "env": "GITHUB_TOKEN"},
    {"name": "lambda_AWS_ACCESS_KEY_ID", "type": "env", "env": "lambda_AWS_ACCESS_KEY_ID"},
    {"name": "lambda_AWS_SECRET_ACCESS_KEY", "type": "env", "env": "lambda_AWS_SECRET_ACCESS_KEY"},
    {"name": "davidh_DOCKERHUB_USERNAME", "type": "env", "env": "DOCKERHUB_USERNAME"},
    {"name": "DAVIDH_DOCKERHUB_USERNAME", "type": "env", "env": "DOCKERHUB_USERNAME"},
    {"name": "davidh_DOCKERHUB_TOKEN", "type": "env", "env": "DOCKERHUB_TOKEN"},
    {"name": "DAVIDH_DOCKERHUB_TOKEN", "type": "env", "env": "DOCKERHUB_TOKEN"},
    {"name": "davidh_DOCENT_API_KEY", "type": "env", "env": "DOCENT_API_KEY"},
    {"name": "DAVIDH_DOCENT_API_KEY", "type": "env", "env": "DOCENT_API_KEY"},
    {"name": "davidh_TINKER_API_KEY", "type": "env", "env": "TINKER_API_KEY"},
    {"name": "DAVIDH_TINKER_API_KEY", "type": "env", "env": "TINKER_API_KEY"},
]
