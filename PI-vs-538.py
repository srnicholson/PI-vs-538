"""Compare FiveThirtyEight's odds for their "states to watch" with PredictIt
prices for each.

PI prices are grabbed from their API.
538 doesn't seem to have an API, but it would be nice to find a way to scrape
their data.
In the meantime, 538 odds for a democratic or republican win in each state are
manually entered in a CSV.
The CSV format is:
    state,dem,rep
    AZ,33.2,66.8
    CO,76.3,23.5
    ...

Jack Enneking
2016-09-08
"""

import csv
import requests
from time import sleep
from sys import exit


############  State objects  ############
# Create the main data structure: a list of objects, each representing a state.

class State:
    """Represent a state and its election probabilities."""
    def __init__(self, abbr, name=''):
        self.abbr = abbr
        self.name = name

stateNames = {
    'AZ': 'Arizona',
    'CO': 'Colorado',
    'FL': 'Florida',
    'GA': 'Georgia',
    'IA': 'Iowa',
    'MI': 'Mississippi',
    'MN': 'Minnesota',
    'NC': 'North Carolina',
    'NH': 'New Hampshire',
    'NV': 'Nevada',
    'OH': 'Ohio',
    'PA': 'Pennsylvania',
    'VA': 'Virginia',
    'WI': 'Wisconsin',
}

states = []    # main data structure: list of state objects
for abbr in sorted(stateNames):    # they'll be printed in this order, so make alphabetical now
    name = stateNames[abbr]
    states.append(State(abbr, name))


############  Read FiveThirtyEight data  ############

try:
    with open('fte.csv', newline='') as csvFile:
        reader = csv.DictReader(csvFile)    # gets each line as a dict
        fteChances = list(reader)    # a list of the line-dicts
except Exception as error:
    print('Could not find FiveThirtyEight data. Is there an "fte.csv" in this directory?')
    print('\n', error)
    exit(1)

print('Read FTE chances:')
for state in states:
    print('  ' + state.abbr + '...', end='', flush=True)    # Let the user know we're trying
    foundIt = False
    for row in fteChances:    # each state in fte.csv
        if state.abbr == row['state']:    # e.g. "AZ"
            state.fteDemChance = float(row['dem'])    # e.g. "33.2"
            state.fteRepChance = float(row['rep'])    # e.g. "66.8"
            foundIt = True
            print(' good!')
            break
    if not foundIt:
        print(' fail!')


############  Get PredictIt data  ############

tries = 5    # times to retry each request if it fails
urlBase = 'https://www.predictit.org/api/marketdata/ticker/'    # all urlBase are belong to us
suffix = 'USPREZ16'    # markets are e.g. AZ.USPREZ16, CO.USPREZ16
headers = {'Accept': 'application/json'}

def getContentDict(url, tries=5, delay=1):
    """Get data from the API and start parsing it."""
    for i in range(tries):
        print('.', end='', flush=True)    # dots count tries
        r = requests.get(url, headers=headers)
        if r.status_code == 200 and r.content != b'null':    # PI gives a 200 for nonexistent markets, just with null contents.
            return(r.json()['Contracts'])    # Extracts the good bits: a list of the (two) contracts.
        sleep(delay)    # wait before retrying
    raise    # if all tries fail

print('Get PI prices:')
for state in states:
    print('  ' + state.abbr + '..', end='', flush=True)    # Let the user know we're trying
    
    url = urlBase + state.abbr + '.' + suffix    # e.g. "https://www.predictit.org/api/marketdata/ticker/AZ.USPREZ16"
    try:
        contracts = getContentDict(url, 5)
    except:
        print(' fail!')
    else:
        print(' good!')
        for contract in contracts:    # contracts should be a list of the two contracts for the state
            if contract['Name'] == 'Democratic':
                state.piDemPrice = contract['BestBuyYesCost']
                state.piDemChance = state.piDemPrice * 100    # prices are /1, chances /100
            elif contract['Name'] == 'Republican':
                state.piRepPrice = contract['BestBuyYesCost']
                state.piRepChance = state.piRepPrice * 100    # prices are /1, chances /100
            else:
                print('Something fishy, though.')    # not Democratic or Republican


############  Printing  ############

colWidth = [4,3,4,3]    # adjust table spacing here

def addSign(n):
    """Format diffs for printing"""
    if int(n) > 0:
        s = '+' + format(n, '0.0f')
    else:
        s = format(n, '0.0f')
    return s

header1 = ' '.join((
    '│'.rjust(6),
    'Democrat'.center(sum(colWidth[1:]) + 2),
    '│',
    'Republican'.center(sum(colWidth[1:]) + 2),
))

header2 = ' '.join((
    'State│'.rjust(6),
    '538'.rjust(colWidth[1]),
    'PI'.center(colWidth[2]),
    'dif'.rjust(colWidth[3]),
    '│',
    '538'.rjust(colWidth[1]),
    'PI'.center(colWidth[2]),
    'dif'.rjust(colWidth[3]),
))

headerBar = '┼'.join((
    '─' * (colWidth[0] + 1),
    '─' * (sum(colWidth[1:]) + 4),
    '─' * (sum(colWidth[1:]) + 4),
))

print('')
print(header1)
print(header2)
#print('─' * len(header2))    # bar under headers
print(headerBar)

badData=[]  # will hold abbr.s of states that don't have all four values
for state in states:
    try:
        state.fteDemChance, state.fteRepChance, state.piDemPrice, state.piRepPrice
    except AttributeError:
        badData.append(state.abbr)
    else:
        fteDemPercent = format(state.fteDemChance, '0.0f') + '%'    # formatted for printing with percent sign
        piDemPercent  = format(state.piDemChance , '0.0f') + '\u00A2'    # formatted for printing with cent sign
        demDiff = addSign(state.piDemChance - state.fteDemChance)    # difference, formatted for printing with +/- sign
        
        fteRepPercent = format(state.fteRepChance, '0.0f') + '%'
        piRepPercent  = format(state.piRepChance , '0.0f') + '\u00A2'
        repDiff = addSign(state.piRepChance - state.fteRepChance)
        
        print(
            state.abbr.rjust(   colWidth[0]),
            '│',
            fteDemPercent.rjust(colWidth[1]),
            piDemPercent.rjust(colWidth[2]),
            demDiff.rjust(colWidth[3]),
            '│',
            fteRepPercent.rjust(colWidth[1]),
            piRepPercent.rjust(colWidth[2]),
            repDiff.rjust(colWidth[3]),
        )    # the goods!

if len(badData):
    print('\nInsufficient data:', ', '.join(badData))

# Happy trading!
