# GiggleSearch
Extension of Giggle to search overlapping data and connect to the UCSC gene browser with a smart view.

### First Time Setup:
We will need to install python packages and create an virtual enviroment in order to host giggle search locally. Be sure to have conda, pip, gzip, Giggle (https://github.com/ryanlayer/giggle), installed and updated.

1. Download Repo

    On macOS and Linux:
    ```unix
    git clone https://github.com/sky123martin/GiggleSearch.git
    cd GiggleSearch/
    ```

2. Create and Activate Virtual Enviorment

    ```unix
    conda install anaconda

    conda create -n search_env python=3

    conda activate search_env
    ```
3. Setup server (follow directions https://github.com/sky123martin/GiggleIndexServer)
    ```unix
    git clone https://github.com/sky123martin/GiggleIndexServer.git
    cd GiggleIndexServer
    
    git clone https://github.com/ryanlayer/giggle.git
    
    mkdir UCSC_utilities

    cd UCSC_utilities

    rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/macOSX.x86_64/bigWigToBedGraph ./

    rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/macOSX.x86_64/bigBedToBed ./

    rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/macOSX.x86_64/bigPslToPsl ./

    rsync -aP rsync://hgdownload.soe.ucsc.edu/genome/admin/exe/macOSX.x86_64/pslToBed ./

    cd ..
    cd ..
    ```

4. Install Requirements

    ```unix
    pip3 install -r ../GiggleIndexServer/requirements.txt
    pip3 install -r requirements.txt
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
