
from .optionalNJIT import optional_njit

printWarnings = True



@optional_njit( cache=True, nogil=True )   
def warnUser( source: str, message: str ) -> None:
    global printWarnings
    if printWarnings:
        print( 'Warning from: ' + source )
        print( message )
