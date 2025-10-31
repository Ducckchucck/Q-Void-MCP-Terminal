from korada_plugin import get_plugin

plugin = get_plugin()
plugin.init()
output = plugin.run({
    "target": "scanme.nmap.org",
    "ports": [22, 80, 443]
})
print(output)
plugin.cleanup()

