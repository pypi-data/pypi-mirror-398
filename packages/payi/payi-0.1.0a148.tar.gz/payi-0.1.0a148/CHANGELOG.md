# Changelog

## 0.1.0-alpha.148 (2025-12-19)

Full Changelog: [v0.1.0-alpha.147...v0.1.0-alpha.148](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.147...v0.1.0-alpha.148)

### Chores

* **internal:** add `--fix` argument to lint script ([1ad65fa](https://github.com/Pay-i/pay-i-python/commit/1ad65fa85e9a506c54aea1166b772ae320e81301))

## 0.1.0-alpha.147 (2025-12-18)

Full Changelog: [v0.1.0-alpha.146...v0.1.0-alpha.147](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.146...v0.1.0-alpha.147)

### Bug Fixes

* use async_to_httpx_files in patch method ([0f57419](https://github.com/Pay-i/pay-i-python/commit/0f57419ddac7a51b4cfb8e57f272738b56ba9b08))


### Chores

* **internal:** add missing files argument to base client ([d3c08cb](https://github.com/Pay-i/pay-i-python/commit/d3c08cb5dc8ca8d68a28985995cd3a5e5fa6d1fa))
* speedup initial import ([c45e208](https://github.com/Pay-i/pay-i-python/commit/c45e208b496c9ac13f736b08c222b7eab86f97f9))

## 0.1.0-alpha.146 (2025-12-10)

Full Changelog: [v0.1.0-alpha.145...v0.1.0-alpha.146](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.145...v0.1.0-alpha.146)

### Bug Fixes

* **types:** allow pyright to infer TypedDict types within SequenceNotStr ([3c188bd](https://github.com/Pay-i/pay-i-python/commit/3c188bd9ab2a8e68977e32123e588b2becbf0d08))


### Chores

* payi_instrument logging ([e86d9ee](https://github.com/Pay-i/pay-i-python/commit/e86d9eec6dbc3dbc22bcd13d11af8222a114da6d))

## 0.1.0-alpha.145 (2025-12-06)

Full Changelog: [v0.1.0-alpha.144...v0.1.0-alpha.145](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.144...v0.1.0-alpha.145)

### Features

* **api:** manual updates ([8ebb98a](https://github.com/Pay-i/pay-i-python/commit/8ebb98ab055c4df7a7c468098413e67cfb36a78c))

## 0.1.0-alpha.144 (2025-12-03)

Full Changelog: [v0.1.0-alpha.143...v0.1.0-alpha.144](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.143...v0.1.0-alpha.144)

### Features

* capture context state in asyncio.gather ([#407](https://github.com/Pay-i/pay-i-python/issues/407)) ([697b2cb](https://github.com/Pay-i/pay-i-python/commit/697b2cbd90ff6507424c5f3fa02bb978ad930088))
* convert all property values to str ([#408](https://github.com/Pay-i/pay-i-python/issues/408)) ([34adf8b](https://github.com/Pay-i/pay-i-python/commit/34adf8bd1441a52db3c33a172d709df3bd2d4aad))
* instrument log prompt and response setting in track and track_context ([#404](https://github.com/Pay-i/pay-i-python/issues/404)) ([5162564](https://github.com/Pay-i/pay-i-python/commit/516256455b5ba2292fad27d401e9abde3a53aed7))
* instrument openai parse() ([#406](https://github.com/Pay-i/pay-i-python/issues/406)) ([78dd447](https://github.com/Pay-i/pay-i-python/commit/78dd4476a56d1c2d2fab5222badae98f63f4f0ba))

## 0.1.0-alpha.143 (2025-12-03)

Full Changelog: [v0.1.0-alpha.142...v0.1.0-alpha.143](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.142...v0.1.0-alpha.143)

### Bug Fixes

* ensure streams are always closed ([89597a0](https://github.com/Pay-i/pay-i-python/commit/89597a0410de59dce92870023e3c291f90011bae))


### Chores

* **deps:** mypy 1.18.1 has a regression, pin to 1.17 ([b1319d6](https://github.com/Pay-i/pay-i-python/commit/b1319d6ae4ce91f84adf1d5cda1b4fcb7e7f2450))
* **docs:** use environment variables for authentication in code snippets ([617a802](https://github.com/Pay-i/pay-i-python/commit/617a802563955d4095d3d219b19c250c4801890e))
* update lockfile ([1107eb0](https://github.com/Pay-i/pay-i-python/commit/1107eb0dec90e15998b4e951b8b8aaaa56424ed0))

## 0.1.0-alpha.142 (2025-11-26)

Full Changelog: [v0.1.0-alpha.141...v0.1.0-alpha.142](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.141...v0.1.0-alpha.142)

### Bug Fixes

* asyncio.create_task wrapper ([#402](https://github.com/Pay-i/pay-i-python/issues/402)) ([81f43c2](https://github.com/Pay-i/pay-i-python/commit/81f43c20ad35308ae69c3095ff8bbf69f651361b))

## 0.1.0-alpha.141 (2025-11-25)

Full Changelog: [v0.1.0-alpha.140...v0.1.0-alpha.141](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.140...v0.1.0-alpha.141)

### Bug Fixes

* instrument azure deployment name ([38fba65](https://github.com/Pay-i/pay-i-python/commit/38fba650b2fe09c95efe91052f18a768f8e4ca92))

## 0.1.0-alpha.140 (2025-11-24)

Full Changelog: [v0.1.0-alpha.139...v0.1.0-alpha.140](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.139...v0.1.0-alpha.140)

### Bug Fixes

* instrument azure deployment name ([5e74ec2](https://github.com/Pay-i/pay-i-python/commit/5e74ec206637ebb804fdf932eb1d8088f96cf611))


### Chores

* add Python 3.14 classifier and testing ([fda7bbc](https://github.com/Pay-i/pay-i-python/commit/fda7bbce713fdb9786634e0e562eafadc6310815))

## 0.1.0-alpha.139 (2025-11-21)

Full Changelog: [v0.1.0-alpha.138...v0.1.0-alpha.139](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.138...v0.1.0-alpha.139)

### Features

* Azure Anthropic ([#397](https://github.com/Pay-i/pay-i-python/issues/397)) ([6e26b73](https://github.com/Pay-i/pay-i-python/commit/6e26b73d6ae6b9a75587ef82b160f792c973ddeb))

## 0.1.0-alpha.138 (2025-11-18)

Full Changelog: [v0.1.0-alpha.137...v0.1.0-alpha.138](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.137...v0.1.0-alpha.138)

### Features

* **api:** manual updates ([8a357fd](https://github.com/Pay-i/pay-i-python/commit/8a357fddaea51eeaedfbd2855d381a250ea0b69a))

## 0.1.0-alpha.137 (2025-11-12)

Full Changelog: [v0.1.0-alpha.136...v0.1.0-alpha.137](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.136...v0.1.0-alpha.137)

### Bug Fixes

* compat with Python 3.14 ([fb9eb17](https://github.com/Pay-i/pay-i-python/commit/fb9eb178b8355db3a0582ba50b0127cb4fe3c77a))
* **compat:** update signatures of `model_dump` and `model_dump_json` for Pydantic v1 ([4f1bce5](https://github.com/Pay-i/pay-i-python/commit/4f1bce57cb24f10e8a10f600c67997eac348a4c6))


### Chores

* **package:** drop Python 3.8 support ([ca7e546](https://github.com/Pay-i/pay-i-python/commit/ca7e5465046cc9fd3f3df3f2b145ef9037205a7c))

## 0.1.0-alpha.136 (2025-11-07)

Full Changelog: [v0.1.0-alpha.135...v0.1.0-alpha.136](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.135...v0.1.0-alpha.136)

### Features

* copy current thread context state to new task state ([#392](https://github.com/Pay-i/pay-i-python/issues/392)) ([4b3a80e](https://github.com/Pay-i/pay-i-python/commit/4b3a80e45bb61edf0bd8734cc7cd530396e11761))

## 0.1.0-alpha.135 (2025-11-04)

Full Changelog: [v0.1.0-alpha.134...v0.1.0-alpha.135](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.134...v0.1.0-alpha.135)

### Features

* **api:** manual updates ([27643c5](https://github.com/Pay-i/pay-i-python/commit/27643c537491c2158bba978fad5081840d939661))
* instrument openai and anthropic response headers ([#391](https://github.com/Pay-i/pay-i-python/issues/391)) ([1af61aa](https://github.com/Pay-i/pay-i-python/commit/1af61aa447fc28b324648163e31c8e02326136df))


### Chores

* **internal/tests:** avoid race condition with implicit client cleanup ([254063e](https://github.com/Pay-i/pay-i-python/commit/254063e279a60865250fe9b4dbef8542fff634d6))
* **internal:** grammar fix (it's -&gt; its) ([d2d51bf](https://github.com/Pay-i/pay-i-python/commit/d2d51bf82e221ce2162f161848c7a838f5837056))

## 0.1.0-alpha.134 (2025-10-30)

Full Changelog: [v0.1.0-alpha.133...v0.1.0-alpha.134](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.133...v0.1.0-alpha.134)

### Features

* model mapping configuration ([#388](https://github.com/Pay-i/pay-i-python/issues/388)) ([dd3c9da](https://github.com/Pay-i/pay-i-python/commit/dd3c9da33328b8005e416341f2017dbe17c2fc1e))

## 0.1.0-alpha.133 (2025-10-30)

Full Changelog: [v0.1.0-alpha.132...v0.1.0-alpha.133](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.132...v0.1.0-alpha.133)

### Bug Fixes

* **client:** close streams without requiring full consumption ([6ec5c11](https://github.com/Pay-i/pay-i-python/commit/6ec5c115c06a2d967d06464054bc7221ea917805))

## 0.1.0-alpha.132 (2025-10-22)

Full Changelog: [v0.1.0-alpha.131...v0.1.0-alpha.132](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.131...v0.1.0-alpha.132)

### Features

* thread local storage ([#385](https://github.com/Pay-i/pay-i-python/issues/385)) ([057de83](https://github.com/Pay-i/pay-i-python/commit/057de83b15fc791e6eb813d8cb62a54a0de0eea9))

## 0.1.0-alpha.131 (2025-10-21)

Full Changelog: [v0.1.0-alpha.130...v0.1.0-alpha.131](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.130...v0.1.0-alpha.131)

### Features

* **api:** limit properties ([16edabe](https://github.com/Pay-i/pay-i-python/commit/16edabe61a480db13ffb71cce1932bf3b017d766))

## 0.1.0-alpha.130 (2025-10-18)

Full Changelog: [v0.1.0-alpha.129...v0.1.0-alpha.130](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.129...v0.1.0-alpha.130)

### Chores

* bump `httpx-aiohttp` version to 0.1.9 ([94e1cd5](https://github.com/Pay-i/pay-i-python/commit/94e1cd5dd8628fd6b146f0b6ecbd6ebb5be7b5cd))

## 0.1.0-alpha.129 (2025-10-17)

Full Changelog: [v0.1.0-alpha.128...v0.1.0-alpha.129](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.128...v0.1.0-alpha.129)

### Bug Fixes

* restore_use_case_step inheritance ([aa78a82](https://github.com/Pay-i/pay-i-python/commit/aa78a820dae165736784c9c9165e1c4f7475d98d))

## 0.1.0-alpha.128 (2025-10-11)

Full Changelog: [v0.1.0-alpha.127...v0.1.0-alpha.128](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.127...v0.1.0-alpha.128)

### Chores

* **internal:** detect missing future annotations with ruff ([d068700](https://github.com/Pay-i/pay-i-python/commit/d068700e0368d22a79c3a24e300eabf9face720a))

## 0.1.0-alpha.127 (2025-10-09)

Full Changelog: [v0.1.0-alpha.126...v0.1.0-alpha.127](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.126...v0.1.0-alpha.127)

### Features

* manual updates ([8becaf6](https://github.com/Pay-i/pay-i-python/commit/8becaf66c1ab732de4224fc7f0ca01270cbbe9e9))

## 0.1.0-alpha.126 (2025-10-07)

Full Changelog: [v0.1.0-alpha.125...v0.1.0-alpha.126](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.125...v0.1.0-alpha.126)

### Features

* offline instrumentation ([#378](https://github.com/Pay-i/pay-i-python/issues/378)) ([ae6a60f](https://github.com/Pay-i/pay-i-python/commit/ae6a60f5992f10bccbdaaf56a0097b2661e70643))

## 0.1.0-alpha.125 (2025-09-30)

Full Changelog: [v0.1.0-alpha.124...v0.1.0-alpha.125](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.124...v0.1.0-alpha.125)

### Bug Fixes

* do not set headers with default to omit ([addd6f4](https://github.com/Pay-i/pay-i-python/commit/addd6f4231c95270ba83d5d651b68a34ec89de1b))

## 0.1.0-alpha.124 (2025-09-24)

Full Changelog: [v0.1.0-alpha.123...v0.1.0-alpha.124](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.123...v0.1.0-alpha.124)

### Chores

* do not install brew dependencies in ./scripts/bootstrap by default ([7b5100c](https://github.com/Pay-i/pay-i-python/commit/7b5100c5e554f0bd186c8075ef6a41aec82373cb))
* **types:** change optional parameter type from NotGiven to Omit ([1cef789](https://github.com/Pay-i/pay-i-python/commit/1cef789e7b927c1f7a153bd466e7ff232dfca19d))

## 0.1.0-alpha.123 (2025-09-24)

Full Changelog: [v0.1.0-alpha.122...v0.1.0-alpha.123](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.122...v0.1.0-alpha.123)

### Chores

* **internal:** update pydantic dependency ([fb48d11](https://github.com/Pay-i/pay-i-python/commit/fb48d111c97e54ec3f63b9f3887cb41446dc7ec3))
* **types:** change optional parameter type from NotGiven to Omit ([1bb17c3](https://github.com/Pay-i/pay-i-python/commit/1bb17c32a90ae1398d38cb66e46746bc6ab7ea46))

## 0.1.0-alpha.122 (2025-09-18)

Full Changelog: [v0.1.0-alpha.121...v0.1.0-alpha.122](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.121...v0.1.0-alpha.122)

### Bug Fixes

* merge properties properly ([#371](https://github.com/Pay-i/pay-i-python/issues/371)) ([66d16d6](https://github.com/Pay-i/pay-i-python/commit/66d16d6e5c62ddc610a1c7e70c21947267da04bf))

## 0.1.0-alpha.121 (2025-09-17)

Full Changelog: [v0.1.0-alpha.120...v0.1.0-alpha.121](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.120...v0.1.0-alpha.121)

## 0.1.0-alpha.120 (2025-09-16)

Full Changelog: [v0.1.0-alpha.119...v0.1.0-alpha.120](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.119...v0.1.0-alpha.120)

### Bug Fixes

* ingest exception logging ([647f9e7](https://github.com/Pay-i/pay-i-python/commit/647f9e74a7bc9973539329de306db1d2bf4a8db0))

## 0.1.0-alpha.119 (2025-09-16)

Full Changelog: [v0.1.0-alpha.118...v0.1.0-alpha.119](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.118...v0.1.0-alpha.119)

### Bug Fixes

* log APIStatusError exception processing as warning ([64aca26](https://github.com/Pay-i/pay-i-python/commit/64aca26e4139d9aebb02a0ab386e4a11978005a6))

## 0.1.0-alpha.118 (2025-09-16)

Full Changelog: [v0.1.0-alpha.117...v0.1.0-alpha.118](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.117...v0.1.0-alpha.118)

### Bug Fixes

* bedrock resource, copy extra_headers ([#366](https://github.com/Pay-i/pay-i-python/issues/366)) ([8e0d188](https://github.com/Pay-i/pay-i-python/commit/8e0d1889bd48b398f27c5ea69b3cab5db23e31fa))

## 0.1.0-alpha.117 (2025-09-16)

Full Changelog: [v0.1.0-alpha.116...v0.1.0-alpha.117](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.116...v0.1.0-alpha.117)

### Chores

* **tests:** simplify `get_platform` test ([9aeaba6](https://github.com/Pay-i/pay-i-python/commit/9aeaba6c83b4cdcd6bb348609a9e22ad86b14b7a))

## 0.1.0-alpha.116 (2025-09-06)

Full Changelog: [v0.1.0-alpha.115...v0.1.0-alpha.116](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.115...v0.1.0-alpha.116)

### Features

* aws bedrock guardians ([#363](https://github.com/Pay-i/pay-i-python/issues/363)) ([08d74c8](https://github.com/Pay-i/pay-i-python/commit/08d74c8d49368cc0e8ae0b8d0f9a94458e7be0fa))

## 0.1.0-alpha.115 (2025-09-05)

Full Changelog: [v0.1.0-alpha.114...v0.1.0-alpha.115](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.114...v0.1.0-alpha.115)

### Features

* improve future compat with pydantic v3 ([4eed721](https://github.com/Pay-i/pay-i-python/commit/4eed7215f87395b4597e3ede506e32b2c37b6c3c))
* **types:** replace List[str] with SequenceNotStr in params ([7c0db43](https://github.com/Pay-i/pay-i-python/commit/7c0db435c169460566096441e24a87fdf2c9e6c8))


### Chores

* **internal:** add Sequence related utils ([9797684](https://github.com/Pay-i/pay-i-python/commit/979768499fe48ef1b580082266dfbc6541016b6c))
* **internal:** move mypy configurations to `pyproject.toml` file ([aa61c96](https://github.com/Pay-i/pay-i-python/commit/aa61c96c8b8c4b493fe09c5bd4a259d5823936a8))

## 0.1.0-alpha.114 (2025-08-28)

Full Changelog: [v0.1.0-alpha.113...v0.1.0-alpha.114](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.113...v0.1.0-alpha.114)

### Bug Fixes

* all response dict key access with get() ([#360](https://github.com/Pay-i/pay-i-python/issues/360)) ([83bd564](https://github.com/Pay-i/pay-i-python/commit/83bd564c909daf73660f898e00aa49157a1ba5db))

## 0.1.0-alpha.113 (2025-08-27)

Full Changelog: [v0.1.0-alpha.112...v0.1.0-alpha.113](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.112...v0.1.0-alpha.113)

### Bug Fixes

* avoid newer type syntax ([4f10599](https://github.com/Pay-i/pay-i-python/commit/4f10599eb1cfb46a2f758914d812fa80ed233bbe))


### Chores

* **internal:** change ci workflow machines ([ff1ef13](https://github.com/Pay-i/pay-i-python/commit/ff1ef13c9d19b02f456467a3d3b8c0b47b3ce9f9))
* **internal:** update pyright exclude list ([e0c2ad1](https://github.com/Pay-i/pay-i-python/commit/e0c2ad17071ca681fccb8fb435508f2e8780cff6))

## 0.1.0-alpha.112 (2025-08-22)

Full Changelog: [v0.1.0-alpha.111...v0.1.0-alpha.112](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.111...v0.1.0-alpha.112)

### Chores

* update github action ([002abfa](https://github.com/Pay-i/pay-i-python/commit/002abfad147184c2e07454f8c5078387d0f88d56))

## 0.1.0-alpha.111 (2025-08-18)

Full Changelog: [v0.1.0-alpha.110...v0.1.0-alpha.111](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.110...v0.1.0-alpha.111)

### Features

* anthropic large context, cohere english v3 embed, amazon titan v1 text embed ([#356](https://github.com/Pay-i/pay-i-python/issues/356)) ([9a3549e](https://github.com/Pay-i/pay-i-python/commit/9a3549e1abd284d1647d7c63fa3cdff01ac14a98))

## 0.1.0-alpha.110 (2025-08-09)

Full Changelog: [v0.1.0-alpha.109...v0.1.0-alpha.110](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.109...v0.1.0-alpha.110)

### Chores

* **internal:** update comment in script ([62f3d00](https://github.com/Pay-i/pay-i-python/commit/62f3d00cbe71bc217f13b9e354a53b9d42dd8c27))
* update @stainless-api/prism-cli to v5.15.0 ([87fc0ef](https://github.com/Pay-i/pay-i-python/commit/87fc0ef32878b5ba1c4003d4c392ce31f8cfde86))

## 0.1.0-alpha.109 (2025-08-06)

Full Changelog: [v0.1.0-alpha.108...v0.1.0-alpha.109](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.108...v0.1.0-alpha.109)

### Chores

* **internal:** fix ruff target version ([e6299f0](https://github.com/Pay-i/pay-i-python/commit/e6299f02beafe98b848e1853b1ac9e8f27a51b43))

## 0.1.0-alpha.108 (2025-08-05)

Full Changelog: [v0.1.0-alpha.107...v0.1.0-alpha.108](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.107...v0.1.0-alpha.108)

### Features

* account_name ([#352](https://github.com/Pay-i/pay-i-python/issues/352)) ([719e871](https://github.com/Pay-i/pay-i-python/commit/719e871927187e2bce511d637144fd99a59b7234))

## 0.1.0-alpha.107 (2025-07-31)

Full Changelog: [v0.1.0-alpha.106...v0.1.0-alpha.107](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.106...v0.1.0-alpha.107)

### Features

* **api:** manual updates ([d348443](https://github.com/Pay-i/pay-i-python/commit/d3484438517ab70577dea7d77abfe9864a5678aa))
* **client:** support file upload requests ([5019812](https://github.com/Pay-i/pay-i-python/commit/501981286bb2996403bcf0415542325d7efb8d2f))

## 0.1.0-alpha.106 (2025-07-30)

Full Changelog: [v0.1.0-alpha.105...v0.1.0-alpha.106](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.105...v0.1.0-alpha.106)

### Features

* ignore request tags ([c1a7479](https://github.com/Pay-i/pay-i-python/commit/c1a747945e5557cf5fe38b70edcd7cf16ddf138c))

## 0.1.0-alpha.105 (2025-07-29)

Full Changelog: [v0.1.0-alpha.104...v0.1.0-alpha.105](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.104...v0.1.0-alpha.105)

### Features

* **api:** manual updates ([48d04d8](https://github.com/Pay-i/pay-i-python/commit/48d04d8d5e8d0627d2c52f28639640f09c960445))

## 0.1.0-alpha.104 (2025-07-25)

Full Changelog: [v0.1.0-alpha.103...v0.1.0-alpha.104](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.103...v0.1.0-alpha.104)

### Chores

* **project:** add settings file for vscode ([b3eb6f5](https://github.com/Pay-i/pay-i-python/commit/b3eb6f51668fbaa2c81fd0822e883d181c989df2))

## 0.1.0-alpha.103 (2025-07-23)

Full Changelog: [v0.1.0-alpha.102...v0.1.0-alpha.103](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.102...v0.1.0-alpha.103)

### Bug Fixes

* **parsing:** parse extra field types ([75f6333](https://github.com/Pay-i/pay-i-python/commit/75f633331136621ecf3adf2e72b46f60b75d6d8e))

## 0.1.0-alpha.102 (2025-07-22)

Full Changelog: [v0.1.0-alpha.101...v0.1.0-alpha.102](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.101...v0.1.0-alpha.102)

### Bug Fixes

* **parsing:** ignore empty metadata ([8599474](https://github.com/Pay-i/pay-i-python/commit/859947442835af355059aa132267284e465cee98))

## 0.1.0-alpha.101 (2025-07-18)

Full Changelog: [v0.1.0-alpha.100...v0.1.0-alpha.101](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.100...v0.1.0-alpha.101)

### Bug Fixes

* properly merge use case state with parent context ([#344](https://github.com/Pay-i/pay-i-python/issues/344)) ([2a001f8](https://github.com/Pay-i/pay-i-python/commit/2a001f8c49a815c08494f08e1393e67728c6da48))

## 0.1.0-alpha.100 (2025-07-16)

Full Changelog: [v0.1.0-alpha.99...v0.1.0-alpha.100](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.99...v0.1.0-alpha.100)

### Features

* use cases and request property bags ([#342](https://github.com/Pay-i/pay-i-python/issues/342)) ([985209e](https://github.com/Pay-i/pay-i-python/commit/985209e1ac179ac7338d3845bd6498aa3d08afc3))

## 0.1.0-alpha.99 (2025-07-15)

Full Changelog: [v0.1.0-alpha.98...v0.1.0-alpha.99](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.98...v0.1.0-alpha.99)

### Features

* clean up environment call outs ([4ec3d02](https://github.com/Pay-i/pay-i-python/commit/4ec3d02fb19859e8f8fd4454bc88aa96755e0b15))


### Bug Fixes

* **client:** don't send Content-Type header on GET requests ([26a0c6b](https://github.com/Pay-i/pay-i-python/commit/26a0c6be48e8ab1d7542f17afe51a65b92388212))

## 0.1.0-alpha.98 (2025-07-11)

Full Changelog: [v0.1.0-alpha.97...v0.1.0-alpha.98](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.97...v0.1.0-alpha.98)

### Features

* instrument provider module version ([9bc9596](https://github.com/Pay-i/pay-i-python/commit/9bc9596edb103b187dc468b9592d5e8a0c5f38f3))


### Bug Fixes

* **parsing:** correctly handle nested discriminated unions ([38be788](https://github.com/Pay-i/pay-i-python/commit/38be7889bf028750274f66a584e229a9578033eb))


### Chores

* **internal:** bump pinned h11 dep ([9a1ef2e](https://github.com/Pay-i/pay-i-python/commit/9a1ef2efb18e5bd7e2e66a8176feefdc1c22ea22))
* **package:** mark python 3.13 as supported ([5ab6ac5](https://github.com/Pay-i/pay-i-python/commit/5ab6ac561585ffdc8ff1d07b06d873e0ef99a1ea))
* **readme:** fix version rendering on pypi ([3f91efc](https://github.com/Pay-i/pay-i-python/commit/3f91efc050e6ffcf97617f2b727c2f68fd83d91f))

## 0.1.0-alpha.97 (2025-07-08)

Full Changelog: [v0.1.0-alpha.96...v0.1.0-alpha.97](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.96...v0.1.0-alpha.97)

## 0.1.0-alpha.96 (2025-07-07)

Full Changelog: [v0.1.0-alpha.95...v0.1.0-alpha.96](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.95...v0.1.0-alpha.96)

### Features

* **api:** manual updates ([4419663](https://github.com/Pay-i/pay-i-python/commit/4419663a981ee2f427d25ff6e7ea7e440e63bc75))

## 0.1.0-alpha.95 (2025-07-07)

Full Changelog: [v0.1.0-alpha.94...v0.1.0-alpha.95](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.94...v0.1.0-alpha.95)

### Features

* **api:** manual updates ([277cffb](https://github.com/Pay-i/pay-i-python/commit/277cffb67c28c34de6a83604f416b057c913c250))
* **api:** manual updates ([d4c3cc6](https://github.com/Pay-i/pay-i-python/commit/d4c3cc61f36d020c853a204f57d2ab8e9bdcf06b))
* **api:** manual updates 2 ([6ebab4d](https://github.com/Pay-i/pay-i-python/commit/6ebab4d8192a521278e2f65eb51c03a922d539f3))
* **api:** manual updates2 ([4cd5132](https://github.com/Pay-i/pay-i-python/commit/4cd5132bad307af7229198600aa72f851cd1c282))


### Chores

* **internal:** version bump ([5bbd1b3](https://github.com/Pay-i/pay-i-python/commit/5bbd1b3e88828f46d082503b99f19c4b4390cffa))

## 0.1.0-alpha.94 (2025-07-02)

Full Changelog: [v0.1.0-alpha.93...v0.1.0-alpha.94](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.93...v0.1.0-alpha.94)

### Chores

* **ci:** change upload type ([9646d10](https://github.com/Pay-i/pay-i-python/commit/9646d106009da1fe89c14b77d9bba23a1195a8ab))

## 0.1.0-alpha.93 (2025-07-01)

Full Changelog: [v0.1.0-alpha.92...v0.1.0-alpha.93](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.92...v0.1.0-alpha.93)

### Features

* limit connection error log messages ([#333](https://github.com/Pay-i/pay-i-python/issues/333)) ([f454006](https://github.com/Pay-i/pay-i-python/commit/f454006c80beaf09dfe92eba98e4aaeae0e017fd))

## 0.1.0-alpha.92 (2025-06-30)

Full Changelog: [v0.1.0-alpha.91...v0.1.0-alpha.92](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.91...v0.1.0-alpha.92)

### Bug Fixes

* **ci:** correct conditional ([b1b1775](https://github.com/Pay-i/pay-i-python/commit/b1b17750b13111f2eb5a7d76fa84134f07575e3b))
* **ci:** release-doctor — report correct token name ([48fc8a1](https://github.com/Pay-i/pay-i-python/commit/48fc8a1381674b1506518c149c483a518d693ffd))


### Chores

* **ci:** only run for pushes and fork pull requests ([ba502ab](https://github.com/Pay-i/pay-i-python/commit/ba502aba39af4a8aca8b64c90b1cb8d323926f93))

## 0.1.0-alpha.91 (2025-06-25)

Full Changelog: [v0.1.0-alpha.90...v0.1.0-alpha.91](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.90...v0.1.0-alpha.91)

### Features

* do not instrument inline base64 image data by default ([#331](https://github.com/Pay-i/pay-i-python/issues/331)) ([8b0455d](https://github.com/Pay-i/pay-i-python/commit/8b0455d24cda3060bc2170b05e5438c72885bf1a))


### Chores

* **tests:** skip some failing tests on the latest python versions ([1856b99](https://github.com/Pay-i/pay-i-python/commit/1856b99b5802dc02e4f536818f1a205d9da708c2))

## 0.1.0-alpha.90 (2025-06-23)

Full Changelog: [v0.1.0-alpha.89...v0.1.0-alpha.90](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.89...v0.1.0-alpha.90)

### Features

* **client:** add support for aiohttp ([e875663](https://github.com/Pay-i/pay-i-python/commit/e87566399607c87091b4a83f855910b78107e31b))


### Bug Fixes

* **client:** correctly parse binary response | stream ([6bb78c4](https://github.com/Pay-i/pay-i-python/commit/6bb78c4488dc3af5d556c1a063372be6ae018342))
* **tests:** fix: tests which call HTTP endpoints directly with the example parameters ([eb727c7](https://github.com/Pay-i/pay-i-python/commit/eb727c742f8f6ac0c9487d7ff4e6e7698afacd0d))


### Chores

* **ci:** enable for pull requests ([e999e4e](https://github.com/Pay-i/pay-i-python/commit/e999e4ee3a05ea8dcb8518eaba1e6ea5f3f958e0))
* **internal:** update conftest.py ([d668101](https://github.com/Pay-i/pay-i-python/commit/d66810199d9394852f8c5783801fc055745a3ef2))
* **internal:** version bump ([5616a6a](https://github.com/Pay-i/pay-i-python/commit/5616a6a1147d94e8ca69350dd5b21a211b9eed75))
* **internal:** version bump ([d93bffd](https://github.com/Pay-i/pay-i-python/commit/d93bffd3f408fc6ec34bf4071dddcc2e55653fcc))
* **internal:** version bump ([d2022a7](https://github.com/Pay-i/pay-i-python/commit/d2022a710955c9bbf6683a96bc3e2fd46a14c3e7))
* **readme:** update badges ([5219fd7](https://github.com/Pay-i/pay-i-python/commit/5219fd70ef3c88f114f6b69e89caabcf0d5a39e0))
* **tests:** add tests for httpx client instantiation & proxies ([bafbfd1](https://github.com/Pay-i/pay-i-python/commit/bafbfd154aba87811edb87bf375d8d9242b6a14e))
* **tests:** run tests in parallel ([6bdbcdd](https://github.com/Pay-i/pay-i-python/commit/6bdbcddb8a4465cc79fee2e0ba66168079a24490))


### Documentation

* **client:** fix httpx.Timeout documentation reference ([60d1b01](https://github.com/Pay-i/pay-i-python/commit/60d1b01aae900736dfe0345aa8250b67fa1ba704))

## 0.1.0-alpha.89 (2025-06-17)

Full Changelog: [v0.1.0-alpha.88...v0.1.0-alpha.89](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.88...v0.1.0-alpha.89)

### Features

* request tags at [@track](https://github.com/track) and payi_instrument() scope ([#327](https://github.com/Pay-i/pay-i-python/issues/327)) ([4323d25](https://github.com/Pay-i/pay-i-python/commit/4323d25f50694e6daa97b0933fd97ae1da940284))

## 0.1.0-alpha.88 (2025-06-16)

Full Changelog: [v0.1.0-alpha.87...v0.1.0-alpha.88](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.87...v0.1.0-alpha.88)

### Features

* remove experiencfes helpers ([7e755be](https://github.com/Pay-i/pay-i-python/commit/7e755be837a44cf61fdf4498ab0fe83b9e4a9e1a))

## 0.1.0-alpha.87 (2025-06-16)

Full Changelog: [v0.1.0-alpha.86...v0.1.0-alpha.87](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.86...v0.1.0-alpha.87)

### Features

* capture function calling ([#324](https://github.com/Pay-i/pay-i-python/issues/324)) ([5e89cb8](https://github.com/Pay-i/pay-i-python/commit/5e89cb8f8526cd8c9053683e40a9d6c9a1773742))

## 0.1.0-alpha.86 (2025-06-13)

Full Changelog: [v0.1.0-alpha.85...v0.1.0-alpha.86](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.85...v0.1.0-alpha.86)

### Bug Fixes

* anthopic logging ([#322](https://github.com/Pay-i/pay-i-python/issues/322)) ([1af515b](https://github.com/Pay-i/pay-i-python/commit/1af515b9603058cf23b75e477fbb67e7acd405ad))

## 0.1.0-alpha.85 (2025-06-12)

Full Changelog: [v0.1.0-alpha.84...v0.1.0-alpha.85](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.84...v0.1.0-alpha.85)

### Features

* AnthropicBedrock ([#320](https://github.com/Pay-i/pay-i-python/issues/320)) ([33b42e3](https://github.com/Pay-i/pay-i-python/commit/33b42e38d7ba3245e0633254b4401cf991937933))

## 0.1.0-alpha.84 (2025-06-09)

Full Changelog: [v0.1.0-alpha.83...v0.1.0-alpha.84](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.83...v0.1.0-alpha.84)

### Features

* **api:** manual updates ([b5edce3](https://github.com/Pay-i/pay-i-python/commit/b5edce3207c9cd01ded791e67b8cc0bbf5ef4ef4))
* consolidate anthropic vision, google.genai and vertex compute usage ([#318](https://github.com/Pay-i/pay-i-python/issues/318)) ([28700fd](https://github.com/Pay-i/pay-i-python/commit/28700fd25e76b03e06f9cb7c963890dbb1675f2b))

## 0.1.0-alpha.83 (2025-06-06)

Full Changelog: [v0.1.0-alpha.82...v0.1.0-alpha.83](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.82...v0.1.0-alpha.83)

### Features

* ingest streaming results aggressively ([#316](https://github.com/Pay-i/pay-i-python/issues/316)) ([2d196f7](https://github.com/Pay-i/pay-i-python/commit/2d196f781c7d4ed1317f453e99501d682f684d3c))

## 0.1.0-alpha.82 (2025-06-06)

Full Changelog: [v0.1.0-alpha.81...v0.1.0-alpha.82](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.81...v0.1.0-alpha.82)

### Bug Fixes

* vertex, google.genai report tokens when details missing ([#314](https://github.com/Pay-i/pay-i-python/issues/314)) ([54dd25b](https://github.com/Pay-i/pay-i-python/commit/54dd25b1abd93e6fdec22dd7bb8dae39236ee532))

## 0.1.0-alpha.81 (2025-06-06)

Full Changelog: [v0.1.0-alpha.80...v0.1.0-alpha.81](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.80...v0.1.0-alpha.81)

### Features

* logger support ([#312](https://github.com/Pay-i/pay-i-python/issues/312)) ([f353bb2](https://github.com/Pay-i/pay-i-python/commit/f353bb2cbc24d28114c3bd770a8243f8b115d1fc))

## 0.1.0-alpha.80 (2025-06-04)

Full Changelog: [v0.1.0-alpha.79...v0.1.0-alpha.80](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.79...v0.1.0-alpha.80)

### Bug Fixes

* tiktoken fallback failure ([#310](https://github.com/Pay-i/pay-i-python/issues/310)) ([76f6a31](https://github.com/Pay-i/pay-i-python/commit/76f6a318f514da2dc5b4e9fbe7927cc6f28a7b27))

## 0.1.0-alpha.79 (2025-06-04)

Full Changelog: [v0.1.0-alpha.78...v0.1.0-alpha.79](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.78...v0.1.0-alpha.79)

### Features

* optional response_id for vertexai, google.genai sync response ([#308](https://github.com/Pay-i/pay-i-python/issues/308)) ([a3d1207](https://github.com/Pay-i/pay-i-python/commit/a3d1207f26db9b40d849bfb8402d4e8142845c3c))

## 0.1.0-alpha.78 (2025-06-03)

Full Changelog: [v0.1.0-alpha.77...v0.1.0-alpha.78](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.77...v0.1.0-alpha.78)

### Features

* **api:** google genai, anthropic stream() ([#306](https://github.com/Pay-i/pay-i-python/issues/306)) ([341da40](https://github.com/Pay-i/pay-i-python/commit/341da40fb228cb83994bec12e7cda457f5452692))

## 0.1.0-alpha.77 (2025-06-03)

Full Changelog: [v0.1.0-alpha.76...v0.1.0-alpha.77](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.76...v0.1.0-alpha.77)

### Features

* **client:** add follow_redirects request option ([3308085](https://github.com/Pay-i/pay-i-python/commit/3308085121c320d80931d6749f36ecee049be669))


### Chores

* **docs:** remove reference to rye shell ([eb25599](https://github.com/Pay-i/pay-i-python/commit/eb255999808df39a9eaaf5b91825c8fe150dbf55))
* **docs:** remove unnecessary param examples ([4d34a34](https://github.com/Pay-i/pay-i-python/commit/4d34a343cd19fc091fb836d411034d9ad62bf564))

## 0.1.0-alpha.76 (2025-05-31)

Full Changelog: [v0.1.0-alpha.75...v0.1.0-alpha.76](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.75...v0.1.0-alpha.76)

## 0.1.0-alpha.75 (2025-05-22)

Full Changelog: [v0.1.0-alpha.74...v0.1.0-alpha.75](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.74...v0.1.0-alpha.75)

### Chores

* **docs:** grammar improvements ([6d91c51](https://github.com/Pay-i/pay-i-python/commit/6d91c51bb84c757cb4354af73fac662290c7362b))
* **internal:** codegen related update ([25ac129](https://github.com/Pay-i/pay-i-python/commit/25ac1298decbbca8f4d1749fa6113faea8dc3b50))

## 0.1.0-alpha.74 (2025-05-16)

Full Changelog: [v0.1.0-alpha.73...v0.1.0-alpha.74](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.73...v0.1.0-alpha.74)

### Chores

* **ci:** fix installation instructions ([f63b318](https://github.com/Pay-i/pay-i-python/commit/f63b318339983ef6f0f90a452728efc1baab2693))
* **ci:** upload sdks to package manager ([3340716](https://github.com/Pay-i/pay-i-python/commit/334071651b6096ab7724fbfd4004fe636747e984))

## 0.1.0-alpha.73 (2025-05-13)

Full Changelog: [v0.1.0-alpha.72...v0.1.0-alpha.73](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.72...v0.1.0-alpha.73)

### Features

* Anthropic Vertex, OpenAi Responses ([#297](https://github.com/Pay-i/pay-i-python/issues/297)) ([535163f](https://github.com/Pay-i/pay-i-python/commit/535163f1d29f39838a16dc87a4ef40542b5d93b0))

## 0.1.0-alpha.72 (2025-05-10)

Full Changelog: [v0.1.0-alpha.71...v0.1.0-alpha.72](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.71...v0.1.0-alpha.72)

### Bug Fixes

* **package:** support direct resource imports ([314f86c](https://github.com/Pay-i/pay-i-python/commit/314f86cb0d46aa35628c9d059c1b1ca25d24d911))


### Chores

* **internal:** avoid errors for isinstance checks on proxies ([b935f82](https://github.com/Pay-i/pay-i-python/commit/b935f82c9de01353ec83b9c12c4ed6749e984c7d))

## 0.1.0-alpha.71 (2025-05-03)

Full Changelog: [v0.1.0-alpha.70...v0.1.0-alpha.71](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.70...v0.1.0-alpha.71)

### Features

* **api:** google vertex ([#294](https://github.com/Pay-i/pay-i-python/issues/294)) ([6d9e39b](https://github.com/Pay-i/pay-i-python/commit/6d9e39b2ee522589d4962c73f697f9cce76fdf6a))
* **api:** manual updates ([7d11112](https://github.com/Pay-i/pay-i-python/commit/7d1111205f30fe78c9e2e833d3f99a62f95419e8))


### Bug Fixes

* lint ([e7d5a21](https://github.com/Pay-i/pay-i-python/commit/e7d5a210db38448629511b470a4d1b426368577f))

## 0.1.0-alpha.70 (2025-04-24)

Full Changelog: [v0.1.0-alpha.69...v0.1.0-alpha.70](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.69...v0.1.0-alpha.70)

### Chores

* broadly detect json family of content-type headers ([e98221d](https://github.com/Pay-i/pay-i-python/commit/e98221da505ddf7a855f661f5a8d49475616e3e3))
* **ci:** only use depot for staging repos ([e651bba](https://github.com/Pay-i/pay-i-python/commit/e651bbad809c53a59452b0fc05f73654e343a727))
* **internal:** codegen related update ([f71eb19](https://github.com/Pay-i/pay-i-python/commit/f71eb19111268d02d07a4db3a1be1da7a8b9ea18))
* **internal:** minor formatting changes ([bfca4fe](https://github.com/Pay-i/pay-i-python/commit/bfca4fe4c63eb2ca6fea5858744327fee9226866))

## 0.1.0-alpha.69 (2025-04-23)

Full Changelog: [v0.1.0-alpha.68...v0.1.0-alpha.69](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.68...v0.1.0-alpha.69)

### Features

* feat: [@track](https://github.com/track), track_context(), automatic use case ([#292](https://github.com/Pay-i/pay-i-python/issues/292)) ([d2b4593](https://github.com/Pay-i/pay-i-python/commit/d2b4593ed30117d8a0fd72f538eb054b2cc5eb98))


### Bug Fixes

* **pydantic v1:** more robust ModelField.annotation check ([7d38125](https://github.com/Pay-i/pay-i-python/commit/7d3812544db66083c00b5160096340ffba42be3d))


### Chores

* **ci:** add timeout thresholds for CI jobs ([b2d095d](https://github.com/Pay-i/pay-i-python/commit/b2d095dd2d4f8275e1bbc8bead56d58ce42c4768))
* **internal:** fix list file params ([15e3e8a](https://github.com/Pay-i/pay-i-python/commit/15e3e8a4bc380ce3ea72fce7e53f766079548d21))
* **internal:** import reformatting ([cf0ee48](https://github.com/Pay-i/pay-i-python/commit/cf0ee483640172d25c7d5a284d1667a54451fad3))
* **internal:** refactor retries to not use recursion ([907871a](https://github.com/Pay-i/pay-i-python/commit/907871a66ca41281bcfc1b2b7c14ffcabcc03525))
* **internal:** update models test ([b400b74](https://github.com/Pay-i/pay-i-python/commit/b400b74a7f1b372f30170d9ff082b30d42b6880a))

## 0.1.0-alpha.68 (2025-04-17)

Full Changelog: [v0.1.0-alpha.67...v0.1.0-alpha.68](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.67...v0.1.0-alpha.68)

### Bug Fixes

* **perf:** optimize some hot paths ([6645b5f](https://github.com/Pay-i/pay-i-python/commit/6645b5f63da0001cb72da48c7334955fc0f3eb92))
* **perf:** skip traversing types for NotGiven values ([6ec70e7](https://github.com/Pay-i/pay-i-python/commit/6ec70e705495c4cebbabc423158e7bcab469c07e))


### Chores

* **client:** minor internal fixes ([f453479](https://github.com/Pay-i/pay-i-python/commit/f453479d5e5eb837fb5222f86aed85a4aeb476ba))
* **internal:** base client updates ([2464002](https://github.com/Pay-i/pay-i-python/commit/2464002241968d08518cfdbd8368a7ca07c2a06f))
* **internal:** bump pyright version ([7ac7381](https://github.com/Pay-i/pay-i-python/commit/7ac7381dbd447f2936c02a80f88caf9cd933af16))
* **internal:** expand CI branch coverage ([eba83f0](https://github.com/Pay-i/pay-i-python/commit/eba83f005cd28c49d0f354be57d55b5455506a99))
* **internal:** reduce CI branch coverage ([119ee53](https://github.com/Pay-i/pay-i-python/commit/119ee5362d995977412b791f6c7b0b3007e1d9ab))
* **internal:** update pyright settings ([1bf3b42](https://github.com/Pay-i/pay-i-python/commit/1bf3b42fb7956cec7db654b5065df438cd8c047f))

## 0.1.0-alpha.67 (2025-04-10)

Full Changelog: [v0.1.0-alpha.66...v0.1.0-alpha.67](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.66...v0.1.0-alpha.67)

### Chores

* **internal:** expand CI branch coverage ([59b85dd](https://github.com/Pay-i/pay-i-python/commit/59b85dd730b834ba2aeab0b3b40bcd01fdfb04d2))
* **internal:** reduce CI branch coverage ([a24f3a3](https://github.com/Pay-i/pay-i-python/commit/a24f3a3f600f91e798976bc4a3c79341ed84a3e3))

## 0.1.0-alpha.66 (2025-04-10)

Full Changelog: [v0.1.0-alpha.65...v0.1.0-alpha.66](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.65...v0.1.0-alpha.66)

### Features

* feat: log inference call timestamp ([e58f9ac](https://github.com/Pay-i/pay-i-python/commit/e58f9ac4866fe6f1244c917eec050721ad220930))


### Chores

* **internal:** expand CI branch coverage ([f2c43ed](https://github.com/Pay-i/pay-i-python/commit/f2c43edd3033fea6976f2385dd621986b0015b7c))
* **internal:** reduce CI branch coverage ([f2e1fa8](https://github.com/Pay-i/pay-i-python/commit/f2e1fa82c4a62c9da75061c573a599b42854dd88))

## 0.1.0-alpha.65 (2025-04-10)

Full Changelog: [v0.1.0-alpha.64...v0.1.0-alpha.65](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.64...v0.1.0-alpha.65)

### Features

* feat: simplify OpenAI streaming setup ([7b50eb2](https://github.com/Pay-i/pay-i-python/commit/7b50eb276c6bb464cb94d6551e342e32b0b76181))

## 0.1.0-alpha.64 (2025-04-09)

Full Changelog: [v0.1.0-alpha.63...v0.1.0-alpha.64](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.63...v0.1.0-alpha.64)

### Chores

* **internal:** slight transform perf improvement ([#283](https://github.com/Pay-i/pay-i-python/issues/283)) ([4b3f9e6](https://github.com/Pay-i/pay-i-python/commit/4b3f9e60fbecf99f8ddffed5903f916f3d5445c5))

## 0.1.0-alpha.63 (2025-04-08)

Full Changelog: [v0.1.0-alpha.62...v0.1.0-alpha.63](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.62...v0.1.0-alpha.63)

### Features

* feat: simplify global instrumentation init ([a3f7f4f](https://github.com/Pay-i/pay-i-python/commit/a3f7f4f22eacb694b648a2da935fd9412c40740e))

## 0.1.0-alpha.62 (2025-04-07)

Full Changelog: [v0.1.0-alpha.61...v0.1.0-alpha.62](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.61...v0.1.0-alpha.62)

### Features

* feat: auto generate use case id ([b50f807](https://github.com/Pay-i/pay-i-python/commit/b50f807b571c917d39f37a1879bf2ea7e7f5d29d))

## 0.1.0-alpha.61 (2025-04-07)

Full Changelog: [v0.1.0-alpha.60...v0.1.0-alpha.61](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.60...v0.1.0-alpha.61)

### Features

* feat(api): global instrumentation ([6977d0c](https://github.com/Pay-i/pay-i-python/commit/6977d0c78ffaa12bb43a439827b0fba08b258e55))

## 0.1.0-alpha.60 (2025-04-07)

Full Changelog: [v0.1.0-alpha.59...v0.1.0-alpha.60](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.59...v0.1.0-alpha.60)

### Features

* **api:** KPIs ([#274](https://github.com/Pay-i/pay-i-python/issues/274)) ([1e6d054](https://github.com/Pay-i/pay-i-python/commit/1e6d0540471a07ac43fe9d32c5b30c1b153e5b70))

## 0.1.0-alpha.59 (2025-04-04)

Full Changelog: [v0.1.0-alpha.58...v0.1.0-alpha.59](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.58...v0.1.0-alpha.59)

### Chores

* **internal:** remove trailing character ([#271](https://github.com/Pay-i/pay-i-python/issues/271)) ([ea4292f](https://github.com/Pay-i/pay-i-python/commit/ea4292f2513b35ac475d494351fe77e7db2c9f57))

## 0.1.0-alpha.58 (2025-03-27)

Full Changelog: [v0.1.0-alpha.57...v0.1.0-alpha.58](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.57...v0.1.0-alpha.58)

### Features

* **api:** manual updates ([#268](https://github.com/Pay-i/pay-i-python/issues/268)) ([caf2531](https://github.com/Pay-i/pay-i-python/commit/caf253148da38fdd21cbd85d6ec20bcb3f753dea))

## 0.1.0-alpha.57 (2025-03-27)

Full Changelog: [v0.1.0-alpha.56...v0.1.0-alpha.57](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.56...v0.1.0-alpha.57)

### Chores

* fix typos ([#265](https://github.com/Pay-i/pay-i-python/issues/265)) ([bd0ede4](https://github.com/Pay-i/pay-i-python/commit/bd0ede47518e6b667f9f856b38736c1670b2ceeb))

## 0.1.0-alpha.56 (2025-03-26)

Full Changelog: [v0.1.0-alpha.55...v0.1.0-alpha.56](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.55...v0.1.0-alpha.56)

### Features

* **api:** manual updates ([#261](https://github.com/Pay-i/pay-i-python/issues/261)) ([39d2166](https://github.com/Pay-i/pay-i-python/commit/39d21668bb6545d29897755a8a17ec7517a0989c))

## 0.1.0-alpha.55 (2025-03-19)

Full Changelog: [v0.1.0-alpha.54...v0.1.0-alpha.55](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.54...v0.1.0-alpha.55)

### Bug Fixes

* **ci:** remove publishing patch ([#257](https://github.com/Pay-i/pay-i-python/issues/257)) ([0c5bfb4](https://github.com/Pay-i/pay-i-python/commit/0c5bfb4725777b366fb50199209f4e8a50711ad9))

## 0.1.0-alpha.54 (2025-03-17)

Full Changelog: [v0.1.0-alpha.53...v0.1.0-alpha.54](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.53...v0.1.0-alpha.54)

### Bug Fixes

* **ci:** ensure pip is always available ([#256](https://github.com/Pay-i/pay-i-python/issues/256)) ([13c3e2c](https://github.com/Pay-i/pay-i-python/commit/13c3e2c3c83f97bc0add1a7e670113e609e3c5d1))
* **types:** handle more discriminated union shapes ([#255](https://github.com/Pay-i/pay-i-python/issues/255)) ([be986f1](https://github.com/Pay-i/pay-i-python/commit/be986f12ea82af0a7a51e7b08803758381050086))


### Chores

* **internal:** bump rye to 0.44.0 ([#254](https://github.com/Pay-i/pay-i-python/issues/254)) ([789c413](https://github.com/Pay-i/pay-i-python/commit/789c413b306c96905507c1b4de8c835cc484b2b8))
* **internal:** remove extra empty newlines ([#252](https://github.com/Pay-i/pay-i-python/issues/252)) ([8b33100](https://github.com/Pay-i/pay-i-python/commit/8b33100d0fee1693e3adc9fc6c652bd4150a2642))
* **internal:** remove unused http client options forwarding ([#248](https://github.com/Pay-i/pay-i-python/issues/248)) ([5f7bf7b](https://github.com/Pay-i/pay-i-python/commit/5f7bf7b9d3745fd3d63c49502bbc9b63ff8cd333))


### Documentation

* revise readme docs about nested params ([#250](https://github.com/Pay-i/pay-i-python/issues/250)) ([19c655d](https://github.com/Pay-i/pay-i-python/commit/19c655d13bbe82916c599a5b9f8292057f7b4b0e))

## 0.1.0-alpha.53 (2025-03-01)

Full Changelog: [v0.1.0-alpha.52...v0.1.0-alpha.53](https://github.com/pay-i/pay-i-python/compare/v0.1.0-alpha.52...v0.1.0-alpha.53)

### Features

* **api:** add Evaluations ([#114](https://github.com/pay-i/pay-i-python/issues/114)) ([9a4a952](https://github.com/pay-i/pay-i-python/commit/9a4a952e5ff57dd869d1bfb35203400eb9e39d38))
* **api:** api update ([#121](https://github.com/pay-i/pay-i-python/issues/121)) ([4bba6ed](https://github.com/pay-i/pay-i-python/commit/4bba6ed2a6ed1f3b1244e6c78b63d5b3b6e1b527))
* **api:** api update ([#124](https://github.com/pay-i/pay-i-python/issues/124)) ([6024da4](https://github.com/pay-i/pay-i-python/commit/6024da433b9a7632a34b6566a895d0888d6550ea))
* **api:** api update ([#125](https://github.com/pay-i/pay-i-python/issues/125)) ([3ed2431](https://github.com/pay-i/pay-i-python/commit/3ed24317882624c96d3dceba89c4a2b91109bc05))
* **api:** api update ([#127](https://github.com/pay-i/pay-i-python/issues/127)) ([f9f8665](https://github.com/pay-i/pay-i-python/commit/f9f8665278eec1f3b4d081076047460004230a97))
* **api:** azure openai ([#215](https://github.com/pay-i/pay-i-python/issues/215)) ([fb85b22](https://github.com/pay-i/pay-i-python/commit/fb85b22a598b5b7d3b98b60f788436af031a56dc))
* **api:** manual updates ([#118](https://github.com/pay-i/pay-i-python/issues/118)) ([cf70992](https://github.com/pay-i/pay-i-python/commit/cf70992e8971e555802517035eba64acef38e00e))
* **api:** update via SDK Studio ([ba34638](https://github.com/pay-i/pay-i-python/commit/ba3463802b7366b450058f6ccdb13419b3bdbfe1))
* **api:** update via SDK Studio ([d627f6a](https://github.com/pay-i/pay-i-python/commit/d627f6a3394dc096463d6228272a8a81c4c1d4b4))
* **api:** update via SDK Studio ([d87c30c](https://github.com/pay-i/pay-i-python/commit/d87c30c4d5c3d7dee3a4b96596c8df9e319ca690))
* **api:** update via SDK Studio ([ea31540](https://github.com/pay-i/pay-i-python/commit/ea315409811b1b3541c93852e22a4dd5f71be7e7))
* **api:** update via SDK Studio ([96d12c3](https://github.com/pay-i/pay-i-python/commit/96d12c3c114642a13469ece184eaec8feee50b1a))
* **api:** update via SDK Studio ([4b2a9a7](https://github.com/pay-i/pay-i-python/commit/4b2a9a7dd2652b6f894a6409f1d2fe9fb3baeeb2))
* **api:** update via SDK Studio ([ba169b1](https://github.com/pay-i/pay-i-python/commit/ba169b1e70894cb2a2f0497e4781121a334716cd))
* **api:** update via SDK Studio ([4705b16](https://github.com/pay-i/pay-i-python/commit/4705b16b08f5e1ea678c4c36385ca5f1a7f2f42b))
* **api:** update via SDK Studio ([#100](https://github.com/pay-i/pay-i-python/issues/100)) ([9e0f07b](https://github.com/pay-i/pay-i-python/commit/9e0f07bec54cbefc0fb45bf81cdee8d812363d81))
* **api:** update via SDK Studio ([#100](https://github.com/pay-i/pay-i-python/issues/100)) ([923fee3](https://github.com/pay-i/pay-i-python/commit/923fee31f30f15341eb78739e745f62d8961ee53))
* **api:** update via SDK Studio ([#103](https://github.com/pay-i/pay-i-python/issues/103)) ([0087070](https://github.com/pay-i/pay-i-python/commit/0087070a5a3b51c14d396cafef7c7bb0eda034aa))
* **api:** update via SDK Studio ([#103](https://github.com/pay-i/pay-i-python/issues/103)) ([48d8eb1](https://github.com/pay-i/pay-i-python/commit/48d8eb1c02216e9d170c219225d2f3374afbaa8e))
* **api:** update via SDK Studio ([#109](https://github.com/pay-i/pay-i-python/issues/109)) ([0f9abb8](https://github.com/pay-i/pay-i-python/commit/0f9abb871884c83310bcb05dd9485b7a285fcfb3))
* **api:** update via SDK Studio ([#111](https://github.com/pay-i/pay-i-python/issues/111)) ([c5ab397](https://github.com/pay-i/pay-i-python/commit/c5ab3978fc2285d274a7d4053d46a9b7fbaeec6f))
* **api:** update via SDK Studio ([#13](https://github.com/pay-i/pay-i-python/issues/13)) ([c35a02e](https://github.com/pay-i/pay-i-python/commit/c35a02e163c67c320566bc77fb24bb6cdd8b4bf6))
* **api:** update via SDK Studio ([#13](https://github.com/pay-i/pay-i-python/issues/13)) ([0728463](https://github.com/pay-i/pay-i-python/commit/0728463f05f5a34803774a377c3bc30c19055bc3))
* **api:** update via SDK Studio ([#21](https://github.com/pay-i/pay-i-python/issues/21)) ([daa4259](https://github.com/pay-i/pay-i-python/commit/daa4259dc2156dd84843d3264362a6a53ee842c4))
* **api:** update via SDK Studio ([#21](https://github.com/pay-i/pay-i-python/issues/21)) ([544adf9](https://github.com/pay-i/pay-i-python/commit/544adf927f8c2418355a839976f87e77668a6c28))
* **api:** update via SDK Studio ([#23](https://github.com/pay-i/pay-i-python/issues/23)) ([5c2aa35](https://github.com/pay-i/pay-i-python/commit/5c2aa35b45c18fb194b4055884d3abded49aad1e))
* **api:** update via SDK Studio ([#23](https://github.com/pay-i/pay-i-python/issues/23)) ([9f4fe9d](https://github.com/pay-i/pay-i-python/commit/9f4fe9d46059757afe180fbb92046b11433439b8))
* **api:** update via SDK Studio ([#25](https://github.com/pay-i/pay-i-python/issues/25)) ([9712710](https://github.com/pay-i/pay-i-python/commit/9712710b0ab67462295a3f7531e3b034a91dc094))
* **api:** update via SDK Studio ([#25](https://github.com/pay-i/pay-i-python/issues/25)) ([18b8e3f](https://github.com/pay-i/pay-i-python/commit/18b8e3f19bcca7bdde1a01d6cd1c4a50c7d6ec7e))
* **api:** update via SDK Studio ([#26](https://github.com/pay-i/pay-i-python/issues/26)) ([eebd44e](https://github.com/pay-i/pay-i-python/commit/eebd44e55d800da8cf7b9a01108e78a3446d1283))
* **api:** update via SDK Studio ([#26](https://github.com/pay-i/pay-i-python/issues/26)) ([1fdcbf7](https://github.com/pay-i/pay-i-python/commit/1fdcbf764fdcdd5ab37fc1ba772d6c263e7aafd9))
* **api:** update via SDK Studio ([#28](https://github.com/pay-i/pay-i-python/issues/28)) ([972e5e3](https://github.com/pay-i/pay-i-python/commit/972e5e3b8c84df6d3b47ba2dba4137151d9e414c))
* **api:** update via SDK Studio ([#28](https://github.com/pay-i/pay-i-python/issues/28)) ([6809f97](https://github.com/pay-i/pay-i-python/commit/6809f9771faec4ee541dda53854871c8ff1b41db))
* **api:** update via SDK Studio ([#30](https://github.com/pay-i/pay-i-python/issues/30)) ([3334f89](https://github.com/pay-i/pay-i-python/commit/3334f89029ba31d70aa759d367be32888a77b603))
* **api:** update via SDK Studio ([#30](https://github.com/pay-i/pay-i-python/issues/30)) ([3e3bbf2](https://github.com/pay-i/pay-i-python/commit/3e3bbf2eac46d39465dbd13768f218ff7b7a3ba9))
* **api:** update via SDK Studio ([#34](https://github.com/pay-i/pay-i-python/issues/34)) ([f05bc0e](https://github.com/pay-i/pay-i-python/commit/f05bc0ee6357f32724b3199ea92aa8f5c17723e1))
* **api:** update via SDK Studio ([#34](https://github.com/pay-i/pay-i-python/issues/34)) ([f40cf18](https://github.com/pay-i/pay-i-python/commit/f40cf18b24fa5ea12eba307fb101c02b626814d3))
* **api:** update via SDK Studio ([#37](https://github.com/pay-i/pay-i-python/issues/37)) ([b794015](https://github.com/pay-i/pay-i-python/commit/b7940155a65297fda08c4022417a2d78ced5ee3f))
* **api:** update via SDK Studio ([#37](https://github.com/pay-i/pay-i-python/issues/37)) ([123f681](https://github.com/pay-i/pay-i-python/commit/123f681c2a77810f4cbbe208cdb38e6c77138113))
* **api:** update via SDK Studio ([#39](https://github.com/pay-i/pay-i-python/issues/39)) ([924942e](https://github.com/pay-i/pay-i-python/commit/924942ed83577f9d6d6bc9709d22e5423a2c50b4))
* **api:** update via SDK Studio ([#39](https://github.com/pay-i/pay-i-python/issues/39)) ([1eae9e4](https://github.com/pay-i/pay-i-python/commit/1eae9e45e1568de115db588000310cf1f531a324))
* **api:** update via SDK Studio ([#4](https://github.com/pay-i/pay-i-python/issues/4)) ([08bb37c](https://github.com/pay-i/pay-i-python/commit/08bb37c7ab580b1c0d6adf12f3745191e9023455))
* **api:** update via SDK Studio ([#4](https://github.com/pay-i/pay-i-python/issues/4)) ([20a797a](https://github.com/pay-i/pay-i-python/commit/20a797a8b7f901d95b04db96976752d1804ce8c0))
* **api:** update via SDK Studio ([#41](https://github.com/pay-i/pay-i-python/issues/41)) ([5fb515c](https://github.com/pay-i/pay-i-python/commit/5fb515c9399354230bda965857e2dfa090db83b7))
* **api:** update via SDK Studio ([#41](https://github.com/pay-i/pay-i-python/issues/41)) ([1985ab9](https://github.com/pay-i/pay-i-python/commit/1985ab99496621510dfcfd8395acd572ebede0bf))
* **api:** update via SDK Studio ([#42](https://github.com/pay-i/pay-i-python/issues/42)) ([acfca49](https://github.com/pay-i/pay-i-python/commit/acfca49e245ef237ca1459f3e80c77e883a7fa4a))
* **api:** update via SDK Studio ([#42](https://github.com/pay-i/pay-i-python/issues/42)) ([b1cfc00](https://github.com/pay-i/pay-i-python/commit/b1cfc00450982df67ad628df833666e47c9cb922))
* **api:** update via SDK Studio ([#44](https://github.com/pay-i/pay-i-python/issues/44)) ([8623402](https://github.com/pay-i/pay-i-python/commit/86234024530b7a6b26508c65aad280a3a0fc33c3))
* **api:** update via SDK Studio ([#44](https://github.com/pay-i/pay-i-python/issues/44)) ([4d66c91](https://github.com/pay-i/pay-i-python/commit/4d66c91473c5cf39a0e1fcaf192a7e9239e7551a))
* **api:** update via SDK Studio ([#45](https://github.com/pay-i/pay-i-python/issues/45)) ([8129c56](https://github.com/pay-i/pay-i-python/commit/8129c56fe00cc676e56e8318533b98be3234cf8f))
* **api:** update via SDK Studio ([#45](https://github.com/pay-i/pay-i-python/issues/45)) ([120e341](https://github.com/pay-i/pay-i-python/commit/120e341ab6b296ca13ed387b6895da49a1076620))
* **api:** update via SDK Studio ([#48](https://github.com/pay-i/pay-i-python/issues/48)) ([5b67542](https://github.com/pay-i/pay-i-python/commit/5b6754279d6b6dcb3b65bda1bf59b0d0092b4bec))
* **api:** update via SDK Studio ([#48](https://github.com/pay-i/pay-i-python/issues/48)) ([aa5c97a](https://github.com/pay-i/pay-i-python/commit/aa5c97a956fb46f8862706923da7b39415f4e578))
* **api:** update via SDK Studio ([#50](https://github.com/pay-i/pay-i-python/issues/50)) ([91c7d2c](https://github.com/pay-i/pay-i-python/commit/91c7d2c29430835dfee501520d8b247755e1679d))
* **api:** update via SDK Studio ([#50](https://github.com/pay-i/pay-i-python/issues/50)) ([84867e5](https://github.com/pay-i/pay-i-python/commit/84867e5209e8d03cef6793fd6d1c54818bb67314))
* **api:** update via SDK Studio ([#57](https://github.com/pay-i/pay-i-python/issues/57)) ([8d6ce22](https://github.com/pay-i/pay-i-python/commit/8d6ce2229764aeaac2b0229cb70266545759cc7d))
* **api:** update via SDK Studio ([#57](https://github.com/pay-i/pay-i-python/issues/57)) ([d074560](https://github.com/pay-i/pay-i-python/commit/d074560cf02cbdef5e06e3e2163d2d48e4d2286e))
* **api:** update via SDK Studio ([#58](https://github.com/pay-i/pay-i-python/issues/58)) ([013389a](https://github.com/pay-i/pay-i-python/commit/013389a52fc87312e7173c34c3f27256e52b7ed5))
* **api:** update via SDK Studio ([#58](https://github.com/pay-i/pay-i-python/issues/58)) ([4d42f05](https://github.com/pay-i/pay-i-python/commit/4d42f05de13c9f91b0c0805b9d279b3da38aa3d4))
* **api:** update via SDK Studio ([#59](https://github.com/pay-i/pay-i-python/issues/59)) ([9f895e6](https://github.com/pay-i/pay-i-python/commit/9f895e649a06a9000b1da8ab4a0b2fb779b09db9))
* **api:** update via SDK Studio ([#59](https://github.com/pay-i/pay-i-python/issues/59)) ([04195a2](https://github.com/pay-i/pay-i-python/commit/04195a2776d85d1904b56771fafb7463a930a6ca))
* **api:** update via SDK Studio ([#63](https://github.com/pay-i/pay-i-python/issues/63)) ([a38f132](https://github.com/pay-i/pay-i-python/commit/a38f132cdbbbcac2c235c71cd758c38631b12a57))
* **api:** update via SDK Studio ([#63](https://github.com/pay-i/pay-i-python/issues/63)) ([1c0b056](https://github.com/pay-i/pay-i-python/commit/1c0b056f561228c80f27003206f834075e0d096c))
* **api:** update via SDK Studio ([#65](https://github.com/pay-i/pay-i-python/issues/65)) ([d32f303](https://github.com/pay-i/pay-i-python/commit/d32f3032d3cb5854617e65e9766447d8ea08f41c))
* **api:** update via SDK Studio ([#65](https://github.com/pay-i/pay-i-python/issues/65)) ([1b2a13c](https://github.com/pay-i/pay-i-python/commit/1b2a13ce216a7f63f13f921df2114e0218fe9d3a))
* **api:** update via SDK Studio ([#66](https://github.com/pay-i/pay-i-python/issues/66)) ([990a0cb](https://github.com/pay-i/pay-i-python/commit/990a0cbcfb381f6f72530d869a7beaae6f9fed2d))
* **api:** update via SDK Studio ([#66](https://github.com/pay-i/pay-i-python/issues/66)) ([fc7bbf2](https://github.com/pay-i/pay-i-python/commit/fc7bbf2b6314cffa670bd869b5d5395bbc053021))
* **api:** update via SDK Studio ([#67](https://github.com/pay-i/pay-i-python/issues/67)) ([b720656](https://github.com/pay-i/pay-i-python/commit/b72065621d50902959a484a5fe4c05051a5e2caa))
* **api:** update via SDK Studio ([#67](https://github.com/pay-i/pay-i-python/issues/67)) ([a8a76c2](https://github.com/pay-i/pay-i-python/commit/a8a76c2e6c3e377085c6bc73c46518885abd7ea6))
* **api:** update via SDK Studio ([#79](https://github.com/pay-i/pay-i-python/issues/79)) ([b7a562e](https://github.com/pay-i/pay-i-python/commit/b7a562ed5f6051fd797ac76087ef095e8c73a8bc))
* **api:** update via SDK Studio ([#79](https://github.com/pay-i/pay-i-python/issues/79)) ([4b7fa83](https://github.com/pay-i/pay-i-python/commit/4b7fa83674ad3057430f63006b847d43fe09ccbd))
* **api:** update via SDK Studio ([#83](https://github.com/pay-i/pay-i-python/issues/83)) ([c78b273](https://github.com/pay-i/pay-i-python/commit/c78b273d807606abe94212e0092eff80895da96d))
* **api:** update via SDK Studio ([#83](https://github.com/pay-i/pay-i-python/issues/83)) ([5674b66](https://github.com/pay-i/pay-i-python/commit/5674b66b718995e019245f7814b49abaed0952d8))
* **api:** update via SDK Studio ([#86](https://github.com/pay-i/pay-i-python/issues/86)) ([ea1bc86](https://github.com/pay-i/pay-i-python/commit/ea1bc86c6a3671b49ba7394841b5534d7e8c0263))
* **api:** update via SDK Studio ([#86](https://github.com/pay-i/pay-i-python/issues/86)) ([a140791](https://github.com/pay-i/pay-i-python/commit/a140791293fbd15f1c57e2c4f298b3a43e41eb8d))
* **api:** update via SDK Studio ([#89](https://github.com/pay-i/pay-i-python/issues/89)) ([b031428](https://github.com/pay-i/pay-i-python/commit/b03142879e9d1798d08288578d078eab98e86353))
* **api:** update via SDK Studio ([#89](https://github.com/pay-i/pay-i-python/issues/89)) ([3f58f9c](https://github.com/pay-i/pay-i-python/commit/3f58f9cbcb3ab3f92020473e8125ba7162a25e8f))
* **api:** update via SDK Studio ([#94](https://github.com/pay-i/pay-i-python/issues/94)) ([d3cd372](https://github.com/pay-i/pay-i-python/commit/d3cd3729991f4d0a8882f28f7ad42ebff73866eb))
* **api:** update via SDK Studio ([#94](https://github.com/pay-i/pay-i-python/issues/94)) ([c7b9be6](https://github.com/pay-i/pay-i-python/commit/c7b9be6453a6008295272e2029a97f2efec80c08))
* change ingest bugdet_ids and request_tags from str -&gt; list[str] ([bb70818](https://github.com/pay-i/pay-i-python/commit/bb7081850e14648db2ad753a0aef461cdd7b1940))
* **client:** add `retry_count` to raw response class ([#71](https://github.com/pay-i/pay-i-python/issues/71)) ([88fdd1d](https://github.com/pay-i/pay-i-python/commit/88fdd1df022c74e173db8697659dfba937f73be7))
* **client:** add `retry_count` to raw response class ([#71](https://github.com/pay-i/pay-i-python/issues/71)) ([506c9b8](https://github.com/pay-i/pay-i-python/commit/506c9b8bbcebb06b152d1f387604076e93ad0ae5))
* **client:** allow passing `NotGiven` for body ([#241](https://github.com/pay-i/pay-i-python/issues/241)) ([aed3b1b](https://github.com/pay-i/pay-i-python/commit/aed3b1b662a84e12f9ada2016c624c2e8ca4e831))
* fix ([cffc96b](https://github.com/pay-i/pay-i-python/commit/cffc96b700565b99a9d1b171e7aa820a3a41fb0a))
* ingest support for resource scope ([17c7435](https://github.com/pay-i/pay-i-python/commit/17c74350cc89c685e705a3d98936058f45c9e357))
* OpenAI embeddings instrumentation ([c43026c](https://github.com/pay-i/pay-i-python/commit/c43026c72c78a60dddc4ba9c886ad03ec32cee0a))
* test rename of autogenerated parameter name ([53b0e7d](https://github.com/pay-i/pay-i-python/commit/53b0e7dd2f37573d9683c4aa0c3a86de6d0e3dea))
* update types and tests ([02af29a](https://github.com/pay-i/pay-i-python/commit/02af29aa209c434083c3ea335ccfc80450deda8c))


### Bug Fixes

* **api:** manual update ([#112](https://github.com/pay-i/pay-i-python/issues/112)) ([bbf745c](https://github.com/pay-i/pay-i-python/commit/bbf745cec5425e0220b410f9a56ea7cdae191935))
* **client:** correctly serialise array body params ([#77](https://github.com/pay-i/pay-i-python/issues/77)) ([e3770e4](https://github.com/pay-i/pay-i-python/commit/e3770e474a9279eb4f13cbd7d87480d4d6a5bc76))
* **client:** correctly serialise array body params ([#77](https://github.com/pay-i/pay-i-python/issues/77)) ([f3e11ea](https://github.com/pay-i/pay-i-python/commit/f3e11ea320736c5c6cc949bef6cfb2ba9c707f4c))
* **client:** mark some request bodies as optional ([aed3b1b](https://github.com/pay-i/pay-i-python/commit/aed3b1b662a84e12f9ada2016c624c2e8ca4e831))
* preserve kwargs ([c02f093](https://github.com/pay-i/pay-i-python/commit/c02f093f0a87d494a6d28e50f8845550002d5723))


### Chores

* **ci:** bump prism mock server version ([#91](https://github.com/pay-i/pay-i-python/issues/91)) ([6cd2937](https://github.com/pay-i/pay-i-python/commit/6cd29379f24f7a7d261ed6beea8e4833e01eacfd))
* **ci:** bump prism mock server version ([#91](https://github.com/pay-i/pay-i-python/issues/91)) ([32499c0](https://github.com/pay-i/pay-i-python/commit/32499c05903f3e21e23d03f787291602efbc3e5c))
* **ci:** limit release doctor target branches ([#54](https://github.com/pay-i/pay-i-python/issues/54)) ([926140e](https://github.com/pay-i/pay-i-python/commit/926140e37dacca0b1e4ae481ed6fb839a154ad88))
* **ci:** limit release doctor target branches ([#54](https://github.com/pay-i/pay-i-python/issues/54)) ([daeb25a](https://github.com/pay-i/pay-i-python/commit/daeb25a27db669eaf4f36446e9f11d77e570048b))
* **docs:** document how to do per-request http client customization ([#53](https://github.com/pay-i/pay-i-python/issues/53)) ([ea27182](https://github.com/pay-i/pay-i-python/commit/ea271822df7ba59dc1cafc88e610b800a162c991))
* **docs:** document how to do per-request http client customization ([#53](https://github.com/pay-i/pay-i-python/issues/53)) ([d7f725f](https://github.com/pay-i/pay-i-python/commit/d7f725f8e025cab8cd799b8f2a5a35a0e31ab3d4))
* **docs:** update client docstring ([#245](https://github.com/pay-i/pay-i-python/issues/245)) ([91f6763](https://github.com/pay-i/pay-i-python/commit/91f6763d2d62f1acc61e1903f4efe52fd5c089e7))
* **examples:** minor formatting changes ([#98](https://github.com/pay-i/pay-i-python/issues/98)) ([7cd8cba](https://github.com/pay-i/pay-i-python/commit/7cd8cba158668bb057c8bd154a267a9410f721b2))
* **examples:** minor formatting changes ([#98](https://github.com/pay-i/pay-i-python/issues/98)) ([f6ca4d9](https://github.com/pay-i/pay-i-python/commit/f6ca4d98da4a0116e4ef34ce183192ef97e9c0d5))
* go live ([#2](https://github.com/pay-i/pay-i-python/issues/2)) ([81ba939](https://github.com/pay-i/pay-i-python/commit/81ba93934fc18d2ac642af4ce1a7772996cb5030))
* go live ([#2](https://github.com/pay-i/pay-i-python/issues/2)) ([3aa3d93](https://github.com/pay-i/pay-i-python/commit/3aa3d938deef0fc099c7855d460c3b8c2c8de921))
* **internal:** add type construction helper ([#60](https://github.com/pay-i/pay-i-python/issues/60)) ([65303cf](https://github.com/pay-i/pay-i-python/commit/65303cf704602ece488a31e8a608be100279a1bc))
* **internal:** add type construction helper ([#60](https://github.com/pay-i/pay-i-python/issues/60)) ([d3d7789](https://github.com/pay-i/pay-i-python/commit/d3d77890e331aecf9810144a270de2654db5f1de))
* **internal:** bump pyright ([#70](https://github.com/pay-i/pay-i-python/issues/70)) ([28a35f0](https://github.com/pay-i/pay-i-python/commit/28a35f0d6412c3fd2d0b0f696b5b723069ce7b98))
* **internal:** bump pyright ([#70](https://github.com/pay-i/pay-i-python/issues/70)) ([872a3f2](https://github.com/pay-i/pay-i-python/commit/872a3f2642f32a930c8472f597d64a2f3912f680))
* **internal:** bump ruff version ([#73](https://github.com/pay-i/pay-i-python/issues/73)) ([f487b64](https://github.com/pay-i/pay-i-python/commit/f487b6409b3d6ac4eb3378e0eace4f68fbd3342f))
* **internal:** bump ruff version ([#73](https://github.com/pay-i/pay-i-python/issues/73)) ([1eed80d](https://github.com/pay-i/pay-i-python/commit/1eed80d723cab7c94be6c49606e9fae4a5dbc124))
* **internal:** codegen related update ([#106](https://github.com/pay-i/pay-i-python/issues/106)) ([2d1f2f7](https://github.com/pay-i/pay-i-python/commit/2d1f2f7db30d05b63ed85b7fe41962c6bfda2a9e))
* **internal:** codegen related update ([#106](https://github.com/pay-i/pay-i-python/issues/106)) ([61152c1](https://github.com/pay-i/pay-i-python/commit/61152c14d52d64cfb9aa24934635a9825d0aa5ea))
* **internal:** codegen related update ([#115](https://github.com/pay-i/pay-i-python/issues/115)) ([24d0e16](https://github.com/pay-i/pay-i-python/commit/24d0e160609a46b4996cc3a1a5e6d56b64a70f0c))
* **internal:** codegen related update ([#119](https://github.com/pay-i/pay-i-python/issues/119)) ([e1e24a4](https://github.com/pay-i/pay-i-python/commit/e1e24a454ef05ea4b25cb5e7a710f48c87613fa8))
* **internal:** codegen related update ([#52](https://github.com/pay-i/pay-i-python/issues/52)) ([4a469a0](https://github.com/pay-i/pay-i-python/commit/4a469a0691431fe21ca111803ca6e256978cd21b))
* **internal:** codegen related update ([#52](https://github.com/pay-i/pay-i-python/issues/52)) ([889648d](https://github.com/pay-i/pay-i-python/commit/889648dcf15a5c2c7467cd3e83349c15d00b3dce))
* **internal:** ensure package is importable in lint cmd ([#92](https://github.com/pay-i/pay-i-python/issues/92)) ([5af85e5](https://github.com/pay-i/pay-i-python/commit/5af85e57dac94be4da96b45b406e683701150365))
* **internal:** ensure package is importable in lint cmd ([#92](https://github.com/pay-i/pay-i-python/issues/92)) ([1d8471d](https://github.com/pay-i/pay-i-python/commit/1d8471de10eaac594109d1ab9753a0a558f53be1))
* **internal:** fix devcontainers setup ([#242](https://github.com/pay-i/pay-i-python/issues/242)) ([3d40475](https://github.com/pay-i/pay-i-python/commit/3d404756409540afe7446ee1373bfe4ba7fe023b))
* **internal:** properly set __pydantic_private__ ([#243](https://github.com/pay-i/pay-i-python/issues/243)) ([dc7c47f](https://github.com/pay-i/pay-i-python/commit/dc7c47ff1501c8c6f5b98ce72b8903895a351d08))
* **internal:** refactor release doctor script ([#55](https://github.com/pay-i/pay-i-python/issues/55)) ([b0a2707](https://github.com/pay-i/pay-i-python/commit/b0a2707b711baa23ee4af9152b7a3f8558ac8d09))
* **internal:** refactor release doctor script ([#55](https://github.com/pay-i/pay-i-python/issues/55)) ([c443bc0](https://github.com/pay-i/pay-i-python/commit/c443bc0ec90b53ad763b8795173298b72ff08080))
* **internal:** remove deprecated ruff config ([#85](https://github.com/pay-i/pay-i-python/issues/85)) ([744ae88](https://github.com/pay-i/pay-i-python/commit/744ae888b57aa5a424e4a4729d7c0e85776b6d08))
* **internal:** remove deprecated ruff config ([#85](https://github.com/pay-i/pay-i-python/issues/85)) ([bdcd6c7](https://github.com/pay-i/pay-i-python/commit/bdcd6c7cb8d83d1686f7b3ff233bb313421bb982))
* **internal:** test updates ([#72](https://github.com/pay-i/pay-i-python/issues/72)) ([1ded1fe](https://github.com/pay-i/pay-i-python/commit/1ded1feade7fb2ad98e2e9eb3d2a4c957146cfb8))
* **internal:** test updates ([#72](https://github.com/pay-i/pay-i-python/issues/72)) ([861bf08](https://github.com/pay-i/pay-i-python/commit/861bf08135ab1fa5c625d9caa4d4bbf00f96839c))
* **internal:** update pydantic compat helper function ([#74](https://github.com/pay-i/pay-i-python/issues/74)) ([16f34b3](https://github.com/pay-i/pay-i-python/commit/16f34b307bd097cbd0ed81328972727c3ccec581))
* **internal:** update pydantic compat helper function ([#74](https://github.com/pay-i/pay-i-python/issues/74)) ([35b49b8](https://github.com/pay-i/pay-i-python/commit/35b49b821537c39e5bb1177f7ad8a17b843e34e0))
* **internal:** update pydantic v1 compat helpers ([#117](https://github.com/pay-i/pay-i-python/issues/117)) ([598362c](https://github.com/pay-i/pay-i-python/commit/598362c8cb2c6fb7a012eec1c17ca540b1ee4a3e))
* **internal:** use `TypeAlias` marker for type assignments ([#69](https://github.com/pay-i/pay-i-python/issues/69)) ([eebb6e9](https://github.com/pay-i/pay-i-python/commit/eebb6e95c4e8ad497dc178099923e036644bfd4a))
* **internal:** use `TypeAlias` marker for type assignments ([#69](https://github.com/pay-i/pay-i-python/issues/69)) ([99c736c](https://github.com/pay-i/pay-i-python/commit/99c736ceb18de8b95d5fc812ce5eb3734d1f09f7))
* **internal:** version bump ([#10](https://github.com/pay-i/pay-i-python/issues/10)) ([fecdc06](https://github.com/pay-i/pay-i-python/commit/fecdc060c15567053f9278258c6e029d7ba068e5))
* **internal:** version bump ([#102](https://github.com/pay-i/pay-i-python/issues/102)) ([5a2e82c](https://github.com/pay-i/pay-i-python/commit/5a2e82cf92d468534b5156d6390472ef23587dc6))
* **internal:** version bump ([#105](https://github.com/pay-i/pay-i-python/issues/105)) ([4e7499d](https://github.com/pay-i/pay-i-python/commit/4e7499d645cce95ba8907c08a01f75290e7b4c63))
* **internal:** version bump ([#113](https://github.com/pay-i/pay-i-python/issues/113)) ([c375532](https://github.com/pay-i/pay-i-python/commit/c375532623f63da11631ade66c5d82032e71a279))
* **internal:** version bump ([#15](https://github.com/pay-i/pay-i-python/issues/15)) ([45fe2bf](https://github.com/pay-i/pay-i-python/commit/45fe2bf5ae17612d6ba292ad5aa4948b76e713bf))
* **internal:** version bump ([#18](https://github.com/pay-i/pay-i-python/issues/18)) ([8e76fc4](https://github.com/pay-i/pay-i-python/commit/8e76fc4f4a99729ea2d0ffd449179265f19f2413))
* **internal:** version bump ([#22](https://github.com/pay-i/pay-i-python/issues/22)) ([4b5aec1](https://github.com/pay-i/pay-i-python/commit/4b5aec1116b6a0709e7e91ea71b95fb0cef01175))
* **internal:** version bump ([#27](https://github.com/pay-i/pay-i-python/issues/27)) ([bc69988](https://github.com/pay-i/pay-i-python/commit/bc6998870779070079f84eb0012cf355a6d16341))
* **internal:** version bump ([#3](https://github.com/pay-i/pay-i-python/issues/3)) ([b2822ad](https://github.com/pay-i/pay-i-python/commit/b2822ad9b7d64291a708bcdd33bc9573e2d78ba9))
* **internal:** version bump ([#31](https://github.com/pay-i/pay-i-python/issues/31)) ([c3024fd](https://github.com/pay-i/pay-i-python/commit/c3024fdd6ed72efc749b59332d72bda4adbb3542))
* **internal:** version bump ([#47](https://github.com/pay-i/pay-i-python/issues/47)) ([70ad20b](https://github.com/pay-i/pay-i-python/commit/70ad20b368f05fe56b3ee5f1ea8c96f366f282df))
* **internal:** version bump ([#62](https://github.com/pay-i/pay-i-python/issues/62)) ([3c6a8a3](https://github.com/pay-i/pay-i-python/commit/3c6a8a3f12fb8f649dde37cf489496e6db883892))
* **internal:** version bump ([#7](https://github.com/pay-i/pay-i-python/issues/7)) ([fbe323e](https://github.com/pay-i/pay-i-python/commit/fbe323e2ad1fcc471b8220d68bc82ef3a67a30b3))
* **internal:** version bump ([#76](https://github.com/pay-i/pay-i-python/issues/76)) ([b657ab0](https://github.com/pay-i/pay-i-python/commit/b657ab0277a0b09afb839ae0ad3057ebc1d23fef))
* **internal:** version bump ([#82](https://github.com/pay-i/pay-i-python/issues/82)) ([1ad176b](https://github.com/pay-i/pay-i-python/commit/1ad176b16a9f7d6ee0f7ed75a734356721cad0a2))
* **internal:** version bump ([#88](https://github.com/pay-i/pay-i-python/issues/88)) ([88588d8](https://github.com/pay-i/pay-i-python/commit/88588d810596d4acd0284f190f2939cf3bb49427))
* **internal:** version bump ([#93](https://github.com/pay-i/pay-i-python/issues/93)) ([a65550e](https://github.com/pay-i/pay-i-python/commit/a65550efd1e1e979bfcd387f06be70c37402fc1d))
* **internal:** version bump ([#97](https://github.com/pay-i/pay-i-python/issues/97)) ([b2f4af6](https://github.com/pay-i/pay-i-python/commit/b2f4af6feaebfb822f9562a80e7b8ee49e3bb04e))
* single header names declaration ([c54f793](https://github.com/pay-i/pay-i-python/commit/c54f793abdf138ea5d742d4d8d3e88bde153caf4))
* **tests:** update prism version ([#56](https://github.com/pay-i/pay-i-python/issues/56)) ([df7370f](https://github.com/pay-i/pay-i-python/commit/df7370f0aa1c8aa77e3091cb0b7c60238fb35ba0))
* **tests:** update prism version ([#56](https://github.com/pay-i/pay-i-python/issues/56)) ([c8de639](https://github.com/pay-i/pay-i-python/commit/c8de639a51631a212afc5827db5e85a7a3fbfaad))
* update SDK settings ([8ff0351](https://github.com/pay-i/pay-i-python/commit/8ff0351ba46df46381eb41cf4eadf655ddb82049))
* update SDK settings ([7499f33](https://github.com/pay-i/pay-i-python/commit/7499f33bafe555ecce0e6da47131135c568826e4))
* update SDK settings ([441d968](https://github.com/pay-i/pay-i-python/commit/441d9681112eae338ced67f5186a4a2e371cb99c))
* update SDK settings ([a3ca848](https://github.com/pay-i/pay-i-python/commit/a3ca8488d686df10ce22f53d69a7ec89f4268131))


### Documentation

* update URLs from stainlessapi.com to stainless.com ([#244](https://github.com/pay-i/pay-i-python/issues/244)) ([35a6787](https://github.com/pay-i/pay-i-python/commit/35a67870e10677ee315a15834207fb25125e98b7))

## 0.1.0-alpha.52 (2025-02-20)

Full Changelog: [v0.1.0-alpha.51...v0.1.0-alpha.52](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.51...v0.1.0-alpha.52)

### Features

* feat: ingest support for resource scope ([e2b4ce8](https://github.com/Pay-i/pay-i-python/commit/e2b4ce847b3f54df1bc5be7a78cf81dccd80c88c))

## 0.1.0-alpha.51 (2025-02-20)

Full Changelog: [v0.1.0-alpha.50...v0.1.0-alpha.51](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.50...v0.1.0-alpha.51)

### Features

* **api:** manual updates ([#235](https://github.com/Pay-i/pay-i-python/issues/235)) ([92e6b3c](https://github.com/Pay-i/pay-i-python/commit/92e6b3c9328caae24efbb75214f5f5087bfd57ec))

## 0.1.0-alpha.50 (2025-02-14)

Full Changelog: [v0.1.0-alpha.49...v0.1.0-alpha.50](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.49...v0.1.0-alpha.50)

### Bug Fixes

* asyncify on non-asyncio runtimes ([#233](https://github.com/Pay-i/pay-i-python/issues/233)) ([fa695e3](https://github.com/Pay-i/pay-i-python/commit/fa695e32df5f90064a16e547ff5e1d2aa7e6655c))


### Chores

* **internal:** update client tests ([#231](https://github.com/Pay-i/pay-i-python/issues/231)) ([9ed5673](https://github.com/Pay-i/pay-i-python/commit/9ed567342c9360349be4a7770580929a96b306be))

## 0.1.0-alpha.49 (2025-02-10)

Full Changelog: [v0.1.0-alpha.48...v0.1.0-alpha.49](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.48...v0.1.0-alpha.49)

### Features

* **api:** manual updates ([#227](https://github.com/Pay-i/pay-i-python/issues/227)) ([e32a7a1](https://github.com/Pay-i/pay-i-python/commit/e32a7a161132b2a0c85244db62a6bf3a37b37444))

## 0.1.0-alpha.48 (2025-02-08)

Full Changelog: [v0.1.0-alpha.47...v0.1.0-alpha.48](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.47...v0.1.0-alpha.48)

### Chores

* **internal:** fix type traversing dictionary params ([#223](https://github.com/Pay-i/pay-i-python/issues/223)) ([a68875f](https://github.com/Pay-i/pay-i-python/commit/a68875ff18bff2222b50567d2aeab5e3da1f2491))
* **internal:** minor type handling changes ([#225](https://github.com/Pay-i/pay-i-python/issues/225)) ([d0085cf](https://github.com/Pay-i/pay-i-python/commit/d0085cf20ded356b6e00c4969bef62cd4fb68bc8))

## 0.1.0-alpha.47 (2025-02-08)

Full Changelog: [v0.1.0-alpha.46...v0.1.0-alpha.47](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.46...v0.1.0-alpha.47)

### Features

* chore: single header names declaration ([e4f634c](https://github.com/Pay-i/pay-i-python/commit/e4f634ce5c903133278aeb29cb1a98262bcd3e0f))
* fix linter ([912b631](https://github.com/Pay-i/pay-i-python/commit/912b6314aaa4075a79aeb378aeb9e93fff47019e))

## 0.1.0-alpha.46 (2025-02-06)

Full Changelog: [v0.1.0-alpha.45...v0.1.0-alpha.46](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.45...v0.1.0-alpha.46)

### Features

* feat: OpenAI embeddings instrumentation ([8649277](https://github.com/Pay-i/pay-i-python/commit/864927729c11c54b4505123ee9c8c3ac6fec2304))

## 0.1.0-alpha.45 (2025-02-06)

Full Changelog: [v0.1.0-alpha.44...v0.1.0-alpha.45](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.44...v0.1.0-alpha.45)

### Features

* fix: preserve kwargs ([7d82f65](https://github.com/Pay-i/pay-i-python/commit/7d82f65c1dc74bf83cb661aca9a2f6dfe268c2df))

## 0.1.0-alpha.44 (2025-02-06)

Full Changelog: [v0.1.0-alpha.43...v0.1.0-alpha.44](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.43...v0.1.0-alpha.44)

### Features

* feat(api): azure openai ([#215](https://github.com/Pay-i/pay-i-python/issues/215)) ([55781bc](https://github.com/Pay-i/pay-i-python/commit/55781bc055535677c2b694a20172abfde595c596))

## 0.1.0-alpha.43 (2025-02-06)

Full Changelog: [v0.1.0-alpha.42...v0.1.0-alpha.43](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.42...v0.1.0-alpha.43)

### Features

* **client:** send `X-Stainless-Read-Timeout` header ([#210](https://github.com/Pay-i/pay-i-python/issues/210)) ([fd485f6](https://github.com/Pay-i/pay-i-python/commit/fd485f692182c38d869cfadddc57d1d7c623df8e))

## 0.1.0-alpha.42 (2025-02-05)

Full Changelog: [v0.1.0-alpha.41...v0.1.0-alpha.42](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.41...v0.1.0-alpha.42)

### Features

* **api:** manual updates ([#208](https://github.com/Pay-i/pay-i-python/issues/208)) ([f49df86](https://github.com/Pay-i/pay-i-python/commit/f49df86c7897ecfe322ad069b1bf609e3f603b4a))

## 0.1.0-alpha.41 (2025-02-04)

Full Changelog: [v0.1.0-alpha.40...v0.1.0-alpha.41](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.40...v0.1.0-alpha.41)

### Chores

* **internal:** bummp ruff dependency ([#204](https://github.com/Pay-i/pay-i-python/issues/204)) ([d6e457f](https://github.com/Pay-i/pay-i-python/commit/d6e457f7e62b5d08199e170abfda75fab75099f6))
* **internal:** change default timeout to an int ([#202](https://github.com/Pay-i/pay-i-python/issues/202)) ([c65e2c5](https://github.com/Pay-i/pay-i-python/commit/c65e2c5c8f420505025be81f7d566f048aa7bc19))

## 0.1.0-alpha.40 (2025-01-31)

Full Changelog: [v0.1.0-alpha.39...v0.1.0-alpha.40](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.39...v0.1.0-alpha.40)

### Features

* update units calculation ([a8dda4a](https://github.com/Pay-i/pay-i-python/commit/a8dda4a72b4fa6720e7e3b621f503e435630481f))

## 0.1.0-alpha.39 (2025-01-31)

Full Changelog: [v0.1.0-alpha.38...v0.1.0-alpha.39](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.38...v0.1.0-alpha.39)

### Features

* **api:** manual updates ([#194](https://github.com/Pay-i/pay-i-python/issues/194)) ([d31bb11](https://github.com/Pay-i/pay-i-python/commit/d31bb11b5138e4f23b5d5a7eadd09843b2c9df76))

## 0.1.0-alpha.38 (2025-01-31)

Full Changelog: [v0.1.0-alpha.37...v0.1.0-alpha.38](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.37...v0.1.0-alpha.38)

### Features

* **api:** manual updates ([#190](https://github.com/Pay-i/pay-i-python/issues/190)) ([ef6d309](https://github.com/Pay-i/pay-i-python/commit/ef6d309a7bf16ae3632bf6fe2bf26815b7652bab))

## 0.1.0-alpha.37 (2025-01-30)

Full Changelog: [v0.1.0-alpha.36...v0.1.0-alpha.37](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.36...v0.1.0-alpha.37)

### Features

* **api:** manual updates ([#187](https://github.com/Pay-i/pay-i-python/issues/187)) ([028e7c8](https://github.com/Pay-i/pay-i-python/commit/028e7c86f30727a2883d9823cdedb450f8397d1c))

## 0.1.0-alpha.36 (2025-01-28)

Full Changelog: [v0.1.0-alpha.35...v0.1.0-alpha.36](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.35...v0.1.0-alpha.36)

### Bug Fixes

* **tests:** make test_get_platform less flaky ([#181](https://github.com/Pay-i/pay-i-python/issues/181)) ([86d5b4a](https://github.com/Pay-i/pay-i-python/commit/86d5b4aa623c276776f0bdba5fa936d5408c6ab3))


### Chores

* **internal:** avoid pytest-asyncio deprecation warning ([#182](https://github.com/Pay-i/pay-i-python/issues/182)) ([38bb22c](https://github.com/Pay-i/pay-i-python/commit/38bb22ca2fa0f6dd88942b4744f9b0ffee030d5c))
* **internal:** codegen related update ([#178](https://github.com/Pay-i/pay-i-python/issues/178)) ([315a2c5](https://github.com/Pay-i/pay-i-python/commit/315a2c576e14d51239590f3bfc53872a288559c7))
* **internal:** codegen related update ([#183](https://github.com/Pay-i/pay-i-python/issues/183)) ([00fdbe7](https://github.com/Pay-i/pay-i-python/commit/00fdbe791e16fa12e73e1203dd0ab02270127e27))
* **internal:** codegen related update ([#184](https://github.com/Pay-i/pay-i-python/issues/184)) ([bf04c0e](https://github.com/Pay-i/pay-i-python/commit/bf04c0e4707fc2218da6fa6e676fd6c2e85bff07))
* **internal:** codegen related update ([#185](https://github.com/Pay-i/pay-i-python/issues/185)) ([e0d7ab1](https://github.com/Pay-i/pay-i-python/commit/e0d7ab154ce6d0a60095d8740b9ba5949a37aa00))


### Documentation

* **raw responses:** fix duplicate `the` ([#180](https://github.com/Pay-i/pay-i-python/issues/180)) ([ef72f36](https://github.com/Pay-i/pay-i-python/commit/ef72f367b02d8a71b6ef108a8e3544be77d5bd60))

## 0.1.0-alpha.35 (2025-01-12)

Full Changelog: [v0.1.0-alpha.34...v0.1.0-alpha.35](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.34...v0.1.0-alpha.35)

### Features

* **api:** manual updates ([#175](https://github.com/Pay-i/pay-i-python/issues/175)) ([3dd351e](https://github.com/Pay-i/pay-i-python/commit/3dd351ecb7d7c34ce73d8a26590000fb4dc38dbc))


### Bug Fixes

* **client:** only call .close() when needed ([#172](https://github.com/Pay-i/pay-i-python/issues/172)) ([75baf12](https://github.com/Pay-i/pay-i-python/commit/75baf1247d05a1b8a02fcfc4aa1342a11ef882b2))


### Chores

* **internal:** bump httpx dependency ([#171](https://github.com/Pay-i/pay-i-python/issues/171)) ([e7bf93a](https://github.com/Pay-i/pay-i-python/commit/e7bf93a87ae1bec99ee4f0fd049b2e4c8f6ef68d))
* **internal:** codegen related update ([#169](https://github.com/Pay-i/pay-i-python/issues/169)) ([03a0803](https://github.com/Pay-i/pay-i-python/commit/03a0803e49689e31d3d7b42d2da7ed9e886434a8))
* **internal:** codegen related update ([#174](https://github.com/Pay-i/pay-i-python/issues/174)) ([21d0af0](https://github.com/Pay-i/pay-i-python/commit/21d0af0f6b7a15efa62f9c514681f61fa1f9ddb8))


### Documentation

* fix typos ([#173](https://github.com/Pay-i/pay-i-python/issues/173)) ([3d97187](https://github.com/Pay-i/pay-i-python/commit/3d971877582257b349fa59bc83535b6cc3374c43))

## 0.1.0-alpha.34 (2025-01-06)

Full Changelog: [v0.1.0-alpha.33...v0.1.0-alpha.34](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.33...v0.1.0-alpha.34)

### Features

* **api:** rename budgets to limits ([#166](https://github.com/Pay-i/pay-i-python/issues/166)) ([7b7bdf3](https://github.com/Pay-i/pay-i-python/commit/7b7bdf3e9deade234ddd46ec1ad8bb9255f4ab64))


### Chores

* **internal:** codegen related update ([#164](https://github.com/Pay-i/pay-i-python/issues/164)) ([c8be7a0](https://github.com/Pay-i/pay-i-python/commit/c8be7a00beab6874fbdae426c52b63c509eba450))

## 0.1.0-alpha.33 (2024-12-18)

Full Changelog: [v0.1.0-alpha.32...v0.1.0-alpha.33](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.32...v0.1.0-alpha.33)

### Chores

* **internal:** add support for TypeAliasType ([#159](https://github.com/Pay-i/pay-i-python/issues/159)) ([8ea8180](https://github.com/Pay-i/pay-i-python/commit/8ea81803464331a9d431871b3965716e7dd751cc))
* **internal:** bump pyright ([#157](https://github.com/Pay-i/pay-i-python/issues/157)) ([9e0676b](https://github.com/Pay-i/pay-i-python/commit/9e0676bcdb4f9c8518632a480650667b9aba27f7))
* **internal:** codegen related update ([#160](https://github.com/Pay-i/pay-i-python/issues/160)) ([5141606](https://github.com/Pay-i/pay-i-python/commit/5141606ed39b82cff8e7c70416a01adab04c0944))
* **internal:** fix some typos ([#162](https://github.com/Pay-i/pay-i-python/issues/162)) ([5ef33a3](https://github.com/Pay-i/pay-i-python/commit/5ef33a34129c147183ddc746373dd99721741b4c))


### Documentation

* **readme:** example snippet for client context manager ([#161](https://github.com/Pay-i/pay-i-python/issues/161)) ([bcbbfa5](https://github.com/Pay-i/pay-i-python/commit/bcbbfa5ce1d75ab4d8cc9a7b2b2d85ae69a13277))

## 0.1.0-alpha.32 (2024-12-10)

Full Changelog: [v0.1.0-alpha.31...v0.1.0-alpha.32](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.31...v0.1.0-alpha.32)

### Chores

* **internal:** bump pydantic dependency ([#154](https://github.com/Pay-i/pay-i-python/issues/154)) ([c2187c5](https://github.com/Pay-i/pay-i-python/commit/c2187c501a445cf1fbeff1d3ca97508c30232236))
* make the `Omit` type public ([#152](https://github.com/Pay-i/pay-i-python/issues/152)) ([def0371](https://github.com/Pay-i/pay-i-python/commit/def0371c51b545d0109ca8473aa4242a35094e3c))


### Documentation

* **readme:** fix http client proxies example ([#155](https://github.com/Pay-i/pay-i-python/issues/155)) ([7eb2bf7](https://github.com/Pay-i/pay-i-python/commit/7eb2bf7e1147968cf5ed67c28a1c155694b69e28))

## 0.1.0-alpha.31 (2024-12-03)

Full Changelog: [v0.1.0-alpha.30...v0.1.0-alpha.31](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.30...v0.1.0-alpha.31)

### Features

* **api:** manual updates ([#149](https://github.com/Pay-i/pay-i-python/issues/149)) ([5f9b61b](https://github.com/Pay-i/pay-i-python/commit/5f9b61b4d344c090dc1ce3192ba659fbd2ec895b))

## 0.1.0-alpha.30 (2024-12-03)

Full Changelog: [v0.1.0-alpha.29...v0.1.0-alpha.30](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.29...v0.1.0-alpha.30)

### Bug Fixes

* **asyncify:** avoid hanging process under certain conditions ([#141](https://github.com/Pay-i/pay-i-python/issues/141)) ([58b8775](https://github.com/Pay-i/pay-i-python/commit/58b8775427865cb3aa4c05748511c7f2d5ab8c22))
* **client:** compat with new httpx 0.28.0 release ([#146](https://github.com/Pay-i/pay-i-python/issues/146)) ([4ae1a72](https://github.com/Pay-i/pay-i-python/commit/4ae1a72109d0633aaa08d9ff9d6d3aef7e1a9e0d))


### Chores

* **internal:** bump pyright ([#147](https://github.com/Pay-i/pay-i-python/issues/147)) ([f169e37](https://github.com/Pay-i/pay-i-python/commit/f169e3780bb33eefaf18ae61f4765a21be418f1e))
* **internal:** codegen related update ([#144](https://github.com/Pay-i/pay-i-python/issues/144)) ([792376c](https://github.com/Pay-i/pay-i-python/commit/792376c30d33a9a2aa0bacf53c38e481ded7be4c))
* **internal:** exclude mypy from running on tests ([#145](https://github.com/Pay-i/pay-i-python/issues/145)) ([3856fd1](https://github.com/Pay-i/pay-i-python/commit/3856fd19391aa68befe8776406e340efdff49984))
* **internal:** fix compat model_dump method when warnings are passed ([#142](https://github.com/Pay-i/pay-i-python/issues/142)) ([58b3ef8](https://github.com/Pay-i/pay-i-python/commit/58b3ef8b4d1dc9c7df2858c6914e587e08f43857))
* rebuild project due to codegen change ([#139](https://github.com/Pay-i/pay-i-python/issues/139)) ([9ed4a24](https://github.com/Pay-i/pay-i-python/commit/9ed4a2439973965d745cbfd2dfc68003958d51c5))


### Documentation

* add info log level to readme ([#143](https://github.com/Pay-i/pay-i-python/issues/143)) ([cec3a51](https://github.com/Pay-i/pay-i-python/commit/cec3a51a51ca9ab67c37dd2692a5222ede4c72cf))

## 0.1.0-alpha.29 (2024-11-15)

Full Changelog: [v0.1.0-alpha.28...v0.1.0-alpha.29](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.28...v0.1.0-alpha.29)

### Features

* **api:** update apikey header ([#132](https://github.com/Pay-i/pay-i-python/issues/132)) ([4e42d00](https://github.com/Pay-i/pay-i-python/commit/4e42d005530be2e002f536c2008c75a2afc1dea2))

## 0.1.0-alpha.28 (2024-11-15)

Full Changelog: [v0.1.0-alpha.27...v0.1.0-alpha.28](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.27...v0.1.0-alpha.28)

### Features

* **api:** api update ([#127](https://github.com/Pay-i/pay-i-python/issues/127)) ([f9f8665](https://github.com/Pay-i/pay-i-python/commit/f9f8665278eec1f3b4d081076047460004230a97))


### Chores

* rebuild project due to codegen change ([#128](https://github.com/Pay-i/pay-i-python/issues/128)) ([31ab0f5](https://github.com/Pay-i/pay-i-python/commit/31ab0f57ca4d1c073c7d1996af9df94db792cf9f))
* rebuild project due to codegen change ([#130](https://github.com/Pay-i/pay-i-python/issues/130)) ([e98d9ce](https://github.com/Pay-i/pay-i-python/commit/e98d9cead371ef5e3e9f3b68116dc81975fbd471))
* rebuild project due to codegen change ([#131](https://github.com/Pay-i/pay-i-python/issues/131)) ([e197c4b](https://github.com/Pay-i/pay-i-python/commit/e197c4b0199f417b550ee4c852ffcaef4888c82c))

## 0.1.0-alpha.27 (2024-10-22)

Full Changelog: [v0.1.0-alpha.26...v0.1.0-alpha.27](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.26...v0.1.0-alpha.27)

### Features

* **api:** api update ([#121](https://github.com/Pay-i/pay-i-python/issues/121)) ([5d4aa28](https://github.com/Pay-i/pay-i-python/commit/5d4aa28bde2fa653fb5c99081758d8c06de572ea))
* **api:** api update ([#125](https://github.com/Pay-i/pay-i-python/issues/125)) ([64e1ac8](https://github.com/Pay-i/pay-i-python/commit/64e1ac8e641917f23998c95fc9ce717484dc826f))

## 0.1.0-alpha.26 (2024-10-01)

Full Changelog: [v0.1.0-alpha.25...v0.1.0-alpha.26](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.25...v0.1.0-alpha.26)

### Features

* **api:** api update ([#121](https://github.com/Pay-i/pay-i-python/issues/121)) ([2705291](https://github.com/Pay-i/pay-i-python/commit/27052910f37169c45456fc2a752a8525eb858d4e))


### Chores

* **internal:** codegen related update ([#119](https://github.com/Pay-i/pay-i-python/issues/119)) ([1e7361a](https://github.com/Pay-i/pay-i-python/commit/1e7361a69e9751e834bb32a450624324aa27c646))

## 0.1.0-alpha.25 (2024-09-25)

Full Changelog: [v0.1.0-alpha.24...v0.1.0-alpha.25](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.24...v0.1.0-alpha.25)

### Features

* **api:** add Evaluations ([#114](https://github.com/Pay-i/pay-i-python/issues/114)) ([6352b8d](https://github.com/Pay-i/pay-i-python/commit/6352b8d8d69a8e2d636e7fd43745dae02b8c7fc9))


### Chores

* **internal:** codegen related update ([#115](https://github.com/Pay-i/pay-i-python/issues/115)) ([17c1b4d](https://github.com/Pay-i/pay-i-python/commit/17c1b4d89f6b54d87bc9e8dbceea2d6f4bd4f30a))
* **internal:** update pydantic v1 compat helpers ([#117](https://github.com/Pay-i/pay-i-python/issues/117)) ([e4a11c5](https://github.com/Pay-i/pay-i-python/commit/e4a11c5d2ad7baf3920d5608d07a31d9649ff570))

## 0.1.0-alpha.24 (2024-09-03)

Full Changelog: [v0.1.0-alpha.23...v0.1.0-alpha.24](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.23...v0.1.0-alpha.24)

### Features

* **api:** update via SDK Studio ([#109](https://github.com/Pay-i/pay-i-python/issues/109)) ([0655739](https://github.com/Pay-i/pay-i-python/commit/0655739af5c05d7dc0a906cba9c9ca6981c5c5c4))
* **api:** update via SDK Studio ([#111](https://github.com/Pay-i/pay-i-python/issues/111)) ([ac5c8a1](https://github.com/Pay-i/pay-i-python/commit/ac5c8a15234a1894d05e71bf7242ccaaa8ce81a7))


### Bug Fixes

* **api:** manual update ([#112](https://github.com/Pay-i/pay-i-python/issues/112)) ([e384406](https://github.com/Pay-i/pay-i-python/commit/e38440680eec95f16d2344b0185cd6752e522093))

## 0.1.0-alpha.23 (2024-09-03)

Full Changelog: [v0.1.0-alpha.22...v0.1.0-alpha.23](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.22...v0.1.0-alpha.23)

### Chores

* **internal:** codegen related update ([#106](https://github.com/Pay-i/pay-i-python/issues/106)) ([2d1f2f7](https://github.com/Pay-i/pay-i-python/commit/2d1f2f7db30d05b63ed85b7fe41962c6bfda2a9e))

## 0.1.0-alpha.22 (2024-08-14)

Full Changelog: [v0.1.0-alpha.21...v0.1.0-alpha.22](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.21...v0.1.0-alpha.22)

### Features

* **api:** update via SDK Studio ([#103](https://github.com/Pay-i/pay-i-python/issues/103)) ([0087070](https://github.com/Pay-i/pay-i-python/commit/0087070a5a3b51c14d396cafef7c7bb0eda034aa))

## 0.1.0-alpha.21 (2024-08-13)

Full Changelog: [v0.1.0-alpha.20...v0.1.0-alpha.21](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.20...v0.1.0-alpha.21)

### Features

* **api:** update via SDK Studio ([#100](https://github.com/Pay-i/pay-i-python/issues/100)) ([9e0f07b](https://github.com/Pay-i/pay-i-python/commit/9e0f07bec54cbefc0fb45bf81cdee8d812363d81))


### Chores

* **examples:** minor formatting changes ([#98](https://github.com/Pay-i/pay-i-python/issues/98)) ([7cd8cba](https://github.com/Pay-i/pay-i-python/commit/7cd8cba158668bb057c8bd154a267a9410f721b2))

## 0.1.0-alpha.20 (2024-08-09)

Full Changelog: [v0.1.0-alpha.19...v0.1.0-alpha.20](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.19...v0.1.0-alpha.20)

### Features

* **api:** update via SDK Studio ([#94](https://github.com/Pay-i/pay-i-python/issues/94)) ([d3cd372](https://github.com/Pay-i/pay-i-python/commit/d3cd3729991f4d0a8882f28f7ad42ebff73866eb))

## 0.1.0-alpha.19 (2024-08-09)

Full Changelog: [v0.1.0-alpha.18...v0.1.0-alpha.19](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.18...v0.1.0-alpha.19)

### Features

* **api:** update via SDK Studio ([#89](https://github.com/Pay-i/pay-i-python/issues/89)) ([b031428](https://github.com/Pay-i/pay-i-python/commit/b03142879e9d1798d08288578d078eab98e86353))


### Chores

* **ci:** bump prism mock server version ([#91](https://github.com/Pay-i/pay-i-python/issues/91)) ([6cd2937](https://github.com/Pay-i/pay-i-python/commit/6cd29379f24f7a7d261ed6beea8e4833e01eacfd))
* **internal:** ensure package is importable in lint cmd ([#92](https://github.com/Pay-i/pay-i-python/issues/92)) ([5af85e5](https://github.com/Pay-i/pay-i-python/commit/5af85e57dac94be4da96b45b406e683701150365))

## 0.1.0-alpha.18 (2024-08-08)

Full Changelog: [v0.1.0-alpha.17...v0.1.0-alpha.18](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.17...v0.1.0-alpha.18)

### Features

* **api:** update via SDK Studio ([#83](https://github.com/Pay-i/pay-i-python/issues/83)) ([c78b273](https://github.com/Pay-i/pay-i-python/commit/c78b273d807606abe94212e0092eff80895da96d))
* **api:** update via SDK Studio ([#86](https://github.com/Pay-i/pay-i-python/issues/86)) ([ea1bc86](https://github.com/Pay-i/pay-i-python/commit/ea1bc86c6a3671b49ba7394841b5534d7e8c0263))


### Chores

* **internal:** remove deprecated ruff config ([#85](https://github.com/Pay-i/pay-i-python/issues/85)) ([744ae88](https://github.com/Pay-i/pay-i-python/commit/744ae888b57aa5a424e4a4729d7c0e85776b6d08))

## 0.1.0-alpha.17 (2024-08-07)

Full Changelog: [v0.1.0-alpha.16...v0.1.0-alpha.17](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.16...v0.1.0-alpha.17)

### Features

* **api:** update via SDK Studio ([#79](https://github.com/Pay-i/pay-i-python/issues/79)) ([b7a562e](https://github.com/Pay-i/pay-i-python/commit/b7a562ed5f6051fd797ac76087ef095e8c73a8bc))


### Bug Fixes

* **client:** correctly serialise array body params ([#77](https://github.com/Pay-i/pay-i-python/issues/77)) ([e3770e4](https://github.com/Pay-i/pay-i-python/commit/e3770e474a9279eb4f13cbd7d87480d4d6a5bc76))

## 0.1.0-alpha.16 (2024-08-07)

Full Changelog: [v0.1.0-alpha.15...v0.1.0-alpha.16](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.15...v0.1.0-alpha.16)

### Features

* **api:** update via SDK Studio ([#67](https://github.com/Pay-i/pay-i-python/issues/67)) ([b720656](https://github.com/Pay-i/pay-i-python/commit/b72065621d50902959a484a5fe4c05051a5e2caa))
* **client:** add `retry_count` to raw response class ([#71](https://github.com/Pay-i/pay-i-python/issues/71)) ([88fdd1d](https://github.com/Pay-i/pay-i-python/commit/88fdd1df022c74e173db8697659dfba937f73be7))


### Chores

* **internal:** bump pyright ([#70](https://github.com/Pay-i/pay-i-python/issues/70)) ([28a35f0](https://github.com/Pay-i/pay-i-python/commit/28a35f0d6412c3fd2d0b0f696b5b723069ce7b98))
* **internal:** bump ruff version ([#73](https://github.com/Pay-i/pay-i-python/issues/73)) ([f487b64](https://github.com/Pay-i/pay-i-python/commit/f487b6409b3d6ac4eb3378e0eace4f68fbd3342f))
* **internal:** test updates ([#72](https://github.com/Pay-i/pay-i-python/issues/72)) ([1ded1fe](https://github.com/Pay-i/pay-i-python/commit/1ded1feade7fb2ad98e2e9eb3d2a4c957146cfb8))
* **internal:** update pydantic compat helper function ([#74](https://github.com/Pay-i/pay-i-python/issues/74)) ([16f34b3](https://github.com/Pay-i/pay-i-python/commit/16f34b307bd097cbd0ed81328972727c3ccec581))
* **internal:** use `TypeAlias` marker for type assignments ([#69](https://github.com/Pay-i/pay-i-python/issues/69)) ([eebb6e9](https://github.com/Pay-i/pay-i-python/commit/eebb6e95c4e8ad497dc178099923e036644bfd4a))

## 0.1.0-alpha.15 (2024-08-06)

Full Changelog: [v0.1.0-alpha.14...v0.1.0-alpha.15](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.14...v0.1.0-alpha.15)

### Features

* **api:** update via SDK Studio ([#63](https://github.com/Pay-i/pay-i-python/issues/63)) ([a38f132](https://github.com/Pay-i/pay-i-python/commit/a38f132cdbbbcac2c235c71cd758c38631b12a57))
* **api:** update via SDK Studio ([#65](https://github.com/Pay-i/pay-i-python/issues/65)) ([d32f303](https://github.com/Pay-i/pay-i-python/commit/d32f3032d3cb5854617e65e9766447d8ea08f41c))
* **api:** update via SDK Studio ([#66](https://github.com/Pay-i/pay-i-python/issues/66)) ([990a0cb](https://github.com/Pay-i/pay-i-python/commit/990a0cbcfb381f6f72530d869a7beaae6f9fed2d))

## 0.1.0-alpha.14 (2024-07-30)

Full Changelog: [v0.1.0-alpha.13...v0.1.0-alpha.14](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.13...v0.1.0-alpha.14)

### Features

* **api:** update via SDK Studio ([#48](https://github.com/Pay-i/pay-i-python/issues/48)) ([5b67542](https://github.com/Pay-i/pay-i-python/commit/5b6754279d6b6dcb3b65bda1bf59b0d0092b4bec))
* **api:** update via SDK Studio ([#50](https://github.com/Pay-i/pay-i-python/issues/50)) ([91c7d2c](https://github.com/Pay-i/pay-i-python/commit/91c7d2c29430835dfee501520d8b247755e1679d))
* **api:** update via SDK Studio ([#57](https://github.com/Pay-i/pay-i-python/issues/57)) ([8d6ce22](https://github.com/Pay-i/pay-i-python/commit/8d6ce2229764aeaac2b0229cb70266545759cc7d))
* **api:** update via SDK Studio ([#58](https://github.com/Pay-i/pay-i-python/issues/58)) ([013389a](https://github.com/Pay-i/pay-i-python/commit/013389a52fc87312e7173c34c3f27256e52b7ed5))
* **api:** update via SDK Studio ([#59](https://github.com/Pay-i/pay-i-python/issues/59)) ([9f895e6](https://github.com/Pay-i/pay-i-python/commit/9f895e649a06a9000b1da8ab4a0b2fb779b09db9))


### Chores

* **ci:** limit release doctor target branches ([#54](https://github.com/Pay-i/pay-i-python/issues/54)) ([926140e](https://github.com/Pay-i/pay-i-python/commit/926140e37dacca0b1e4ae481ed6fb839a154ad88))
* **docs:** document how to do per-request http client customization ([#53](https://github.com/Pay-i/pay-i-python/issues/53)) ([ea27182](https://github.com/Pay-i/pay-i-python/commit/ea271822df7ba59dc1cafc88e610b800a162c991))
* **internal:** add type construction helper ([#60](https://github.com/Pay-i/pay-i-python/issues/60)) ([65303cf](https://github.com/Pay-i/pay-i-python/commit/65303cf704602ece488a31e8a608be100279a1bc))
* **internal:** codegen related update ([#52](https://github.com/Pay-i/pay-i-python/issues/52)) ([4a469a0](https://github.com/Pay-i/pay-i-python/commit/4a469a0691431fe21ca111803ca6e256978cd21b))
* **internal:** refactor release doctor script ([#55](https://github.com/Pay-i/pay-i-python/issues/55)) ([b0a2707](https://github.com/Pay-i/pay-i-python/commit/b0a2707b711baa23ee4af9152b7a3f8558ac8d09))
* **tests:** update prism version ([#56](https://github.com/Pay-i/pay-i-python/issues/56)) ([df7370f](https://github.com/Pay-i/pay-i-python/commit/df7370f0aa1c8aa77e3091cb0b7c60238fb35ba0))

## 0.1.0-alpha.13 (2024-07-11)

Full Changelog: [v0.1.0-alpha.12...v0.1.0-alpha.13](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.12...v0.1.0-alpha.13)

### Features

* **api:** update via SDK Studio ([#45](https://github.com/Pay-i/pay-i-python/issues/45)) ([8129c56](https://github.com/Pay-i/pay-i-python/commit/8129c56fe00cc676e56e8318533b98be3234cf8f))

## 0.1.0-alpha.12 (2024-07-08)

Full Changelog: [v0.1.0-alpha.11...v0.1.0-alpha.12](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.11...v0.1.0-alpha.12)

### Features

* **api:** update via SDK Studio ([#42](https://github.com/Pay-i/pay-i-python/issues/42)) ([acfca49](https://github.com/Pay-i/pay-i-python/commit/acfca49e245ef237ca1459f3e80c77e883a7fa4a))
* **api:** update via SDK Studio ([#44](https://github.com/Pay-i/pay-i-python/issues/44)) ([8623402](https://github.com/Pay-i/pay-i-python/commit/86234024530b7a6b26508c65aad280a3a0fc33c3))

## 0.1.0-alpha.11 (2024-07-03)

Full Changelog: [v0.1.0-alpha.10...v0.1.0-alpha.11](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.10...v0.1.0-alpha.11)

### Features

* **api:** update via SDK Studio ([#39](https://github.com/Pay-i/pay-i-python/issues/39)) ([924942e](https://github.com/Pay-i/pay-i-python/commit/924942ed83577f9d6d6bc9709d22e5423a2c50b4))
* **api:** update via SDK Studio ([#41](https://github.com/Pay-i/pay-i-python/issues/41)) ([5fb515c](https://github.com/Pay-i/pay-i-python/commit/5fb515c9399354230bda965857e2dfa090db83b7))

## 0.1.0-alpha.10 (2024-07-02)

Full Changelog: [v0.1.0-alpha.9...v0.1.0-alpha.10](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.9...v0.1.0-alpha.10)

### Features

* **api:** update via SDK Studio ([#37](https://github.com/Pay-i/pay-i-python/issues/37)) ([b794015](https://github.com/Pay-i/pay-i-python/commit/b7940155a65297fda08c4022417a2d78ced5ee3f))

## 0.1.0-alpha.9 (2024-07-02)

Full Changelog: [v0.1.0-alpha.8...v0.1.0-alpha.9](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.8...v0.1.0-alpha.9)

### Features

* **api:** update via SDK Studio ([#34](https://github.com/Pay-i/pay-i-python/issues/34)) ([f05bc0e](https://github.com/Pay-i/pay-i-python/commit/f05bc0ee6357f32724b3199ea92aa8f5c17723e1))

## 0.1.0-alpha.8 (2024-07-02)

Full Changelog: [v0.1.0-alpha.7...v0.1.0-alpha.8](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.7...v0.1.0-alpha.8)

### Features

* **api:** update via SDK Studio ([#28](https://github.com/Pay-i/pay-i-python/issues/28)) ([972e5e3](https://github.com/Pay-i/pay-i-python/commit/972e5e3b8c84df6d3b47ba2dba4137151d9e414c))
* **api:** update via SDK Studio ([#30](https://github.com/Pay-i/pay-i-python/issues/30)) ([3334f89](https://github.com/Pay-i/pay-i-python/commit/3334f89029ba31d70aa759d367be32888a77b603))

## 0.1.0-alpha.7 (2024-07-02)

Full Changelog: [v0.1.0-alpha.6...v0.1.0-alpha.7](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.6...v0.1.0-alpha.7)

### Features

* **api:** update via SDK Studio ([#23](https://github.com/Pay-i/pay-i-python/issues/23)) ([5c2aa35](https://github.com/Pay-i/pay-i-python/commit/5c2aa35b45c18fb194b4055884d3abded49aad1e))
* **api:** update via SDK Studio ([#25](https://github.com/Pay-i/pay-i-python/issues/25)) ([9712710](https://github.com/Pay-i/pay-i-python/commit/9712710b0ab67462295a3f7531e3b034a91dc094))
* **api:** update via SDK Studio ([#26](https://github.com/Pay-i/pay-i-python/issues/26)) ([eebd44e](https://github.com/Pay-i/pay-i-python/commit/eebd44e55d800da8cf7b9a01108e78a3446d1283))

## 0.1.0-alpha.6 (2024-06-30)

Full Changelog: [v0.1.0-alpha.5...v0.1.0-alpha.6](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.5...v0.1.0-alpha.6)

### Features

* **api:** update via SDK Studio ([#21](https://github.com/Pay-i/pay-i-python/issues/21)) ([daa4259](https://github.com/Pay-i/pay-i-python/commit/daa4259dc2156dd84843d3264362a6a53ee842c4))

## 0.1.0-alpha.5 (2024-06-28)

Full Changelog: [v0.1.0-alpha.4...v0.1.0-alpha.5](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.4...v0.1.0-alpha.5)

### Features

* change ingest bugdet_ids and request_tags from str -&gt; list[str] ([bb70818](https://github.com/Pay-i/pay-i-python/commit/bb7081850e14648db2ad753a0aef461cdd7b1940))
* update types and tests ([02af29a](https://github.com/Pay-i/pay-i-python/commit/02af29aa209c434083c3ea335ccfc80450deda8c))

## 0.1.0-alpha.4 (2024-06-27)

Full Changelog: [v0.1.0-alpha.3...v0.1.0-alpha.4](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.3...v0.1.0-alpha.4)

### Features

* **api:** update via SDK Studio ([#13](https://github.com/Pay-i/pay-i-python/issues/13)) ([c35a02e](https://github.com/Pay-i/pay-i-python/commit/c35a02e163c67c320566bc77fb24bb6cdd8b4bf6))

## 0.1.0-alpha.3 (2024-06-27)

Full Changelog: [v0.1.0-alpha.2...v0.1.0-alpha.3](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.2...v0.1.0-alpha.3)

### Features

* fix ([cffc96b](https://github.com/Pay-i/pay-i-python/commit/cffc96b700565b99a9d1b171e7aa820a3a41fb0a))
* test rename of autogenerated parameter name ([53b0e7d](https://github.com/Pay-i/pay-i-python/commit/53b0e7dd2f37573d9683c4aa0c3a86de6d0e3dea))

## 0.1.0-alpha.2 (2024-06-27)

Full Changelog: [v0.1.0-alpha.1...v0.1.0-alpha.2](https://github.com/Pay-i/pay-i-python/compare/v0.1.0-alpha.1...v0.1.0-alpha.2)

### Features

* **api:** update via SDK Studio ([#4](https://github.com/Pay-i/pay-i-python/issues/4)) ([08bb37c](https://github.com/Pay-i/pay-i-python/commit/08bb37c7ab580b1c0d6adf12f3745191e9023455))

## 0.1.0-alpha.1 (2024-06-27)

Full Changelog: [v0.0.1-alpha.0...v0.1.0-alpha.1](https://github.com/Pay-i/pay-i-python/compare/v0.0.1-alpha.0...v0.1.0-alpha.1)

### Features

* **api:** update via SDK Studio ([ba34638](https://github.com/Pay-i/pay-i-python/commit/ba3463802b7366b450058f6ccdb13419b3bdbfe1))
* **api:** update via SDK Studio ([d87c30c](https://github.com/Pay-i/pay-i-python/commit/d87c30c4d5c3d7dee3a4b96596c8df9e319ca690))
* **api:** update via SDK Studio ([96d12c3](https://github.com/Pay-i/pay-i-python/commit/96d12c3c114642a13469ece184eaec8feee50b1a))
* **api:** update via SDK Studio ([ba169b1](https://github.com/Pay-i/pay-i-python/commit/ba169b1e70894cb2a2f0497e4781121a334716cd))


### Chores

* go live ([#2](https://github.com/Pay-i/pay-i-python/issues/2)) ([81ba939](https://github.com/Pay-i/pay-i-python/commit/81ba93934fc18d2ac642af4ce1a7772996cb5030))
* update SDK settings ([8ff0351](https://github.com/Pay-i/pay-i-python/commit/8ff0351ba46df46381eb41cf4eadf655ddb82049))
* update SDK settings ([441d968](https://github.com/Pay-i/pay-i-python/commit/441d9681112eae338ced67f5186a4a2e371cb99c))
