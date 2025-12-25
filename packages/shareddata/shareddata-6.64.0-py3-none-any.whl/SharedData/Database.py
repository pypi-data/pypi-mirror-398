DATABASE_PKEYS = {
    
    'TimeSeries':       ['date'],
    'Symbols':          ['symbol'],
    'Hashs':            ['hash'],
    'Accounts':         ['portfolio'],
            
    'MarketData':       ['date', 'symbol'],
    'Text':             ['date', 'hash'],
    'Portfolios':       ['date', 'portfolio'],

    'Relationships':    ['date', 'symbol', 'symbol1'],
    'Tags':             ['date', 'tag', 'symbol'],
    'Signals':          ['date', 'portfolio', 'symbol'],
    'Risk':             ['date', 'portfolio', 'symbol'],
    'Positions':        ['date', 'portfolio', 'symbol'],
    'Requests':         ['date', 'portfolio', 'requestid'],
    'Orders':           ['date', 'portfolio', 'clordid'],

    'Trades':           ['date', 'portfolio', 'symbol', 'tradeid'],
    'Options':          ['date', 'symbol', 'expiry', 'strike', 'callput'],    
}

STRING_FIELDS = ['symbol', 'tag', 'portfolio', 'requestid', 'clordid', 'tradeid', 'hash']

NUMERIC_FIELDS = ['expiry', 'strike']

PERIODS = ['D1', 'M15', 'M1', 'RT']
