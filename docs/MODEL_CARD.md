# Lumora — Model Card

> **Read this first.** On a fresh install every model is trained on **synthetic** data produced by
> `backend/app/ml/synthetic.py`. The metrics below come from a held-out split of that synthetic data. They show
> that the training and evaluation pipeline works end to end. They are **not** evidence of real-world accuracy.
> Once enough real interactions exist, retrain with `python -m app.ml.train --source db`.

| Model | Purpose | Algorithm | Used by |
|---|---|---|---|
| Mastery tracing | P(learner knows the topic) | Bayesian Knowledge Tracing | Engine (`mastery` family), dashboard, quiz results, recommendations |
| Struggle predictor | P(next answer is incorrect) | Logistic regression (standardized) | Engine (`ml_struggle` family, weight 0.20) |
| Engagement predictor | P(learner continues ≥ 5 more minutes) | Chosen on validation data from {Gradient Boosting, Logistic Regression} | Engine: break suggestions, content density, quiz length |
| Learning-behaviour profiles | Descriptive behaviour clusters | K-means (k = 4) on standardized aggregates | Grown-up Insights only |
| Performance trend | Is accuracy improving? | Least-squares slope on a rolling mean | Engine (`momentum` family), dashboard insight |
| Recommendations | What to learn next | Interpretable linear ranking | Dashboard, `/api/recommendations` |

---

## 1. Features

All features are computed by **one** function set in `app/ml/features.py`. It is used for production inference, for
training on real data (`app/ml/real_data.py`) and for the synthetic simulator, so there is no train/serve skew.

**Struggle predictor**: computed from the learner's history *before* the answer being predicted:

| Feature | Description |
|---|---|
| `mastery` | BKT P(known) for the topic |
| `recent_accuracy` | Accuracy over the last 10 answers |
| `hint_rate` | Hints per question (recent) |
| `skip_rate` | Share of skipped questions (recent) |
| `mistake_streak` | Consecutive incorrect answers (capped at 6) |
| `avg_response_ratio` | Response time ÷ expected time for that difficulty (capped at 4) |
| `low_confidence_rate` | Share of answers the learner marked "Not sure" |
| `next_difficulty` | 1–3 |
| `log_attempts` | log(1 + answers on this topic) |

**Engagement predictor**: one snapshot per answer within a session: `session_minutes`, `events_per_minute`,
`recent_accuracy`, `hint_rate`, `skip_rate`, `mistake_streak` and `idle_seconds`. Label: the session continued for ≥ 5 more minutes.

**Profiles**: per-learner `accuracy`, `hint_rate`, `avg_response_ratio`, `skip_rate` and `avg_session_minutes`.

## 2. Training and evaluation

* `python -m app.ml.train [--source synthetic|db|auto]` writes `*.joblib` artifacts and `metrics.json`.
* The **split is grouped by learner** (`GroupShuffleSplit`, 25 % test). No learner appears in both train and test.
* The engagement model is **selected on a validation split carved out of the training set**. The test split is used once, for the report.
* Every metric is reported next to a naive baseline (constant base-rate Brier score, majority-class accuracy).
* In `auto`/`db` mode, real data is used only if there are ≥ `ML_MIN_REAL_SAMPLES` rows from ≥ 4 learners and both classes are present.

## 3. Results (synthetic hold-out, from `metrics.json`)

| Model | ROC-AUC | Brier | Baseline Brier | Accuracy @0.5 | Majority baseline | n test |
|---|---|---|---|---|---|---|
| Struggle (logistic regression) | **0.690** | **0.209** | 0.233 | 0.671 | 0.629 | 2,531 |
| Engagement (selected: gradient boosting) | 0.573 | 0.242 | 0.241 | 0.592 | 0.595 | 4,998 |

Validation ROC-AUC used for engagement model selection: gradient boosting 0.606, logistic regression 0.601.

Profile clustering: silhouette **0.168** on 600 synthetic learners. That is weak separation: these behaviours
form a continuum, not discrete types.

### Interpretation (honest reading)

* **Struggle model**: a modest but real improvement over baseline. The standardized coefficients go in the
  expected directions: harder questions (+0.53), more "not sure" answers (+0.31), slower answers (+0.13) and
  more hints (+0.12) raise the predicted struggle. Higher recent accuracy (−0.22), more practice (−0.18) and higher mastery
  (−0.11) lower it. An AUC around 0.7 is typical for next-answer prediction in knowledge tracing.
* **Engagement model**: **barely better than chance**, and its Brier score is no better than predicting the base rate.
  The simulator's drop-off is driven largely by a hidden "persistence" trait that the features can't observe. The
  engine therefore uses this prediction only for gentle nudges (break suggestions, lighter pages, shorter quizzes),
  and only after ≥ 4 events in the current session.
* **Profiles**: descriptive only. They are shown to grown-ups with the caveat that they describe recent behaviour and
  change as the learner changes. They are never shown to children and are never used as labels.

## 4. Bayesian Knowledge Tracing parameters

`p_init = 0.20`, `p_learn = 0.15` and `p_slip = 0.10`. `p_guess = 1 / number of options shown`, so dropping to 3
options (high-support mode) correctly makes a guess more likely. A correct answer given *after a hint* raises
`p_guess` by 0.15 per hint, so it counts as weaker evidence. A skip counts as weak negative evidence. These parameters are
literature-typical defaults, not fitted. Fitting them per skill with EM on real data is listed under future work.

## 5. Limitations and responsible use

* Synthetic bootstrap data reflects the simulator's assumptions, not real children.
* No demographic data is collected, so fairness across groups **cannot be measured**. This is a deliberate privacy trade-off.
* The models predict learning *behaviour*. They do not, and must not, infer ADHD, dyslexia, autism or any
  other condition. Nothing in the feature set is designed or validated for that, and Lumora does not do it.
* With fewer than about 3 answers per topic, the engine leans on a supportive prior (`COLD_START_PRIOR = 0.58`) rather than on the models.
