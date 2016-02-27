#
# Regular cron jobs for the gateway package
#
0 4	* * *	root	[ -x /usr/bin/gateway_maintenance ] && /usr/bin/gateway_maintenance
