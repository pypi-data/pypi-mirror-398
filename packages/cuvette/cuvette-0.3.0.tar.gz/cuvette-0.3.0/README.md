## cuvette

a tiny wrapper around Beaker tooling. pairs well with [davidheineman/beaker_image](https://github.com/davidheineman/beaker_image).

### quick start

```sh
pip install cuvette
```

`cuvette` ❤️ `uv run`!

```sh
uv run --with cuvette blist -w ai2/davidh
```

### demo

https://github.com/user-attachments/assets/4255e0be-b29d-40a0-ae9e-364ba7c9c446

### commands

`cuvette` is mainly a bag of terminal utilities:

```sh
### hosts info ###
gpus # see free gpus
hosts # see all hosts (useful for `bl -H`)

### for session ###
bl # use interactive session launcher
bd # show current session
bs # stop current session
bport # change port for "ai2" host

### for experiments ###
bdall # show all jobs
blist # list all jobs
bstop # stop jobs
bpriority # modify priority for currently running jobs
brestart # restart failed jobs

### for environment ###
ai2code . # launch remote code
ai2cursor . # launch remote cursor
ai2cleanup # run ai2 cleaning utils

### for logs ###
blogs # get logs for job
bstream # stream logs for job
bparse # pipe logs into ChatGPT to ask about errors (requires .[openai] dependency)

### for workspaces / secrets ###
bcreate # create workspace
bsecrets # add secrets to workspace
blist # list secrets in workspace
bsync # sync secrets to workspace
```

**New!** Launch with specific hostnames using `bl -H`. E.g. `bl -H titan-cs-aus-463.reviz.ai2.in -g 0`

<details>
<summary>configuring secrets</summary>

```sh
# Make secrets files
touch secrets/.ssh/id_rsa # SSH private key (cat ~/.ssh/id_rsa)
touch secrets/.aws/credentials # AWS credentials (from 1password)
touch secrets/.aws/config # AWS config
touch secrets/.gcp/service-account.json # GCP service acct
touch secrets/.kaggle/kaggle.json # Kaggle acct

# Set secrets locally to add to Beaker
export HF_TOKEN=""
export OPENAI_API_KEY=""
export ANTHROPIC_API_KEY=""
export BEAKER_TOKEN=""
export WANDB_API_KEY=""
export COMET_API_KEY=""
export AWS_SECRET_ACCESS_KEY=""
export AWS_ACCESS_KEY_ID=""
export GOOGLE_API_KEY=""
export WEKA_ENDPOINT_URL=""
export R2_ENDPOINT_URL=""
export SLACK_WEBHOOK_URL=""

# Create your workspace
bcreate ai2/davidh

# Copy secrets to workspace
bsync ai2/davidh --all

# List secrets
blist ai2/davidh
```


</details>

### widget

MacOS toolbar extension to show free GPUs, and currently running jobs!

<p align="center">
<img width="243" alt="demo-mac-plugin" src="https://github.com/user-attachments/assets/d648a0bb-b787-45f8-b5ac-7542eeb4a654" />
</p>


<details>
<summary>widget install instructions</summary>

```sh
# install widget dependencies
pip install "cuvette[widget]"

# setup
brew install libffi
npm install -g pm2

# to test
bwidget

# to run (using a pm2 background process)
pm2 start bwidget --name "macos-widget" --interpreter python
pm2 save
pm2 startup
# pm2 list
# pm2 stop macos-widget
# pm2 restart macos-widget
```

</details>

<hr>

### todos

- [ ] `l40`, `a100`, `h100`, `b200`, `cpu`

### tips

1. Working with Cursor on remote? Add this to your `~/Library/Application Support/Cursor/User/settings.json`

```json
"remote.SSH.useLocalServer": false,
"remote.SSH.enableDynamicForwarding": true,
"remote.SSH.useExecServer": false,
"remote.SSH.lockfilesInTmp": true,
"remote.SSH.serverPickPortsFromRange": {
    "ai2": "50000-50100"
}
```
