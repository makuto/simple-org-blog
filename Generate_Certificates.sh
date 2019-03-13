#!/bin/bash
mkdir certificates
openssl req -x509 -nodes -days 365 -newkey rsa:1024 -keyout certificates/server_jupyter_based.crt.key -out certificates/server_jupyter_based.crt.pem
