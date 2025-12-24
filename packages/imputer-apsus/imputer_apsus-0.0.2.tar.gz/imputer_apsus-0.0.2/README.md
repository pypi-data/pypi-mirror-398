# Imputer APSUS

Biblioteca de imputação de dados com IA para conjuntos de dados de saúde, desenvolvida para o projeto APSUS.

## Funcionalidades

- **Imputação com Random Forest**: Usa aprendizado máquina para imputar valores faltantes de forma inteligente  
- **Engenharia automática de features**: Gera automaticamente features temporais e categóricas  
- **Normalização de dados**: Aplica standard scaling nas features relevantes  
- **Métricas de desempenho**: Avalia a qualidade da imputação com métricas: MSE, RMSE e MAE

## Instalação

### Pelo PyPI
```bash
pip install imputer_apsus
```

### A partir do código-fonte (desenvolvimento)
```bash
git clone https://github.com/SmartAPSUS/analisededados.git
cd imputer
python -m pip install --upgrade build wheel setuptools
python -m build
pip install dist/imputer_apsus-[versao].whl
```

## Início rápido

```python
from imputer_apsus import impute_dataframe, evaluate_imputation

# Carregue seus dados
df = pd.read_csv("your_data.csv")

# Impute valores faltantes
result_df = impute_dataframe(
    df, 
    col_to_impute="Atendimentos Totais", 
    method="random_forest"
)

```

## Formato dos dados de entrada

Seu DataFrame deve conter:
- **Data**: coluna de data (formato: DD/MM/YYYY)
- **APS**: identificador da unidade de saúde
- **Atendimentos Totais**: coluna alvo para imputação (valores a serem imputados)

Exemplo:
```
   Data          APS  Atendimentos Totais
0  01/01/2020    UBS A     150
1  01/02/2020    UBS A     0          (deve ser tratado(igual NaN) antes da imputação)
2  01/01/2020    UBS B     200
```

## Requisitos

- Python >= 3.8  
- pandas >= 1.3.0  
- numpy >= 1.21.0  
- scikit-learn >= 1.0.0


## Licença

Este projeto está licenciado sob a MIT License — veja o arquivo LICENSE para detalhes.

## Autor

Desenvolvido por Lucas Emanoel para o projeto SmartAPSUS.