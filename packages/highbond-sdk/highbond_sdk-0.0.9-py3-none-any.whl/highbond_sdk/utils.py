import pandas as pd

def to_dataframe(data):
    """
    Converte uma resposta de API ou generator/lista de dicts em um pandas.DataFrame.
    Aceita:
      - dict com chave 'data' (padrão das respostas HighBond)
      - generator/lista de dicts
    """
    if isinstance(data, dict) and "data" in data:
        return pd.json_normalize(data["data"])
    elif isinstance(data, list) or hasattr(data, "__iter__"):
        return pd.json_normalize(list(data))
    else:
        raise ValueError("Formato de dados não suportado para conversão em DataFrame.")
