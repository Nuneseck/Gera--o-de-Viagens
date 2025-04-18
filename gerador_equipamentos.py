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
                # Verifica se todos os itens têm peso definido
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
        total = sum(pesos)
        if total == 0:
            pesos = [1 for _ in pesos]
            total = sum(pesos)

        pesos_normalizados = [p/total for p in pesos]
        return random.choices(lista_itens, weights=pesos_normalizados, k=1)[0]

    def gerar_arma(self) -> Tuple[Optional[Dict], str]:
        """Gera uma arma aleatória considerando pesos e categorias"""
        # Escolhe primeiro a categoria da arma
        categorias = {
            'uma_mao': 40,
            'duas_maos': 40,
            'leves': 20
        }

        categoria = random.choices(
            list(categorias.keys()),
            weights=list(categorias.values()),
            k=1
        )[0]

        arma = self.escolher_item_com_peso(self.dados['armas'].get(categoria, []))
        return arma, categoria

    def gerar_armadura(self) -> Optional[Dict]:
        """Gera uma armadura aleatória considerando pesos"""
        return self.escolher_item_com_peso(self.dados.get("armaduras", []))

    def gerar_escudo(self) -> Optional[Dict]:
        """Gera um escudo aleatório considerando pesos"""
        return self.escolher_item_com_peso(self.dados.get("escudos", []))

    def gerar_equipamentos(self, qtd_armas: int = 1, qtd_armaduras: int = 1) -> Dict:
        """Gera um conjunto de equipamentos aleatórios com combinações lógicas"""
        equipamentos = {
            "armas_primarias": [],
            "armaduras": [],
            "armas_com_escudos": {},  # Dicionário para armazenar escudos associados a armas PRIMÁRIAS
            "armas_duplas": {}       # Dicionário para armazenar armas leves associadas a armas PRIMÁRIAS
        }

        # Gera as armas primárias
        for _ in range(qtd_armas):
            arma, categoria = self.gerar_arma()
            equipamentos["armas_primarias"].append(arma)

        # Processa cada arma primária para gerar adicionais
        for arma_primaria in equipamentos["armas_primarias"]:
            categoria = None
            # Determina a categoria da arma primária (pode ser mais eficiente se a categoria fosse armazenada)
            for subcategoria in self.dados['armas']:
                if arma_primaria in self.dados['armas'][subcategoria]:
                    categoria = subcategoria
                    break
            if categoria is None:
                for subcategoria in self.dados['armas']:
                    for item in self.dados['armas'][subcategoria]:
                        if item['nome'] == arma_primaria['nome']:
                            categoria = subcategoria
                            break
                    if categoria:
                        break

            if categoria == 'uma_mao':
                escudos_disponiveis = self.dados.get("escudos", [])
                armas_leves_disponiveis = self.dados['armas'].get('leves', [])

                adicional_gerado = False

                chance_escudo = 0.7
                chance_arma_leve = 0.3

                if random.random() < chance_escudo:
                    if escudos_disponiveis:
                        escudo = self.escolher_item_com_peso(escudos_disponiveis)
                        if escudo:
                            equipamentos["armas_com_escudos"][arma_primaria['nome']] = escudo
                            adicional_gerado = True
                    if not adicional_gerado and armas_leves_disponiveis:
                        arma_leve = self.escolher_item_com_peso(armas_leves_disponiveis)
                        if arma_leve:
                            equipamentos["armas_duplas"][arma_primaria['nome']] = arma_leve
                            adicional_gerado = True
                else:
                    if armas_leves_disponiveis:
                        arma_leve = self.escolher_item_com_peso(armas_leves_disponiveis)
                        if arma_leve:
                            equipamentos["armas_duplas"][arma_primaria['nome']] = arma_leve
                            adicional_gerado = True
                    if not adicional_gerado and escudos_disponiveis:
                        escudo = self.escolher_item_com_peso(escudos_disponiveis)
                        if escudo:
                            equipamentos["armas_com_escudos"][arma_primaria['nome']] = escudo
                            adicional_gerado = True
            elif categoria == 'leves':
                armas_leves_disponiveis = self.dados['armas'].get('leves', [])
                if armas_leves_disponiveis:
                    outra_arma_leve = self.escolher_item_com_peso(armas_leves_disponiveis)
                    if outra_arma_leve:
                        equipamentos["armas_duplas"][arma_primaria['nome']] = outra_arma_leve

        return equipamentos

    def formatar_equipamento(self, equipamento: Dict, escudo: Optional[Dict] = None, arma_secundaria: Optional[Dict] = None) -> str:
        """Formata os detalhes de um equipamento como string, incluindo escudo e arma secundária se existirem"""
        if equipamento is None:
            return "Nenhum"

        linha_nome = f"{equipamento['nome']} (Peso: {equipamento.get('peso', 1)})"

        if escudo:
            linha_nome += f" + {escudo['nome']} (Defesa: {escudo['defesa']} | Penalidade: {escudo['penalidade']})"

        if arma_secundaria:
            linha_nome += f" + {arma_secundaria['nome']} (Peso: {arma_secundaria.get('peso', 1)})"

        if "dano" in equipamento:  # É uma arma
            return (
                f"{linha_nome}\n"
                f"Dano: {equipamento['dano']} | Crítico: {equipamento['critico']}\n"
                f"Alcance: {equipamento['alcance']} | Tipo: {equipamento['tipo']}\n"
                f"Habilidade: {equipamento['habilidade']}"
            )
        elif "defesa" in equipamento:  # É armadura
            return (
                f"{linha_nome}\n"
                f"Defesa: {equipamento['defesa']} | Penalidade: {equipamento['penalidade']}"
            )

    def salvar_resultados(self, equipamentos: Dict, arquivo_saida: str = "resultados_equipamentos.txt"):
        """Salva os resultados em um arquivo TXT, sobrescrevendo o anterior"""
        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            f.write("=== RESULTADOS DA GERAÇÃO DE EQUIPAMENTOS ===\n\n")

            # Armaduras
            if equipamentos["armaduras"]:
                f.write("=== ARMADURAS GERADAS ===\n")
                for i, armadura in enumerate(equipamentos["armaduras"], 1):
                    f.write(f"\nArmadura {i}:\n")
                    f.write(self.formatar_equipamento(armadura) + "\n")

            # Armas (com escudos e armas leves secundárias se aplicável)
            if equipamentos["armas_primarias"]:
                f.write("\n=== ARMAS GERADAS ===\n")
                for i, arma_primaria in enumerate(equipamentos["armas_primarias"], 1):
                    escudo = equipamentos["armas_com_escudos"].get(arma_primaria['nome'])
                    arma_secundaria = equipamentos["armas_duplas"].get(arma_primaria['nome'])

                    f.write(f"\nArma {i}:\n")
                    f.write(self.formatar_equipamento(arma_primaria, escudo, arma_secundaria) + "\n")

            if not any(equipamentos.values()):
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
    if equipamentos["armaduras"]:
        print("\n=== Armaduras Geradas ===")
        for i, armadura in enumerate(equipamentos["armaduras"], 1):
            print(f"\nArmadura {i}:")
            print(gerador.formatar_equipamento(armadura))

    if equipamentos["armas_primarias"]:
        print("\n=== Armas Geradas ===")
        for i, arma_primaria in enumerate(equipamentos["armas_primarias"], 1):
            escudo = equipamentos["armas_com_escudos"].get(arma_primaria['nome'])
            arma_secundaria = equipamentos["armas_duplas"].get(arma_primaria['nome'])

            print(f"\nArma {i}:")
            print(gerador.formatar_equipamento(arma_primaria, escudo, arma_secundaria))

    if not any(equipamentos.values()):
        print("\nNenhum equipamento foi gerado.")

    print("\nResultados salvos em 'resultados_equipamentos.txt'")