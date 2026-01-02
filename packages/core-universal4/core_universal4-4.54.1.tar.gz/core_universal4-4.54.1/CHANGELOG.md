# Changelog

## [4.54.1](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.54.0...python/core-universal@4.54.1) (2025-12-28)


### Dependencies

* @applitools/dom-snapshot bumped to 4.15.4
  #### Bug Fixes

  * CSS variables in Shadow DOM style tags not expanded | FLD-3790 ([#3427](https://github.com/Applitools-Dev/sdk/issues/3427)) ([3d84b5f](https://github.com/Applitools-Dev/sdk/commit/3d84b5f120dd5e72dea5ec77b5d446e7ca696d52))
* @applitools/core bumped to 4.54.1
  #### Bug Fixes

  * improve error notification (UFG) | AD-12270 ([#3418](https://github.com/Applitools-Dev/sdk/issues/3418)) ([a4efc55](https://github.com/Applitools-Dev/sdk/commit/a4efc55cd178dc13096fbfb066c287b0d6a452d3))




## [4.54.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.53.2...python/core-universal@4.54.0) (2025-12-14)


### Dependencies

* @applitools/core-base bumped to 1.31.0
  #### Features

  * Baseline branch fallback list | FLD-3837 ([#3373](https://github.com/Applitools-Dev/sdk/issues/3373)) ([e94bb10](https://github.com/Applitools-Dev/sdk/commit/e94bb10ad6b49322a56e4ce6dfde560b237e9ac0))
* @applitools/nml-client bumped to 1.11.13

* @applitools/ec-client bumped to 1.12.15

* @applitools/core bumped to 4.54.0
  #### Features

  * Baseline branch fallback list | FLD-3837 ([#3373](https://github.com/Applitools-Dev/sdk/issues/3373)) ([e94bb10](https://github.com/Applitools-Dev/sdk/commit/e94bb10ad6b49322a56e4ce6dfde560b237e9ac0))




## [4.53.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.53.0...python/core-universal@4.53.2) (2025-12-07)


### Dependencies

* @applitools/dom-snapshot bumped to 4.15.3
  #### Bug Fixes

  * capture JavaScript-modified CSS selectors in nested [@layer](https://github.com/layer) rules ([#3391](https://github.com/Applitools-Dev/sdk/issues/3391)) ([b3bceb5](https://github.com/Applitools-Dev/sdk/commit/b3bceb5bfe894f3548173d23942e09d0e04b7e04))
* @applitools/core bumped to 4.53.2
  #### Bug Fixes

  * Upgrade core version ([#3398](https://github.com/Applitools-Dev/sdk/issues/3398)) ([68858c7](https://github.com/Applitools-Dev/sdk/commit/68858c7024e0413c1cc6af68752b1c3a9a04bb0b))




## [4.53.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.52.0...python/core-universal@4.53.0) (2025-11-19)


### Dependencies

* @applitools/utils bumped to 1.14.0
  #### Features

  * disable heartbeats whenever no tests are running ([#3344](https://github.com/Applitools-Dev/sdk/issues/3344)) ([b66d28a](https://github.com/Applitools-Dev/sdk/commit/b66d28a7a382f26b68de70c8633c027cb4bdf225))
* @applitools/core-base bumped to 1.30.0
  #### Features

  * disable heartbeats whenever no tests are running ([#3344](https://github.com/Applitools-Dev/sdk/issues/3344)) ([b66d28a](https://github.com/Applitools-Dev/sdk/commit/b66d28a7a382f26b68de70c8633c027cb4bdf225))


  #### Bug Fixes

  * fails to create test with coded dynamic region | AD-11074 ([#3361](https://github.com/Applitools-Dev/sdk/issues/3361)) ([7f8c8cd](https://github.com/Applitools-Dev/sdk/commit/7f8c8cd85c0cd2e5861cd33fbc29c465903258d5))
  * resolved an issue with `matchTimeout` changing `retryTimeout` ([f656f59](https://github.com/Applitools-Dev/sdk/commit/f656f59dbfb7c41fdb569fbc56d2e9daecefb854))



* @applitools/logger bumped to 2.2.6

* @applitools/dom-snapshot bumped to 4.15.1

* @applitools/socket bumped to 1.3.7

* @applitools/req bumped to 1.8.6

* @applitools/image bumped to 1.2.5

* @applitools/dom-capture bumped to 11.6.7

* @applitools/driver bumped to 1.24.2

* @applitools/spec-driver-webdriver bumped to 1.5.2

* @applitools/spec-driver-selenium bumped to 1.7.8

* @applitools/spec-driver-puppeteer bumped to 1.6.8

* @applitools/screenshoter bumped to 3.12.9

* @applitools/nml-client bumped to 1.11.11
  #### Bug Fixes

  * better nml error messages ([#3311](https://github.com/Applitools-Dev/sdk/issues/3311)) ([3deea01](https://github.com/Applitools-Dev/sdk/commit/3deea0130636c44573adc919b95c1c99e6d194f1))



* @applitools/tunnel-client bumped to 1.11.4

* @applitools/ufg-client bumped to 1.18.2

* @applitools/ec-client bumped to 1.12.13

* @applitools/core bumped to 4.53.0
  #### Features

  * disable heartbeats whenever no tests are running ([#3344](https://github.com/Applitools-Dev/sdk/issues/3344)) ([b66d28a](https://github.com/Applitools-Dev/sdk/commit/b66d28a7a382f26b68de70c8633c027cb4bdf225))


  #### Bug Fixes

  * better nml error messages ([#3311](https://github.com/Applitools-Dev/sdk/issues/3311)) ([3deea01](https://github.com/Applitools-Dev/sdk/commit/3deea0130636c44573adc919b95c1c99e6d194f1))
  * fails to create test with coded dynamic region | AD-11074 ([#3361](https://github.com/Applitools-Dev/sdk/issues/3361)) ([7f8c8cd](https://github.com/Applitools-Dev/sdk/commit/7f8c8cd85c0cd2e5861cd33fbc29c465903258d5))
  * resolved an issue with `matchTimeout` changing `retryTimeout` ([f656f59](https://github.com/Applitools-Dev/sdk/commit/f656f59dbfb7c41fdb569fbc56d2e9daecefb854))



* @applitools/test-server bumped to 1.3.5


## [4.52.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.51.0...python/core-universal@4.52.0) (2025-11-09)


### Dependencies

* @applitools/utils bumped to 1.13.0
  #### Features

  * restart cache and keepalive | FLD-3773 ([#3326](https://github.com/Applitools-Dev/sdk/issues/3326)) ([0fd12ca](https://github.com/Applitools-Dev/sdk/commit/0fd12ca703b4546560b563076a38f9ada24acc75))
* @applitools/logger bumped to 2.2.5

* @applitools/dom-snapshot bumped to 4.15.0
  #### Features

  * add support for adopted stylesheets with nesting | FLD-3212 ([#3325](https://github.com/Applitools-Dev/sdk/issues/3325)) ([8587926](https://github.com/Applitools-Dev/sdk/commit/8587926b0d6ef820cfbd8f89ddb062a3d77f65ab))



* @applitools/core-base bumped to 1.29.0
  #### Features

  * restart cache and keepalive | FLD-3773 ([#3326](https://github.com/Applitools-Dev/sdk/issues/3326)) ([0fd12ca](https://github.com/Applitools-Dev/sdk/commit/0fd12ca703b4546560b563076a38f9ada24acc75))



* @applitools/socket bumped to 1.3.6

* @applitools/req bumped to 1.8.5

* @applitools/image bumped to 1.2.4

* @applitools/dom-capture bumped to 11.6.6
  #### Performance Improvements

  * remove dynamic loading of Dom capture and Dom snapshot ([#3322](https://github.com/Applitools-Dev/sdk/issues/3322)) ([7d15ee9](https://github.com/Applitools-Dev/sdk/commit/7d15ee98d5d39c7e478b6bfe3e14b8eea93937e5))



* @applitools/driver bumped to 1.24.1

* @applitools/spec-driver-webdriver bumped to 1.5.1

* @applitools/spec-driver-selenium bumped to 1.7.7

* @applitools/spec-driver-puppeteer bumped to 1.6.7

* @applitools/screenshoter bumped to 3.12.8

* @applitools/nml-client bumped to 1.11.10

* @applitools/tunnel-client bumped to 1.11.3

* @applitools/ufg-client bumped to 1.18.1

* @applitools/ec-client bumped to 1.12.12

* @applitools/core bumped to 4.52.0
  #### Features

  * restart cache and keepalive | FLD-3773 ([#3326](https://github.com/Applitools-Dev/sdk/issues/3326)) ([0fd12ca](https://github.com/Applitools-Dev/sdk/commit/0fd12ca703b4546560b563076a38f9ada24acc75))


  #### Performance Improvements

  * remove dynamic loading of Dom capture and Dom snapshot ([#3322](https://github.com/Applitools-Dev/sdk/issues/3322)) ([7d15ee9](https://github.com/Applitools-Dev/sdk/commit/7d15ee98d5d39c7e478b6bfe3e14b8eea93937e5))



* @applitools/test-server bumped to 1.3.4


## [4.51.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.50.4...python/core-universal@4.51.0) (2025-11-03)


### Dependencies

* @applitools/dom-snapshot bumped to 4.14.0
  #### Features

  * logging errors from dom snapshot to the backend | AD-11641 ([#3291](https://github.com/Applitools-Dev/sdk/issues/3291)) ([7f5b487](https://github.com/Applitools-Dev/sdk/commit/7f5b48701ff93bf980924c9346a8241ed87f5a56))


  #### Bug Fixes

  * sandbox prototype pollution | FLD-3738 ([#3310](https://github.com/Applitools-Dev/sdk/issues/3310)) ([3185558](https://github.com/Applitools-Dev/sdk/commit/31855586851d5372169aae7bf0268cec139abc59))


  #### Code Refactoring

  * blob generation error handling ([#2501](https://github.com/Applitools-Dev/sdk/issues/2501)) ([94bc14f](https://github.com/Applitools-Dev/sdk/commit/94bc14faf3de0fd9a8ca24af4870f839756a8aad))
* @applitools/ufg-client bumped to 1.18.0
  #### Features

  * logging errors from dom snapshot to the backend | AD-11641 ([#3291](https://github.com/Applitools-Dev/sdk/issues/3291)) ([7f5b487](https://github.com/Applitools-Dev/sdk/commit/7f5b48701ff93bf980924c9346a8241ed87f5a56))
* @applitools/core bumped to 4.51.0
  #### Features

  * logging errors from dom snapshot to the backend | AD-11641 ([#3291](https://github.com/Applitools-Dev/sdk/issues/3291)) ([7f5b487](https://github.com/Applitools-Dev/sdk/commit/7f5b48701ff93bf980924c9346a8241ed87f5a56))




## [4.50.4](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.50.3...python/core-universal@4.50.4) (2025-10-22)


### Dependencies

* @applitools/dom-snapshot bumped to 4.13.12
  #### Bug Fixes

  * upgrade from @applitools/css-tree fork to official css-tree v3.1.0 | AD-11642 ([#3286](https://github.com/Applitools-Dev/sdk/issues/3286)) ([187ac4b](https://github.com/Applitools-Dev/sdk/commit/187ac4bbca0921ed692b2a676200c6a967c0fb33))
* @applitools/ufg-client bumped to 1.17.5
  #### Bug Fixes

  * upgrade from @applitools/css-tree fork to official css-tree v3.1.0 | AD-11642 ([#3286](https://github.com/Applitools-Dev/sdk/issues/3286)) ([187ac4b](https://github.com/Applitools-Dev/sdk/commit/187ac4bbca0921ed692b2a676200c6a967c0fb33))
* @applitools/core bumped to 4.50.4
  #### Bug Fixes

  * upgrade from @applitools/css-tree fork to official css-tree v3.1.0 | AD-11642 ([#3286](https://github.com/Applitools-Dev/sdk/issues/3286)) ([187ac4b](https://github.com/Applitools-Dev/sdk/commit/187ac4bbca0921ed692b2a676200c6a967c0fb33))




## [4.50.3](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.50.2...python/core-universal@4.50.3) (2025-10-21)


### Dependencies

* @applitools/dom-snapshot bumped to 4.13.11
  #### Bug Fixes

  * don't throw on CSSNestedDeclarations |  AD-11640 ([#3284](https://github.com/Applitools-Dev/sdk/issues/3284)) ([d0a0f31](https://github.com/Applitools-Dev/sdk/commit/d0a0f31f6749cbe5b44f090c05af9da7676ad131))
* @applitools/core bumped to 4.50.3
  #### Bug Fixes

  * don't throw on CSSNestedDeclarations |  AD-11640 ([#3284](https://github.com/Applitools-Dev/sdk/issues/3284)) ([d0a0f31](https://github.com/Applitools-Dev/sdk/commit/d0a0f31f6749cbe5b44f090c05af9da7676ad131))




## [4.50.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.49.0...python/core-universal@4.50.2) (2025-10-16)


### Dependencies

* @applitools/dom-snapshot bumped to 4.13.10
  #### Bug Fixes

  * sandboxing | FLD-3482 ([#3274](https://github.com/Applitools-Dev/sdk/issues/3274)) ([b452cbf](https://github.com/Applitools-Dev/sdk/commit/b452cbf831907b04cd70624c0af655246ce580f1))



* @applitools/driver bumped to 1.24.0
  #### Features

  * use performActions (W3C) instead of touchPerform (MJSONWP) ([#3223](https://github.com/Applitools-Dev/sdk/issues/3223)) ([d4e5da8](https://github.com/Applitools-Dev/sdk/commit/d4e5da8dc19ad3c3f76de8e762be867970df3dd2))
* @applitools/spec-driver-webdriver bumped to 1.5.0
  #### Features

  * use performActions (W3C) instead of touchPerform (MJSONWP) ([#3223](https://github.com/Applitools-Dev/sdk/issues/3223)) ([d4e5da8](https://github.com/Applitools-Dev/sdk/commit/d4e5da8dc19ad3c3f76de8e762be867970df3dd2))



* @applitools/spec-driver-selenium bumped to 1.7.6

* @applitools/spec-driver-puppeteer bumped to 1.6.6

* @applitools/screenshoter bumped to 3.12.7

* @applitools/nml-client bumped to 1.11.9

* @applitools/ec-client bumped to 1.12.11

* @applitools/core bumped to 4.50.2
  #### Bug Fixes

  * missed verifying environments | AD-11225 ([#3256](https://github.com/Applitools-Dev/sdk/issues/3256)) ([e8a5d78](https://github.com/Applitools-Dev/sdk/commit/e8a5d78426422614fc776b3d32ff2c375b95be18))




## [4.49.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.48.0...python/core-universal@4.49.0) (2025-10-01)


### Dependencies

* @applitools/screenshoter bumped to 3.12.6
  #### Bug Fixes

  * wait after scroll | FLD-3594 ([#3252](https://github.com/Applitools-Dev/sdk/issues/3252)) ([e452422](https://github.com/Applitools-Dev/sdk/commit/e4524229b64e40d9b9596a92bfa94daf5824286a))
* @applitools/core-base bumped to 1.28.1
  #### Bug Fixes

  * unexpected concurrency values from server | AD-11465 ([#3248](https://github.com/Applitools-Dev/sdk/issues/3248)) ([0dd28c7](https://github.com/Applitools-Dev/sdk/commit/0dd28c7b297d5ad3aabc6b87e427e3e09a993825))
* @applitools/nml-client bumped to 1.11.7

* @applitools/ec-client bumped to 1.12.9

* @applitools/core bumped to 4.49.0
  #### Features

  * storybook addon ([#3104](https://github.com/Applitools-Dev/sdk/issues/3104)) ([16e09cb](https://github.com/Applitools-Dev/sdk/commit/16e09cba8928c3a24b9e0d9d41e0936fbaec2773))


  #### Bug Fixes

  * duplicate concurrency warnings ([#3255](https://github.com/Applitools-Dev/sdk/issues/3255)) ([ef2f94a](https://github.com/Applitools-Dev/sdk/commit/ef2f94ab4137c78396583f166344285beeb49be7))




## [4.48.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.47.1...python/core-universal@4.48.0) (2025-09-22)


### Dependencies

* @applitools/core-base bumped to 1.28.0
  #### Features

  * use concurrency from server | AD-10015 ([#3207](https://github.com/Applitools-Dev/sdk/issues/3207)) ([5336c9e](https://github.com/Applitools-Dev/sdk/commit/5336c9e6578a8f935b2b255344e7172beadeb551))
* @applitools/nml-client bumped to 1.11.6

* @applitools/ec-client bumped to 1.12.8

* @applitools/core bumped to 4.48.0
  #### Features

  * use concurrency from server | AD-10015 ([#3207](https://github.com/Applitools-Dev/sdk/issues/3207)) ([5336c9e](https://github.com/Applitools-Dev/sdk/commit/5336c9e6578a8f935b2b255344e7172beadeb551))




## [4.47.1](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.47.0...python/core-universal@4.47.1) (2025-09-16)


### Dependencies

* @applitools/logger bumped to 2.2.4
  #### Bug Fixes

  * remove duplicate tests on different sessions for same batch ([#3184](https://github.com/Applitools-Dev/sdk/issues/3184)) ([ede0d1f](https://github.com/Applitools-Dev/sdk/commit/ede0d1fd8018e14c19811903d78c273bce048f84))
* @applitools/dom-snapshot bumped to 4.13.7

* @applitools/socket bumped to 1.3.5

* @applitools/req bumped to 1.8.4

* @applitools/dom-capture bumped to 11.6.5

* @applitools/driver bumped to 1.23.5

* @applitools/spec-driver-webdriver bumped to 1.4.5

* @applitools/spec-driver-selenium bumped to 1.7.5

* @applitools/spec-driver-puppeteer bumped to 1.6.5

* @applitools/screenshoter bumped to 3.12.5

* @applitools/nml-client bumped to 1.11.5

* @applitools/tunnel-client bumped to 1.11.2

* @applitools/ufg-client bumped to 1.17.4

* @applitools/core-base bumped to 1.27.4

* @applitools/ec-client bumped to 1.12.7

* @applitools/core bumped to 4.47.1
  #### Bug Fixes

  * remove duplicate tests on different sessions for same batch ([#3184](https://github.com/Applitools-Dev/sdk/issues/3184)) ([ede0d1f](https://github.com/Applitools-Dev/sdk/commit/ede0d1fd8018e14c19811903d78c273bce048f84))



* @applitools/test-server bumped to 1.3.3


## [4.47.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.46.0...python/core-universal@4.47.0) (2025-09-15)


### Dependencies

* @applitools/core bumped to 4.47.0
  #### Features

  * update default concurrency ([#3230](https://github.com/Applitools-Dev/sdk/issues/3230)) ([f548cda](https://github.com/Applitools-Dev/sdk/commit/f548cda77d74b68890abc7c53f566b145e6484ba))

## [4.46.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.45.0...python/core-universal@4.46.0) (2025-09-09)


### Dependencies

* @applitools/utils bumped to 1.12.0
  #### Features

  * enable canvas with webgl for autonomous | FLD 3515 ([#3197](https://github.com/Applitools-Dev/sdk/issues/3197)) ([23f22e5](https://github.com/Applitools-Dev/sdk/commit/23f22e517d52dc70f24093dfb21e072b9aa9fb60))
* @applitools/logger bumped to 2.2.3

* @applitools/dom-snapshot bumped to 4.13.6

* @applitools/socket bumped to 1.3.4

* @applitools/req bumped to 1.8.3

* @applitools/image bumped to 1.2.3

* @applitools/dom-capture bumped to 11.6.4

* @applitools/driver bumped to 1.23.4

* @applitools/spec-driver-webdriver bumped to 1.4.4

* @applitools/spec-driver-selenium bumped to 1.7.4

* @applitools/spec-driver-puppeteer bumped to 1.6.4

* @applitools/screenshoter bumped to 3.12.4

* @applitools/nml-client bumped to 1.11.4

* @applitools/tunnel-client bumped to 1.11.1

* @applitools/ufg-client bumped to 1.17.3

* @applitools/core-base bumped to 1.27.3

* @applitools/ec-client bumped to 1.12.6

* @applitools/core bumped to 4.46.0
  #### Features

  * enable canvas with webgl for autonomous | FLD 3515 ([#3197](https://github.com/Applitools-Dev/sdk/issues/3197)) ([23f22e5](https://github.com/Applitools-Dev/sdk/commit/23f22e517d52dc70f24093dfb21e072b9aa9fb60))


  #### Bug Fixes

  * update offline test fixtures to use Google Fonts v12 ([#3215](https://github.com/Applitools-Dev/sdk/issues/3215)) ([ba8ef0c](https://github.com/Applitools-Dev/sdk/commit/ba8ef0c3b11a7f5e9e59a58f29fd5d60760a68ee))



* @applitools/test-server bumped to 1.3.2


## [4.45.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.44.5...python/core-universal@4.45.0) (2025-09-04)


### Dependencies

* @applitools/dom-shared bumped to 1.1.1
  #### Code Refactoring

  * dom shared js -&gt; ts ([#3202](https://github.com/Applitools-Dev/sdk/issues/3202)) ([c6d6b77](https://github.com/Applitools-Dev/sdk/commit/c6d6b77179d48539cc40f609f150f380aa48d6bb))
* @applitools/dom-snapshot bumped to 4.13.5

* @applitools/dom-capture bumped to 11.6.3

* @applitools/tunnel-client bumped to 1.11.0
  #### Features

  * mask apiKey and eyesServerUrl from the logs | AD-10661 ([#3200](https://github.com/Applitools-Dev/sdk/issues/3200)) ([eaba565](https://github.com/Applitools-Dev/sdk/commit/eaba565898d8e72745a1e95c9b17ae77c396ca14))
  * report to coralogix | AD-10945 ([#3191](https://github.com/Applitools-Dev/sdk/issues/3191)) ([2f57db1](https://github.com/Applitools-Dev/sdk/commit/2f57db162db4d3dbe4cdab06096f0d183af94946))
* @applitools/ec-client bumped to 1.12.5

* @applitools/core bumped to 4.45.0
  #### Features

  * respect NO_PROXY for WebDriver | AD-10927 | FLD-2702 ([#3186](https://github.com/Applitools-Dev/sdk/issues/3186)) ([8e53d9a](https://github.com/Applitools-Dev/sdk/commit/8e53d9a7c1b6fe38c11d63fad915fc89b199a749))




## [4.44.5](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.44.2...python/core-universal@4.44.5) (2025-08-27)


### Dependencies

* @applitools/dom-snapshot bumped to 4.13.4
  #### Bug Fixes

  * canvas blob ([#3194](https://github.com/Applitools-Dev/sdk/issues/3194)) ([d90cfca](https://github.com/Applitools-Dev/sdk/commit/d90cfcaa78df93d4bd8992d77f41eb93edd56f4c))
  * canvas blobs ([#3192](https://github.com/Applitools-Dev/sdk/issues/3192)) ([f15ac4e](https://github.com/Applitools-Dev/sdk/commit/f15ac4ed68cc1746ee6cef51f2258388428fd1c7))
* @applitools/core bumped to 4.44.5
  #### Bug Fixes

  * browser extension | FLD-3221 ([#3185](https://github.com/Applitools-Dev/sdk/issues/3185)) ([8212155](https://github.com/Applitools-Dev/sdk/commit/8212155e51ce919beb3bcecc7da1970da4a65be7))




## [4.44.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.43.0...python/core-universal@4.44.2) (2025-08-05)


### Features

* release java ([7bc39e6](https://github.com/Applitools-Dev/sdk/commit/7bc39e679eab27a19322ca4b121177da7437c106))


### Dependencies

* @applitools/utils bumped to 1.11.0
  #### Features

  * improve configuration handling ([#3130](https://github.com/Applitools-Dev/sdk/issues/3130)) ([def7be1](https://github.com/Applitools-Dev/sdk/commit/def7be1dd07460f49142cddfe55203baa884e6c3))
  * make utils.general.guid crypto secured ([#3137](https://github.com/Applitools-Dev/sdk/issues/3137)) ([775df08](https://github.com/Applitools-Dev/sdk/commit/775df08307e41402a6603812205bc857bd3f936e))
* @applitools/test-server bumped to 1.3.0
  #### Features

  * release java ([7bc39e6](https://github.com/Applitools-Dev/sdk/commit/7bc39e679eab27a19322ca4b121177da7437c106))



* @applitools/logger bumped to 2.2.1

* @applitools/dom-snapshot bumped to 4.13.1

* @applitools/socket bumped to 1.3.1

* @applitools/req bumped to 1.8.1

* @applitools/image bumped to 1.2.1

* @applitools/dom-capture bumped to 11.6.1

* @applitools/driver bumped to 1.23.1

* @applitools/spec-driver-webdriver bumped to 1.4.1

* @applitools/spec-driver-selenium bumped to 1.7.1

* @applitools/spec-driver-puppeteer bumped to 1.6.1

* @applitools/screenshoter bumped to 3.12.1

* @applitools/nml-client bumped to 1.11.1

* @applitools/tunnel-client bumped to 1.10.2

* @applitools/ufg-client bumped to 1.17.1

* @applitools/core-base bumped to 1.27.1

* @applitools/ec-client bumped to 1.12.2

* @applitools/core bumped to 4.44.2


## [4.43.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.38.0...python/core-universal@4.43.0) (2025-07-23)


### Dependencies

* @applitools/nml-client bumped to 1.10.0
  #### Features

  * android multi target | AD-9868 ([#2943](https://github.com/Applitools-Dev/sdk/issues/2943)) ([808aa21](https://github.com/Applitools-Dev/sdk/commit/808aa21e489c3562b93006e2e26ff7ffbb743dd6))



* @applitools/core-base bumped to 1.26.0
  #### Features

  * batch properties limit | FLD-3174 ([#3080](https://github.com/Applitools-Dev/sdk/issues/3080)) ([feb9e79](https://github.com/Applitools-Dev/sdk/commit/feb9e79d79f5eab3c58eac2b4ef3c15a562f079c))
* @applitools/ec-client bumped to 1.11.1

* @applitools/core bumped to 4.43.0
  #### Features

  * android multi target | AD-9868 ([#2943](https://github.com/Applitools-Dev/sdk/issues/2943)) ([808aa21](https://github.com/Applitools-Dev/sdk/commit/808aa21e489c3562b93006e2e26ff7ffbb743dd6))
  * batch properties limit | FLD-3174 ([#3080](https://github.com/Applitools-Dev/sdk/issues/3080)) ([feb9e79](https://github.com/Applitools-Dev/sdk/commit/feb9e79d79f5eab3c58eac2b4ef3c15a562f079c))




## [4.38.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.37.0...python/core-universal@4.38.0) (2025-05-22)


### Features

* adding the mac-arm64 binary ([#2975](https://github.com/Applitools-Dev/sdk/issues/2975)) ([95d647f](https://github.com/Applitools-Dev/sdk/commit/95d647ff4a451309d985a786f7cec544d926f0e5))

## [4.37.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.35.1...python/core-universal@4.37.0) (2025-04-17)


### Performance Improvements

* cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))


### Dependencies

* @applitools/dom-snapshot bumped to 4.11.18
  #### Bug Fixes

  * simplify sandbox creation and ensure cleanup after execution ([#2869](https://github.com/Applitools-Dev/sdk/issues/2869)) ([72c5e01](https://github.com/Applitools-Dev/sdk/commit/72c5e01307f6abd83fab365a7e235124caae0694))



* @applitools/snippets bumped to 2.6.5
  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))
* @applitools/driver bumped to 1.21.1
  #### Bug Fixes

  * executePoll error logging FLD-2870 ([#2890](https://github.com/Applitools-Dev/sdk/issues/2890)) ([a8ff720](https://github.com/Applitools-Dev/sdk/commit/a8ff720efafacabe2023282748a6d8a0f1b3ff73))



* @applitools/spec-driver-webdriver bumped to 1.2.2
  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))



* @applitools/spec-driver-selenium bumped to 1.5.98
  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))



* @applitools/spec-driver-puppeteer bumped to 1.4.27
  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))



* @applitools/screenshoter bumped to 3.11.1
  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))



* @applitools/nml-client bumped to 1.9.1
  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))



* @applitools/tunnel-client bumped to 1.6.5
  #### Bug Fixes

  * enhance error messages in tunnel client ([cab26e6](https://github.com/Applitools-Dev/sdk/commit/cab26e6e3d56fa3cbabaa1a9c68de13046b8f57e))
* @applitools/ufg-client bumped to 1.16.9
  #### Bug Fixes

  * basic auth protected resources | FLD-2761 | FMRI-120 ([#2444](https://github.com/Applitools-Dev/sdk/issues/2444)) ([b48cf49](https://github.com/Applitools-Dev/sdk/commit/b48cf49dec50bbf1ed2ba111608a48cf09962565))


  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))
* @applitools/ec-client bumped to 1.10.9
  #### Performance Improvements

  * cachify http agent ([#2466](https://github.com/Applitools-Dev/sdk/issues/2466)) ([bc2f4a1](https://github.com/Applitools-Dev/sdk/commit/bc2f4a1fae3c379f061c9199edf4c5257769fb44))



* @applitools/core bumped to 4.37.0
  #### Features

  * height layout breakpoints ([#2801](https://github.com/Applitools-Dev/sdk/issues/2801)) ([819e241](https://github.com/Applitools-Dev/sdk/commit/819e2418f1fd93220a07dfbcf1157ffcf4995dd7))




## [4.35.1](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.33.0...python/core-universal@4.35.1) (2025-04-03)


### Dependencies

* @applitools/core bumped to 4.35.1
  #### Bug Fixes

  * dummy ([9b8ffef](https://github.com/Applitools-Dev/sdk/commit/9b8ffef6277015a9073caf50f5dc5741986fbf07))

## [4.33.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.32.2...python/core-universal@4.33.0) (2025-03-26)


### Dependencies

* @applitools/core bumped to 4.33.0
  ### Features

  * support HTTPS_PROXY and HTTP_PROXY environment variables ([#2795](https://github.com/Applitools-Dev/sdk/issues/2795)) ([226ae08](https://github.com/Applitools-Dev/sdk/commit/226ae08627381a1212df8b938c6576e82c777914))


## [4.32.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.31.0...python/core-universal@4.32.2) (2025-03-06)


### Dependencies

* @applitools/core bumped to 4.32.2
  #### Bug Fixes

  * add environment variable aliases (_NAME suffix) ([#2791](https://github.com/Applitools-Dev/sdk/issues/2791)) ([67501a4](https://github.com/Applitools-Dev/sdk/commit/67501a4f5491319ca62949a56ee03face08a59e5))
  * support test concurrency in offline mode ([#2831](https://github.com/Applitools-Dev/sdk/issues/2831)) ([3b7d137](https://github.com/Applitools-Dev/sdk/commit/3b7d137a9b34bb5c564e0a5c7d3fb2520ef8a167))


## [4.31.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.29.1...python/core-universal@4.31.0) (2025-01-30)


### Dependencies

* @applitools/dom-snapshot bumped to 4.11.15

* @applitools/driver bumped to 1.20.4
  #### Bug Fixes

  * handle device screen info extraction gracefully ([#2757](https://github.com/Applitools-Dev/sdk/issues/2757)) ([92d0118](https://github.com/Applitools-Dev/sdk/commit/92d0118137b77e49d780092d110973df8ed8b40c))
* @applitools/spec-driver-webdriver bumped to 1.1.25

* @applitools/spec-driver-selenium bumped to 1.5.95

* @applitools/spec-driver-puppeteer bumped to 1.4.24

* @applitools/screenshoter bumped to 3.10.5

* @applitools/nml-client bumped to 1.8.24

* @applitools/ufg-client bumped to 1.16.3
  #### Bug Fixes

  * unthrottle renders in offline mode ([#2754](https://github.com/Applitools-Dev/sdk/issues/2754)) ([b65d816](https://github.com/Applitools-Dev/sdk/commit/b65d81610504ae725b7b52611282a1bb28a049fe))
* @applitools/ec-client bumped to 1.10.3

* @applitools/core bumped to 4.31.0
  #### Features

  * remove iPhoneX from list of available UFG Safari devices ([#2756](https://github.com/Applitools-Dev/sdk/issues/2756)) ([e24d054](https://github.com/Applitools-Dev/sdk/commit/e24d054328df900fbc4988fdbf8213aadffa9a37))


  #### Bug Fixes

  * handle device screen info extraction gracefully ([#2757](https://github.com/Applitools-Dev/sdk/issues/2757)) ([92d0118](https://github.com/Applitools-Dev/sdk/commit/92d0118137b77e49d780092d110973df8ed8b40c))
  * unthrottle renders in offline mode ([#2754](https://github.com/Applitools-Dev/sdk/issues/2754)) ([b65d816](https://github.com/Applitools-Dev/sdk/commit/b65d81610504ae725b7b52611282a1bb28a049fe))




## [4.29.1](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.28.0...python/core-universal@4.29.1) (2025-01-19)


### Dependencies

* @applitools/socket bumped to 1.2.1
  #### Bug Fixes

  * mask from config property ([#2739](https://github.com/Applitools-Dev/sdk/issues/2739)) ([6840624](https://github.com/Applitools-Dev/sdk/commit/6840624f5f3f56512dce96547815904adec94704))
* @applitools/req bumped to 1.7.7
  #### Bug Fixes

  * memory usage going high when resource is uint8array ([#2743](https://github.com/Applitools-Dev/sdk/issues/2743)) ([d06deeb](https://github.com/Applitools-Dev/sdk/commit/d06deeb845de62e96ec623efefa90ae65a703736))
* @applitools/spec-driver-webdriver bumped to 1.1.24
  #### Bug Fixes

  * universal core on windows ([#2736](https://github.com/Applitools-Dev/sdk/issues/2736)) ([9bd0744](https://github.com/Applitools-Dev/sdk/commit/9bd0744ca816a020973f20645aeb2460af76f44c))
* @applitools/tunnel-client bumped to 1.6.1
  #### Bug Fixes

  * memory usage going high when resource is uint8array ([#2743](https://github.com/Applitools-Dev/sdk/issues/2743)) ([d06deeb](https://github.com/Applitools-Dev/sdk/commit/d06deeb845de62e96ec623efefa90ae65a703736))



* @applitools/screenshoter bumped to 3.10.4

* @applitools/nml-client bumped to 1.8.23

* @applitools/ufg-client bumped to 1.16.1
  #### Bug Fixes

  * memory usage going high when resource is uint8array ([#2743](https://github.com/Applitools-Dev/sdk/issues/2743)) ([d06deeb](https://github.com/Applitools-Dev/sdk/commit/d06deeb845de62e96ec623efefa90ae65a703736))



* @applitools/core-base bumped to 1.22.1

* @applitools/ec-client bumped to 1.10.2

* @applitools/core bumped to 4.29.1
  #### Bug Fixes

  * mask from config property ([#2739](https://github.com/Applitools-Dev/sdk/issues/2739)) ([6840624](https://github.com/Applitools-Dev/sdk/commit/6840624f5f3f56512dce96547815904adec94704))
  * universal core on windows ([#2736](https://github.com/Applitools-Dev/sdk/issues/2736)) ([9bd0744](https://github.com/Applitools-Dev/sdk/commit/9bd0744ca816a020973f20645aeb2460af76f44c))




## [4.28.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.24.2...python/core-universal@4.28.0) (2024-12-31)


### Features

* logger masking  ([#2640](https://github.com/Applitools-Dev/sdk/issues/2640)) ([bd69d21](https://github.com/Applitools-Dev/sdk/commit/bd69d21f6341447b1acdb042f4ee1a6328d7428f))


### Dependencies

* @applitools/utils bumped to 1.7.7
  #### Bug Fixes

  * shim process execution functions for browser environment ([#2698](https://github.com/Applitools-Dev/sdk/issues/2698)) ([8d77db4](https://github.com/Applitools-Dev/sdk/commit/8d77db48e1c7fd54cad92c89a819a924255e5868))
* @applitools/logger bumped to 2.1.0
  #### Features

  * logger masking  ([#2640](https://github.com/Applitools-Dev/sdk/issues/2640)) ([bd69d21](https://github.com/Applitools-Dev/sdk/commit/bd69d21f6341447b1acdb042f4ee1a6328d7428f))



* @applitools/dom-snapshot bumped to 4.11.13
  #### Bug Fixes

  * code scanning issue ([#2687](https://github.com/Applitools-Dev/sdk/issues/2687)) ([f301056](https://github.com/Applitools-Dev/sdk/commit/f301056cccfc9cc0c21ceedbd521d8f4b054f058))



* @applitools/socket bumped to 1.2.0
  #### Features

  * logger masking  ([#2640](https://github.com/Applitools-Dev/sdk/issues/2640)) ([bd69d21](https://github.com/Applitools-Dev/sdk/commit/bd69d21f6341447b1acdb042f4ee1a6328d7428f))



* @applitools/core-base bumped to 1.22.0
  #### Features

  * deterministic output in offline execution ([#2711](https://github.com/Applitools-Dev/sdk/issues/2711)) ([5e8c7ca](https://github.com/Applitools-Dev/sdk/commit/5e8c7ca43c98e7ba6aed0c1a66c5a60b4001aeff))
  * logger masking  ([#2640](https://github.com/Applitools-Dev/sdk/issues/2640)) ([bd69d21](https://github.com/Applitools-Dev/sdk/commit/bd69d21f6341447b1acdb042f4ee1a6328d7428f))



* @applitools/req bumped to 1.7.6

* @applitools/image bumped to 1.1.16

* @applitools/dom-capture bumped to 11.5.3
  #### Bug Fixes

  * code scanning issue ([#2687](https://github.com/Applitools-Dev/sdk/issues/2687)) ([f301056](https://github.com/Applitools-Dev/sdk/commit/f301056cccfc9cc0c21ceedbd521d8f4b054f058))
* @applitools/driver bumped to 1.20.2

* @applitools/spec-driver-puppeteer bumped to 1.4.22

* @applitools/tunnel-client bumped to 1.6.0
  #### Features

  * logger masking  ([#2640](https://github.com/Applitools-Dev/sdk/issues/2640)) ([bd69d21](https://github.com/Applitools-Dev/sdk/commit/bd69d21f6341447b1acdb042f4ee1a6328d7428f))



* @applitools/ec-client bumped to 1.10.0
  #### Features

  * logger masking  ([#2640](https://github.com/Applitools-Dev/sdk/issues/2640)) ([bd69d21](https://github.com/Applitools-Dev/sdk/commit/bd69d21f6341447b1acdb042f4ee1a6328d7428f))



* @applitools/spec-driver-webdriver bumped to 1.1.22

* @applitools/spec-driver-selenium bumped to 1.5.93

* @applitools/screenshoter bumped to 3.10.2

* @applitools/nml-client bumped to 1.8.21

* @applitools/ufg-client bumped to 1.16.0
  #### Features

  * deterministic output in offline execution ([#2711](https://github.com/Applitools-Dev/sdk/issues/2711)) ([5e8c7ca](https://github.com/Applitools-Dev/sdk/commit/5e8c7ca43c98e7ba6aed0c1a66c5a60b4001aeff))


  #### Bug Fixes

  * code scanning issue ([#2687](https://github.com/Applitools-Dev/sdk/issues/2687)) ([f301056](https://github.com/Applitools-Dev/sdk/commit/f301056cccfc9cc0c21ceedbd521d8f4b054f058))



* @applitools/core bumped to 4.28.0
  #### Features

  * deterministic output in offline execution ([#2711](https://github.com/Applitools-Dev/sdk/issues/2711)) ([5e8c7ca](https://github.com/Applitools-Dev/sdk/commit/5e8c7ca43c98e7ba6aed0c1a66c5a60b4001aeff))
  * logger masking  ([#2640](https://github.com/Applitools-Dev/sdk/issues/2640)) ([bd69d21](https://github.com/Applitools-Dev/sdk/commit/bd69d21f6341447b1acdb042f4ee1a6328d7428f))


  #### Bug Fixes

  * take snapshots with coded regions on pages that has cross origin frames ([#2705](https://github.com/Applitools-Dev/sdk/issues/2705)) ([5972fec](https://github.com/Applitools-Dev/sdk/commit/5972fec890a1454a9f96c4eddcf17634e72111aa))




## [4.24.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.21.2...python/core-universal@4.24.2) (2024-11-27)


### Dependencies

* @applitools/dom-shared bumped to 1.0.16
  #### Bug Fixes

  * enhance error logging in takeScreenshots and pollify functions ([#2644](https://github.com/Applitools-Dev/sdk/issues/2644)) ([2428fa5](https://github.com/Applitools-Dev/sdk/commit/2428fa500a9fd47a803aa5aca9f79e5c5b3584f9))
* @applitools/req bumped to 1.7.4
  #### Bug Fixes

  * set heartbeat request timeout as the request interval ([#2587](https://github.com/Applitools-Dev/sdk/issues/2587)) ([0251d27](https://github.com/Applitools-Dev/sdk/commit/0251d27d9ed44ec247732f66904ae3d4fa4123f1))
* @applitools/core-base bumped to 1.19.3
  #### Bug Fixes

  * set heartbeat request timeout as the request interval ([#2587](https://github.com/Applitools-Dev/sdk/issues/2587)) ([0251d27](https://github.com/Applitools-Dev/sdk/commit/0251d27d9ed44ec247732f66904ae3d4fa4123f1))



* @applitools/dom-snapshot bumped to 4.11.11

* @applitools/dom-capture bumped to 11.5.2

* @applitools/nml-client bumped to 1.8.19

* @applitools/tunnel-client bumped to 1.5.10

* @applitools/ufg-client bumped to 1.14.1

* @applitools/ec-client bumped to 1.9.15

* @applitools/core bumped to 4.24.2
  #### Bug Fixes

  * don't populate branchName and parentBranchName when scm integration exists ([#2634](https://github.com/Applitools-Dev/sdk/issues/2634)) ([e45d671](https://github.com/Applitools-Dev/sdk/commit/e45d671e11ed40a82de1bd5ab22e757aff00b63f))
  * enhance error logging in takeScreenshots and pollify functions ([#2644](https://github.com/Applitools-Dev/sdk/issues/2644)) ([2428fa5](https://github.com/Applitools-Dev/sdk/commit/2428fa500a9fd47a803aa5aca9f79e5c5b3584f9))




## [4.21.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.21.0...python/core-universal@4.21.2) (2024-10-29)


### Dependencies

* @applitools/screenshoter bumped to 3.9.2
  #### Bug Fixes

  * test in screenshoter web ([f068dbe](https://github.com/Applitools-Dev/sdk/commit/f068dbe9036163fb3e316411cfd9f47a226d7c9c))
* @applitools/core bumped to 4.21.2


## [4.21.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.18.2...python/core-universal@4.21.0) (2024-10-21)


### Dependencies

* @applitools/snippets bumped to 2.5.1
  #### Bug Fixes

  * isStaleElement error ([#2567](https://github.com/Applitools-Dev/sdk/issues/2567)) ([2675086](https://github.com/Applitools-Dev/sdk/commit/2675086aa28589082249e2958942ee29a5f2ef12))
* @applitools/core-base bumped to 1.18.0
  #### Features

  * ability to download side by side with highlighted diffs (2419) ([#2530](https://github.com/Applitools-Dev/sdk/issues/2530)) ([e06ce69](https://github.com/Applitools-Dev/sdk/commit/e06ce699f30e9e444ac58dafdf5989ff1c96ca1c))
  * dynamic regions ([#2538](https://github.com/Applitools-Dev/sdk/issues/2538)) ([d8b5c48](https://github.com/Applitools-Dev/sdk/commit/d8b5c48fb35f9789c702447314dc72b4f415ade1))
  * setting up SCM information automatically ([#2542](https://github.com/Applitools-Dev/sdk/issues/2542)) ([696461a](https://github.com/Applitools-Dev/sdk/commit/696461af3f8e2e3ed94eb78fed5ead6233bd16b2))
* @applitools/driver bumped to 1.19.3

* @applitools/spec-driver-webdriver bumped to 1.1.15

* @applitools/spec-driver-selenium bumped to 1.5.86

* @applitools/spec-driver-puppeteer bumped to 1.4.15

* @applitools/screenshoter bumped to 3.9.0
  #### Features

  * capture status bar ([#2571](https://github.com/Applitools-Dev/sdk/issues/2571)) ([5e1c75e](https://github.com/Applitools-Dev/sdk/commit/5e1c75ef9cf34af80f08806a3bceaf06a94f2780))



* @applitools/nml-client bumped to 1.8.13

* @applitools/ec-client bumped to 1.9.9

* @applitools/core bumped to 4.21.0
  #### Features

  * add chrome emulation devices ([#2559](https://github.com/Applitools-Dev/sdk/issues/2559)) ([0499aaf](https://github.com/Applitools-Dev/sdk/commit/0499aaf3bb809d2ac0105b4493e6f6bb8730ea3f))
  * capture status bar ([#2571](https://github.com/Applitools-Dev/sdk/issues/2571)) ([5e1c75e](https://github.com/Applitools-Dev/sdk/commit/5e1c75ef9cf34af80f08806a3bceaf06a94f2780))
  * dynamic regions ([#2538](https://github.com/Applitools-Dev/sdk/issues/2538)) ([d8b5c48](https://github.com/Applitools-Dev/sdk/commit/d8b5c48fb35f9789c702447314dc72b4f415ade1))
  * setting up SCM information automatically ([#2542](https://github.com/Applitools-Dev/sdk/issues/2542)) ([696461a](https://github.com/Applitools-Dev/sdk/commit/696461af3f8e2e3ed94eb78fed5ead6233bd16b2))


  #### Bug Fixes

  * don't remove offline execution folder after running ([654e195](https://github.com/Applitools-Dev/sdk/commit/654e195dd50dc7dab93dd907ec26d788549c6e81))




## [4.18.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.18.0...python/core-universal@4.18.2) (2024-09-10)


### Dependencies

* @applitools/dom-capture bumped to 11.4.0
  #### Features

  * ability to capture all css props in computed style ([#2484](https://github.com/Applitools-Dev/sdk/issues/2484)) ([8769ee5](https://github.com/Applitools-Dev/sdk/commit/8769ee566f2d9e163437c7bcd385ec993f05f370))
* @applitools/driver bumped to 1.19.0
  #### Features

  * add support for env var APPLITOOLS_IS_IC ([#2469](https://github.com/Applitools-Dev/sdk/issues/2469)) ([87d7b5c](https://github.com/Applitools-Dev/sdk/commit/87d7b5cc1f7ea774c6b90504e85296f0681d0b1e))


  #### Bug Fixes

  * handle userAgent.brands returned as string ([#2453](https://github.com/Applitools-Dev/sdk/issues/2453)) ([dd6328b](https://github.com/Applitools-Dev/sdk/commit/dd6328be3e7d885714124a8e43aabaae3abecde9))
  * searching for scrollable element multiple times ([#2493](https://github.com/Applitools-Dev/sdk/issues/2493)) ([d98db80](https://github.com/Applitools-Dev/sdk/commit/d98db8016c6312f467f244444c6f1a87bc09b7da))
* @applitools/tunnel-client bumped to 1.5.8
  #### Bug Fixes

  * upgrade execution-grid-tunnel ([#2475](https://github.com/Applitools-Dev/sdk/issues/2475)) ([e5952b4](https://github.com/Applitools-Dev/sdk/commit/e5952b4ca1bd0c065111ce1109b218f1fd68f6fc))



* @applitools/core-base bumped to 1.16.1
  #### Bug Fixes

  * infinity concurrency ([#2477](https://github.com/Applitools-Dev/sdk/issues/2477)) ([f488e16](https://github.com/Applitools-Dev/sdk/commit/f488e162f124acc249ed7b43b714f13c18306dc8))
* @applitools/spec-driver-webdriver bumped to 1.1.12

* @applitools/spec-driver-selenium bumped to 1.5.83

* @applitools/spec-driver-puppeteer bumped to 1.4.12

* @applitools/screenshoter bumped to 3.8.36

* @applitools/nml-client bumped to 1.8.10

* @applitools/ec-client bumped to 1.9.4

* @applitools/core bumped to 4.18.2
  #### Bug Fixes

  * don't call check-network when executing binary and cli ([#2491](https://github.com/Applitools-Dev/sdk/issues/2491)) ([ef00d20](https://github.com/Applitools-Dev/sdk/commit/ef00d205450b7bbe7abc1bc9bce8d6970f769091))




## [4.18.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal-v4.16.5...python/core-universal@4.18.0) (2024-07-23)


### Bug Fixes

* trigger js core, python, ruby, dotnet release ([f072fd2](https://github.com/Applitools-Dev/sdk/commit/f072fd219aeb095e6caa94eed42d5ffb9b14f483))
* trigger python and dotnet release ([ce35c60](https://github.com/Applitools-Dev/sdk/commit/ce35c60afd5b98a4cb40342da67063bec2299407))
* trigger python,ruby,dotnet release ([14cb160](https://github.com/Applitools-Dev/sdk/commit/14cb160b3559fbc838261fb51cafb228dd213374))
* trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))
* trigger release for python,ruby,dotnet ([8b3b316](https://github.com/Applitools-Dev/sdk/commit/8b3b3167bbf9f9069176cb597991693a06b5328e))
* trigger ruby,python,dotnet release ([9326ee0](https://github.com/Applitools-Dev/sdk/commit/9326ee0f0e1a21a9be262893f77b5d19646da64a))


### Dependencies

* @applitools/driver bumped to 1.18.0
  #### Features

  * disable broker url cache ([#2428](https://github.com/Applitools-Dev/sdk/issues/2428)) ([cb8d5fe](https://github.com/Applitools-Dev/sdk/commit/cb8d5fefb13d3ab42984d2bd4d4ac3d4e10646b0))


  #### Bug Fixes

  * executing web script on mobile environment ([#2380](https://github.com/Applitools-Dev/sdk/issues/2380)) ([da2e551](https://github.com/Applitools-Dev/sdk/commit/da2e551e01082d3cc21b9da5b43e6680233c080d))
* @applitools/spec-driver-webdriver bumped to 1.1.11

* @applitools/spec-driver-selenium bumped to 1.5.82

* @applitools/screenshoter bumped to 3.8.35

* @applitools/ufg-client bumped to 1.12.3
  #### Bug Fixes

  * update makeUploadResource to include apiKey in the cache key ([#2411](https://github.com/Applitools-Dev/sdk/issues/2411)) ([4114c58](https://github.com/Applitools-Dev/sdk/commit/4114c58ec16fa855374b23810cef1e36d4bb53a7))


  #### Performance Improvements

  * trim file content when logging it ([#2437](https://github.com/Applitools-Dev/sdk/issues/2437)) ([02ec1f7](https://github.com/Applitools-Dev/sdk/commit/02ec1f79a323af2e89a7428b75212707c761d1ca))
* @applitools/spec-driver-puppeteer bumped to 1.4.11

* @applitools/nml-client bumped to 1.8.9

* @applitools/ec-client bumped to 1.9.3

* @applitools/core bumped to 4.18.0
  #### Features

  * disable broker url cache ([#2428](https://github.com/Applitools-Dev/sdk/issues/2428)) ([cb8d5fe](https://github.com/Applitools-Dev/sdk/commit/cb8d5fefb13d3ab42984d2bd4d4ac3d4e10646b0))




## [4.16.5](https://github.com/Applitools-Dev/sdk/compare/js/core@4.16.4...js/core@4.16.5) (2024-06-16)


### Dependencies

* @applitools/tunnel-client bumped to 1.5.6
  #### Bug Fixes

  * tunnel client ([6830f02](https://github.com/Applitools-Dev/sdk/commit/6830f02c988e07c1c1ce257a84467f234149fc05))
* @applitools/ec-client bumped to 1.9.1


## [4.16.4](https://github.com/Applitools-Dev/sdk/compare/js/core@4.16.3...js/core@4.16.4) (2024-06-16)


### Dependencies

* @applitools/tunnel-client bumped to 1.5.5
  #### Bug Fixes

  * update tunnel to 3.0.5 ([#2394](https://github.com/Applitools-Dev/sdk/issues/2394)) ([cdd7f90](https://github.com/Applitools-Dev/sdk/commit/cdd7f90416bf0e29b216a29789e7dbbc9c5d1e0d))
* @applitools/ec-client bumped to 1.9.0
  #### Features

  * support findElements self healing ([#2387](https://github.com/Applitools-Dev/sdk/issues/2387)) ([57521e2](https://github.com/Applitools-Dev/sdk/commit/57521e273cf2a836a822baafbb88f342358e3ac2))




## [4.16.3](https://github.com/Applitools-Dev/sdk/compare/js/core@4.16.2...js/core@4.16.3) (2024-06-11)


### Bug Fixes

* cache nml client per driver session ([#2368](https://github.com/Applitools-Dev/sdk/issues/2368)) ([5840389](https://github.com/Applitools-Dev/sdk/commit/5840389f74111c0e0e68026389c755c59a027b74))


### Dependencies

* @applitools/spec-driver-webdriver bumped to 1.1.9

* @applitools/spec-driver-selenium bumped to 1.5.80

* @applitools/spec-driver-puppeteer bumped to 1.4.9

* @applitools/driver bumped to 1.17.4
  #### Bug Fixes

  * cache nml client per driver session ([#2368](https://github.com/Applitools-Dev/sdk/issues/2368)) ([5840389](https://github.com/Applitools-Dev/sdk/commit/5840389f74111c0e0e68026389c755c59a027b74))
* @applitools/screenshoter bumped to 3.8.33

* @applitools/nml-client bumped to 1.8.7

* @applitools/ec-client bumped to 1.8.9
  #### Bug Fixes

  * shadow dom self healing ([#2375](https://github.com/Applitools-Dev/sdk/issues/2375)) ([4d3a88c](https://github.com/Applitools-Dev/sdk/commit/4d3a88cbc3e05c3dd317afbb5de8d677368c346d))




## [4.16.2](https://github.com/Applitools-Dev/sdk/compare/js/core@4.16.1...js/core@4.16.2) (2024-06-01)


### Bug Fixes

* trigger ([1da3548](https://github.com/Applitools-Dev/sdk/commit/1da35489ccb0340706c9d226154da0b80f298dfa))
* trigger core release ([33551bc](https://github.com/Applitools-Dev/sdk/commit/33551bc5ff20eb18716060388afab349c6860c42))
* trigger js/core, dotnet and java release ([5f520f7](https://github.com/Applitools-Dev/sdk/commit/5f520f7f8f48b33a7ef065aa9cbda8fc2fc0971f))


### Dependencies

* @applitools/ec-client bumped to 1.8.8

* @applitools/core-base bumped to 1.15.2
  #### Bug Fixes

  * send proper request body to checkAndClose endpoint ([c6524bf](https://github.com/Applitools-Dev/sdk/commit/c6524bfd0f621f6943ff8a08de1148ce92d6c650))




## [4.16.1](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.16.0...python/core-universal@4.16.1) (2024-05-28)


### Bug Fixes

* trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))


### Dependencies

* @applitools/utils bumped to 1.7.3
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))
* @applitools/logger bumped to 2.0.17
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/socket bumped to 1.1.17
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/req bumped to 1.7.1
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/image bumped to 1.1.12
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/snippets bumped to 2.4.26
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))
* @applitools/css-tree bumped to 1.1.3
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))
* @applitools/dom-shared bumped to 1.0.14
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))
* @applitools/dom-capture bumped to 11.2.8
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/dom-snapshot bumped to 4.11.2
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/spec-driver-webdriver bumped to 1.1.8
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/spec-driver-selenium bumped to 1.5.79
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/spec-driver-puppeteer bumped to 1.4.8
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/driver bumped to 1.17.3
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/screenshoter bumped to 3.8.32
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/nml-client bumped to 1.8.6
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/tunnel-client bumped to 1.5.4
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/ufg-client bumped to 1.12.1
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/ec-client bumped to 1.8.7
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/core-base bumped to 1.15.1
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))



* @applitools/core bumped to 4.16.1
  #### Bug Fixes

  * trigger release ([88c4f81](https://github.com/Applitools-Dev/sdk/commit/88c4f812bd92eae61ee8ebbee5da0d64ad8c8859))




## [4.16.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.15.0...python/core-universal@4.16.0) (2024-05-28)


### Dependencies

* @applitools/req bumped to 1.7.0
  #### Features

  * dynamic timeout based on uploaded file size ([#2364](https://github.com/Applitools-Dev/sdk/issues/2364)) ([8a82d68](https://github.com/Applitools-Dev/sdk/commit/8a82d6839ace60fda27e153ba233019f137017fe))
* @applitools/nml-client bumped to 1.8.5

* @applitools/tunnel-client bumped to 1.5.3

* @applitools/ufg-client bumped to 1.12.0
  #### Features

  * dynamic timeout based on uploaded file size ([#2364](https://github.com/Applitools-Dev/sdk/issues/2364)) ([8a82d68](https://github.com/Applitools-Dev/sdk/commit/8a82d6839ace60fda27e153ba233019f137017fe))



* @applitools/core-base bumped to 1.15.0
  #### Features

  * tell Splunk when clients assume `Target`'s mutability ([#2266](https://github.com/Applitools-Dev/sdk/issues/2266)) ([d18a524](https://github.com/Applitools-Dev/sdk/commit/d18a52491fb6a64e780f84ccff1dcf945351bf95))


  #### Bug Fixes

  * multiple heartbeats for multiple runners in the same process ([#2372](https://github.com/Applitools-Dev/sdk/issues/2372)) ([6ec0f0d](https://github.com/Applitools-Dev/sdk/commit/6ec0f0de7d69a69cdab8437df910a82df15479ea))



* @applitools/ec-client bumped to 1.8.6

* @applitools/core bumped to 4.16.0
  #### Features

  * tell Splunk when clients assume `Target`'s mutability ([#2266](https://github.com/Applitools-Dev/sdk/issues/2266)) ([d18a524](https://github.com/Applitools-Dev/sdk/commit/d18a52491fb6a64e780f84ccff1dcf945351bf95))


  #### Bug Fixes

  * multiple heartbeats for multiple runners in the same process ([#2372](https://github.com/Applitools-Dev/sdk/issues/2372)) ([6ec0f0d](https://github.com/Applitools-Dev/sdk/commit/6ec0f0de7d69a69cdab8437df910a82df15479ea))
  * throw from createRenderResults if rendering failed ([#2352](https://github.com/Applitools-Dev/sdk/issues/2352)) ([50b0394](https://github.com/Applitools-Dev/sdk/commit/50b0394f35464f4d61dd578bf7e84947af00b99b))


  #### Performance Improvements

  * don't wait for ufg client when take-snapshots performed on non-… ([#2366](https://github.com/Applitools-Dev/sdk/issues/2366)) ([4d8ab41](https://github.com/Applitools-Dev/sdk/commit/4d8ab41a421ff9b7f6f7d107bc8c5e9647404430))


  #### Code Refactoring

  * remove eyesServerUrl and apiKey when not necessary ([#2345](https://github.com/Applitools-Dev/sdk/issues/2345)) ([121ae5d](https://github.com/Applitools-Dev/sdk/commit/121ae5d00417d70d9857b8199b4bcfd92de353c6))




## [4.15.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.14.0...python/core-universal@4.15.0) (2024-05-07)


### Dependencies

* @applitools/dom-capture bumped to 11.2.7
  #### Bug Fixes

  * capture user input from input elements ([#2347](https://github.com/Applitools-Dev/sdk/issues/2347)) ([f82d3bb](https://github.com/Applitools-Dev/sdk/commit/f82d3bbc79c624ab7e8eeade7559b523f6adfeac))
* @applitools/core-base bumped to 1.14.0
  #### Features

  * expose git latest commit info in env vars ([#2349](https://github.com/Applitools-Dev/sdk/issues/2349)) ([1db248c](https://github.com/Applitools-Dev/sdk/commit/1db248c83ee1cbc83f905163fe5bd63dd5e293c2))
  * long eyes requests with custom domain ([#2343](https://github.com/Applitools-Dev/sdk/issues/2343)) ([d54beea](https://github.com/Applitools-Dev/sdk/commit/d54beea8c33a56a0516904773daaa5095340fd12))
* @applitools/ec-client bumped to 1.8.5

* @applitools/core bumped to 4.15.0
  #### Features

  * expose git latest commit info in env vars ([#2349](https://github.com/Applitools-Dev/sdk/issues/2349)) ([1db248c](https://github.com/Applitools-Dev/sdk/commit/1db248c83ee1cbc83f905163fe5bd63dd5e293c2))




## [4.14.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.12.3...python/core-universal@4.14.0) (2024-05-01)


### Dependencies

* @applitools/dom-snapshot bumped to 4.11.1
  #### Bug Fixes

  * support for using unicode and just using escape with numbers ([#2241](https://github.com/Applitools-Dev/sdk/issues/2241)) ([c59f47f](https://github.com/Applitools-Dev/sdk/commit/c59f47f73585d7f308c43c9ee1845e097a2111a3))
* @applitools/driver bumped to 1.17.2
  #### Bug Fixes

  * cache nml client per driver ([#2336](https://github.com/Applitools-Dev/sdk/issues/2336)) ([02c09a5](https://github.com/Applitools-Dev/sdk/commit/02c09a53eb6ca6340c93365908f4c485ab389c21))
* @applitools/core-base bumped to 1.13.0
  #### Features

  * `matchTimeout` ([#2309](https://github.com/Applitools-Dev/sdk/issues/2309)) ([626529e](https://github.com/Applitools-Dev/sdk/commit/626529e839fd2a96ac0de98332f42873c0f387a4))
* @applitools/spec-driver-webdriver bumped to 1.1.7

* @applitools/spec-driver-selenium bumped to 1.5.78

* @applitools/spec-driver-puppeteer bumped to 1.4.7

* @applitools/screenshoter bumped to 3.8.31

* @applitools/nml-client bumped to 1.8.4

* @applitools/ec-client bumped to 1.8.4

* @applitools/core bumped to 4.14.0
  #### Features

  * `matchTimeout` ([#2309](https://github.com/Applitools-Dev/sdk/issues/2309)) ([626529e](https://github.com/Applitools-Dev/sdk/commit/626529e839fd2a96ac0de98332f42873c0f387a4))


  #### Bug Fixes

  * cache nml client per driver ([#2336](https://github.com/Applitools-Dev/sdk/issues/2336)) ([02c09a5](https://github.com/Applitools-Dev/sdk/commit/02c09a53eb6ca6340c93365908f4c485ab389c21))
  * support for using unicode and just using escape with numbers ([#2241](https://github.com/Applitools-Dev/sdk/issues/2241)) ([c59f47f](https://github.com/Applitools-Dev/sdk/commit/c59f47f73585d7f308c43c9ee1845e097a2111a3))




## [4.12.3](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.11.2...python/core-universal@4.12.3) (2024-04-17)


### Bug Fixes

* trigger python and dotnet release ([ce35c60](https://github.com/Applitools-Dev/sdk/commit/ce35c60afd5b98a4cb40342da67063bec2299407))


### Dependencies

* @applitools/core bumped to 4.12.3
  #### Bug Fixes

  * trigger core release ([364466f](https://github.com/Applitools-Dev/sdk/commit/364466fd5dfca2aca33a80fda6b44d0be0098b0f))

## [4.11.2](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.11.0...python/core-universal@4.11.2) (2024-04-01)


### Bug Fixes

* trigger js core, python, ruby, dotnet release ([f072fd2](https://github.com/Applitools-Dev/sdk/commit/f072fd219aeb095e6caa94eed42d5ffb9b14f483))


### Dependencies

* @applitools/core bumped to 4.11.2
  #### Bug Fixes

  * trigger js core, python, ruby, dotnet release ([f072fd2](https://github.com/Applitools-Dev/sdk/commit/f072fd219aeb095e6caa94eed42d5ffb9b14f483))

## [4.11.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.10.5...python/core-universal@4.11.0) (2024-03-31)


### Dependencies

* @applitools/spec-driver-selenium bumped to 1.5.73
  #### Bug Fixes

  * remove getSessionDetails call in JS Selenium ([#2280](https://github.com/Applitools-Dev/sdk/issues/2280)) ([d15748f](https://github.com/Applitools-Dev/sdk/commit/d15748f68c931f2f84c13efd8472399c1ff72e25))
* @applitools/core-base bumped to 1.10.0
  #### Features

  * Add GitMergeBaseTimestamp support ([#2281](https://github.com/Applitools-Dev/sdk/issues/2281)) ([5489608](https://github.com/Applitools-Dev/sdk/commit/54896085445663a51b5e5595a2517e48fa8736f3))
  * batch buildId ([#2263](https://github.com/Applitools-Dev/sdk/issues/2263)) ([f19ac38](https://github.com/Applitools-Dev/sdk/commit/f19ac38612bc55d870f59161a39b5b7eb01e25f3))
  * send heartbeat to keep test alive ([#2246](https://github.com/Applitools-Dev/sdk/issues/2246)) ([58636e7](https://github.com/Applitools-Dev/sdk/commit/58636e7dd353f06eb2b3bee1120ab81c3f9fcc94))


  #### Bug Fixes

  * retry Eyes request on ECONNREFUSED to improve stability during deployment ([d1e4dca](https://github.com/Applitools-Dev/sdk/commit/d1e4dcae79185578808b4f2c5f94fa79d7d914a3))
* @applitools/ec-client bumped to 1.7.31

* @applitools/core bumped to 4.11.0
  #### Features

  * Add GitMergeBaseTimestamp support ([#2281](https://github.com/Applitools-Dev/sdk/issues/2281)) ([5489608](https://github.com/Applitools-Dev/sdk/commit/54896085445663a51b5e5595a2517e48fa8736f3))
  * batch buildId ([#2263](https://github.com/Applitools-Dev/sdk/issues/2263)) ([f19ac38](https://github.com/Applitools-Dev/sdk/commit/f19ac38612bc55d870f59161a39b5b7eb01e25f3))




## [4.10.5](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.10.3...python/core-universal@4.10.5) (2024-03-20)


### Bug Fixes

* trigger python,ruby,dotnet release ([14cb160](https://github.com/Applitools-Dev/sdk/commit/14cb160b3559fbc838261fb51cafb228dd213374))
* trigger ruby,python,dotnet release ([9326ee0](https://github.com/Applitools-Dev/sdk/commit/9326ee0f0e1a21a9be262893f77b5d19646da64a))


### Dependencies

* @applitools/core bumped to 4.10.5
  #### Bug Fixes

  * include js core in ruby,python,dotnet release PR ([8326659](https://github.com/Applitools-Dev/sdk/commit/83266595ca3d2e21d7e2d5a50d299c42de4ea96c))

## [4.10.3](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.10.0...python/core-universal@4.10.3) (2024-03-19)


### Bug Fixes

* trigger release for python,ruby,dotnet ([8b3b316](https://github.com/Applitools-Dev/sdk/commit/8b3b3167bbf9f9069176cb597991693a06b5328e))


### Dependencies

* @applitools/core bumped to 4.10.3
  #### Bug Fixes

  * trigger release of js core ([3518656](https://github.com/Applitools-Dev/sdk/commit/351865693f0ca700c563d079e78fe1ef9b557d36))

## [4.10.0](https://github.com/Applitools-Dev/sdk/compare/python/core-universal@4.9.1...python/core-universal@4.10.0) (2024-03-17)


### Dependencies

* @applitools/css-tree bumped to 1.1.0
  #### Features

  * support [@container](https://github.com/container) and [@layer](https://github.com/layer) cssom rules ([#2209](https://github.com/Applitools-Dev/sdk/issues/2209)) ([7da07c4](https://github.com/Applitools-Dev/sdk/commit/7da07c4f5b7f338fb5944ce244af8f2de928cab6))
* @applitools/dom-snapshot bumped to 4.9.0
  #### Features

  * support [@container](https://github.com/container) and [@layer](https://github.com/layer) cssom rules ([#2209](https://github.com/Applitools-Dev/sdk/issues/2209)) ([7da07c4](https://github.com/Applitools-Dev/sdk/commit/7da07c4f5b7f338fb5944ce244af8f2de928cab6))



* @applitools/driver bumped to 1.16.3
  #### Bug Fixes

  * skip execution of getCurrentWorld and getWorlds when env var is set ([#2234](https://github.com/Applitools-Dev/sdk/issues/2234)) ([3a88602](https://github.com/Applitools-Dev/sdk/commit/3a886028b0437b73dae0474408d9bb74ba940dec))
  * trigger build ([acb9c88](https://github.com/Applitools-Dev/sdk/commit/acb9c88161cf55e8b1e409425b5571d69a2e1d5c))
* @applitools/ufg-client bumped to 1.10.0
  #### Features

  * support [@container](https://github.com/container) and [@layer](https://github.com/layer) cssom rules ([#2209](https://github.com/Applitools-Dev/sdk/issues/2209)) ([7da07c4](https://github.com/Applitools-Dev/sdk/commit/7da07c4f5b7f338fb5944ce244af8f2de928cab6))
  * throttle fetching resources by default ([#2216](https://github.com/Applitools-Dev/sdk/issues/2216)) ([a2da800](https://github.com/Applitools-Dev/sdk/commit/a2da80076eb30241a168500903a9d80344900213))



* @applitools/spec-driver-webdriver bumped to 1.1.1

* @applitools/spec-driver-selenium bumped to 1.5.70

* @applitools/spec-driver-puppeteer bumped to 1.4.1

* @applitools/screenshoter bumped to 3.8.25

* @applitools/nml-client bumped to 1.7.3

* @applitools/ec-client bumped to 1.7.28

* @applitools/core bumped to 4.10.0
  #### Features

  * support webview in nml ([#2236](https://github.com/Applitools-Dev/sdk/issues/2236)) ([b4440d8](https://github.com/Applitools-Dev/sdk/commit/b4440d86a863d1af8089f8606ac6819636fa46f4))




## [4.9.1](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.8.0...python/core-universal@4.9.1) (2024-02-29)


### Dependencies

* @applitools/req bumped to 1.6.5
  #### Bug Fixes

  * fixed url concatenation logic ([#2197](https://github.com/applitools/eyes.sdk.javascript1/issues/2197)) ([c3b2e0a](https://github.com/applitools/eyes.sdk.javascript1/commit/c3b2e0ad47f002978544eaac759a80f18f7c5ee3))
* @applitools/dom-shared bumped to 1.0.13
  #### Bug Fixes

  * dont execute script synchronously in polling ([#2228](https://github.com/applitools/eyes.sdk.javascript1/issues/2228)) ([04f525b](https://github.com/applitools/eyes.sdk.javascript1/commit/04f525bcac19bc2fb7240928add28f71efcef0ea))
* @applitools/core-base bumped to 1.9.1
  #### Bug Fixes

  * fixed url concatenation logic ([#2197](https://github.com/applitools/eyes.sdk.javascript1/issues/2197)) ([c3b2e0a](https://github.com/applitools/eyes.sdk.javascript1/commit/c3b2e0ad47f002978544eaac759a80f18f7c5ee3))



* @applitools/dom-capture bumped to 11.2.6

* @applitools/dom-snapshot bumped to 4.8.1

* @applitools/nml-client bumped to 1.7.2

* @applitools/tunnel-client bumped to 1.4.1
  #### Bug Fixes

  * upgrade execution-grid-tunnel to avoid port collision ([751e4e2](https://github.com/applitools/eyes.sdk.javascript1/commit/751e4e2441eb85604bbece0a9dbe18fa16b23847))



* @applitools/ufg-client bumped to 1.9.10

* @applitools/ec-client bumped to 1.7.27

* @applitools/core bumped to 4.9.1


## [4.8.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.7.0...python/core-universal@4.8.0) (2024-02-13)


### Dependencies

* @applitools/dom-snapshot bumped to 4.7.17
  #### Bug Fixes

  * throw error for encoding none unicode char ([#2171](https://github.com/applitools/eyes.sdk.javascript1/issues/2171)) ([4edb9cf](https://github.com/applitools/eyes.sdk.javascript1/commit/4edb9cfb27d8db2ff4cb09c8ebf1b95ab020633d))
* @applitools/spec-driver-webdriver bumped to 1.0.57
  #### Bug Fixes

  * fixed issue with cdp commands on chromium browsers ([#2180](https://github.com/applitools/eyes.sdk.javascript1/issues/2180)) ([550fc77](https://github.com/applitools/eyes.sdk.javascript1/commit/550fc772d3988aae29e6f4a1a11d2a408072dc38))
* @applitools/spec-driver-puppeteer bumped to 1.4.0
  #### Features

  * added support for puppeteer &gt;= 22 ([#2185](https://github.com/applitools/eyes.sdk.javascript1/issues/2185)) ([59d23a9](https://github.com/applitools/eyes.sdk.javascript1/commit/59d23a9689d77c7db06df53b67fa293a3b3f166e))
* @applitools/nml-client bumped to 1.7.0
  #### Features

  * add support for regions and calculated regions ([#2161](https://github.com/applitools/eyes.sdk.javascript1/issues/2161)) ([fea4b1f](https://github.com/applitools/eyes.sdk.javascript1/commit/fea4b1fca3d8f59eada2b5186cd32d47352ccf1a))


  #### Bug Fixes

  * missing viewport when using system screenshot and multi viewport ([#2173](https://github.com/applitools/eyes.sdk.javascript1/issues/2173)) ([411283c](https://github.com/applitools/eyes.sdk.javascript1/commit/411283c7bebc09f178d73b6b47e81e5ce4244d5e))



* @applitools/screenshoter bumped to 3.8.23

* @applitools/ec-client bumped to 1.7.25

* @applitools/core bumped to 4.8.0
  #### Features

  * add support for regions and calculated regions ([#2161](https://github.com/applitools/eyes.sdk.javascript1/issues/2161)) ([fea4b1f](https://github.com/applitools/eyes.sdk.javascript1/commit/fea4b1fca3d8f59eada2b5186cd32d47352ccf1a))


  #### Bug Fixes

  * missing viewport when using system screenshot and multi viewport ([#2173](https://github.com/applitools/eyes.sdk.javascript1/issues/2173)) ([411283c](https://github.com/applitools/eyes.sdk.javascript1/commit/411283c7bebc09f178d73b6b47e81e5ce4244d5e))
  * nml coded region integration with universal ([6fb0934](https://github.com/applitools/eyes.sdk.javascript1/commit/6fb09348238dfe4698856f88e762a9abf80c686f))
  * throw error for encoding none unicode char ([#2171](https://github.com/applitools/eyes.sdk.javascript1/issues/2171)) ([4edb9cf](https://github.com/applitools/eyes.sdk.javascript1/commit/4edb9cfb27d8db2ff4cb09c8ebf1b95ab020633d))




## [4.7.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.6.0...python/core-universal@4.7.0) (2024-01-30)


### Features

* Python/add visual locator to images sdk ([#2138](https://github.com/applitools/eyes.sdk.javascript1/issues/2138)) ([efae455](https://github.com/applitools/eyes.sdk.javascript1/commit/efae4557a8cbe12c640ba99050994c7182ba908c))


### Dependencies

* @applitools/snippets bumped to 2.4.25
  #### Bug Fixes

  * losing root context after layout breakpoints reload ([#2113](https://github.com/applitools/eyes.sdk.javascript1/issues/2113)) ([afa1473](https://github.com/applitools/eyes.sdk.javascript1/commit/afa14735e5539ab0f79aa610e6ec1ea8989a5922))
* @applitools/driver bumped to 1.16.2
  #### Bug Fixes

  * losing root context after layout breakpoints reload ([#2113](https://github.com/applitools/eyes.sdk.javascript1/issues/2113)) ([afa1473](https://github.com/applitools/eyes.sdk.javascript1/commit/afa14735e5539ab0f79aa610e6ec1ea8989a5922))



* @applitools/spec-driver-webdriver bumped to 1.0.55

* @applitools/spec-driver-selenium bumped to 1.5.69

* @applitools/spec-driver-puppeteer bumped to 1.3.5

* @applitools/screenshoter bumped to 3.8.21

* @applitools/nml-client bumped to 1.6.5

* @applitools/ec-client bumped to 1.7.23

* @applitools/core bumped to 4.7.0
  #### Features

  * added support of proxy server url env var ([#2159](https://github.com/applitools/eyes.sdk.javascript1/issues/2159)) ([2f69c3d](https://github.com/applitools/eyes.sdk.javascript1/commit/2f69c3d37d7af9be1f459fd3d5f41b361161b5bf))


  #### Bug Fixes

  * losing root context after layout breakpoints reload ([#2113](https://github.com/applitools/eyes.sdk.javascript1/issues/2113)) ([afa1473](https://github.com/applitools/eyes.sdk.javascript1/commit/afa14735e5539ab0f79aa610e6ec1ea8989a5922))




## [4.6.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.5.2...python/core-universal@4.6.0) (2024-01-16)


### Dependencies

* @applitools/dom-snapshot bumped to 4.7.16
  #### Bug Fixes

  * handle unparsable values of media attribute in dom snapshot ([a2afe2e](https://github.com/applitools/eyes.sdk.javascript1/commit/a2afe2e18508f44f9c046270da0c1e09fb9aea03))
* @applitools/nml-client bumped to 1.6.4
  #### Bug Fixes

  * remove local environment id ([#2152](https://github.com/applitools/eyes.sdk.javascript1/issues/2152)) ([59aaeae](https://github.com/applitools/eyes.sdk.javascript1/commit/59aaeaed474fbde78b76ae7ac803960e3ecd8166))
* @applitools/core-base bumped to 1.9.0
  #### Features

  * added possibility to provide `fallbackBaselineId` in environment objects ([#2146](https://github.com/applitools/eyes.sdk.javascript1/issues/2146)) ([f0782ea](https://github.com/applitools/eyes.sdk.javascript1/commit/f0782ea4c38935f97fc47248ed6a5b67f87b0634))


  #### Bug Fixes

  * add environment variable for setting ufg server ufg ([#2147](https://github.com/applitools/eyes.sdk.javascript1/issues/2147)) ([cfc701f](https://github.com/applitools/eyes.sdk.javascript1/commit/cfc701f7a43fed0fe252d4090b9c1dc490063c76))
* @applitools/ec-client bumped to 1.7.22

* @applitools/core bumped to 4.6.0
  #### Features

  * added possibility to provide `fallbackBaselineId` in environment objects ([#2146](https://github.com/applitools/eyes.sdk.javascript1/issues/2146)) ([f0782ea](https://github.com/applitools/eyes.sdk.javascript1/commit/f0782ea4c38935f97fc47248ed6a5b67f87b0634))


  #### Bug Fixes

  * add environment variable for setting ufg server ufg ([#2147](https://github.com/applitools/eyes.sdk.javascript1/issues/2147)) ([cfc701f](https://github.com/applitools/eyes.sdk.javascript1/commit/cfc701f7a43fed0fe252d4090b9c1dc490063c76))
  * remove local environment id ([#2152](https://github.com/applitools/eyes.sdk.javascript1/issues/2152)) ([59aaeae](https://github.com/applitools/eyes.sdk.javascript1/commit/59aaeaed474fbde78b76ae7ac803960e3ecd8166))




## [4.5.2](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.5.1...python/core-universal@4.5.2) (2024-01-02)


### Dependencies

* @applitools/dom-shared bumped to 1.0.12
  #### Bug Fixes

  * fix error handling in process page poll ([#2127](https://github.com/applitools/eyes.sdk.javascript1/issues/2127)) ([4346026](https://github.com/applitools/eyes.sdk.javascript1/commit/4346026d567b92747df5b4f13fb1e82b849a856e))
* @applitools/dom-capture bumped to 11.2.5

* @applitools/dom-snapshot bumped to 4.7.15
  #### Bug Fixes

  * fix error handling in process page poll ([#2127](https://github.com/applitools/eyes.sdk.javascript1/issues/2127)) ([4346026](https://github.com/applitools/eyes.sdk.javascript1/commit/4346026d567b92747df5b4f13fb1e82b849a856e))



* @applitools/nml-client bumped to 1.6.3
  #### Bug Fixes

  * environment for each check for local environment ([#2135](https://github.com/applitools/eyes.sdk.javascript1/issues/2135)) ([f3a4483](https://github.com/applitools/eyes.sdk.javascript1/commit/f3a44831d41e190aa259367b17e930e7b6f39a04))
* @applitools/core-base bumped to 1.8.0
  #### Features

  * sorted result regions of locate method ([ef6b249](https://github.com/applitools/eyes.sdk.javascript1/commit/ef6b249ad9d6998d6089423efd93f0220f13d378))


  #### Bug Fixes

  * fixed concurrency splank logging ([#2115](https://github.com/applitools/eyes.sdk.javascript1/issues/2115)) ([83afd7d](https://github.com/applitools/eyes.sdk.javascript1/commit/83afd7dd2b52125fdc233dadbaf774811ea1c738))
* @applitools/ec-client bumped to 1.7.21

* @applitools/core bumped to 4.5.2
  #### Bug Fixes

  * environment for each check for local environment ([#2135](https://github.com/applitools/eyes.sdk.javascript1/issues/2135)) ([f3a4483](https://github.com/applitools/eyes.sdk.javascript1/commit/f3a44831d41e190aa259367b17e930e7b6f39a04))
  * fixed concurrency splank logging ([#2115](https://github.com/applitools/eyes.sdk.javascript1/issues/2115)) ([83afd7d](https://github.com/applitools/eyes.sdk.javascript1/commit/83afd7dd2b52125fdc233dadbaf774811ea1c738))
  * fixed the issue when custom os name passed through configuration wasn't respected ([359fc0d](https://github.com/applitools/eyes.sdk.javascript1/commit/359fc0df5a9400312605bb9e8842784b7a05ba7d))




## [4.5.1](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.5.0...python/core-universal@4.5.1) (2023-12-19)


### Dependencies

* @applitools/spec-driver-webdriver bumped to 1.0.54
  #### Bug Fixes

  * fixed extraction of the driver server url ([ddc6449](https://github.com/applitools/eyes.sdk.javascript1/commit/ddc6449fc72166ab26c99e9ba7bb83c05fd591d6))



* @applitools/driver bumped to 1.16.1
  #### Bug Fixes

  * fixed bug with screenshot not being properly scaled on ios devices with appium 2 ([#2092](https://github.com/applitools/eyes.sdk.javascript1/issues/2092)) ([26678bf](https://github.com/applitools/eyes.sdk.javascript1/commit/26678bfe254def506ea82e6a645519d6567fb3fd))
  * fixed extraction of the driver server url ([ddc6449](https://github.com/applitools/eyes.sdk.javascript1/commit/ddc6449fc72166ab26c99e9ba7bb83c05fd591d6))
  * fixed infinite loop that may appear during attribute extraction ([#2102](https://github.com/applitools/eyes.sdk.javascript1/issues/2102)) ([6bef680](https://github.com/applitools/eyes.sdk.javascript1/commit/6bef680fbd2d5c26a46cf2a4f00bd083d1d02109))
* @applitools/screenshoter bumped to 3.8.20
  #### Bug Fixes

  * fixed bug with screenshot not being properly scaled on ios devices with appium 2 ([#2092](https://github.com/applitools/eyes.sdk.javascript1/issues/2092)) ([26678bf](https://github.com/applitools/eyes.sdk.javascript1/commit/26678bfe254def506ea82e6a645519d6567fb3fd))



* @applitools/core-base bumped to 1.7.5
  #### Bug Fixes

  * avoid caching concurrency ([#2103](https://github.com/applitools/eyes.sdk.javascript1/issues/2103)) ([34db2e9](https://github.com/applitools/eyes.sdk.javascript1/commit/34db2e9c554b0851b18b514b1a8a82b83ff310cd))
* @applitools/spec-driver-selenium bumped to 1.5.68

* @applitools/spec-driver-puppeteer bumped to 1.3.4

* @applitools/nml-client bumped to 1.6.2

* @applitools/ec-client bumped to 1.7.20

* @applitools/core bumped to 4.5.1
  #### Bug Fixes

  * avoid caching concurrency ([#2103](https://github.com/applitools/eyes.sdk.javascript1/issues/2103)) ([34db2e9](https://github.com/applitools/eyes.sdk.javascript1/commit/34db2e9c554b0851b18b514b1a8a82b83ff310cd))




## [4.5.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.4.0...python/core-universal@4.5.0) (2023-12-18)


### Dependencies

* @applitools/driver bumped to 1.16.0
  #### Features

  * add set of env variables to skip/ignore some optional automations ([#2097](https://github.com/applitools/eyes.sdk.javascript1/issues/2097)) ([bd3b08c](https://github.com/applitools/eyes.sdk.javascript1/commit/bd3b08c3d2997eb98d545b308a1f15501192178e))
* @applitools/spec-driver-webdriver bumped to 1.0.53

* @applitools/spec-driver-selenium bumped to 1.5.67

* @applitools/spec-driver-puppeteer bumped to 1.3.3

* @applitools/screenshoter bumped to 3.8.19

* @applitools/nml-client bumped to 1.6.1

* @applitools/ec-client bumped to 1.7.19

* @applitools/core bumped to 4.5.0
  #### Features

  * add set of env variables to skip/ignore some optional automations ([#2097](https://github.com/applitools/eyes.sdk.javascript1/issues/2097)) ([bd3b08c](https://github.com/applitools/eyes.sdk.javascript1/commit/bd3b08c3d2997eb98d545b308a1f15501192178e))


  #### Bug Fixes

  * fixed issue when page wasn't reloaded for one of the breakpoints if the initial viewport size matches it ([9038723](https://github.com/applitools/eyes.sdk.javascript1/commit/9038723ee68515f7d4fe20ed31ec501df9a381dc))




## [4.4.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.3.0...python/core-universal@4.4.0) (2023-12-12)


### Dependencies

* @applitools/driver bumped to 1.15.3
  #### Bug Fixes

  * layout breakpoints reload and lazy load ([#2073](https://github.com/applitools/eyes.sdk.javascript1/issues/2073)) ([ab2c49e](https://github.com/applitools/eyes.sdk.javascript1/commit/ab2c49ea1ecff3fef337637a83aa5bef755a7b01))
* @applitools/nml-client bumped to 1.6.0
  #### Features

  * support updated applitools lib protocol ([#2086](https://github.com/applitools/eyes.sdk.javascript1/issues/2086)) ([31b49fc](https://github.com/applitools/eyes.sdk.javascript1/commit/31b49fc411c452d0b3da341fd701309714484485))



* @applitools/tunnel-client bumped to 1.4.0
  #### Features

  * sign windows binaries ([87fd29c](https://github.com/applitools/eyes.sdk.javascript1/commit/87fd29c8953fc512489c3bb00841ca91c5b2f030))
* @applitools/spec-driver-webdriver bumped to 1.0.52

* @applitools/spec-driver-selenium bumped to 1.5.66

* @applitools/spec-driver-puppeteer bumped to 1.3.2

* @applitools/screenshoter bumped to 3.8.18

* @applitools/ec-client bumped to 1.7.18

* @applitools/core bumped to 4.4.0
  #### Features

  * sign windows binaries ([87fd29c](https://github.com/applitools/eyes.sdk.javascript1/commit/87fd29c8953fc512489c3bb00841ca91c5b2f030))
  * support updated applitools lib protocol ([#2086](https://github.com/applitools/eyes.sdk.javascript1/issues/2086)) ([31b49fc](https://github.com/applitools/eyes.sdk.javascript1/commit/31b49fc411c452d0b3da341fd701309714484485))


  #### Bug Fixes

  * layout breakpoints reload and lazy load ([#2073](https://github.com/applitools/eyes.sdk.javascript1/issues/2073)) ([ab2c49e](https://github.com/applitools/eyes.sdk.javascript1/commit/ab2c49ea1ecff3fef337637a83aa5bef755a7b01))


  #### Code Refactoring

  * fix safe selector generation ([#2072](https://github.com/applitools/eyes.sdk.javascript1/issues/2072)) ([373f11b](https://github.com/applitools/eyes.sdk.javascript1/commit/373f11b0dfea6eab417eb7077e0cfec79877dc1b))




## [4.3.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.2.0...python/core-universal@4.3.0) (2023-12-05)


### Dependencies

* @applitools/utils bumped to 1.7.0
  #### Features

  * add Eyes.getResults method ([#2046](https://github.com/applitools/eyes.sdk.javascript1/issues/2046)) ([#2069](https://github.com/applitools/eyes.sdk.javascript1/issues/2069)) ([4d263e1](https://github.com/applitools/eyes.sdk.javascript1/commit/4d263e19cb5e5708790a1a7ef90ff8f3eee50d91))
* @applitools/core-base bumped to 1.7.4
  #### Bug Fixes

  * do not block concurrency when server response is 503 ([#2049](https://github.com/applitools/eyes.sdk.javascript1/issues/2049)) ([f285009](https://github.com/applitools/eyes.sdk.javascript1/commit/f2850098f7522776c0d0a98bb1d958303628b149))



* @applitools/logger bumped to 2.0.14

* @applitools/socket bumped to 1.1.14

* @applitools/req bumped to 1.6.4

* @applitools/image bumped to 1.1.9

* @applitools/spec-driver-webdriver bumped to 1.0.51

* @applitools/spec-driver-selenium bumped to 1.5.65

* @applitools/spec-driver-puppeteer bumped to 1.3.1

* @applitools/driver bumped to 1.15.2

* @applitools/screenshoter bumped to 3.8.17

* @applitools/nml-client bumped to 1.5.17

* @applitools/tunnel-client bumped to 1.3.2

* @applitools/ufg-client bumped to 1.9.9

* @applitools/ec-client bumped to 1.7.17

* @applitools/core bumped to 4.3.0
  #### Features

  * add Eyes.getResults method ([#2046](https://github.com/applitools/eyes.sdk.javascript1/issues/2046)) ([#2069](https://github.com/applitools/eyes.sdk.javascript1/issues/2069)) ([4d263e1](https://github.com/applitools/eyes.sdk.javascript1/commit/4d263e19cb5e5708790a1a7ef90ff8f3eee50d91))




## [4.2.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.1.0...python/core-universal@4.2.0) (2023-11-21)


### Dependencies

* @applitools/utils bumped to 1.6.3
  #### Bug Fixes

  * don't throw error for missing configuration file ([#2034](https://github.com/applitools/eyes.sdk.javascript1/issues/2034)) ([d084e7b](https://github.com/applitools/eyes.sdk.javascript1/commit/d084e7bf6e1727e3969622b4e597881f18241eb3))
* @applitools/logger bumped to 2.0.13

* @applitools/req bumped to 1.6.3

* @applitools/image bumped to 1.1.8

* @applitools/dom-snapshot bumped to 4.7.14
  #### Bug Fixes

  * preserve css declarations order in dom-snapshot ([#2037](https://github.com/applitools/eyes.sdk.javascript1/issues/2037)) ([1381851](https://github.com/applitools/eyes.sdk.javascript1/commit/1381851d46f28ea7e7724025c4eab33c81c4e144))
* @applitools/spec-driver-webdriver bumped to 1.0.50
  #### Bug Fixes

  * send devtool commands in chromium ([#2039](https://github.com/applitools/eyes.sdk.javascript1/issues/2039)) ([ff42043](https://github.com/applitools/eyes.sdk.javascript1/commit/ff42043c3d9f110eb7b22ab1a8448d77859923b4))



* @applitools/spec-driver-puppeteer bumped to 1.3.0
  #### Features

  * added notification about outdated sdk version ([#2012](https://github.com/applitools/eyes.sdk.javascript1/issues/2012)) ([0f0a646](https://github.com/applitools/eyes.sdk.javascript1/commit/0f0a6462a56e7c97f9a22173c3b63af91e220adb))



* @applitools/core-base bumped to 1.7.3
  #### Bug Fixes

  * remove connection timeout in case of a long running tasks ([#2006](https://github.com/applitools/eyes.sdk.javascript1/issues/2006)) ([49a596a](https://github.com/applitools/eyes.sdk.javascript1/commit/49a596ac1b022a66b5c07ecfee458cc061891ce0))
  * return result when error in the ufg ([#2020](https://github.com/applitools/eyes.sdk.javascript1/issues/2020)) ([28cdcc5](https://github.com/applitools/eyes.sdk.javascript1/commit/28cdcc5a859641d0edde032165c5068fcc580c8d))



* @applitools/socket bumped to 1.1.13

* @applitools/spec-driver-selenium bumped to 1.5.64

* @applitools/driver bumped to 1.15.1

* @applitools/screenshoter bumped to 3.8.16

* @applitools/nml-client bumped to 1.5.16

* @applitools/tunnel-client bumped to 1.3.1

* @applitools/ufg-client bumped to 1.9.8

* @applitools/ec-client bumped to 1.7.16

* @applitools/core bumped to 4.2.0
  #### Features

  * added notification about outdated sdk version ([#2012](https://github.com/applitools/eyes.sdk.javascript1/issues/2012)) ([0f0a646](https://github.com/applitools/eyes.sdk.javascript1/commit/0f0a6462a56e7c97f9a22173c3b63af91e220adb))
  * log driver environment info to splank ([#2023](https://github.com/applitools/eyes.sdk.javascript1/issues/2023)) ([11d0546](https://github.com/applitools/eyes.sdk.javascript1/commit/11d0546e76962b4c231e140b0229b8402da27f69))


  #### Bug Fixes

  * return result when error in the ufg ([#2020](https://github.com/applitools/eyes.sdk.javascript1/issues/2020)) ([28cdcc5](https://github.com/applitools/eyes.sdk.javascript1/commit/28cdcc5a859641d0edde032165c5068fcc580c8d))




## [4.1.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.0.2...python/core-universal@4.1.0) (2023-11-07)


### Dependencies

* @applitools/dom-shared bumped to 1.0.11
  #### Bug Fixes

  * (java/eyes-appium-java5): fix incorrect stitchMode mapping in checkSettings ([c70428e](https://github.com/applitools/eyes.sdk.javascript1/commit/c70428ec83e26b8b5e398ff11814f8376ca97d56))
* @applitools/dom-capture bumped to 11.2.4
  #### Bug Fixes

  * (java/eyes-appium-java5): fix incorrect stitchMode mapping in checkSettings ([c70428e](https://github.com/applitools/eyes.sdk.javascript1/commit/c70428ec83e26b8b5e398ff11814f8376ca97d56))



* @applitools/dom-snapshot bumped to 4.7.13
  #### Bug Fixes

  * (java/eyes-appium-java5): fix incorrect stitchMode mapping in checkSettings ([c70428e](https://github.com/applitools/eyes.sdk.javascript1/commit/c70428ec83e26b8b5e398ff11814f8376ca97d56))
  * handled duplicated style properties in inline style tags ([#2014](https://github.com/applitools/eyes.sdk.javascript1/issues/2014)) ([2f8bada](https://github.com/applitools/eyes.sdk.javascript1/commit/2f8bada9cd44c65a69e54cbd08f57534632f12d2))



* @applitools/driver bumped to 1.15.0
  #### Features

  * added warning when driver used with capabilities that may conflict with applitools lib workflow ([#2011](https://github.com/applitools/eyes.sdk.javascript1/issues/2011)) ([081006d](https://github.com/applitools/eyes.sdk.javascript1/commit/081006d879894db03a2713129b66586496b6eb02))
* @applitools/screenshoter bumped to 3.8.15

* @applitools/nml-client bumped to 1.5.15

* @applitools/ufg-client bumped to 1.9.7
  #### Bug Fixes

  * added retries on ufg requests that respond with 503 status code ([7d78917](https://github.com/applitools/eyes.sdk.javascript1/commit/7d78917d559fa182c6723ca34cef2118cf08a036))
* @applitools/spec-driver-webdriver bumped to 1.0.49

* @applitools/spec-driver-selenium bumped to 1.5.63

* @applitools/spec-driver-puppeteer bumped to 1.2.5

* @applitools/ec-client bumped to 1.7.15

* @applitools/core bumped to 4.1.0
  #### Features

  * added warning when driver used with capabilities that may conflict with applitools lib workflow ([#2011](https://github.com/applitools/eyes.sdk.javascript1/issues/2011)) ([081006d](https://github.com/applitools/eyes.sdk.javascript1/commit/081006d879894db03a2713129b66586496b6eb02))


  #### Bug Fixes

  * fixed issue that caused dom snapshots to be taken for different viewport sizes when layout breakpoints were explicitly turned off ([4121876](https://github.com/applitools/eyes.sdk.javascript1/commit/4121876189f133b6023cfea52ca91c02c31079fb))




## [4.0.2](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.0.1...python/core-universal@4.0.2) (2023-10-30)


### Dependencies

* @applitools/core bumped to 4.0.2
  #### Bug Fixes

  * generate safe selectors as close as possible to taking dom snapshot ([#1987](https://github.com/applitools/eyes.sdk.javascript1/issues/1987)) ([102208b](https://github.com/applitools/eyes.sdk.javascript1/commit/102208b909c0b149808f6e4c24a0a662305b1b78))

## [4.0.1](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@4.0.0...python/core-universal@4.0.1) (2023-10-25)


### Dependencies

* @applitools/tunnel-client bumped to 1.3.0
  #### Features

  * add more logs for tunnel worker ([60cf839](https://github.com/applitools/eyes.sdk.javascript1/commit/60cf839f23b214dff89ff4a9c59f231c96160daf))
* @applitools/ec-client bumped to 1.7.14

* @applitools/core bumped to 4.0.1


## [4.0.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal-v3.11.8...python/core-universal@4.0.0) (2023-10-17)


### Features

* new devices added to IosDeviceName enum ([#1905](https://github.com/applitools/eyes.sdk.javascript1/issues/1905)) ([d32f4a3](https://github.com/applitools/eyes.sdk.javascript1/commit/d32f4a37c1400a6b07afa41fb606ab5b4d3adefa))


### Dependencies

* @applitools/utils bumped to 1.6.2
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))
* @applitools/logger bumped to 2.0.12
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/socket bumped to 1.1.12
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/req bumped to 1.6.2
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/image bumped to 1.1.7
  #### Bug Fixes

  * avoid using ascii text decoder ([1b68d39](https://github.com/applitools/eyes.sdk.javascript1/commit/1b68d3945d96b17b9ab1f1a87d352206fd0c81d6))


  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/driver bumped to 1.14.4
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/tunnel-client bumped to 1.2.4
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/ec-client bumped to 1.7.13
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/spec-driver-webdriver bumped to 1.0.48

* @applitools/spec-driver-puppeteer bumped to 1.2.4
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/screenshoter bumped to 3.8.14
  #### Bug Fixes

  * allow css scrolling when taking screenshot of the webview ([2d3a257](https://github.com/applitools/eyes.sdk.javascript1/commit/2d3a2572768e7f979d16297ca316a79ab2538adb))


  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/core-base bumped to 1.7.2
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))



* @applitools/nml-client bumped to 1.5.14

* @applitools/ufg-client bumped to 1.9.6
  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))
  * drop jsdom dependency ([1b68d39](https://github.com/applitools/eyes.sdk.javascript1/commit/1b68d3945d96b17b9ab1f1a87d352206fd0c81d6))



* @applitools/spec-driver-selenium bumped to 1.5.62

* @applitools/core bumped to 4.0.0
  #### ⚠ BREAKING CHANGES

  * update core to v4 ([#1936](https://github.com/applitools/eyes.sdk.javascript1/issues/1936))

  #### Features

  * update core to v4 ([#1936](https://github.com/applitools/eyes.sdk.javascript1/issues/1936)) ([1b68d39](https://github.com/applitools/eyes.sdk.javascript1/commit/1b68d3945d96b17b9ab1f1a87d352206fd0c81d6))


  #### Bug Fixes

  * upgrade dom-snapshot ([#1969](https://github.com/applitools/eyes.sdk.javascript1/issues/1969)) ([458beb8](https://github.com/applitools/eyes.sdk.javascript1/commit/458beb803aec3e6d51484a557b3eed8f537a709d))


  #### Code Refactoring

  * disallow usage of global Buffer ([#1957](https://github.com/applitools/eyes.sdk.javascript1/issues/1957)) ([adcc082](https://github.com/applitools/eyes.sdk.javascript1/commit/adcc082f20f6b92e819b96424e995d9a69d99758))




## [3.9.1](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@3.9.0...python/core-universal@3.9.1) (2023-08-18)


### Dependencies

* @applitools/utils bumped to 1.5.1
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))
* @applitools/logger bumped to 2.0.8
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/socket bumped to 1.1.8
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/req bumped to 1.5.3
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/image bumped to 1.1.3
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/snippets bumped to 2.4.23
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))
* @applitools/spec-driver-webdriver bumped to 1.0.42
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/spec-driver-selenium bumped to 1.5.56
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/spec-driver-puppeteer bumped to 1.1.73
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/driver bumped to 1.13.5
  #### Bug Fixes

  * optimize driver usage in close ([#1867](https://github.com/applitools/eyes.sdk.javascript1/issues/1867)) ([60dff6b](https://github.com/applitools/eyes.sdk.javascript1/commit/60dff6b160e69d3893c91a1125d668fa18b43072))


  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/screenshoter bumped to 3.8.8
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/nml-client bumped to 1.5.8
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/tunnel-client bumped to 1.2.0
  #### Features

  * replace and destroy tunnels by tunnel id ([#1878](https://github.com/applitools/eyes.sdk.javascript1/issues/1878)) ([22bcc15](https://github.com/applitools/eyes.sdk.javascript1/commit/22bcc15b31457e3da56cdb6f73bee3dcb7e051a1))


  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/ufg-client bumped to 1.7.1
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/ec-client bumped to 1.7.5
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/core-base bumped to 1.5.1
  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))



* @applitools/core bumped to 3.9.1
  #### Bug Fixes

  * optimize driver usage in close ([#1867](https://github.com/applitools/eyes.sdk.javascript1/issues/1867)) ([60dff6b](https://github.com/applitools/eyes.sdk.javascript1/commit/60dff6b160e69d3893c91a1125d668fa18b43072))


  #### Code Refactoring

  * refactored spec driver interface ([#1839](https://github.com/applitools/eyes.sdk.javascript1/issues/1839)) ([aa49ec2](https://github.com/applitools/eyes.sdk.javascript1/commit/aa49ec2a7d14b8529acc3a8a4c2baecfa113d98a))




## [3.9.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@3.8.0...python/core-universal@3.9.0) (2023-08-10)


### Dependencies

* @applitools/nml-client bumped to 1.5.7
  #### Bug Fixes

  * propagate stitch mode to applitools lib ([a2dcedb](https://github.com/applitools/eyes.sdk.javascript1/commit/a2dcedb4bc6b999c137ed2aab43e0a463aa90169))
* @applitools/core bumped to 3.9.0
  #### Features

  * re-release ([e62abc7](https://github.com/applitools/eyes.sdk.javascript1/commit/e62abc7e74ea0e193eb7770036ae7f97bd11188a))


  #### Bug Fixes

  * propagate stitch mode to applitools lib ([a2dcedb](https://github.com/applitools/eyes.sdk.javascript1/commit/a2dcedb4bc6b999c137ed2aab43e0a463aa90169))




## [3.8.1](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal@3.8.0...python/core-universal@3.8.1) (2023-08-08)


### Dependencies

* @applitools/core bumped to 3.8.1
  #### Bug Fixes

  * some fix ([5dc537a](https://github.com/applitools/eyes.sdk.javascript1/commit/5dc537aa5d40933c21f21b8f138f7ff944c064a8))

## [3.8.0](https://github.com/applitools/eyes.sdk.javascript1/compare/python/core-universal-v3.6.6...python/core-universal@3.8.0) (2023-08-08)


### Dependencies

* @applitools/core bumped to 3.8.0
  #### Features

  * rework log event on opent eyes ([#1842](https://github.com/applitools/eyes.sdk.javascript1/issues/1842)) ([532756b](https://github.com/applitools/eyes.sdk.javascript1/commit/532756b75c1023967c3781316148c890dbcfaac8))
