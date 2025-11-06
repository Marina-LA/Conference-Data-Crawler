<br/>
<div align="center">
    <img src="logo.png" alt="Logo" width="500">
</div>
<br/>
<br>
<br>
<br>

<div align="center"><strong>This crawler obtains the data using <a href="https://dblp.org">DBLP</a>, <a href="https://openalex.org">OpenAlex</a> and <a href="https://www.semanticscholar.org">Semantic Scholar</a></strong></div>

<br>
<br>

# Conference Data Crawler

This crawler is composed of three different crawlers, each of which extracts different data that complements each other.

- **Base Crawler:** Extracts the main data from papers published in a conference. This data is extracted using DBLP and OpenAlex.
- **Extended Crawler:** Extracts data related to cited papers and abstracts among others. The data is extracted from Semantic Scholar (and OpenAlex in certain specific cases).
- **Citations Crawler:** Given the citations extracted with the extended crawler, it extracts information related to the cited papers (authors affiliations, year published, etc.).

## Required Libraries

You can install the required libraries for the project using the following command.

```console
pip install -r requirements.txt
```

## How to run the crawler?

**The crawler can be executed in two different ways: via code or via command.**

If you want to run it via code, you can modify the `main.py` file, where there is currently a small example of how to corretly run the three crawlers.

If you want to execute the crawler via command line, you can usa a command with the following structure:

```console
python ./crawler_cli.py --c {conference/s} --y {year/s} [--extended] [--citations] 
```

Here's some examples:

```console
python ./crawler_cli.py --c middleware cloud --y 2015 2020 --extended 
```

Fetch the data for the middleware and SoCC conferences from 2015 to 2020. Use the **extended crawler**.

```console
python ./crawler_cli.py --c nsdi --y 2023 
```

Get the data for USENIX NSDI from the year 2023. It will use the **base crawler**.

### Arguments

- `--c` The name or names of the conferences from which crawling is desired.
- `--y` The range of years from which data is desired. The first year must be lower than the second. You can only provide one year.
- `--extended` A flag indicating whether to use the extended crawler.
- `--citations` A flag indicating whether to use the citations crawler.

The arguments `--c` and `--y` are mandatory. On the other hand, the arguments `--extended` and `--citations` are used to indicate which crawler you want to use. If neither of these two is specified, the **base crawler** will be used as default.

## Configuration

This file contains all the constants used throughout the crawler, which configure several key aspects of it. It is important to review this file if you wish to modify the behavior of the crawler. 

### Semantic Scholar API Key

In order to achieve a higher rate limit with Semantic Scholar, it is necessary to use an API Key. Semantic Scholar provides them for free upon filling out this [form](https://www.semanticscholar.org/product/api#api-key-form).

You can also use the crawler without an API key, but it should be noted that the request limits are quite low, so they may cause issues.

To use an API_KEY, you need to create a `.env` file in the main directory of the project. Inside this file, you should create the field `SEMANTIC_SCHOLAR_API_KEY` and set the value to the key that Semantic Scholar has assigned to you upon filling out the form.

Here is a small example of how you should do it:

```console
SEMANTIC_SCHOLAR_API_KEY="you_key_here" 
```

## Data Directory

In this folder, the data obtained through the crawler will be stored. All data is saved in JSON files.

This directory contains three other directories, ``base_crawler_data``, ``extended_crawler_data`` and ``citations_crawler_data``. Inside each of these directories are the JSON files that store the dates extracted with the crawlers.

**Note:** If crawling is performed for different years of the same conference at separate times, the data for these years will be written into the existing file (for that conference), meaning no new file will be created. If crawling is performed for a year of a conference that is already written in the file (crawling was done previously), that year will be overwritten. The only time new files are created is the first time crawling is done for the conference.

### Base Crawler Data

In this directory, the JSON files obtained using the base crawler are stored. If the extended crawler is used, files will also be placed in this directory.

The data files in these directories have this naming format ``{conf}_base_data.json``, and the data follows this format:

```json
{
    "20XX": [
        {
            "Title": "The title here",
            "Year": "1999",
            "DOI Number": "10.1111/12345.12345",
            "OpenAlex Link": "https://api.openalex.org/works/", 
            "Authors and Institutions": [
                {
                    "Author": "Author Name 1",
                    "Institutions": [
                        {
                            "Institution Name": "Institution Name here",
                            "Country": "Country Code ISO-2 here"
                        }
                    ]
                },
                {
                    "Author": "Author Name 2",
                    "Institutions": [
                        {
                            "Institution Name": "Institution Name here",
                            "Country": "Country Code ISO-2 here"
                        }
                    ]
                }
            ]
        }
    ]
}
```

### Extended Crawler Data

The data files in these directories have this naming format ``{conf}_extended_data.json``, and the data follows this format:

```json
{
    "20XX": [{
                "Title": "Paper title here",
                "Year": "1999",
                "DOI Number": "10.1111/12345.12345",
                "OpenAlex Link": "https://api.openalex.org/works/",
                "Authors and Institutions": [
                    {
                        "Author": "Author Name 1",
                        "Institutions": [
                            {
                                "Institution Name": "Institution Name here",
                                "Country": "Country Code ISO-2 here"
                            }
                        ]
                    },
                    {
                        "Author": "Author Name 2",
                        "Institutions": [
                            {
                                "Institution Name": "Institution Name here",
                                "Country": "Country Code ISO-2 here"
                            }
                        ]
                    }
                ],
                "S2 Paper ID": "abcdefghijklmnopqrstuvwxyz0123456789",
                "Abstract": "Paper abstract here",
                "TLDR": "Semantic Scholar TLDR here",
                "Citations S2": [
                    {
                        "paperId": "12345678910abcdefghijklmnopqrstuvwxyz",
                        "title": "Cited paper title here"
                    },
                    {
                        "paperId": "12345678910abcdefghijklmnopqrstuvwxyz",
                        "title": "Cited paper title here"
                    },
                    {
                        "paperId": "12345678910abcdefghijklmnopqrstuvwxyz",
                        "title": "Cited paper title here"
                    }
                ]
            }
        ]
    }
```

### Citations Crawler Data

In this directory, the JSON files obtained using the citations crawler are stored. If the extended crawler is used, files will also be placed in this directory.

The data files in these directories have this naming format ``{conf}_citations_data.json``, and the data follows this format:

```json
{
    "Title Paper Citing 1": [
        {
            "Title": "Title Cited Paper 1",
            "DOI Number": "10.1111/12345.12345",
            "Venue": "Venue Name here",
            "Year": "1999",
            "Authors": [
                {
                    "Author": "Author Name 1",
                    "Institutions": [
                        {
                            "Institution Name": "Institution Name here",
                            "Country": "Country Code ISO-2 here"
                        }
                    ]
                },
                {
                    "Author": "Author Name 2",
                    "Institutions": [
                        {
                            "Institution Name": "Institution Name here",
                            "Country": "Country Code ISO-2 here"
                        }
                    ]
                }
            ]
        },
        {
            "Title": "Title Cited Paper 2",
            "DOI Number": "10.1111/12345.12345",
            "Venue": "Venue Name here",
            "Year": "1999",
            "Authors": [
                {
                    "Author": "Author Name 1",
                    "Institutions": [
                        {
                            "Institution Name": "Institution Name here",
                            "Country": "Country Code ISO-2 here"
                        }
                    ]
                }
            ]s
        } 
    ]
}
```

## Log Folder

In this folder, we find two files, ``logging_config.py`` is responsible for configuring the log, and ``crawler.log`` will store information about any possible errors that may occur during the execution of the crawler. They can be modified to adapt them to each user's needs.

## Adding a new conference

If you want to crawl a certain conference, you need to simply go to dblp and search for the conference.
Then you will have to extract the name that this conference has on its link.

For example:

``dblp.org/db/conf/<THIS_IS_THE_NAME_YOU_WILL_NEED>/index.html``

``https://dblp.org/db/conf/middleware/index.html`` for Middleware is simply middleware``

``https://dblp.org/db/conf/cloud/index.html``  for Socc (Symposium on Cloud Computing) is cloud``

**Important:** We also need to consider the link that contains the papers for each year because there are conferences where the name changes in this link. Therefore, the `verify_link` function located in the `base_crawler.py` file should be modified to include a condition that takes into account this new name. SoCC presents this case, as it needs to be searched with the name 'cloud', as shown above, but for this link, it needs to be searched by the name 'socc'.

## Data Extracted

This crawler has been used to obtain information related to conferences in the field of Computer Science.

## License

This project is available under the MIT License.
