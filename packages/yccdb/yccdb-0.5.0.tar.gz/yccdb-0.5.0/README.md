# *YCCDB*
## A database api for yorkson creek coding club hosted databases
## *EXAMPLE CODE* :
### (replace `exampleToken` with db token if you want to actually do this)
### (also replace `main` with another `.db` files name you can add the `.db` extentsion but you can do it without the extension for that file but `main` is the default added file so it works.)
#### 1 (pushdb): 
```py
import yccdb as db
import time
db.pushdb("exampleToken", "time", "time", str(time.time()) )
```
#### 2 (dumpdb): 
```py
import yccdb as db
import time
db.dumpdb("exampleToken", "time", {"time": str(time.time())} )
```
#### 3 (clr):
```py
import yccdb as db
def resetUsers():
    db.clrdb("exampleToken", "users" )
```
#### 4 (deldb): 
```py
import yccdb as db
def remove(key: str):
    db.deldb("exampleToken", "Settings", key) # deletes a key in the db not the entire db lol
```
#### 5 (getdb):
```py
import yccdb as db
def get(key: str):
    return db.getdb("exampleToken", "Settings")[key]
```
#### 6 (attrdb):
```py
import yccdb as db
def created():
    return int(db.attrdb("exampleToken")["created at"])
```
#### 7 (isonline):
```py
import yccdb as db
# some code

if not db.isonline():
    print("db is not online. please check later")
    exit(0)

# some more code
```
**Keep in mind you don't _need_ to import it as db instead of the default yccdb and you can import it as anything you want**
\
*other packages by us :*
* [customTraceback](https://pypi.org/customTraceback)
* [tracelib](https://pypi.org/traceLib)
* [tracebacksilencer](https://pypi.org/tracebackSilencer)
* [coolAnsiFORMATING](https://pypi.org/coolAnsiFORMATING)
* [dynamicIO (coming soon)](https://pypkgs.bloodcircuit.org/coming-soon/dynamicIO)
* [EnCryptox (coming soon)](https://pypkgs.bloodcircuit.org/coming-soon/encryptox)
#
That's it for now...
# CREDITS:
## _Th3ou1d3x_ : Project owner. dev for backend (api links) and frontend (actual package) protocols
## _Anthony_ : Project co-owner and friend of owner. dev for backend (debugging and creating api links) and frontend (debugging actual package and creating more protocols)
### We basicly did the same thing. Anthony just did more frontend and I (Th3ou1d3x) did more backend I did like very little frontend
### - Th3ou1d3x and Anthony
## ABOUT US:
## [_Th3ou1d3x_](https://owners.bloodcircuit.org/Th3ou1d3x)
## [_Anthony_](https://owners.bloodcircuit.org/Anthony)