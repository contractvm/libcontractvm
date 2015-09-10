import requests
import json
import sys

HEADERS = {'content-type': 'application/json'}


def doRequest (command, args = []):
	payload = {
		"method": command,
		"params": args,
		"jsonrpc": "2.0",
		"id": 0,
	}
	try:
		return requests.post('http://localhost:8181/', data=json.dumps(payload), headers=HEADERS).json()
	except:
                return requests.post('http://localhost:2819/', data=json.dumps(payload), headers=HEADERS).json()

if len (sys.argv) > 1:
	r = doRequest (sys.argv[1], sys.argv[2:])
else:
	r = doRequest ('info')

try:
	print (json.dumps(r['result'], sort_keys=True, indent=4, separators=(',', ': ')))
except:
	print (json.dumps(r['error'], sort_keys=True, indent=4, separators=(',', ': ')))

