# VNP Simulation Exploration Results
Generated: 2026-02-10 21:28:34

## E1: Strategy Comparison

| Program | Final Tick | Automata | Offspring | Resources |
|---------|------------|----------|-----------|-----------|
| safe | 10000 | 1 | 0 | 0 |
| standard | 72 | 0 | 2 | 27 |
| static | 37 | 0 | 0 | 0 |
| traveler | 111 | 0 | 4 | 45 |

### Observations:
- **Safe**: Survives longest (10000 ticks) by frequently resting, but doesn't collect resources
- **Traveler**: Best reproduction rate (4 offspring) with aggressive exploration
- **Standard**: Balanced approach, moderate results
- **Static**: Poor performance - needs tuning

## E2: Part Scale Comparison

| Program | Final Tick | Automata | Offspring | Resources |
|---------|------------|----------|-----------|-----------|
| balanced | 32 | 0 | 0 | 0 |
| big_collector | 22 | 0 | 0 | 8 |
| big_engine | 80 | 0 | 3 | 25 |
| big_power | 26 | 0 | 0 | 0 |
| big_scanner | 23 | 0 | 0 | 4 |
| big_storage | 245 | 0 | 34 | 329.4 |

### Observations:
- **Big Storage (5.0)**: Best overall - 34 offspring, 329 resources
- **Big Engine (4.0)**: Good mobility, 3 offspring
- **Balanced**: Reference configuration
- Large parts = higher mass = more energy consumption

## E3: World Configuration Comparison

| Program | Final Tick | Automata | Offspring | Resources |
|---------|------------|----------|-----------|-----------|
| large_world | 207 | 0 | 48 | 645.3 |
| seed_100 | 105 | 0 | 9 | 122.4 |
| seed_200 | 365 | 0 | 86 | 1133.8 |
| seed_300 | 30 | 0 | 0 | 0 |
| small_world | 87 | 0 | 4 | 36.2 |

### Observations:
- **Seed 200**: Best world - 86 offspring, 1133 resources (365 ticks)
- **Large World (120x120)**: More space = more opportunities
- **Seed 300**: Worst - likely no resources near spawn point
- World generation significantly affects automaton success

## Summary
1. **Storage capacity is critical** - bigger storage allows more resource accumulation for reproduction
2. **World seed matters a lot** - resource distribution near spawn determines early survival
3. **Balance between collection and exploration** - too passive means no growth, too aggressive means energy death
4. **Safe strategy** shows interesting long-term survival but zero reproduction