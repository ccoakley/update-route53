# update-route53
[![Build Status](https://travis-ci.com/ccoakley/update-route53.svg?branch=master)](https://travis-ci.com/ccoakley/update-route53)
[![codecov](https://codecov.io/gh/ccoakley/update-route53/branch/master/graph/badge.svg)](https://codecov.io/gh/ccoakley/update-route53)

Updates route53 for a name and IP address. This was designed to allow a machine with a floating IP address to self-update its hostname.

# To build

```bash
python3 -m venv venv
source venv/bin/activate
pip install wheel setuptools -U
python setup.py sdist bdist_wheel
```

## to install once built

```bash
deactivate
sudo pip3 install dist/update_route53-0.0.1-py3-none-any.whl
```

## To install in crontab

```bash
sudo crontab -e

## I place my env variables above the descriptive comments in the crontab
AWS_ACCESS_KEY_ID=AKIA**********
AWS_SECRET_ACCESS_KEY=********************
DNSNAME=subdomain.mydomain.com

# For more information see the manual pages of crontab(5) and cron(8)
#
# m h  dom mon dow   command
18 * * * * /usr/local/bin/update-route53 ${DNSNAME} >>/var/log/update-route53.log 2>>/var/log/update-route53.error
```

The above runs 18 minutes past the hour. Consider picking a random number
between 0-59. My old boss preferred prime number intervals between all services.
This makes your job easier if your system ever displays periodic instability.
If your periodic tasks all start on the hour, isolating the cause of problems is
slightly harder. In this case, I'm just thinking of the poor guy running the IP
echo service this code is hitting. Spread that load out.

# To test

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m unittest
```

# AWS setup

I have included an example IAM policy in `conf/aws/route53-updater-policy.json`.
I suggest creating a user that has no permissions other than this policy,
and using those permissions with the script/service. Note, do NOT ever install a
policy you haven't audited yourself. Please take a look at it and look up the
associated permissions.
