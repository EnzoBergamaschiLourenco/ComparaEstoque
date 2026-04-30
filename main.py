from email_reader import buscar_link
from umovextractor import extrair_produtos
from nfextractor import extrair_dados_tabresult
from report_converter import convert_report
from addpurchase import consolidar_com_dicionario
from salesdeducer import processar_estoque as deduzir_vendas
from addpurchase import consolidar_com_dicionario



if __name__ == "__main__":
    print("--- Iniciando Fluxo de Automação de Estoque ---")

    # 1. Obter links
    linkumov = buscar_link() 
    linknf = "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=35260401157555005173651090000563311424429371%7C2%7C1%7C1%7CD9518715BD2F7807C13B726F53F5BA69CC89BD46"
    
    # 2. Extração (Gera os JSONs de entrada)
    if linkumov:
        extrair_produtos(linkumov) # Gera produtos_contagem.json
        
    if linknf:
        extrair_dados_tabresult(linknf) # Gera produtos_compra.json
        
    # 3. Vendas (Gera resultado_vendas.json)
    convert_report('relatorioABCVenda.csv', 'resultado_vendas.json')
    
    # No passo 4 do main.py:
    print("\nProcessando compras com dicionário de sinônimos...")
    consolidar_com_dicionario("produtos_contagem.json", "produtos_compra.json", "purchasedictionary.json", "estoque_adicionado_compra.json")
    
    # No passo 5 deduzir vendas do estoque somado:
    print("\nDeduzindo vendas do estoque consolidado...")
    deduzir_vendas(
        "estoque_adicionado_compra.json", 
        "resultado_vendas.json", 
        "salesdictionary.json",
        "estoque_final.json"
    )
    
    print("\n--- Processo concluído! Ficheiro 'estoque_final.json' gerado com sucesso. ---")