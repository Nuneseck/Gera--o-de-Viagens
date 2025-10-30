import json
import random
from typing import Dict, List, Optional, Tuple

class GeradorEquipamentos:
    def __init__(self, arquivo_json: str = "equipamentos.json"):
        self.arquivo_json = arquivo_json
        self.dados = self.carregar_dados()

    def carregar_dados(self) -> Dict:
        """Carrega os dados de equipamentos do arquivo JSON"""
        try:
            with open(self.arquivo_json, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                # Verifica se todos os itens têm peso definido, senão adiciona peso 1
                for categoria in ['armas', 'armaduras', 'escudos']:
                    if categoria in dados:
                        if categoria == 'armas':
                            for subcategoria in ['uma_mao', 'duas_maos', 'leves']:
                                for item in dados['armas'].get(subcategoria, []):
                                    if 'peso' not in item:
                                        item['peso'] = 1
                        else:
                            for item in dados.get(categoria, []):
                                if 'peso' not in item:
                                    item['peso'] = 1
                return dados
        except FileNotFoundError:
            print(f"Erro: Arquivo '{self.arquivo_json}' não encontrado.")
            return {"armas": {}, "armaduras": [], "escudos": []}
        except json.JSONDecodeError:
            print(f"Erro: Arquivo '{self.arquivo_json}' mal formatado.")
            return {"armas": {}, "armaduras": [], "escudos": []}

    def escolher_item_com_peso(self, lista_itens: List[Dict]) -> Optional[Dict]:
        """Escolhe um item aleatório considerando os pesos"""
        if not lista_itens:
            return None
        
        pesos = [item.get('peso', 1) for item in lista_itens]
        
        # Se todos os pesos forem 0, trata todos como se tivessem peso 1
        if sum(pesos) == 0:
            pesos = [1] * len(lista_itens)

        return random.choices(lista_itens, weights=pesos, k=1)[0]

    def gerar_arma(self) -> Tuple[Optional[Dict], str]:
        """Gera uma arma aleatória e já retorna sua categoria para evitar buscas futuras."""
        # Pesos para cada categoria de arma
        categorias = {
            'uma_mao': 40,
            'duas_maos': 40,
            'leves': 20
        }
        # Escolhe a categoria com base nos pesos
        categoria_escolhida = random.choices(
            list(categorias.keys()),
            weights=list(categorias.values()),
            k=1
        )[0]
        
        # Escolhe uma arma da lista da categoria sorteada
        lista_armas = self.dados['armas'].get(categoria_escolhida, [])
        arma = self.escolher_item_com_peso(lista_armas)
        
        # Retorna tanto a arma quanto a sua categoria
        return arma, categoria_escolhida

    def gerar_armadura(self) -> Optional[Dict]:
        """Gera uma armadura aleatória considerando pesos"""
        return self.escolher_item_com_peso(self.dados.get("armaduras", []))

    def gerar_escudo(self) -> Optional[Dict]:
        """Gera um escudo aleatório considerando pesos"""
        return self.escolher_item_com_peso(self.dados.get("escudos", []))

    def gerar_equipamentos(self, qtd_armas: int = 1, qtd_armaduras: int = 1) -> Dict:
        """Gera um conjunto de equipamentos aleatórios com combinações lógicas e otimizadas."""
        equipamentos = {
            "armas_primarias": [],
            "armaduras": [],
            "armas_com_escudos": {},
            "armas_duplas": {}
        }

        # === CORREÇÃO: Laço para gerar armaduras que estava faltando ===
        for _ in range(qtd_armaduras):
            armadura = self.gerar_armadura()
            if armadura:
                equipamentos["armaduras"].append(armadura)

        # Armazena as armas primárias junto com suas categorias
        armas_geradas_com_categoria = []
        for _ in range(qtd_armas):
            arma, categoria = self.gerar_arma()
            if arma:
                # Adicionamos a arma e sua categoria para uso futuro
                armas_geradas_com_categoria.append((arma, categoria))
                equipamentos["armas_primarias"].append(arma)
        
        # Processa cada arma primária para gerar adicionais (escudo ou arma secundária)
        for arma_primaria, categoria in armas_geradas_com_categoria:
            nome_arma = arma_primaria.get('nome', 'Arma Desconhecida')

            if categoria == 'uma_mao':
                # Lógica simplificada para escolher entre escudo, arma leve ou nada
                opcoes_adicionais = ['escudo', 'arma_leve', 'nada']
                pesos_adicionais = [70, 30, 20]
                escolha = random.choices(opcoes_adicionais, weights=pesos_adicionais, k=1)[0]

                if escolha == 'escudo' and self.dados.get("escudos"):
                    escudo = self.gerar_escudo()
                    if escudo:
                        equipamentos["armas_com_escudos"][nome_arma] = escudo
                
                elif escolha == 'arma_leve' and self.dados['armas'].get('leves'):
                    arma_leve = self.escolher_item_com_peso(self.dados['armas']['leves'])
                    if arma_leve:
                        equipamentos["armas_duplas"][nome_arma] = arma_leve
            
            elif categoria == 'leves':
                # Chance de 50% de gerar uma segunda arma leve para ambidestria
                if random.random() < 0.8 and self.dados['armas'].get('leves'):
                    outra_arma_leve = self.escolher_item_com_peso(self.dados['armas']['leves'])
                    if outra_arma_leve:
                        equipamentos["armas_duplas"][nome_arma] = outra_arma_leve
        
        return equipamentos

    def formatar_equipamento(self, equipamento: Dict, escudo: Optional[Dict] = None, arma_secundaria: Optional[Dict] = None) -> str:
        """Formata os detalhes de um equipamento como string, incluindo escudo e arma secundária se existirem"""
        if equipamento is None:
            return "Nenhum"
        
        nome_item = equipamento.get('nome', 'Item Desconhecido')
        peso_item = equipamento.get('peso', 1)
        linha_nome = f"{nome_item} (Peso: {peso_item})"

        if escudo:
            nome_escudo = escudo.get('nome', 'Escudo')
            defesa_escudo = escudo.get('defesa', '+?')
            penalidade_escudo = escudo.get('penalidade', '?')
            linha_nome += f" + {nome_escudo} (Defesa: {defesa_escudo} | Penalidade: {penalidade_escudo})"
        
        if arma_secundaria:
            nome_secundaria = arma_secundaria.get('nome', 'Arma Secundária')
            peso_secundaria = arma_secundaria.get('peso', 1)
            linha_nome += f" + {nome_secundaria} (Peso: {peso_secundaria})"

        if "dano" in equipamento:  # É uma arma
            return (
                f"{linha_nome}\n"
                f"Dano: {equipamento.get('dano', '?')} | Crítico: {equipamento.get('critico', '?')}\n"
                f"Alcance: {equipamento.get('alcance', '?')} | Tipo: {equipamento.get('tipo', '?')}\n"
                f"Habilidade: {equipamento.get('habilidade', '?')}"
            )
        elif "defesa" in equipamento:  # É armadura ou escudo (embora escudo seja tratado acima)
            return (
                f"{linha_nome}\n"
                f"Defesa: {equipamento.get('defesa', '?')} | Penalidade: {equipamento.get('penalidade', '?')}"
            )
        return linha_nome # Fallback para itens sem categoria definida

    def salvar_resultados(self, equipamentos: Dict, arquivo_saida: str = "resultados_equipamentos.txt"):
        """Salva os resultados em um arquivo TXT, sobrescrevendo o anterior"""
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            f.write("=== RESULTADOS DA GERAÇÃO DE EQUIPAMENTOS ===\n\n")
            
            # Armaduras
            if equipamentos.get("armaduras"):
                f.write("=== ARMADURAS GERADAS ===\n")
                for i, armadura in enumerate(equipamentos["armaduras"], 1):
                    f.write(f"\nArmadura {i}:\n")
                    f.write(self.formatar_equipamento(armadura) + "\n")
            
            # Armas (com escudos e armas leves secundárias se aplicável)
            if equipamentos.get("armas_primarias"):
                f.write("\n=== ARMAS GERADAS ===\n")
                for i, arma_primaria in enumerate(equipamentos["armas_primarias"], 1):
                    nome_arma = arma_primaria.get('nome', 'Arma Desconhecida')
                    escudo = equipamentos.get("armas_com_escudos", {}).get(nome_arma)
                    arma_secundaria = equipamentos.get("armas_duplas", {}).get(nome_arma)
                    f.write(f"\nArma {i}:\n")
                    f.write(self.formatar_equipamento(arma_primaria, escudo, arma_secundaria) + "\n")
            
            if not equipamentos.get("armaduras") and not equipamentos.get("armas_primarias"):
                f.write("Nenhum equipamento foi gerado.\n")
                
            f.write("\n=== FIM DOS RESULTADOS ===")

def obter_quantidade(tipo: str) -> int:
    """Obtém do usuário a quantidade de itens a gerar"""
    while True:
        try:
            qtd = int(input(f"Quantas {tipo} deseja gerar? (0-10): "))
            if 0 <= qtd <= 10:
                return qtd
            print("Por favor, digite um número entre 0 e 10.")
        except ValueError:
            print("Por favor, digite um número válido.")

if __name__ == "__main__":
    gerador = GeradorEquipamentos()
    print("=== Gerador de Equipamentos para NPCs (Tormenta 20) ===")
    print("Sistema com categorias de armas e combinações automáticas\n")

    # Obtém as quantidades do usuário
    qtd_armas = obter_quantidade("armas")
    qtd_armaduras = obter_quantidade("armaduras")

    # Gera equipamentos
    equipamentos = gerador.gerar_equipamentos(qtd_armas=qtd_armas, qtd_armaduras=qtd_armaduras)

    # Salva os resultados em arquivo
    gerador.salvar_resultados(equipamentos)

    # Exibe os resultados no console
    print("\n--- Resultados ---")
    if equipamentos.get("armaduras"):
        print("\n=== Armaduras Geradas ===")
        for i, armadura in enumerate(equipamentos["armaduras"], 1):
            print(f"\nArmadura {i}:")
            print(gerador.formatar_equipamento(armadura))
            
    if equipamentos.get("armas_primarias"):
        print("\n=== Armas Geradas ===")
        for i, arma_primaria in enumerate(equipamentos["armas_primarias"], 1):
            nome_arma = arma_primaria.get('nome', 'Arma Desconhecida')
            escudo = equipamentos.get("armas_com_escudos", {}).get(nome_arma)
            arma_secundaria = equipamentos.get("armas_duplas", {}).get(nome_arma)
            print(f"\nArma {i}:")
            print(gerador.formatar_equipamento(arma_primaria, escudo, arma_secundaria))
            
    if not equipamentos.get("armaduras") and not equipamentos.get("armas_primarias"):
        print("\nNenhum equipamento foi gerado.")
        
    print("\n\nResultados salvos em 'resultados_equipamentos.txt'")