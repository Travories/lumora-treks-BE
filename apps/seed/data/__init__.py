"""
Lumora's seed content: every image, destination, package, blog post, page and
site setting a fresh database starts with. Plain data only — the pipeline in
`apps/seed/pipeline.py` turns it into records.

Cross-references use stable keys (image keys, destination and package slugs);
the pipeline resolves them and fails loudly on a key that doesn't exist.
"""
