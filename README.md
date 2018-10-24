# tinxapi


### Database configuration

```
mysql> CREATE USER 'tcrd_read_only'@'%' IDENTIFIED BY 'tcrd_read_only';
Query OK, 0 rows affected (0.00 sec)

mysql> CREATE DATABASE tcrd;
Query OK, 1 row affected (0.00 sec)

mysql> GRANT SELECT ON tcrd.* TO 'tcrd_read_only'@'%';
Query OK, 0 rows affected (0.00 sec)

```

On a machine with the full tcrd database, you can run the script `export_tcrd_subset.sh`. This creates a file called `tcrd_subset.sql.gz` that has all of the tcrd tables needed by the TIN-X REST API.

Upload the file `tcrd_subset.sql.gz` to the same folder where you cloned `tinxapi` on the local machine / server. Then execute the following commands: 

```
$ gunzip tcrd_subset.sql.gz
$ mysql -u root -p tcrd < import_tcrd_subset.sql
```

### Launch using Docker Version

1. Install docker `sudo apt install docker.io`
2. Build the container `./build.sh`
3. Create `secrets.py` by copying `secrets.example.py` and then updating details.
4. Run the container `./run.sh`
5. You can use your IDE like normal and changes will be reflected without rebuilding


Navigate to http://localhost:8000


### Local Install (without Docker)
1. `git clone git@bitbucket.org:iterative-consulting/tinxapi.git`
2. `cd tinxapi`
3. `sudo apt-get install virtualenv libmysqlclient-dev python-dev`
4. `virtualenv env`
5. `source env/bin/activate`
6. `pip install -r requirements.txt`
7. `cd tinxapi`
8. `python manage.py migrate`
9. `python manage.py runserver`


## Troubleshooting

### Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock

```
$ sudo usermod -a -G docker $USER
$ exit
```

Then log back in again.


https://techoverflow.net/2017/03/01/solving-docker-permission-denied-while-trying-to-connect-to-the-docker-daemon-socket/


### OperationalError: Can't connect to MySQL server on '172.17.0.1' (111)

1. Edit your mysql configuration: `sudo vim /etc/mysql/mysql.conf.d/mysqld.cnf`
2. Change `bind-address` to `bind-address: 0.0.0.0`
3. Restart MySQL: `sudo service mysql restart`


## Deployments

### Confiure container to always run

1. Configure docker to run on startup: `sudo systemctl enable docker`
2. Configure tinx container to always run: `docker run -dit --restart unless-stopped -v $PWD:/tinx -p 8000:8000 -ti tinx`

