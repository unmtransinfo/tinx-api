import os
from pathlib import Path


if os.path.isfile('/run/secrets/mysql_password'):
  password = Path('/run/secrets/mysql_password').read_text()
else:
  password = os.environ['DB_PASSWORD']


tcrd = {
	'host'     : os.environ['DB_HOST'],
	'user'     : os.environ['DB_USER'],
	'password' : password
}
