from datetime import datetime
from time import time as it
import random
from colorama import init, Fore, Back, Style


class SetAccess:
    """
    Обычная дата(Human readable time) 	Секунды
    1 минута	60 секунд
    1 час	3600 секунд
    1 день	86400 секунд
    1 неделя	604800 секунд
    1 месяц (30.44 дней) 2629743 секунд
    1 год (365.24 дней) 31556926 секунд
    """
    min = 60
    hour = 3600
    day = 86400
    week = 604800
    month = 2629743
    year = 31556926

    alphabet = {1: '%OrAHkYvUD', 2: '$GoSQnwxhf', 3: '&LigydCKbu', 4: '@tjzEVBaPZ', 5: '~NmJcqlXRp'}

    @classmethod
    def gen(cls, num):
        print('Время:', num, '\nЗашифрованное время:', end=' ')
        task = list(map(int, list(str(num))))
        line = ''
        for i in task:
            rez = list(cls.alphabet[random.randint(1, 5)])
            line += rez[i]
            print(rez[i], end='')
            for i_step in range(5):
                serial = random.choice(list('MalSt'))
                if i_step == 4:
                    line += serial
                else:
                    line += rez[random.randint(0, 9)]
        print(f'\nКлюч: {Fore.GREEN}{line}', Style.RESET_ALL)
        print('Действителен до:', Fore.YELLOW, datetime.utcfromtimestamp(num).strftime('%d.%m.%Y  %H:%M'), Style.RESET_ALL)


if __name__ == '__main__':
    now_time = int(it())
    SetAccess.gen(now_time + (SetAccess.month * 1))

# pyinstaller --onefile -i "rbt.ico" --add-data "a_file.txt;." --add-data "headers.json;." --add-data "catalog.json;." LeroyMerlinParser.py
#  pyinstaller --onefile -i "rbt.ico" LeroyMerlinParser.py
#  pyinstaller -F -i "rbt.ico" LeroyMerlinParser.py


