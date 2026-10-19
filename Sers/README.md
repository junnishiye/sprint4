# GoodCharge — Gestão inteligente de recarga veicular com geração solar simulada

**Disciplina:** Soluções em Energias Renováveis e Sustentáveis  
**Desafio de referência:** proposta acadêmica contextualizada na GoodWe  
**Simulador:** [Projeto GoodCharge no Wokwi](https://wokwi.com/projects/475074425949813761)

## Equipe

- Gabriel Silveira
- João Vitor Jun
- André Félix
- Henrique Aragão
- Davi Pacheco

---

## 1. Resumo do projeto

O **GoodCharge** é um protótipo acadêmico de gerenciamento de recarga de veículos elétricos. Desenvolvido no simulador Wokwi com Raspberry Pi Pico e MicroPython, o sistema modela a relação entre uma fonte renovável simulada, uma potência de recarga selecionável, uma reserva energética interna e até três veículos conectados a estações de carregamento.

Um fotoresistor (LDR) fornece uma leitura analógica usada como aproximação da geração solar. Um potenciômetro define a potência de recarga solicitada. O programa calcula uma disponibilidade estimada, mantém uma variável que representa a carga de uma bateria central, distribui a potência estimada entre as estações ativas e apresenta informações em quatro displays LCD 16×2. Três LEDs sinalizam os estados de recarga definidos pelo código: autorizada, reduzida ou bloqueada.

A solução demonstra, em escala didática, como sensores, processamento embarcado, interface visual e lógica de controle podem cooperar para apoiar decisões de gerenciamento energético. **Não é um carregador elétrico comercial real nem mede energia fotovoltaica real**: a geração é inferida de uma leitura do LDR, e a recarga dos carros é representada por variáveis de software.

## 2. Problema e objetivos

### Problema abordado

Uma instalação que carrega vários veículos precisa administrar a potência disponível, evitar que a demanda de recarga ultrapasse o orçamento energético definido e informar ao operador quando a recarga pode ocorrer integralmente, precisa ser reduzida ou deve ser bloqueada. Quando a geração fotovoltaica varia, um sistema de controle pode ajustar a carga e aproveitar melhor a energia renovável disponível.

### Objetivo geral

Construir uma simulação interativa de gerenciamento de recarga veicular que relacione a geração renovável simulada, a potência solicitada e a presença de até três veículos, expondo os principais estados operacionais ao usuário.

### Objetivos específicos

1. Simular uma variação de geração por meio do LDR e de sua leitura analógica.
2. Permitir o ajuste da potência nominal solicitada com um potenciômetro.
3. Detectar até três estações por entradas digitais e dividir a saída calculada entre os veículos conectados.
4. Modelar percentuais de bateria de uma reserva central e dos veículos.
5. Exibir geração, consumo acumulado, potência selecionada, potência de saída, disponibilidade estimada e estado de recarga.
6. Relacionar o controle de carga ao uso eficiente de energia renovável, reconhecendo as limitações da simulação.

## 3. Arquitetura e integração dos sistemas

A arquitetura combina quatro camadas: **aquisição de entradas**, **processamento e lógica de controle**, **modelo virtual dos veículos** e **apresentação dos estados**. O diagrama abaixo foi reconstruído com base nas declarações de pinos e chamadas visíveis em `main.py`; ele representa a arquitetura lógica do software, e não a disposição física exata dos componentes na tela do Wokwi.

![Arquitetura funcional do GoodCharge](assets/arquitetura_goodcharge.png)

### 3.1. Aquisição de dados

- **Fotoresistor LDR — `ADC(28)`:** fornece a leitura analógica usada por `CalcularVoltagem()` como estimativa de potência de geração. O sensor mede a resposta elétrica associada à iluminação; ele não mede diretamente watts nem substitui um sensor de corrente, tensão ou um medidor fotovoltaico. Para um protótipo físico seria necessário calibrar a relação entre irradiância, potência do arranjo e leitura elétrica.
- **Potenciômetro — `ADC(27)`:** a função `Recarga()` converte o resultado `read_u16()` em uma potência solicitada nominal entre aproximadamente **0 e 6.500 W**. A conversão é uma escala matemática do valor ADC, não uma medição da potência real entregue ao veículo.
- **Entradas digitais das estações — GP11, GP12 e GP13:** o código lê três pinos digitais para identificar as estações ativas. Cada entrada corresponde a um veículo (`carro1`, `carro2` ou `carro3`).

### 3.2. Processamento embarcado

O Raspberry Pi Pico executa o `main.py` em MicroPython. O laço contínuo coleta as entradas, estima a potência de geração, calcula uma saída de recarga, atualiza as variáveis de bateria, trata as estações conectadas e atualiza os indicadores. O `time.sleep(0.25)` estabelece uma pausa nominal de 250 ms por ciclo, equivalente a quatro ciclos por segundo antes de considerar o tempo gasto nas operações.

As funções centrais declaradas no código são:

| Função | Responsabilidade observada no código | Limite de interpretação |
|---|---|---|
| `CalcularVoltagem(lux)` | Converte a leitura ADC do LDR em uma estimativa rotulada no restante do código como potência em watts. | O nome sugere tensão, mas o valor é tratado como potência; |
| `Recarga()` | Converte o potenciômetro em potência nominal solicitada e aplica uma regra de redução/bloqueio relacionada ao percentual da bateria central. | Não mede a potência elétrica real. A variável global `bloqueado` também afeta a autorização. |
| `Bateria(energiaDisponivel)` | Atualiza `energiaArmazenada`, limita o acumulador a 0–50.000W e calcula `porcentagemBateria`. | Não há nenhuma bateria na realidade, utilizando apenas de uma string para escrever a energia restante. |
| `Conectar()` | Conta estações digitais ativas e distribui a saída calculada pelos veículos conectados, atualizando seus objetos e o contador `consumo`. | A variável `consumo` soma valores de potência por ciclo, não energia acumulada fisicamente dimensionada. |
| `VerificarCarregamento(potencia)` | Aciona os LEDs e devolve um texto de estado. | O argumento recebido não é usado; a decisão depende da porcentagem da bateria central e de `bloqueado`, e não diretamente da disponibilidade calculada. |

### 3.3. Modelo dos veículos — `carro.py`

O arquivo `carro.py` é importado por `main.py` e instanciado três vezes por meio de `carro.Carro()`. O código principal consulta os atributos `marca`, `placa` e `porcentagemBateria`, chama `Carregar(energiaConsumida)` quando uma estação está ativa e chama `CriarNovo()` quando um veículo que chegou a 100% é desconectado. Assim, cada estação possui um estado virtual próprio.

A função interna de cada método deve ser interpretada a partir da versão completa de `carro.py` incluída no projeto Wokwi. A documentação aqui descreve as interfaces que o `main.py` efetivamente utiliza sem presumir detalhes internos que não estejam visíveis nesse arquivo principal.

### 3.4. Saídas e interface

**LEDs de estado**

| Pino declarado | Cor | Regra escrita em `VerificarCarregamento()` |
|---|---|---|
| GP1 | Verde | Percentual da bateria central ≥ 30% e `bloqueado == False`: “Recarga Autorizada”. |
| GP5 | Amarelo | Percentual > 1% e `bloqueado == False`, quando não atende à condição verde: “Recarga Reduzida”. |
| GP9 | Vermelho | Demais casos: “Recarga Bloqueada”. |

**Displays LCD 16×2**

O programa cria quatro objetos `I2cLcd`, agrupados em dois barramentos I²C:

| Objeto no código | Barramento e pinos declarados | Endereço | Conteúdo pretendido |
|---|---|---|---|
| `lcdInfo` | I²C1 — SDA GP26, SCL GP27 | `0x27` | Geração estimada e consumo acumulado. |
| `lcdSaidaRecarga` | I²C1 — SDA GP26, SCL GP27 | `0x26` | Potência solicitada e saída de recarga calculada. |
| `lcdStatus` | I²C0 — SDA GP20, SCL GP21 | `0x27` | Disponibilidade estimada e texto do status. |
| `lcdBateria` | I²C0 — SDA GP20, SCL GP21 | `0x26` | Percentual e barra textual da bateria central. |

Os endereços `0x27` e `0x26` aparecem em ambos os barramentos; isso não significa colisão por si só, pois cada par está associado a uma instância I²C diferente. A compatibilidade real depende da pinagem e dos dispositivos descritos em `diagram.json`.

![Mapa lógico de pinos do GoodCharge](assets/mapa_pinos.png)

**Monitor serial**

A saída serial lista o estado de cada estação, marca, placa e percentual dos três veículos, além do percentual da bateria central em representações decimal, binária e hexadecimal. Essas informações são úteis para depuração e para observar a execução da simulação.

### 3.5. Fluxo operacional

![Fluxograma de operação do GoodCharge](assets/fluxo_operacional.png)

Em cada ciclo, o programa estima a geração a partir do LDR e obtém uma potência solicitada do potenciômetro. Em seguida calcula `disponivel = potencia - Recarga()`, atualiza o acumulador da bateria central, trata as estações conectadas e atualiza as telas e os LEDs. É importante notar que **o valor de `disponivel` é apresentado no LCD, mas não é o critério utilizado pela função atual para escolher a cor do LED**. Portanto, a implementação ainda não garante que o status visual corresponda diretamente ao balanço geração–demanda.

## 4. Justificativa de alinhamento ao desafio GoodWe e à disciplina

A proposta se relaciona ao desafio de pensar um carregador de veículos elétricos que use melhor a energia disponível e gerencie a recarga conforme as condições do sistema. A GoodWe apresenta carregadores veiculares da linha HCA/HCA G2 integráveis a sistemas fotovoltaicos e de armazenamento, com opções de gerenciamento e monitoramento; isso constitui uma referência real para a motivação do protótipo ([GoodWe — HCA G2](https://br.goodwe.com/carregadores-hca-g2-goodwe)). **É uma prova de conceito acadêmica inspirada no problema de gerenciamento energético**.

O alinhamento com a disciplina “Soluções em Energias Renováveis e Sustentáveis” está na representação da geração solar, no balanço entre oferta e demanda, na tentativa de priorizar o uso consciente da potência e na discussão das limitações de um controle automático. O uso do LDR torna a simulação interativa: quando o nível de luz muda, a leitura usada como geração também muda, permitindo observar como um controlador precisaria reagir à variabilidade de uma fonte renovável.

| Elemento | Ponto do desafio que aborda | Benefício potencial e limite atual |
|---|---|---|
| LDR e entrada ADC | Representar variação da geração renovável. | Permite experimentar condições de luminosidade sem um painel real; precisa de calibração para representar potência real. |
| Potenciômetro | Simular demanda/potência escolhida pelo usuário ou pelo controlador. | Facilita testar vários níveis de potência; A saída pode alterar dependendo das condições. |
| Contagem de até três estações | Considerar carregamento simultâneo. | Demonstra compartilhamento básico de potência; ainda não há algoritmo de otimização por prioridade, prazo, tarifa ou necessidade de cada carro. |
| Modelo de bateria central e baterias virtuais | Representar armazenamento e estado de carga. | Ajuda a ilustrar uma política de controle. |
| LEDs e LCDs | Tornar o sistema observável para o operador. | Melhora a transparência e a depuração. |
| MicroPython no Pico | Automatizar a leitura, cálculo e sinalização. | Demonstra integração de sensores e lógica embarcada com baixo custo. |

## 5. Resultados quantitativos e qualitativos

### 5.1. Valores quantitativos identificáveis no código

Os valores abaixo são **parâmetros e limites definidos no código**, sem comprovações com valores reais ou pararelo com o real consumo elétrico.

| Parâmetro | Valor extraído do código | Interpretação correta |
|---|---:|---|
| Estações/veículos virtuais | 3 | O programa verifica três entradas digitais, GP11, GP12 e GP13. |
| Displays | 4 unidades, 16×2 caracteres cada | São endereçados por dois barramentos I²C. |
| LEDs de estado | 3 | Verde, amarelo e vermelho, em GP1, GP5 e GP9. |
| Frequência nominal de atualização | Pausa de 0,25 s | Aproximadamente 4 ciclos/s, desconsiderando o tempo de processamento. |
| Escala da saída selecionada | 0–6.500 W | Conversão linear do ADC do potenciômetro em `Recarga()`. |
| Limite interno da bateria central | 50.000 W | Varia o tamanho da string da bateria no display de acordo com a energia armazenada. |
| Limiar para estado verde | 30% | Percentual da bateria central simulada, com bloqueio falso. |
| Limiar inferior da recarga reduzida | Acima de 1% | Abaixo ou igual a 1%, o código segue pela condição de bloqueio. |
| Escala nominal de geração | Próxima de 0–5.000 W pretendidos | Com uma limitação do fotorresistor de não chegar em 0, apenas 0,1. |


### 5.2. Resultados qualitativos demonstráveis

- **Aquisição de dados simulados:** a leitura do LDR fornece uma entrada variável para os testes, e o potenciômetro permite alterar a potência de recarga solicitada.
- **Automação:** o ciclo principal realiza leituras, cálculos, atualização de estados e escrita nos displays sem intervenção manual a cada etapa.
- **Gestão multiestação:** há lógica para contar até três conexões e dividir a saída calculada entre os veículos reconhecidos como conectados.
- **Observabilidade:** os quatro displays e a saída serial expõem valores internos importantes para compreender e depurar o protótipo.
- **Representação de estados:** o sistema implementa três sinalizações distintas, de acordo com a bateria simulada.

## 6. Avaliação crítica: sustentabilidade, automação e eficiência

### Sustentabilidade

O principal ganho sustentável potencial é a **lógica de associar a recarga à disponibilidade de energia renovável**, permitindo pensar em maior autoconsumo fotovoltaico e menor dependência de energia de outras fontes nos momentos favoráveis. O uso do LDR permite demonstrar de maneira acessível que a oferta solar é variável, o que é essencial ao planejar uma política de carregamento. No estágio atual, porém, não é possível quantificar emissões evitadas.

### Automação

A aquisição de entradas, a classificação da bateria, o compartilhamento entre veículos e a atualização das interfaces ocorrem em um ciclo de controle contínuo. Isso reduz a dependência de decisões manuais repetitivas e estabelece uma base para futuras regras de prioridade, o benefício é demonstrativo.

### Eficiência energética

A disponibilidade é calculada como geração estimada menos a saída de recarga solicitada. Em tese, esse balanço pode indicar quando reduzir a potência ou adiar a recarga para limitar a demanda. Assim, o protótipo apresenta os conceitos de gestão energética.

### Inovação e escalabilidade

A inovação didática está na integração de um sensor ambiental simulado, entradas analógicas de controle, modelo de bateria, recarga multiestação, interface local e lógica embarcada em uma plataforma de baixo custo. A estrutura pode servir como base para incorporar telemetria, registros históricos, regras de prioridade, tarifas dinâmicas e integração com inversor fotovoltaico.

## 7. Como executar e testar

1. Abra o [projeto GoodCharge no Wokwi](https://wokwi.com/projects/475074425949813761).
2. Varie a iluminação do fotoresistor para observar a leitura e a potência estimada.
3. Varie o potenciômetro para testar a potência de recarga solicitada.
4. Acione uma, duas e três entradas de estação e compare o rateio da potência exibido no LCD/console.
5. Observe simultaneamente os quatro LCDs, os três LEDs e as mensagens da saída serial.

## 8. Ferramentas, linguagens, sensores e componentes

| Tecnologia/componente | Utilização no projeto | Referência |
|---|---|---|
| Wokwi | Simulação virtual do circuito e execução do programa embarcado. | [Projeto GoodCharge](https://wokwi.com/projects/475074425949813761) · [Formato de `diagram.json`](https://docs.wokwi.com/diagram-format) |
| Raspberry Pi Pico / RP2040 | Microcontrolador que executa a lógica e disponibiliza GPIO, ADC e interfaces I²C. | [Documentação oficial Raspberry Pi Pico](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) |
| MicroPython | Linguagem/ambiente do programa em `main.py`, com leitura ADC, pinos digitais, temporização e I²C. | [ADC](https://docs.micropython.org/en/latest/library/machine.ADC.html) · [Pin](https://docs.micropython.org/en/latest/library/machine.Pin.html) · [I²C](https://docs.micropython.org/en/latest/library/machine.I2C.html) |
| LDR/fotoresistor | Entrada analógica relacionada à iluminação; usada como proxy da geração solar. | [Wokwi — Photoresistor Sensor](https://docs.wokwi.com/parts/wokwi-photoresistor-sensor) |
| Potenciômetro | Entrada analógica usada para selecionar potência nominal de recarga. | [ADC MicroPython](https://docs.micropython.org/en/latest/library/machine.ADC.html) |
| LEDs | Indicação visual do estado de recarga segundo as regras atuais. | [GPIO / Pin MicroPython](https://docs.micropython.org/en/latest/library/machine.Pin.html) |
| LCD 16×2 com interface I²C | Exibição de geração, consumo, saída, status e percentual da bateria. | [I²C MicroPython](https://docs.micropython.org/en/latest/library/machine.I2C.html); driver `pico_i2c_lcd.py` no projeto. |
| `carro.py` | Modelo de software dos veículos e das suas baterias individuais. | Arquivo `carro.py` do projeto Wokwi. |
| `pico_i2c_lcd.py` | Camada de software para controlar os LCDs por I²C. | Arquivo `pico_i2c_lcd.py` do projeto Wokwi. |

## 9. Conclusão

O GoodCharge apresenta uma arquitetura didática para discutir a gestão de recarga de veículos elétricos a partir de uma fonte solar simulada. A integração de LDR, potenciômetro, Raspberry Pi Pico, modelo de três veículos, LEDs, displays e monitor serial torna visíveis diferentes etapas de um sistema automatizado: aquisição, estimativa, tomada de decisão e comunicação de estado.

O projeto está alinhado conceitualmente à disciplina e ao desafio de explorar o uso eficiente da energia em recarga veicular. Seu resultado atual é uma **prova de conceito em simulação**, e não uma demonstração de eficiência energética. Para evoluir em direção a uma solução tecnicamente consistente, iremos corrigir a importação e a pinagem, calibrar a relação luminosidade–potência, usar unidades físicas coerentes, vincular os estados ao balanço de energia e registrar testes repetíveis.

Com essas melhorias, o protótipo pode se tornar uma base mais robusta para estudar gestão de carga, autoconsumo fotovoltaico, compartilhamento de potência e critérios de operação sustentável em pontos de recarga.