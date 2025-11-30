
# Evaluation Plan

This document outlines the evaluation methodology for the Transparent Prompt-to-Vis Pipeline system.  
The evaluation focuses on **automatic, objective measurement** of pipeline quality and chart correctness, supplemented by a small **qualitative analysis** of clarity and expressiveness.

The evaluation comprises four key dimensions:

1. **Correctness** (automated)
2. **Logical Consistency** (automated)
3. **Clarity** (manual qualitative)
4. **Expressiveness** (manual qualitative)

Only the first two dimensions use code-based metrics.  
Clarity and expressiveness are analyzed qualitatively using a small set of end-to-end examples.


---

## 1. Goals

The evaluation aims to determine:

- Whether the system correctly infers the **six-step pipeline** (columns, filters, aggregations, mark type, encodings, sort).
- Whether the six steps form a **logically coherent** pipeline.
- Whether the step explanations are **clear and understandable**.
- Whether the six-step pipeline design is **expressive enough** to cover typical NL → visualization requests.


---

## 2. Quantitative Evaluation (Correctness + Logical Consistency)

We evaluate **10 queries** that:

- Have **explicitly specified chart types** (bar, line, point, area, rect, arc, boxplot)
- Are fully compatible with the cleaned `imdb_sample.csv` dataset
- Can be expressed entirely within the six-step pipeline
- Serve as the basis of automated correctness and logical consistency scoring

### 2.1 Step-Level Correctness

For each query, the system outputs a JSON pipeline of six steps.  
We compare each step against manually prepared **ground truth**.

**Metrics (with explicit normalization/leniency):**

- **Per-step match** — judged on the core fields below; cosmetic extras (legend, tooltip, etc.) do not affect correctness.
- **Pipeline correctness** — aggregate of step1–step6.

Normalization + leniency rules:

- Column order ignored
- Axis swap allowed only for symmetric charts (`point`, some `bar`)
- Filters normalized (uppercase categories, canonical comparison)
- Encodings compared on channel → field/aggregate/type (+ timeUnit/sort when present)
- Sorting compared by field + direction; if GT omits sort, any sort passes
- Leniency for temporal axes: missing `timeUnit` is accepted if the channel is temporal
- Leniency for temporal sort: if GT expects sort on a temporal field and pred omits sort but uses the same temporal field on x/y, it is accepted

### Step Comparison Cheatsheet

| Step | Criterion (core) | Example of pass | Example of fail |
|------|------------------|-----------------|-----------------|
| Step1 | Selected columns set matches | `["Genre","Rating"]` vs `["Rating","Genre"]` | Missing required column |
| Step2 | Intent string matches (case-insensitive) | `trend` vs `TREND` | `trend` vs `correlation` |
| Step3 | Aggregations/filters/group_by normalized | `count(Title)` + `Year>2000` | Wrong agg column or filter op |
| Step4 | Mark type matches | `bar` vs `bar` | `line` vs `bar` |
| Step5 | Encodings core matches; GT may be subset; temporal missing `timeUnit` accepted; point/bar allow x/y swap | Pred adds tooltip; GT has `timeUnit=year`, Pred only `type=temporal` | Wrong field (e.g., `count_Genre` vs `Title`), wrong sort when GT specifies |
| Step6 | Sort matches; if GT has sort and pred omits it but uses same temporal field on x/y, accept | GT sort `Year asc`, Pred no sort but x is temporal `Year` | GT sort on `Title count`, Pred no sort and x/y not that field |


### 2.2 Logical Consistency

A pipeline is considered **logically inconsistent** if:

- A step references a field not selected earlier
- Sorting references fields not defined or not aggregated
- Mark type contradicts encoding type (e.g., line with nominal x-axis)
- Aggregation references a field absent in selected columns or filters

**Metric:**  
- Binary per-query score (1 = consistent, 0 = inconsistent)


### 2.3 Quantitative Evaluation Dataset

The Quantitative test set consists of the following **10 queries**  
(covering all allowed mark types and including sorted charts):

| ID | Query | Expected Mark | Notes |
|----|--------|----------------|--------|
| Q1 | Use a horizontal bar chart to show the number of movies in each genre, sorted from lowest to highest count. | horizontal bar | basic aggregation + ascending sort |
| Q2 | Use a line chart to show the average rating by year. | line | temporal trend |
| Q3 | Use a point chart to show the relationship between Runtime (Minutes) and Rating. | point | scatter |
| Q4 | Use an area chart to show how the total number of movies released each year has changed over time. | area | area trend |
| Q5 | Use a rect (heatmap) to show the average rating for each combination of Genre and Year. | rect | heatmap |
| Q6 | Use an arc chart to show the share of movies by genre. | arc | pie chart |
| Q7 | Use a boxplot to show the distribution of movie ratings for each genre. | boxplot | distribution |
| Q8 | Use a bar chart to show the total revenue for each genre, sorted from highest to lowest, including only movies released after 2000. | bar | filter + aggregation + sort desc |
| Q9 | Use a point chart to show the relationship between Rating and Revenue (Millions). | point | scatter |
| Q10 | Use a line chart to show the number of movies released each year, with a separate line for each genre. | line | multi-series trend |


---

## 3. Qualitative Evaluation (Clarity + Expressiveness)

These dimensions cannot be fully automated, so we include **additional queries** not part of the correctness evaluation.

These queries:

- contain **ambiguous language** → test *clarity*，like:
    Q : `“Show the popularity of movies over time.”`

    **Ambiguity**:
    - “popularity” could map to rating, revenue, or count

    - Used to test clarity of generated explanation

    - Pipeline must clarify how it interprets popularity
- require **functionality beyond** the six-step pipeline → test *expressiveness limitations*, like:
    Q: `Show the average rating per genre and also how it changed year over year.`

    **Requires two separate views (Multi-view requriement)**:
    - summary bar chart
    - trend line chart
    - The pipeline cannot generate multi-view → expected category = Not supported

### 3.1 Clarity Evaluation

We inspect whether the system provides **clear and interpretable explanations** for:

- Column selection reasoning
- Filter interpretation
- Chart type justification
- Encoding choices

Each step is scored manually:

- **2 = clear**
- **1 = partially clear**
- **0 = unclear**

### 3.2 Expressiveness Evaluation

We categorize each qualitative query as:

- **Supported**  
- **Partially supported** (pipeline can express a subset)  
- **Not supported** (pipeline cannot represent required operations)

This explicitly addresses instructor feedback on *expressiveness limitations*.

### 3.3 Qualitative Test Queries

| ID | Query | Purpose |
|----|-------|---------|
| C1 | "Show the popularity of movies over time." | Clarity (ambiguity: popularity) |
| C2 | "Use a bar chart to show the number of movies in each genre, sorted from lowest to highest count." | Clarity (ambiguity: bar chart vs horizontal bar chart) | 
| C3 | "Show the average rating per genre and also how it changed year over year." | Expressiveness (multi-view required) |


---

## 4. Procedure

### 4.1 Quantitative Evaluation

1. Run the system on the 10 queries.
2. Store:
   - six-step pipelines (JSON)
   - generated Vega-Lite specifications
3. Compare each output to the ground truth using correctness rules.
4. Detect logical inconsistencies.
5. Output:
   - per-step correctness table
   - overall correctness score
   - logical consistency score

### 4.2 Qualitative Evaluation

1. Run the system End2End on clarity/expressiveness queries.
2. Manually inspect:
   - clarity of explanations
   - pipeline expressiveness
3. Summarize representative successes and limitations.


---

## 5. Deliverables

Evaluation-related files will be stored in:
- `evaluation.md` (this document)
- `evaluation/query_set.json` (10 test queries + expected mark)
- `evaluation/ground_truth.json` (ground-truth pipelines + Vega-Lite specs)
- `evaluate.ipynb` (Quantitative & qualitative testing results + summerized table)

