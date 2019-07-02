This repo refers to blog post:


### TEST

Start the containers.
docker-compose up -d
Pgweb container often starts too soon compared to postgres, you might have to run
another docker-compose up -d once postgres had time to start.
The worker container is in exit mode, that's normal, it's not supposed to be running all the time.

When postgres and pgweb containers are up, log into the worker container:
docker-compose run worker /bin/bash
Now import the excel spreadsheet into postgres:
python insert.py
exit

Now go to pgweb interface in your web browser on localhost:8000
and you should see the table "sheet_1" with the excel sheet data in it.
