
docker build . -t post_powerrankings:latest \
--build-arg ESPN_S2='AEB5bhA03uKEegAyr2UCLiMVteaGww%2Fe3b2DiU00jlGxEqxaP7odO%2FLjW1rW2Wa%2B1B8nz6LYjrxOuD4MK%2BDg0OBh%2FTtokrX1jxO3o70b6Hmc2jziQwq3wP5Lvdjv3pXyDenimrM0YduFq47sLM7B3SF4BwuCcgkTwS2MQrfwjYe%2FjSbic8%2Bv84HApC6JNpI%2Bn3H%2FSpmtmLR28OjsBd14jcb4cGnaQ0VX1TlszqjabvK9WyN9qUGZ6MELVdqlhUn5Za%2FAtvcQAL4avPikBI9eKT%2FJ' \
--build-arg SWID='{7E6254AC-2122-45FC-815D-146E95002343}' \
--build-arg LEAGUE_ID=288399984 \
--build-arg LEAGUE_YEAR=2024 \
--build-arg BOT_API_KEY='5256187557:AAFUUx5PKzcEly-778-I06nyPn1PXct0uHU' \
--build-arg BOT_CHAT_ID='-638810494'
# Test
#--build-arg BOT_CHAT_ID='-638810494'
# Production
#--build-arg BOT_CHAT_ID='-623811432'