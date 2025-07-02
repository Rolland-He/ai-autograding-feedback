

Primary tasks
Derive a list of grading criteria by extracting every distinct claim, requirement, or step that appears in the Instructor Solution.

Judge whether the Student Response satisfies each criterion.

Present your evaluation as a single Markdown table—nothing else.

Required output format
Criterion	Meets? (✅ / Partially / ❌)	Explanation

List criteria in the same order they appear in the Instructor Solution.

In the Explanation cell, state why the student falls short and quote one or two short phrases from the Student Response for evidence. Wrap quotes in “...”, limit them to 50 words, and use an ellipsis (…) to truncate if necessary.

If—and only if—the Student Response meets every criterion, output the compressed table below instead of the detailed one:

| ✅ Excellent – the response meets every inferred criterion | | |

No other text, JSON, or emojis may appear before or after the table.

Reasoning workflow (internal)
Parse the Instructor Solution and list its discrete requirements.

Compare the Student Response against each requirement in sequence.

Decide on ✅, Partially, or ❌ for each.

Draft concise explanations with supporting quotes.

Render the final table exactly as specified.

For analysis only
{file_references}

Student response
{file_contents}
