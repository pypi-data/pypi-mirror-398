#!/usr/bin/env python

""""""
# AUSnumtools - A lightweight Python module that validates Australian phone numbers."""

# SPDX-FileCopyrightText: 2025 Ben Bonacci <ben at benbonaccci dot com>
# SPDX-License-Identifier: GPL-3.0-only

""""""
import re

AUS_ACMA_LANDLINE_REGEX = re.compile("^[0][2|3|7|8](5550|7010)[0-9]{4}$")
AUS_ACMA_MOBILE_DICT = ["0491570006", "0491570156", "0491570157", "0491570158", "0491570159", "0491570110", "0491570313", "0491570737", "0491571266", "0491571491", "0491571804", "0491572549", "0491572665", "0491572983", "0491573770", "0491573087", "0491574118", "0491574632", "0491575254", "0491575789", "0491576398", "0491576801", "0491577426", "0491577644", "0491578957", "0491578148", "0491578888", "0491579212", "0491579760", "0491579455"]
AUS_ACMA_SMARTNUM_DICT = ["1800160401", "1800975707", "1800975708", "1800975709", "1800975710", "1800975711", "1300975707", "1300975708", "1300975709", "1300975710", "1300975711"]

AUS_NUM_LANDLINE_REGEX = re.compile("^[0][2|3|7|8][0-9]{8}$")
AUS_NUM_MOBILE_REGEX = re.compile("^[0][4][0-9]{8}$")
AUS_NUM_SMARTNUM_REGEX = re.compile("^[1][3|8][0]{2}[0-9]{6}$")
AUS_NUM_13SMARTNUM_REGEX = re.compile("^[1][3][0-9]{4}$")


## Default preferences
#None


## Functions
def is_au_landline(number: str, blockFiction: bool=False) -> bool:
    """Validates that the provided phone number is valid for an Australian landline"""
    if AUS_NUM_LANDLINE_REGEX.search(number):
        if blockFiction == True:
            if AUS_ACMA_LANDLINE_REGEX.search(number):
                return False
            else:
                return True
        else:
            return True
    else:
        return False

def is_au_mobile(number: str, blockFiction: bool=False) -> bool:
    """Validates that the provided phone number is valid for an Australian mobile"""
    if AUS_NUM_MOBILE_REGEX.search(number):
        if blockFiction == True:
            for i in AUS_ACMA_MOBILE_DICT:
                if i == number:
                    return False
            else:
                return True
        else:
            return True
    else:
        return False

def is_au_smartnum(number: str, blockFiction: bool=False) -> bool:
    """Validates that the provided phone number is valid for an Australian smart number"""
    if AUS_NUM_SMARTNUM_REGEX.search(number):
        if blockFiction == True:
            for i in AUS_ACMA_SMARTNUM_DICT:
                if i == number:
                    return False
                else:
                    return True
        else:
            return True
    elif AUS_NUM_13SMARTNUM_REGEX.search(number):
        if blockFiction == True:
            return True # While there are no designated 13 XXXX smart numbers for fictional use by the ACMA, this condition remains in case there are future changes by the ACMA.
        else:
            return True
    else:
        return False

def is_au_number(number: str, blockFiction: bool=False) -> bool:
    """Validates that the provided phone number is valid for any Australian number"""
    if AUS_NUM_LANDLINE_REGEX.search(number):
        if blockFiction == True:
            if AUS_ACMA_LANDLINE_REGEX.search(number):
                return False
            else:
                return True
        else:
            return True
    elif AUS_NUM_MOBILE_REGEX.search(number):
        if blockFiction == True:
            for i in AUS_ACMA_MOBILE_DICT:
                if i == number:
                    return False
            else:
                return True
        else:
            return True
    elif AUS_NUM_SMARTNUM_REGEX.search(number):
        if blockFiction == True:
            for i in AUS_ACMA_SMARTNUM_DICT:
                if i == number:
                    return False
                else:
                    return True
        else:
            return True
    elif AUS_NUM_13SMARTNUM_REGEX.search(number):
        if blockFiction == True:
            return True
        else:
            return True
    else:
        return False



if __name__ == "__main__":
    print("AUSnumtools is a Python module and not an interactive Python script. Please import AUSnumtools in order to use it. Consult the documentation for further assistance.")
