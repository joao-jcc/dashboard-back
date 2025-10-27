# Resumo dos Cálculos

Os cálculos de receita e inscrições deste projeto seguem critérios claros para garantir a consistência dos indicadores:

- Apenas inscrições e transações válidas são consideradas (status, cancelamento, campos obrigatórios).
- A receita reflete entradas e saídas financeiras reais, agrupadas por dias de antecedência ao evento.
- O ticket médio e a média diária de inscrições são calculados apenas sobre dados efetivos.
- Gráficos acumulados mostram a evolução temporal dos indicadores.

Essas regras garantem que os relatórios gerados sejam confiáveis para análise e tomada de decisão.

# Receita de Evento — Detalhamento do Cálculo

## 1. Seleção de Transações e Inscrições
- São consideradas apenas transações com `counts_for` igual a `both` ou `organization_only`.
- O `enrollment_id` da transação deve estar em inscrições (`inscricaos`) com:
	- `evento_id` igual ao evento analisado
	- `status` igual a `Ok` ou `Pendente`
	- `canceled` igual a `0`
- Transações com valores nulos em `amount`, `credit` ou `transaction_date` são descartadas.

## 2. Cálculo do Total de Receita (`total_revenue`)
- Para cada transação selecionada:
	- Se `credit == 1`, o valor de `amount` é somado à receita.
	- Se `credit == 0`, o valor de `amount` é subtraído da receita (estorno/saída).
- Fórmula:
	```
	total_revenue = soma(amount onde credit=1) - soma(amount onde credit=0)
	```

## 3. Gráfico de Receita Acumulada
- A receita é agrupada por `dias_antecedencia` (dias entre a transação e o início do evento).
- Para cada dia, soma-se a receita do dia e calcula-se o acumulado reverso (do início do evento para trás).
- O gráfico mostra a evolução da receita conforme a proximidade do evento.

## 4. Ticket Médio (`ticket_price`)
- Considera apenas transações com `credit == 1` (pagamentos efetivos).
- O ticket médio é a média dos valores de `amount` dessas transações:
	```
	ticket_price = média(amount onde credit=1)
	```

# Cálculo das Inscrições

- Seleciona apenas o campo `created_at` das inscrições (`inscricaos`) onde `status` está em ('Pendente', 'Ok') e `canceled = 0`.
- O número total de inscritos é o tamanho desse conjunto.
- A média diária de inscrições é calculada entre a data de abertura e a data de início do evento.
- Para o gráfico, acumulam-se as inscrições por dia de antecedência até o início do evento.


# Campos Dinâmicos

O cálculo gera a distribuição de respostas dos campos dinâmicos preenchidos.

- **Seleção:** Respostas extraídas de `serial_event_dynamic_fields` das inscrições válidas (`status` em ('Ok', 'Pendente'), `canceled = 0`).
- **Formato do Dado:** O `serial_event_dynamic_fields` contém **vários pares `id : valor`**.
- **Processamento:**
    1. **Quebra (Deserialização):** Os vários pares `id : valor` são separados e extraídos.
    2. **Busca e Filtragem:** Apenas os IDs de campo válidos para o evento são considerados.
    3. Contagem de frequência por rótulo (`label`) do campo.
- **Contagem:** Inclui `undefined` (não preenchido).
- **Exibição:** Apenas campos com **2 a 20 tipos de respostas únicas** (incluindo `undefined`).