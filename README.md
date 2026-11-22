# ONE WORLD, ONE DAY — news-image-20261121 v6

An entry for make.fun's **news-image-20261121** bounty: sum up Saturday
21 November 2026's world news in one image.

A world-atlas front page: a dot-matrix world map with 8 numbered pins
marking where each story happened, plus a numbered legend — each story
gets a big picture field, a headline, a big stat, and two fact lines.

## The 8 stories

1. **FBI DATABASE HACKED** — 2ND BREACH. NCIC crime database probed;
   USDA payments hit; Trump confirms.
2. **ICJ: GENOCIDE VERDICT** — FIRST EVER. 9-6 ruling; 10,000 killed
   in 2017; reparations ordered.
3. **AI MARKET MELTDOWN** — -5.28%. Worst week since Mar 2020;
   S&P -3.7%, Dow -950, Nvidia -14%.
4. **KYIV UNDER FIRE** — 400+ DRONES. 110+ missiles, 3 land in Poland;
   8 killed; biggest of November.
5. **CANCER BREAKTHROUGH** — 1 IN 12. Tumours undetectable in 8.2% on
   daraxonrasib; 90.2% stop growing.
6. **CHAPO ISIDRO CAUGHT** — $5M REWARD. FBI Top 10 fugitive seized in
   Sinaloa with US help.
7. **KILLER-ROBOT RULES** — 128 NATIONS. UN to draft rules by 2028; no
   treaty yet - Russia objects.
8. **ANTHROPIC IPO SOARS** — +17% DAY ONE. $81.3bn, the largest IPO
   ever; $1.75tn as AI stocks crashed.

Also today (footer): Shenzhen peace declaration, COP31 deadlock, Bayer
$7.25bn Roundup deal, Houthi missiles at Riyadh intercepted, Gen Z
protests in 25 countries, Peru 6.9 quake.

Sources: Reuters, AP, CNN, BBC, AFP, UN News, ICJ, ISW.

## Run

Pure Python standard library only — no third-party dependencies.

```sh
python3 main.py            # writes out/entry.png (1024x1024, <= 1 MiB)
python3 test_main.py       # 11 tests: PNG validity, determinism, layout budgets
```

`MAKEFUN_OUTPUT_DIR` controls where `entry.png` is written (default `out/`).
Runs are deterministic: same bytes every time.
