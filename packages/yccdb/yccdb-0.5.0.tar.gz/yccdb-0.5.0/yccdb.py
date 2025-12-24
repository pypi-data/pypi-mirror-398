import requests
import ast
def isonline():
    return requests.get("https://yorksoncoding.bloodcircuit.org/debugapi?dbg=return hello").text == "hello"
def checkfix(o:str):
    if o == "file does not exist":
        raise FileNotFoundError("file does not exist")
    if o.startswith("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <title>We are experiencing some technical difficulties</title>"):
        print("api is experiencing technical difficulties. please contact support@bloodcircuit.org")
        return False
    return True
def getdb(tkn : str, file : str = None):
    if not isonline():
        print("api is not online. please contact support@bloodcircuit.org")
        return None
    db = requests.get(f"http://yorksoncoding.bloodcircuit.org/db/__api__?req=get&tkn={tkn}&dbfile={file}")
    if checkfix(db.text):
        return None
    return ast.literal_eval(db.text)
def pushdb(tkn : str, file : str, pkey : str, pval):
    if not isonline():
        print("api is not online. please contact support@bloodcircuit.org")
        return None
    o = requests.get(f"http://yorksoncoding.bloodcircuit.org/db/__api__?req=push&tkn={tkn}&dbfile={file}&pkey={pkey}&pval={str(pval)}")
    checkfix(o.text)
def dumpdb(tkn : str, file : str, data : dict):
    if not isonline():
        print("api is not online. please contact support@bloodcircuit.org")
        return None
    o = requests.get(f"http://yorksoncoding.bloodcircuit.org/db/__api__?req=dump&tkn={tkn}&dbfile={file}&data={str(data)}")
    checkfix(o.text)
def deldb(tkn : str, file : str, dkey):
    if not isonline():
        print("api is not online. please contact support@bloodcircuit.org")
        return None
    o = requests.get(f"http://yorksoncoding.bloodcircuit.org/db/__api__?req=del&tkn={tkn}&dbfile={file}&dkey={str(dkey)}")
    checkfix(o.text)
def clrdb(tkn : str, file : str = None):
    if not isonline():
        print("api is not online. please contact support@bloodcircuit.org")
        return None
    o = requests.get(f"http://yorksoncoding.bloodcircuit.org/db/__api__?req=clr&tkn={tkn}&dbfile={file}")
    checkfix(o.text)
def attrdb(tkn : str):
    if not isonline():
        print("api is not online. please contact support@bloodcircuit.org")
        return None
    o = requests.get(f"http://yorksoncoding.bloodcircuit.org/db?gattr=true&tkn={tkn}")
    checkfix(o.text)
    return ast.literal_eval(o.text)