# Jobsdle

A daily guessing game: name the monthly change in U.S. nonfarm payrolls (2000 to the latest report), with unemployment, CPI and other figures from the same BLS release revealed as hints.

- `index.html` is the whole game, with the data built in.
- `update_data.py` pulls the last 10 years from the BLS API and adds new or revised months to `index.html`.
- `build.py` is the original one-time build of the full history.
- `.github/workflows/update-data.yml` runs the update every day and publishes only when something changed.

Data: U.S. Bureau of Labor Statistics, seasonally adjusted, current revised estimates.
