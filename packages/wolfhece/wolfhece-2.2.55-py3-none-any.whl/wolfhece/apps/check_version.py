import pkg_resources

from .version import WolfVersion

def validate_version(expected_version:str):

    # Test de la version afin de s'assurer que les dernières fonctionnalités sont présentes
    major, minor, patch = str(WolfVersion()).split('.')
    major = int(major)
    minor = int(minor)
    patch = int(patch)

    major_expected, minor_expected, patch_expected = expected_version.split('.')
    major_expected = int(major_expected)
    minor_expected = int(minor_expected)
    patch_expected = int(patch_expected)

    test = major == major_expected and minor == minor_expected and patch >= patch_expected

    if test:
        return 'Version correcte'
    else:
        return 'Version incorrecte'

def validate_package_version(expected_version:str):
    # Test de la version afin de s'assurer que les dernières fonctionnalités sont présentes
    # Obtenir la version du paquet 'wolfhece' dans l'espace de
    # stockage des paquets de l'environnement Python actif.
    # Potentiellement différente de la version accessible via le PATH
    # en fonction de la amchine utilisée.
    pkg_wolfhece = pkg_resources.get_distribution('wolfhece')
    locversion_pkg = pkg_wolfhece.version
    major, minor, patch = str(locversion_pkg).split('.')
    major = int(major)
    minor = int(minor)
    patch = int(patch)

    major_expected, minor_expected, patch_expected = expected_version.split('.')
    major_expected = int(major_expected)
    minor_expected = int(minor_expected)
    patch_expected = int(patch_expected)

    test = major == major_expected and minor == minor_expected and patch >= patch_expected

    if test:
        return 'Version correcte'
    else:
        return 'Version incorrecte'

