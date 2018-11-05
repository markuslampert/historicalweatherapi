import pymysql


class MySqlDBAccess:

    def __init__(self, server, user, passwd, database, input_table="", output_table=""):
        db = pymysql.connect(server, user, passwd, database)
        cursor = db.cursor()
        self.db = db
        self.cursor = cursor
        self.input_table = input_table
        self.output_table = output_table

    def close(self):
        self.db.close()
        self.cursor = None
        self.db = None
