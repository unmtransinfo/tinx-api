# tinxapi


### Database configuration

#### 1. Create an empty database and a read-only database user:

```
mysql> CREATE USER 'tcrd_read_only'@'%' IDENTIFIED BY 'tcrd_read_only';
Query OK, 0 rows affected (0.00 sec)

mysql> CREATE DATABASE tcrd;
Query OK, 1 row affected (0.00 sec)

mysql> GRANT SELECT ON tcrd.* TO 'tcrd_read_only'@'%';
Query OK, 0 rows affected (0.00 sec)

```

####  2. (Skip this step if you have been provided a copy of the database to load.) On a machine with the full tcrd database, you can run the script `export_tcrd_subset.sh`. This creates a file called `tcrd_subset.sql.gz` that has all of the tcrd tables needed by the TIN-X REST API.

#### 3. Upload the file `tcrd_subset.sql.gz` to the same folder where you cloned `tinxapi` on the local machine / server. Then execute the following commands:

```
$ gunzip tcrd_subset.sql.gz
$ mysql -u root -p tcrd < import_tcrd_subset.sql
```

####  4. Run the script `compute_nds_rank.py`:

```
$ python compute_nds_rank.py
```

### Option 1: Launch using Docker Version (recommended)

1. Install docker `sudo apt install docker.io`
2. Build the container `./build.sh`
3. Create `secrets.py` by copying `secrets.example.py` and then updating details.
4. Run the container `./run.sh`
5. You can use your IDE like normal and changes will be reflected without rebuilding


Navigate to http://localhost:8000


### Option 2: Local Install (without Docker)
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

## Solr
You must use solr:6.6.6, Solr8 does not work correctly with Haystack.
There is a bug with django-haystack where it does not handle django_ct correctly. There is no fix for this issue presently so we are capping our version of Solr at 6.6.6 as opposed to editing core files.

If you see an issue involving django_ct or django_id, you are using the wrong version of Solr.

It is not clear to me how the managed-schema file was generated, but it is the only one that works presently, so preserve it.

I've authored scripts to redeploy solr once it is built and you can see that work in redeploy-solr.sh.

I've also created a utility script to update solr indices and that can be found in update_solr_index.sh
### Missing Schema Params

Haystack won't add all the necessary schema parameters that Solr needs to run through `./manage.py build_solr_schema`


Make the following replacement in managed-schema

```
<!-- <field name="django_ct" type="string" indexed="true" stored="true" multiValued="false"/> -->
<field name="django_ct" type="text_general" indexed="true" stored="true" multiValued="false"/>
```

Then add this block after the last <fieldtype> element

```
<!-- NRR manual insert start -->
<!-- Lines from origin managed-schema: -->
<fieldType name="pdate" class="solr.DatePointField" docValues="true"/>
<fieldType name="pdates" class="solr.DatePointField" docValues="true" multiValued="true"/>
<fieldType name="pdouble" class="solr.DoublePointField" docValues="true"/>
<fieldType name="pdoubles" class="solr.DoublePointField" docValues="true" multiValued="true"/>
<fieldType name="pfloat" class="solr.FloatPointField" docValues="true"/>
<fieldType name="pfloats" class="solr.FloatPointField" docValues="true" multiValued="true"/>
<fieldType name="pint" class="solr.IntPointField" docValues="true"/>
<fieldType name="pints" class="solr.IntPointField" docValues="true" multiValued="true"/>
<fieldType name="plong" class="solr.LongPointField" docValues="true"/>
<fieldType name="plongs" class="solr.LongPointField" docValues="true" multiValued="true"/>
<!-- NRR manual insert end -->

```

Solr-8 can now be restarted and the indexes updated through `./manage.py rebuild_index`




## Deployment

### Basic deployment (Easiest):
* Copy `.env.example` to `.env`
* Run `docker compose up`

#### Notes
* You should create a cron job to back up ./db regularly. You can tar the directory (requires stopping containers) or use mysqldump (https://dev.mysql.com/doc/refman/8.3/en/mysqldump.html) along with the mysql container. (ex: `docker compose exec mysql mysqldump [options] > dump.sql`)

### Recommended (Requires external MySql database):

* Copy `.env.example` to `.env`
* Edit .env to have connection information for an external database
* Run `docker compose up`

### Note
* The docker compose file comes with a Mysql database however, it is recommended to use an external Mysql database. To connect to an external database, copy the .env.example file to .env and edit the variables.

* If you decide to use the internal database the datastore location can be changed with DATABASE_VOLUME_PATH (default ./db)