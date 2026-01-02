class ModuleEspurna(object):
	URL_GET_RELAY="http://{ip}/api/relay/{relayNum}?apikey={apiKey}"
	URL_SET_RELAY=URL_GET_RELAY+"&value={status}"
