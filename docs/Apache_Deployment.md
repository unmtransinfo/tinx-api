# Apache Deployment

`docker-compose.prod.yml` no longer runs nginx or certbot. TLS termination and reverse
proxying are handled by a host-level Apache, outside of Docker and outside this
repo — `api` only binds to `127.0.0.1:${TINX_API_PORT}`, and `ui` builds its static
files straight into `/var/www/tinx-ui` on the host, for Apache to serve directly.

This mirrors how other apps (badapple2, cfchem, ro5, tictac) are served from
`shishito.health.unm.edu` — see the
[TID-server-management](https://github.com/unmtransinfo/TID-server-management)
repo for the Ansible role that manages that Apache config.

## Production (`newdrugtargets.org` / `api.newdrugtargets.org`)

The production host isn't managed by `TID-server-management`, so this isn't
applied automatically — adapt and install by hand
(`/etc/apache2/sites-available/newdrugtargets.org.conf`), enabling `ssl`,
`headers`, `proxy`, `proxy_http`, and `rewrite`:

```apache
<VirtualHost *:80>
    ServerName newdrugtargets.org
    ServerAlias api.newdrugtargets.org
    RewriteEngine On
    RewriteCond %{REQUEST_URI} !^/.well-known/acme-challenge/
    RewriteRule ^.*$ https://%{HTTP_HOST}%{REQUEST_URI} [R=301,QSA,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName newdrugtargets.org
    SSLEngine on
    SSLCertificateFile      /etc/letsencrypt/live/newdrugtargets.org/fullchain.pem
    SSLCertificateKeyFile   /etc/letsencrypt/live/newdrugtargets.org/privkey.pem

    DocumentRoot /var/www/tinx-ui
    <Directory /var/www/tinx-ui>
        Options -Indexes +FollowSymLinks
        AllowOverride None
        Require all granted

        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule ^ index.html [L]
    </Directory>

    Header always set Strict-Transport-Security "max-age=63072000"
</VirtualHost>

<VirtualHost *:443>
    ServerName api.newdrugtargets.org
    SSLEngine on
    SSLCertificateFile      /etc/letsencrypt/live/newdrugtargets.org/fullchain.pem
    SSLCertificateKeyFile   /etc/letsencrypt/live/newdrugtargets.org/privkey.pem

    ProxyPreserveHost On
    RequestHeader set X-Forwarded-Proto "https"
    RequestHeader set X-Forwarded-For %{REMOTE_ADDR}s
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    Header always set Strict-Transport-Security "max-age=63072000"
</VirtualHost>
```

Replace `8000` with `TINX_API_PORT` if you've changed it from the default.

## Testing ground (`shishito.health.unm.edu`)

`shishito` is used to test this deployment before it goes to production, using
subdomains under the `*.shishito.health.unm.edu` wildcard cert to mirror the
prod api/root split:

- `tinx.shishito.health.unm.edu` → `/var/www/tinx-ui` (UI)
- `tinx-api.shishito.health.unm.edu` → `http://localhost:8005/` (API)

This is configured via Ansible in `TID-server-management`
(`ansible/inventory/host_vars/shishito/shishito.yml`'s `apache_additional_vhosts`,
rendered by `apache2_vhost_ssl.conf.j2`) — do not hand-edit Apache config on
`shishito` directly. When deploying `tinx-api` there, set in `.env`:

```
TINX_API_PORT=8005
BUILD_COMMAND=build-staging
API_ROOT=https://tinx-api.shishito.health.unm.edu
```

(Port `8005` avoids clashing with badapple2/cfchem/ro5/tictac's `8001`-`8004`;
adjust if `apache_additional_vhosts` on shishito is configured differently.)
