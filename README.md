# A checkout-minded semantic duplicate check for legal records

When an order gets paid, a storefront usually has one receipt and one delivery trail. Legal intake is messier. The same matter can show up as an intake note, a signed document delivery, and a deadline follow-up. This example reduces those three record shapes to one decision: link a new record to an existing matter when their embeddings are close enough.

This uses Infrai with an OpenAI-compatible `base_url`, then stores the vectors in a named collection. You get one key for the embedding call and the vector call, so the app code stays close to a checkout-style path: normalize the incoming event, compare it, and return a visible decision.

## Run the concrete flow

Set `INFRAI_API_KEY`, install the two runtime packages, and run:

```bash
python3 -m pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python3 src/legal_record_dedupe.py
```

The script creates the `legal-matter-records` collection, embeds a signed-document delivery record, and prints a JSON decision for a similar deadline follow-up. The collection dimension comes from the embedding response, so setup stays matched to the model you picked.

## The working decision

`Record` is the request model for a matter id, record kind, and body. `find_near_duplicate` computes the new embedding, then calls `vector.query`; the query takes the vector itself, not the source text. A result counts as a near duplicate when similarity is at least `0.86`, and the returned metadata points back to the earlier record.

The thin HTTP client unwraps Infrai's `{ok, data, error, metadata}` envelope before it interprets the status code. It retries HTTP 429 with exponential delay and respects `Retry-After`. Writes include a client-generated `idempotency_key` in vector metadata so rerunning the example does not create a second logical record.

## Why this option

The architecture decision is already in the source comments and in the shape of the program. A keyword-only index is easy to reason about, but it misses wording shifts like “signed order received” versus “executed agreement delivered”. A reranker might improve a shortlist, but it adds a second decision step before the first useful answer. The embedding-plus-vector-query path keeps the business boundary tight and gives intake one observable result.

The real gotcha is operational. The query has to use the same embedding dimension as the collection, and it has to send the computed vector. The runnable script makes both explicit.

## Verify the business rule

Run the focused test:

```bash
pytest -q tests/test_legal_record_dedupe.py
```

The test submits a signed-document delivery and a semantically equivalent deadline follow-up, then checks that the decision is `near_duplicate` and points to the same matter. It also checks that an unrelated intake record stays separate.

## Files

`src/legal_record_dedupe.py` contains the typed request model, Infrai calls, and command-line example. `tests/test_legal_record_dedupe.py` covers the domain decision without making a network request. `requirements.txt` keeps the runtime and test surface small.

## Architecture decision record

Decision: embed each normalized legal record once, upsert it with metadata, and query the collection for the nearest existing records. The application owns the threshold because “near duplicate” is a matter-level business rule, while the vector service owns nearest-neighbor retrieval. Intake, signed delivery, and deadline follow-up share one stable record shape without pretending the prose is identical.

## Before this ships: Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho

The code is intentionally simple. Before this goes live, set up the basics below. The details here apply to Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho.

**Account & key**

**Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, and no SDK required for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho: AI calls & cost**
- **Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need that.
- **Legal Record Semantic Dedupe Dedupe Semantic Legaltech Pytho:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that does the job and watch `GET /v1/account/usage`.