
global db_instance, connected
db_instance = None
connected = False


## Connect to db
# @param db_name database name, should fill.
# @param user_name user access name.
# @param user_pass user password.
# @param host hostname or ip addres where mongod running, default 127.0.0.1.
# @param port port number, default 27017 (mongod default port).
# @return db instance, if success then global variable `connected` is set to True.
def connect(db_name,user_name="",user_pass="",host="127.0.0.1",port=27017,config={}):
    global db_instance, connected
    if db_instance != None:
        return db_instance
    from monga import MongoDB
    db_instance = MongoDB(db_name,user_name,user_pass,host,port,config=config)
    connected = db_instance != None
    return db_instance



