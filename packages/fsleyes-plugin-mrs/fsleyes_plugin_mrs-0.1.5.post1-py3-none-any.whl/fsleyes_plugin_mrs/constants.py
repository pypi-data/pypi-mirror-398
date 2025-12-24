'''Define nuclei and other constants here

Will Clarke <william.clarke@ndcn.ox.ac.uk>
Copyright, University of Oxford, 2023
'''

GYRO_MAG_RATIO = {
    '1H': 42.576,
    '2H': 6.536,
    '13C': 10.7084,
    '31P': 17.235}

PPM_SHIFT = {
    '1H': 4.65,
    '2H': 4.80,
    '13C': 0.0,
    '31P': 0.0}

PPM_RANGE = {
    '1H': (0.2, 4.2),
    '2H': (0.0, 6),
    '13C': (10, 100),
    '31P': (-20, 10)}

NOISE_REGION = {
    '1H': ([None, int(-2)], [10, None]),
    '2H': ([None, int(-2)], [10, None]),
    '31P': ([None, int(-15)], [12, None])}
