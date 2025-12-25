# SLR Query Tester 

SLR Query Tester is a Python toolkit to assist researchers in conducting Systematic Literature Reviews (SLRs) by testing and managing queries across multiple bibliographic databases. It streamlines the process of translating common queries into database-specific syntax, fetching and caching results, comparing them against a golden solution, and generating comprehensive reports.

If you use this tool, you are required to cite it as: 

```
Rakshit Mittal, "SLRQueryTester: A Toolkit to Test Queries for SLRs" (2025) arXiv
```

## Table of Contents 
 
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Git Integration](#git-integration)
- [Report Generation](#report-generation)
- [Caching](#caching)
- [Disclaimer](#disclaimer)
- [Notes](#notes)
- [License](#license)

<!-- start omit -->
### Further resources:

- [Common Query Language Specification](docs/language.md)
- [Language Translation](docs/translation.md)
- [APIs, Querying, Rate Limits](docs/api.md)
- [Reports and Comparison of Entries](docs/reports.md)
<!-- end omit -->

---

## Features 
 
- **Multiple Database Support:**  Query various bibliographic databases such as Scopus, IEEE, OpenAlex, Springer, and more.
 
- **Query Translation:**  Automatically translates common query strings into database-specific syntax.
 
- **Caching Mechanism:**  Caches API responses to minimize redundant calls and manage data efficiently.
 
- **Enhanced Query Decomposition:**  Decomposes complex queries into executable subqueries and also merges the result as per the original query. (incomplete feature)
 
- **Golden Solution Comparison:**  Compares fetched results against a golden solution to identify matches using fuzzy logic while using the multiprocessing framework to reduce time taken.
 
- **Comprehensive Reporting:**  Generates detailed CSV reports, including a main report and secondary reports for each query.
 
- **Git Integration:**  Automatically commits and pushes cache updates to your Git repository, maintaining version control of cached data, and allowing multiple researchers to pool data from traditionally rate-limited APIs, enabled by the design of the cache management methods.

---

## Installation

### 1. **Using `pip` (Recommended)**

Ensure you have [Python](https://www.python.org/downloads/) installed (version 3.7 or higher is recommended).

```bash
pip install slrquerytester
```
### 2. **Installing from Git** 

If you want the latest development version:


```bash
pip install git+https://gitlab.rakshitmittal.net/rmittal/slrquerytester.git
```
### 3. **Setting Up a Virtual Environment (Optional but Recommended)** 
Creating a virtual environment helps manage dependencies and avoid conflicts.


```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Then proceed with the installation steps above.

---

## Configuration 

SLR Query Tester uses a configuration file (`config.json`) to manage settings. The idea is that each SLR project has a unique configuration file. Ensure that you create and properly configure this file before running the tool. Example `config.json`

```json
{
  "api_keys": {
    "CORE": "YOUR_CORE_API_KEY",
    "Dimensions": "YOUR_DIMENSIONS_API_KEY",
    "IEEE": "YOUR_IEEE_API_KEY",
    "LENS": "YOUR_LENS_API_KEY",
    "OpenAlex": "YOUR_EMAIL_FOR_OPENALEX_API",
    "Scopus-Free": "YOUR_FREE_SCOPUS_API_KEY",
    "Scopus-Premium": "YOUR_PREMIUM_SCOPUS_API_KEY",
    "Springer-Free": "YOUR_FREE_SPRINGER_API_KEY",
    "Springer-Premium": "YOUR_PREMIUM_SPRINGER_API_KEY",
    "WOS": "YOUR_WOS_API_KEY"
  },
  "repository": "/absolute/path/to/repository",
  "threshold_days": 30
}
```
or
```json
{
  "api_keys": {
    "CORE": "YOUR_CORE_API_KEY",
    "Dimensions": "YOUR_DIMENSIONS_API_KEY",
  },
  "cache_directory": "/absolute/path/to/directory",
  "golden_solution_directory": "/absolute/path/to/directory",
  "report_directory": "/absolute/path/to/directory",
  "queries_file": "/absolute/path/to/file",
  "threshold_days": 30
}
```

Only specify the API keys that you have! Notice the difference, either specifying the 'repository' or all the other directory paths.
### Configuration Fields 
 
- **`api_keys`** : `dict[str,str]`: (not required for `--report`, but required for `--query`)
  - **`CORE`** : `str`: API key for [CORE API](https://core.ac.uk/services/api).
  - **`Dimensions`** : `str`: API key for [Dimensions Analytics API](https://api-lab.dimensions.ai/index.html). (created according to spec but not tested due to lack of API key)
  - **`IEEE`** : `str` : API key for [IEEE Metadata Search API](https://developer.ieee.org/docs/read/Home). (created according to spec but not tested due to lack of API key)
  - **`OpenAlex`** : `str` : Email address for [OpenAlex API Polite pool](https://docs.openalex.org/how-to-use-the-api/api-overview).
  - **`Scopus-Free`** : `str` : Free API key for [Elsevier Scopus Search API](https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl).
  - **`Scopus-Premium`** : `str` : Premium API key for [Elsevier Scopus Search API](https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl).
  - **`Springer-Free`** : `str` : Free API key for [Springer Meta/v2 API](https://docs-dev.springernature.com/docs/#api-endpoints/meta-api).
  - **`Springer-Premium`** : `str` : Premium API key for [Springer Meta/v2 API](https://docs-dev.springernature.com/docs/#api-endpoints/meta-api).
  - **`WOS`** : `str` : API key for [Clarivate Web of Science API Expanded](https://developer.clarivate.com/apis/wos).
 
- **`cache_directory`**  : `str` (required) : Absolute path to directory where cached API responses and related data are stored.
 
- **`golden_solution_directory`** : `str` (required) : Absolute path to directory containing the golden solution file/s (BibTeX only with `.bib` or `.bibtex` extension) against which results will be compared.

- **`queries_file`** : `str` (required) : Absolute path to the `queries.json` file containing the list of queries and their decomposition levels. 

- **`report_directory`** : `str` (required) : Absolute path to directory where generated reports will be saved.

- **`maual_articles_directory`** : `str` (required for `--manual`) : Absolute path to directory where manually obtained results are saved in a specific format.

- **`repository_path`** : `str` (not required, recommended) : Absolute path to the top-level project directory. **You cannot use this with other file path specifications, or the tool will return an error.** If you do specify a repository path, the default file-paths will be as follows:
  - `cache_directory = repository_path + 'slrquerytester.cache/'`
  - `golden_solution_directory = repository_path + 'golden_solution/'`
  - `report_directory = repository_path + 'reports/'`
  - `queries_file = repository_path + 'queries.json'`
  - `manual_aricles_directory = repository_path + 'manual_articles/'`

- **`threshold_days`** : `int`  (default = 100) : Number of days after which cached results are considered stale and need to be refreshed.

- **`language`** : `str` (default = "en") : Language tag that can be interpreted by [langcodes](https://pypi.org/project/langcodes/). You may use this to filter results to a specific language.
 
#### Example `queries.json`

```json
[
    {
        "query": "machine learning AND (deep learning OR neural networks) AND publication_year>=2020",
        "decomposition_level": 2
    },
    {
        "query": "data mining OR big data NOT (social media)",
        "decomposition_level": 1
    }
]
```
 
- **`query`** : The query string to be executed, in the common query language.
 
- **`decomposition_level`** : The level of decomposition for complex queries. Higher values enable deeper decomposition.

**Note:**  Ensure that all paths specified in the `config.json` file exist or can be created by the tool. Adjust file permissions as necessary to allow read/write operations in the designated directories.

---

## Usage 

After installation and configuration, you can run SLR Query Tester using the command-line interface (CLI).

### Basic Command 


```bash
slrquerytester --config path/to/config.json [options]
```

### Available Options 
 
- **`--config`** : Path (relative to cwd) to the configuration JSON file. Required unless you enable the `--docs` flag. **Default:**  `config.json`
 
- **`--query`** : If set, query databases and cache results.

- **`--manual`** : If set, cache manually obtained articles.

- **`--report`** : If set, generate reports.

- **`--output_merge`** : If set with `--report`, cache the merged/union results from all databases for each query. The union articles are stored in a special `slrquerytester-union` directory within the cache. Can only be used when `--report` is also set.

- **`--git`** : If set, automatically commit and push cache updates to the specified Git repository. **requires** `repository_path` in configuration.
 
- **`--debug`** : If set, output debug-level logs for more detailed information.

- **`--docs`** : If set, generate documentation using pdoc and open the browser.

### Examples 
 
1. **Query Databases and Generate Reports (without Saving the Union)** 

```bash
slrquerytester --config config.json --query --report
```
 
2. **Query Databases, Generate Reports (without Saving the Union), and Push to Git** 

```bash
slrquerytester --config config.json --query --report --git
```
 
3. **Generate Reports and Cache Union Results** 

```bash
slrquerytester --config config.json --report --output_merge
```

4. **Regenerate Reports Without Querying Databases or Saving the Union** 

```bash
slrquerytester --config config.json --report
```

5. **Generate and View Documentation** 

```bash
slrquerytester --docs
```

6. **Cache Manually Obtained Articles** 

```bash
slrquerytester --manual
```

---

## Cache Manual Articles

It may be the case, that you have to manually extract articles using the Web UI of the bibliographic databases (like ACM-DL), or from another tool, in bib format. In that case, you can specify the `manual_articles_directory` or simply populate the default in the `repository` according to a precise structure:

```
manual_articles_directory
├── <random_hash_or_query_number>
│   ├── <database_name>
│   │   ├── metadata.json
│   │   ├── results.bib
│   │   └── results2.bib (any random name and number of bib files)
│   ├── <database_name>
│   │   ├── metadata.json
│   │   └── results.bib
│   └── ...
├── <random_hash_or_query_number>
│   ├── <database_name>
│   │   ├── metadata.json
│   │   └── results.bib
│   └── ...
└── ...
```
It is very important to be consistent with the database_names in the sub-directories.

Each `metadata.json` should be a dictionary with a single key, value pair: 
```json
{
  "general_query_string": "query_in_general_query_syntax"
}
```

---

## Git Integration 

SLR Query Tester can automatically commit and push cache updates to a Git repository, ensuring version control of your cached data.

### How It Works 
 
1. **Appending Commit Messages:**  
  - Whenever new data is added to the cache via API calls, a commit message is appended to `git_commit_message.txt` located in the `repository_path`.
 
2. **Committing and Pushing:**  
  - If the `--git` flag is set, the tool stages all changes, commits them using the messages in `git_commit_message.txt`, and pushes the commit to the remote repository.
 
  - Upon a successful push, the `git_commit_message.txt` file is deleted to prevent duplicate commits.

### Important Notes 
 
- **Repository Path:** 
Ensure that the `repository_path` in your `config.json` points to the root of your Git repository.
 
- **Git Authentication:** 
Make sure your Git repository is properly authenticated to allow push operations. This may involve setting up SSH keys or configuring credential helpers.
 
- **Commit Message File Location:** 
The `git_commit_message.txt` file is located in the `repository_path` and is not part of the cache, ensuring easy retrieval and management.

---

## Report Generation 

SLR Query Tester generates detailed reports summarizing the results of your queries and their comparison against the golden solution.

### Main Report (`main.csv`) 
- **Location:** Saved in the `report_directory`.
- **Context:** provides the data for each performed query, so also the decomposed sub-queries, and the queries specified in `queries.json`
- **Contents for each query:**  
  - **Serial Number:**  Unique identifier for each query.
 
  - **Query String:**  The original query string.
 
  - **For Each Database:**  
    - **Translated Query:**  The database-specific version of the query.
 
    - **Articles Retrieved:**  Number of articles fetched from the database.
 
    - **Golden Matches:**  Number of articles matching the golden solution.
 
  - **Total Unique Articles:**  Combined unique articles from all databases.
 
  - **Total Golden Matches:**  Combined matches across all databases.

### Secondary Reports (`1.csv`, `2.csv`, etc.) 
- **Location:** 
Saved in the `report_directory`, named after the serial number corresponding to each query in the main report.
 
- **Contents:**  
  - **First Column:**  Article titles from the golden solution.
 
  - **Subsequent Columns:**  Each database name.
 
  - **Cells:**  Indicates 'Yes' if the article is present in the database's results, 'No' otherwise.

### Viewing the Reports 
 
1. **Main Report:** Open `main.csv` in your preferred spreadsheet application to view an overview of all queries and their results across databases.
 
2. **Secondary Reports:** Open individual CSV files (e.g., `1.csv`) to see detailed comparisons for each query, showing which golden solution articles were retrieved by each database.

---

## Article Duplicate Detection

When merging articles from multiple databases (both for union generation and golden solution comparison), SLR Query Tester uses a sophisticated multi-step duplicate detection algorithm to identify and eliminate duplicate entries:

### Detection Algorithm

1. **Exact Key Matching**: Articles with identical BibTeX keys are considered duplicates.

2. **DOI-based Matching**: Articles are compared using their Digital Object Identifiers (DOIs). DOIs are normalized (lowercased and trimmed) before comparison to handle formatting variations.

3. **Fuzzy Text Matching**: For articles without DOIs or with non-matching DOIs, the tool uses fuzzy string matching on normalized article metadata.

### Fuzzy Matching Process

The fuzzy matching algorithm:

1. **Normalization**: Article fields are extracted in alphabetical order (author, title, year) and normalized by:
   - Converting to lowercase
   - Removing special characters and punctuation
   - Expanding journal abbreviations using the JabRef abbreviation database
   - Stripping extra whitespace
   - Combining into format: `"author: <author> | title: <title> | year: <year>"`

2. **Similarity Scoring**: Uses the Levenshtein distance-based ratio from the `fuzzywuzzy` library to compute similarity scores (0-100).

3. **Threshold**: Articles with a similarity score above **75%** are considered duplicates.

*Note: For performance optimization, articles are grouped into blocks based on the first 10 characters of the normalized title before fuzzy comparison. This means that duplicate articles with significantly different title beginnings may not be detected as duplicates, trading some accuracy for faster processing.*

---

## Caching

### Cache Directory Structure 
The cache is organized in a hierarchical directory structure within the specified `cache_directory`:

```
cache_directory
├── <query_hash>
│   ├── <database_name>
│   │   ├── metadata.json
│   │   └── results.bib
│   ├── <database_name>
│   │   ├── metadata.json
│   │   └── results.bib
│   ├── slrquerytester-union/     # ← Union results (when using --output_merge)
│   │   ├── metadata.json
│   │   └── result0.bib
│   └── ...
├── <query_hash>
│   ├── <database_name>
│   │   ├── metadata.json
│   │   └── results.bib
│   └── ...
└── ...
```
 
- **`<query_hash>/`** : A unique identifier generated from the query string using an MD5 hash. This ensures that each query has a distinct directory, avoiding conflicts and facilitating quick lookups.
 
- **`<database_name>/`** : Subdirectories within each query hash directory, representing the specific databases (e.g., Scopus, PubMed) queried.
 
- **`metadata.json`** : A JSON file containing metadata about the cached results for the specific query and database.
 
- **`results.bib`** : BibTeX file containing the fetched articles from the database corresponding to the query.

### Metadata (`metadata.json`)
Each `metadata.json` file stores essential information about the cached results to manage data integrity, freshness, and completeness. Below is an example structure and explanation of each field:

```json
{
    "expected_num_articles": 100,
    "num_articles_retrieved": 80,
    "last_api_call_time": "2024-04-15T12:34:56Z",
    "translated_query_string": "TITLE-ABS-KEY(machine learning AND (deep learning OR neural networks) AND PUBYEAR > 2019)",
    "general_query_string": "machine learning AND (deep learning OR neural networks) AND publication_year>=2020"
}
```

- **`expected_num_articles`** : The total number of articles expected from the query. This number is typically derived from the database's response metadata indicating the total available results. Helps determine if all expected articles have been retrieved or if further API calls are necessary to fetch additional results.
 
- **`num_articles_retrieved`** : The number of articles currently retrieved and stored in the cache. Tracks progress in fetching articles, especially when handling paginated API responses or large result sets.
 
- **`last_api_call_time`** : The timestamp of the most recent API call made for this query and database. ISO 8601 format with a 'Z' suffix indicating UTC time (e.g., `"2024-04-15T12:34:56Z"`). Determines the freshness of the cached data. If the data is older than the specified `threshold_days`, it is considered stale and may require refreshing.
 
- **`translated_query_string`** : The database-specific version of the original query string. Stores how the general query has been translated to fit the syntax requirements of the specific database, facilitating accurate execution and future reference.
 
- **`general_query_string`** : The original, user-defined query string as specified in `queries.json`. Maintains a reference to the initial query, allowing for easy identification and comparison across different databases and reports.

### How the Cache Works 
 
1. **Query Execution:** 
  - When a user runs a query, the tool translates it into the specific syntax required by each targeted database.
 
2. **Caching Results:**  
  - Results from each database are stored in the `results.bib` file within their respective `<database_name>/` directories.
 
  - Metadata about each query and database combination is stored in `metadata.json`.
 
3. **Cache Validation:** 
  - Before executing a query, the tool checks if results are already cached.
 
  - It verifies if the cached data is stale based on the `last_api_call_time` and `threshold_days`.
 
  - It also checks if the number of retrieved articles meets the `expected_num_articles`.
 
4. **Updating the Cache:**  
  - If data is stale or incomplete, the tool fetches additional results and updates both `results.bib` and `metadata.json`.
 
  - Commit messages are appended to `git_commit_message.txt` to document these updates for version control.
 
5. **Git Integration:**  
  - When the `--git` flag is used, the tool commits and pushes changes in the cache to the specified Git repository, ensuring that all team members have access to the latest cached data.

### Benefits of the Cache Structure 
 
- **Efficiency:** 
Minimizes redundant API calls by reusing cached data, saving time and reducing the load on external services.
 
- **Scalability:** 
Handles multiple queries and databases systematically, allowing for easy expansion as more queries or databases are added.
 
- **Data Integrity:** 
Metadata ensures that cached data remains accurate and up-to-date, facilitating reliable comparisons and reporting.
 
- **Collaboration:** 
Git integration allows multiple researchers to share and maintain a consistent cache, enhancing collaborative efforts in large-scale SLR projects.

### Managing the Cache 
 
- **Clearing the Cache for a Specific Query and Database:** If you need to remove cached data for a particular query and database (e.g., to force a fresh fetch), navigate to the corresponding directory and delete the `results.bib` and `metadata.json` files.

```bash
rm /path/to/cache_directory/<query_hash>/<database_name>/results.bib
rm /path/to/cache_directory/<query_hash>/<database_name>/metadata.json
```
 
- **Clearing the Entire Cache:** To remove all cached data, delete the entire `cache_directory`.

```bash
rm -rf /path/to/cache_directory/*
```
*Use with caution, as this will require re-fetching all data.*
 
- **Backing Up the Cache:** Regularly back up the `cache_directory` to prevent data loss and ensure that cached results can be restored if needed.

---

## Disclaimer

SLR Query Tester is provided "as-is" without any warranty. The author does not assume any responsibility for any misuse of this tool. Users are responsible for ensuring that their use of this tool complies with the terms and conditions of the APIs and the data they retrieve. Please respect all licensing agreements and usage policies associated with the bibliographic databases and their APIs.

## Notes 
 
- **API Rate Limits:** 
Be mindful of the rate limits and usage policies of the databases you query to avoid exceeding allowed request quotas. `slrquerytester` has a built-in exponential backoff rate-limiter.
- **API Keys:** 
Be careful to not share your API keys with anyone, or upload them with the configuration file to a shared Git repository. It is advisable to keep the configuration file outside the Git repo. The idea is to have a unique configuration file for each such SLR project that you may be working on (hats-off to you if you're doing that!).  

---

## License 
[MIT License](LICENSE)