#!/usr/bin/env python3

import findspark
from pyspark import *
import string
import enchant
import sys
import random
import googlesearch

findspark.init()

conf = SparkConf().setMaster("local").setAppName("HW2")
sc = SparkContext(conf=conf)

alphabet = 'abcdefghijklmnopqrstuvwxyz'
dictionary = enchant.Dict('en-US')


def differenceBetweenLetters(letter, compareTo='e'):
    return string.ascii_lowercase.index(compareTo.lower()) - string.ascii_lowercase.index(letter.lower())


def shiftText(text, howMuch):
    newString = ""
    for char in text:
        if char.lower() not in alphabet:  # don't shift numbers, spaces or special characters
            newString += char
        else:
            newIndex = string.ascii_lowercase.index(char.lower()) + howMuch
            if newIndex > 25:  # loop back around to beginning of alphabet
                newIndex -= 26
            if newIndex < 0:  # loop back around to beginning of alphabet
                newIndex += 26
            newString += alphabet[newIndex]
    return newString


def mostCommonLetter(charArray, index=0):
    try:
        char = charArray[index][0]  # first character in sorted array is the most common character
        if str(char) not in alphabet:  # if most common character is not a letter, find the second most common, etc.
            return mostCommonLetter(charArray, index + 1)
        return char
    except Exception as e:
        print(e)
        sys.exit(0)
    return None


def check_if_words(decrypted_words):
    passed = 0
    failed = 0
    test_count = int(len(decrypted_words) / 20)
    for _ in range(test_count):  # check 5% of words
        index = random.randint(0, len(decrypted_words) - 1)
        word = ''.join(c for c in decrypted_words[index] if str(c).isalnum()).lower()
        if not word:
            test_count -= 1
            continue
        if dictionary.check(word):  # track number of valid and non-valid words
            passed += 1
        else:
            failed += 1
    if failed == 0:
        print('Tested {} word(s): 100% validity.'.format(test_count))
        return True
    passed_percentage = (passed / test_count) * 100
    print('Tested {} word(s): {}% validity.'.format(test_count, "{0:.2f}".format(passed_percentage)))
    if passed_percentage >= 75:
        return True
    return False


def check_google(text):
    query_length = min(20, len(text))
    query_text = ""
    for i in range(query_length):
        query_text += text[i] + " "  # use the first 20 words (or entire string if less than 20 words) as a search query on google
    search_results = googlesearch.search(query=query_text, tld="com", lang='en', num=3, stop=3, pause=2.0)
    if search_results:
        print("Potential sources:")
        for result in search_results:
            print(result)


filename = input("What txt file would you like to decrypt (exclude extension)? ")
auto_check_complete = False
res = input("Let the script determine when the cipher is decoded (true) or manually decide for yourself (false)? ")
if res.lower().startswith('t'):
    auto_check_complete = True

textFile = sc.textFile('{}.txt'.format(filename)).cache()
chars = textFile.flatMap(lambda line: list(line))
charMap = chars.map(lambda char: (char.lower(), 1)).reduceByKey(lambda k, v: k + v).collect()
charMap.sort(key=lambda charTuple: charTuple[1], reverse=True)
letter = mostCommonLetter(charMap)

letterMarkers = ['e', 't', 'a', 'o', 'i', 'n', 's', 'h', 'r', 'd']  # cite: https://en.wikipedia.org/wiki/Letter_frequency
letterMarkerIndex = 0
validWords = False
print("Most common letter: {}".format(letter))
while not validWords:
    if letterMarkerIndex > len(letterMarkers) - 1:
        print("Exhausted the 10 most common letters. Quitting...")
        break
    letterMarker = letterMarkers[letterMarkerIndex]
    diff = differenceBetweenLetters(letter, letterMarker)
    print("Adjusting for '{}'. Shifting text by {}...".format(letterMarker, diff))
    adjustedText = shiftText(chars.collect(), diff)
    print(adjustedText)
    if auto_check_complete:
        adjustedWords = adjustedText.split()
        if check_if_words(adjustedWords):
            validWords = True
            print("A significant number of the words are dictionary words. Deciphering complete.")
    else:
        res = input("Does that look correct? (y/n): ")
        if res.lower().startswith('y'):
            validWords = True
    letterMarkerIndex += 1
with open("{}_decrypted.txt".format(filename), 'w+') as f:  # save decrypted text to a file
    f.writelines(adjustedText)
    f.close()
print("Decrypted file saved: {}_decrypted.txt".format(filename))
check_google(adjustedWords)  # search for the text source on Google
