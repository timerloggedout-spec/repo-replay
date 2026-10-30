# Exported methods — imported by timerloggedout-spec/termux-monorepo

Monorepo imports these *methods* (by reference to this repo + version);
it does not copy the implementation. Clear distinction: this repo owns the
system; the monorepo is a consumer + test subject.

- `extract(exports) -> objects + provenance` — session exports -> object store
- `build_index(objects) -> index/v1` — forward + reverse, one pass
- `compose(recipe) -> file` — materialize a recipe (Modes A master / B aggregate)
- `replay(store, path) -> tree` — reconstruct files from recipes
- `verify(replayed, oracle) -> diff report` — vs .git tree / validator copies
- `fill_gap(missing, provenance|validator) -> object` — deletion repair, hash-verified
- `jit_resolve(imports, index) -> segments` — compile-time import resolution, lazy
- `edit(ptr, op, payload) -> new recipe` — surgical pointer-addressed edit + history node
