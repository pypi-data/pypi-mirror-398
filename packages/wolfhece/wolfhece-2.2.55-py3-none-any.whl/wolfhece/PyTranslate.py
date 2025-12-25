#Test de la présence de la fonction de traduction i18n "gettext" et définition le cas échéant pour ne pas créer d'erreur d'exécution
# if not '_' in globals()['__builtins__']:
#     import gettext
#     _=gettext.gettext
import os
import gettext
if os.path.exists(os.path.dirname(__file__)+'\\..\\locales'):
    t = gettext.translation('base', localedir=os.path.dirname(__file__)+'\\..\\locales', languages=['fr'])
    t.install()
else:
    try:
        t = gettext.translation('base', localedir='wolfhece\\locales', languages=['fr'])
        t.install()
    except:
        pass

_=gettext.gettext
