## overdrive-reconcile

A collection of scripts used to reconcile available electronic resources between NYPL & BPL Sierra and OverDrive Platform.

The reconciliation requires Sierra export and access to SimplyE databases.

### sierra list creation & export

Use following searches in Sierra to create a list. In case large list files are unavailable use Sierra bib #s to track extracted data and combine partial reports into one file.
BPL query can be retrieved from Sierra as "2022-Overdrive ALL bibs-tak" saved search, or loaded from [this JSON file](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/bpl-marcexpress-sierra-search.json)
NYPL query can be loaded from [this JSON file](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/nypl-marcexpress-sierra-search.json)

#### NYPL
start bib: b170902584 end bib: b*

BIBLIOGRAPHIC  MARC Tag 037|a  not equal to  ""    AND BIBLIOGRAPHIC  MARC Tag 037|b  has  "overdrive"    AND BIBLIOGRAPHIC  MARC Tag 856|u  All Fields don't have  "serialssolutions"    AND BIBLIOGRAPHIC  Call No.  starts with  "enypl"

#### BPL
BIBLIOGRAPHIC  MARC Tag 003  not equal to  "wasess"    AND BIBLIOGRAPHIC  MARC Tag 037|a  not equal to  ""    AND BIBLIOGRAPHIC  MARC Tag 037|b  has  "overdrive"    AND BIBLIOGRAPHIC  MARC Tag 856|u  All Fields don't have  "serialssolutions"    AND BIBLIOGRAPHIC  CALL #  starts with  "e"

Export following fields from created list: RECORD # (BIBLIOGRAPHIC), MARC Tag 37|a. Use default export values: field delimiter `,`, text qualifier `"`, repeated field delimiter `;`, maximum field lenght `none`.

### launching scripts
1. Activate virtual environment
2. Change working directory to the main repo directory
3. In the command line run the following:
```bash
$ python run.py reconcile {library} {path-to-sierra-export-file}
```
BPL example:
```bash
$ python run.py reconcile BPL "C:/temp/overdrive-all-sierra-export.txt"
```

Above routine includes a verification of availability of resources that web scrapes OverDrive catalog for each system. This webscraping is prone to timeouts on OverDrive server. If that happens, simply note the number of the next resource to be checked and restart the process utilizing the following command:
```bash
$ python run.py webscrape {library} {data source path} {row to start from} 
```
{data source path} is the appropriate `{library}-for-deletion-verification-required.csv` file created by previous scripts. This restarting command can be simplified if run the same day when analysis is initially launched. In this case, instead of providing the full path to data source enter "default", as in the example below:

CLI shows traceback to a timeout error (last processed resource had number 626):
[![scraping timeout](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/webscraping-error.png)](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/webscraping-error.png)

Restart the process by providing the number of the next resource and "default" instead of the full path for the source:
```bash
$ python run.py webscrape BPL default 627
```

### analysis reports

The reconciliation script creates a designated directory to put all its reports: `overdrive-reconcile/files/{library}/{YYYY-MM-DD}/`
It creates the following reports:
+ `{library}-FINAL-available-resources.csv`
+ `{library}-FINAL-duplicate-reserveid-sierra.csv`
+ `{library}-FINAL-for-deletion-verified-resources.csv`
+ `{library}-FINAL-for-import-missing-resources.csv`
+ `{library}-false-positive-for-deletion.csv`
+ `{library}-for-deletion-verification-required.csv` (temp, work file)
+ `{library}-sierra-prepped-reserve-ids.csv` (temp, work file)
+ `{library}-sierra-rejected-not-overdrive-ids.csv` (work file)
+ `{library}-simplye-reserve-ids.csv` (temp, work file)
+ `{library}-unique-reserveid-sierra.csv` (temp, work file)

Actionable reports have the `FINAL` affix in the title.

`FINAL-duplicate-reserveid-sierra.csv` provides information on discovered in the ILS duplicates based on OverDrive Reserve ID.

`FINAL-for-deletion-verified-resources.csv` provides a list of records that can be deleted from ILS because the library no longer have access to the resource or because OverDrive removed the resource from their catalog. Please take extra precautions deleting records from Sierra. It is possible that occasionally an item record belonging to a print version of the resource is attached to electronic resource bib in Sierra. In such cases a new record for print must be first brought from WorldCat, then item transfered to it before the electronic resource bib can be deleted.

`Final-for-import-missing-resources.csv` provides a list of Reserve IDs that can be used to create a MARC file in OverDrive Marketplace that can be used to add these resources to the ILS.

`false-positive-for-deletion.csv` includes resources that were not present in the SimplyE database, but were discovered in the ILS and the verification routine (webscraping of OverDrive catalog - see details below) found that in fact they are available to our patrons. This report should be shared with SimplyE devs to mitigate missing in SimplyE titles.

### how this works?

The script analyzes OverDrive data pulled from ILS (Sierra) and compares it with data pulled from SimplyE database. These two sets acquire information from two different sources: OverDrive Marketplace MARC records and OverDrive API. Resources found in both sets are considered to be available and are left alone. Identification of resources found in the SimplyE database only allow compilation of a MARC file in the OverDrive Marketplace so they are ingested into ILS. Resources found only in Sierra may indicate they are no logger available from OverDrive. This however needs to be verified because of OverDrive API crashes ([SIMPLY-391 issue](https://jira.nypl.org/browse/SIMPLY-3961)) that result in missing data in SimplyE DB. 

[![diagram](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/Overdrive-weeding.drawio.png)](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/Overdrive-weeding.drawio.png)

The verification process of missing in Sierra resources is done via web scraping of OverDrive catalog (we do not have access to OverDrive API to do it more efficiently).

### changelog
