# near warchest bot

*Status: super rough, APIs are subject to change*

A Python library for development of applications that are using NEAR platform.


# Install necessary packages
```bash
sudo apt-get install python3-setuptools
sudo apt-get install python3-dev
```
First, install the package in development mode:
```bash
python3 setup.py develop
```

modify line 10 in warchest.service with the actual absolute path to warchest.py

# Start service and check if it's running
Prefix commands with ```sudo ``` if necessary
```bash
cp warchest.service /etc/systemd/system/warchest.service
systemctl start warchest.service
systemctl status warchest.service
```
# Monitoring the warchest bot
```bash
systemctl status warchest.service
journalctl -u warchest.service --since today
```
# License

This repository is distributed under the terms of both the MIT license and the Apache License (Version 2.0). See LICENSE and LICENSE-APACHE for details.
