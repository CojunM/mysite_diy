import itertools
import datetime
import time
def generatelibary(library, length=6):

    libararys =itertools.product(library,repeat=length)

    with open("d:\paswordlirbarys.txt","a",encoding='utf-8') as dic:
        for i in libararys:
            dic.write("".join(i))
            dic.write("".join("\n"))

if __name__ == "__main__":

    lowercase = 'abcdefghijklmnopqrstuvwxyz'
    uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    digits = '0123456789'
    special = """!#$%&*?@""" # """!"#$%&'( )*+,-./:;<=>?@[]^_`{|}~"""
    word = lowercase + uppercase + special + digits

    starttime = datetime.datetime.now()
    print(time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())))
    generatelibary(word,length=8)  #生成8位数字字典
    endtime = datetime.datetime.now()
    print(time.strftime("%Y%m%d%H%M%S", time.localtime(time.time())))
    print('The time cost: ')
    print(endtime - starttime)