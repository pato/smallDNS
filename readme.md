smallDNS - Simple multi-agent locally listable DNS
==================================================

Super simple DNS implementation where each machine pings the master server
with it's hostname and ip address.

The server stores keeps a locally hosted, file based, DNS map which
stores the mapping from hostnames to ip addresses.

The client scripts ping the server if they notice a change in ip address (either
from reboot or lease renewal).

Features:
* Client scripts can be deployed on multiple agents without any setup
* Server keeps track of any agents that have been added
* Client will only ping the server if a change is noticed
* Server can generate a hosts file that can be merged with `/etc/hosts`

Limitations:
* The server needs to have a static ip address that must be configured in the client script

Requirements:
* Go (server)
* Bash, wget (client)

Command Line Arguments:
* `-debug` prints debug information
* `-udp` pings with udp instead of icmp (doesn't require root, but doesn't seem to work on linux)
* `-port <port number>` serves on the specified port (default 7979)


Suggested deployment:
* Run `dnsServer.go` on server
* Set up cron job to execute `pingDNS.sh` at a reasonable interval (example in `crontab.entry`)
