<!--
SPDX-FileCopyrightText: 2025 Ben Bonacci <ben at benbonacci dot com>

SPDX-License-Identifier: GPL-3.0-only
-->

# AUSnumtools

## About
AUSnumtools is a lightweight Python module that validates Australian phone numbers. 

## How it works
The Australian Communications and Media Authority (ACMA) outlines the telephone numbering plan for Australia. Specifically, it details the format of a phone number, such as which groups of digits represent an area code or a mobile carrier. This module uses a RegEx pattern of valid Australian phone number ranges and returns a Boolean ```true``` or ```false``` value.

- ```is_au_landline("0212345678")``` can be used to validate an Australian landline number
- ```is_au_mobile("0412345678")``` can be used to validate an Australian mobile number
- ```is_au_smartnum("1800123456")``` can be used to validate an Australian smart number
- ```is_au_number("0812345678")``` can be used to validate any Australian phone number

It can also consider fictional numbers designated by the ACMA to be invalid as of the v1.1.0 release of this module by setting the ```blockFiction``` parameter to ```True```. By default, fictional numbers will **not** be invalidated.

However, please note that there are limitations to this type of validation:
 - It cannot validate if the geographical code of a landline number does exist (These types of validation may be supported in a future release)
 - It cannot validate if the mobile number is in a range associated with a specific mobile carrier (These types of validation may be supported in a future release)
 - It cannot validate if the mobile number is connected to a specific mobile carrier (Mobile number porting makes this difficult to determine with certainty)
 - It cannot validate if the phone number is allocated to a or belongs to the subscriber (Only the phone carrier can determine this with certainty, however a callback or SMS verification is typically enough for most cases)

## Example
If ```0412 345 678``` is checked as an Australian mobile number:
> ```print(ausnumtools.is_au_mobile("0412345678"))```

The output would be ```True```, as Australian mobile numbers begin with ```04``` followed by eight digits.


If ```(09) 1234 56789``` is checked as an Australian landline number:
> ```print(ausnumtools.is_au_landline("09123456789"))```

The output would be ```False```, as the ```09``` area code does not exist in Australia and is followed by more than eight digits.

If [1300 655 506](https://www.youtube.com/watch?v=7F-J26xLj4A) is checked as an Australian smart number:
> ```print(ausnumtools.is_au_smartnum("1300655506"))```

The output would be ```True```, as ```1300``` smart numbers are followed by six digits.

If ```0491 570 006``` is checked as an Australian landline or mobile number _and_ checked against the ACMA's designated fictional numbers:
> ```print(ausnumtools.is_au_number("0491570006", blockFiction=True))```

The output would be ```False```, as this Australian mobile number is designated for fictional use by the ACMA and is therefore not available to subscribers.

## Install
AUSnumtools is listed on the Python Package Index and can be download via Python's package manager, pip.

> ```pip install ausnumtools```

Then, the module can be imported into the desired Python script.

> ```import ausnumtools```

Alternatively, the module can be packaged and installed manually. Please consult Python's documentation for such instructions.


