# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v0.0.25](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.25) - 2025-12-25

<small>[Compare with v0.0.24](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.24...v0.0.25)</small>

### Bug Fixes

- handle edge cases in inv_lerp and smoothstep functions; simplify sign function ([19d5441](https://github.com/sicksubroutine/funcy-bear/commit/19d54410a9c19d76d307e59daf262b871f80daf7) by chaz).

## [v0.0.24](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.24) - 2025-12-25

<small>[Compare with v0.0.22](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.22...v0.0.24)</small>

## [v0.0.22](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.22) - 2025-12-15

<small>[Compare with v0.0.21](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.21...v0.0.22)</small>

### Features

- implement color gradient utility with RGB interpolation ([e5c6ad5](https://github.com/sicksubroutine/funcy-bear/commit/e5c6ad5d47b0e101a83a9a99a8b6d15d14248818) by chaz).

## [v0.0.21](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.21) - 2025-12-08

<small>[Compare with v0.0.20](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.20...v0.0.21)</small>

## [v0.0.20](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.20) - 2025-12-04

<small>[Compare with v0.0.19](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.19...v0.0.20)</small>

### Features

- add HTTP status code constants and enumeration ([c7a0885](https://github.com/sicksubroutine/funcy-bear/commit/c7a0885b40d76f4f450d28c42715394d1d961af7) by chaz).

## [v0.0.19](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.19) - 2025-12-04

<small>[Compare with v0.0.17](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.17...v0.0.19)</small>

### Features

- add constants for escaping characters and Python syntax (#13) ([553ad51](https://github.com/sicksubroutine/funcy-bear/commit/553ad517c461184dcdb8d179a7fdcb8f93243ae1) by Chaz).
- add constants for escaping characters and Python syntax (#12) ([832dde7](https://github.com/sicksubroutine/funcy-bear/commit/832dde783235ebc899c16051fce70e62624de1c8) by Chaz). * refactor: update type hints in add, __setattr__, __getitem__, __setitem__, __delitem__, and __delattr__ methods for improved type safety

## [v0.0.17](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.17) - 2025-11-16

<small>[Compare with v0.0.16](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.16...v0.0.17)</small>

### Code Refactoring

- clean up CollectionProtocol methods and add PathInfo protocol ([50a975e](https://github.com/sicksubroutine/funcy-bear/commit/50a975e12080ed7cd094052750bf378e90ef58eb) by chaz).

## [v0.0.16](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.16) - 2025-11-16

<small>[Compare with v0.0.15](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.15...v0.0.16)</small>

### Code Refactoring

- update cache path assignment in DirectoryManager ([302ce35](https://github.com/sicksubroutine/funcy-bear/commit/302ce3518524e9417ae25881794fa7592f5ed798) by chaz).

## [v0.0.15](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.15) - 2025-11-15

<small>[Compare with v0.0.14](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.14...v0.0.15)</small>

## [v0.0.14](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.14) - 2025-11-14

<small>[Compare with v0.0.12](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.12...v0.0.14)</small>

### Code Refactoring

- remove default type for WriteAheadLog generic parameter ([0781175](https://github.com/sicksubroutine/funcy-bear/commit/0781175eb11f9831b48669ddcb93071dc37667fe) by chaz).
- remove unused WALConfig protocol and related methods from Write-Ahead Log implementation ([0b7509a](https://github.com/sicksubroutine/funcy-bear/commit/0b7509a361bd439a4b2b011fadb91a8689f82270) by chaz).

## [v0.0.12](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.12) - 2025-11-14

<small>[Compare with v0.0.11](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.11...v0.0.12)</small>

### Code Refactoring

- enhance WALConfig class with protocol definition and additional methods ([23ef6e6](https://github.com/sicksubroutine/funcy-bear/commit/23ef6e655837085866d88e85927bb0568282e52f) by chaz).

## [v0.0.11](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.11) - 2025-11-14

<small>[Compare with v0.0.7](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.7...v0.0.11)</small>

### Features

- Add file cache management utilities and implement basic cache system (#8) ([3ffaa5e](https://github.com/sicksubroutine/funcy-bear/commit/3ffaa5ed4cf9d1fdc680321011b6f049839c61ea) by Chaz).

## [v0.0.7](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.7) - 2025-11-03

<small>[Compare with v0.0.2](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.2...v0.0.7)</small>

## [v0.0.2](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.2) - 2025-11-02

<small>[Compare with first commit](https://github.com/sicksubroutine/funcy-bear/compare/8e029e5457c2e2d907a64b67d19cb49a76ce6e23...v0.0.2)</small>

## [v0.0.13](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.13) - 2025-11-14

<small>[Compare with v0.0.12](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.12...v0.0.13)</small>

### Code Refactoring

- remove default type for WriteAheadLog generic parameter ([0781175](https://github.com/sicksubroutine/funcy-bear/commit/0781175eb11f9831b48669ddcb93071dc37667fe) by chaz).
- remove unused WALConfig protocol and related methods from Write-Ahead Log implementation ([0b7509a](https://github.com/sicksubroutine/funcy-bear/commit/0b7509a361bd439a4b2b011fadb91a8689f82270) by chaz).

## [v0.0.12](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.12) - 2025-11-14

<small>[Compare with v0.0.11](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.11...v0.0.12)</small>

### Code Refactoring

- enhance WALConfig class with protocol definition and additional methods ([23ef6e6](https://github.com/sicksubroutine/funcy-bear/commit/23ef6e655837085866d88e85927bb0568282e52f) by chaz).

## [v0.0.11](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.11) - 2025-11-14
****
<small>[Compare with v0.0.7](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.7...v0.0.11)</small>

### Features

- Add file cache management utilities and implement basic cache system (#8) ([3ffaa5e](https://github.com/sicksubroutine/funcy-bear/commit/3ffaa5ed4cf9d1fdc680321011b6f049839c61ea) by Chaz).

## [v0.0.7](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.7) - 2025-11-03

<small>[Compare with v0.0.2](https://github.com/sicksubroutine/funcy-bear/compare/v0.0.2...v0.0.7)</small>

## [v0.0.2](https://github.com/sicksubroutine/funcy-bear/releases/tag/v0.0.2) - 2025-11-02

<small>[Compare with first commit](https://github.com/sicksubroutine/funcy-bear/compare/8e029e5457c2e2d907a64b67d19cb49a76ce6e23...v0.0.2)</small>
