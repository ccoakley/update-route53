# Installing the update-route53 systemd service
This is a work in progress. Consequently, my documentation may be incorrect. I
have manually installed this service and may have skipped steps. This will be
corrected next time I wipe the server and reinstall everything. The service and
timer files included can be manually copied into `/etc/systemd/system/`. You
will need to edit the file with the appropriate values for aws access and the
DNS name. Note: The timer is currently set for 1 hour. Do not schedule more
frequently than this, as the url used for determining the public IP address is a
free service that specifically requests not to be overwhelmed with requests.

I was considering adding a standard place to drop configuration. However, after
reading [This stackoverflow answer](https://unix.stackexchange.com/a/419061), I
have decided against it. In short, systemd service files should be edited by a
sysadmin, and using EnvironmentFile or config files just splits that
configuration into multiple locations unnecessarily. As a consequence, I have
put placeholders in the service file, and a sysadmin should feel comfortable
modifying them with appropriate values.

You can run
`sudo bash install-update-route53-service.sh`
Which will copy the service file and timer file. Edit the placeholder values in
`/etc/systemd/system/update-route53.service`
At a minimum, you should set the aws key, secret key, and dns name.
Calling
`sudo systemctl enable update-route53.timer`
should create a symlink to the timer file just copied
`sudo systemctl daemon-reload`
should allow you to see the timer unit
`sudo systemctl start update-route53.timer`
should start the service.
