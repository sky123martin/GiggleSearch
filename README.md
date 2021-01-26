# GiggleSearch
Extension of Giggle to search overlapping data and connect to the UCSC gene browser with a smart view.

### First Time Setup:
We will need to install python packages and create an virtual enviroment in order to host giggle search locally. Be sure to have conda and pip installed and updated.

1. Install pip (package manager)

    On macOS and Linux:
    ```unix
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    rm get-pip.py
    ```

2. Create and Activate Virtual Enviorment

    ```
    conda install anaconda

    conda create -n search_env python=3

    conda activate search_env
    ```

    Install necessary python libararies
    ```
    conda install --file requirements.txt
    ```


4. Install Requirements

    ```unix
    conda install --file requirements.txt
    pip3 install -r <path to server>/requirements.txt 
    e.g. pip3 install -r ../GiggleIndexServer/requirements.txt
    ```

5. Run Application
    ```unix
    export FLASK_APP=main.py
    flask run
    ```

6. Exit Enviorment
    ```unix
    conda deactivate
    ```


### Return Setup:
Instructions if you have already configured env.

1. Activate Virtual Enviorment

    On macOS and Linux:
    ```unix
    conda activate search_env
    ```

2. Run Application
    ```unix
    export FLASK_APP=main.py
    flask run
    ```
3. Exit Enviorment
    ```unix
    conda deactivate
    ```