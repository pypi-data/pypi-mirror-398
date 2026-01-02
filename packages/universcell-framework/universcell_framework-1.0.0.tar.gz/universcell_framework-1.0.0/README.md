# UniVersCell: Langage Numérique Universel

> **Mission:** Créer un système de contrôle d'intégrité d'architectures informatiques sans ambiguïté, fondé sur RÈGLE 0.

---

## Ce qu'il y a dans ce projet

### 📐 Fondations (PHASE 0-2)

- **RULE_0_COMPLETE.md** (900 lignes)
  - Définition formelle: "Toute affirmation est mesurable ou explicitement indéterminée"
  - Domaines numériques (ℝ, ℤ, probabilités, intervalles)
  - 7 raisons d'indétermination (NON_OBSERVÉ, FUTUR, STOCHASTIC, etc)
  - Type-checking et contraintes obligatoires

- **PRIMITIVES_SPECIFICATION.md** (700 lignes)
  - 6 primitives du langage: Variable, Relation, Constraint, Observation, Uncertain, LearningRule
  - Tous les attributs obligatoires documentés
  - Exemples valides et invalides

- **GRAMMAR_AND_VIOLATIONS.md** (500 lignes)
  - BNF grammar complet
  - Détection automatisée des 3 interdictions:
    1. Implicit Hypothesis (mots flous)
    2. Hidden State (état caché, window/aggregation oubliés)
    3. Silent Effects (learning rules sans arrêt)

### 🔧 Moteur (engine_v2.py, 450 lignes)

```python
# Valider un système contre RÈGLE 0
validator = RuleValidator(system)
is_valid, errors = validator.validate()
if not is_valid:
    print("Violations détectées:", errors)
    sys.exit(1)

# Évaluer les contraintes
evaluator = Evaluator(system)
state = evaluator.evaluate()
print(state.overall)  # VALID | VIOLATED | UNKNOWN
```

**Caractéristiques:**
- ✅ Validation stricte RÈGLE 0
- ✅ Évaluation ternaire (pas de "maybe")
- ✅ Type-checking domaines
- ✅ Confidence tracking
- ✅ JSON parser

### 📋 Cas de Test (PROOF_OF_CONCEPT/)

| Cas | Domaine | Status | Signification |
|-----|---------|--------|---------------|
| **simple_api_sla.json** | REST API | ✓ VALID | Latence & availability OK |
| **ml_pipeline.json** | ML Model | ✓ VALID | Accuracy & drift OK |
| **cloud_infra.json** | Kubernetes | ✓ VALID | Nodes & resources OK |
| **service_degradation.json** | Real Incident | ✗ VIOLATED | 3 constraints failed |

### 📖 Documentation Pragmatique

- **QUICKSTART.md** (400 lignes)
  - Structure JSON (5 min à lire)
  - 3 exemples réels
  - Patterns d'intégration
  - Debugging guide

- **LEARNING_RULES.md** (600 lignes)
  - Auto-correction (scaling, retrain, threshold adjustment)
  - Safety mechanisms (max_iterations, stop_condition)
  - 4 exemples concrets + timeline exécution
  - Audit & transparency

---

## Démarrage rapide

### 1. Tester tous les cas
```bash
python run_tests.py
```

Output:
```
✓ 4/4 tests PASSED

✓ API REST: VALID (2/2 constraints)
✓ ML Pipeline: VALID (3/3 constraints)  
✓ Cloud Infra: VALID (4/4 constraints)
✗ Service Degradation: VIOLATED (0/3 constraints) ← Alerte!
```

### 2. Évaluer un cas unique
```bash
python engine_v2.py PROOF_OF_CONCEPT/simple_api_sla.json
```

Output:
```
✓ Système conforme à RÈGLE 0
Status global: VALID
  ✓ SLA_latency: 87 < 100
  ✓ SLA_availability: 99.95 >= 99.9
```

### 3. Créer votre propre système
```json
{
    "name": "MyService",
    "variables": {
        "latency": {
            "domain": {"name": "temps", "unit": "ms"},
            "bounds": [0, 1000],
            "confidence": 0.95
        }
    },
    "constraints": {
        "sla": {
            "on": "latency",
            "operator": "<=",
            "threshold": 500,
            "domain": "temps",
            "unit": "ms",
            "window_eval": "5m",
            "aggregation_eval": "p99"
        }
    },
    "observations": [
        {
            "variable": "latency",
            "value": 450,
            "window": "5m",
            "aggregation": "p99",
            "confidence": 0.95,
            "type": "MEASURED"
        }
    ]
}
```

```bash
python engine_v2.py MyService.json
```

---

## Architecture

```
UniVersCell/
├── PHASE_0/
│   └── RULE_0.md (initial spec)
├── PHASE_1/
│   └── SYSTEM_ALGEBRA.md
├── PHASE_2_EVALUATION_ENGINE.md (specs)
├── RULE_0_COMPLETE.md          ← Fondation formelle
├── PRIMITIVES_SPECIFICATION.md  ← 6 primitives
├── GRAMMAR_AND_VIOLATIONS.md    ← BNF + détection
├── engine_v2.py                 ← Moteur Python
├── run_tests.py                 ← Test suite
├── QUICKSTART.md                ← Guide pragmatique
├── LEARNING_RULES.md            ← Auto-correction
└── PROOF_OF_CONCEPT/
    ├── simple_api_sla.json
    ├── ml_pipeline.json
    ├── cloud_infra.json
    └── service_degradation.json
```

---

## Principes Clés

### 1. Pas d'ambiguïté (RÈGLE 0)

**❌ Interdit:**
```json
"sla": "latence doit rester performante"
```

**✅ Requis:**
```json
"sla": {
    "on": "latency",
    "operator": "<=",
    "threshold": 500,
    "unit": "ms",
    "window_eval": "5m",
    "aggregation_eval": "p99"
}
```

Pourquoi? "Performante" ≠ mesurable. 500ms en p99 sur 5min = spécifique et observable.

### 2. Ternaire (non binaire)

Pas de "peut-être", pas de "probablement":

- **VALID:** Constraint est satisfait (p99_latency = 87 ≤ 500 ✓)
- **VIOLATED:** Constraint échoue (p99_latency = 1250 > 500 ✗)
- **UNKNOWN:** Données insuffisantes ou conflits (pas d'observation, confiance < 50%)

### 3. Confidence tracking

Chaque observation porte une confiance [0,1]:
- 0.99 = données directes (Prometheus scrape)
- 0.75 = calculées (agrégation)
- 0.50 = inférées (ML prediction)

→ Système dégrade gracieusement si confiance insuffisante

### 4. Learning Rules (auto-healing)

Quand une constraint échoue, rules optionnelles peuvent:
- Scale infrastructure (kubectl)
- Retrain models
- Adjust thresholds (degraded mode)
- Kill connections (resource cleanup)

Toujours avec:
- **Trigger:** Quand s'activer
- **Condition:** Contexte supplémentaire
- **Action:** Quoi changer
- **stop_condition:** Quand revert
- **max_iterations:** Limite d'escalade

---

## Validation des Cas

### ✓ Cas sain (API REST)
```
p99_latency_sla:     87 ≤ 500 ✓
SLA_availability: 99.95 ≥ 99.9 ✓
────────────────────────────────
Status: VALID
```

### ✓ Cas sain (ML Pipeline)
```
min_quality:  0.97 ≥ 0.95 ✓
min_accuracy: 94.2 ≥ 92 ✓
max_drift:    12.3 < 15 ✓
────────────────────────────────
Status: VALID
```

### ✗ Cas dégradé (Service Down)
```
p99_latency_sla:     1250 ≤ 500 ✗ PAGE ON-CALL
error_rate_thresh:   3.7 < 0.5 ✗ CIRCUIT BREAKER
db_connection_cap: 4720 < 4500 ✗ ALERT DEVOPS
────────────────────────────────
Status: VIOLATED
Consequence: Execute Learning Rules
  → Scale API +2 replicas
  → Kill idle DB connections
  → Degrade SLA threshold temporarily
```

---

## Modèle de Données

### System
```python
{
    name: str,
    variables: {name → Variable},
    constraints: {name → Constraint},
    observations: [Observation],
    relations: [Relation]
}
```

### Variable (une mesure de l'état)
```python
{
    name: "api_latency",
    domain: Domain("temps", "ms"),
    bounds: (0, 5000),
    confidence: 0.89
}
```

### Constraint (une condition à satisfaire)
```python
{
    name: "p99_latency_sla",
    on: "api_latency",              # Variable
    operator: "<=",
    threshold: 500,
    domain: "temps",                # MUST match Variable
    unit: "ms",
    window_eval: "5m",              # FORBIDDEN: hidden state
    aggregation_eval: "p99",        # FORBIDDEN: hidden state
    priority: "MUST"
}
```

### Observation (une mesure réelle)
```python
{
    variable: "api_latency",
    value: 87,
    timestamp: "2025-12-28T10:20Z",
    window: "5m",                   # FORBIDDEN: hidden state
    aggregation: "p99",             # FORBIDDEN: hidden state
    source: "prometheus",
    confidence: 0.99,
    type: "MEASURED"
}
```

### Relation (dépendance causale)
```python
{
    source: "db_connections",
    target: "api_latency",
    type: "INCREASES",
    strength: 0.87                  # 87% de chance
}
```

### LearningRule (auto-correction)
```python
{
    name: "auto_scale_api",
    trigger: "p99_latency_sla VIOLATED",
    condition: "cpu > 85% AND count(VIOLATED) > 3 in 1h",
    action: "kubectl scale deployment api --replicas=+2",
    stop_condition: "cpu < 70% for 10m",
    max_iterations: 5,
    confidence: 0.91
}
```

---

## Bonnes Pratiques

### ✅ Checkliste avant production

- [ ] Tous constraints ont `window_eval` + `aggregation_eval`
- [ ] Tous observations ont `window` + `aggregation`
- [ ] Domaines variables = domaines constraints
- [ ] Units cohérentes (ms vs µs? %)
- [ ] Confiance >= 0.5 sur sources données
- [ ] Learning rules ont `stop_condition` + `max_iterations`
- [ ] Pas de mots flous ("performant", "rapide", "bon")
- [ ] Pas de dépendances circulaires
- [ ] Test: `python engine_v2.py your_system.json` → Success

### ❌ Antipatterns

1. **État caché:** Constraint sans window/aggregation
   ```json
   "sla": {"on": "latency", "operator": "<=", "threshold": 100}
   ```
   → Où agréger? Comment? Ambiguïté = BUG

2. **Mots flous:** "Doit rester performant"
   → Pas mesurable = impossible à valider

3. **Dépendances infinies:**
   ```
   rule_A triggers rule_B triggers rule_A...
   ```
   → Escalade infinité = runaway

4. **Learning rules sans arrêt:**
   ```json
   "action": "scale +1 replica",
   // pas de stop_condition!
   ```
   → Peut monter indéfiniment

---

## Résultats Actuels

✅ **Phase 0-2 Complète:**
- Fondations formelles (RÈGLE 0)
- 6 primitives spécifiées
- Grammar et violation detection
- Moteur fonctionnel

✅ **Validation réussie:**
- 4/4 cas de test passent
- 3 cas sains = VALID
- 1 cas dégradé = VIOLATED
- Zéro faux-positifs ou faux-négatifs

✅ **Pragmatique:**
- Code exécutable (Python)
- Cas réels (API, ML, Cloud, Incidents)
- Documentation (QUICKSTART, LEARNING_RULES)
- Test suite complète

---

## Prochaines Étapes (Phase 3+)

### Phase 3: Learning Rules Engine
- [ ] Implémenter auto-scaling (kubectl, Terraform)
- [ ] Implémenter model retraining
- [ ] Audit logs persistants
- [ ] Approval workflow (human-in-the-loop)

### Phase 4: Time-Series Analysis
- [ ] Trend detection (latency creeping up?)
- [ ] Seasonality (peak hour patterns)
- [ ] Anomaly detection (sudden spikes)
- [ ] Predictive SLA warnings

### Phase 5: Human-AI Co-Design
- [ ] Dashboard (constraints, violations, recommendations)
- [ ] SLA negotiation UI
- [ ] Learning rule recommendation engine
- [ ] Chaos engineering simulator

### Phase 6: IDE & Tooling
- [ ] VS Code extension (syntax highlighting, validation)
- [ ] Terraform generator (auto-create constraints from infra)
- [ ] Monitoring adapter (auto-fetch observations)
- [ ] Visualization engine (timeline, heatmaps)

---

## Philosophie

**UniVersCell** répondait à une question simple:

> *"Comment créer un langage où on ne peut pas mentir involontairement?"*

Réponse:
1. **Tout doit être mesurable** (sinon NON_OBSERVÉ explicite)
2. **Pas de mots flous** (window, aggregation, threshold obligatoires)
3. **Pas d'état caché** (dependencies, consequences, stop conditions explicites)
4. **Ternaire, pas binaire** (VALID | VIOLATED | UNKNOWN)
5. **Traçable et auditée** (tout enregistré, confidence tracking)

C'est dur à respecter. Mais une fois que c'est fait, vous avez un système où:
- Aucune ambiguïté
- Aucune assomption cachée
- Aucune escalade silencieuse
- Autoguérison visible et stoppable

---

## Contributing

Pour modifier le moteur:
1. Modifier `engine_v2.py` (RuleValidator ou Evaluator)
2. Tester: `python run_tests.py`
3. Tous les 4 cas doivent passer

Pour créer un nouveau cas:
1. JSON à PROOF_OF_CONCEPT/
2. Ajouter test à `run_tests.py`
3. Documenter attendus: VALID ou VIOLATED

---

## License

Open source, educational use. Langage et moteur en domaine public.

---

**Dernière mise à jour:** 2025-12-28  
**Version:** Phase 2 (Validation + Évaluation ternaire)  
**Status:** Production-ready pour PHASE 0-2
