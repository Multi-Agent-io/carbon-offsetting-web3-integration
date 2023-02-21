"""Constants for the Web3 Carbon Offsetting Integration."""

DOMAIN = "carbon_offsetting_web3"
CONF_IP = "ip"
PLATFORMS = ["sensor"]

CONF_ENERGY_CONSUMPTION_ENTITIES = "energy_consumption_entities"
CONF_ENERGY_PRODUCTION_ENTITIES = "energy_production_entities"
CONF_ADMIN_SEED = "admin_seed_secret"
CONF_WARN_DATA_SENDING = "warn_data_sending"
CONF_IPFS_GW = "ipfs_gw"
CONF_IS_W3GW = "is_ipfs_gw_w3"
CONF_IPFS_GATEWAY_AUTH = "ipfs_gw_auth"
CONF_IPFS_GATEWAY_PWD = "ipfs_gw_pwd_secret"

IPFS_GW = "/ip4/127.0.0.1/tcp/5001/http"
AGENT_NODE_MULTIADDR = "/dns/robonomics.rpc.multi-agent.io/tcp/44440"

LAST_COMPENSATION_DATE_QUERY_TOPIC = "last_compensation_date_query"
LAST_COMPENSATION_DATE_RESPONSE_TOPIC = "last_compensation_date_response"
LIABILITY_QUERY_TOPIC = "liability_query"
LIABILITY_REPORT_TOPIC = "liability_report"
