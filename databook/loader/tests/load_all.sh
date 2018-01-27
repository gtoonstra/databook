#!/bin/bash

(cd ../python; python3 person_loader.py persons.csv --clear)
(cd ../python; python3 person_groups_loader.py person_groups.csv)
(cd ../python; python3 person_tableauchart_loader.py person_tableau_charts.csv)
(cd ../python; python3 person_tableauworkbook_loader.py person_tableau_workbooks.csv)
(cd ../python; python3 tableauworkbook_chart_loader.py tableau_charts_workbook.csv)
(cd ../python; python3 table_databases_loader.py table_databases.csv)
(cd ../python; python3 table_table_loader.py table_table.csv)
(cd ../python; python3 tableauchart_table_loader.py tableauchart_table.csv)
