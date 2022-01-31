# JobSearcherv3
There are some improvements with respect to V2, enough to make
the previous version irrelevant, so I'm not listing them.
This is the first "production-ready" version, and I'm using it
twice a day for automated job searching without troubles.

# Requirements
This is something that needs to be done at some point, it couldn't
be called production ready if I am the only one using it. Anyways,
for now, there are no plans on creating some windows package, GUI or
something useful for others. The general requirements are:
- Selenium
- Scrapy
- Sqlite3
- Pandas
- Chromedriver

# Description
*****************************
## About the tables in DB:
- Data (Columns: ['id', 'job', 'company', 'location', 'date', 'site', 'opened', 'link'])
- Search (Columns: ['id', 'keyword', 'site', 'update_date']
*****************************
## How to use it:
After modifying project_constants with the settings you want, you need to call main.py. Once with
the right settings, you will not need to modify project_constants. About project constants:
- The database search parameters is in the "Search parameters" section. There are two arrays of
keywords with the OR logic (Ignore the KEYWORD_AND name, it's another OR), linked by AND. Also,
the ONLY_NON_OPENED constant is for testing purposes, so leave it as is.
- The "Scraping parameters" are for database update. Since I'm executing this program twice a day, I only
need to search for jobs from one day ago. If you execute it with less frequency, you should modify the
date limit. KEYWORDS are self-explanatory.
- About the booleans on the "Database parameters" section, they are for program control. The first one is
for normal operation (scrape, update, and search), the second for only scraping and update, and the third
one for only search.
- The other constants are related to the program. Their names are self-explanatory.
*****************************
## About scripts:
The code is well documented and self-explanatory, so I'm not going in depth. The folders and scripts
are the following:
- main.py: Calls all the relevant functions based on the control of project_constants.py. Creates a
thread for each of the job posting websites, searching all the keywords in each one of them.
- project_constants.py: The parameters for main.py and other scripts in this project. They must be
modified here, so you don't need to modify main.py.
- items.csv: Temporary CSV that collects the scrapy output before uploading it to the database.
- utils/: folder with tools for the program, like Selenium webpage control, sqlite3 database control,
and tools for data cleaning for the three websites.
- site_scraper/: scrapy project. Almost all the files are auto-generated, except for the ones I will
list after this (auto-generated but modified).
- site_scraper/items.py: has the fields for the csv output, the same of the Data table (except for the auto-
generated id column).
- site_scraper/spiders/basic.py: performs a fake call to begin parsing each of the webpages and keywords.
Something that could be useful for others is that parameters can be passed to the spider with an extra
argument on process creation (main.py - basic.py - self.parameters).
- site_scraper/pipelines: when an item gets out of the basic.py, it is sent to the pipeline. In this pipeline,
I perform data cleaning.

Something noteworthy is that the amount of code is greatly reduced due to class structure. I could add some
extra websites, but right now I have accomplished my purpose and I'm going for other projects until I have a
reason to update/retake/improve this project.
