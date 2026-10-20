# Youtube Sampler

Extract segments from youtube clips and save them as `.mp3`.

Has a web interface, where you can preview your selection.


## Dev

`docker compose -f compose.yml -f compose.dev.yml up --build`

## Prod

`docker compose -f compose.yml -f compose.prod.yml up --build -d`

## To keep it up to date

Run `update.sh` with corntab.

```0 4 * * 0 /path/to/update.sh /path/to/app >> /var/log/update.log 2>&1```


## API "Docs"

The api has two endpoints

/extract 
- returns audio file of chosen length (start and end in milliseconds)
```
http://localhost:420/extract?url=https://www.youtube.com/watch?v=ThvESdCX8QM&start=1000&end=5000
```

/segment 
- returns the queried audio/video cut up into x segments (length of segment in milliseconds)
```
http://localhost:420/segment?url=https://www.youtube.com/watch?v=ThvESdCX8QM&segment_len=60000
```
