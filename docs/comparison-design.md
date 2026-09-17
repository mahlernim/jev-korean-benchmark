# Jev and LLM comparison design

Evidence checked September 17, 2026. This records the rationale prepared before the Luna run. The [completed Luna-none comparison](luna-comparison.html) is reported separately.

## Existing evidence

[TypeSafe's workflow evaluation](https://evals.typesafe.ai/) compares models on four code-defined workflows, using provider-default reasoning for evaluated models. Its reference labels average GPT-6 Astra and Claude Fable 5.1 at high thinking. The scores therefore measure agreement with a model-derived reference, rather than independently verified task correctness. These workflows differ from our single-question Korean tests.

The [launch methodology](https://typesafe.ai/blog/introducing-system-one-models-and-jev) says its LLM adapter requests structured probabilities and acknowledges that this can be slower and costlier than requesting decisions alone. Its separate wikiracing demonstration uses non-reasoning or lowest-reasoning configurations. There is no single thinking level shared by all demonstrations.

[Every's independent early-access test](https://every.to/also-true-for-humans/mini-vibe-check-typesafe-s-jev-judged-everything-i-ve-written-in-0-7-seconds) compares Jev with Fable 5.1 at high effort on four writing checks across 12 synthetic passages. It reports six of seven planted defects detected by Jev and seven by Fable. The experiment is useful but too small and different in task design to establish Korean performance or a universal speed ratio.

## Start with Luna without reasoning

The [official Luna model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna) lists `none`, `low`, `medium` (default), `high`, `xhigh`, and `max`. Start with explicit `none`. Decide whether higher reasoning is useful after this first comparison, retaining its results unchanged. The hypothesis that Jev lies between Luna-none and Luna-max is untested and need not hold task by task.

Use the same frozen cases, content, instructions, option meanings and order. Ask Luna for only a constrained answer ID or boolean, without explanations, tools, retrieval or conversational history. Minimal schema instructions are an unavoidable interface difference and must be published. Do not require Luna to generate an entire probability vector for the primary accuracy, time and cost comparison. That would add output work unrelated to the decision. Probability elicitation, if later studied, belongs in a separately labeled experiment. Self-reported probabilities are not interchangeable with model token probabilities or Jev probabilities.

Compare each task and language condition separately with paired correctness differences, confidence intervals, failures and answer-order sensitivity. Keep unreviewed synthetic cases exploratory. Existing cases support paired replication, but this extension is designed after viewing Jev results. Prompt tuning must use development cases only. Any broader claim should be checked on new held-out cases.

Measure sequential client request duration to validated final answer, all attempts, p50/p95, total API and runner time, input, cached-input, output and reasoning tokens. Count reasoning tokens within billed output without double counting. Record API service tier, requested and returned model, dates, SDK, retries, response schema and actual cache usage. Use standard synchronous service rather than discounted asynchronous batch when comparing latency. The original Jev run is a historical comparator, so provider load and date remain confounders. A later contemporaneous, interleaved replication would strengthen latency claims.

## Cost planning

The official standard Luna rates checked above are $0.20 per million input tokens, $0.02 cached input and $1.20 output. As an illustration, 0.5 million uncached input tokens plus 20,000 output tokens costs $0.124. Tokenizers and schema overhead differ, so this is not a quote for our run. Start with ten development calls and project the complete cost from observed usage. Do not assume the original Jev-specific $0.25 ceiling automatically authorizes an unbounded reasoning experiment.

No existing vendor speedup should be transferred into the Korean report. A decision-only `none` baseline directly addresses whether a low-cost LLM already meets this task's needs. Higher reasoning can then be assessed as an additional accuracy versus cost tradeoff.
