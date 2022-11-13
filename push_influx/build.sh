
docker build . -t push_influx:latest \
--build-arg ESPN_S2='AEB%2BFXoRNN%2B7FcNagzaKvUqUC5D8K9Dd4c2pl3BhB6T9911xvhC38U9t1ZKFaD4C%2Bmpg2ZzIzjRM5%2BKxIFY1jbngt13zNRaWVQ2rOqhZPRNmvJ%2BnCYW1lhyx43JC7ZBgMPhQiAEXO%2FHIaEWYuyB6bEsWhhjZfM7dksRwxEUoI0pzQ4bT2lJXOor20vJNonfmGXWqRWnjbj0%2FK4cPKOjQ1v85FUSV23SLUTE0QTUdf5Ntoe%2FMHnTtm41Z3MSaiau%2BbidL9vAQS8ganFa5SafOrd6S' \
--build-arg SWID='{7E6254AC-2122-45FC-815D-146E95002343}' \
--build-arg LEAGUE_ID=537930371 \
--build-arg LEAGUE_YEAR=2023 \
--build-arg INFLUX_TOKEN="42NVptvGheHKqeJlb7j4x0WrmnL0v3Um" \
--build-arg INFLUX_ORG="HomeOrg" \
--build-arg INFLUX_URL="http://tanker.fritz.box/influxdb" \
--build-arg INFLUX_BUCKET="HomeBucket"