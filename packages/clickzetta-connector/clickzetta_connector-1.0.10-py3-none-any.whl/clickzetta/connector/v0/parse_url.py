import re
from sqlalchemy.engine.url import make_url
import logging

logger = logging.getLogger(__name__)

GROUP_DELIMITER = re.compile(r"\s*\,\s*")
KEY_VALUE_DELIMITER = re.compile(r"\s*\:\s*")
HTTP_PROTOCOL_DEFAULT_PORT = '80'
HTTP_PROTOCOL_PREFIX = 'http://'
HTTPS_PROTOCOL_PREFIX = 'https://'


def parse_boolean(bool_string):
    bool_string = bool_string.lower()
    if bool_string == "true":
        return True
    elif bool_string == "false":
        return False
    else:
        raise ValueError()

# origin_url example:
# clickzetta://username:password@host:port/workspace?virtualcluster=default&schema=public&magic_token=xxx&protocol=https
def parse_url(origin_url):
    url = make_url(origin_url)
    query = dict(url.query)
    port = url.port

    instance = url.host.split('.')[0]
    length = len(instance) + 1
    host = url.host[length:]
    
    path = url.database
    workspace = path
    api_in_path = False
    
    if path and '/' in path:
        path_parts = path.split('/')
        if len(path_parts) >= 2 and path_parts[0].lower() == 'api':
            workspace = path_parts[1]
            api_in_path = True
        else:
            workspace = path_parts[0]
    
    protocol = query.pop("protocol", "https")
    if protocol not in ["http", "https"]:
        raise ValueError("protocol parameter must be http or https. Other protocols are not supported yet.")
    
    protocol_prefix = HTTP_PROTOCOL_PREFIX if protocol == "http" else HTTPS_PROTOCOL_PREFIX
    service_base = f"{protocol_prefix}{host}"
    
    if port:
        service_base += f":{port}"
    
    service = f"{service_base}/api" if api_in_path else service_base

    username = url.username
    driver_name = url.drivername
    password = url.password
    token_expire_time_ms = None

    vcluster_keys = ["virtualcluster", "virtualCluster", "vcluster"]
    vcluster = None
    for key in vcluster_keys:
        if key in query:
            vcluster = query.pop(key)
            break
    
    if not vcluster:
        raise ValueError("url must have `virtualcluster` or `virtualCluster` or `vcluster` parameter.")
    
    schema = query.pop("schema", None)
    magic_token = query.pop("magic_token", None)
    if "token_expire_time_ms" in query:
        token_expire_time_ms = int(query.pop("token_expire_time_ms"))

    logger.info(f"parse the context from url: service={service}, username={username}, "
                f"driver_name={driver_name}, instance={instance}, workspace={workspace}, "
                f"vcluster={vcluster}, schema={schema}, magic_token={magic_token}, "
                f"protocol={protocol}, host={host}, token_expire_time_ms={token_expire_time_ms}, query={query}")

    return (
        service,
        username,
        driver_name,
        password,
        instance,
        workspace,
        vcluster,
        schema,
        magic_token,
        protocol,
        host,
        port,
        token_expire_time_ms,
        query,
    )


def generate_url(client):
    return (
            f"clickzetta://{client.username}:{client.password}@"
            + f"{client.instance}.{client.host}/{client.workspace}?virtualcluster={client.vcluster or 'default'}"
            + ("" if client.schema is None else f"&schema={client.schema}")
            + ("" if client.magic_token is None else f"&magic_token={client.magic_token}")
            + ("" if client.token_expire_time_ms is None else f"&token_expire_time_ms={client.token_expire_time_ms}")
            + ("" if client.protocol is None else f"&protocol={client.protocol}")
            + "".join(
        f"&{key}={value}"
        for key, value in client.extra.items()
    )
    )
