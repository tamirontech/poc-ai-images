# Coffee Roaster Test Scenarios

## Scenario 1: Core Brand Launch (JSON)
- File: `test_inputs/campaign_brief_coffee_roaster_launch.json`
- Goal: Validate a standard coffee roaster campaign with two flagship products.
- Focus:
  - Parser compatibility (JSON)
  - Multi-product generation
  - Brand color usage and messaging consistency

Run:

```bash
python -m app.main run \
  --brief test_inputs/campaign_brief_coffee_roaster_launch.json \
  --provider mock \
  --output test_outputs/coffee_roaster/launch
```

## Scenario 2: Seasonal Collection (YAML)
- File: `test_inputs/campaign_brief_coffee_roaster_seasonal.yaml`
- Goal: Validate seasonal campaign styling and YAML parsing.
- Focus:
  - Parser compatibility (YAML)
  - Seasonal campaign narrative
  - 3 required aspect ratios across two products

Run:

```bash
python -m app.main run \
  --brief test_inputs/campaign_brief_coffee_roaster_seasonal.yaml \
  --provider mock \
  --output test_outputs/coffee_roaster/seasonal
```
