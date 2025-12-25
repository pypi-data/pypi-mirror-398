import sys

# Obtém a versão principal e secundária do Python em uso
major = sys.version_info.major
minor = sys.version_info.minor

# Constrói o nome do módulo a ser importado com base na versão do Python
if major == 3:
    if minor == 8:
        from .cd3_connector38 import CD3Connector
    elif minor == 9:
        from .cd3_connector39 import CD3Connector
    elif minor == 10:
        from .cd3_connector310 import CD3Connector
    elif minor == 11:
        from .cd3_connector311 import CD3Connector
    elif minor == 12:
        from .cd3_connector312 import CD3Connector
    elif minor == 13:
        from .cd3_connector313 import CD3Connector
    else:
        raise ImportError("Versão do Python não suportada.")
else:
    raise ImportError("Versão do Python não suportada.")