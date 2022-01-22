# CONNECTING WITH PYMYSQL: Open database connection
from melitk import melipass
from melitk.melipass import get_env



def connectBD ():
    try: 
        mysql_endpoint = melipass.get_env('DB_MYSQL_DESAENV05_MLMCONRET_MLMCONRET_ENDPOINT')
        mysql_pass = melipass.get_env('DB_MYSQL_DESAENV05_MLMCONRET_MLMCONRET_WPROD')

        mysql_host = mysql_endpoint.split(":")[0]
        mysql_port = int(mysql_endpoint.split(":")[1])
        mysql_user = 'mlmConRet_WPROD'
 
        mysql_db = get_env(mlmConRet) 
        
        return (mysql_host, mysql_port, mysql_user, mysql_pass, mysql_db)
    except Exception as error: 
        host = getJson("db_host")
        port = getJson("db_port") 
        user = getJson("db_user") 
        passwd = getJson("db_passw") 
        db = getJson("db_db")
        return (host, port, user, passwd, db)
