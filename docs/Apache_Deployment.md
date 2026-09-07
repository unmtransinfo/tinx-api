# Apache Deployment

`docker-compose.prod.yml` no longer runs nginx or certbot. TLS termination and reverse
proxying are handled by a host-level Apache, outside of Docker and outside this
repo — `api` only binds to `127.0.0.1:${TINX_API_PORT}`, and `ui` builds its static
files straight into `/var/www/tinx-ui` on the host, for Apache to serve directly.

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
