## overdrive-reconcile

A collection of scripts used to reconcile available electronic resources between NYPL & BPL Sierra and OverDrive Platform.

The reconciliation requires Sierra export and access to SimplyE databases.

### sierra list creation & export

Use following searches in Sierra to create a list. In case large list files are unavailable use Sierra bib #s to track extracted data and combine partial reports into one file.

#### NYPL
BIBLIOGRAPHIC  MARC Tag 037|a  not equal to  ""    AND BIBLIOGRAPHIC  MARC Tag 037|b  has  "overdrive"    AND BIBLIOGRAPHIC  Call No.  starts with  "enypl"

#### BPL
BIBLIOGRAPHIC  MARC Tag 003  not equal to  "wasess"    AND BIBLIOGRAPHIC  MARC Tag 037|a  not equal to  ""    AND BIBLIOGRAPHIC  MARC Tag 037|b  has  "overdrive"    AND BIBLIOGRAPHIC  CALL #  starts with  "e"

Export following fields from created list: RECORD # (BIBLIOGRAPHIC), MARC Tag 37|a. Use default export values: field delimiter `,`, text qualifier `"`, repeated field delimiter `;`, maximum field lenght `none`.

### launching scripts
1. Activate virtual environment
2. Change working directory to the main repo directory
3. In the command line run the following:
```bash
$ python run.py {library} {path-to-sierra-export-file}
```
BPL example:
```bash
$ python run.py BPL "C:/temp/overdrive-all-sierra-export.txt"
```

### analysis reports

The reconciliation scrips creates a designated directory to put all its reports: `overdrive-reconcile/files/{library}/{YYYY-MM-DD}/`
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
`FINAL-for-deletion-verified-resources.csv` provides a list of records that can be deleted from ILS because the library no longer have access to the resource or because OverDrive removed the resource from their catalog.
`Final-for-import-missing-resources.csv` provides a list of Reserve IDs that can be used to create a MARC file in OverDrive Marketplace that can be used to add these resources to the ILS.

`false-positive-for-deletion.csv` includes resources that were not present in the SimplyE database, but were discovered in the ILS and an alternative verification (webscraping of OverDrive catalog - see details below) found that in fact they are available to our patrons. This report should be shared with SimplyE devs to mitigate missing in SimplyE titles.

### how this works?

[![diagram](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/Overdrive-weeding.drawio.png)](https://github.com/BookOps-CAT/overdrive-reconcile/blob/main/docs/media/Overdrive-weeding.drawio.png)

### verifying deletion list




### changelog
