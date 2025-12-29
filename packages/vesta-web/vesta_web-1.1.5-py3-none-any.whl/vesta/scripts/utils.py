import subprocess
from configparser import ConfigParser


from vesta import Server
import sys
from psycopg import sql

def ex(command):
    subprocess.run(command, shell=True, check=True)

class Installer:
    def __init__(self, configFile, path):
        self.PATH = path
        self.importConf(configFile)
        self.uniauth = False
        self.name = self.config.get("server", "SERVICE_NAME").replace(" ", "_").lower()

    def installNginx(self, link=True):
        print("----NGINX----")

        if self.config.getboolean("server", "DEBUG"):
            self.editFile("misc/nginx_local", {"[PATH]": self.PATH, "[SERV-PORT]": self.config.get("server", "PORT")})
            ex("sudo cp ./misc/nginx_local_filled /etc/nginx/sites-available/" + self.name)
        else:
            try:
                self.editFile("misc/nginx_prod", {"[PATH]": self.PATH, "[SERV-PORT]": self.config.get("server", "PORT"), "[WS-PORT]": self.config.get("NOTIFICATION", "PORT")})
            except Exception:
                self.editFile("misc/nginx_prod", {"[PATH]": self.PATH, "[SERV-PORT]": self.config.get("server", "PORT")})
            ex("sudo cp ./misc/nginx_prod_filled /etc/nginx/sites-available/" + self.name)

        if not link:
            return

        ex("sudo ln -s /etc/nginx/sites-available/" + self.name + " /etc/nginx/sites-enabled/")

    def addNginxMimeType(self):
        pattern = 'application/javascript'
        new_line = 'application/javascript mjs;'
        with open('/etc/nginx/mime.types', 'r+') as f:
            lines = f.readlines()
            found = False
            for i, line in enumerate(lines):
                if pattern in line:
                    found = True
                    lines.insert(i + 1, new_line + '\n')
                    break
            if not found:
                print(f"Pattern '{pattern}' not found in {filename}.")
            else:
                f.seek(0)
                f.writelines(lines)

    def setupCrons(self):
        try:
            ex("crontab -l > crontab")
        except Exception:
            pass
        ex("echo '*/15 * * * * " + self.PATH + "/venv/bin/python3 " + self.PATH + "/crons/15mins.py' >> crontab")
        ex("echo '0 * * * * " + self.PATH + "/venv/bin/python3 " + self.PATH + "/crons/1h.py' >> crontab")
        ex("echo '0 0 * * * " + self.PATH + "/venv/bin/python3 " + self.PATH + "/crons/1day.py' >> crontab")
        ex("crontab crontab")

    def importConf(self, configFile):
        self.config = ConfigParser()
        try:
            self.config.read(configFile)
            print("config at " + configFile + " loaded")
        except Exception:
            print("please create a config file")

    def nukeNginx(self):
        ex("sudo rm /etc/nginx/sites-available/" + self.name)

    def installService(self):
        self.editFile("misc/vesta.service", {"[PATH]": self.PATH, "[SERV-PORT]": self.config.get("server", "PORT"), "[NAME]":self.config.get("server", "service_name")} )
        ex("cp ./misc/vesta.service_filled /etc/systemd/system/" + self.name + ".service")
        ex("sudo systemctl daemon-reload")
        ex("sudo systemctl enable " + self.name + ".service")
        ex("sudo systemctl start " + self.name + ".service")

    def editFile(self, file, templates):
        with open(file, "r+") as f:
            data = f.read()
            for key in templates:
                data = data.replace(key, templates[key])
        with open(file+"_filled", "w+") as f:
            f.write(data)

    # -----------------__DB METHODS__----------------- #
    def initDB(self):
        initializer = DBInitializer(path=self.PATH, configFile="/server.ini", noStart=True)
        self.uniauth = True
        if self.uniauth:
            initializer.initUniauth()
        initializer.initDB()


    def resetDB(self):
        ex("sudo -u postgres dropdb " + self.config.get("DB", "DB_NAME"))
        self.initDB()

    def createUniauth(self):
        while True:
            uniauth = input("Do you want to create a uniauth database? (y/n)")
            if uniauth.upper() == 'Y' or uniauth.upper() == 'N':
                self.uniauth = uniauth.upper()
                break

        if self.uniauth == 'Y':
            ex("sudo -u postgres createdb " + self.config.get("UNIAUTH", "DB_NAME"))

    def createDB(self):
        ex("sudo -u postgres createdb " + self.config.get("DB", "DB_NAME"))

    def createUser(self):
        ex("sudo -u postgres createuser " + self.config.get("DB", "DB_USER") + " -s --pwprompt ")


class DBInitializer(Server):
    def initUniauth(self):
        self.uniauth.initUniauth()

    def initDB(self):
        self.referenceUniauth()
        self.db.cur.execute(open(self.path + "/db/schema.sql", "r").read())
        self.db.conn.commit()

    def referenceUniauth(self):
        self.db.cur.execute("CREATE EXTENSION if not exists postgres_fdw;")
        # using sql.SQL because we cant use %s inside OPTIONS
        self.db.cur.execute(
            sql.SQL("""
    CREATE SERVER IF NOT EXISTS uniauth
    FOREIGN DATA WRAPPER postgres_fdw
    OPTIONS (host {host}, port {port}, dbname {dbname});
    """).format(
                host=sql.Literal(self.config.get('UNIAUTH', 'DB_HOST')),
                port=sql.Literal(self.config.get('UNIAUTH', 'DB_PORT')),
                dbname=sql.Literal(self.config.get('UNIAUTH', 'DB_NAME'))
            )
        )

        self.db.cur.execute(
            sql.SQL("""
    CREATE USER MAPPING IF NOT EXISTS FOR CURRENT_USER 
    SERVER uniauth
    OPTIONS (user {user}, password {password});
    """).format(
                user=sql.Literal(self.config.get('DB', 'DB_USER')),
                password=sql.Literal(self.config.get('DB', 'DB_PASSWORD'))
            )
        )
        self.db.cur.execute(
            """
            CREATE FOREIGN TABLE if not exists account (id bigserial NOT NULL)
            SERVER uniauth
            OPTIONS (schema_name 'public', table_name 'account');
            """)
