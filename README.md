# tinxapi

### Local Install
1. `git clone git@bitbucket.org:iterative-consulting/tinxapi.git`
2. `cd tinxapi`
3. `sudo apt-get install virtualenv libmysqlclient-dev python-dev`
4. `virtualenv env`
5. `source env/bin/activate`
6. `pip install -r requirements.txt`
7. `cd tinxapi`
8. `python manage.py migrate`
9. `python manage.py runserver`

### Launch using Docker Version

1. Install docker `sudo apt install docker.io`
2. Build the container `./build.sh`
3. Run the container `./run.sh`
4. You can use your IDE like normal and changes will be reflected without rebuilding


Navigate to http://localhost:8000







