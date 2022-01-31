"""
Libraries for cleaning scraped data
"""
import re
from datetime import timedelta, datetime
#pylint: disable=import-error
import project_constants as prc
#pylint: enable=import-error

def select_data_cleaner(site):
    """Return a control object based on the site to scrape"""
    allowed_sites = prc.ALLOWED_SITES
    cleaner = None
    if site == allowed_sites[0]:
        cleaner = BumeranCleaner()
    elif site == allowed_sites[1]:
        cleaner = ComputrabajoCleaner()
    elif site == allowed_sites[2]:
        cleaner = IndeedCleaner()
    return cleaner

class DataCleaner:
    """Class with methods that will be overriden in cleaners"""
    @classmethod
    def clean_job(cls, column_value):
        """Method for cleaning job name"""
        return column_value

    @classmethod
    def clean_company(cls, column_value):
        """Method for cleaning company name"""
        return column_value

    @classmethod
    def clean_location(cls, column_value):
        """Method for cleaning location data"""
        return column_value

    @classmethod
    def clean_date(cls, column_value):
        """Method for cleaning date info"""
        return column_value

    @classmethod
    def clean_link(cls, column_value):
        """Method for cleaning link info"""
        return column_value

class BumeranCleaner(DataCleaner):
    """Class for bumeran data cleaning"""
    monthDict = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo':5 , 'junio':6, 'julio':7, 'agosto':8,
                'setiembre':9, 'septiembre':9, 'octubre':10,
                'noviembre':11, 'diciembre':12}
    base_URL = "https://www.bumeran.com.pe"

    @classmethod
    def clean_job(cls, column_value):
        """Method for cleaning job name"""
        tmpstring = re.sub(r'\(a\)', '', column_value[0].lower().strip())
        tmpstring = re.sub(r'[^0-9a-zA-Z \u00C0-\u00FF,]+', '', tmpstring)
        tmpstring = re.sub(r' +', ' ', tmpstring)
        return tmpstring

    @classmethod
    def clean_company(cls, column_value):
        """Method for cleaning company name"""
        return column_value[0].lower().strip()

    @classmethod
    def clean_location(cls, column_value):
        """Method for cleaning location data"""
        if column_value[0] is None:
            return None
        return column_value[0].lower()

    @classmethod
    def get_lag_days(cls, split_string):
        """Auxiliary method for getting lag days"""
        len_string = len(split_string)
        lag_days = -1
        if len_string == 2:
            lag_days = (0 if split_string[1] == 'Hoy' else 1)
        elif len_string == 4:
            lag_days = int(split_string[2])
        return lag_days

    @classmethod
    def get_day_month_year(cls, split_string):
        """Auxiliary method for getting the date of a given format"""
        today = datetime.now().date()
        year = today.year
        month = cls.monthDict[split_string[4]]
        day = int(split_string[2])
        tmp = datetime(year, month, day)
        if today < tmp.date():
            tmp = datetime(tmp.year -1 , tmp.month, tmp.day)
        return tmp.date()

    @classmethod
    def clean_date(cls, column_value):
        """Method for cleaning date info"""
        today = datetime.now().date()
        tmp = re.split(' ', column_value[0])
        lag_days = cls.get_lag_days(tmp)
        return_date = None
        if lag_days >= 0:
            return_date = today - timedelta(days = lag_days)
        elif len(tmp) == 5:
            return_date = cls.get_day_month_year(tmp)
        return return_date

    @classmethod
    def clean_link(cls, column_value):
        """Method for cleaning link info"""
        return cls.base_URL + column_value[0]

class ComputrabajoCleaner(DataCleaner):
    """Class for computrabajo data cleaning"""
    monthDict = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo':5 , 'junio':6, 'julio':7, 'agosto':8,
                'setiembre':9, 'septiembre':9, 'octubre':10,
                'noviembre':11, 'diciembre':12}
    base_URL = "https://www.computrabajo.com.pe"

    @classmethod
    def clean_job(cls, column_value):
        """Method for cleaning job name"""
        tmpstring = re.sub(r'\(a\)', '', column_value[0].lower().strip())
        tmpstring = re.sub(r'[^0-9a-zA-Z \u00C0-\u00FF,]+', '', tmpstring)
        tmpstring = re.sub(r' +', ' ', tmpstring)
        return tmpstring

    @classmethod
    def clean_company(cls, column_value):
        """Method for cleaning company name"""
        company = "confidencial"
        if len(column_value) > 1:
            company = column_value[1].lower().strip()
        return company

    @classmethod
    def clean_location(cls, column_value):
        """Method for cleaning location data"""
        if len(column_value) == 1:
            location = column_value[0].split('\n')[-1].lower().strip()
        else:
            location = column_value[-1].lower().strip()
        return location

    @classmethod
    def get_lag_days(cls, split_string):
        """Auxiliary method for getting lag days"""
        lag_days = -1
        if split_string[0] == "Ayer":
            lag_days = 1
        elif split_string[0] == "Ahora":
            lag_days = 0
        elif split_string[0] == "Hace":
            if split_string[2] == "día" or split_string[2] == "días":
                lag_days = int(split_string[1])
            else:
                lag_days = 0
        return lag_days

    @classmethod
    def get_day_month_year(cls, split_string):
        """Auxiliary method for getting the date of a given format"""
        today = datetime.now().date()
        year = today.year
        month = cls.monthDict[split_string[2]]
        day = int(split_string[0])
        tmp = datetime(year, month, day)
        if today < tmp.date():
            tmp = datetime(tmp.year -1 , tmp.month, tmp.day)
        return tmp.date()

    @classmethod
    def clean_date(cls, column_value):
        """Method for cleaning date info"""
        today = datetime.now().date()
        tmp = re.split(' ', column_value[0])
        lag_days = cls.get_lag_days(tmp)
        return_date = None
        if lag_days >= 0:
            return_date = today - timedelta(days = lag_days)
        elif len(tmp) == 3:
            return_date = cls.get_day_month_year(tmp)
        else:
            #More than 30 days
            return_date = today - timedelta(days = 30)
        return return_date

    @classmethod
    def clean_link(cls, column_value):
        """Method for cleaning link info"""
        return cls.base_URL + column_value[0]

class IndeedCleaner(DataCleaner):
    """Class for indeed data cleaning"""
    monthDict = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                'mayo':5 , 'junio':6, 'julio':7, 'agosto':8,
                'setiembre':9, 'septiembre':9, 'octubre':10,
                'noviembre':11, 'diciembre':12}
    base_URL = "https://pe.indeed.com"

    @classmethod
    def clean_job(cls, column_value):
        """Method for cleaning job name"""
        return column_value[0].lower().strip()

    @classmethod
    def clean_company(cls, column_value):
        """Method for cleaning company name"""
        return column_value[0].lower().strip()

    @classmethod
    def clean_location(cls, column_value):
        """Method for cleaning location data"""
        return column_value[0].lower().strip()

    @classmethod
    def get_lag_days(cls, split_string):
        """Auxiliary method for getting lag days"""
        lag_days = None
        len_string = len(split_string)
        if len_string < 3:
            lag_days = 0
        elif split_string[1].isnumeric():
            lag_days = int(split_string[1])
        else:
            #More than 30 days.
            lag_days = 30
        return lag_days

    @classmethod
    def clean_date(cls, column_value):
        """Method for cleaning date info"""
        today = datetime.now().date()
        tmp = re.split(' ', column_value[0])
        lag_days = cls.get_lag_days(tmp)
        return_date = today - timedelta(days = lag_days)
        return return_date

    @classmethod
    def clean_link(cls, column_value):
        """Method for cleaning link info"""
        return cls.base_URL + column_value[0]
    