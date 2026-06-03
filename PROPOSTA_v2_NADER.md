# Proposta Atualizada — Projeto QUESH

**Versão 2.0** — 28 de maio de 2026
**De:** Bell Walton
**Para:** Nader Jarrah Hamad

---

## 1. Resumo executivo

Esta proposta atualiza o plano original do projeto QUESH em três pontos:

1. A Fase 1 (MVP) foi entregue e está validada em produção. Aguardando aprovação no Workana.
2. A Fase 2 será expandida para incluir agentes conversacionais com IA, em conversação real e natural, tanto por voz quanto por WhatsApp.
3. O orçamento total do projeto sobe de USD 2.842,71 para USD 3.842,71 (acréscimo de USD 1.000) por causa do escopo conversacional adicional.

---

## 2. Status atual

**Fase 1 (MVP) — ENTREGUE em 28/05/2026**

Validado em testes reais no telefone do cliente:

- Importação de devedores por Excel/CSV
- Motor de IA (Claude) escolhendo canal, tom, horário e gerando mensagem personalizada
- Envio por WhatsApp (Z-API), SMS e Voz (Twilio)
- Cobrança Pix automática (Asaas) com link curto na mensagem
- Compliance CDC (horário 08-21 BRT, intervalo entre tentativas, limite diário)
- Painel web com Dashboard, Campanhas e Devedores
- Deploy em produção no Railway

---

## 3. Comparativo de ferramentas para agentes conversacionais

Após pesquisa, considero três opções para a parte de voz conversacional:

### Opção A — ElevenLabs Agents (recomendada)

A ElevenLabs é referência mundial em qualidade de voz natural por IA. Eles têm um produto próprio de agentes conversacionais (ElevenLabs Agents) que combina a voz mais realista do mercado com lógica de conversa, suporte a LLM da Anthropic (Claude) e baixa latência.

- Qualidade de voz: a melhor do mercado, emocional e fluida
- Latência: baixa (boa pra conversa natural)
- LLM: integra Claude nativamente
- Customização: configuração por agente (personalidade, voz, tom, instruções)
- Custo médio por minuto: USD 0,08 a 0,15 dependendo do plano e da voz

### Opção B — Vapi

Plataforma desenvolvedor-friendly, muito flexível. Permite usar qualquer provedor de voz (inclusive ElevenLabs por baixo), qualquer LLM, custom logic.

- Qualidade de voz: depende do provedor escolhido (geralmente ElevenLabs)
- Latência: baixa
- Customização: máxima
- Custo médio por minuto: USD 0,05 (Vapi) + USD 0,07 a 0,15 (TTS) = USD 0,12 a 0,20

### Opção C — Retell

Foco em qualidade e latência, mais simples de integrar que Vapi.

- Qualidade de voz: boa
- Customização: média
- Custo médio por minuto: USD 0,10 a 0,20

### Recomendação

**ElevenLabs Agents.** Melhor qualidade de voz, menor latência, custo médio mais baixo, integração nativa com Claude. Cumpre todos os requisitos descritos: voz natural, negociação, contexto, customização por cliente.

---

## 4. Milestones atualizados

### Milestone 1 — MVP

**Valor:** USD 1.042,71
**Status:** ENTREGUE e validado, aguardando aprovação no Workana
**Prazo:** já concluído

### Milestone 2 — Agentes Conversacionais

**Valor:** USD 1.500
**Status:** a iniciar após aprovação da Fase 1
**Prazo estimado:** 3 semanas

**Escopo:**

- Integração ElevenLabs Agents para chamada de voz conversacional em tempo real
- Bot conversacional bidirecional no WhatsApp (texto e áudio, com transcrição via Whisper)
- Camada de customização por cliente (cada cliente final do QUESH configura sua própria personalidade, tom de voz, ritmo de conversa, vocabulário, comportamento de escalação)
- Memória de conversa persistida no banco do QUESH (o agente lembra de conversas anteriores com o mesmo devedor)
- Negociação contextual (entendimento de objeções, hesitação, urgência, parcelamento)
- Guardrails legais (o agente não pode oferecer descontos ou condições não autorizadas)
- Integração total com o fluxo de cobrança existente do MVP
- Dashboard de conversas (visualização de cada interação)

### Milestone 3 — Plataforma SaaS Completa

**Valor:** USD 1.300
**Status:** a iniciar após aprovação da Fase 2
**Prazo estimado:** 3 semanas

**Escopo:**

- Autenticação multi-tenant (cada cliente final entra com sua própria conta no painel, isolado dos demais)
- Painel administrativo para o Nader (gerenciar todos os clientes da plataforma, ver uso, faturar)
- Integração CRM/ERP via API REST de entrada (clientes podem mandar base de devedores direto do sistema deles)
- Regras de compliance específicas por segmento (financeiro, varejo, telecom)
- Onboarding guiado para novos clientes assinarem o QUESH sozinhos
- Documentação técnica e materiais comerciais

---

## 5. Custos recorrentes esperados (operação)

Esses custos são **da operação** do produto, não do desenvolvimento. São repassados pelo Nader aos clientes finais no preço do serviço SaaS.

**Por chamada de voz conversacional:**
- ElevenLabs Agents: USD 0,08 a 0,15 por minuto
- Duração média de cobrança: 1 a 3 minutos
- Custo médio por chamada: USD 0,10 a 0,45

**Por mensagem WhatsApp conversacional:**
- Claude API (LLM): USD 0,001 a 0,005 por mensagem
- Whisper (transcrição de áudio): USD 0,006 por minuto de áudio
- Custo médio por interação: USD 0,01 a 0,05

**Projeção mensal por volume:**

| Volume mensal | Voz | WhatsApp conversacional | Total estimado |
|---|---|---|---|
| 1.000 chamadas | USD 100 - 450 | USD 10 - 50 | USD 110 - 500 |
| 5.000 chamadas | USD 500 - 2.250 | USD 50 - 250 | USD 550 - 2.500 |
| 10.000 chamadas | USD 1.000 - 4.500 | USD 100 - 500 | USD 1.100 - 5.000 |

**Importante:** esses custos são pagos diretamente pela conta do cliente final às plataformas (ElevenLabs, Anthropic, Twilio, Z-API). O Nader configura uma taxa de uso no preço do plano cobrado dos clientes.

---

## 6. Cronograma

- **Semana 0:** Aprovação da proposta + liberação da Fase 1 no Workana
- **Semanas 1 a 3:** Desenvolvimento da Fase 2 (Agentes Conversacionais)
- **Semana 4:** Testes e ajustes com o cliente
- **Semanas 5 a 7:** Desenvolvimento da Fase 3 (Plataforma SaaS Completa)
- **Semana 8:** Testes e ajustes finais
- **Semana 9:** Entrega final, transferência e documentação

---

## 7. Resumo financeiro

| Fase | Valor | Status |
|---|---|---|
| Fase 1 (MVP) | USD 1.042,71 | Entregue, escrow no Workana |
| Fase 2 (Agentes Conversacionais) | USD 1.500,00 | A iniciar |
| Fase 3 (Plataforma SaaS) | USD 1.300,00 | A iniciar |
| **Total** | **USD 3.842,71** | |

Comparado ao plano original de USD 2.842,71, são USD 1.000 a mais, distribuídos entre Fase 2 e Fase 3, justificados pelo escopo conversacional adicional solicitado.

---

## 8. Próximos passos

1. Validação desta proposta com os sócios
2. Aprovação e liberação da Fase 1 no Workana
3. Assinatura da Fase 2 no Workana
4. Início imediato do desenvolvimento da Fase 2

---

## 9. Por que esse caminho

- **Usa o estado da arte do mercado de IA conversacional.** ElevenLabs Agents é o mesmo nível de tecnologia que empresas como a Salesforce e Klarna estão usando em seus agentes de voz.
- **Mantém o controle do produto com o QUESH.** Toda a lógica de cobrança, customização por cliente, persistência de conversas e dashboard fica na nossa plataforma. Os agentes da ElevenLabs são chamados de dentro do QUESH, não substituem a plataforma.
- **Modelo de custo escalável.** Os custos por minuto/mensagem só crescem com o uso real, e são repassáveis aos clientes finais.
- **Caminho rápido para o produto completo.** 6 a 7 semanas adicionais para entregar tudo, com baixo risco técnico já que estamos usando ferramentas maduras.

---

Qualquer dúvida ou ajuste necessário antes de apresentar aos sócios, é só me avisar.

Atenciosamente,
Bell Walton
