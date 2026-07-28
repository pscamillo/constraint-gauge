# GATE0 — Critérios pré-registrados: benchmark de calibração de geradores de winding constraints

Projeto (nome de trabalho): constraint-gauge
Autor: pscamillo
Data do rascunho: 2026-07-27
Data da revisão e selagem: 2026-07-28
Status: FINAL PARA SELAGEM. Revisado pelo autor em 28/07 (τ mantido,
hipótese de ablação mantida com direção, juiz da arbitragem mantido).
Após selar: mudanças só por adendo datado, nunca edição.

---

## 0. Objetivo

Medir a acurácia por-localização e a calibração de confiança de geradores
automáticos de winding constraints contra ground truth humano, com critérios
definidos antes de qualquer número ser produzido.

O benchmark mede; não propõe gerador novo. Resultado nulo ("nenhum gerador
atual atinge o limiar X") é entregável válido.

## 1. Sujeitos (fixados antes de rodar)

- S-A: abundantjoe/winding-sync (commit pinado no dia da primeira medição;
  registrar hash aqui por adendo).
- S-B: cadeia de constraints do IyanDopico/vesuvius-sheet-tools
  (scripts/constraints, mesmo regime de pin).
- S-C: baseline BFS (solve_bfs_tree do winding-sync, rodando no MESMO grafo
  de S-A — isola solver de gerador).

Sujeitos adicionais só por adendo. Nenhum sujeito é medido publicamente sem
DM prévia ao autor (ver §7).

## 2. Ground truth

- GT-1: pares anotados humanos do spiral-input PHercParis4
  (HF snapshot a pinar; base dos 706 pares binados por radius pelo Iyán).
- GT-2: pares dos labels stitched do PHerc1218 (9.054 pares; controle
  plano-a-1,001 já publicado).
- GT-3 (opcional, adendo): as 278 fiber line annotations novas do time
  (HF buckets/scrollprize/datasets/tree/spiral/PHercParis4, upload 27/07)
  — só entram se o formato permitir extração de pares com a mesma regra §3.

Declaração de dependência (obrigatória em qualquer publicação):
GT-1 e GT-2 NÃO são independentes do winding atlas para fins de pitch —
o pitch 173 µm do 1218 tem o atlas como um dos três pés. Para acurácia de
winding (Δw inteiro), a dependência não se aplica: os pares são anotação
humana direta. Para a arbitragem de pitch (§6), a regra de independência
é a do §6.3.

## 3. Regra de matching anotação↔seed (pré-registrada)

3.1 Cada seed do gerador tem posição (z, y, x) em espaço de volume
    (winding-sync emite seed_coords; Iyán idem via point collections).
3.2 Um par anotado (P, Q, Δw_humano) é PONTUÁVEL para um gerador se
    existem seeds s_P, s_Q com dist(P, s_P) ≤ τ e dist(Q, s_Q) ≤ τ.
3.3 τ = 0,5 × pitch mediano do scroll, em voxels do nível medido.
    Justificativa: acima de meio pitch, o seed pode estar na folha vizinha
    e o match deixa de ser interpretável. τ é FIXO; não será ajustado
    após ver resultados.
3.4 Pares não pontuáveis contam em COBERTURA, não em acurácia. Não
    penalizam nem creditam.
3.5 Empate de vizinho mais próximo: menor distância euclidiana; empate
    exato (improvável) → menor índice de seed. Determinístico.
3.6 Sensibilidade a τ (τ/2 e 2τ) é reportada como diagnóstico, nunca
    como métrica primária.

## 4. Métricas primárias (fixadas)

- M1: exact agreement por-localização em pares adjacentes (dw=1):
      fração de pares pontuáveis com Δw_gerador == Δw_humano.
- M2: residual absoluto médio |Δw_gerador − Δw_humano| sobre pares
      pontuáveis (a métrica que melhor separou L1 de BFS em dado real:
      0,51 vs 1,75, per README do winding-sync).
- M3: curva de calibração — confiança declarada (weights) vs acurácia
      empírica, em 10 bins de quantil; ECE reportado.
- M4: cobertura — fração de pares GT pontuáveis.

Métricas secundárias/diagnósticas podem ser adicionadas por adendo, mas
nunca promovidas a primárias após a primeira medição.

## 5. Ablação pré-registrada: prior de spacing no S-A

Rodar winding-sync com CORPUS_SPACING_UM = 225,0 (default dele) e 187,3
(atlas v2), demais parâmetros idênticos. Reportar ΔM1, ΔM2, ΔM4.
Hipótese registrada: prior menor melhora M1 em Paris 4. Direção e
magnitude são resultado, não premissa — publicar qualquer que seja o sinal.

## 6. Arbitragem de pitch (187,3 vs 225)

6.1 Pergunta: qual estimador de spacing concorda com o pitch implicado
    pelos pares anotados (distância física entre pares Δw=1), nos mesmos
    scrolls, mesma resolução declarada.
6.2 Vereditos possíveis (escritos antes): (a) 187,3 compatível, 225 não;
    (b) 225 compatível, 187,3 não; (c) ambos compatíveis em regimes
    diferentes (ex.: dependência radial explica); (d) nenhum compatível;
    (e) GT insuficiente para decidir. Todos publicáveis.
6.3 Independência: o juiz é a distância física dos pares anotados
    humanos, não qualquer estimador automático. O atlas NÃO participa
    como evidência na arbitragem — só como uma das partes medidas.
6.4 Enquadramento público: medição conjunta de dois métodos, nunca
    correção de autor. Sem nome no veredito antes da DM do §7.

## 7. Conduta

7.1 DM ao abundantjoe com a spec deste documento ANTES de qualquer run
    público de S-A; idem resultados antes de post público. Mesma regra
    para o Iyán em S-B (formalidade menor, parceria existente).
7.2 Erratas afirmativas, nunca defensivas. Números públicos só derivados
    por script de agregação a partir dos CSVs (regra do aggregate.py —
    nenhum número digitado à mão em artefato público).
7.3 Artefatos públicos em inglês, registro trivial (sem travessão,
    sem tríades, uma pergunta por mensagem). Docs internos em português.

## 8. Condições externas registradas

- C1: RESOLVIDA. sean (bruniss) respondeu em DM, 27/07 21:16: o time
  não tem eval automático de geradores e não está construindo um no
  momento, e registrou que consideraria útil ("not that we dont think
  it would be useful"). Sem duplicação; publicação desimpedida.
- C2: pin de commits/snapshots de todos os sujeitos e GTs no dia da
  primeira medição, por adendo com hashes.

## 9. Selagem

Após revisão: `sha256sum GATE0_criteria.md` registrado em local público
(gist ou primeiro commit do repo) antes da primeira medição de S-A/S-B.

---

## ADENDOS (datados; o corpo acima permanece selado)

### A1 — 2026-07-28 — Pins de sujeitos e GT (cumpre C2 parcial)
- S-A winding-sync: commit 25842b6 (abundantjoe/winding-sync).
- GT-1 Paris 4 relative_windings.json: snapshot local validado em
  28/07 (2173 pontos, 254 collections, 8156 pares dw 1-6; reproduz os
  706 pares da janela z10000-11000 do trabalho de julho). Hash do
  arquivo a registrar no primeiro run pontuado.

### A2 — 2026-07-28 — tau local (motivado por Paul Henderson, #general)
Limitacao reconhecida do 3.3: tau derivado do pitch MEDIANO pode
cruzar folha onde o empacotamento local aperta (espacamento varia ~4x
dentro de um crop; binning radial do Paris 4 corre 136-259 um).
Mitigacoes ja em vigor: pares sem match custam cobertura e nunca
acuracia (3.4); o CSV por-par grava as duas distancias de match, entao
matches em regiao apertada sao auditaveis.
Correcao adotada: tau LOCAL derivado do espacamento local (raio-
dependente no Paris 4 via o binning radial ja medido; regra geral a
especificar em A2.1 antes do primeiro numero publico). O tau mediano
do 3.3 permanece como fallback onde nao ha medida local. Nenhum numero
publico sai antes de A2.1 estar commitado.

### A3 — 2026-07-28 — meshes GP como fonte de GT prioritaria
(motivado por sean/bruniss, Paul Henderson e djosey, #general)
GT-3 promovida: segmentos GP verificados por humanos do Paris 4 (lista
do sean, com overlap de wrap na emenda a descontar) e o tifxyz merged
do PHerc1667 (djosey; sem overlap). GT densa de superficie carrega
continuidade de folha que pontos esparsos nao tem, e viabiliza tau
apertado. As point collections (GT-1/GT-2) permanecem validas; a
extracao de pares das meshes sera especificada em A3.1 com a regra de
overlap explicita.

### A4 — 2026-07-28 — sujeitos adicionais
- S-D: estimador E1 do winding-ruler (autor deste benchmark).
  Reportado em duas linhas: in-sample (706 pares z10000-11000, usados
  no desenvolvimento) e held-out (todos os demais pares, nunca vistos).
  So a linha held-out e comparavel aos outros sujeitos.
- S-E: variante angle-binned radial pitch de alyalya
  (abundantjoe/winding-sync#1), a convite aceito em #general.

### A5 — 2026-07-28 — parametros operacionais do primeiro run Paris 4
pitch-um 180 (ancora humana; apenas tolerancia de matching, nao
evidencia), um-per-vox 2.4. Registrado que qualquer valor em 175-190
da os mesmos vereditos via o diagnostico tau/2-2tau do 3.6.

### A6 — 2026-07-28 — confianca por par (decisao de implementacao)
conf_par = min(conf_a, conf_b): o par vale o que vale sua ponta mais
fraca. Fixado antes de qualquer medicao de sujeito externo.

### A2.1 — 2026-07-28 — regra do tau local (implementa A2)
tau(p) = 0.5 x pitch_local(r(p)); r = distancia in-plane ao eixo do
scroll (config por scroll ou mediana (x,y) do GT); pitch_local por
lookup em tabela radial MEDIDA por scroll (data/paris4_pitch_table.json
para o Paris 4, do binning dos pares humanos de julho, 136-259 um).
Extrapolacao pelo bin mais proximo nas duas pontas da tabela — abaixo
do bin interno a mediana seria mais frouxa que o pitch local, que e o
exato risco de cruzar folha; a mediana do 3.3 so se aplica sem tabela.
Demonstrado em tests/test_localtau.py: tau mediano envenenado por
matches cruzando folha (M1 0.840), tau local limpo (M1 1.000) ao custo
de cobertura (0.830 -> 0.757). Numeros publicos desbloqueados.
