# Changelog

## [0.5.2](https://github.com/acdh-oeaw/django-interval/compare/v0.5.1...v0.5.2) (2025-12-23)


### Bug Fixes

* **utils:** update error message ([ed7f52d](https://github.com/acdh-oeaw/django-interval/commit/ed7f52d7d6d61288ae724500228d88bfb4f3cec5))


### Dependencies

* **dev:** add pytest and pytest-django as dev dependencies ([1ce7960](https://github.com/acdh-oeaw/django-interval/commit/1ce7960488146bcc31bf94c9326bf29726888fad))


### Documentation

* **fields:** expand FuzzyDateRegexField documentation ([c4a0ee4](https://github.com/acdh-oeaw/django-interval/commit/c4a0ee4b9fdad73df731dc123d96ef7af405b6dd))
* **fields:** use `r` on docstring because it contains a regex ([e87a18f](https://github.com/acdh-oeaw/django-interval/commit/e87a18f95784ea0b83ff7f161e841e795f8df027))
* **utils:** document parse_angle_brackets properly ([f4ab8d3](https://github.com/acdh-oeaw/django-interval/commit/f4ab8d35116f622988ab84d8ef15e00d060fc936))

## [0.5.1](https://github.com/acdh-oeaw/django-interval/compare/v0.5.0...v0.5.1) (2025-04-01)


### Bug Fixes

* **fields:** explicitly populate generated fields during form save ([f1dad46](https://github.com/acdh-oeaw/django-interval/commit/f1dad46d1f884cd2bed4c7f602e2571ba899adfc)), closes [#58](https://github.com/acdh-oeaw/django-interval/issues/58)
* **fields:** unset auto fields if main field is empty ([0c4996b](https://github.com/acdh-oeaw/django-interval/commit/0c4996bf27cd163ee2eb2370298a46178c28d4cc)), closes [#56](https://github.com/acdh-oeaw/django-interval/issues/56)

## [0.5.0](https://github.com/acdh-oeaw/django-interval/compare/v0.4.0...v0.5.0) (2025-03-27)


### Features

* **fields:** set the auto_created attribute of the auto created fields ([bd50343](https://github.com/acdh-oeaw/django-interval/commit/bd50343852b826de06b9ac39d325f056e570b3b5))
* **filters:** add YearIntervalRangeFilter and DateIntervalRangeFilter ([ed44d8a](https://github.com/acdh-oeaw/django-interval/commit/ed44d8a8d50a4b72fff24455cb0bb166f890fac4))


### Bug Fixes

* **views:** catch exception and pass error message on to template ([4d77f5c](https://github.com/acdh-oeaw/django-interval/commit/4d77f5cb9dbb6caca883e179d8fef43f68a4ca65)), closes [#53](https://github.com/acdh-oeaw/django-interval/issues/53)

## [0.4.0](https://github.com/acdh-oeaw/django-interval/compare/v0.3.2...v0.4.0) (2025-03-11)


### ⚠ BREAKING CHANGES

* **templates:** use new templatetag instead of hardcoding output

### Features

* **templatetags:** introduce date_interval templatetag ([1c0318b](https://github.com/acdh-oeaw/django-interval/commit/1c0318b24ec5b337b1d8938f9e1ee669dd2dc9a3))


### Bug Fixes

* **fields:** use date on the parsed values to get more sensible error ([3aed7d4](https://github.com/acdh-oeaw/django-interval/commit/3aed7d47857d3e4460525718035e3058d2c0340f)), closes [#37](https://github.com/acdh-oeaw/django-interval/issues/37)
* **templates:** use new templatetag instead of hardcoding output ([13d9f6c](https://github.com/acdh-oeaw/django-interval/commit/13d9f6c79a7dc9a0929d3d9f0ddbde95e6a0fc2f)), closes [#47](https://github.com/acdh-oeaw/django-interval/issues/47)
* **utils:** set all the dates also on day-specific date values ([a356d9d](https://github.com/acdh-oeaw/django-interval/commit/a356d9d9cfcf547c62bb5e45c18515c36aed9067))


### Documentation

* **readme:** fix postfixes in Readme ([833fe5c](https://github.com/acdh-oeaw/django-interval/commit/833fe5c34e1fcf3194c09aa2ddc0fbfad340fc38))

## [0.3.2](https://github.com/acdh-oeaw/django-interval/compare/v0.3.1...v0.3.2) (2025-03-03)


### Bug Fixes

* **widgets:** append closing tag to script element ([117995a](https://github.com/acdh-oeaw/django-interval/commit/117995a6f8c75a70387541342729ffe429868e65))

## [0.3.1](https://github.com/acdh-oeaw/django-interval/compare/v0.3.0...v0.3.1) (2025-03-03)


### Bug Fixes

* **fields:** escape special regex characters ([147b4b1](https://github.com/acdh-oeaw/django-interval/commit/147b4b15f2e79e5585325a32c658991a9ecfa8d1)), closes [#34](https://github.com/acdh-oeaw/django-interval/issues/34)
* **widgets:** use `defer` when including the intervalwidget.js ([822835b](https://github.com/acdh-oeaw/django-interval/commit/822835be8c12d4da827c04ed90acc585444b65a4)), closes [#41](https://github.com/acdh-oeaw/django-interval/issues/41)

## [0.3.0](https://github.com/acdh-oeaw/django-interval/compare/v0.2.5...v0.3.0) (2025-02-24)


### ⚠ BREAKING CHANGES

* **templates:** move interval.html

### Bug Fixes

* **js:** add keyup trigger always, not only on load ([d524c41](https://github.com/acdh-oeaw/django-interval/commit/d524c41f996db71c1cd00095805e40d62d90806d)), closes [#31](https://github.com/acdh-oeaw/django-interval/issues/31)


### Code Refactoring

* **templates:** move interval.html ([a13a20c](https://github.com/acdh-oeaw/django-interval/commit/a13a20cd7b9f7eda4bf97053e786da932356c06b))

## [0.2.5](https://github.com/b1rger/django-interval/compare/v0.2.4...v0.2.5) (2025-01-16)


### Bug Fixes

* **fields:** only parse field if there is even a value ([a282102](https://github.com/b1rger/django-interval/commit/a2821023b89a0fa8aa2e4a8ab5b4c9ed88b8dd4f))
* **fields:** skip parsing in historical model instances ([d34e5fb](https://github.com/b1rger/django-interval/commit/d34e5fbf468699f98ce7e30077052114a598130b))

## [0.2.4](https://github.com/b1rger/django-interval/compare/v0.2.3...v0.2.4) (2025-01-15)


### Bug Fixes

* **fields:** add additional check for migrations ([1c2243f](https://github.com/b1rger/django-interval/commit/1c2243fa1a4cdfbe09bced4ae0aff875eb4a56c6))

## [0.2.3](https://github.com/b1rger/django-interval/compare/v0.2.2...v0.2.3) (2024-12-20)


### Bug Fixes

* **field:** handle missing interval view gracefully ([69318f0](https://github.com/b1rger/django-interval/commit/69318f0b8eb179f647b88dda954a8d797c41ce2f)), closes [#11](https://github.com/b1rger/django-interval/issues/11)

## [0.2.2](https://github.com/b1rger/django-interval/compare/v0.2.0...v0.2.2) (2024-12-16)


### Miscellaneous Chores

* release 0.2.1 ([9c6821b](https://github.com/b1rger/django-interval/commit/9c6821be61b0e18a8ed36bde8bee49cc3ae5995d))
* release 0.2.2 ([b975c63](https://github.com/b1rger/django-interval/commit/b975c63800a921672a2e79868cbf7a1b89d2e0c8))

## [0.2.0](https://github.com/b1rger/django-interval/compare/v0.1.0...v0.2.0) (2024-12-16)


### Features

* **views:** add view and route to get calculated dates ([8c8de34](https://github.com/b1rger/django-interval/commit/8c8de346486318da24617e3270cbb93c9846998f))
* **widgets:** introduce and use a custom interval widget ([c1d91fb](https://github.com/b1rger/django-interval/commit/c1d91fb2febd3f05f11ba9a343f75f9b72a09f45))

## 0.1.0 (2024-12-12)


### Miscellaneous Chores

* release 0.1.0 ([d8a215d](https://github.com/b1rger/django-interval/commit/d8a215d2702e02c604be47d001e4d7858b45e2e1))
