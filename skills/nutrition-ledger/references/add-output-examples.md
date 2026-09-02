# Add Output Examples

For one food:

**Logged Food**

| Food | Amount | Calories | Protein | Carbs | Fat | Fiber |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Whole milk | 128 g | 78 kcal | 4.04 g | 6.13 g | 4.18 g | 0.00 g |

**Today So Far**

| Calories | Protein | Carbs | Fat | Fiber | Water |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1,820 kcal | 146.33 g | 143.73 g | 73.24 g | 13.00 g | 24.0 fl oz |

Target progress: 1,820 / 2,000 kcal; 146.33 / 160 g protein; 143.73 / 190 g carbs; 73.24 / 67 g fat; 13 / 30 g fiber. Logged and verified.

For multiple foods, I’d use one `Logged Foods` table, then the same single aggregate `Today So Far` table:

**Logged Foods**

| Meal | Food | Amount | Calories | Protein | Carbs | Fat | Fiber |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Snacks | Walnuts | 10 g | 65 kcal | 1.52 g | 1.37 g | 6.52 g | 0.67 g |
| Snacks | Seaweed snack | 5 g | 30 kcal | 1.00 g | 1.00 g | 2.00 g | 1.00 g |

**Target Progress**

Calories: 1,742 / 2,000 kcal
Protein: 142.29 / 160 g
Carbs: 137.60 / 190 g
Fat: 69.06 / 67 g
Fiber: 13.00 / 30 g minimum

Logged and verified. Source: [gimMe seaweed snack label](https://example.com/source)

**Data Quality**

Aplenty spanakopita was scaled from the listed 86 g serving to 4 oz. Product identity was matched to the reported brand. Missing nutrient values remain `unknown`; they are not treated as zero.

**Sources**

Aplenty Greek-style spanakopita: package nutrition reference, URL unavailable.
USDA FoodData Central: generic nutrient reference, URL unavailable.

**Logged Food**

| Food | Amount | Calories | Protein | Carbs | Fat | Fiber |
| --- | --- | ---: | ---: | ---: | ---: |
| Whole milk | 128 g | 78 kcal | 4.04 g | 6.13 g | 4.18 g | 0.00 g |

**Today So Far**

| Metric | Amount | Target |
| --- | --- | --- |
| Entries | 16 | active foods only |
| Weight | 218.0 lb | body weight |
| Calories | 1,820 kcal | 1,820 / 2,000 (180 remaining) |
| Protein | 146.33 g | 146.33 / 160 (13.67 remaining) |
| Carbs | 143.73 g | 143.73 / 190 (46.27 remaining) |
| Fat | 73.24 g | 73.24 / 67 (-6.24 remaining) |
| Fiber | 13.00 g | 13.00 / 30 (17.00 remaining) |
| Hydration | 710 mL (24.0 fl oz) | tracked drinking water |

Target progress: 1,820 / 2,000 kcal; 146.33 / 160 g protein; 143.73 / 190 g carbs; 73.24 / 67 g fat; 13 / 30 g fiber.

Logged and verified.

**Logged Foods**

| Meal | Food | Amount | Calories | Protein | Carbs | Fat | Fiber |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Snacks | Aplenty Greek-style spanakopita | 4 oz | 251 kcal | 9.23 g | 30.32 g | 9.23 g | 1.32 g |
| Snacks | Roasted seaweed snack | 5 g | 30 kcal | 1.00 g | 1.00 g | 2.00 g | 1.00 g |

**Today So Far**

| Metric | Amount | Target |
| --- | --- | --- |
| Entries | 17 | active foods only |
| Weight | 218.0 lb | body weight |
| Calories | 2,101 kcal | 2,101 / 2,000 (101 over) |
| Protein | 156.56 g | 156.56 / 160 (3.44 remaining) |
| Carbs | 175.05 g | 175.05 / 190 (14.95 remaining) |
| Fat | 82.47 g | 82.47 / 67 (15.47 over) |
| Fiber | 15.32 g | 15.32 / 30 (14.68 remaining) |
| Hydration | 710 mL (24.0 fl oz) | tracked drinking water |

Target progress: 2,101 / 2,000 kcal; 156.56 / 160 g protein; 175.05 / 190 g carbs; 82.47 / 67 g fat; 15.32 / 30 g fiber.

Logged and verified.

Sources

[Aplenty Greek-style spanakopita reference](https://android.fatsecret.com/calories-nutrition/aplenty/greek-style-spanakopita)
[gimMe roasted seaweed snack label/reference](https://example.com/source)

**Logged Food**

| Food | Amount | Calories | Protein | Carbs | Fat | Fiber |
| --- | --- | ---: | ---: | ---: | ---: |
| Unbranded bakery pastry | 1 piece | 280 kcal | 4.00 g | 38.00 g | 12.00 g | unknown |

**Today So Far**

| Metric | Amount | Target |
| --- | --- | --- |
| Entries | 18 | active foods only |
| Weight | 218.0 lb | body weight |
| Calories | 2,381 kcal | 381 over |
| Protein | 160.56 g | 0.56 over |
| Carbs | 213.05 g | 23.05 over |
| Fat | 94.47 g | 27.47 over |
| Fiber | 15.32 g | 14.68 remaining |
| Hydration | 710 mL (24.0 fl oz) | tracked drinking water |

Target progress: Calories, carbs, and fat are over target; protein is met; 14.68 g fiber remain.

Logged and verified.

Data quality

Fiber was not available from the source and remains `unknown`. This item is an estimate pending product or package details.

The standard output order is now:

1. `Logged Food` or `Logged Foods`
2. The item-level general nutrition table
3. `Today So Far`
4. Small target-progress blurb
5. Persistence confirmation
6. `Data quality`, only when needed
7. `Sources`, always last when sources exist

This keeps every add response consistent while preserving detail without printing the full panel.
