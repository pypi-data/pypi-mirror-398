# Changelog

## 0.1.0-alpha.40 (2025-12-19)

Full Changelog: [v0.1.0-alpha.39...v0.1.0-alpha.40](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.39...v0.1.0-alpha.40)

### Features

* **api:** api update ([c60b079](https://github.com/scaleapi/sgp-python-beta/commit/c60b0795b74718ba3d91cfc5322e0acae84318c0))
* **api:** api update ([42b9f6a](https://github.com/scaleapi/sgp-python-beta/commit/42b9f6a356f27e922eacfbb863f423a4eb72b621))


### Bug Fixes

* ensure streams are always closed ([a53f824](https://github.com/scaleapi/sgp-python-beta/commit/a53f82441b8e792c236bf2776fe62b8713c22c78))
* **types:** allow pyright to infer TypedDict types within SequenceNotStr ([d17d003](https://github.com/scaleapi/sgp-python-beta/commit/d17d0035c2c7b7e785991f0efb5a75c1642ead2b))
* use async_to_httpx_files in patch method ([0ffb743](https://github.com/scaleapi/sgp-python-beta/commit/0ffb7434c08322df729a87b5d8b2dd11329519b5))


### Chores

* add missing docstrings ([0ead346](https://github.com/scaleapi/sgp-python-beta/commit/0ead346d668d8d5525c26c08b23f9690e63b0aac))
* **deps:** mypy 1.18.1 has a regression, pin to 1.17 ([77a4985](https://github.com/scaleapi/sgp-python-beta/commit/77a498580aee97a654b716203062851c83ba1ac8))
* **docs:** use environment variables for authentication in code snippets ([98c4741](https://github.com/scaleapi/sgp-python-beta/commit/98c47414cb45132c312e6e117d9a236ed802e3d5))
* **internal:** add `--fix` argument to lint script ([fb424fc](https://github.com/scaleapi/sgp-python-beta/commit/fb424fc6e44fd01a795324eadffc3524510e5ff1))
* **internal:** add missing files argument to base client ([b2c3913](https://github.com/scaleapi/sgp-python-beta/commit/b2c3913ea86dc6a462a483db2536cda7c7cda8a4))
* speedup initial import ([d7310c5](https://github.com/scaleapi/sgp-python-beta/commit/d7310c5260b152479fdc3a33e766928fa5624845))
* update lockfile ([0f851f0](https://github.com/scaleapi/sgp-python-beta/commit/0f851f0d6a7a82af1111600f323278c4ef7281d3))


### Documentation

* add more examples ([ad9506e](https://github.com/scaleapi/sgp-python-beta/commit/ad9506e256c9796a56611af66a03eed2ff80c102))

## 0.1.0-alpha.39 (2025-11-21)

Full Changelog: [v0.1.0-alpha.38...v0.1.0-alpha.39](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.38...v0.1.0-alpha.39)

### Bug Fixes

* **tracing:** handle non-dict JSON in parse_input_output ([377f7b5](https://github.com/scaleapi/sgp-python-beta/commit/377f7b5b8c355f7a691f1a067edea504fa92c141))


### Chores

* **internal:** codegen related update ([a92ffed](https://github.com/scaleapi/sgp-python-beta/commit/a92ffed83d81cbb83ee34640c290e66ffb42cb6c))

## 0.1.0-alpha.38 (2025-11-21)

Full Changelog: [v0.1.0-alpha.37...v0.1.0-alpha.38](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.37...v0.1.0-alpha.38)

### Features

* **api:** api update ([b1d4b0b](https://github.com/scaleapi/sgp-python-beta/commit/b1d4b0beaf03b77e40149cd07cb33828b530e4b5))
* **api:** api update ([29b8944](https://github.com/scaleapi/sgp-python-beta/commit/29b89443e5022f2981e10544f86a78d0cd3a737e))
* **api:** manual updates ([227aa78](https://github.com/scaleapi/sgp-python-beta/commit/227aa78a5ea1b6ed4f0b85dcc76a578c933b8c3c))


### Bug Fixes

* **compat:** update signatures of `model_dump` and `model_dump_json` for Pydantic v1 ([f86a9e9](https://github.com/scaleapi/sgp-python-beta/commit/f86a9e998f20a76c28eea3c8cc67c63d9408ac5e))

## 0.1.0-alpha.37 (2025-11-10)

Full Changelog: [v0.1.0-alpha.36...v0.1.0-alpha.37](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.36...v0.1.0-alpha.37)

### Features

* **api:** api update ([47b3853](https://github.com/scaleapi/sgp-python-beta/commit/47b38530ea4075b38d47151515a5a2139a0aafcb))
* **api:** api update ([97b2a9a](https://github.com/scaleapi/sgp-python-beta/commit/97b2a9aefa4ccb9f45f374dbd909d0b6e848e875))
* **api:** api update ([1cc7a60](https://github.com/scaleapi/sgp-python-beta/commit/1cc7a6042e0c423f42e44647c4dc194f65183c8a))


### Bug Fixes

* compat with Python 3.14 ([0e2d607](https://github.com/scaleapi/sgp-python-beta/commit/0e2d6074349ba9b087dbe467fad26b1c92df0ec6))


### Chores

* **internal:** grammar fix (it's -&gt; its) ([2abb05b](https://github.com/scaleapi/sgp-python-beta/commit/2abb05b9f299a981bf593079e24a1ad9de2495ec))
* **package:** drop Python 3.8 support ([5c1b01c](https://github.com/scaleapi/sgp-python-beta/commit/5c1b01c1154a4e411f8c20b155361b407aa37035))

## 0.1.0-alpha.36 (2025-10-31)

Full Changelog: [v0.1.0-alpha.35...v0.1.0-alpha.36](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.35...v0.1.0-alpha.36)

### Features

* **api:** api update ([76132f3](https://github.com/scaleapi/sgp-python-beta/commit/76132f3014a1bb76c6fbc361eeb22b70e5ba2c8e))
* **api:** api update ([d49fc07](https://github.com/scaleapi/sgp-python-beta/commit/d49fc0725a798935a158e948b6bec9957ad70735))
* **api:** api update ([159f86b](https://github.com/scaleapi/sgp-python-beta/commit/159f86bc297c0d5f2c0274130cb80eafb42dcbcb))
* **api:** api update ([45b625d](https://github.com/scaleapi/sgp-python-beta/commit/45b625d2fa05372e691ce1104aa2ad57e35f7298))
* **api:** api update ([5f5f260](https://github.com/scaleapi/sgp-python-beta/commit/5f5f2600c93e4139e0a4166161760926726e8db9))
* **api:** api update ([82f6432](https://github.com/scaleapi/sgp-python-beta/commit/82f6432e0fc15b49b1af61b68e5c532128cb17db))
* **api:** api update ([f6f38a1](https://github.com/scaleapi/sgp-python-beta/commit/f6f38a1d672cbf164e274e4bb4c0b7edba40ba2f))
* **api:** api update ([a21c810](https://github.com/scaleapi/sgp-python-beta/commit/a21c810df306cd18556db68c75b11121a746fa2b))
* **api:** api update ([f4348cc](https://github.com/scaleapi/sgp-python-beta/commit/f4348cc051044d9eee0bcd0355265a8f563e9f2d))
* **api:** manual updates ([4c36350](https://github.com/scaleapi/sgp-python-beta/commit/4c363507e9eba1e4d04ef2e274cb07020ce0160d))


### Bug Fixes

* **client:** close streams without requiring full consumption ([d0d9d1d](https://github.com/scaleapi/sgp-python-beta/commit/d0d9d1d1539f006f6b8dd358657bae7639086c52))


### Chores

* **internal/tests:** avoid race condition with implicit client cleanup ([8dcca91](https://github.com/scaleapi/sgp-python-beta/commit/8dcca913c6a8413a9bf49d0594452e998911054a))

## 0.1.0-alpha.35 (2025-10-21)

Full Changelog: [v0.1.0-alpha.34...v0.1.0-alpha.35](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.34...v0.1.0-alpha.35)

### Features

* **api:** api update ([0f88ebc](https://github.com/scaleapi/sgp-python-beta/commit/0f88ebc40c1c1ce42bf8294ae33008dc4c9b7174))
* **api:** api update ([8da9a9a](https://github.com/scaleapi/sgp-python-beta/commit/8da9a9a0a199642e8b02c8bff920ff52e46e9e47))


### Chores

* bump `httpx-aiohttp` version to 0.1.9 ([02ce1c2](https://github.com/scaleapi/sgp-python-beta/commit/02ce1c2952a38e1e44495b47b28dff73809d4105))

## 0.1.0-alpha.34 (2025-10-11)

Full Changelog: [v0.1.0-alpha.33...v0.1.0-alpha.34](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.33...v0.1.0-alpha.34)

### Features

* **api:** api update ([32d5e6a](https://github.com/scaleapi/sgp-python-beta/commit/32d5e6a237f66ba6fe8289cff52c22c994d4bc1b))
* **api:** api update ([feda14a](https://github.com/scaleapi/sgp-python-beta/commit/feda14abd4e2abe328b80d8b990c8e843d617a3b))
* **api:** manual updates ([1e19009](https://github.com/scaleapi/sgp-python-beta/commit/1e190092ff4e30a56de8e2cf7b795c7cebaaea21))
* **api:** manual updates ([68d0f06](https://github.com/scaleapi/sgp-python-beta/commit/68d0f06626e220a5fa4ff6c5d89b63af1b3b7777))
* **api:** manual updates ([79a7506](https://github.com/scaleapi/sgp-python-beta/commit/79a750659ac6e3e8dd31a51723574b96113d7a6d))


### Chores

* **internal:** detect missing future annotations with ruff ([36182a5](https://github.com/scaleapi/sgp-python-beta/commit/36182a5b1dd725add76a13e2a4ce7416badfd72d))

## 0.1.0-alpha.33 (2025-10-03)

Full Changelog: [v0.1.0-alpha.32...v0.1.0-alpha.33](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.32...v0.1.0-alpha.33)

### Features

* **api:** api update ([78cd9ff](https://github.com/scaleapi/sgp-python-beta/commit/78cd9fff9644ccdb90fd31fc944da5eba11c9044))
* **api:** api update ([e47c322](https://github.com/scaleapi/sgp-python-beta/commit/e47c3224f983ed125379b0bf98f947a0d8520fa1))
* **api:** api update ([f0a9e63](https://github.com/scaleapi/sgp-python-beta/commit/f0a9e63cd22ecb8c4940cbffac94b97837fe762b))

## 0.1.0-alpha.32 (2025-09-26)

Full Changelog: [v0.1.0-alpha.31...v0.1.0-alpha.32](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.31...v0.1.0-alpha.32)

### Features

* **api:** api update ([2eb1602](https://github.com/scaleapi/sgp-python-beta/commit/2eb160218e79533b1f0e4260a3f9b828797d2314))
* **api:** manual updates ([4ed981c](https://github.com/scaleapi/sgp-python-beta/commit/4ed981cf2de7e19e70748eda6c2dbd09b1f5514c))
* **api:** manual updates ([e3247e7](https://github.com/scaleapi/sgp-python-beta/commit/e3247e7b052e3c637569557ca5191f74b5000101))
* **api:** manual updates ([cb4c708](https://github.com/scaleapi/sgp-python-beta/commit/cb4c708c8fe3ecc587decfc22cb1aba7a5811a34))
* **api:** manual updates ([660f1dd](https://github.com/scaleapi/sgp-python-beta/commit/660f1dd346101d16a7a9b21c41b77b8ef8ac2b96))
* **api:** manual updates to include credentials ([0c52328](https://github.com/scaleapi/sgp-python-beta/commit/0c52328cc2ed22bf807dd134099fdddd83ccf28b))


### Bug Fixes

* **compat:** compat with `pydantic&lt;2.8.0` when using additional fields ([35ba695](https://github.com/scaleapi/sgp-python-beta/commit/35ba695442389342ceca42425ff8cb15820c0563))


### Chores

* do not install brew dependencies in ./scripts/bootstrap by default ([99a2cbf](https://github.com/scaleapi/sgp-python-beta/commit/99a2cbf0e0e17467794d5e8a53280d1cf0d51e07))
* **internal:** update pydantic dependency ([f4bf819](https://github.com/scaleapi/sgp-python-beta/commit/f4bf819066012c1b27e13a59e7b36299bfe28245))
* **types:** change optional parameter type from NotGiven to Omit ([749cf11](https://github.com/scaleapi/sgp-python-beta/commit/749cf115e8483aae69c45e28139fcfa67aeda387))

## 0.1.0-alpha.31 (2025-09-12)

Full Changelog: [v0.1.0-alpha.30...v0.1.0-alpha.31](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.30...v0.1.0-alpha.31)

### Features

* **api:** api update ([634d8ff](https://github.com/scaleapi/sgp-python-beta/commit/634d8ff90de74851a61fb4abe8481df5a1d4d3d0))
* **api:** api update ([38e9839](https://github.com/scaleapi/sgp-python-beta/commit/38e9839fc58ab32857105a2fc4b5aa8e77f0da18))
* **api:** manual updates ([5d8d58e](https://github.com/scaleapi/sgp-python-beta/commit/5d8d58e933cf059a231fe2c6cf832e1737768ef9))
* improve future compat with pydantic v3 ([27d1b19](https://github.com/scaleapi/sgp-python-beta/commit/27d1b19b94153d9fcb5a624c38e3dead258ddf23))
* **types:** replace List[str] with SequenceNotStr in params ([d46edac](https://github.com/scaleapi/sgp-python-beta/commit/d46edac508f4a4c5a1608bd87741c9a19cb21586))


### Bug Fixes

* avoid newer type syntax ([60fd422](https://github.com/scaleapi/sgp-python-beta/commit/60fd42209abd344b9e5657fcac61447e62867506))


### Chores

* **internal:** add Sequence related utils ([572922d](https://github.com/scaleapi/sgp-python-beta/commit/572922d80e64eac017048e2da190eedcc687cabc))
* **internal:** move mypy configurations to `pyproject.toml` file ([65b59d2](https://github.com/scaleapi/sgp-python-beta/commit/65b59d2abf7f19ba38523e51108feae5922793a8))
* **internal:** update pyright exclude list ([4083c91](https://github.com/scaleapi/sgp-python-beta/commit/4083c91897c5231f09ae6742235fb8315af0ee10))
* **tests:** simplify `get_platform` test ([3d68c4d](https://github.com/scaleapi/sgp-python-beta/commit/3d68c4df754f527c312b6168aecb0970a672d79f))

## 0.1.0-alpha.30 (2025-08-26)

Full Changelog: [v0.1.0-alpha.29...v0.1.0-alpha.30](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.29...v0.1.0-alpha.30)

### Features

* **api:** api update ([cb4c1c5](https://github.com/scaleapi/sgp-python-beta/commit/cb4c1c5edb6a15c7e3e998d54c83604f9c6bb3a1))
* **api:** api update ([32e9415](https://github.com/scaleapi/sgp-python-beta/commit/32e9415aa3fc23ebdae39d438cabf8c6a2496b49))
* **api:** api update ([8146bf3](https://github.com/scaleapi/sgp-python-beta/commit/8146bf3e9e9c65defb95d3a80525538cb05fa825))
* **api:** api update ([b112792](https://github.com/scaleapi/sgp-python-beta/commit/b1127924897e97dbf82f342b53f926407cf84591))
* **api:** api update ([674f2b1](https://github.com/scaleapi/sgp-python-beta/commit/674f2b1c7289ebf7ca41be8b91913df2da04835e))
* **api:** api update ([48c91fa](https://github.com/scaleapi/sgp-python-beta/commit/48c91fa1edf4b05196ad396e092d26e102a31ae2))
* **api:** api update ([680a7f9](https://github.com/scaleapi/sgp-python-beta/commit/680a7f9fff37bed71a05bed10928ef0ceae19079))
* **api:** api update ([d44ffe4](https://github.com/scaleapi/sgp-python-beta/commit/d44ffe4df3e02a55abb1d73abca68e2978a95f07))
* **api:** api update ([8ce7997](https://github.com/scaleapi/sgp-python-beta/commit/8ce79973d97ec3f4e362301979fd055a4021e046))
* **api:** api update ([fddd794](https://github.com/scaleapi/sgp-python-beta/commit/fddd7945fa11de496a252c30f950e717dbde2a71))
* **api:** api update ([491142b](https://github.com/scaleapi/sgp-python-beta/commit/491142b453f9f37b0907982e2a35819b05c79aba))
* **api:** api update ([4a8519e](https://github.com/scaleapi/sgp-python-beta/commit/4a8519eacadbdf4e7e5094b61671ec5282330772))
* **api:** api update ([c8bf560](https://github.com/scaleapi/sgp-python-beta/commit/c8bf5604617ddf3b23e35d3fa63f8992e27cc677))
* **api:** manual updates ([b86c069](https://github.com/scaleapi/sgp-python-beta/commit/b86c0694240b1d7c1925d1ec7ef48a230939a795))
* **api:** manual updates ([8efcc54](https://github.com/scaleapi/sgp-python-beta/commit/8efcc5412b8f912c8b7fc94eaf72ee6f2de8f9e3))
* **api:** manual updates ([d8144e7](https://github.com/scaleapi/sgp-python-beta/commit/d8144e7b869b9ccb10e1c23997d3e28bddc5d5df))
* clean up environment call outs ([8aa4d07](https://github.com/scaleapi/sgp-python-beta/commit/8aa4d075fcebffcf02fc539525c6af434291e823))
* **client:** support file upload requests ([76d95ab](https://github.com/scaleapi/sgp-python-beta/commit/76d95abb89870b14e6303de8ef52e764bbe4403a))
* SGP client hooks ([#128](https://github.com/scaleapi/sgp-python-beta/issues/128)) ([f247adb](https://github.com/scaleapi/sgp-python-beta/commit/f247adb2273f081c2d2083cc256e43c08b83c21a))


### Bug Fixes

* **parsing:** ignore empty metadata ([a1190e2](https://github.com/scaleapi/sgp-python-beta/commit/a1190e280c32aaac4faad6d496e012eedfeb9490))
* **parsing:** parse extra field types ([6b64a45](https://github.com/scaleapi/sgp-python-beta/commit/6b64a450d2a0b70ea857b58ccbc3540f1ad7713b))


### Chores

* Added CONTRIBUTING.MD for lib ([#127](https://github.com/scaleapi/sgp-python-beta/issues/127)) ([2b1bda7](https://github.com/scaleapi/sgp-python-beta/commit/2b1bda7ab925c4c8c44976f72f9f5723a9e61f30))
* **internal:** change ci workflow machines ([d7ace41](https://github.com/scaleapi/sgp-python-beta/commit/d7ace4109f8a7f2a98dd8f2cc526fee2b40f85b5))
* **internal:** fix ruff target version ([057e041](https://github.com/scaleapi/sgp-python-beta/commit/057e041dc7ec6638e68ba66868bbd851aeaba3b8))
* **internal:** update comment in script ([4760add](https://github.com/scaleapi/sgp-python-beta/commit/4760add2d22f15b47d5d8b4153dc7744523a0c63))
* **project:** add settings file for vscode ([ae9740b](https://github.com/scaleapi/sgp-python-beta/commit/ae9740bd28d7aaa21a089cd328554caea643a538))
* **types:** rebuild Pydantic models after all types are defined ([a1d6eec](https://github.com/scaleapi/sgp-python-beta/commit/a1d6eece8eaae0e783eda5aad65dceb62249cdad))
* update @stainless-api/prism-cli to v5.15.0 ([a15a320](https://github.com/scaleapi/sgp-python-beta/commit/a15a320bf13cdc88ffc312253655ad97dfa517a9))
* update github action ([f78e671](https://github.com/scaleapi/sgp-python-beta/commit/f78e67191edd058555d76a45f5b08d4bf974a2c4))

## 0.1.0-alpha.29 (2025-07-14)

Full Changelog: [v0.1.0-alpha.28...v0.1.0-alpha.29](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.28...v0.1.0-alpha.29)

### Features

* **api:** Add application_operation_type ([2455e20](https://github.com/scaleapi/sgp-python-beta/commit/2455e20838b22637ddce2a8e523f113d43acab0e))
* **api:** Add span status to span models ([c3fb91c](https://github.com/scaleapi/sgp-python-beta/commit/c3fb91c773d6ef11e1cc02e4546ff1923fc25c82))
* **api:** change name of app op type to span_type ([2285f10](https://github.com/scaleapi/sgp-python-beta/commit/2285f10ca3f1d51d3733996724d24daa09e83b88))


### Bug Fixes

* Use stainless types auto generated types for Span status and span type. ([#125](https://github.com/scaleapi/sgp-python-beta/issues/125)) ([6a3b070](https://github.com/scaleapi/sgp-python-beta/commit/6a3b07040137cb283711399bad76bedf78affcaf))

## 0.1.0-alpha.28 (2025-07-11)

Full Changelog: [v0.1.0-alpha.27...v0.1.0-alpha.28](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.27...v0.1.0-alpha.28)

### Features

* **api:** api update ([63befc8](https://github.com/scaleapi/sgp-python-beta/commit/63befc8168d56b166e43bdcfb804033cce9b1052))


### Bug Fixes

* **client:** don't send Content-Type header on GET requests ([9ca896f](https://github.com/scaleapi/sgp-python-beta/commit/9ca896fb0adf0a643cc071ad97a956752d63e42a))


### Chores

* **readme:** fix version rendering on pypi ([f4d2382](https://github.com/scaleapi/sgp-python-beta/commit/f4d23824e3d9238635cbefc406bd525a652ad8cc))

## 0.1.0-alpha.27 (2025-07-10)

Full Changelog: [v0.1.0-alpha.26...v0.1.0-alpha.27](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.26...v0.1.0-alpha.27)

### Features

* OpenAI subprocessor ([#121](https://github.com/scaleapi/sgp-python-beta/issues/121)) ([321507e](https://github.com/scaleapi/sgp-python-beta/commit/321507e666c4aec253451c670fbf42ff13361dbc))

## 0.1.0-alpha.26 (2025-07-09)

Full Changelog: [v0.1.0-alpha.25...v0.1.0-alpha.26](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.25...v0.1.0-alpha.26)

### Features

* **api:** api update ([161a258](https://github.com/scaleapi/sgp-python-beta/commit/161a2581292234a12334743798408e7b099dc2ac))


### Bug Fixes

* **parsing:** correctly handle nested discriminated unions ([e4f6af5](https://github.com/scaleapi/sgp-python-beta/commit/e4f6af5f550f10d960866d375d3e354f27c1fea5))

## 0.1.0-alpha.25 (2025-07-08)

Full Changelog: [v0.1.0-alpha.24...v0.1.0-alpha.25](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.24...v0.1.0-alpha.25)

### Features

* **api:** api update ([d937386](https://github.com/scaleapi/sgp-python-beta/commit/d937386969965002529ef23275b4a288d2499d99))
* **api:** api update ([6d1b192](https://github.com/scaleapi/sgp-python-beta/commit/6d1b1928c7a5ebd0f513e0d384314cbed61e30b9))
* **api:** api update ([3844cb9](https://github.com/scaleapi/sgp-python-beta/commit/3844cb9da4431fd0e6142ee1496338f003155a3d))
* **api:** api update ([c67aa4a](https://github.com/scaleapi/sgp-python-beta/commit/c67aa4a949bee450e441b68ea2e923c7efb2a20f))
* **api:** api update ([dedd79c](https://github.com/scaleapi/sgp-python-beta/commit/dedd79c9b8688d55319b3f15793ddb72059aabf2))
* **api:** api update ([4c1c95c](https://github.com/scaleapi/sgp-python-beta/commit/4c1c95c0c759128dc9252c7eefc3debd3c620df2))
* **api:** api update ([94b4574](https://github.com/scaleapi/sgp-python-beta/commit/94b457407f359ecf58b4cfe47317764a2d8aa610))
* **api:** api update ([e736ad9](https://github.com/scaleapi/sgp-python-beta/commit/e736ad9f41f3ac68d3f7ba060e723ee51d47400d))
* **api:** manual updates ([8cc70c3](https://github.com/scaleapi/sgp-python-beta/commit/8cc70c3398981e1f36d257d66438c9778da71931))
* **client:** add support for aiohttp ([434a3f5](https://github.com/scaleapi/sgp-python-beta/commit/434a3f5cb69df3fecac702adcd4aef34e028c3c3))


### Bug Fixes

* **ci:** correct conditional ([c5f62cb](https://github.com/scaleapi/sgp-python-beta/commit/c5f62cb467a83d0f37127cac3e0dba86d27bd664))
* **ci:** release-doctor — report correct token name ([d95eac6](https://github.com/scaleapi/sgp-python-beta/commit/d95eac67fb447632b873d19537f1708f23407bb8))


### Chores

* **ci:** change upload type ([67827be](https://github.com/scaleapi/sgp-python-beta/commit/67827be9e10d33930494853a052ba3691082f8d8))
* **ci:** only run for pushes and fork pull requests ([38f3abf](https://github.com/scaleapi/sgp-python-beta/commit/38f3abf82ac72ade0d957b16520ad70885870cdb))
* **internal:** bump pinned h11 dep ([26726a9](https://github.com/scaleapi/sgp-python-beta/commit/26726a9554265d94f47ccfea4b95130aefe30870))
* **internal:** codegen related update ([e241cab](https://github.com/scaleapi/sgp-python-beta/commit/e241cabb4fe8251ac8469e47dec7483398a52dc4))
* **package:** mark python 3.13 as supported ([0e5f57c](https://github.com/scaleapi/sgp-python-beta/commit/0e5f57ca0cc7a40ed9f66f702e9916b26c963b17))
* **tests:** skip some failing tests on the latest python versions ([918baf4](https://github.com/scaleapi/sgp-python-beta/commit/918baf442cc1add527ea97709f4b791cf5b5afa8))

## 0.1.0-alpha.24 (2025-06-20)

Full Changelog: [v0.1.0-alpha.23...v0.1.0-alpha.24](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.23...v0.1.0-alpha.24)

### Features

* Add queue_manger override for create span and trace & explicit option to disable daemon worker on TraceQueueManager. ([#117](https://github.com/scaleapi/sgp-python-beta/issues/117)) ([746ffa0](https://github.com/scaleapi/sgp-python-beta/commit/746ffa07ef7e31dfde972f443a440b0c7267b4fd))
* make span.py thread safe. ([#115](https://github.com/scaleapi/sgp-python-beta/issues/115)) ([55116b9](https://github.com/scaleapi/sgp-python-beta/commit/55116b9a296c64a9d94773a230a25c5ba22ca1ee))

## 0.1.0-alpha.23 (2025-06-20)

Full Changelog: [v0.1.0-alpha.22...v0.1.0-alpha.23](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.22...v0.1.0-alpha.23)

### Features

* Added set_error() to trace and span. ([#114](https://github.com/scaleapi/sgp-python-beta/issues/114)) ([2f08610](https://github.com/scaleapi/sgp-python-beta/commit/2f086103d8eed97a27f744e803717527ef64875c))


### Bug Fixes

* **tests:** fix: tests which call HTTP endpoints directly with the example parameters ([2a67032](https://github.com/scaleapi/sgp-python-beta/commit/2a6703258180ed241018002e3092d90d7974da56))


### Chores

* **ci:** enable for pull requests ([05e2eb0](https://github.com/scaleapi/sgp-python-beta/commit/05e2eb00b7d50d7c4d46d488f5b64cb9d2dcbb0d))
* **internal:** codegen related update ([9ae2242](https://github.com/scaleapi/sgp-python-beta/commit/9ae2242e355b8f1cfbaa28eab55d4b9ef7776833))
* **internal:** update conftest.py ([357f5ed](https://github.com/scaleapi/sgp-python-beta/commit/357f5ed5a3447bc889e5260911d8b4200c5f982f))
* **tests:** add tests for httpx client instantiation & proxies ([6ae6d18](https://github.com/scaleapi/sgp-python-beta/commit/6ae6d18ff82de7bec888e6617fdf9f54be0f4aa6))


### Documentation

* **client:** fix httpx.Timeout documentation reference ([dc2482b](https://github.com/scaleapi/sgp-python-beta/commit/dc2482bf483a51b0178db63d1a4dd24ed97e351b))

## 0.1.0-alpha.22 (2025-06-16)

Full Changelog: [v0.1.0-alpha.21...v0.1.0-alpha.22](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.21...v0.1.0-alpha.22)

### Features

* Updated README.md to include tracing information ([#111](https://github.com/scaleapi/sgp-python-beta/issues/111)) ([e2d0d8d](https://github.com/scaleapi/sgp-python-beta/commit/e2d0d8de22d347b830771fdf7a7fd4be954f30f0))

## 0.1.0-alpha.21 (2025-06-13)

Full Changelog: [v0.1.0-alpha.20...v0.1.0-alpha.21](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.20...v0.1.0-alpha.21)

### Features

* Group id support ([#110](https://github.com/scaleapi/sgp-python-beta/issues/110)) ([d934d91](https://github.com/scaleapi/sgp-python-beta/commit/d934d9136db1210e934e2c34b754200678ea60ca))


### Bug Fixes

* **client:** correctly parse binary response | stream ([f802181](https://github.com/scaleapi/sgp-python-beta/commit/f80218120e7f6780461ee0eac836139241532421))

## 0.1.0-alpha.20 (2025-06-12)

Full Changelog: [v0.1.0-alpha.19...v0.1.0-alpha.20](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.19...v0.1.0-alpha.20)

### Features

* Added flush() to Span ([#108](https://github.com/scaleapi/sgp-python-beta/issues/108)) ([5caf42f](https://github.com/scaleapi/sgp-python-beta/commit/5caf42f047f7ff0e4fbc9cb04835e9b9e13d65dc))


### Chores

* **tests:** run tests in parallel ([b707f08](https://github.com/scaleapi/sgp-python-beta/commit/b707f08569ff81e9ed21d010d80de65013f8db67))

## 0.1.0-alpha.19 (2025-06-11)

Full Changelog: [v0.1.0-alpha.18...v0.1.0-alpha.19](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.18...v0.1.0-alpha.19)

### Bug Fixes

* linter ([00fbc4a](https://github.com/scaleapi/sgp-python-beta/commit/00fbc4aca85f7c5a6561de566c2005310bc6c751))
* linter ([6831fe5](https://github.com/scaleapi/sgp-python-beta/commit/6831fe5b79ed35a1250fc2d2dd2d6e05b83dbc7f))
* remove check on end_timestamp for params creation ([4338936](https://github.com/scaleapi/sgp-python-beta/commit/433893642fc08cd2a9e0381297791f8d9368ec4b))

## 0.1.0-alpha.18 (2025-06-11)

Full Changelog: [v0.1.0-alpha.17...v0.1.0-alpha.18](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.17...v0.1.0-alpha.18)

### Features

* use upsert endpoint and report span start as well as end. ([3f8c073](https://github.com/scaleapi/sgp-python-beta/commit/3f8c073e8c1d97b2d7f2aced5558918bfd526de6))


### Bug Fixes

* new endpoints change ([8ccdf28](https://github.com/scaleapi/sgp-python-beta/commit/8ccdf28885781f1a1689c62616220a07aaea4a6c))

## 0.1.0-alpha.17 (2025-06-11)

Full Changelog: [v0.1.0-alpha.16...v0.1.0-alpha.17](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.16...v0.1.0-alpha.17)

### Features

* **api:** Added Span upsert batch and search endpoints ([f109f69](https://github.com/scaleapi/sgp-python-beta/commit/f109f6919886874122f541bf3bc8bb7d690648f1))

## 0.1.0-alpha.16 (2025-06-10)

Full Changelog: [v0.1.0-alpha.15...v0.1.0-alpha.16](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.15...v0.1.0-alpha.16)

### Features

* **api:** api update ([b0bf7cf](https://github.com/scaleapi/sgp-python-beta/commit/b0bf7cf4a9799a507bf3c10c2279489c7ed37c1a))
* **api:** api update ([90b9193](https://github.com/scaleapi/sgp-python-beta/commit/90b9193b9eff72dbae591dae4c3864fa77778047))
* **api:** api update ([0ec9b86](https://github.com/scaleapi/sgp-python-beta/commit/0ec9b868c7a29d4cdea9f4f4933ac6dbdce439ec))
* **api:** api update ([0274201](https://github.com/scaleapi/sgp-python-beta/commit/0274201fa05dc64f410788095c621f0b0a888f98))
* **api:** api update ([ad18d45](https://github.com/scaleapi/sgp-python-beta/commit/ad18d45455dcf21c2a42d48492e3d13a9fce0179))
* **client:** add follow_redirects request option ([8d3448d](https://github.com/scaleapi/sgp-python-beta/commit/8d3448d3264be245a532f02afec67f46c59191f0))


### Bug Fixes

* **docs/api:** remove references to nonexistent types ([6c8ad0c](https://github.com/scaleapi/sgp-python-beta/commit/6c8ad0c25bf1440f3349d416eabc0272df02558e))


### Chores

* **docs:** remove reference to rye shell ([8c6f8b7](https://github.com/scaleapi/sgp-python-beta/commit/8c6f8b7d5b02d3e3ec3dc794ea0778facf0994af))
* **docs:** remove unnecessary param examples ([96fcc25](https://github.com/scaleapi/sgp-python-beta/commit/96fcc2565136824cc8fa2416f97a86c8b03da866))

## 0.1.0-alpha.15 (2025-05-23)

Full Changelog: [v0.1.0-alpha.14...v0.1.0-alpha.15](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.14...v0.1.0-alpha.15)

### Features

* **api:** fix missing variant name ([60e4ff6](https://github.com/scaleapi/sgp-python-beta/commit/60e4ff6842ef5edf67c237bf4e5bae3cbcf7f4f8))
* **api:** fix pydantic model_X collisions ([20b40e7](https://github.com/scaleapi/sgp-python-beta/commit/20b40e7d15f13f03b7f54f29889100caff400839))
* **api:** manual updates ([9a6e7b3](https://github.com/scaleapi/sgp-python-beta/commit/9a6e7b37520b6ba028d40354fe0d01873a5f5e71))

## 0.1.0-alpha.14 (2025-05-22)

Full Changelog: [v0.1.0-alpha.13...v0.1.0-alpha.14](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.13...v0.1.0-alpha.14)

### Features

* **api:** api update ([a7854c8](https://github.com/scaleapi/sgp-python-beta/commit/a7854c88a19af8442bcb1e5a1a6fe2c24b4213d4))
* **api:** api update ([c057be8](https://github.com/scaleapi/sgp-python-beta/commit/c057be8694bee6eff4c0e0ac22fb08b9a2d1d99b))
* **api:** manual updates ([5f3f811](https://github.com/scaleapi/sgp-python-beta/commit/5f3f811d74d1b29eac140b2759e1790968ed5670))
* **api:** manual updates ([501caa0](https://github.com/scaleapi/sgp-python-beta/commit/501caa023930b0dcc085c41a9e4199c6015648d9))
* **api:** manual updates ([4c69d65](https://github.com/scaleapi/sgp-python-beta/commit/4c69d65dc11a2eaa2544772ff73505c11acd124e))
* **api:** manual updates ([0157eea](https://github.com/scaleapi/sgp-python-beta/commit/0157eeafa888830976d0fa97225a0661749ac666))

## 0.1.0-alpha.13 (2025-05-22)

Full Changelog: [v0.1.0-alpha.12...v0.1.0-alpha.13](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.12...v0.1.0-alpha.13)

### Features

* **api:** api update ([5b82818](https://github.com/scaleapi/sgp-python-beta/commit/5b8281851632b4112c52c41dcf5de986de45050e))
* **api:** api update ([7b9a1ea](https://github.com/scaleapi/sgp-python-beta/commit/7b9a1eab7b23e795e1f6b13840ef4305faa0dd32))
* **api:** api update ([d4c6fda](https://github.com/scaleapi/sgp-python-beta/commit/d4c6fdad60d19e5ce975bfbc12376b251801a865))
* **api:** api update ([a1410d2](https://github.com/scaleapi/sgp-python-beta/commit/a1410d217a935aec4cc628b6a9b16c01ef86022c))
* **api:** api update ([273c5e1](https://github.com/scaleapi/sgp-python-beta/commit/273c5e1b6051bf20c5d04d1062af465a727037a3))
* **api:** api update ([779e279](https://github.com/scaleapi/sgp-python-beta/commit/779e27983f5a924f8917198429e322198df883bc))
* **api:** api update ([0933742](https://github.com/scaleapi/sgp-python-beta/commit/09337428fcf8eb1273db579219391110c982923d))
* **api:** api update ([a81cc59](https://github.com/scaleapi/sgp-python-beta/commit/a81cc59f4ecd98d6f4938e9b9bb740a8dd0850f8))
* **api:** api update ([fece491](https://github.com/scaleapi/sgp-python-beta/commit/fece491adfe92a75b7c2f9babfb47cb2ff523f59))
* **api:** api update ([3132ac9](https://github.com/scaleapi/sgp-python-beta/commit/3132ac9561a12d3f84a76bdd7c82bd36bd8a8f06))
* **api:** api update ([b3167a6](https://github.com/scaleapi/sgp-python-beta/commit/b3167a6af1d92f393bf04adce08aedfc2e850b87))
* **api:** api update ([d0c013c](https://github.com/scaleapi/sgp-python-beta/commit/d0c013cfcb395069f99969c308a3deb8e36acf4b))
* **api:** manual updates ([f13f2a1](https://github.com/scaleapi/sgp-python-beta/commit/f13f2a152ac55117115fb8bb2d8dd543dedb77c2))
* **api:** manual updates ([af1ada4](https://github.com/scaleapi/sgp-python-beta/commit/af1ada46136c870f88dd4c89abb64768f4a04603))
* **api:** manual updates ([5aa4ea5](https://github.com/scaleapi/sgp-python-beta/commit/5aa4ea564d3f3139f7e8f43e2f2722e471162d8e))
* **api:** manual updates ([4f539f8](https://github.com/scaleapi/sgp-python-beta/commit/4f539f80a54782c00d8030a2f7e64db81e2a9028))
* **api:** manual updates ([5c01155](https://github.com/scaleapi/sgp-python-beta/commit/5c01155422f61cd6bb40454ef3fcb45c8542e059))
* **api:** move Container to shared ([2152b71](https://github.com/scaleapi/sgp-python-beta/commit/2152b717c14d718ff7280f796126e3e7213c0813))


### Bug Fixes

* **package:** support direct resource imports ([a0caefe](https://github.com/scaleapi/sgp-python-beta/commit/a0caefedd6379c43a8ea66d9181dd8b3c3096aef))
* **tests:** apply removeNullsFromHeaders transform ([9c1fb39](https://github.com/scaleapi/sgp-python-beta/commit/9c1fb39cb8b7c71c35c8e5ce6643bf28b2f7308a))


### Chores

* **ci:** fix installation instructions ([77e7457](https://github.com/scaleapi/sgp-python-beta/commit/77e745704c3fed8834332f5f3a60cb351d9535e1))
* **ci:** upload sdks to package manager ([9e5e4db](https://github.com/scaleapi/sgp-python-beta/commit/9e5e4dbe2ca5691684d7c94b8fcc07c61f21cd80))
* **ci:** use --pre flag for prerelease installation instructions ([ef07614](https://github.com/scaleapi/sgp-python-beta/commit/ef076143377808a173b6571b4cdb858139429161))
* **ci:** use --pre flag for prerelease installation instructions ([12a782c](https://github.com/scaleapi/sgp-python-beta/commit/12a782c721f51497de41f63db3b6db0860534170))
* configure new SDK language ([fdfbf2c](https://github.com/scaleapi/sgp-python-beta/commit/fdfbf2c78f97e7d1281be7aac127fc437ee59669))
* **docs:** grammar improvements ([e215c92](https://github.com/scaleapi/sgp-python-beta/commit/e215c92a1e8ae5aee0536fb033245cd3dd6ac1ba))
* **internal:** avoid errors for isinstance checks on proxies ([5f4179b](https://github.com/scaleapi/sgp-python-beta/commit/5f4179b46cf8977293df2e8619181ee2f0663449))

## 0.1.0-alpha.12 (2025-04-25)

Full Changelog: [v0.1.0-alpha.11...v0.1.0-alpha.12](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.11...v0.1.0-alpha.12)

### Features

* **api:** api update ([3cfce67](https://github.com/scaleapi/sgp-python-beta/commit/3cfce670301591436df98a53e816e806f2fd952e))

## 0.1.0-alpha.11 (2025-04-23)

Full Changelog: [v0.1.0-alpha.10...v0.1.0-alpha.11](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.10...v0.1.0-alpha.11)

### Features

* **api:** api update ([7dd030d](https://github.com/scaleapi/sgp-python-beta/commit/7dd030d4c05afbf0996d7518999ca8ad0eb6e5a0))


### Bug Fixes

* **pydantic v1:** more robust ModelField.annotation check ([14b6081](https://github.com/scaleapi/sgp-python-beta/commit/14b608127196089b64efe73576200bfeb6a7d24f))


### Chores

* broadly detect json family of content-type headers ([9a9dabe](https://github.com/scaleapi/sgp-python-beta/commit/9a9dabe03051b1e62ed79c9b9336c265c6c24527))
* **ci:** add timeout thresholds for CI jobs ([0a33fea](https://github.com/scaleapi/sgp-python-beta/commit/0a33fea76726982e704d1599c3f5a80867cb3a84))
* **ci:** only use depot for staging repos ([da2bc36](https://github.com/scaleapi/sgp-python-beta/commit/da2bc36d70511d7c77b8797d31abb33621bb4b01))
* **ci:** run on more branches and use depot runners ([ddbf6c7](https://github.com/scaleapi/sgp-python-beta/commit/ddbf6c7f5ee9d4472c4545673853ed502bd07a62))
* **internal:** fix list file params ([20eba2e](https://github.com/scaleapi/sgp-python-beta/commit/20eba2eb456acc873d79b329fa1836bd16af6fa2))
* **internal:** import reformatting ([fc395f5](https://github.com/scaleapi/sgp-python-beta/commit/fc395f5783168411f8ffc231f71c274c8f0e3818))
* **internal:** refactor retries to not use recursion ([ea5ebdc](https://github.com/scaleapi/sgp-python-beta/commit/ea5ebdc0c4d1aa7ef8a3c8156fce8e3b908caa57))
* **internal:** update models test ([7ae8a97](https://github.com/scaleapi/sgp-python-beta/commit/7ae8a97fe007dfe15f63468bdf24baaea442f193))

## 0.1.0-alpha.10 (2025-04-17)

Full Changelog: [v0.1.0-alpha.9...v0.1.0-alpha.10](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.9...v0.1.0-alpha.10)

### Features

* **api:** api update ([044fefc](https://github.com/scaleapi/sgp-python-beta/commit/044fefcaa84c7694fde0f73d6f3a5b29fc76e098))
* **api:** api update ([7095222](https://github.com/scaleapi/sgp-python-beta/commit/7095222925acfa17d33a5e9f0ea3d65212831e21))
* **api:** manual updates ([0b94e2f](https://github.com/scaleapi/sgp-python-beta/commit/0b94e2f170528fa471afc54248afc4719275b953))
* **api:** manual updates ([8a8bd63](https://github.com/scaleapi/sgp-python-beta/commit/8a8bd63fb26ad9a3fdbd3eba57f62eb08008a806))


### Bug Fixes

* **perf:** optimize some hot paths ([1976fbb](https://github.com/scaleapi/sgp-python-beta/commit/1976fbb7a9004f6a9768cc934025edd06e951dd2))
* **perf:** skip traversing types for NotGiven values ([04d48dc](https://github.com/scaleapi/sgp-python-beta/commit/04d48dc5473053469cb6e3a2c83a247736c55ced))


### Chores

* **client:** minor internal fixes ([274a136](https://github.com/scaleapi/sgp-python-beta/commit/274a1365f4b8b06e03f6faa579307389a394b7ad))
* **internal:** base client updates ([116fbf6](https://github.com/scaleapi/sgp-python-beta/commit/116fbf62eaef6ce9e5a796676eb1007d6384f682))
* **internal:** bump pyright version ([d623570](https://github.com/scaleapi/sgp-python-beta/commit/d623570bb964f4c68c69ce8170ad4324ac2e23b5))
* **internal:** codegen related update ([3abbaf7](https://github.com/scaleapi/sgp-python-beta/commit/3abbaf7c0df300969035da2d1d5bea4687cc4eb8))
* **internal:** expand CI branch coverage ([#95](https://github.com/scaleapi/sgp-python-beta/issues/95)) ([5f995e6](https://github.com/scaleapi/sgp-python-beta/commit/5f995e65e6f78e219c7c96d45ade69a1114a3a14))
* **internal:** reduce CI branch coverage ([2840b13](https://github.com/scaleapi/sgp-python-beta/commit/2840b13e606078157b3432815d5e0546268569f1))
* **internal:** remove trailing character ([#91](https://github.com/scaleapi/sgp-python-beta/issues/91)) ([88858d1](https://github.com/scaleapi/sgp-python-beta/commit/88858d146953d174ef449b3d0de11b03e4d81522))
* **internal:** slight transform perf improvement ([#93](https://github.com/scaleapi/sgp-python-beta/issues/93)) ([81fd884](https://github.com/scaleapi/sgp-python-beta/commit/81fd884857371fd25a7478138fd96a71aa4def83))
* **internal:** update pyright settings ([ed35bc1](https://github.com/scaleapi/sgp-python-beta/commit/ed35bc1436de07edb46ac9a6c989280d8445ca8d))
* slight wording improvement in README ([#94](https://github.com/scaleapi/sgp-python-beta/issues/94)) ([d268327](https://github.com/scaleapi/sgp-python-beta/commit/d268327c838b41dc61e74cf495d6074f452f7691))

## 0.1.0-alpha.9 (2025-03-27)

Full Changelog: [v0.1.0-alpha.8...v0.1.0-alpha.9](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.8...v0.1.0-alpha.9)

### Features

* **api:** api update ([#87](https://github.com/scaleapi/sgp-python-beta/issues/87)) ([7241799](https://github.com/scaleapi/sgp-python-beta/commit/7241799c9507303b833ca29740bc61b7656c50fe))
* **api:** manual updates ([#89](https://github.com/scaleapi/sgp-python-beta/issues/89)) ([456e1ff](https://github.com/scaleapi/sgp-python-beta/commit/456e1fff2edb5ce655d5692b10ce7981bd4aca9d))

## 0.1.0-alpha.8 (2025-03-26)

Full Changelog: [v0.1.0-alpha.7...v0.1.0-alpha.8](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.7...v0.1.0-alpha.8)

### Features

* **api:** manual updates ([#83](https://github.com/scaleapi/sgp-python-beta/issues/83)) ([a742789](https://github.com/scaleapi/sgp-python-beta/commit/a74278982def1c9ce87d1568cc3e6f65c992ec8b))
* **api:** manual updates ([#85](https://github.com/scaleapi/sgp-python-beta/issues/85)) ([de471f9](https://github.com/scaleapi/sgp-python-beta/commit/de471f973d6dfd512841ec7af8b762da4c1c9ade))

## 0.1.0-alpha.7 (2025-03-26)

Full Changelog: [v0.1.0-alpha.6...v0.1.0-alpha.7](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.6...v0.1.0-alpha.7)

### Features

* **api:** api update ([#78](https://github.com/scaleapi/sgp-python-beta/issues/78)) ([29cfd2f](https://github.com/scaleapi/sgp-python-beta/commit/29cfd2f2eb0cdc8526ea45c382433f52734c393c))
* **api:** api update ([#81](https://github.com/scaleapi/sgp-python-beta/issues/81)) ([10144d1](https://github.com/scaleapi/sgp-python-beta/commit/10144d14f6fcbafef4725bbcce06b90fc9c74152))


### Chores

* fix typos ([#80](https://github.com/scaleapi/sgp-python-beta/issues/80)) ([89f1f30](https://github.com/scaleapi/sgp-python-beta/commit/89f1f30ab410cc5af7f55dfb7e5bfc4a050324a7))

## 0.1.0-alpha.6 (2025-03-25)

Full Changelog: [v0.1.0-alpha.5...v0.1.0-alpha.6](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.5...v0.1.0-alpha.6)

### Features

* **api:** manual updates ([#75](https://github.com/scaleapi/sgp-python-beta/issues/75)) ([c5024ac](https://github.com/scaleapi/sgp-python-beta/commit/c5024acfddff1cd3410426d5690ea43d4b5c8ca6))

## 0.1.0-alpha.5 (2025-03-24)

Full Changelog: [v0.1.0-alpha.4...v0.1.0-alpha.5](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.4...v0.1.0-alpha.5)

### Features

* **api:** manual updates ([#72](https://github.com/scaleapi/sgp-python-beta/issues/72)) ([cd2e07e](https://github.com/scaleapi/sgp-python-beta/commit/cd2e07edc8e0566bc5192be8fec5ebc20441fa53))

## 0.1.0-alpha.4 (2025-03-17)

Full Changelog: [v0.1.0-alpha.3...v0.1.0-alpha.4](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.3...v0.1.0-alpha.4)

### Features

* **api:** api update ([#63](https://github.com/scaleapi/sgp-python-beta/issues/63)) ([2a712d0](https://github.com/scaleapi/sgp-python-beta/commit/2a712d0e51d74b6a5e76205341b08f65d07f796e))
* **api:** api update ([#65](https://github.com/scaleapi/sgp-python-beta/issues/65)) ([e5c071b](https://github.com/scaleapi/sgp-python-beta/commit/e5c071ba2535eb3bae74fbf470204af85131c4c9))


### Bug Fixes

* **ci:** ensure pip is always available ([#69](https://github.com/scaleapi/sgp-python-beta/issues/69)) ([e054e83](https://github.com/scaleapi/sgp-python-beta/commit/e054e831f464d6644f143b02ae71e9bd41e0abfa))
* **ci:** remove publishing patch ([#70](https://github.com/scaleapi/sgp-python-beta/issues/70)) ([cacfacf](https://github.com/scaleapi/sgp-python-beta/commit/cacfacf2e3a869893db9a378e86d7b321ece1d3e))
* **types:** handle more discriminated union shapes ([#68](https://github.com/scaleapi/sgp-python-beta/issues/68)) ([3013250](https://github.com/scaleapi/sgp-python-beta/commit/3013250213505a0d5fac5af06aae97f2a50736f6))


### Chores

* **internal:** bump rye to 0.44.0 ([#66](https://github.com/scaleapi/sgp-python-beta/issues/66)) ([ee4214c](https://github.com/scaleapi/sgp-python-beta/commit/ee4214c22b22d7cf529c1154c1ad517e79d40ba7))
* **internal:** codegen related update ([#62](https://github.com/scaleapi/sgp-python-beta/issues/62)) ([826dc22](https://github.com/scaleapi/sgp-python-beta/commit/826dc2260c20ba197e11a57ea86fded1457a6cd4))
* **internal:** codegen related update ([#67](https://github.com/scaleapi/sgp-python-beta/issues/67)) ([bb07a9c](https://github.com/scaleapi/sgp-python-beta/commit/bb07a9cc6887845c337fd956b2fe50a82a9896f0))
* **internal:** remove extra empty newlines ([#64](https://github.com/scaleapi/sgp-python-beta/issues/64)) ([d6cf4e1](https://github.com/scaleapi/sgp-python-beta/commit/d6cf4e1428717137f0cb51f7d47d2b2de2c94530))
* **internal:** remove unused http client options forwarding ([#58](https://github.com/scaleapi/sgp-python-beta/issues/58)) ([f5d4dbd](https://github.com/scaleapi/sgp-python-beta/commit/f5d4dbd4980aa57e649bde22f46f3c241add3ab6))


### Documentation

* revise readme docs about nested params ([#60](https://github.com/scaleapi/sgp-python-beta/issues/60)) ([bf4986e](https://github.com/scaleapi/sgp-python-beta/commit/bf4986eeede8dd114f3c05280e17b76d2defaeb6))

## 0.1.0-alpha.3 (2025-02-27)

Full Changelog: [v0.1.0-alpha.2...v0.1.0-alpha.3](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.2...v0.1.0-alpha.3)

### Features

* **api:** api update ([#38](https://github.com/scaleapi/sgp-python-beta/issues/38)) ([2b937be](https://github.com/scaleapi/sgp-python-beta/commit/2b937be5ad88ee52c14549dea80b075dae953848))
* **api:** api update ([#41](https://github.com/scaleapi/sgp-python-beta/issues/41)) ([8c13bc8](https://github.com/scaleapi/sgp-python-beta/commit/8c13bc821acf116e0f4831ec6512f99563f9c17a))
* **api:** manual updates ([#45](https://github.com/scaleapi/sgp-python-beta/issues/45)) ([47f0b21](https://github.com/scaleapi/sgp-python-beta/commit/47f0b21f78173cda0ed957d9e64cbaf39a79befd))
* **api:** manual updates ([#46](https://github.com/scaleapi/sgp-python-beta/issues/46)) ([d722b15](https://github.com/scaleapi/sgp-python-beta/commit/d722b157c62561666ede72aa2a3ede32753a6fe7))
* **api:** manual updates ([#48](https://github.com/scaleapi/sgp-python-beta/issues/48)) ([373c6e3](https://github.com/scaleapi/sgp-python-beta/commit/373c6e31bb8d3729e7b5617082c9f6d9ede7ea82))
* **api:** manual updates ([#56](https://github.com/scaleapi/sgp-python-beta/issues/56)) ([7ce79e6](https://github.com/scaleapi/sgp-python-beta/commit/7ce79e6545ccd1cb49dcc7ef880b5fc059ae149a))
* **client:** allow passing `NotGiven` for body ([#42](https://github.com/scaleapi/sgp-python-beta/issues/42)) ([b2e3024](https://github.com/scaleapi/sgp-python-beta/commit/b2e3024c1ed0ed05f18e300cd58b0cf99658e1fd))


### Bug Fixes

* **client:** mark some request bodies as optional ([b2e3024](https://github.com/scaleapi/sgp-python-beta/commit/b2e3024c1ed0ed05f18e300cd58b0cf99658e1fd))


### Chores

* **internal:** codegen related update ([#40](https://github.com/scaleapi/sgp-python-beta/issues/40)) ([c9f4be1](https://github.com/scaleapi/sgp-python-beta/commit/c9f4be1c9d5688926ba1b4033cbcac66950a950f))
* **internal:** fix devcontainers setup ([#43](https://github.com/scaleapi/sgp-python-beta/issues/43)) ([0752322](https://github.com/scaleapi/sgp-python-beta/commit/07523229582db759392ab96d8309e467a803f48b))
* **internal:** properly set __pydantic_private__ ([#44](https://github.com/scaleapi/sgp-python-beta/issues/44)) ([a539736](https://github.com/scaleapi/sgp-python-beta/commit/a539736da3a00608372e6fbbdc518bae9df7eb1d))
* remove custom code ([b3b0db0](https://github.com/scaleapi/sgp-python-beta/commit/b3b0db07483635cdb552d42f4068ce01531c0d8f))


### Documentation

* mention it is a beta client ([e8aea2a](https://github.com/scaleapi/sgp-python-beta/commit/e8aea2a70b60cb181ba5ade2c810960564e0cc84))

## 0.1.0-alpha.2 (2025-02-13)

Full Changelog: [v0.1.0-alpha.1...v0.1.0-alpha.2](https://github.com/scaleapi/sgp-python-beta/compare/v0.1.0-alpha.1...v0.1.0-alpha.2)

### Features

* **api:** manual updates ([#32](https://github.com/scaleapi/sgp-python-beta/issues/32)) ([927026a](https://github.com/scaleapi/sgp-python-beta/commit/927026a171687f67d06e1fe7a5b8a5cc99618642))
* **api:** manual updates ([#34](https://github.com/scaleapi/sgp-python-beta/issues/34)) ([11584bd](https://github.com/scaleapi/sgp-python-beta/commit/11584bddf865d0203bb720d18e7732433f4d74b0))


### Bug Fixes

* asyncify on non-asyncio runtimes ([#35](https://github.com/scaleapi/sgp-python-beta/issues/35)) ([ed7c2b9](https://github.com/scaleapi/sgp-python-beta/commit/ed7c2b9e4311f22ab832265329b4b14e0783e806))


### Chores

* remove custom code ([bbe97f6](https://github.com/scaleapi/sgp-python-beta/commit/bbe97f6096e6060bb8ffb91860b72278d8d12ea8))

## 0.1.0-alpha.1 (2025-02-12)

Full Changelog: [v0.0.1-alpha.0...v0.1.0-alpha.1](https://github.com/scaleapi/sgp-python-staging/compare/v0.0.1-alpha.0...v0.1.0-alpha.1)

### Features

* **api:** api update ([#11](https://github.com/scaleapi/sgp-python-staging/issues/11)) ([2fb80e0](https://github.com/scaleapi/sgp-python-staging/commit/2fb80e00757a9564a8fd20bf489f54f69a3df03f))
* **api:** api update ([#12](https://github.com/scaleapi/sgp-python-staging/issues/12)) ([2bf36d8](https://github.com/scaleapi/sgp-python-staging/commit/2bf36d893979de65fcbf11eec417c708a0d843a8))
* **api:** api update ([#13](https://github.com/scaleapi/sgp-python-staging/issues/13)) ([ece2fbf](https://github.com/scaleapi/sgp-python-staging/commit/ece2fbffe5f5472e557f4e334854bdc9423755d2))
* **api:** api update ([#15](https://github.com/scaleapi/sgp-python-staging/issues/15)) ([242cbb2](https://github.com/scaleapi/sgp-python-staging/commit/242cbb298df286d60d2f77e1debf178c3ed7a822))
* **api:** api update ([#16](https://github.com/scaleapi/sgp-python-staging/issues/16)) ([37450c1](https://github.com/scaleapi/sgp-python-staging/commit/37450c10cda23fb380a6d69347c08d13033be209))
* **api:** api update ([#23](https://github.com/scaleapi/sgp-python-staging/issues/23)) ([744c5e9](https://github.com/scaleapi/sgp-python-staging/commit/744c5e928b9a4cf933f2a208e99bc7abdf330ab2))
* **api:** manual updates ([#22](https://github.com/scaleapi/sgp-python-staging/issues/22)) ([cdca33d](https://github.com/scaleapi/sgp-python-staging/commit/cdca33d186e2315ba99cb0fb3974a6a6bc3191fe))
* **api:** manual updates ([#25](https://github.com/scaleapi/sgp-python-staging/issues/25)) ([a1d911f](https://github.com/scaleapi/sgp-python-staging/commit/a1d911fe312d00434b33a79c0dd821bf6c079450))
* **api:** manual updates ([#4](https://github.com/scaleapi/sgp-python-staging/issues/4)) ([c6d7dc0](https://github.com/scaleapi/sgp-python-staging/commit/c6d7dc0986c17e7a673088d4e412f3310a05dda6))
* **api:** manual updates ([#5](https://github.com/scaleapi/sgp-python-staging/issues/5)) ([01c515e](https://github.com/scaleapi/sgp-python-staging/commit/01c515e6427f9a7c6e57318e7ecac6f10acbc141))
* **client:** send `X-Stainless-Read-Timeout` header ([#19](https://github.com/scaleapi/sgp-python-staging/issues/19)) ([99ee73e](https://github.com/scaleapi/sgp-python-staging/commit/99ee73e2a4b601e2d89f3b28cda5e99e00a47f6f))


### Bug Fixes

* reuse model in pagination items type ([#9](https://github.com/scaleapi/sgp-python-staging/issues/9)) ([919a286](https://github.com/scaleapi/sgp-python-staging/commit/919a2860ba89be9606f2dc1fecf2623faf3b79ff))
* **tests:** make test_get_platform less flaky ([#7](https://github.com/scaleapi/sgp-python-staging/issues/7)) ([85de808](https://github.com/scaleapi/sgp-python-staging/commit/85de808e7a1dc78495422f0de14d063025c5d4da))


### Chores

* go live ([#1](https://github.com/scaleapi/sgp-python-staging/issues/1)) ([2d44278](https://github.com/scaleapi/sgp-python-staging/commit/2d4427857ebf005c08adfc914827691fe7fd0483))
* **internal:** avoid pytest-asyncio deprecation warning ([#8](https://github.com/scaleapi/sgp-python-staging/issues/8)) ([ddd5097](https://github.com/scaleapi/sgp-python-staging/commit/ddd5097d71b209866bbeab727d3b54ddc1d849ea))
* **internal:** bummp ruff dependency ([#18](https://github.com/scaleapi/sgp-python-staging/issues/18)) ([870d146](https://github.com/scaleapi/sgp-python-staging/commit/870d146cce49e09977a9b0a855b87ec408309501))
* **internal:** change default timeout to an int ([#17](https://github.com/scaleapi/sgp-python-staging/issues/17)) ([7a31b9e](https://github.com/scaleapi/sgp-python-staging/commit/7a31b9e6905efa0d513e0ef3038dcef16994303c))
* **internal:** fix type traversing dictionary params ([#20](https://github.com/scaleapi/sgp-python-staging/issues/20)) ([6ff63d1](https://github.com/scaleapi/sgp-python-staging/commit/6ff63d181ba8ca0e9875bc8da12d9a7c943baab2))
* **internal:** minor formatting changes ([#14](https://github.com/scaleapi/sgp-python-staging/issues/14)) ([f1bdbf8](https://github.com/scaleapi/sgp-python-staging/commit/f1bdbf8f82236d7a3572ea6dacfe5c94b7947a5c))
* **internal:** minor style changes ([#10](https://github.com/scaleapi/sgp-python-staging/issues/10)) ([7e4ea59](https://github.com/scaleapi/sgp-python-staging/commit/7e4ea591d2d06400560aee75826446c551835e31))
* **internal:** minor type handling changes ([#21](https://github.com/scaleapi/sgp-python-staging/issues/21)) ([55769fc](https://github.com/scaleapi/sgp-python-staging/commit/55769fcfcd60a2fdadd6e5a2f46f0a45dc694f29))
* **internal:** update client tests ([#24](https://github.com/scaleapi/sgp-python-staging/issues/24)) ([1d2db48](https://github.com/scaleapi/sgp-python-staging/commit/1d2db489f0f70e046208762449121e9033dd660e))
* update SDK settings ([#3](https://github.com/scaleapi/sgp-python-staging/issues/3)) ([888f0ca](https://github.com/scaleapi/sgp-python-staging/commit/888f0caaf4ff28fd5f0ecf5e5e02c3ec425b3d23))


### Documentation

* **raw responses:** fix duplicate `the` ([#6](https://github.com/scaleapi/sgp-python-staging/issues/6)) ([f7b1b6b](https://github.com/scaleapi/sgp-python-staging/commit/f7b1b6b1b9dc15bef3afee314b207a6df605a040))
