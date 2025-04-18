import os
from functools import lru_cache
import json
import random

def carregar_caracteristicas(tipo):
    """Carrega características do JSON baseado no tipo de criatura"""
    caminho = os.path.join('encounters', 'caracteristicas', f"{tipo}.json")
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar características: {str(e)}")
        return {}

def gerar_caracteristicas(tipo, quantidade=1):
    """Gera características aleatórias para o tipo especificado"""
    dados = carregar_caracteristicas(tipo)
    if not dados:
        return []
    
    chaves = list(dados.keys())
    resultados = []
    
    for _ in range(quantidade):
        caracteristica = random.choice(chaves)
        resultados.append({
            'caracteristica': caracteristica,
            'efeito': dados[caracteristica]  # Corrigido: usa a variável definida acima
        })
    
    return resultados

# Interface de linha de comando (opcional)
def main():
    tipos_validos = ["humanoide", "animal", "monstro", "espirito", "morto-vivo", "constructo", "lefeu"]

    print("Escolha o tipo de criatura:")
    for idx, tipo in enumerate(tipos_validos, start=1):
        print(f"{idx}. {tipo.capitalize()}")

    try:
        escolha = int(input("Digite o número correspondente: ")) - 1
        
        if escolha < 0 or escolha >= len(tipos_validos):
            print("Opção inválida!")
            return

        tipo_escolhido = tipos_validos[escolha]
        quantidade = int(input("Quantos inimigos deseja gerar? "))

        inimigos = gerar_caracteristicas(tipo_escolhido, quantidade)

        if not inimigos:
            print("Nenhum inimigo foi gerado.")
            return

        print("\nInimigos gerados:")
        for idx, inimigo in enumerate(inimigos, start=1):
            print(f"Inimigo {idx}: {inimigo['caracteristica']} ({inimigo['efeito']})")

    except ValueError:
        print("Por favor, digite um número válido.")

if __name__ == "__main__":
    main()