# Ice Hockey Product — documentation

| Document | Description |
| --- | --- |
| [ice_hockey_api_testing_report.md](./ice_hockey_api_testing_report.md) | **API testing:** 40-route pass, verdicts, response types |
| [ice_hockey_api_variation_testing.md](./ice_hockey_api_variation_testing.md) | **Variations:** pagination (page 2000), status filters, list vs detail, auth, validity |
| [ice_hockey_product_flow.md](./ice_hockey_product_flow.md) | **Product flow:** UI journeys, endpoint coverage, user-facing issues |

Raw probe output lives in [`../data/`](../data/) (not duplicated here).

## Regenerate

From the product root:

```bash
python3 scripts/probe_all_endpoints.py
python3 scripts/generate_api_testing_report.py
python3 scripts/probe_variations.py
python3 scripts/generate_variation_report.py
```
