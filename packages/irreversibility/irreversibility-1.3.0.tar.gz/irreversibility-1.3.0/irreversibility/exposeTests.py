

from irreversibility.Metrics.BDS import GetPValue as BDSTest
from irreversibility.Metrics.Casali import GetPValue as CasaliTest
from irreversibility.Metrics.COP import GetPValue as COPTest
from irreversibility.Metrics.CostaIndex import GetPValue as CostaTest
from irreversibility.Metrics.DFK import GetPValue as DFKTest
from irreversibility.Metrics.Diks import GetPValue as DiksTest
from irreversibility.Metrics.LocalCC import GetPValue as LocalCCTest
from irreversibility.Metrics.MSTrends import GetPValue as MSTrendsTest
from irreversibility.Metrics.PermPatterns import GetPValue as PPTest
from irreversibility.Metrics.Pomeau import GetPValue as PomeauTest
from irreversibility.Metrics.ProductOfPowers import GetPValue as ProdOfPowers
from irreversibility.Metrics.Ramsey import GetPValue as RamseyTest
from irreversibility.Metrics.Skewness import GetPValue as SkewnessTest
from irreversibility.Metrics.TernaryCoding import GetPValue as TCTest
from irreversibility.Metrics.TPLength import GetPValue as TPTest
from irreversibility.Metrics.VisibilityGraph import GetPValue as VGTest
from irreversibility.Metrics.Zumbach import GetPValue as ZumbachTest

allTests = [
    [ 'BDS', BDSTest ],
    [ 'Casali', CasaliTest ],
    [ 'COP', COPTest ],
    [ 'Costa Index', CostaTest ],
    [ 'DFK', DFKTest ],
    [ 'Diks', DiksTest ],
    [ 'Local CC', LocalCCTest ],
    [ 'MS Trends', MSTrendsTest ],
    [ 'Permutation patterns', PPTest ],
    [ 'Pomeau', PomeauTest ],
    [ 'Product of Powers', ProdOfPowers ],
    [ 'Ramsey', RamseyTest ],
    [ 'Skewness', SkewnessTest ],
    [ 'Ternary Coding', TCTest ],
    [ 'TP Length', TPTest ],
    [ 'Visibility Graph', VGTest ],
    [ 'Zumbach', ZumbachTest ],
]
