import os
from time import sleep

print("<<<<<<<< >>>>>>>>> HELLO WORLD <<<<<<<< >>>>>>>>>")
sleep_time = 20

sample_secret_env_var = os.getenv('ZIPHER_API_KEY')
if sample_secret_env_var and sample_secret_env_var == 'test_key':
    print(f"Successfully retrieved secret from environment variable: {sample_secret_env_var}")
    sleep_time = 90


print(f"About to sleep for {sleep_time} seconds")
sleep(sleep_time)
print("<<<<<<<< >>>>>>>>> GOODBYE WORLD <<<<<<<< >>>>>>>>>")