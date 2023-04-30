Mini-Aspire API
This is a mini-Aspire API built with Python Django and Django Ninja. The API allows authenticated users to go through a loan application, with fields for the required amount and loan term. Loans will be assumed to have a weekly repayment frequency, and users can submit weekly repayments.

Installation: 
For docker and docker-compose users, the installation is very straightforward. 
1. Run the docker-start.sh script. (Use chmod +x if you run into permission issues)
2. Enter the email and password for admin user. (Please not them for logging into admin user. You can create additional users if you want via docker exec -it web sh and then running python manage.py createsuperuser)
3. After building and fetching the images, the server will run. Go to your browser at localhost:8000/api/docs or 127.0.0.1:8000/api/docs to see the 
OpenAPI docs for the project.
4. Docker-compose runs two containers, Django web application and Postgres DB. 

For non-docker users:
1. create a virtual environment using python3 -m venv <your_env_name>
2. Activate the virtual environment. source <your_env_name>/bin/activate
3. Install all the required packages using pip install -r requirements.txt
4. Check the aspireAPI/settings.py file for DB settings and change as needed. 
5. Run python manage.py migrate to run database migrations on your Database. (If facing an issue, please verify you have done Step 4 correctly)
6. Run python manage.py createsuperuser to create an admin user. 
7. Run python manage.py runserver to run the development server. Navigate to localhost:8000/api/docs or 127.0.0.1:8000/api/docs to see the OpenAPI docs for the project. 

Usage: 
To use and see the APIs, the best way is to go to localhost:8000/api/docs which gives an interactive OpenAPI documentation for the project. 

Testing:
For Docker users, 
1. Go to the shell inside the web container. docker exec -it aspire_web sh
2. Run the test command. python manage.py test
    a. If you want to run the test command with code coverage, use coverage run manage.py test
    b. After the tests are complete, you can view the coverage report by executing coverage report
    c. To see the coverage report with files in an HTML format, run coverage html and then open the index.html file in the browser of your choice. 

For Non-Docker users: Run commands from step 2 inside your virtual environment.

Features: 
1. Allows Users to Apply for Loan based on Amount and term. 
2. The rounding error for non terminating decimals is handled. 
3. Only Superuser can approve/reject the Loan Application. 
4. Restrictive checks in place for safeguard of User and data safety. Ex- no repayment allowed if paid already, repayment not allowed if prior installments are pending, etc. 
5. Self descriptive OpenAPI documentation. 

Additional Sections: 

Issues you might run into: 
1. CSRF Validation Failure. This can happend on using the OpenAPI docs after logging in and out of account, since the server is unable to verify the signature after change of user authentication. 
    * Fix: Refresh the page and execute the request again. 

Further Enhancements:
1. Using environment variables for security data: Username, password, Django Secret Key etc. should be stored as env variables instead of in the codebase. 
2. Segregation of python packages and settings.py for development and production environments. 
