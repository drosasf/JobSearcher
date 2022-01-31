# JobSearcherV1
This is the first version of a Job Searcher/Scraper that I am building. It doesn't have some capabilities, this version is only for kicking the ball and make it roll.

# Requirements
I haven't listed them, but the main requirements are having chromium (you will need to modify the path and the user agent) and the libraries it needs. In the final version
I will take care of this to make the program useful for non programmers, but now here is a bit of it.

# Description
*****************************
DATA FRAME COLUMNS: 
    ['Job', 'Company', 'Location', 'Date', 'Link']

*****************************
About classes:
    
    class DBHandling: this is a class only used for grouping functions
        related to database (csv) load and applying the second filter
        to a dataframe.
    
    class Scraper: this is an attempt to a general scraper class, grouping
        attributes and methods common to all scrapers to develop. Also, there
        is a lot of inheritance and overriding with the intention of improving
        code reusability.
    
    class BumeranScraper: child class of Scraper. There are lots of site-
        specific variables and procedures, so it's necessary to build a class
        for each scraper. Of course, the new code should be as small as
        possible, so it uses inheritance from the Scraper class.
    
    class TestBumeranScraper: child class of BumeranScraper. There are methods
        to test the search capabilities, loop exit conditions tests to verify
        if the scraper gathers only necessary data, tests for the primary and
        secondary filters, and tests to see if webpage opening capabilities
        are working as intended. Even if here doesn't look like I need
        inheritance, if for some reason I want to overload some method with
        an equivalent with more print functions, this could be useful.

*****************************
How to use:
    
    1 - Change parameters as desired. It's recommended to not update the database
    unless you need it since scraping takes some time.
    
    2 - Execute the code with the secondary parameters you desire. The first
    secondary search (strSearch1) is an AND search, meaning that all the words 
    inside the string must be in the job name. The second search (strSearch2)
    uses an OR logic, meaning that at least one of the words must be in the job
    name. If you don't want some of them, leave them with "".
    
    3 - The program will print the resulting dataframe. If you think that is too
    big, don't load the webpages and refine the search (more ANDs or less ORs).
    
    4 - Don't worry about testing because that is for developing purposes.
        
*****************************
Program description:
    
    Of course, the code needs better cleaning and formatting, but this is a
    first out of (at least) four (which come with more websites and features),
    so it will be a bit cumbersome to use the code. Anyways, here is an attempt:
    
    1 - Define the scraping and search parameters. The variable names are self-
    explanatory, but here are some guidelines about the less intuitive ones:
        
        - mainLimDays and secLimDays: primary and secondary date filter. They
        define how much days back from today are considered in the search.
        
        - mainSearch: primary search keywords which use the website database.
        Don't be too refined with this search since web posting jobs are bad
        with this.
        
        - secSearch1 and secSearch2: secondary search keywords. I have explained
        them in the "how to use", but a remainder is always good. secSearch1 uses
        AND logic, while secSearch2 uses OR logic. If you want to ignore one or
        both, use "" as name. In any case, it's recommended to use this for the
        finer searches since the databases are already loaded in pandas (and it
        is extremely fast).
        
    2 - Populate the database with data from the main search if the boolean of
    updateDatabase is True. The main search for names uses the Bumeran search
    capabilities which has some ugly problems. This is the reason for the second
    search.
    
    3 - Load the saved database and applies the second filter, asking if you want
    to open all links in chromium. This is useful because sometimes there are too
    much links, and if you open all you will take a lot of time to manually check
    them (and also to load). About the second filter, remember that the secSearch1
    acts using AND, and the secSearch2 acts using OR. The date filter overrides
    the first date filter.
    
    4 - There is some commented out code, this is for testing purposes. You can
    change some parameters in the class if you want to test with another parameters.
