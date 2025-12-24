# Changelog

## 0.2.0 (2025-12-20)

### Changed

- **Breaking**: `BM25Index` now auto-creates the `pg_textsearch` extension when the index is created
- Removed `0001_install_pg_textsearch` migration (no longer needed)
- Removed `check_pg_textsearch_extension` system check (extension is now created on-demand)

### Improved

- Zero-configuration setup: users can add `BM25Index` to models immediately without running migrations first
- No more migration dependency issues when adding `BM25Index` to new projects

## 0.1.0 (2025-12-20)

Initial release.

### Features

- `BM25Searchable` mixin for easy model integration
- `BM25Index` for declarative index configuration
- `BM25Score` expression for custom queries
- Automatic extension setup via Django migrations
- Chainable queryset API compatible with Django ORM
- Configurable BM25 parameters (k1, b, text_config)
