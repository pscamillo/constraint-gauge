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

### A2.2 — 2026-07-28 — tau das anotacoes (motivado por sean/bruniss e
Paul Henderson, #general; substitui A2.1 como regra primaria)
Critica aceita: espacamento winding-a-winding nao e uma constante com
significado, e raio ao umbilicus nao correlaciona com winding sob
deformacao (o crop do Paul demonstra variacao drastica em curta
distancia). Regra nova, sem geometria: tau(p) = 0.5 x distancia ao
ponto anotado mais proximo em winding adjacente na MESMA collection —
medido no ponto, sem constante, sem eixo, sem modelo radial. Cadeia de
fallback onde a anotacao e esparsa: min(tau_anotacao, tau_tabela A2.1,
tau_mediano 3.3) — o mais apertado vence; apertado custa cobertura,
nunca acuracia. Demonstrado em tests/test_gt_tau.py: definido em 100%
dos pontos do sintetico, M1 1.000 sem geometria alguma. A tabela
radial do A2.1 fica rebaixada a fallback.

### A3.1 — 2026-07-28 — extracao de GT das meshes verificadas
(implementa A3; regra sem geometria, coerente com A2.2)
Fonte: segmentos GP verificados por humanos, formato tifxyz, na
variante registrada no mesmo volume das anotacoes quando existir
(PHercParis4/segments/<id>/mesh/<id>-on-<volume>-<um>.tifxyz).
Atribuicao de winding SEM eixo e SEM constante: ao longo da linha media
do eixo de arco, cadeia de auto-proximidade — o proximo no e o ponto
3D mais proximo entre os que ja deram a volta (corda < 0.5 x arco,
criterio adimensional); winding(u) = indice do intervalo da cadeia. A
malha conta as proprias voltas.
Overlap (aviso do sean): cada mesh e uma collection isolada, pares
entre meshes nao existem; primeira e ultima volta descartadas por
padrao (trim=1). O tifxyz merged do 1667 (djosey) roda com trim=0.
Frames: cada braco de GT pontua no frame do volume em que a mesh esta
registrada; nao se comparam frames diferentes.
Validado em 20231022170901 (Paris 4): 8 voltas detectadas, batendo a
contagem independente de alyalya em #general; arcos por volta
monotonicos 16511 -> 12264 vox; 41755 pontos pos-trim, ~19x a
densidade do braco de anotacoes.

### A7 — 2026-07-28 — proveniencia sujeito-GT (motivado por Iyán Dopico,
que a declarou contra o proprio interesse; texto aprovado por ele antes
do commit)
S-F: cadeia de constraints do IyanDopico/vesuvius-sheet-tools. A cadeia
descende dos mesmos stitched labels que formam o GT-2 (1218): sujeito e
regua compartilham parent nesse braco. Regra geral adotada: TODO sujeito
declara proveniencia contra CADA braco de GT antes de ser pontuado, e
todo resultado publicado sai rotulado independent / shared-parent /
in-sample. Para S-F: Paris 4 = teste independente; 1218 = reportado com
asterisco shared-parent. Para S-D (E1, do autor deste benchmark): janela
z10000-11000 = in-sample; demais pares = independent. Nenhuma linha
shared-parent ou in-sample e comparavel entre sujeitos sem o rotulo.

### A3.2 — 2026-07-29 — cruzamento por profundidade + consenso de linhas
(substitui o detector de cadeia do A3.1; motivado por falha em mesh real)
Regra: um retorno de volta e o primeiro trecho contiguo onde
corda <= 5 x (menor corda a frente) E corda < 0.5 x arco; o no e o
argmin da corda nesse trecho. A menor corda a frente E uma medicao do
espacamento local entre folhas, entao ambos os criterios sao
adimensionais e auto-derivados: sem eixo, sem constante de pitch.
Consenso: a cadeia roda em 5 linhas bem cobertas do grid; a contagem
modal vence e a melhor linha modal da as fronteiras. Uma dobra que
engana uma linha nao engana cinco alturas.
Resultado nas 10 meshes GP do Paris 4: 10/10 extraem, arcos monotonicos
em todas; a mesh que falhava (20231005123336) sai de 1 volta espuria de
93k vox para 4 voltas de ~23k (4 x 23.3k = arco total, ao voxel).
Quatro meshes contam 1 volta a menos que a leitura de linha unica:
direcao conservadora — subcontar perde cobertura, nunca corrompe
rotulos, pois as voltas mantidas sao internamente consistentes.
Bracos totais: 271864 pontos de mesh + 2173 anotados, mesmo frame
(volume 20260411134726, z max 75784 comporta ambos).

### A7.1 — 2026-07-29 — proveniencia no codigo (implementa A7)
Registro em data/provenance.json: por sujeito, um rotulo por braco de
GT (independent / shared-parent / in-sample) mais nota de justificativa.
O runner carimba cada summary com subject, gt_arm, provenance e
publishable_as_headline; sujeito ou braco nao declarado sai UNDECLARED
com aviso. O bloqueio e social, nao tecnico: linha sem rotulo nao se
publica. Declarado hoje: winding-sync/l1 e /bfs (independent nos tres
bracos), E1 (in-sample no braco anotado; E1/held-out independent),
cadeia do Iyan (shared-parent no 1218, independent no Paris 4, por
declaracao do autor), variante angle-binned da alyalya (independent).

### A3.3 — 2026-07-29 — trim adaptativo e collection de winding unico
O trim de emenda (A3.1) so se aplica quando sobram >= 2 windings; caso
contrario roda sem trim. Collection que ainda assim fica com um unico
winding e DESCARTADA: sem winding vizinho nao ha par dw>=1 nem tau
medido, entao carregar esses pontos so os exporia ao fallback frouxo.
Efeito nas 10 meshes do Paris 4: 20231031143852 e 20231106155351
recuperadas com trim=0 (3 windings cada, +22853 pontos), 20231210121321
descartada (1 volta). Braco final: 9 meshes, 289171 pontos, tau A2.2
medido em 100% deles, faixa 3.4-37.5 vox. O fallback mediano deixa de
ser usado no braco de meshes.

### A8 — 2026-07-29 — escala (correcao de implementacao, sem efeito em regra)
build_pairs passa a contar pares por histograma de windings e amostrar
por bloco: memoria O(max_pairs), nao O(todos os pares). Vizinho mais
proximo (matcher e tau A2.2) passa a usar KD-tree com fallback para
forca bruta em blocos. Nenhum criterio mudou; o mesmo self-test que
consumia 31 GB e nao terminava agora roda em 2.4 s com 775 MB.

### A6.1 — 2026-07-29 — estimador e curva de convergencia da arbitragem
(registra o metodo ANTES de qualquer medicao real; o veredito continua
sendo o do 6.2)
Dois estimadores reportados lado a lado. NEAREST: distancia de cada
ponto anotado ao vizinho mais proximo em winding adjacente, mediana
sobre pontos — e exatamente 2x a tolerancia A2.2, isto e, a grandeza
contra a qual um gerador realmente compete. E um LIMITE SUPERIOR do
espacamento perpendicular: dois pontos anotados raramente estao
perpendiculares atraves do vao. ALLPAIRS: mediana sobre todos os pares
dw=1, leitura literal do 6.1, reportada como teto.
Curva de convergencia: o vies do nearest encolhe com a densidade de
amostragem. Amostrando o mesmo braco em varias densidades traca-se uma
curva decrescente cujo limite e o espacamento fisico. Lei de
convergencia derivada da geometria: o parceiro mais proximo esta a
sqrt(d^2 + r^2) com r^2 ~ A/n, entao mediana^2 = d^2 + b/n, e o
intercepto do ajuste linear de mediana^2 contra 1/n da d^2. Intervalo
por bootstrap sobre os pontos de GT (curva refeita em cada replica).
Validado em tests/test_pitch.py contra folhas sinteticas de espacamento
CONHECIDO (180 um): estimador nunca subestima, decresce com densidade,
limite extrapolado 181.9 um (erro 1.1%, r2 0.999), allpairs 4971 um
confirmando que e teto e nao competidor. Registro de erro: o primeiro
modelo tentado (linear em n^-1/2) subestimava 16% e foi rejeitado pelo
proprio teste sintetico antes de qualquer contato com dado real.

### A6.2 — 2026-07-29 — papeis dos dois bracos na arbitragem
(registrado ANTES de qualquer medicao real)
Braco de MESHES (A3.1/A3.3) e o ARBITRO: nem o atlas (187.3) nem o
winding-sync (225) usaram os segmentos GP verificados como insumo.
Braco ANOTADO tem DEPENDENCIA DECLARADA com o 187.3: o atlas deste
autor foi calibrado contra anotacoes humanas do Paris 4, entao ele
partilha insumo com esse claim, ainda que grandeza e metodo sejam
outros. Consequencia fixada antes do numero: uma confirmacao do 187.3
que venha apenas do braco anotado NAO conta como confirmacao. Um
veredito contra qualquer dos dois claims vale nos dois bracos. Regra
6.4 aplica-se igualmente ao 225 e ao 187.3: cada autor ve antes.

### A6.4 — 2026-07-29 — wrap-skip correction, and the invalidation of
the run that preceded it
INVALIDATION. The 12:xx mesh run printed verdict (a), favouring this
author's own 187.3, and it does not count. The exclusion threshold that
produced it (implied/measured < 0.8) was chosen AFTER seeing the table
of ratios, and the choice decides the verdict: the median over all nine
meshes is 248.9 um, compatible with 225; over the five survivors it is
180.0 um, compatible with 187.3. A post-hoc criterion that moves the
answer to the author's own claim is exactly the degree of freedom
pre-registration exists to remove. Not published, not counted.
RULE, stated by principle rather than fitted. A spiral whose arc per
wrap shrinks by dA implies radial growth dA/2pi per wrap; comparing
that with the measured gap gives ratio = implied/measured. If the chain
merged k wraps into one, the measured gap is k times the true spacing
and the ratio lands near 1/k. So: k = round(1/ratio) applied when
k >= 2, and the mesh is ACCEPTED only if the corrected ratio falls in
[0.75, 1.6], the band that unskipped meshes occupy on geometric
grounds (measured slightly below implied because scrolls are not
circular). The correction predicts its own factor before that factor is
known, so it is falsifiable: a mesh whose CORRECTED ratio still misses
the band is rejected, not rescaled again.
The bootstrap resamples MESHES, not points: adjacent grid cells measure
nearly the same gap, and point-level resampling gave a spurious 0.7 um
interval.
Verdicts from the next run under this rule count, whichever way they
fall.
