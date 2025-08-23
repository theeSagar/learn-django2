# MPIDC Repo
This repo is User registration, token-based authentication, custom user profiles, and profile retrieval for authenticated users.

# Clone repo
$ git clone clone_url

# Create a virtual environment to install dependencies in and activate it:
## for windows 
$ python3 -m venv <myenv_name>
$ source myenv_name/bin/activate

## for ubuntu
$ virtualenv <myenv_name> 
$ source myenv_name/bin/activate

# Install the dependencies:
$ (myenv_name) pip install -r requirements.txt or pip3 install -r requirements.txt

# Run server:
$ python manage.py runserver