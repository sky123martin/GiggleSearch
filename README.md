# GiggleSearch
Extension of Giggle to search overlapping data and connect to the UCSC gene browser with a smart view.

### First Time Setup:
We will need to install python packages and create an virtual enviroment in order to host giggle search locally.

1. Install pip (package manager)

    On macOS and Linux:
    ```unix
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    rm get-pip.py
    ```

2. Create Virtual Enviorment

    On macOS and Linux:
    ```unix
    python3 -m venv env
    ```

3. Activate Virtual Enviorment

    On macOS and Linux:
    ```unix
    source ./env/bin/activate 
    ```

4. Install Requirments

    ```unix
    pip install -r requirements.txt
    ```

5. Run Application
    ```unix
    export FLASK_APP=main.py
    python -m flask run
    ```

6. Exit Enviorment
    ```unix
    deactivate
    ```

7. Delete Enviorment (optional)
    ```unix
    rm -rf env
    ```


### Return Setup:
Instructions if you have already configured env.

1. Activate Virtual Enviorment

    On macOS and Linux:
    ```unix
    source env/bin/activate
    ```

2. Run Application
    ```unix
    export FLASK_APP=app
    flask run
    ```
3. Exit Enviorment
    ```unix
    deactivate
    ```