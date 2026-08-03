# 提示词评估报告

## 1. Experiment Overview

| Item | Value |
| --- | --- |
| Dataset size | 2 versions |
| Prompt versions | v1, v2 |
| Provider | openai_compatible |
| Model | deepseek-v4-flash |
| Evaluation time | 2026-08-03T08:41:44.315884+00:00 |
| Dataset hash | 320fb0c6ab776a79 |
| Repair enabled | True |
| Max attempts | 2 |
| Run ID | d1997bc52280 |

## 2. Prompt Comparison

| Metric | V1 | V2 |
| --- | --- | --- |
| JSON Parse Rate | 100.0% | 100.0% |
| Structured Success Rate | 100.0% | 100.0% |
| Category Accuracy | 70.0% | 70.0% |
| Priority Accuracy | 88.2% | 88.2% |
| Order ID Accuracy | 100.0% | 100.0% |
| Human Review Accuracy | 60.0% | 75.0% |
| Tag Recall | 82.9% | 85.4% |
| Fabrication Rate | 0.0% | 0.0% |
| Repair Trigger Rate | 0.0% | 0.0% |
| Avg Provider Calls | 1.0 | 1.0 |
| Avg Duration (s) | 2.21 | 2.53 |
| End-to-End Success Rate | 40.0% | 55.0% |

## 3. Failure Analysis

### v1 Failures

**JSON Parse Failures:** None

**Category Errors (6):**
- case_004: got `物流问题`
- case_005: got `一般咨询`
- case_008: got `物流问题`
- case_013: got `换货问题`
- case_018: got `一般咨询`
- case_019: got `一般咨询`

**Fabrication Cases:** None

**Repair Still Failed:** None

### v2 Failures

**JSON Parse Failures:** None

**Category Errors (6):**
- case_004: got `物流问题`
- case_005: got `一般咨询`
- case_008: got `物流问题`
- case_013: got `售后问题`
- case_018: got `一般咨询`
- case_019: got `一般咨询`

**Fabrication Cases:** None

**Repair Still Failed:** None

## 4. Prompt Difference Analysis

### V1: Instruction-driven generation (Zero-shot)

V1 relies solely on system instructions describing the task, field definitions,
rules, and output format. The model must infer the expected behavior from the
instruction text alone, with no worked examples.

### V2: Example-guided generation (Few-shot)

V2 extends V1 with 3 curated examples covering:
- Clear classification with order ID present
- Missing order ID (uncertain_fields handling)
- Insufficient information (low confidence, human review required)

### Observed Differences

| Area | V1 | V2 | Analysis |
| --- | --- | --- | --- |
| Category Accuracy | 70.0% | 70.0% | Equal |
| JSON Parse Rate | 100.0% | 100.0% | Equal |
| Fabrication Rate | 0.0% | 0.0% | Equal |

> **Note:** Analysis is based on observed data. Where sample size is small (20 cases),
> differences may not be statistically significant. Do not over-generalize.
## 5. Limitations

- 20 test cases provide limited coverage of real-world ticket diversity
- Tag recall uses simplified substring matching, may miss synonyms
- Category accuracy depends on subjective expected values
- Single run per case; results may vary between runs
## 6. Recommendations

- Consider running multiple repetitions to reduce sampling variance
- Add more boundary and edge cases to the test dataset
- If V2 shows better category accuracy, few-shot examples are likely helping disambiguation
- If V1 and V2 show similar performance, the instruction alone may be sufficient
- Expand test dataset to 50+ cases for statistical significance
- Add multi-label evaluation for cases with multiple valid categories
