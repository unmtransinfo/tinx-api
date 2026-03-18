# Tinx Migration
This is the migration guide to migrate the Tinx server initially from AWS to Chiltepin, but can be used for any future migration to other server(s).

This migration was carried out along with Elevato Digital (J. Wahl, D. Cannon, V. Metzger)

> Pre-requisites:

The tinx backend repository can be accessed [here](https://github.com/unmtransinfo/tinx-api).
The tinx frontend repository can be accessed [here](https://github.com/unmtransinfo/tinx-ui).

The backend and frontend servers run from the same docker files (docker compose), as different services.

> Please note: Currently the docker files are on branch TINX-35 on Github (frontend and backend). In case these branches are merged, change the URL in the docker-compose file (for the UI service)
>
     services:
      tinx_ui:
        build:
          context: https://github.com/unmtransinfo/tinx-ui.git#TINX-35 <------ This URL needs to be changed to the correct branch

 - All Environment variables are uploaded to Git in file named *.env.example*

## Apache Configuration on Chiltepin

> These instructions can also be used to migrate on other server than Chiltepin which runs apache web server to serve requests

The Tinx server runs on port 8000 inside the docker container. To serve this port on apache, and to redirect requests to the `BASE_URL/tinx` (BASE_URL = https://chiltepin.health.unm.edu/ in this case), the `apache.conf` file needs changes (found at /etc/apache2).

In order to separate the specific apache code for tinx, create a new file called `tinx.conf` in `sites-available` directory.

***tinx.conf***

<VirtualHost *:80>
    ServerName newdrugtargets.org
    ServerAlias test.newdrugtargets.org
    ServerAlias api.newdrugtargets.org
    ProxyPreserveHost On
    ProxyRequests Off

    # Redirect only /tinx to HTTPS
    RewriteEngine On
    RewriteCond %{HTTPS} !=on

    RewriteCond %{SERVER_PORT} ^80$
    RewriteRule ^/(.*)$ https://newdrugtargets.org/$1 [R=301,L]

    # Proxy the ACME challenge paths for Certbot
    ProxyPass /.well-known/acme-challenge/ http://localhost:8080/.well-known/acme-challenge/
    ProxyPassReverse /.well-known/acme-challenge/ http://localhost:8080/.well-known/acme-challenge/
</VirtualHost>

<VirtualHost *:443>
    SSLCertificateFile /opt/tinx/tinx-api/certbot/live/newdrugtargets.org-0003/fullchain.pem # server specific
    SSLCertificateKeyFile /opt/tinx/tinx-api/certbot/live/newdrugtargets.org-0003/privkey.pem # server specific
    ServerName newdrugtargets.org
    ServerAlias test.newdrugtargets.org
    ServerAlias api.newdrugtargets.org
    ProxyPass / http://localhost:8443/
    ProxyPassReverse / http://localhost:8443/
    ProxyRequests Off
    ProxyPreserveHost ON
</VirtualHost>

The `tinx.conf` file needs to be linked to the main `apache.conf` file. This can be done by adding the following line to `apache.conf`

    Include /etc/apache2/sites-available/tinx.conf

And finally, reload the apache server to load the new configuration using

    sudo systemctl reload apache2



## Security Note
Docker and Ubuntu do not work well together and will open ports to the public in error with out ufw knowing. https://github.com/chaifeng/ufw-docker was used to address this.