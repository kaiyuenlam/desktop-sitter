#!/usr/bin/env python3
## give response based on detected emotion with flush sentences

import time
import sys
import os

happyword = 'glad to see you being happy! it makes me happy too!\n'
surprisedword = 'wow! surprising indeed!\n'
angryword = 'chill out~\n'
anxiousword = 'everything will be fine\n'

while True:
    emotionstate = input('Input the detected emotion here (For Testing): happy / surprised / angry / anxious : ')
    if emotionstate == 'happy':
        for x in happyword:
            print(x, end='') #Print the sentence
            sys.stdout.flush() #Display the sentence word-by-word like typewriters
            time.sleep(0.05) #Time interval for printing out each character
    if emotionstate == 'surprised':
        for x in surprisedword:
            print(x, end='')
            sys.stdout.flush()
            time.sleep(0.05)
    if emotionstate == 'angry':
        for x in angryword:
            print(x, end='')
            sys.stdout.flush()
            time.sleep(0.05)
    if emotionstate == 'anxious':
        for x in anxiousword:
            print(x, end='')
            sys.stdout.flush()
            time.sleep(0.05)
    time.sleep(5)
    os.system("cls || clean")