import click

from sap_ecs_log_forwarder.crypto import encrypt_value, generate_key, get_active_key
from .config import load_config, save_config

@click.group()
def cli():
    pass

@cli.command("config-path")
def config_path():
    """Show resolved config file path."""
    from sap_ecs_log_forwarder.config import CONFIG_FILE
    click.echo(str(CONFIG_FILE.resolve()))

@cli.command("set-log-file")
@click.option("--path", prompt=True, help="Path to write JSON logs (e.g., /var/log/sap-log-forwarder/app.log)")
def set_log_file(path):
    """Configure a file path to write logs. Use an empty path to disable file logging."""
    cfg = load_config()
    p = path.strip()
    if p:
        cfg["logFile"] = p
        click.echo(f"Log file set to: {p}")
    else:
        cfg.pop("logFile", None)
        click.echo("File logging disabled.")
    save_config(cfg)

@cli.group()
def input():
    pass

@input.command("add")
@click.option("--provider", type=click.Choice(["gcp","aws","azure"]), prompt=True)
@click.option("--name", prompt=True)
@click.option("--subscription", help="GCP subscription path ( Full Path - projects/{project_id}/subscriptions/{sub_name} )")
@click.option("--queue", help="AWS/Azure queue URL or name")
@click.option("--region", help="AWS region")
@click.option("--bucket", help="Bucket name (AWS/GCP)")
@click.option("--storage-account", help="Azure storage account or conn string")
@click.option("--max-retries", type=int, default=5, show_default=True)
@click.option("--retry-delay", type=int, default=10, show_default=True)
@click.option("--log-level", type=click.Choice(["DEBUG","INFO","WARNING","ERROR","CRITICAL"]), default="INFO", show_default=True, help="Log level for this input")
def add_input(provider, name, subscription, queue, region, bucket, storage_account, max_retries, retry_delay, log_level):
    cfg = _load_mutable()
    if any(i.get("name")==name for i in cfg["inputs"]):
        click.echo(f"Input '{name}' exists.")
        return
    base = {
        "provider": provider,
        "name": name,
        "maxRetries": max_retries,
        "retryDelay": retry_delay,
        "includeFilter": [],
        "excludeFilter": [],
        "outputs": [],
        "logLevel": log_level.upper(),
    }
    if provider == "gcp":
        base["subscription"] = subscription or click.prompt("GCP subscription")
        base["bucket"] = bucket or click.prompt("GCP bucket (optional)", default="")
    elif provider == "aws":
        base["queue"] = queue or click.prompt("SQS queue URL")
        base["region"] = region or click.prompt("AWS region")
        base["bucket"] = bucket or click.prompt("S3 bucket")
    elif provider == "azure":
        base["queue"] = queue or click.prompt("Azure queue name")
        base["storageAccount"] = storage_account or click.prompt("Azure storage account / conn string")
    cfg["inputs"].append(base)
    save_config(cfg)
    click.echo(f"Added input '{name}' ({provider}).")

@input.command("list")
def list_inputs():
    cfg = _load_mutable()
    if not cfg["inputs"]:
        click.echo("No inputs.")
        return
    for i in cfg["inputs"]:
        click.echo(f"- {i['name']} [{i['provider']}]")

@input.command("remove")
@click.argument("name")
def remove_input(name):
    cfg = _load_mutable()
    before = len(cfg["inputs"])
    cfg["inputs"] = [i for i in cfg["inputs"] if i.get("name") != name]
    save_config(cfg)
    if len(cfg["inputs"]) == before:
        click.echo("Not found.")
    else:
        click.echo("Removed.")

@cli.group()
def output():
    pass

@output.command("add")
@click.option("--input-name", prompt=True)
@click.option("--type", "otype", type=click.Choice(["files","http","console"]), prompt=True)
@click.option("--destination", help="For files/http")
@click.option("--compress", is_flag=True, default=False)
@click.option("--include", "include_filters", multiple=True, help="Regex include filter(s) for output (can be repeated)")
@click.option("--exclude", "exclude_filters", multiple=True, help="Regex exclude filter(s) for output (can be repeated)")
def add_output(input_name, otype, destination, compress, include_filters, exclude_filters):
    cfg = _load_mutable()
    inp = _find(cfg, input_name)
    if not inp:
        click.echo("Input not found.")
        return
    out = {"type": otype}
    if otype in ("files","http"):
        out["destination"] = destination or click.prompt("Destination")
    if otype == "files":
        out["compress"] = compress

    # Attach output-level filters if provided
    if include_filters:
        out["includeFilter"] = list(include_filters)
    if exclude_filters:
        out["excludeFilter"] = list(exclude_filters)

    if otype in ("files","http") and not out.get("destination"):
        click.echo("Destination required.")
        return
    inp.setdefault("outputs", []).append(out)
    save_config(cfg)
    click.echo("Output added.")

@output.command("list")
@click.argument("input_name")
def list_outputs(input_name):
    cfg = _load_mutable()
    inp = _find(cfg, input_name)
    if not inp:
        click.echo("Input not found.")
        return
    outs = inp.get("outputs", [])
    if not outs:
        click.echo("No outputs.")
        return
    for idx, o in enumerate(outs):
        inc = ", ".join(o.get("includeFilter", [])) or "-"
        exc = ", ".join(o.get("excludeFilter", [])) or "-"
        click.echo(f"[{idx}] {o['type']} -> {o.get('destination','')} (include: {inc}; exclude: {exc})")

@output.command("remove")
@click.option("--input-name", prompt=True)
@click.option("--index", type=int, prompt=True)
def remove_output(input_name, index):
    cfg = _load_mutable()
    inp = _find(cfg, input_name)
    if not inp:
        click.echo("Input not found.")
        return
    outs = inp.get("outputs", [])
    if not (0 <= index < len(outs)):
        click.echo("Invalid index.")
        return
    outs.pop(index)
    save_config(cfg)
    click.echo("Removed.")

@cli.command("gen-key")
def gen_key():
    key = generate_key()
    click.echo(f"Generated key: {key}")
    click.echo("Export it: export FORWARDER_ENCRYPTION_KEY='{}'".format(key))

@cli.group()
def creds():
    """Manage encrypted credentials."""
    pass

@creds.command("set-provider-auth")
@click.option("--input-name", prompt=True)
def set_provider_auth(input_name):
    cfg = _load_mutable()
    inp = _find(cfg, input_name)
    if not inp:
        click.echo("Input not found.")
        return
    provider = inp.get("provider")
    key = get_active_key()
    if not key:
        click.echo("Encryption key not set (env FORWARDER_ENCRYPTION_KEY).")
        return
    auth = {}
    if provider == "aws":
        mode = click.prompt("AWS auth mode (static/dynamic)", default="static")
        if mode == "static":
            access_key = click.prompt("AWS Access Key ID", hide_input=True)
            secret_key = click.prompt("AWS Secret Access Key", hide_input=True)
            auth["accessKeyId"] = "enc:" + encrypt_value(access_key, key)
            auth["secretAccessKey"] = "enc:" + encrypt_value(secret_key, key)
        else:
            client_id = click.prompt("Backend client_id", hide_input=True)
            client_secret = click.prompt("Backend client_secret", hide_input=True)
            login_url = click.prompt("Login URL", default="http://localhost:8000/api/v1/app/login")
            aws_creds_url = click.prompt("AWS Credentials URL", default="http://localhost:8000/api/v1/aws/credentials")
            auth["clientId"] = "enc:" + encrypt_value(client_id, key)
            auth["clientSecret"] = "enc:" + encrypt_value(client_secret, key)
            auth["loginUrl"] = login_url
            auth["awsCredsUrl"] = aws_creds_url
            click.echo("Dynamic AWS auth will request temporary credentials every ~15 minutes.")
    elif provider == "azure":
        mode = click.prompt("Azure auth mode (sas/dynamic)", default="sas")
        if mode == "sas":
            sas = click.prompt("Azure SAS Token", hide_input=True)
            auth["sasToken"] = "enc:" + encrypt_value(sas, key)
        else:
            client_id = click.prompt("Backend client_id", hide_input=True)
            client_secret = click.prompt("Backend client_secret", hide_input=True)
            login_url = click.prompt("Login URL", default="http://localhost:8000/api/v1/app/login")
            creds_url = click.prompt("Credentials URL", default="http://localhost:8000/api/v1/azure/credentials")
            # Store dynamic auth params
            auth["clientId"] = "enc:" + encrypt_value(client_id, key)
            auth["clientSecret"] = "enc:" + encrypt_value(client_secret, key)
            auth["loginUrl"] = login_url
            auth["credsUrl"] = creds_url
            click.echo("Dynamic Azure auth will request temporary SAS tokens every ~15 minutes.")
    elif provider == "gcp":
        mode = click.prompt("GCP service account JSON input mode (file/paste)", default="file")
        if mode == "file":
            path = click.prompt("Path to service account JSON file")
            try:
                with open(path, "r") as f:
                    content = f.read()
            except Exception as e:
                click.echo(f"Failed to read file: {e}")
                return
        else:
            click.echo("Paste JSON, finish with EOF (Ctrl-D):")
            try:
                import sys
                content = sys.stdin.read()
            except Exception as e:
                click.echo(f"Failed to read input: {e}")
                return
        auth["serviceAccountJson"] = "enc:" + encrypt_value(content.strip(), key)
    else:
        click.echo("Unsupported provider for auth.")
        return
    auth["encrypted"] = True
    inp["authentication"] = auth
    save_config(cfg)
    click.echo("Provider credentials stored (encrypted).")

@creds.command("set-http-auth")
@click.option("--input-name", prompt=True)
@click.option("--output-index", type=int, prompt=True)
@click.option("--auth-type", type=click.Choice(["bearer","api-key","basic"]), prompt=True)
def set_http_auth(input_name, output_index, auth_type):
    cfg = _load_mutable()
    inp = _find(cfg, input_name)
    if not inp:
        click.echo("Input not found.")
        return
    outs = inp.get("outputs", [])
    if not (0 <= output_index < len(outs)):
        click.echo("Invalid index.")
        return
    out = outs[output_index]
    if out.get("type") != "http":
        click.echo("Selected output not HTTP.")
        return
    key = get_active_key()
    if not key:
        click.echo("Encryption key not set (env FORWARDER_ENCRYPTION_KEY).")
        return
    if auth_type == "bearer":
        token = click.prompt("Bearer token", hide_input=True)
        out["authorization"] = {"type":"bearer","token":"enc:"+encrypt_value(token, key),"encrypted":True}
    elif auth_type == "api-key":
        api_key = click.prompt("API key", hide_input=True)
        out["authorization"] = {"type":"api-key","apiKey":"enc:"+encrypt_value(api_key, key),"encrypted":True}
    elif auth_type == "basic":
        user = click.prompt("Username")
        pwd = click.prompt("Password", hide_input=True)
        out["authorization"] = {
            "type":"basic",
            "user":user,
            "password":"enc:"+encrypt_value(pwd, key),
            "encrypted":True
        }
    save_config(cfg)
    click.echo("Credentials stored (encrypted).")

def _load_mutable():
    try:
        return load_config()
    except FileNotFoundError:
        return {"logLevel":"info","inputs":[]}

def _find(cfg, name):
    for i in cfg.get("inputs", []):
        if i.get("name")==name:
            return i
    return None

if __name__ == "__main__":
    cli()