# Format Specification Votes

Acceptable file formats are files which are generated by hand, by the "Wabsti Elections and Referenda (VRSG)" election program or the web application itself.

"Municipality" might refer to a district, ward, etc.

## Content

<!-- TOC START min:1 max:4 link:true asterisk:false update:true -->
- [Format Specification Votes](#format-specification-votes)
    - [Content](#content)
    - [Preface](#preface)
        - [Entities](#entities)
    - [Formats](#formats)
        - [Standard format](#standard-format)
            - [Columns](#columns)
            - [Temporary results](#temporary-results)
            - [Template](#template)
        - [OneGov](#onegov)
            - [Columns](#columns-1)
            - [Temporary results](#temporary-results-1)
            - [Template](#template-1)
        - [Wabsti](#wabsti)
            - [Columns](#columns-2)
            - [Temporary results](#temporary-results-2)
            - [Template](#template-2)
        - [WabstiCExport](#wabsticexport)
<!-- TOC END -->


## Preface

### Entities

An entity is either a municipality (cantonal instances, communal instances without quarters) or a quarter (communal instances with quarters).


## Formats

### Standard format

There is generally one CSV/Excel file per referendum proposal. However, should the referendum include a counter-proposal and a tie-breaker, then three files need to be delivered: One file with the results of the referendum, one file with the results of the counter-proposal and one file with the results of the tie-breaker.

#### Columns

Each line contains the result of a single municipality, provided that this has been counted in full. The following columns are expected in the order listed here:

Name|Description
---|---
`ID`|The municipality number (BFS number) at the time of the vote. A value of `0` can be used for expats.
`Ja Stimmen`|The number of “yes” votes. If the word `unknown`/`unbekannt` is entered, the line will be ignored (not yet counted).
`Nein Stimmen`|The number of “no” votes. If the word `unknown`/`unbekannt` is entered, the line will be ignored (not yet counted).
`Stimmberechtigte`|The number of persons eligible to vote. If the word `unknown`/`unbekannt` is entered, the line will be ignored (not yet counted).
`Leere Stimmzettel`|The number of blank ballot papers. If the word `unknown`/`unbekannt` is entered, the line will be ignored (not yet counted).
`Ungültige Stimmzettel`|The number of spoilt ballot papers. If the word `unknown`/`unbekannt` is entered, the line will be ignored (not yet counted).

#### Temporary results

Municipalities are deemed not to have been counted yet if the municipality is not included in the results.

#### Template

- [vote_standard.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_standard.csv)


### OneGov

The format used by the web application for the export consists of one single file per vote. There is a line for every municipality and type of referendum (proposal, counter-proposal, tie-breaker).

#### Columns

The following columns will be evaluated and should exist at the least:

Name|Description
---|---
`status`|`unknown`, `interim` or `final`.
`type`|`proposal`, `counter-proposal` or `tie-breaker`.
`entity_id`|The municipality number (BFS number). A value of `0` can be used for expats.
`counted`|`true` if the municipality has been counted.
`yeas`|The number of “yes” votes.
`nays`|The number of “no” votes.
`invalid`|The number of spoilt votes.
`empty`|The number of blank votes.
`eligible_voters`|The number of persons eligible to vote.

#### Temporary results

Municipalities are deemed not to have been counted yet if one of the following two conditions apply:
- `counted = false`
- the municipality is not included in the results

If the status is
- `interim`, the whole vote is considered not yet completed
- `final`, the whole vote is considered completed
- `unknown`, the whole vote is considered completed, if all (expected) municipalities are counted

#### Template

- [vote_onegov.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_onegov.csv)


### Wabsti

The format of the "Wabsti Elections and Referenda (VRSG)" election program consists of a single file which contains all the data for many referenda. There is a line for every referendum and municipality.

#### Columns

The following columns will be evaluated and should exist at the least:
- `Vorlage-Nr.`
- `Name`
- `BfS-Nr.`
- `Stimmberechtigte`
- `leere SZ`
- `ungültige SZ`
- `Ja`
- `Nein`
- `GegenvJa`
- `GegenvNein`
- `StichfrJa`
- `StichfrNein`
- `StimmBet`

#### Temporary results

Municipalities are deemed not to have been counted yet if one of the following two conditions apply:
- `StimmBet = 0`
- the municipality is not included in the results

#### Template

- [vote_wabsti.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_wabsti.csv)


### WabstiCExport

Version `>= 2.2` is supported, please refer to the documentation provided by the exporter program for more information about the columns of the different files.
