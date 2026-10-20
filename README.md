# Youtube Sampler

an api/tool using youtube_dl to extract audio segments from youtube clips and save them as mp3

makes it easy to get audio from youtube into your sampler (or whatever)

## Dev

docker compose -f compose.yml -f compose.dev.yml up --build

## Prod

docker compose -f compose.yml -f compose.prod.yml up --build -d

## To keep it up to date


## API "Docs"

the api has two endpoints

extract - returns audio file of chosen length (start and end in milliseconds)
```
http://localhost:420/extract?url=https://www.youtube.com/watch?v=ThvESdCX8QM&start=1000&end=5000
```

segment - returns the queried audio/video cut up into x segments (length of segment in milliseconds)
```
http://localhost:420/segment?url=https://www.youtube.com/watch?v=ThvESdCX8QM&segment_len=60000
```
