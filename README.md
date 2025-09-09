# overdrive-reconcile

A collection of scripts used to identify available electronic resources and reconcile data between NYPL & BPL Sierra and OverDrive's Discovery APIs.

The reconciliation requires an export of data from Sierra and access to the OverDrive Discovery APIs.
OverDrive API credentials should be in a YAML file and include the following keys:
```yaml
---
CLIENT_KEY: overdrive_client_key
CLIENT_SECRET: overdrive_client_secret
LIBRARY_ID: library_id
```

## 1. Verify all available OverDrive MarcExpress files have been loaded
To begin the reconciliation process, verify with staff responsible for loading OverDrive records that there are no outstanding files in the OverDrive Marketplace and all available records have been loaded into both BPL and NYPL Sierra. Only after receving a confirmation all OverDrive Reserve IDs are in Sierra should one begin creating lists in Sierra for export.

## 2. Sierra list creation & export

Use following the searches in Sierra to create a list. If large list files are unavailable use Sierra bib IDs to track extracted data and combine partial reports into one file.

Because of the large number of OverDrive records in NYPL Sierra (over 300,000) attempting to create one large list in tends to fail. It's a good strategy to use smaller (ie. 10,000 records) lists before running a large one (ie. 100,000 records). It is also recommended to limit the start and end bib ID number to the smallest slice of the database possible.

The BPL query can be retrieved from Sierra as the `2022-Overdrive ALL bibs-tak` saved search, or loaded from [this JSON file](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/bpl-marcexpress-sierra-search.json).

The NYPL query can be loaded from [this JSON file](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/nypl-marcexpress-sierra-search.json)

### NYPL
Store Record Type: BIBLIOGRAPHIC b

Start: b170902584

Stop: b*

|Operator|Type|Field|Condition|ValueA|
|---|---|---|---|---|
||BIBLIOGRAPHIC|MARC Tag 037|a|not equal to|""|
|AND|BIBLIOGRAPHIC|MARC Tag 037|b|has |"overdrive"|
|AND|BIBLIOGRAPHIC|MARC Tag 856|u|All Fields don't have|"serialssolutions"|
|AND|BIBLIOGRAPHIC|Call No.|starts with|"enypl"|

### BPL
Store Record Type: BIBLIOGRAPHIC b

Start: b112402306 

Stop: b*

|Operator|Type|Field|Condition|ValueA|
|---|---|---|---|---|
||BIBLIOGRAPHIC  MARC Tag 003  not equal to  "wasess"|
|AND|BIBLIOGRAPHIC|MARC Tag 037\|a|not equal to|""|
|AND|BIBLIOGRAPHIC|MARC Tag 037\|b|has|"overdrive"|
|AND|BIBLIOGRAPHIC|MARC Tag 856\|u|All Fields don't have|"serialssolutions"|
|AND|BIBLIOGRAPHIC|CALL #|starts with|"e"|

### Both Systems
Export the following fields from created list:

|Type|Field|
|---|---|
|BIBLIOGRAPHIC|Record Number|
|BIBLIOGRAPHIC|MARC Tag 037\|a|

Use default export values: 

+ Field delimiter: `,`
+ Text qualifier: `"`
+ Repeated field delimiter: `;`
+ Maximum field length: `<none>`

## 3. Launching scripts
1. Activate virtual environment
2. Change working directory to the main repo directory
3. In the command line run the following:
```bash
$ python run.py reconcile {library} {path-to-sierra-export-file}
```
BPL example:
```bash
$ python run.py reconcile BPL "./temp/overdrive-all-sierra-export.txt"
```

The above routine verifies a resource's availability by scraping the OverDrive website for the resource. This webscraping is prone to timeouts on the OverDrive server. 

CLI shows traceback to a timeout error (last processed resource had number 626):
[![scraping timeout](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/webscraping-error.png)](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/webscraping-error.png)

If that happens, simply note the number of the next resource to be checked and restart the process utilizing the following command:
```bash
$ python run.py webscrape {library} {data source path} {row to start from} 
```
{data source path} is the appropriate `{library}-for-deletion-verification-required.csv` file created by previous scripts. If restarting the process on the same day the command can be simplified by entering `default` instead of providing the full path to data source:

```bash
$ python run.py webscrape BPL default 627
```

## 4. Analysis reports

The reconciliation script creates a designated directory where all reports are saved: `overdrive-reconcile/files/{library}/{YYYY-MM-DD}/`. 

The scripts generate the following reports:
+ `{library}-FINAL-available-resources.csv`
+ `{library}-FINAL-duplicate-reserveid-sierra.csv`
+ `{library}-FINAL-for-deletion-verified-resources.csv`
+ `{library}-FINAL-for-import-missing-resources.csv`
+ `{library}-false-positive-for-deletion.csv`
+ `{library}-for-deletion-verification-required.csv` (temp, work file)
+ `{library}-for-import-verification-required.csv` (temp, work file)
+ `{library}-overdrive-api-reserve-ids.csv` (temp, work file)
+ `{library}-sierra-prepped-reserve-ids.csv` (temp, work file)
+ `{library}-sierra-rejected-not-overdrive-ids.csv` (work file)
+ `{library}-unique-reserveid-sierra.csv` (temp, work file)

Actionable reports have the `FINAL` prefix in the title.

### `FINAL-duplicate-reserveid-sierra.csv`
This report contains a list of duplicate resources discovered in the ILS based on OverDrive Reserve ID. The csv contains Bib IDs and reserve IDs.

### `FINAL-for-deletion-verified-resources.csv`
This report provides a list of records that can be deleted from Sierra because the library no longer has access to the resource or because OverDrive removed the resource from their catalog. Please take extra precautions deleting records from Sierra. It is possible that occasionally an item record belonging to a print version of the resource is attached to electronic resource bib in Sierra. In such cases a new record for print must be first brought from WorldCat, then the item should be transfered to it before the bib for the electronic resource can be deleted.

### `FINAL-for-import-missing-resources.csv`
This report contains a list of reserve IDs that can be used to create a MARC file in OverDrive Marketplace to then load into Sierra.

### `false-positives-for-deletion.csv`
This report includes resources that were not present in the inventory retrieved from the OverDrive Digital Inventory API, but were discovered in the ILS and the verification routine (webscraping of OverDrive catalog - see details below) found that in fact they are available to our patrons.

## How does this work?

The script analyzes OverDrive data pulled from the ILS (Sierra) and compares it with data pulled from the OverDrive Digital Inventory API. These two sets acquire information from two different sources: OverDrive Marketplace MARC records and the OverDrive Discovery APIs. Resources found in both sets are considered to be available and are left alone. Resources identified as only being found in the OverDrive Digital Inventory API can be used to create a MARC file in the OverDrive Marketplace so that MARC records for those resources can be ingested into the ILS. Resources found only in Sierra may indicate they are no longer available from OverDrive. Deletion verification though webscraping of OverDrive catalog is needed.

[![diagram](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/Overdrive-weeding.drawio.png)](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/Overdrive-weeding.drawio.png)

After identifying resources that could be deleted from Sierra the list is verified via web scraping the OverDrive catalog.

## Changelog

### [1.2.0] - (9/9/2025)
#### Added

#### Changed

#### Fixed

#### Removed

### [1.1.0] - (2/14/2024)
#### Added
+ step in the instruction to confirm all Overdrive MarcExpress records have been loaded to the ILS
+ information about credentials format
+ added requests (2.31.0) to dependencies
#### Changed
+ local simplyE credentials moved to `~/.cred/.simplyE/` directory
+ updated dependencies:
  + beautifulsoup4 (4.12.3)
  + pandas (2.2.0)
  + pymarc (4.2.2)
  + SQLAlchemy (2.0.27)
  + psycopg2 (2.9.9)
+ updated dev dependencies:
  + black (22.12.0)
  + pytest (7.4.4)
+ refactored tests based on updated dependencies
#### Removed
+ removed unused dependencies

[1.1.0]: https://github.com/BookOps-CAT/overdrive-reconcile/compare/1.0.0...v1.1.0
