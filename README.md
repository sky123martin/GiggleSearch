# GiggleSearch
Extension of Giggle to search overlapping data and connect to the UCSC gene browser with a smart view.

### First Time Setup:
We will need to install python packages and create an virtual enviroment in order to host giggle search locally.

1. Install pip (package manager)

    On macOS and Linux:
    ```unix
    python3 -m pip install --user --upgrade pip
    ```


    On Windows:
    ```unix
    py -m pip install --upgrade pip
    ```

2. Install Virtual Enviorment

    On macOS and Linux:
    ```unix
    python3 -m pip install --user virtualenv
    ```

    On Windows:
    ```unix
    py -m pip install --user virtualenv
    ```

3. Create Virtual Enviorment

    On macOS and Linux:
    ```unix
    python3 -m venv env
    ```

    On Windows:
    ```unix
    py -m venv env
    ```


4. Activate Virtual Enviorment

    On macOS and Linux:
    ```unix
    source env/bin/activate
    ```

    On Windows:
    ```unix
    .\env\Scripts\activate
    ```

    Check Python versions:
    
    On macOS and Linux:
    ```unix
    which python
    ```

    On Windows:
    ```unix
    where python
    ```

5. Install Requirments

    ```unix
    pip install -r requirements.txt
    ```

6. Run Application
    ```unix
    export FLASK_APP=app
    flask run
    ```
7. Exit Enviorment
    ```unix
    deactivate
    ```


### Return Setup:
We will need to install python packages and create an virtual enviroment in order to host giggle search locally.

1. Activate Virtual Enviorment

    On macOS and Linux:
    ```unix
    source env/bin/activate
    ```

    On Windows:
    ```unix
    .\env\Scripts\activate
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