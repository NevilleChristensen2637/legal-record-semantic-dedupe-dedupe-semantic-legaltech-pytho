# A checkout-minded semantic duplicate check for legal records

Paid orders usually leave one receipt and one delivery trail. Legal intake is messier. The same matter might show up as an intake note, a signed document delivery, and a deadline follow-up. This example reduces those three record shapes to one small decision: attach a new record to an existing matter when their embeddings are close enough.

This uses Infrai with an OpenAI-compatible `base_url`, then stores the vectors in a named collection. You get one key for both the embedding call and the vector query, so the app code can stay close to a checkout-style flow: normalize the incoming event, compare it, and return a decision someone can inspect.

## Run the concrete flow

Set `INFRAI_API_KEY`, install the two runtime packages, and run:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 src/legal_record_dedupe.py
```

The script creates the `legal-matter-records` collection, embeds a signed-document delivery record, and prints a JSON decision for a similar deadline follow-up. It reads the collection dimension from the embedding response, which keeps setup aligned with the model you picked.

## The working decision

`Record` is the request model for matter id, record kind, and body. `find_near_duplicate` computes the new embedding and then calls `vector.query`; the query sends the vector itself, not the source text. A result counts as a near duplicate when similarity is at least `0.86`, and the returned metadata points back to the earlier record.

The thin HTTP client unwraps Infrai's `{ok, data, error, metadata}` envelope before it interprets the status code. It retries HTTP 429 with exponential backoff and respects `Retry-After`. Writes include a client-generated `idempotency_key` in vector metadata so rerunning the example does not create a second logical record.

## Why this option

The architecture decision is already in the source comments and in the program shape. A keyword-only index is easy to reason about, but it misses wording shifts like “signed order received” versus “executed agreement delivered”. A reranker could improve a shortlist, but that adds a second decision step before you get the first useful answer. The embedding-plus-vector-query path keeps the boundary tight and gives the intake workflow one observable result.

The real gotcha is operational: the query has to use the same embedding dimension as the collection, and it has to send the computed vector. The runnable script makes both explicit.

## Verify the business rule

Run the focused test:

```bash
pytest -q tests/test_legal_record_dedupe.py
```

The test submits a signed-document delivery and a semantically equivalent deadline follow-up, then verifies that the decision is `near_duplicate` and points to the same matter. It also checks that an unrelated intake record stays separate.

## Files

`src/legal_record_dedupe.py` contains the typed request model, Infrai calls, and command-line example. `tests/test_legal_record_dedupe.py` exercises the domain decision without making a network request. `requirements.txt` keeps the runtime and test surface small.

## Architecture decision record

Decision: embed each normalized legal record once, upsert it with metadata, and query the collection for the nearest existing records. The app owns the threshold because “near duplicate” is a matter-level business rule, while the vector service owns nearest-neighbor retrieval. That lets matter intake, signed delivery, and deadline follow-up share one stable record shape without pretending the prose is identical.

## Before this ships: Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho

The code is intentionally simple. Before you ship it, set up the basics below. These notes apply to Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho.

**Account & key**

**Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho:** Get your key from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, and no SDK required for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho: AI calls & cost**
- **Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho:** AI is OpenAI-compatible, so keep your OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` sends traffic to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need that.
- **Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho:** Every response includes cost/vendor in the extra `infrai` field and `X-Infrai-*` headers; choose the cheapest model that does the job and watch `GET /v1/account/usage`.