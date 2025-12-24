# Changelog

## 1.2.7 (2025-12-05)

Full Changelog: [v1.2.6...v1.2.7](https://github.com/prosights/recreate-sdk-python/compare/v1.2.6...v1.2.7)

### Chores

* **deps:** mypy 1.18.1 has a regression, pin to 1.17 ([3fea6f6](https://github.com/prosights/recreate-sdk-python/commit/3fea6f6b0e60aa6a6e8e91d3bc29918d5d94e0dd))
* **deps:** mypy 1.18.1 has a regression, pin to 1.17 ([236123e](https://github.com/prosights/recreate-sdk-python/commit/236123eaf3dbdab8030366aefe7d46eed849e7c3))
* update lockfile ([89370ad](https://github.com/prosights/recreate-sdk-python/commit/89370ad0605a3aa2363ed3b80e11ce7b5792d4a2))

## 1.2.6 (2025-11-28)

Full Changelog: [v1.2.5...v1.2.6](https://github.com/prosights/recreate-sdk-python/compare/v1.2.5...v1.2.6)

### Bug Fixes

* compat with Python 3.14 ([8a59869](https://github.com/prosights/recreate-sdk-python/commit/8a5986982750a1a7b1ea798a15c9c005cef3c673))
* **compat:** update signatures of `model_dump` and `model_dump_json` for Pydantic v1 ([aa600d5](https://github.com/prosights/recreate-sdk-python/commit/aa600d5f2c8ab3b0b3162a29950a7759cbf7e104))
* ensure streams are always closed ([c2d3990](https://github.com/prosights/recreate-sdk-python/commit/c2d3990150f27e856c7217caf8338e2e4f2ce782))


### Chores

* add Python 3.14 classifier and testing ([bffbae8](https://github.com/prosights/recreate-sdk-python/commit/bffbae888c243c2c035476effabcdeb07b4b26c7))
* **package:** drop Python 3.8 support ([2614dc9](https://github.com/prosights/recreate-sdk-python/commit/2614dc97d611a369260f8ed3945d85efa9293603))

## 1.2.5 (2025-11-04)

Full Changelog: [v1.2.4...v1.2.5](https://github.com/prosights/recreate-sdk-python/compare/v1.2.4...v1.2.5)

### Bug Fixes

* **client:** close streams without requiring full consumption ([9d7cbc1](https://github.com/prosights/recreate-sdk-python/commit/9d7cbc16302988fe9ad40e4c21963fca5c99fbfc))


### Chores

* bump `httpx-aiohttp` version to 0.1.9 ([07b2449](https://github.com/prosights/recreate-sdk-python/commit/07b2449fbe22594c075cd89a31ce4da454783da8))
* **internal/tests:** avoid race condition with implicit client cleanup ([367d2e8](https://github.com/prosights/recreate-sdk-python/commit/367d2e8a4cef4e3de7501b2f2fba3e7284122a04))
* **internal:** detect missing future annotations with ruff ([c2a9af1](https://github.com/prosights/recreate-sdk-python/commit/c2a9af1085bf72a6e67fd669bc128dd4cab8f2d9))
* **internal:** grammar fix (it's -&gt; its) ([b488991](https://github.com/prosights/recreate-sdk-python/commit/b488991de3f136c116d23630f2205ed5e3c040dc))

## 1.2.4 (2025-09-22)

Full Changelog: [v1.2.3...v1.2.4](https://github.com/prosights/recreate-sdk-python/compare/v1.2.3...v1.2.4)

## 1.2.3 (2025-09-22)

Full Changelog: [v1.2.2...v1.2.3](https://github.com/prosights/recreate-sdk-python/compare/v1.2.2...v1.2.3)

## 1.2.2 (2025-09-22)

Full Changelog: [v1.2.1...v1.2.2](https://github.com/prosights/recreate-sdk-python/compare/v1.2.1...v1.2.2)

## 1.2.1 (2025-09-21)

Full Changelog: [v1.2.0...v1.2.1](https://github.com/prosights/recreate-sdk-python/compare/v1.2.0...v1.2.1)

### Chores

* do not install brew dependencies in ./scripts/bootstrap by default ([d66bf23](https://github.com/prosights/recreate-sdk-python/commit/d66bf236afbcf1d7c066b96b1f08e002d606ffdc))
* **internal:** update pydantic dependency ([49f4fba](https://github.com/prosights/recreate-sdk-python/commit/49f4fba6cb93b0f596718e5811e1d09ed7c76c6b))
* **types:** change optional parameter type from NotGiven to Omit ([1066460](https://github.com/prosights/recreate-sdk-python/commit/10664605454501c4cff9a89e4c8e7f10fe2341ae))

## 1.2.0 (2025-09-06)

Full Changelog: [v1.1.2...v1.2.0](https://github.com/prosights/recreate-sdk-python/compare/v1.1.2...v1.2.0)

### Features

* improve future compat with pydantic v3 ([8b74cfd](https://github.com/prosights/recreate-sdk-python/commit/8b74cfd86bade6ba32dc9a8e1edf893128766eee))
* **types:** replace List[str] with SequenceNotStr in params ([86a0107](https://github.com/prosights/recreate-sdk-python/commit/86a01073e6aaaad91f74795ea6bc6236889e7849))


### Chores

* **internal:** move mypy configurations to `pyproject.toml` file ([087a058](https://github.com/prosights/recreate-sdk-python/commit/087a058d94d4a0ff9df2c8cca94ba2066e5416dc))
* **tests:** simplify `get_platform` test ([705720b](https://github.com/prosights/recreate-sdk-python/commit/705720b69f21415f281fe34a6e7ea6e26480a3ad))

## 1.1.2 (2025-08-31)

Full Changelog: [v1.1.1...v1.1.2](https://github.com/prosights/recreate-sdk-python/compare/v1.1.1...v1.1.2)

### Chores

* **internal:** add Sequence related utils ([af3e0ab](https://github.com/prosights/recreate-sdk-python/commit/af3e0ab2f452b6ef99e7ad6e2d4691452c9baf21))

## 1.1.1 (2025-08-27)

Full Changelog: [v1.1.0...v1.1.1](https://github.com/prosights/recreate-sdk-python/compare/v1.1.0...v1.1.1)

### Bug Fixes

* avoid newer type syntax ([eaa9b77](https://github.com/prosights/recreate-sdk-python/commit/eaa9b777802960723f6d1780d14a05715eb9e37f))


### Chores

* **internal:** change ci workflow machines ([4b38a77](https://github.com/prosights/recreate-sdk-python/commit/4b38a7705ebe7a1222b6d6d8b06ce8a4292d7ffa))
* **internal:** update pyright exclude list ([469b3dc](https://github.com/prosights/recreate-sdk-python/commit/469b3dc828342fb937a0201ae000056bdc251954))

## 1.1.0 (2025-08-22)

Full Changelog: [v1.0.3...v1.1.0](https://github.com/prosights/recreate-sdk-python/compare/v1.0.3...v1.1.0)

### Features

* **api:** update via SDK Studio ([d0cb2eb](https://github.com/prosights/recreate-sdk-python/commit/d0cb2eb84adccb52ff60ac877e41df41afe38181))

## 1.0.3 (2025-08-22)

Full Changelog: [v1.0.2...v1.0.3](https://github.com/prosights/recreate-sdk-python/compare/v1.0.2...v1.0.3)

### Chores

* update github action ([d5053f3](https://github.com/prosights/recreate-sdk-python/commit/d5053f35ba955a7e25d25bd5d2cf32b51888671c))

## 1.0.2 (2025-08-12)

Full Changelog: [v1.0.1...v1.0.2](https://github.com/prosights/recreate-sdk-python/compare/v1.0.1...v1.0.2)

### Chores

* **internal:** codegen related update ([94886a3](https://github.com/prosights/recreate-sdk-python/commit/94886a364df2a5a2e0b7ee946b13687d40c52297))
* **internal:** fix ruff target version ([4d0d6c5](https://github.com/prosights/recreate-sdk-python/commit/4d0d6c59c1263dfc9878d04749b5f5ec5dd73cd8))
* **internal:** update comment in script ([236f5cc](https://github.com/prosights/recreate-sdk-python/commit/236f5cc265a0b8a7849933f4dff0c27575c24e41))
* update @stainless-api/prism-cli to v5.15.0 ([bf74c02](https://github.com/prosights/recreate-sdk-python/commit/bf74c023539d4e6337938f011c798d0dee37b573))

## 1.0.1 (2025-08-04)

Full Changelog: [v1.0.0...v1.0.1](https://github.com/prosights/recreate-sdk-python/compare/v1.0.0...v1.0.1)

## 1.0.0 (2025-08-04)

Full Changelog: [v0.0.1-alpha.0...v1.0.0](https://github.com/prosights/recreate-sdk-python/compare/v0.0.1-alpha.0...v1.0.0)

### Chores

* update SDK settings ([f269ac2](https://github.com/prosights/recreate-sdk-python/commit/f269ac257cb9f7aa9a34781b81ba88086f5ff6df))
* update SDK settings ([6d0fbc5](https://github.com/prosights/recreate-sdk-python/commit/6d0fbc591c628d3384fb93089e1092002af86f1f))
