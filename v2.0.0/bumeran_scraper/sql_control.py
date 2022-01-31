"""
Controls the data flow between SQL database and the program
"""
import os
import sqlite3
from datetime import timedelta, datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import project_constants as prc

class SearchHelper:
    """Helper class for containing search parameters and generating
    SQL queries for searches"""
    #####################################
    ##Initialize instance of the class
    def __init__(self):
        self.max_past_days = None
        self.keywords_and = None
        self.keywords_or = None
        self.only_non_opened = None

    #####################################
    ##Generate SQL query from search parameters
    def generate_sql_query(self):
        """Generate SQL query according to search parameters"""
        query_string = ""
        #Generate query strings
        for string in self.generate_particular_query():
            if string == "":
                continue
            if query_string != "":
                query_string += "\nAND "
            query_string += string
        if query_string != "":
            query_string = "\nWHERE " + query_string
        query_string = "SELECT * FROM Data " + query_string
        return query_string

    def generate_particular_query(self):
        """Generate variable SQL query part based on parameters"""
        query_parts = list()
        query_parts.append(self.generate_date_query_string())
        query_parts += self.generate_keyword_query_string()
        if self.only_non_opened:
            query_parts.append("opened = False")
        return query_parts

    def generate_date_query_string(self):
        """Obtain date query string"""
        if self.max_past_days:
            limit_date = datetime.now().date() - timedelta(
                days = self.max_past_days)
            date_string = "date >= " + str(limit_date)
        else:
            date_string = ""
        return date_string

    @classmethod
    def generate_partial_keyword_string(cls, keywords, logic):
        """Generate partial strings based on and/or logic and an
        array of keyword"""
        keyword_string = ""
        if (not keywords) or keywords == []:
            return keyword_string
        logic_link = logic.upper().strip()
        length_keywords = len(keywords)
        for idx, keyword in enumerate(keywords):
            keyword_string += "job LIKE \"%{}%\" ".format(keyword)
            if idx+1 < length_keywords:
                keyword_string += logic_link
            keyword_string += "\n"
        keyword_string = "(" + keyword_string + ")"
        return keyword_string

    def generate_keyword_query_string(self):
        """Create keyword query strings for the and/or logic"""
        keyword_string_and = self.generate_partial_keyword_string(
            self.keywords_and, "and")
        keyword_string_or = self.generate_partial_keyword_string(
            self.keywords_or, "or")
        return [keyword_string_and, keyword_string_or]

class DBControl:
    """Class for controlling DB - I/O interaction"""
    DATABASE_PATH = r"C:\Users\PC-UVW0102\Desktop\Databases\\"[:-1]
    CHROMEDRIVER_PATH = r"C:\Program Files\chromedriver_win32\chromedriver.exe"
    USER_AGENT = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                  'AppleWebKit/537.36 (KHTML, like Gecko)',
                  ' Chrome/96.0.4664.110 Safari/537.36')

    #####################################
    ##Initialize instance of the class
    def __init__(self):
        self.db_path = None
        self.connection = None
        self.cursor = None
        self.search_params = None
        self.driver = None

    #####################################
    ##Check if database exists, connect to it and check if tables exist.
    def connect_and_check_db(self, db_name, clear = False):
        """Clear db if required, connects and check if tables are present.
        If not, it creates them."""
        self.point_or_clear_db(db_name, clear = clear)
        self.connect_to_db()
        self.create_tables(self.tables_exist())

    def point_or_clear_db(self, db_name, clear = False):
        """Load db_path attribute to point to db, and clears it on
        condition."""
        self.db_path = self.DATABASE_PATH + db_name
        if clear or not os.path.isfile(self.db_path):
            os.remove(self.db_path)

    def connect_to_db(self):
        """Connects to a DB. Creates it if don't exist or is cleared"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = lambda cursor, row: list(row)
        self.cursor = self.connection.cursor()

    def tables_exist(self):
        """Check if the required tables exist"""
        table_names = ['Data', 'Search']
        sql_query = """SELECT name FROM sqlite_master
                    WHERE type='table'
                    ORDER BY name;"""
        list_of_tables = self.cursor.execute(sql_query).fetchall()
        list_of_tables = [x[0] for x in list_of_tables]
        return [table in list_of_tables for table in table_names]

    def create_tables(self, created_status):
        """Create tables for scraping"""
        sql_queries = ["""CREATE TABLE "Data" (
                    	"id"	INTEGER,
                    	"job"	TEXT,
                    	"company"	TEXT,
                    	"location"	TEXT,
                    	"date"	TEXT,
                    	"site"	TEXT,
                    	"opened"	INTEGER,
                    	"link"	TEXT,
                    	PRIMARY KEY("id" AUTOINCREMENT));""",
                    """CREATE TABLE "Search" (
                    	"id"	INTEGER,
                    	"keyword"	TEXT,
                        "site"	TEXT,
                    	"update_date"	TEXT,
                    	PRIMARY KEY("id" AUTOINCREMENT));"""]
        for index, query in enumerate(sql_queries):
            if not created_status[index]:
                self.cursor.execute(query).fetchall()
        if sum(created_status)>0:
            self.connection.commit()

    #####################################
    ##Update Data and Search tables provided relevant data
    def update_data_tbl(self, csv_name):
        """Load csv and update data table with it"""
        dataframe = pd.read_csv(csv_name)
        dataframe.to_sql('Data', self.connection, if_exists='append',
                  index = False, chunksize = 10000)
        self.erase_duplicates_data_tbl()

    def update_search_tbl(self, keyword_dict):
        """Update search table with new dates"""
        keyword_rows = list(list(item) for item in keyword_dict.items())
        dataframe = pd.DataFrame(keyword_rows, columns=["keyword", "site"])
        dataframe['update_date'] = datetime.now().date()
        dataframe.to_sql('Search', self.connection, if_exists='append',
                  index = False, chunksize = 10000)
        self.erase_duplicates_search_tbl()

    def erase_duplicates_data_tbl(self, select_type = "min"):
        """Erase duplicates in data table"""
        sql_query = """DELETE FROM Data
                    WHERE id NOT IN (
                   	SELECT {}(id) FROM Data
                   	GROUP BY link);""".format(select_type)
        self.cursor.execute(sql_query).fetchall()
        self.connection.commit()

    def erase_duplicates_search_tbl(self):
        """Erase duplicates in search table"""
        sql_query = """DELETE FROM Search
                    WHERE id NOT IN (
                   	SELECT max(id) FROM Search
                   	GROUP BY keyword, site);"""
        self.cursor.execute(sql_query).fetchall()
        self.connection.commit()

    @classmethod
    def generate_keyword_dict(cls, keywords):
        """Create the keyword dictionary from some keywords"""
        keyword_dict = dict()
        for keyword in keywords:
            keyword_dict[keyword] = "Bumeran"
        return keyword_dict

    #####################################
    ##Search in Data table for keywords and dates using SQL
    def search_in_data_tbl(self, max_past_days, keywords_and,
                           keywords_or, only_non_opened = True):
        """Search in data table and return a dataframe"""
        #Initialize attributes
        self.search_params = SearchHelper()
        self.search_params.max_past_days = max_past_days
        self.search_params.keywords_and = keywords_and
        self.search_params.keywords_or = keywords_or
        self.search_params.only_non_opened = only_non_opened
        #Create query
        sql_query = self.search_params.generate_sql_query()
        data_list = self.cursor.execute(sql_query).fetchall()
        if data_list:
            dataframe = self.format_searched_data(data_list)
        else:
            dataframe = None
        return dataframe

    def format_searched_data(self, data_list):
        """Change the format from rows of data to a dataframe
        with named columns"""
        dataframe = pd.DataFrame(data_list)
        dataframe.columns = self.get_column_names("Data")
        return dataframe

    def get_column_names(self, table_name):
        """Get coluumn names for a table in the database"""
        sql_query = "PRAGMA table_info({});".format(table_name)
        column_names = self.cursor.execute(sql_query).fetchall()
        return [item[1] for item in column_names]

    #####################################
    ##Open data in driver and update database with opened data
    def open_search_results(self):
        """Get search results from DB and asks if you will open them"""
        dataframe = self.search_in_data_tbl(prc.MAX_PAST_DAYS,
                                           prc.KEYWORDS_AND,
                                           prc.KEYWORDS_OR,
                                           only_non_opened=prc.ONLY_NON_OPENED)
        if dataframe is None or dataframe.empty:
            print("No matches were found")
        else:
            print("Matches for the search: ", len(dataframe))
            open_links = "N"
            open_links = input("Open links? [Y/N]: ")
            if open_links.lower() == "y":
                self.open_data_in_driver(dataframe)

    def open_data_in_driver(self, dataframe):
        """Open selenium chromedriver with links of dataframe"""
        options = Options()
        options.headless = False
        user_agent = self.USER_AGENT
        options.add_argument('--disable-infobars')
        options.add_argument(f'user-agent={user_agent}')
        self.driver = webdriver.Chrome(self.CHROMEDRIVER_PATH,
                                       options=options)
        for link in dataframe['link']:
            self.driver.get(link)
            self.driver.execute_script("window.open('');")
            tab_list = self.driver.window_handles
            self.driver.switch_to.window(tab_list[-1])
        if len(self.driver.window_handles) == len(dataframe) + 1:
            self.update_opened_data(dataframe)

    def update_opened_data(self, dataframe):
        """Update opened data status in DB"""
        dataframe['opened'] = True
        dataframe.drop(['id'], axis=1, inplace=True)
        dataframe.to_sql('Data', self.connection, if_exists='append',
                  index = False, chunksize = 10000)
        self.erase_duplicates_data_tbl(select_type="max")

if __name__ == "__main__" :
    #DB creation and update
    dbc = DBControl()
    dbc.connect_and_check_db(prc.DB_NAME, clear = False)
    if prc.UPDATE_DB:
        dbc.update_data_tbl(prc.CSV_NAME)
        dbc.update_search_tbl(dbc.generate_keyword_dict(prc.KEYWORDS))
    #Search in DB - Parameters and conversion
    df = dbc.search_in_data_tbl(prc.MAX_PAST_DAYS,prc.KEYWORDS_AND,
                        prc.KEYWORDS_OR, only_non_opened=prc.ONLY_NON_OPENED)
    if df is None or df.empty:
        print("No matches were found")
    else:
        print("Matches for the search: ", len(df))
        OPEN_LINKS = "N"
        OPEN_LINKS = input("Open links? [Y/N]: ")
        if OPEN_LINKS.lower() == "y":
            dbc.open_data_in_driver(df)
    dbc.connection.close()
    