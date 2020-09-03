# ccmc-swpc-cat-web


ccmc-swpc-cat-web is a new CCMC web implementation of NOAA's SWPC_CAT IDL program.  

The project page is located at the Community Coordinated Modeling Center, located at NASA Goddard Space Flight Center.

Official site page https://webserver1.ccmc.gsfc.nasa.gov/swpc_cat_web/

ccmc-swpc-cat-web source code is hosted on github under a permissive NASA open source license:

https://github.com/nasa/ccmc-swpc-cat-web/

## INSTALLATION
ccmc-swpc-cat-web is a plotly-dash based web application, the following steps will start a python simple server:

### prerequisites:
```
python3.7 already installed
virtualenv already installed
``` 

### 1. create venv using python 3.7
```
NOTE: "/usr/bin/python3.7" is an example path, you might need to change this path
virtualenv -p /usr/bin/python3.7 venv
```

### 2. install requirements.txt
```
source venv/bin/activate
pip3 install -r requirements.txt 
```

### 3. start server
```
source venv/bin/activate
python __SWPC_CAT__.py
Visit: http://127.0.0.1:8050/ in a web browser (preferably chrome)
