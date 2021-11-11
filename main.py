'''
Run this file when live running the bot.
'''
from bot import bot
from time import sleep, time
##################CONFIG####################
RH_USERNAME = '' #Put your RH username inbetween the quotes
RH_PASSWORD = '' #Put your RH password inbetween the quotes
SHARE_UNIT = 10 #Amount of dollars used for each trade
##################ENDCONFIG#################

def run():
    b = bot(RH_USERNAME, RH_PASSWORD, crypto=False, qauntity_constant=SHARE_UNIT, 
        min_mark_cap=100000000000)
    b.login()
    print(b.min_mark_cap)

    while True:
        start = time()
        b._test_run()
        end = time()
        print(f'Cycle Elapsed in {end - start}')
        sleep(3600)

if __name__ == '__main__':
    run()