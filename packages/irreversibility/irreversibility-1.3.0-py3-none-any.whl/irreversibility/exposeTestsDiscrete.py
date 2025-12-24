

from irreversibility.DiscreteMetrics.Gaspard import GetPValue as GaspardTest
from irreversibility.DiscreteMetrics.CostaIndex import GetPValue as CostaIndexTest
from irreversibility.DiscreteMetrics.DetBalance import GetPValue as DetBalanceTest


allTests = [
    [ 'Gaspard', GaspardTest ],
    [ 'Costa Index', CostaIndexTest ],
    [ 'Detailed Balance', DetBalanceTest ],
]
