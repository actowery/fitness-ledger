# Changelog

## 1.1.0 - 2026-09-01

- Replace the impossible skills-only assumption of in-place ChatGPT Library replacement with verified revisioned successor artifacts.
- Add deterministic `_fitness_ledger_revision` fingerprinting, supersession, and canonical-selection helpers.
- Fail closed when multiple different artifacts claim the same latest revision instead of guessing by filename or timestamp.
- Require Library read-back of the generated successor before a nutrition mutation may be reported as persisted.
- Preserve legacy/import ledgers as revision-zero canonical roots for migration compatibility.

## 1.0.2

- Bump package and plugin metadata versions to 1.0.2.

## 1.0.1

- Bump package and plugin metadata versions to 1.0.1.

## 0.4.0

- Add deterministic food-master identity/version migration primitives.
- Add nutrient coverage, confidence, enrichment, integrity, debt, longitudinal,
  contribution, activity, resilience, and body-trend analysis helpers.
- Migrate Library food-master metadata without rewriting historical nutrition.

## 0.2.1 - 2026-08-30

- Prepared the skills-only package for public Plugins Directory review.
- Added public listing metadata, square branding assets, and starter prompts.
- Added explicit privacy, terms, support, review test cases, and release notes.
- Enforced public metadata limits and synchronized package/plugin versions in tests.

## 0.2.0 - 2026-08-30

- Reworked the nutrition and fitness skills for ChatGPT Library-native persistence.
- Removed runtime dependence on local JSON paths, local processes, and manual script execution.
- Preserved bundled Python helpers as offline developer/test references.
- Clarified that Caliber and Apple Health are external optional source adapters.

## 0.1.0 - 2026-08-30

- Initial skills-only release candidate.
- Nutrition ledger skill with validation and standardized daily reports.
- Fitness reconciliation skill with explicit source-policy safeguards.
- Explicit IANA-timezone setup and source-adapter intent configuration.
- GitHub marketplace installation and continuous integration.
