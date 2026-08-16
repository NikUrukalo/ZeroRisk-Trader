from functools import wraps
from Presentation.bottleext import get, post, run, request, template, redirect, static_file, url, response, template_user

from Services.transakcije_service import TransakcijeService
from Services.auth_service import AuthService
import os

# Ustvarimo instance servisov, ki jih potrebujemo. 
# Če je število servisov veliko, potem je service bolj smiselno inicializirati v metodi in na
# začetku datoteke (saj ne rabimo vseh servisov v vseh metodah!)

service = TransakcijeService()
auth = AuthService()


# privzete nastavitve
SERVER_PORT = os.environ.get('BOTTLE_PORT', 8080)
RELOADER = os.environ.get('BOTTLE_RELOADER', True)




 # Dokler nimate razvitega vmesnika za dodajanje uporabnikov, jih dodajte kar ročno.
#auth.dodaj_uporabnika('gasper', 'admin', 'gasper')
if __name__ == "__main__":
   
    run(host='localhost', port=SERVER_PORT, reloader=RELOADER, debug=True)