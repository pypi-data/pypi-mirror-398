# Dockerfile usage for CastorDoc package

## How To

- The Dockerfile is present on the pypi package
- For building it you should use this command `docker build -t castor-extractor-looker --build-arg EXTRA=looker .` with replacing looker one or several of: [bigquery,looker,metabase,powerbi,qlik,redshift,snowflake,tableau]
- For running it you should do `docker run -v <local-path>:/data --env-file <castor-extract-looker.env> castor-extractor-looker` where `</local-path>` have to be replaced and `<castor-extract-looker.env>` have to be set.
- Extracted datas would be available on `<local-path>`. The path should exists
- `<castor-extract-looker.env>` would contain env vars for credentials, url...

#### example

```bash
docker run -v /logs:/data --env-file /config/castor-extract-looker.env castor-extractor-looker
```

## Limitation

- This docker image is for a specific techno
- This docker image is based on python 3.11
- This docker image use the latest castor-extractor package version
