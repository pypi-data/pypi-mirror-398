# Changelog

## 0.5.3 (2025-12-23)

Full Changelog: [v0.5.2...v0.5.3](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.5.2...v0.5.3)

## 0.5.2 (2025-12-18)

Full Changelog: [v0.5.1...v0.5.2](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.5.1...v0.5.2)

## 0.5.1 (2025-12-18)

Full Changelog: [v0.5.0...v0.5.1](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.5.0...v0.5.1)

## 0.5.0 (2025-12-16)

Full Changelog: [v0.4.0...v0.5.0](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.4.0...v0.5.0)

### Features

* Bro 949 mouse click api to support dom selector click ([88947eb](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/88947eb7af3414d1ac76f6de3961623f2f3c173d))
* Bro 949 mouse click api to support dom selector click ([2f21297](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/2f21297ca41d95d1f5c455fdff0990a7df07069f))


### Chores

* **internal:** add missing files argument to base client ([3eb10ca](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/3eb10ca9462a0dd082a1a89872a15da21abee703))

## 0.4.0 (2025-12-11)

Full Changelog: [v0.3.13...v0.4.0](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.13...v0.4.0)

### Features

* BRO-1383 Add get identity credentials endpoint to SDK ([0548f2f](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/0548f2fd39fb76b7e972154637aafe317a6ce17f))

## 0.3.13 (2025-12-09)

Full Changelog: [v0.3.12...v0.3.13](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.12...v0.3.13)

### Bug Fixes

* **types:** allow pyright to infer TypedDict types within SequenceNotStr ([cb35cbc](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/cb35cbcfddccb5fee912b1cafe3dfab5b237209f))


### Chores

* add missing docstrings ([6e46d9f](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/6e46d9f28d01af030ea754883f0086cd80705999))

## 0.3.12 (2025-12-03)

Full Changelog: [v0.3.11...v0.3.12](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.11...v0.3.12)

### Chores

* **docs:** use environment variables for authentication in code snippets ([8d13120](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/8d13120a106de59c11150b731c22056d50df1192))
* update lockfile ([4d3c63b](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/4d3c63b11cacbd6e10f2c837c7e25ce9842b7cc2))

## 0.3.11 (2025-11-28)

Full Changelog: [v0.3.10...v0.3.11](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.10...v0.3.11)

### Bug Fixes

* ensure streams are always closed ([89d49bb](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/89d49bb68cf30e8581917468718f36fd0e29a508))


### Chores

* **deps:** mypy 1.18.1 has a regression, pin to 1.17 ([bcb31f0](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/bcb31f0d220339f4cb119ab87d2c5c30544f009d))

## 0.3.10 (2025-11-22)

Full Changelog: [v0.3.9...v0.3.10](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.9...v0.3.10)

### Chores

* add Python 3.14 classifier and testing ([4a00b57](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/4a00b57d3d9ef00df7132fc01211e53630c862ec))

## 0.3.9 (2025-11-16)

Full Changelog: [v0.3.8...v0.3.9](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.8...v0.3.9)

### Features

* BRO-1203 docs: remove sessionId and taskSessionId parameters from run… ([9ae6b61](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/9ae6b61094c9c4668f3409a0a6505c08a4ce7051))

## 0.3.8 (2025-11-12)

Full Changelog: [v0.3.7...v0.3.8](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.7...v0.3.8)

### Bug Fixes

* **compat:** update signatures of `model_dump` and `model_dump_json` for Pydantic v1 ([fab1433](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/fab1433ffae3fdcbdce4f8cdf5f92aaade6385eb))

## 0.3.7 (2025-11-11)

Full Changelog: [v0.3.6...v0.3.7](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.6...v0.3.7)

## 0.3.6 (2025-11-11)

Full Changelog: [v0.3.5...v0.3.6](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.5...v0.3.6)

### Features

* max_steps_default ([9cbe618](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/9cbe6182c79f0269e2061fc4a074031d2c112e99))


### Bug Fixes

* compat with Python 3.14 ([4bac4f2](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/4bac4f2667d41c6d9ecb4ca4df14d50ed5f1bcc7))


### Chores

* **package:** drop Python 3.8 support ([7c976b9](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/7c976b92b74eb47f4dccd3891e0e8557b494160d))

## 0.3.5 (2025-11-04)

Full Changelog: [v0.3.4...v0.3.5](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.4...v0.3.5)

### Chores

* **internal:** grammar fix (it's -&gt; its) ([592da81](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/592da814085e1d7348a4eaefc98ebd987ed0d59f))

## 0.3.4 (2025-10-31)

Full Changelog: [v0.3.3...v0.3.4](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.3...v0.3.4)

## 0.3.3 (2025-10-31)

Full Changelog: [v0.3.2...v0.3.3](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.2...v0.3.3)

### Features

* Enhanced agent features documentation ([6ebf420](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/6ebf4206b4e60185adc696d63c8847dcebd45c83))


### Bug Fixes

* **client:** close streams without requiring full consumption ([3ff9aa7](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/3ff9aa743c874d2ecdbf3884fc630d1c81abc32c))


### Chores

* **internal/tests:** avoid race condition with implicit client cleanup ([5883b7c](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/5883b7ce49e1d130b094b44bee109b9ae20c27a9))

## 0.3.2 (2025-10-27)

Full Changelog: [v0.3.1...v0.3.2](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.1...v0.3.2)

## 0.3.1 (2025-10-26)

Full Changelog: [v0.3.0...v0.3.1](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.3.0...v0.3.1)

### Features

* **api:** manual updates ([ab2e49e](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/ab2e49eeb383bef056d6255e30503363fa87869e))

## 0.3.0 (2025-10-21)

Full Changelog: [v0.2.0...v0.3.0](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.2.0...v0.3.0)

### ⚠ BREAKING CHANGES

* **python:** Use `client.task.run()` instead of `client.task.run.execute()`

### Features

* **python:** move task.run.execute() to task.run() ([7d19ce5](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/7d19ce588df9a75d38fc0e53472b126c1b71112c))


### Bug Fixes

* reorganize task tests ([c9621f8](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/c9621f84d08522a8aa04bafda00893a026355979))
* resolve linting errors ([b2e73c8](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/b2e73c8a22b11cb5f4624b6ed3a6687cd9265bc7))
* resolve linting errors1 ([4544a64](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/4544a6435773a443fdb360e2647762224ac3c50b))
* resolve linting errors2 ([0405baa](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/0405baa1fb7fb666fe5144e7a5762224cdea6cff))

## 0.2.0 (2025-10-20)

Full Changelog: [v0.1.1...v0.2.0](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.1.1...v0.2.0)

### Features

* added batch and cursor rules ([db09e9b](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/db09e9b9fb753744809924e7b7eab822055c4b38))
* **api:** manual updates ([5847952](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/58479526f72df0bb37f42957243b416418e4f0d8))
* Bro 908 1 password integration 2 ([a63dc90](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/a63dc908ecf9de43296b3143574b756b6c94089e))
* BRO-959 us as default proxy country code ([a3d9294](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/a3d9294f0d20e07f49386dd07e8d8344a32d1d10))
* BRO-976 docs: add extra_stealth to openai and sdk ([d7aea94](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/d7aea94bd209bbafc08777a022203f8ab89697e3))


### Bug Fixes

* agent pause resume is back ([77d8397](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/77d8397b3742e77faacb39b89682d4fabaeb7ed1))


### Chores

* bump `httpx-aiohttp` version to 0.1.9 ([316d40e](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/316d40e4bb48b4c6b2a38afd75b7c855fc80f126))

## 0.1.1 (2025-10-11)

Full Changelog: [v0.1.0...v0.1.1](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/compare/v0.1.0...v0.1.1)

### Features

* Add disable_web_security ([cefa8d4](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/cefa8d4ae15c0ec2d39543b67ac3dde4bc1da791))
* added additional fetch-webpage options ([c7eead2](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/c7eead27ece65dd5c41860d9080f2167017f9da2))
* added agent pause and continue ([49a1a49](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/49a1a49c98831a12d031064ff251c81a83932651))
* Added OpenAPI specification for file uploads to browser sessions, inc… ([205c296](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/205c29632e3a19a1555b37b83cf8b0e2fca88843))
* added use os for scroll ([71bc128](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/71bc128ffde6bdf309d56fbfb6f1d44e7b46c1bf))
* **api:** manual updates ([41b55e3](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/41b55e3455ee8543f057191346995ff6f2fbb4df))
* **api:** manual updates ([171046c](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/171046c5f8dfbcd3f632e15e0d5bdae2d478af31))
* **api:** manual updates ([342688b](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/342688b498fc4aba7fcb0eb4cc54ea5be9051f35))
* BRO-622 update openapi spec with session get ([3c5ee34](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/3c5ee34dca0be7b44be1e4977290f8cb80a847b7))
* BRO-764 City based proxy ([936ffb8](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/936ffb8d46ee08a7edd345323a7adc4271b58f75))
* improve future compat with pydantic v3 ([4e5c038](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/4e5c038e9edcad6b418a32846813f76f67ff47c0))
* **types:** replace List[str] with SequenceNotStr in params ([0c39bce](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/0c39bce296ccf2143b9cc8d89bab75d53d3f1acc))


### Bug Fixes

* avoid newer type syntax ([f78c034](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/f78c034003d403087c556a4c18d9438637311a07))
* **compat:** compat with `pydantic&lt;2.8.0` when using additional fields ([53b002f](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/53b002f642874a7518ffc4a49f822e25ec6c83a0))


### Chores

* do not install brew dependencies in ./scripts/bootstrap by default ([75a97d0](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/75a97d04851d9cda1c1680c07efd24ed66b1bb6f))
* **internal:** add Sequence related utils ([d2c8ffc](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/d2c8ffc2d93043c6ef7b99d172542adb7c0bea0a))
* **internal:** change ci workflow machines ([31cfb87](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/31cfb877b7bd28f3726c996d778db040c27bda10))
* **internal:** codegen related update ([2103cfa](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/2103cfa93c032268d647554707d6bd11015e8ffd))
* **internal:** codegen related update ([bf5c542](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/bf5c5420a54af077edeb4c465254e39553859dc2))
* **internal:** detect missing future annotations with ruff ([8658af6](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/8658af6f33402b406e084607981a9fb0d052ec6f))
* **internal:** fix ruff target version ([3e2468a](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/3e2468a77261ccbf3420521293241253b269dd9d))
* **internal:** move mypy configurations to `pyproject.toml` file ([b42de93](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/b42de93096441c5b36b32bfeb36d8fd6383c3c55))
* **internal:** update comment in script ([a58dcb2](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/a58dcb25c04d22f93f495ff95dce45d15fd26571))
* **internal:** update pydantic dependency ([765c63f](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/765c63f233924e94f42d7b12a7d58341de6b8adb))
* **internal:** update pyright exclude list ([eeadbf8](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/eeadbf8cf3a12f552bb2ce88a64e15491815a1f8))
* **types:** change optional parameter type from NotGiven to Omit ([f84b4e0](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/f84b4e01b536f0f34703562c891d45a1b68ef9db))
* update @stainless-api/prism-cli to v5.15.0 ([88b661e](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/88b661e22651c660b72239df4a00f83a063e5e93))
* update github action ([bc5a5df](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/bc5a5df363f929149198bb713d26bb529c29d12d))


### Documentation

* add reset_preferences option to session profile configuration i… ([a35fb22](https://github.com/anchorbrowser/AnchorBrowser-SDK-Python/commit/a35fb2285e3c1225512860c9f957450ddb4cf896))
