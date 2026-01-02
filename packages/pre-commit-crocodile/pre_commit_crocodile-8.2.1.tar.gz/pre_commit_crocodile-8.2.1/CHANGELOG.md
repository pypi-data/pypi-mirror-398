# Changelog

<a name="8.2.1"></a>
## [8.2.1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/8.2.0...8.2.1) (2025-12-27)

### ✨ Features

- **pre-commit:** exclude NPM lock files from large files checks ([91e6652](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/91e66524b0f4bbfcbf152bdee96e1310e469b31e))

### 🚀 CI

- **commits:** skip job when running on schedule ([36173d3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/36173d384e8af2871889849c5a9f26f77b3f87f8))


<a name="8.2.0"></a>
## [8.2.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/8.1.0...8.2.0) (2025-09-19)

### ⚙️ Cleanups

- **commitizen:** apply YAML codestyle improvements ([a8c4c95](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a8c4c95dcffdab8f465b1bc4581391303ab9d328))
- **commitizen:** add missing documentation for 'revert' ([ec680c1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ec680c102b09cdfcdb00bb02025490a56ca1c08f))
- **commitizen:** sort commits type regex in the same order ([d0ec280](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d0ec280e6022076c4f8964a4282bf8c21a8b9500))
- **commitizen:** implement 'deps' for dependencies related commits ([bb33d08](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bb33d08e393c1d98f20304505cf113b57137f367))

### 🚀 CI

- **commits:** implement 'validate_merge_commits' CI/CD input ([56fb175](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/56fb175e93a400c5b5ea5a15ec7b653dceee21ad))


<a name="8.1.0"></a>
## [8.1.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/8.0.1...8.1.0) (2025-09-16)

### 🚀 CI

- **commits:** disable 'set -x' verbose execution logs ([e012b91](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e012b9121601c638fbdb18a42fb694e935cc3967))
- **commits:** implement 'validate_commitizen_config' CI/CD input ([ba5d5e5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ba5d5e5a5951d06270a9f4e46ee795f932b0c86f))
- **commits:** implement 'validate_commitizen_range' CI/CD input ([14eee9d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/14eee9df39cf7bb2ea7e048ce6c331eaa5392022))
- **commits:** implement 'validate_hooks_checks' CI/CD input ([a507ec3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a507ec328fc37e0ea6f8592e56b9a6f59ec4091c))
- **commits:** implement 'validate_duplicated_commits' CI/CD input ([08da916](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/08da91672352b97378d57176eade685704a0ce4e))
- **commits:** implement 'validate_wip_commits' CI/CD input ([dcd6e6a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/dcd6e6a5b822107731a83b66d1e36a669111eeb0))


<a name="8.0.1"></a>
## [8.0.1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/8.0.0...8.0.1) (2025-09-15)

### ✨ Features

- **pre-commit-config:** migrate to 'prek' 0.2.1 ([5663ddf](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5663ddf6421f5d597e6a8258c87ce180ca02ed1f))

### 🐛 Bug Fixes

- **precommit:** resolve 'pip install PACKAGE1 PACKAGE2' usage ([cfe7274](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cfe7274b038ddb81476254b93e4e770cdcb9a6ee))

### 🚀 CI

- **commits:** upgrade engine if older than 'minimum_{pre_commit,prek}_version' ([d78936a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d78936ac5d5a7da24d7701ce7c3478c1cdc64676))
- **gitlab-ci:** use '$CI_SERVER_FQDN/$CI_PROJECT_PATH' for forks ([5ba2f44](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5ba2f4491c3f663c78785e54baa5e450c30fe82f))
- **gitlab-ci:** resolve 'CI_COMMIT_REF_NAME' quoting syntax ([c32a8a8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c32a8a8e8b1fdcc35eec1c8bdf421b7026dd9953))
- **gitlab-ci:** disable 'quality:sonarcloud' without 'SONAR_{HOST_URL,TOKEN}' ([bad88bd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bad88bd20bacf4b5627dc8a5b4e1f7261e396265))


<a name="8.0.0"></a>
## [8.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/7.0.0...8.0.0) (2025-09-14)

### ✨ Features

- **cli:** implement 'includes: remotes:' support and '--remotes' ([c640cb4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c640cb498aa1e9dbf1e7951a601f5ba1cd84f373))
- **pre-commit-config:** migrate to 'prek' 0.2.0 ([efaec2a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/efaec2a4d6e3e22dc5d125d9d4b3bc7adb8c3a04))
- **pre-commit-config:** migrate to 'commitizen' v4.9.1 ([731a152](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/731a1527ae19f7e81b4d30729e7bbd1fcc296cc0))
- **pre-commit-config:** migrate to 'gcil' 13.0.1 ([0d76eef](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0d76eefad0fb2d8b47e881404b662bbdd0e103fb))
- **precommit:** migrate to 'prek auto-update' usage ([9e7da0f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9e7da0f6eca3b54526fe6a81703f6728dac5cce9))
- **precommit:** configure 'prek' as default engine ([e172dd6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e172dd68cb290335fdaa4d9a755b24b81e8018d3))
- **src, requirements:** migrate to 'commitizen' 4.9.1+adriandc.20250914 ([b46a211](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b46a2118c3bb40d1e72fe5c4d85ffe4c1b91a6db))

### 🐛 Bug Fixes

- **assets:** isolate template as '.pre-commit-config.template.yaml' ([4188926](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4188926227d9949de2bb33d60cee133044b5ee68))

### 📚 Documentation

- **components:** document 'include: remote:' syntax usage ([c415801](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c4158010673de6bc5ca314ae4e5ae4b122c786be))
- **readme:** document engine settings configuration ([0b88412](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0b88412285e15fef4585333739db128959ac471d))
- **readme:** improve documentation to document provided features ([8d4c424](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8d4c424a8533457f81d218941e6104c7005264e4))
- **readme:** move 'prek' default engine first ([c9401ea](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c9401ead05423257830869ac078a2c84a3f3a7cb))

### ⚙️ Cleanups

- **assets:** use 'PACKAGE_REVISION' simpler text syntax ([b24ae12](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b24ae12a6167dff377ed8ce6d7b26a7b7a11ba99))

### 🚀 CI

- **commits:** configure 'prek' as default engine ([d07cd24](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d07cd2478718f6fca5a76106c0e444d9fe59e3da))
- **commits:** detect duplicated commits titles in checked ranges ([b675527](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b675527ad8f1624bad2eb5986731b29be7c8a848))

### 📦 Build

- **commits:** raise minimal image version to '7' ([57e2fa3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/57e2fa354bbf4bdea8819bb6a2c3557ee4d47072))


<a name="7.0.0"></a>
## [7.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/6.2.1...7.0.0) (2025-08-14)

### ✨ Features

- **cli, features:** implement 'prek' engine 'pre-commit' alternative ([e369d7e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e369d7e1d53ccde73be8f8e3e3236e44664a3b0e))
- **features:** add support for multiple 'PACKAGES' dependencies ([91d1b0e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/91d1b0ef5d8aab77d2229db9b90aa6018eeab2b4))
- **main:** implement '--set-engine' to set 'pre-commit' or 'prek' ([1db9afa](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1db9afafc0a58f8b33640ab3a7fd79bdb1a88f4b))
- **main:** add 3 seconds warning if engine setting is not done ([305a999](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/305a999595e789e648529c25486837598b55bcf8))
- **pre-commit:** migrate 'minimum_prek_version' to 0.0.25 ([db06b79](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/db06b7964ff78c11fb67801886e5cfdc3f921e9c))
- **precommit:** add support for 'prek run' output parsing ([ac36ae3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ac36ae31c2d62cd415bcfa0c34e3c858eefcd24e))
- **src:** isolate 'pre-commit' and 'commitizen' titles to constants ([16ab56f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/16ab56ffabb2d373446f7c3eb11270cb7dfb9f77))

### 🐛 Bug Fixes

- **main:** show engine warning only without a critical result ([f111b40](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f111b407e4837c669c1386b7590ff2b354daf2bd))
- **main, colors:** use '‣' symbol only in UTF-8 terminals ([bdfce45](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bdfce4558309faf01db57f2e0b9655474ea30700))
- **version:** enforce against digit only revision with 'x.y.z[-N-gSHA]' ([b9f5983](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b9f59830e34949375199f9fe09c5c17f992888c7))

### 📚 Documentation

- **readme:** document 'prek' and 'uv' as being use ([747ad94](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/747ad94ce4fb1ace84bd8adc867d3089e6635438))
- **readme, docs, setup, bundle:** improve description with 'prek' ([b0d4d6e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b0d4d6ee4cdf327e8afa5481383fd6c7b3851700))

### 🚀 CI

- **commits:** avoid 'install --install-hooks' upon local jobs ([c4aa944](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c4aa9440adb8ec4f112070982bc84c2afcb40375))
- **gitlab-ci:** bind 'commits' job locally for validation tests ([d243212](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d24321270f908a4e4e37fbdc47c549232e030887))

### 📦 Build

- **commits:** implement 'prek' optional 'pre-commit' engine ([3c5f33d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3c5f33da6eeb56b69634fb6ab4af9bdd5fe6ea44))
- **commits:** optimize Rust compiler caches out of the image ([e132755](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e13275584218dab883c027aae73f3d2532193c3a))
- **containers/rehost:** revert to Debian 12 'python:3.13-slim-bookworm' ([287673a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/287673a731e32dd5f8fd62a6d16c7eebf03ccce6))
- **requirements:** upgrade to 'playwright' 1.54.0 ([bd5fa6d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bd5fa6d8ac781451bb9ac7c6a49744d58e3e6722))
- **requirements:** install 'prek' 0.0.25 and 'uv' 0.8.10 ([1199962](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1199962a071c5dcb87ad6bf8eed338d1d1eadb60))


<a name="6.2.1"></a>
## [6.2.1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/6.2.0...6.2.1) (2025-08-13)

### ✨ Features

- **entrypoint:** create missing 'README.md' if '--badges' used ([1352f4b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1352f4b83a35ffa924284d0eeed8017ad19694bf))

### 🐛 Bug Fixes

- **entrypoint:** avoid 'git commit' if no differences added ([6174883](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6174883754275cb7bdd7377a3bb8a70551118238))
- **entrypoint:** add missing '--badge' header and output flushes ([8fa468b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8fa468b983fe9ec4b8d0f9c38d01dfa78bf3e6de))
- **entrypoint:** re-inject partially missing badges properly ([1117ea3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1117ea3f0a2d27f96c92dc3f83671c439f80fb02))
- **entrypoint:** resolve unreliable 'README.md' badges line endings ([a46036e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a46036ed7754c0bc3dabbdfde4de68c47ffb28c4))
- **main:** avoid '--configure' if '--commit' is used with '--badges' ([f7ee29a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f7ee29aa2191518864b6f16d3bc75c42cee95956))

### 🚀 CI

- **gitlab-ci:** remove redundant 'before_script:' references ([41fae52](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/41fae52f645f11983637600f20c848f6d28a19fa))


<a name="6.2.0"></a>
## [6.2.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/6.1.0...6.2.0) (2025-08-11)

### ✨ Features

- **entrypoint, features:** fix configure without 'git' repository ([6719a65](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6719a653511b8d846d5604c495a36959e885a753))
- **main:** automatically imply '--configure' if '--commit' is used ([0105b4a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0105b4a5d35eae046f63371e1f71d90cb081026f))
- **pre-commit-config:** migrate to 'pre-commit-hooks' v6.0.0 ([f8b3d22](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f8b3d228c964a34b4fc3f9699662c1b253ddc5fe))
- **pre-commit-config:** migrate to 'gcil' 13.0.0 ([17f7069](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/17f70698f6d148dfd45fefc50c7e5bc7c3f7885c))

### 🐛 Bug Fixes

- **check_commitizen_branch:** ignore missing remote branches ([f6ba7b4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f6ba7b4ffc4ccfabe0ae01388ab0006dffac7b76))
- **entrypoint:** register '.gitlab-ci.yml' file configurations ([655b243](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/655b24340bb1795d3c393d7d2a8a6704aa36f330))
- **entrypoint:** resolve handlings of empty 'README.md' file ([d877ba0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d877ba0dbf361406fbd4fbafb3761df13dcf3762))
- **entrypoint, git:** resolve diff on untracked files with intend add ([a97c10d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a97c10df7d6d65ff8933054432a116f59ec4ab08))

### 🚀 CI

- **commits:** implement 'skip' CI/CD input to exclude pre-commit hooks ([3235ab4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3235ab47cdf4a49632e50ebed21fb28380012d4f))
- **gitlab-ci:** implement GitLab tags protection jobs ([cf6f446](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cf6f44662ed5a28dda9ef1c585dcdf776ca9c518))

### 📦 Build

- **commits:** install 'git-lfs' in the 'commits' image ([15c48e3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/15c48e37293d3cda552b7d5f35dd67aa97a68149))
- **commits:** install 'bash' in the 'commits' image ([e76a933](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e76a933e846d3284cf2272b74fb78512afba38ea))


<a name="6.1.0"></a>
## [6.1.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/6.0.0...6.1.0) (2025-07-29)

### 🚀 CI

- **commits:** validate 'commits' minimal image version ([abb3fbb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/abb3fbb02fd019021f193d7cd7497ee0b91c54ef))
- **commits:** resolve '.git/hooks' user ownerships ([3a3601b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3a3601b25cf2e1eab8ab73ef45c3ee96006ab86c))

### 📦 Build

- **containers/commits:** install 'coreutils' for 'chown --reference' ([e71b38c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e71b38cb27d3655f362f86c02d196193cce2e4fd))
- **containers/commits:** create '/VERSION' version marker file ([ed76432](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ed76432dda2dbccafc222d3701135dcae47d64fe))


<a name="6.0.0"></a>
## [6.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/5.1.0...6.0.0) (2025-07-21)

### ✨ Features

- **cli:** implement '--components' to force online components ([3687cc1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3687cc1759c588ac5eb7505a4ca31957ca7cfba4))
- **cli, git:** detect 'gitlab.com' remote to configure local components ([01f7d0c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/01f7d0cfbb07120fb95c9d606ffaa5b878b28955))
- **commitizen:** ensure single space after 'type(scope):' ([4d80a55](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4d80a55ce760bf46811c040125f73d65e8e7b54a))
- **entrypoint:** improve '--configure' output delays timings ([e56496c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e56496cb857180dd85588a9a38ea6abeb856396c))
- **entrypoint:** run 'pre-commit autoupdate' upon configuration ([bcfe530](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bcfe530e753f9d1c61a09f40fe5f6a675dc1ac3b))
- **entrypoint:** prepare '.gitlab-ci.yml' configuration for 'stages' ([c731e3e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c731e3e55c07ea504483e190efe58fff4ff14599))
- **entrypoint:** enable 'pre-commit' after '--configure' steps ([9ea730d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9ea730d047085418fc90ff9a095db67654339d93))
- **entrypoint:** implement components binding to '.gitlab-ci.yml' ([0b2a028](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0b2a0289431bd52f2bf6a9284823540d9896bb18))
- **entrypoint:** avoid Commitizen check calls without commits ([0fd63d3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0fd63d3ed3d48ec392b4a7685dee8f3622e37a68))
- **entrypoint, git:** avoid 'git commit' if no differences added ([3a34920](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3a349201d4e163d4ef3d2dedda63718f9644d8d6))
- **entrypoint, git:** avoid Git sources hints if no differences ([11c0fa4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/11c0fa4af8c7dddee7fcce12dab6c4b6cefb0baa))
- **entrypoint, precommit:** disable configurations hooks for users ([85ab407](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/85ab407e1d9b069497e29951859023cc48239496))
- **hooks, pre-commit:** implement 'check-commitizen-branch' wrapper ([e0b148f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e0b148f41dd2b42c65b7dfd49362a13083afe4c9))
- **pre-commit-config:** migrate to 'pre-commit-hooks' v5.0.0 ([83ae2a3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/83ae2a31a76d8a8dea1f3459b0fe3e6906c3e7ff))
- **pre-commit-config:** migrate to 'commitizen' v4.8.3 ([6e4fa36](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6e4fa36d52a135592c29837620d87f3f1cf9f443))
- **setup:** add support for Python 3.13 ([7386afd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7386afd8155b36e090338f6cf5213eacccc36284))

### 🐛 Bug Fixes

- **commitizen:** ignore error '23' if checking non-existing ranges ([a0056cd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a0056cd05a3a6846001a759bc0fd00da4dc4077a))
- **configurations:** resolve support for files starting with '.' or '_' ([06dde1f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/06dde1fbb2433327dfaa4ae639c2a081c3a3247e))
- **configurations:** fixup 'LICENSE', 'README', 'CHANGELOG' matchers ([71fb3f1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/71fb3f12652bdbe741eb3d70109ae89dd4c58489))
- **entrypoint:** resolve Git commit command hints ([52c3f5d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/52c3f5d371756689a11e6269e361e198d7cd8e8e))
- **pre-commit:** resolve deprecate 'pre-commit' stages names ([fa278b1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fa278b104f502cf66a97bf59d16f36c61fa077ce))
- **pre-commit-config:** ignore remotes without 'set-head -a' ([7db090c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7db090c9d1ff983abda53d17aadd33661d71554d))

### 📚 Documentation

- **mkdocs:** embed coverage HTML page with 'mkdocs-coverage' ([cec6d3d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cec6d3d245209a05f1c996ae09067713033d5e00))
- **prepare:** prepare empty HTML coverage report if missing locally ([73cbba8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/73cbba8f1ee3d32cc9e4c295addc44bc6bf7e5f1))
- **readme:** document 'mkdocs-coverage' plugin in references ([284b684](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/284b684e506819eed001749d73f54ac98b077f89))

### 🎨 Styling

- **precommit:** create 'HOOK_...' constants for reuse ([6189105](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/618910571381e1d277332189a036d2c92f81f136))

### 🧪 Test

- **platform:** improve coverage for Windows target ([016f7c6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/016f7c6b4209e6f41008f342b2b22abc5e4f181c))

### ⚙️ Cleanups

- **gitlab-ci, docs, src:** resolve non breakable spacing chars ([35fccd6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/35fccd69b9950e563975a0237d79ddeca20cc56e))
- **strings:** remove unused 'random' method and dependencies ([04ec7b9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/04ec7b9fa925054c9a64922a50fd0387b261b4d5))

### 🚀 CI

- **gitlab-ci:** bind coverage reports to GitLab CI/CD artifacts ([f2ab6a9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f2ab6a9f896c7d3f7b42357f234fecc2da656e37))
- **gitlab-ci:** configure 'coverage' to parse Python coverage outputs ([c90c1a7](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c90c1a73063e025e71aa0a4fca9e3b3876e04a01))
- **gitlab-ci:** always run 'coverage:*' jobs on merge requests CI/CD ([e0cbbbb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e0cbbbbaf2788b919aa8f2e5173e12d61952ca78))
- **gitlab-ci:** show coverage reports in 'script' outputs ([24fcdf0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/24fcdf076102c499f5e4369beaad63044aeb2eb6))
- **gitlab-ci:** restore Windows coverage scripts through templates ([bf85f89](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bf85f8966decf8eea60fe8b415ae02a5fc9dabc1))
- **gitlab-ci:** resolve 'coverage' regex syntax for Python coverage ([c99b19d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c99b19d20f3e613fa4e0de487d016fd3282fabb8))
- **gitlab-ci:** resolve 'coverage:windows' relative paths issues ([1f98024](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1f98024afc3b756039ab577a33a1394d9387347e))
- **gitlab-ci:** run normal 'script' in 'coverage:windows' with 'SUITE' ([101b4ba](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/101b4ba891899f4ff1033a7ab604d128e18d4629))
- **gitlab-ci:** use 'before_script' from 'extends' in 'coverage:*' ([527d924](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/527d92430e1c92a2c70787eb5971d7618bd6e287))
- **gitlab-ci:** run 'versions' tests on 'coverage:windows' job ([ead73e3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ead73e32b4031825147693097e87a8c726e6560e))
- **gitlab-ci:** fix 'pragma: windows cover' in 'coverage:linux' ([7350ef1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7350ef14cd742532a10275769cb68754832931a3))
- **gitlab-ci:** run 'colors' tests in 'coverage:windows' ([7c6cf41](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7c6cf415e049aeaf6569a58448e3f6e2014ac00d))
- **gitlab-ci:** add 'pragma: ... cover file' support to exclude files ([154b070](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/154b07097a26704af8858f3e8870d601d9499459))
- **gitlab-ci:** isolate 'pages' and 'pdf' to 'pages.yml' template ([302293f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/302293fff0f3cf6f838d5bf4ace69638d1b9f5a6))
- **gitlab-ci:** isolate 'deploy:*' jobs to 'deploy.yml' template ([5c46db3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5c46db341f8a8deaba6015c1df57217ac7e17196))
- **gitlab-ci:** isolate 'sonarcloud' job to 'sonarcloud.yml' template ([8364828](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8364828eafc3ff2310f7c5dfa6c800af8f362bd3))
- **gitlab-ci:** isolate 'readme' job to 'readme.yml' template ([ce6ab32](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ce6ab3290ad51b15a6512fd6bfe926a53ba56fd7))
- **gitlab-ci:** isolate 'install' job to 'install.yml' template ([eee29b1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/eee29b1dc6235b3a1fb1cafae0ff4b320027a2b8))
- **gitlab-ci:** isolate 'registry:*' jobs to 'registry.yml' template ([3648720](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3648720750614c6295b8e16fa573e14fa6f91b03))
- **gitlab-ci:** isolate 'changelog' job to 'changelog.yml' template ([fef22df](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fef22dfb2efcee86261dffae4d46b0fa9f1336a3))
- **gitlab-ci:** isolate 'build' job to 'build.yml' template ([b048157](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b048157e545f07dfef1ded0241168636d70dcc55))
- **gitlab-ci:** isolate 'codestyle' job to 'codestyle.yml' template ([e9067d2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e9067d2eb559a60f1129de2e53246c93eb7af3f8))
- **gitlab-ci:** isolate 'lint' job to 'lint.yml' template ([311b16c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/311b16ce267ced9ac80c3c9b4c32b165cd71ac99))
- **gitlab-ci:** isolate 'typings' job to 'typings.yml' template ([9e9a91a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9e9a91ae441dff4340790ec664521958060bc1d0))
- **gitlab-ci:** create 'quality:coverage' job to generate HTML report ([251d92c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/251d92c1213850737a141a17efd9fc0f583dd551))
- **gitlab-ci:** cache HTML coverage reports in 'pages' ([3644fa3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3644fa32e77c73e2d36049166d5758c8b4d6a4fd))
- **gitlab-ci:** migrate to 'quality:sonarcloud' job name ([8823190](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/88231900aae85c1e5916071b007ff347d9980b3f))
- **gitlab-ci:** isolate 'clean' job to 'clean' template ([52ffbd2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/52ffbd2c0ccc5223763be561141b95e05b35cf3a))
- **gitlab-ci:** deprecate 'hooks' local job ([cd2ad39](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cd2ad39d8d58770f1c24cd3cb2e2f2a61c79b782))
- **gitlab-ci:** use more CI/CD inputs in 'pages.yml' template ([e2c5265](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e2c5265805b6d99da2139acdfe7bf49107c123eb))
- **gitlab-ci:** isolate 'preview' to 'preview.yml' template ([62573ba](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/62573ba8b780637a2af51e4b474d43458fd841b2))
- **gitlab-ci:** isolate '.test:template' to 'test.yml' template ([b39091c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b39091cf852c25fbba25c304aeb8731675d993bd))
- **gitlab-ci:** isolate '.coverage:*' to 'coverage.yml' template ([1c494fc](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1c494fc9e478171c3874cf4f52a2a943d569d452))
- **gitlab-ci:** raise latest Python test images from 3.12 to 3.13 ([3365d45](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3365d450b9bedeab0cce06c2aaa06e2bd281bf64))
- **gitlab-ci:** migrate to RadianDevCore components submodule ([9a9dc89](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9a9dc89812d243e03a403295e8f9fdabaa58e2b1))
- **gitlab-ci:** isolate Python related templates to 'python-*.yml' ([fa28d12](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fa28d12b83a9a93708e3e34acfb4f539de3bfb52))
- **gitlab-ci:** migrate to 'git-cliff' 2.9.1 and use CI/CD input ([3d17254](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3d172543feb08119327eef0c5bd25807968a41a8))
- **gitlab-ci:** create 'paths' CI/CD input for paths to cleanup ([fb425b0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fb425b0668102e590f3102ecc227e8de4ffa19ec))
- **gitlab-ci:** create 'paths' CI/CD input for paths to format ([c6459b3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c6459b37c4a0c037208b72637e9c1e0577646189))
- **gitlab-ci:** create 'paths' CI/CD input for paths to check ([0a8da54](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0a8da54ebff730478375302cb587372a9e3ccac2))
- **gitlab-ci:** create 'paths' CI/CD input for paths to lint ([2d78cb2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2d78cb242ffcbc1ecfd8aa211e8e715ac3b17b5e))
- **gitlab-ci:** create 'intermediates' and 'dist' CI/CD inputs ([d04cb26](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d04cb26738dcdbd60f7618c3a9adb8caffd66c8d))

### 📦 Build

- **pages:** install 'coverage.txt' requirements in 'pages' image ([e28dc56](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e28dc56e996ca1e40c73bcdd5016abd878e11a41))
- **requirements:** install 'mkdocs-coverage>=1.1.0' for 'pages' ([72fb372](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/72fb372daa4fe026244fcfdf9d74dfeefe7475f0))


<a name="5.1.0"></a>
## [5.1.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/5.0.0...5.1.0) (2025-06-09)

### ✨ Features

- **cli:** implement '--no-components' to import 'commits.yml' template ([c3a6999](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c3a6999908adbc4886dc2767938c8e32c3dbf6e9))
- **gcil:** raise minimal 'gcil' version to 12.0.0 ([0ac2606](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0ac26061767becf86d1b1e7c48b81fd676da3701))
- **templates:** refactor '--no-components' with 'spec: inputs:' ([c2f7365](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c2f7365fb3eb9f29dc4eff575d48199ee67b10a2))

### ⚙️ Cleanups

- **cz:** migrate from 'multiple_line_breaker' to 'break_multiple_line' ([8068901](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8068901bb1811be110a0007b755367fb1bf62aef))

### 🚀 CI

- **gitlab-ci:** migrate to 'CI_LOCAL_*' variables with 'gcil' 12.0.0 ([e8cdad9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e8cdad9589f92e7a591313a0321b0529c9874d77))


<a name="5.0.0"></a>
## [5.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/4.2.1...5.0.0) (2025-06-08)

### ✨ Features

- **cli:** add '--commit' to automatically commit '--configure' changes ([6f4dd94](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6f4dd94259c9a6498b9a6eefa8c796dcb37ff8dc))
- **cli, gcil:** implement '--offline' to disable initial autoupdate ([bd1ef50](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bd1ef50f1871c13a45184ab2d87dc12382baa5c5))
- **commitizen:** migrate to 'AdrianDC/commitizen' sources tag ([7a925bc](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7a925bca39a46fa2323eafef4e16dd91cb9ce5f1))
- **entrypoint:** improve '--configure' command hints for updates ([659cc3e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/659cc3ed513c667c33c722ed48a41f260c059826))
- **entrypoint:** run '--run' steps in '--enable' if supported ([ab1720c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ab1720caa0173936a7c9997284372274f368468d))
- **requirements, src:** migrate to 'commitizen' 4.8.2+adriandc.20250608 ([ffd5ea9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ffd5ea982b6bb0dadaf95875a61cddbeee2d8332))
- **src:** refactor section headers style and look closed to 'gcil' ([1b34aef](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1b34aefd09983549e155ff4a1773aca5da413099))

### 🐛 Bug Fixes

- **version:** migrate from deprecated 'pkg_resources' to 'packaging' ([314bf0d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/314bf0de218060412f59cdbea87448a755db2359))
- **version:** try getting version from bundle name too ([79450cf](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/79450cf8afe598f46eae0e39dd4b986962481c6c))

### 📚 Documentation

- **commits:** document 'cz commit --edit' syntax ([e848a43](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e848a438b7ae79763a25cc44d19061e2e1912664))

### ⚙️ Cleanups

- **pre-commit-config:** explicit 'commit-msg' stage for 'commitizen' ([adc0f35](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/adc0f358145878e41f84645591bf58da1292d9d5))
- **vscode:** install 'ryanluker.vscode-coverage-gutters' ([1f44dbb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1f44dbb3a89455d2292e01defc9983dbec5fa7e4))
- **vscode:** configure coverage file and settings ([641d6af](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/641d6afaf3d28c039978d9af0480d154e0e5df6b))

### 🚀 CI

- **coveragerc, gitlab-ci:** implement coverage specific exclusions ([2badbc5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2badbc5d11cdadfbfa4039d7822e2d4d89cbbe24))
- **gitlab-ci:** improve combined coverage local outputs ([2b31171](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2b311712fe84d716d6bed4b50c5d6eb73ec6df73))
- **gitlab-ci:** enforce 'coverage' runs tool's 'src' sources only ([9bdf726](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9bdf72624086b33d623e7435b33c65d293d539a2))
- **gitlab-ci:** add support for '-f [VAR], --flag [VAR]' in 'readme' ([8396c68](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8396c689b4fc99b8bf86afe6e112feabd7f5bf66))

### 📦 Build

- **requirements:** add 'importlib-metadata' runtime requirement ([43f298f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/43f298f39b0437a71c454313d798ceb2f514d96e))


<a name="4.2.1"></a>
## [4.2.1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/4.2.0...4.2.1) (2025-05-31)

### 🐛 Bug Fixes

- **precommit:** fix mismatching excludes upon '--configure' ([039a2da](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/039a2da953da11f48e4fa505ddf32f38322b8d98))


<a name="4.2.0"></a>
## [4.2.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/4.1.0...4.2.0) (2025-05-31)

### ✨ Features

- **entrypoint:** avoid 'sleep' calls without user input TTY ([e3ecb29](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e3ecb29f87fbc505d8eec491733809cc56a8a8a6))
- **pre-commit-config:** exclude '.md' files from 'trailing-whitespace' ([db98cc2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/db98cc22984380e4f47f16b3f6cd425db98d57ad))

### 🐛 Bug Fixes

- **pre-commit:** fix empty hooks with 'hooks: []' upon '--configure' ([3ef9cbe](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3ef9cbe3cebcc9627bd4510a519b13ce41cdfd89))

### ⚙️ Cleanups

- **pre-commit:** migrate to 'gcil' 10.2.0 ([257ec3a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/257ec3ac7a0efcce32aa759c049a3977cc485537))

### 🚀 CI

- **gitlab-ci:** remove unrequired 'stage: deploy' in 'pdf' job ([e07a8f2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e07a8f29b735772357cd1235d7d76a39345ec0f9))


<a name="4.1.0"></a>
## [4.1.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/4.0.0...4.1.0) (2025-05-31)

### ✨ Features

- **configurations:** implement support for '.gitmodules' files ([f4f452d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f4f452d51ead15299a65d8b9a536a1d48e17be42))
- **configurations:** implement support for 'Dockerfile' files ([dfb036c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/dfb036c3d97f401c9afc0b31faa5ce09a0d039a7))
- **configurations:** add support for 'scripts/' commit messages ([274516d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/274516d3d81ffc48c0d58e70e19b546a172d19f8))

### 🐛 Bug Fixes

- **hooks:** resolve changes detection for 'path.ext -> path.ext2' ([6a53954](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6a53954af6a003b7ade8dfcc14ffcefcf55d382b))

### 📚 Documentation

- **license, mkdocs:** raise copyright year to '2025' ([ba17df1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ba17df10a19c3d450678b5f128a27daeb3529982))
- **prepare:** avoid 'TOC' injection if 'hide:  - toc' is used ([b6664ff](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b6664ff041282057eaed12a89612e283a20c1882))

### 🎨 Styling

- **colors:** ignore 'Colored' import 'Incompatible import' warning ([6b04f76](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6b04f76c1800e40e303ceed028646d6f6ac4404c))

### ⚙️ Cleanups

- **sonar-project:** configure coverage checks in SonarCloud ([e526d65](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e526d65cc3453e0c1de5088ff799d2ef307d0acc))

### 🚀 CI

- **commits:** disable submodules clone with 'GIT_SUBMODULE_STRATEGY' ([87e2b11](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/87e2b11a55ad0dc4d4116f70360ae6bcdf82ec32))
- **commits:** ensure './.cz.yaml' is always being used by 'git cz' ([d7038a5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d7038a5579261727a4dc845d15da16a7be622ead))
- **gitlab-ci:** ensure 'pages' job does not block pipeline if manual ([b4ed026](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b4ed0267cd180eac766c18b17b2d2ab3e0f901f6))
- **gitlab-ci:** change release title to include tag version ([a9a8a53](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a9a8a53b7a22d4be42eab3ab7c776d3c1bd19813))
- **gitlab-ci:** run coverage jobs if 'sonar-project.properties' changes ([cca4330](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cca433013b774614af4c25302cda283b0f53c85d))
- **gitlab-ci:** watch for 'docs/.*' changes in 'pages' jobs ([582f84f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/582f84fd969448a3f5ee047fcaa70d699d4260f0))


<a name="4.0.0"></a>
## [4.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/3.1.0...4.0.0) (2025-01-01)

### ✨ Features

- **cli:** implement '--badges' option as partial '--configure' ([a63468f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a63468fe895815ecdd8f40cf0f7b5f9804094f10))
- **cli:** inject RadianDevCore Guidelines badge automatically ([fef9c67](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fef9c676b37525ef7c84606015306169b170aec8))
- **commitizen:** accept '[Ww][Ii][Pp]' types without casing ([9d85387](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9d85387033264071c7bd62a6bf807bc606ab0544))
- **configurations:** add matchers for 'tsconfig.json' files ([72fa06e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/72fa06e9dbff1a2fd2f8aac4e0bae527392107bb))
- **hooks:** implement 'check-yaml-ruamel-pure' hook with pure 'ruamel.yaml' ([295b39b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/295b39b6d681fb54b066c92f4dd8f21df304945e))
- **hooks:** handle 'res' and 'resources' in 'prepare-commit-message' ([37c5854](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/37c58543d7a11a4c7bf1d4214d54a04a882e42eb))
- **pre-commit:** exclude Vivado '.vhd', '.xci' and '.xdc' files ([fe8ffab](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fe8ffab4f9caef7b84315300c23b1bc2bd488bd9))
- **pre-commit:** exclude '.nmconnection' from 'check-case-conflict' ([60cde89](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/60cde891a9d045a22255863b54a3f40c8db3090a))
- **pre-commit-config:** enable 'check-yaml' by default ([906d11c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/906d11c33430f6f7f8cfd4f2a61c91220a474d52))
- **pre-commit-config:** enable 'detect-private-key' by default ([6c3222b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6c3222ba7954a980b63fdbd251e1bc9b6100adc5))
- **pre-commit-config:** exclude 'archives/' root folder from cz checks ([0ea05c4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0ea05c4237c96ba4294451ec06547d387b7c5c06))
- **prepare_commit_message:** always lowercase the commit's scope ([69a8510](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/69a8510195cab220ad018a8e2c634469a17e5c02))

### 🐛 Bug Fixes

- **cli:** use package name for 'Updates' checks ([3d6c4c5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3d6c4c5a047c618692e1876630ce3cc0f4fb5707))
- **configurations:** fix '.' regex syntaxes in 'prepare_commit_message' ([be01676](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/be016761f8a9f45bc8e706b70df9419b54caba1a))
- **git:** fetch the remote before updating remote HEAD pointers ([2c1713f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2c1713ff57e3144871f13586a0218e7eae1227c7))
- **main:** ensure 'FORCE_COLOR=0' if using '--no-color' flag ([a1d79e4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a1d79e4a9b8dc0c83e360b708f056515d83a004a))
- **pre-commit:** add missing 'commit-msg' stage for commitizen ([24af224](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/24af224006db1678db57f81e04d2e4941854850d))
- **pre-commit-config:** disable 'check-yaml' hook by default ([cda428c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cda428ce9acb7eb38c65f513e0f39aa3d82ffb79))
- **pre-commit-config:** exclude '.drawio' files from 'pre-commit' ([74398c5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/74398c55cfa53aa24e1a78e654d495ec4186b649))
- **pre-commit-config:** resolve 'README.md' regex file name ([08154eb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/08154ebbb42a7e238ff14ab8d562cd7c930edb94))

### 📚 Documentation

- **assets:** prepare mkdocs to generate mermaid diagrams ([41cf08a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/41cf08a12f97f6ab6ec30dfe1dc24fa2bb38871d))
- **commits:** isolate generated documentation into included file ([bdc1796](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bdc17965b5cb3b72e7a838bf288d1e17106e50f7))
- **covers:** resolve broken page header / footer titles ([b3b6906](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b3b6906df57cf54205843912601b22a77c3d9f6c))
- **custom:** change to custom header darker blue header bar ([06623e7](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/06623e77757be2328d15aec35860affe7bd3d848))
- **docs:** migrate to page breaks using 'span' elements ([8828f38](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8828f38940ddd3e95acc28a4c8a2d9e5e11f0115))
- **docs:** improve documentation PDF outputs with page breaks ([7e287ba](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7e287bab38ec0640ee3a3652846815a2c2e9d73f))
- **hooks:** refactor and improve 'check-yaml-ruamel-pure' documentation ([77e7662](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/77e7662de27130754b9fdde8da507f522fa330c9))
- **mkdocs:** enable 'git-revision-date-localized' plugin ([3b055c0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3b055c0651b7d1b145ee4dd6172088bf3be6830d))
- **mkdocs:** change web pages themes colors to 'blue' ([5d504b6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5d504b69bd7d6da41ec92ecc5c320d7226463ebf))
- **mkdocs:** fix 'git-revision-date-localized' syntax ([151d0f9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/151d0f9f5bf1de90fe6b18f5d1459b77c54eb85b))
- **mkdocs:** migrate to 'awesome-pages' pages navigation ([f1ec64b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f1ec64b502ad27723ac0865287052f18da9759b9))
- **mkdocs:** change 'auto / light / dark' themes toggle icons ([1113338](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/11133380a2f49e9d9643cf5cfe06e9c4dadf02c3))
- **mkdocs:** enable and configure 'minify' plugin ([39236c6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/39236c6e31cc68b85277e05d69613b7fb87a26d2))
- **mkdocs:** install 'mkdocs-macros-plugin' for Jinja2 templates ([a898280](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a8982801dd66ea3ec0ec9b280a8f7cef88abe1f9))
- **mkdocs:** enable 'pymdownx.emoji' extension for Markdown ([8289f48](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8289f487be532975ebcadb08c981d55d32cb025d))
- **mkdocs:** implement 'mkdocs-exporter' and customize PDF style ([66cb7ff](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/66cb7ffff74b1bfefd2510ec446847609a65daff))
- **mkdocs:** set documentation pages logo to 'solid/code' ('</>') ([7a57a85](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7a57a85e74daa82875510bd009824df5a257edf5))
- **mkdocs:** enable 'permalink' headers anchors for table of contents ([82d4019](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/82d4019f6baa38460c5335ee02f6fefb90f1a948))
- **mkdocs:** prepare 'privacy' and 'offline' plugins for future usage ([86bd751](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/86bd751602d046c401e0e94af2e32f8ca74220b2))
- **mkdocs:** disable Google fonts to comply with GDPR data privacy ([8d369d8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8d369d8ae35543358d3cd185136f22cfb5e108b4))
- **mkdocs:** implement 'Table of contents' injection for PDF results ([7fa333e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7fa333e4a1bdad1c705add4324077fe1058ec7e4))
- **mkdocs:** enable 'Created' date feature for pages footer ([59237fd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/59237fd599f61e3ec287d26c3dd4ef0cf49ba57a))
- **mkdocs:** add website favicon image and configuration ([f740eda](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f740edaba0f9c0f8578196ee7b2a29cc258d1b62))
- **mkdocs:** implement 'book' covers to have 'limits' + 'fronts' ([32ac6a1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/32ac6a135b8345073b8fb3bd7c2e4a99835c0414))
- **mkdocs:** isolate assets to 'docs/assets/' subfolder ([d6e55e3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d6e55e3b41f630a290976271fc4f2ade588e5f87))
- **mkdocs:** exclude '.git' from watched documentation sources ([524010c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/524010c7727f84c2de9a1b2b239b3b89cc248a73))
- **mkdocs:** minor '(prefers-color-scheme...)' syntax improvements ([82efc4c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/82efc4c4086c5cd1a5cd12b8cb450f5950038f87))
- **mkdocs, pages:** use 'MKDOCS_EXPORTER_PDF_OUTPUT' for PDF file ([890acf6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/890acf6dd7667a212a8ae29ae3ca26a3b00a0723))
- **pages:** rename index page title to '‣ Usage' ([25fd14f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/25fd14f81524ca38503fbf2ca2dc2d04d643727a))
- **pages:** rename PDF link title to 'Export as PDF' ([13e5bc2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/13e5bc2c1138e398ea5c8f25f183ba422437b7a3))
- **pdf:** simplify PDF pages copyright footer ([371c84a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/371c84aa6fe5998bb8b6056b3d8e284da541c894))
- **pdf:** migrate to custom state pseudo class 'state(...)' ([f3bdb3c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f3bdb3c3d596d1ec7d4aff98c2e684b48f525c2d))
- **pdf:** avoid header / footer lines on front / back pages ([ea28186](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ea28186224b95f0be40751ce76d43a3dc04ba7b4))
- **pdf:** minor stylesheets codestyle improvements ([5800649](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/580064945f3d7d8036725ea1eef1fba7168b9107))
- **pdf:** reverse PDF front / back cover pages colors for printers ([cf420dd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cf420ddb79435b5743e0b0a36c181bff543d9422))
- **prepare:** avoid 'md_in_html' changes to 'changelog' and 'license' ([e82ff9e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e82ff9e542b9e083ba7be296fda89113238ed7f1))
- **prepare:** fix '<' and '>' changelog handlings and files list ([d13f57f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d13f57f602f266bedbd846b634604026bde76d97))
- **prepare:** implement 'About / Quality' badges page ([3180bdb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3180bdb6521b19d8991b24aa8e5967e86373b814))
- **prepare:** improve 'Quality' project badges to GitLab ([7624936](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7624936505ccc5685d64e0ca32acba03a9f7856d))
- **prepare:** use 'docs' sources rather than '.cache' duplicates ([121c343](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/121c343e50ab85d233f377119ae4fc465f31e89d))
- **prepare:** resolve 'docs/about' intermediates cleanup ([0e09ba4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0e09ba4284be2f7637cf6340bdf1fdae57ab5f60))
- **prepare:** add PyPI badges and license badge to 'quality' page ([28950ac](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/28950acac5bf2151b2f0eb7a9a7587ce280a36ef))
- **prepare:** avoid adding TOC to generated and 'no-toc' files ([e9c6231](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e9c62314ece8a5264a0b4a78d98575920077f60c))
- **prepare:** use 'mkdocs.yml' to get project name value ([3b8b36b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3b8b36bf644c25d23587b40e7df81800f179e343))
- **readme:** add pypi, python versions, downloads and license badges ([2747e58](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2747e5818e481cf06475f251bc88904b1611fc3f))
- **readme:** improve projects documentation for developers ([e1d01b5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e1d01b5f5f158bb903a9faf4cf9b55470e66e8e1))
- **robots:** configure 'robots.txt' for pages robots exploration ([3e3347a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3e3347a28bd4d5a8f78594b2421729ce089d06bf))
- **stylesheets:** resolve lines and arrows visibility in dark mode ([b2a6c4f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b2a6c4f9cf09285cd411c9ed3453c6d70488b64b))
- **templates:** add 'Author' and 'Description' to PDF front page ([920d5d9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/920d5d9bc5e2613a6c21889d18f400c88d7dd9dc))
- **templates:** add 'Date' detail on PDF front page ([a3c66ee](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a3c66eed6c260631c1c4bf478d9ac5079790b195))
- **templates:** use Git commit SHA1 as version if no Git tag found ([2348bec](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2348bec935305a625ff085c6b5ecd8c3d34b6c55))

### ⚙️ Cleanups

- **bundle, readme:** minor codestyle and syntax improvements ([cb46ca3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cb46ca384f06bf41bf81369173a66c71f5e5f6cb))
- **gitignore:** exclude only 'build' folder from sources root ([339d183](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/339d1834c006435c6adb0162de5792cf513d9f99))
- **gitignore:** exclude '/build' folder or symlink too ([28b7a69](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/28b7a69a580fdee7f048f37cd7d39d5eab4d5ecb))
- **hooks:** resolve 'too-many-positional-arguments' new lint warnings ([c30f7fc](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c30f7fcba03488daef5cfa2b5de1aed6d81b0219))
- **pre-commit:** disable 'check-useless-excludes' hook ([75f8ec3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/75f8ec32cfc9eddc4644c618c331c942971aa78e))
- **pre-commit:** exclude '.drawio' diagrams and images files ([0773900](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0773900aa78a37c3ba028f6dc01d399e222a7497))
- **vscode:** use 'yzhang.markdown-all-in-one' for Markdown formatter ([533b56d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/533b56df683a30f7b98be1d9556eaa8f78c0c398))

### 🚀 CI

- **build:** add missing 'containers/build/Dockerfile' to tracked files ([3f07bc8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3f07bc8cce617e6b979a8d34750dd2a0f0c8c795))
- **commits:** minor GitLab CI job logs readability improvements ([29eb6f4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/29eb6f47d0986ad95ef258c6954a397915e21eb9))
- **commits:** add 'name' component input configuration for job name ([d8e274b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d8e274b22cf7f94fc704431b5330fe87834ddd0d))
- **commits:** resolve and support single-commit Git histories ([f6bf4bb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f6bf4bb856d7e0e14f31c668710557a9cc88f33e))
- **commits:** validate 'HEAD' has a parent commit through 'git log' ([968ca51](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/968ca51decf769a983a7c7aec70d568032dcb4bd))
- **gitlab-ci:** enforce 'requirements/pages.txt' in 'serve' job ([61e3737](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/61e3737983ccaa742f4d3bd1ebf1476e0438459e))
- **gitlab-ci:** add 'python:3.12-slim' image mirror ([daa7287](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/daa7287a89050323fe3b14944dc7a116d1e0cfb8))
- **gitlab-ci:** inject only 'mkdocs-*' packages in 'serve' job ([67fa3c2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/67fa3c26f63e4d32718fcc3c015f086652363775))
- **gitlab-ci:** install 'playwright' with chromium in 'serve' job ([cefbcff](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cefbcffff9da01ecacd89047e6719178a115fe7a))
- **gitlab-ci:** improve GitLab CI job outputs for readability ([8a8e69f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8a8e69f2aafde93cc74a4bf6fd9b9806360bc119))
- **gitlab-ci:** deploy GitLab Pages on 'CI_DEFAULT_BRANCH' branch ([f34cf59](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f34cf59ff8aa4856898955cb8fcf6347e4ecfb3b))
- **gitlab-ci:** find files only for 'entr' in 'serve' ([6c37678](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6c3767830aa3903ffe42e23b6cc5c0b0b2d19f27))
- **gitlab-ci:** ignore 'variables.scss' in 'serve' watcher ([144f35b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/144f35b1beda57e4aac892d29df1c28e83a905ab))
- **gitlab-ci:** preserve only existing Docker images after 'images' ([14c2217](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/14c22175aba83917a898f6d02ae4e0520bc8d921))
- **gitlab-ci:** use 'MKDOCS_EXPORTER_PDF_ENABLED' to disable PDF exports ([c7d38a9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c7d38a976e214f5255a3c5ac9624e6379842c62a))
- **gitlab-ci:** run 'pages' job on GitLab CI tags pipelines ([539dcd6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/539dcd62fcf8b7b443e2e9795446345df634ca6a))
- **gitlab-ci:** isolate 'pages: rules: changes' for reuse ([255bd8f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/255bd8f8a6fcec583b88d36cf860bc5c6dc6a59f))
- **gitlab-ci:** allow manual launch of 'pages' on protected branches ([0cb3464](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0cb34642d4fec8478c26ea02d3c3137d4e5ec28e))
- **gitlab-ci:** create 'pdf' job to export PDF on tags and branches ([c5e4eba](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c5e4ebadd4708b94e398ec1ba9a3ef657130b074))
- **gitlab-ci:** implement local pages serve in 'pages' job ([0864919](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0864919c1474c06f5e6cacd081d535dedf8b4fbd))
- **gitlab-ci:** raise minimal 'gcil' version to '11.0' ([03efbe2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/03efbe21d77b357888188df3fd7642d1de8993ad))
- **gitlab-ci:** enable local host network on 'pages' job ([6f0b6c6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6f0b6c68554175bd5e3c7c04f0584aea315c0310))
- **gitlab-ci:** detect failures from 'mkdocs serve' executions ([d4d434d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d4d434d59a659bb0bd8ace1c683d0deb6ba88202))
- **gitlab-ci:** refactor images containers into 'registry:*' jobs ([0b69a9b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0b69a9b5b7d7f843468e9c90df4b1531fc9aa5d2))
- **gitlab-ci:** bind 'registry:*' dependencies to 'requirements/*.txt' ([39e8846](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/39e884615051c61fbc776498efd0310632468714))
- **gitlab-ci:** avoid PDF slow generation locally outside 'pdf' job ([b556868](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b556868b861faebe25fd2d8c10085d75b4868cf7))
- **gitlab-ci:** validate host network interfaces support ([64ac80a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/64ac80abd40acea5dfea3fcd52ba2e60d0f19458))
- **gitlab-ci:** enable '.local: no_regex' feature ([dd8a20c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/dd8a20c6b830ff2fafe82004d6fd88e97397341f))
- **gitlab-ci:** append Git version to PDF output file name ([7b318b7](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7b318b7403895b87d6db01d07840b6c93e943eaf))
- **gitlab-ci:** rename PDF to 'pre-commit-crocodile' ([1937a42](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1937a42e927a346dae109c93d34a4a6f9c8aa002))

### 📦 Build

- **build:** add 'gcc' and 'libc-dev' for pre-commit-hooks v5.0.0 ([8c8e17f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8c8e17f0e2cb621e413f63a40ca4419cda6ceb06))
- **codestyle:** add 'gcc' and 'libc-dev' for pre-commit-hooks v5.0.0 ([9b52c0d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9b52c0daac7f4cf42af54aad34d38985a6349096))
- **commits:** add 'gcc' and 'libc-dev' for pre-commit-hooks v5.0.0 ([1b86f3c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1b86f3cbe7f405e7f1a1439bbf6208c011c173d9))
- **pages:** migrate to 'python:3.12-slim' Ubuntu base image ([5c3936d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5c3936d524c5397c9972262339081543ca5c4c29))
- **pages:** install 'playwright' dependencies for 'mkdocs-exporter' ([e44333d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e44333d03f403e151c2dc6172a54359c54b11ca9))
- **pages:** install 'entr' in the image ([d2eb9d1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d2eb9d1c36d4106c573dc85a116505450ff38cdd))
- **requirements:** install 'mkdocs-git-revision-date-localized-plugin' ([7628aa3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7628aa3574755ce24a0cc76557f292d83e269616))
- **requirements:** install 'mkdocs-awesome-pages-plugin' plugin ([abe762c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/abe762c7c3518919b71b76bacbaa7e6be4c4c11f))
- **requirements:** install 'mkdocs-minify-plugin' for ':pages' ([7de6f86](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7de6f86097e3dc4cbbc22e29cf1c5b1ee059e725))
- **requirements:** install 'mkdocs-exporter' in ':pages' ([0a6fe7b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0a6fe7b2d836a11f7ce727b66e79acb4f5952fca))
- **requirements:** migrate to 'mkdocs-exporter' with PR#35 ([4c74f9a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4c74f9af992435318a7a338cb66a622ff407509b))
- **requirements:** upgrade to 'playwright' 1.48.0 ([e41415f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e41415fa09ba0748ae619fc81f360cce40ad90a8))
- **requirements:** migrate to 'mkdocs-exporter' with PR#42/PR#41 ([e3c5c26](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e3c5c26ca83ae7e9220c44ed61cbb1e81957da16))


<a name="3.1.0"></a>
## [3.1.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/3.0.0...3.1.0) (2024-08-25)

### ✨ Features

- **cli:** implement '--stage STAGE' for '--run' to specify stage ([9ef3d2a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9ef3d2ac4c9017ca247595da41a7cd9e5f998bd7))
- **configurations:** implement matcher for 'sonar-project.properties' ([b9627a6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b9627a653a5336e3b1483894bd7a3c0c9b71c514))
- **gcil:** inject 'gcil' badge automatically if configured or installed ([6cfe076](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6cfe07681fe0ac7e8ac35d4c95da4bc36a8f045f))
- **gcil:** implement automatic 'run-gcil-push' hooks with whitelist ([56e9e6c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/56e9e6ca4c46e11eb86479127a98042e9a039693))
- **main:** add '-D' as short flag for '--default' long flag ([6515c29](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6515c295868477d4bb3f88111b67fbf1d157ae5d))
- **pre-commit:** add 'pygrep-hooks' hooks to 'pre-commit' template ([8813f81](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8813f8119c88c39a62834fcf1f5a0b8fe74211aa))

### 🐛 Bug Fixes

- **features:** enforce 'Commands' conditional arguments syntax ([142108f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/142108f37896f9523e43144f3433092b1b4b5952))

### 📚 Documentation

- **cliff:** improve 'Unreleased' and refactor to 'Development' ([abaf0c9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/abaf0c9c11ac9e1e5bbf37fa3d5fe99f9290e436))
- **mkdocs, prepare:** resolve Markdown support in hidden '<details>' ([d647166](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d647166f68fcccd2ab7ec1c3717622fa365a8bd8))
- **prepare:** regenerate development 'CHANGELOG' with 'git-cliff' ([0cc6cc7](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0cc6cc7995c56d91b1fb1eb7f9f63c35ce7c3609))
- **readme:** link against 'gcil' and 'pexpect-executor' documentation pages ([3044355](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/304435558aeab4e9792b4029c8a9d9b26ef54771))
- **readme:** add 'gcil:enabled' documentation badge ([f06542b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f06542bac9d87e6844171cca4d4c96f9182ff91f))

### ⚙️ Cleanups

- **sonar:** wait for SonarCloud Quality Gate status ([f48b69e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f48b69efeb94f034b3fbf84dfaeebb35dfc0e6ea))

### 🚀 CI

- **gitlab-ci:** prevent 'sonarcloud' job launch upon 'gcil' local use ([8ba9700](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8ba97001ad13c6feb40e02dfac391c1169740f0f))
- **gitlab-ci:** run SonarCloud analysis on merge request pipelines ([0f34e2d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0f34e2da8dfff5e7eb27a987dd02ffcc2c7aa3f6))
- **gitlab-ci:** watch for 'config/*' changes in 'serve' job ([c47e433](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c47e4339fc6f321debce26c57dd265fea51eb3f8))
- **gitlab-ci:** fetch Git tags history in 'pages' job execution ([c4c8b71](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c4c8b71f55198eae1e273cd00e81df94a87c15f9))
- **gitlab-ci:** fetch with '--unshallow' for full history in 'pages' ([cd6d65e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cd6d65e3f82b61afc7d56aadec907bf1489e688a))

### 📦 Build

- **containers:** use 'apk add --no-cache' for lighter images ([d13b26a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d13b26a2bc88327bebfad60e635604ac786c9f4a))
- **pages:** add 'git-cliff' to the ':pages' image ([26f26c6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/26f26c6f0b06e3835a5d553eb5342d2ba5ec94da))


<a name="3.0.0"></a>
## [3.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/2.1.0...3.0.0) (2024-08-25)

### ✨ Features

- **cli:** implement '--config FOLDER' and '--default' configurations ([081fd94](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/081fd94afd0d89ef2ac3ca23c68858c53df1216d))
- **cli:** implement '--clean' to run 'pre-commit clean' cache cleanups ([b971337](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b9713370b85e610aa724c2f45322c50dc461227d))
- **entrypoint:** configure unused hooks upon '--default' use ([a271c43](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a271c431988f116a57f5fa375eb1bf8cf4dbbc89))
- **entrypoint:** inject badge in 'README.md' upon '--configure' ([739774d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/739774d6b44f7cd5ce3b45738758215e74152f69))
- **entrypoint:** add 'README.md' to '--configure' commmands hint ([8d7ddcc](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8d7ddccf2b530ad02c92a0a29b0894f37e8154df))
- **entrypoint:** migrate to commitizen '3.29.0+adriandc.20240825' ([9c6f378](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9c6f37849e17f3ccd2baf302789045ed16424e86))
- **entrypoint:** allow newer commitizen versions usage ([138ef35](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/138ef3533a03ceb0b5a6a7a7568795efd717e975))
- **entrypoint, features:** refactor into static features classes ([9b85378](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9b85378eb831690fe83550dbea5b9575e1f04fa7))
- **🚨 BREAKING CHANGE 🚨 |** **main:** avoid running '--run' features upon '--enable' ([1c9134d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1c9134d152c69fbe34192461f62f1522e32bac21))
- **prepare_commit_message:** inject signoff if commitizen 'always_signoff' ([f402004](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f402004cde6c84a6bc8857fd6cd6ddcd0618d0a0))
- **updates:** migrate from deprecated 'pkg_resources' to 'packaging' ([1205341](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1205341bc1b7d7f96dfb8830b32c8853a96a31de))

### 🐛 Bug Fixes

- **entrypoint:** resolve unused hooks issues with '--default' ([9dc8309](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9dc8309dc8c2ff819d7ffe8fc0f7b46f1e52e438))
- **entrypoint:** remove 'README.md' debugging log in '--configure' ([71ceb42](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/71ceb42808eaabf64998a79624a3be0a7995e29c))
- **precommit:** resolve '--default' use with existing configuration ([7543149](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7543149382f5280b074a24b1dbd403821810e36e))
- **templates:** migrate to 'run-gcil-*' skipped hooks names ([63df3c3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/63df3c36819540f119f82c1a37e7848078580e13))

### 📚 Documentation

- **readme:** add badge compatibility and syntax documentation ([9de0ad9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9de0ad97fdadf6cccd958b425ab5aafda1c02b38))
- **readme:** add 'mkdocs' and 'mkdocs-material' references ([f9eac20](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f9eac20e5db2c7b383462930c9b1ca194da07af7))
- **requirements:** install 'types-PyYAML>=6.0.12.2' as quality dependency ([4d09100](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4d0910084d1392467dbca5298c01bcab7befaec8))

### ⚙️ Cleanups

- **commitizen:** migrate to new 'filter' syntax (commitizen#1207) ([4342bea](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4342bea56efb8e9c45bcaa7372770cc0c240ae44))
- **entrypoint:** constantify '{PACKAGE_REVISION}' template string ([8a77371](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8a77371e9f476293941e27748817b4a858cb6e9a))
- **pre-commit:** add 'python-check-blanket-type-ignore' and 'python-no-eval' ([31738fe](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/31738fe68508926ed433190d870d7aea4c9464a5))
- **pre-commit:** simplify and unify 'local-gcil' hooks syntax ([001b11d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/001b11d840056d2a0a30faabac2e246f450163dd))
- **pre-commit:** add 'additional_dependencies' for missing YAML ([9c80622](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9c806225083194d7d4e21de7b49fcefe38b53bfd))
- **pre-commit:** improve syntax for 'args' arguments ([0d7e947](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0d7e9476f5bf41c56ca699c4339a74900fa073c8))
- **pre-commit:** migrate to 'run-gcil-*' template 'gcil' hooks ([8e0f5cf](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8e0f5cfcee7db56b2dff830401e97ce8b6a70f86))
- **pre-commit:** update against 'run-gcil-push' hook template ([cb69d0b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cb69d0bbe2b1ca9f0338e005ec1447577355f856))
- **pre-commit:** add missing 'commit-msg' stage for commitizen ([a27b9dd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a27b9dd23b33a0fbd99164a386d01485cc5b51c0))

### 📦 Build

- **requirements:** add 'PyYAML>=6.0' as runtime dependency ([2fe8d58](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2fe8d58e586daa760d8d062368cdfe33028cddc4))


<a name="2.1.0"></a>
## [2.1.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/2.0.2...2.1.0) (2024-08-24)

### ✨ Features

- **entrypoint:** use 'pre-commit install --allow-missing-config' ([d41b2f3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d41b2f39d024ba14dde024ae021649b991631a0d))
- **entrypoint:** use 'pre-commit run --all-files' parameter syntax ([956cb33](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/956cb333028e61d2e1e14b5971d233f4882d069a))
- **pre-commit:** exclude '.patch' Git patch files from hooks ([e865955](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e865955cc09781725dc0aa88314506b951ce3350))
- **pre-commit:** disable 'detect-private-key' by default ([5ef6060](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5ef6060fba92d46fde84530ccb08a271d50d2c94))
- **pre-commit-config:** exclude 'eicar.*' Anti Malware Testfile ([6dbdb7c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6dbdb7c5c7727788ffd9974e8dc0dee8c9c0c467))

### 🐛 Bug Fixes

- **pre-commit:** fix 'destroyed-symlinks' v4.6.0 missing stages ([5377b8f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5377b8fc5349301a8c10cb24edf3e6d511626ddb))
- **templates/commits:** avoid failing without 'local-gcil-*' hooks ([1d9dc15](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1d9dc15b5fa3310251b35ab5f7f24398b2cfff93))

### 📚 Documentation

- **components:** add GitLab CI/CD Catalog for components URL ([47068c6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/47068c6bce3758119db692ff74d0de9370ae199c))
- **hooks:** fix hooks 'repo:' URL for '.pre-commit-config.yaml' ([b7c059e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b7c059ef2a72d307c629231606e836ade5564ec5))
- **hooks:** improve hook '.pre-commit-config.yaml' documentation ([7a3c283](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7a3c283ffb7c60bcdb9f9909c8b9194755982cfe))
- **prepare:** fix 'Commit type' list faulty indentation issue ([42f49cb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/42f49cb494c206752723df29996012ca4935e742))

### ⚙️ Cleanups

- **pre-commit:** fail 'gcil' jobs if 'PRE_COMMIT' is defined ([1fcb35c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1fcb35c0224b31a0641f138c784ca59a53da75b5))

### 🚀 CI

- **gitlab-ci:** improve 'serve' job syntax for YAML rendering ([aa41a7e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/aa41a7e3544e40ede01733a83a9b9b936a8747e0))
- **gitlab-ci:** cleanup cache upon 'serve' job end ([4574326](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/45743265d47b41929cebda731b444857feba9e14))
- **gitlab-ci:** ignore 'serve' job failure due to 'Ctrl+C' end ([c8718b5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c8718b5257069ab7e5410bea086aecece90a39a3))
- **gitlab-ci:** avoid failures of 'codestyle' upon local launches ([6660428](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/666042865a99dd49fd092abc13e06f3de039b887))


<a name="2.0.2"></a>
## [2.0.2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/2.0.1...2.0.2) (2024-08-22)

### 📚 Documentation

- **components, hooks:** add file name headers for sources changes ([77cfb9b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/77cfb9b4dc249e70811afc1161d4fefd170877e4))
- **prepare:** bind 'preview.svg' image as a webpage asset ([2e214bd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2e214bdb63459c4265b035a6d86fe2e0ef69c1ef))
- **preview:** add 'clear' calls before 'git add' sections ([8dd763c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8dd763c308e2319ea48c771fcb0abebdaa58f591))
- **preview:** fix SVG preview for version 2.0.1 ([1d34359](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1d34359768b881efd1a6ee3a0ec9a17f9fac17be))
- **readme:** remove '{ ... }' wrappers for single commands ([dd892d8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/dd892d8233f304b4b24cf3475f6c24f2a1e1ce5d))
- **readme:** simplify and cleanup commands documentation ([d2d3b38](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d2d3b38a87780524bcd56a41ca52b8276f633553))

### 🚀 CI

- **gitlab-ci:** create 'hooks' local job for maintenance ([df35dc9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/df35dc992f811dbd35981d59643c7d20b51d20c0))
- **gitlab-ci:** prepare and remove '.cache' even upon failures ([f56f38e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f56f38e29e33877871ce1cc538e569374e1fa349))
- **gitlab-ci:** use 'origin/develop' as hooks revision for 'preview' ([9c0c29c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9c0c29c353297c8ec21329ea3dfec3b1187c708a))


<a name="2.0.1"></a>
## [2.0.1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/2.0.0...2.0.1) (2024-08-21)

### ✨ Features

- **commitizen:** refactor commits documentation and improve markdown ([10d1da9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/10d1da9cf8e6a957a63ab820b4aa36235130db37))

### 📚 Documentation

- **docs:** add 'commitizen' to the project main description ([effba2f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/effba2fa32ad96e3373332fc143240eab36308c6))
- **docs:** embed files directly using 'mkdocs' syntax '--8<-- "..."' ([a51755e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a51755e1db63ea04d23d2f77af53f053687707fa))
- **docs:** improve headers with links for configurations files ([565c92f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/565c92f6151201c3bde104619f8c9f36442092ad))
- **preview:** refresh SVG preview for version 2.0.1 ([50621dc](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/50621dc1eb74c6382d9865f02e4819f83b6a3b26))
- **readme:** add 'Package' link in the 'README' documentation ([6238b85](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6238b85d63fac17cd658c89c7af92def065f6a43))

### 🚀 CI

- **gitlab-ci:** watch for '.cz.yaml' in 'serve' job ([e1f8319](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e1f8319c6cb4b5530f9bd24bc08f4bf4e54216d6))


<a name="2.0.0"></a>
## [2.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/1.1.0...2.0.0) (2024-08-21)

### ✨ Features

- **cli:** refactor 'manage' tool into 'pre-commit-crocodile' entrypoint ([fcd6a33](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fcd6a33aa3dc87c070415e259e6da544a663eaad))
- **cli:** run requested mode only and not related modes too ([4aef5dd](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4aef5dd4381ebaa0b5e5ecb06c040c7c1e8fec08))
- **cli:** implement '--list' mode to list installed hooks ([72bc197](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/72bc1978900f9aa8920927e3065b7109339abf92))
- **configurations:** add 'mkdocs' detection and isolate 'docs/' ([3d8f988](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3d8f98867c86efa6d71da44cd8c10950e48fb599))
- **configurations:** refactor 'docs/' and 'test[s]?/' into evaluators ([f0e880c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f0e880cf87f9961710940ce44469b0a32e0d8062))
- **configurations:** catch 'recipes-*/(...)' Yocto recipe as fallback ([ee8d4c2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ee8d4c20264ffb3c0d5021a70797bff31b23d781))
- **configurations:** evaluate 'containers/' changes for commits ([1078898](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/10788981f8c41940bb5820022780dec969f14ba5))
- **configurations:** add evaluator for 'templates/' as 'ci' commit ([e818b59](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e818b59e4c1c6353eb411dfcc584e75aade95195))
- **entrypoint:** configure '.pre-commit-config.yaml' with revision ([db6f0f8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/db6f0f84c10333dc7a4197944d330efd81c6cf29))
- **entrypoint:** list detected Git remote upon 'git remote set-head' ([4b91a48](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4b91a4898009d8a50323a617fa7cd55e0e7d220e))
- **entrypoint:** add commit instructions for '--configure' mode ([750d69b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/750d69b7e82b87f47005cf0af0894d382de72806))
- **entrypoint:** automatically resolve 'check-hooks-apply' errors ([69852d1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/69852d159be15f8be3944fd8eae18ddd3b227238))
- **hooks:** comment 'Issue: #...' template by default ([bdf466f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bdf466f0412fa7b88f42d8ef5e80a8434e139c13))
- **main:** set '--configure' as 'Edit sources with hooks configurations' ([ff16952](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ff16952901c9d6f59571fac99df34de09a7d2944))
- **main:** avoid '--autoupdate' features upon '--enable' mode ([c715b6a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c715b6a0bc2565580a9cf2094b54bef538a7962b))
- **main:** enable '--enable' features upon '--autoupdate' mode ([2e5464b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2e5464b92d04ee70dc233b6f862408e82504339b))
- **mkdocs, gitlab-ci:** implement GitLab Pages with 'mkdocs' ([76b963a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/76b963a65c898b490b3c639d61a84a860fd45456))
- **package:** add 'DEBUG_REVISION_SHA' to force package revision ([372c7c0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/372c7c09313bf418b47ec078cc56f4804a710c46))
- **🚨 BREAKING CHANGE 🚨 |** **setup:** drop support for Python 3.8 due to 'importlib.resources' ([0e2772f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0e2772f0827568693c796f990c8881e900c22a52))
- **src:** import package, prints, system and types from 'gcil' ([f30ec12](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f30ec121b3584b0e311a511a2b12cd3927405e35))
- **version:** create 'Version.revision' API to get tag or SHA1 revision ([6d28e45](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6d28e45d2367a789f1ffbf45d01ba157d07f5f86))

### 🐛 Bug Fixes

- **cli, assets:** implement '--configure' to deploy configurations ([e64a0a8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e64a0a83ace8c121580bd47806bf3f0c71ffa78e))
- **configurations:** detect 'requirements/' changes for commit messages ([06d0243](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/06d0243d5c043a36c566916d60575d778b445696))
- **configurations:** make folder and file name regexes non-greedy ([356001f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/356001f53d2221bde08d0136e6fbdcd49ee715c6))
- **entrypoint:** uninstall Python packages only if installed first ([ed6291f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ed6291f52fa6d33625c1cf4efa713072a55235da))
- **entrypoint:** use 'HEAD~1' instead of 'HEAD^' for Windows compatibility ([fe44ab8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/fe44ab8f12ef324269e9c4a7dec37ffd39fc2576))
- **entrypoint:** update Git remote upon '--enable' instead of '--autoupdate' ([e3f9ead](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e3f9eadf2d8c0d4d625c22e405b80482fbc4cc97))
- **entrypoint:** pre-stage '.pre-commit-config.yaml' for hooks checks ([a3bcfc9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/a3bcfc903e1780a1e72719f1150c0a33208359fc))
- **entrypoint:** resolve Python 3.8 support of f-string with quotes ([6f127a7](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6f127a7a3fd2f91ccdf4018b9e378a5a43a0e0d9))
- **entrypoint:** fix Python <3.11 without 'importlib.resources.abc' ([0708445](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/07084454c7665275355b0321c54bd52457f5e54a))
- **hooks:** use '\n' as commit message lines separator ([8abf039](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8abf03901691a502456528632bb421d6082694c7))
- **main:** align help position limit to 23 chars ([db766b8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/db766b89f99d56657136c71622bc2722bf9716f1))
- **main:** merge and refactor modes validation (python:S108) ([5f76347](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5f76347623a546d20eeae97268183b3a431c8d4b))
- **platform:** always flush on Windows hosts without stdout TTY ([3848f85](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3848f85860243ebdf97620a9444f58b433796b00))
- **pre-commit-config:** enable all 'pre-commit-hooks' hooks by default ([c487bf8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c487bf80ed1f4f8f082ba978fbafbce9a6dab31c))

### 🚜 Code Refactoring

- **hooks:** isolate all hooks sources under 'src/hooks/' ([49beecf](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/49beecf79eca3b38db805bb8c11be8d313d9ac0f))

### 📚 Documentation

- **components:** document GitLab CI/CD component for 'commits' ([db8565d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/db8565d78947423659b8193363d7929641affa82))
- **docs:** refactor and create new specification pages ([15b43ff](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/15b43ff9a4afe2e22d73afb112023f9379ea1501))
- **docs:** remove 'Documentation:' link from 'README.md' sources ([b269976](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b26997691f4962d27b58f4c92da5092086f0e51a))
- **mkdocs:** migrate to 'mkdocs-material' theme and features ([d7079d6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d7079d67f326e71e7e2c8ed8994bc29c8e6eaf35))
- **mkdocs:** add 'commitizen' and 'pre-commit' reference pages ([864af2a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/864af2a9c141c1aca96df58e5a299183cc0e7f82))
- **prepare:** fixup `[optional !]:` quotings for 'commits` ([612f2a1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/612f2a102ba11dd7250f2f1b0a0aa6828537116e))
- **preview:** implement 'preview' SVG documentation ([86831d5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/86831d51e1235f604b5e575eae2e42f22ba7ca8f))
- **preview:** implement commits creation documentation ([3b2709e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3b2709eace6f7be2595796a18cbb84bd4ed3c2a3))
- **preview:** refresh SVG preview for 'check-hooks-apply' fixes ([9710474](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/97104741931832f3f6593df65054e4d7f2977f80))
- **readme:** improve 'prepare-commit-message' documentation ([f7cdcd4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f7cdcd4e7b11854c114eef937ffcc16810e661c1))
- **readme:** document 'pre-commit' and 'commitizen' installations ([9ec1970](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9ec1970e858986cdfa41bcde86e2fe1487789882))
- **readme:** document '--settings' and 'NO_COLOR' configurations ([30931f6](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/30931f69ae2a17126cacc03dafd4e875207294ae))
- **readme:** add new dependencies and references links ([9949b22](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9949b22350a7b0557e91f64eb48bf3bfad068af3))
- **readme:** improve 'Features' and 'Commands' documentations ([2b52013](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2b52013238df998c6fbbdbdaf797c96066ca8fbd))
- **readme:** fix 'pre-commit-crocodile --autoupdate' documentation ([b392403](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b39240331e6d67b0218b6662f0c7863372abf5e0))
- **readme:** refactor and use 'pre-commit' badges for 'Commands' ([03b3b7c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/03b3b7c8e8725682f19fb59344482a3d3aa357b9))
- **readme:** add 'pre-commit-crocodile' documentation badges ([812d22b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/812d22b496c3f404a7c918ea016978abc11c0ee4))
- **readme:** add SonarCloud analysis project badges ([0a55099](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0a55099210f4c4bd797c9e53d758183c10c3823f))
- **readme:** link 'gcil' back to 'gitlabci-local' PyPI package ([5f90c33](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5f90c33f77e350ace19b0f9d47c470e3618200ef))
- **readme:** isolate '--autoupdate' from '--enable' instructions ([2f87610](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2f876104b4b8c10fd102ce7ef0131442c20f7271))
- **readme:** clarify commands for projects with/without configurations ([5be9579](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5be95798c90ca790d21ae7dd5f1f22a506706ec8))
- **readme, docs:** add 'pre-commit enabled' badges ([df4de33](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/df4de33c8c1f1255d355c2ef799ed6930523e735))
- **settings:** remove 'engines' configuration derived from 'gcil' ([136173f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/136173f3edec9350b0a8bd3b4de75e9cea91c9a7))

### 🧪 Test

- **requirements:** raise 'pexpect-executor' version to 4.0.0 ([240a9e2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/240a9e253d2dddf74c96c19b9e93c9456c38667b))
- **requirements:** raise 'pexpect-executor' version to 4.0.1 ([66fad86](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/66fad8614f106f7298a52be4c4d10896f83d64d4))

### ⚙️ Cleanups

- **cliff:** fix 'pre-commit-crocodile' GitLab URL in CHANGELOG ([b92eaca](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b92eacae357f606cc5714c26038b61ab268a1e7e))
- **entrypoint:** refactor assets resources access ([aaa104f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/aaa104f796093425ba914fa7ce3ed38af3812da8))
- **entrypoint:** reorder 'options.disable' code section ([cdd8dad](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cdd8dad082a59a377e4198a28d51f109580ff905))
- **entrypoint:** minor 'Commands' codestyle improvements ([4751c20](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4751c20621b8dbba8faf74dc29a76c0f6d2cd321))
- **gitattributes:** always checkout Shell scripts with '\n' EOL ([6ff1836](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/6ff1836a02f37fa9ef2e556268851b0f3b1296d2))
- **gitignore:** ignore '.*.swp' intermediates 'nano' files ([b63d959](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b63d959c7e714d6ccdf6252cf9ac8c107b897f00))
- **gitignore:** ignore '.tmp.*' intermediate files ([c11c992](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/c11c9928104d0bc47d120f9e8ac42a9599b50684))
- **gitignore:** minor comment improvement for 'Documentation' ([cb96c3c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cb96c3ccdd0d3dceb2ae7ea449bcf10444df6cd4))
- **pre-commit:** rename repository to 'pre-commit-crocodile' ([8e92229](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8e922290f490a31eeced7332df317f90cf1a1e0b))
- **pre-commit:** run 'codestyle', 'lint' and 'typings' jobs ([6556920](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/655692022b12f7175d01d65cfb6b1433e01cdd23))
- **pre-commit:** fix '.py' local Python hook execution ([27d8d2e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/27d8d2ef49a85bb75ad22095d866b4c18c0e5643))
- **setup:** add requirements from 'runtime.txt' as dependencies ([73ed96f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/73ed96f92f752e7c5591ca82646106e39f126765))
- **setup:** add 'Statistics' URL to the package description ([33a92e5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/33a92e514df909e248fdda99bb49a23c076694cd))
- **vscode:** ignore '.tmp.entrypoint.*' files in VSCode ([39e9170](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/39e917045fa8661ddfb9bdd0e3c81a34340db9f9))

### 🚀 CI

- **commits:** use 'pre-commit-crocodile:commits' image ([f3fefc2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f3fefc28f135391eb9474dd3235a054f7d0f1fdb))
- **commits:** implement 'commits' job as a GitLab component ([510f44c](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/510f44c79c9ad34acc93055e29d83c85bdf2c23b))
- **gitlab-ci:** show fetched merge request branches in 'commits' ([b109199](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b10919985d627023719b9e21fb92ee898348b90b))
- **gitlab-ci:** need preparation jobs for 'pages' deployment job ([4f68937](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4f689373dd794148fbfa03a7db9f302b6eb3d1f4))
- **gitlab-ci:** always run 'commits' job on merge request pipelines ([3c54504](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3c54504413f2bc1e30d254033611988bdccb39be))
- **gitlab-ci:** fix 'image' of 'commits' job ([9a7614b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9a7614bc4dcbbee9edfa7b58022fd1156803374c))
- **gitlab-ci:** fix 'before_script' of 'commits' job and add comments ([cc7492a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cc7492a30166a64f59596841dd41b18dff7afb20))
- **gitlab-ci:** validate 'pre-commit' checks in 'commits' job ([ac2291d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ac2291d83d46307a8c92267feb211084a31158fe))
- **gitlab-ci:** rehost 'python:3.12' with 'images' job for 'pages' ([bca847a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bca847ae7c8fa631ad197ec638f5fbba7a3d337a))
- **gitlab-ci:** prepare 'build' and 'deploy' container images ([355c3fb](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/355c3fbe1c73638de6d7f59251fdf92a1ab7465e))
- **gitlab-ci:** implement 'build' job to build and package '.whl' ([dc2558d](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/dc2558d15a757fc5f942c3af5f626c2fb25fa495))
- **gitlab-ci:** import 'install' job from 'gcil' ([5c3327b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5c3327bf12b8756ad4390d89909cadc29b2016d0))
- **gitlab-ci:** import 'readme' job from 'gcil' ([2b0ec11](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2b0ec110a9a144ad0b7730f270c478c38e87ba97))
- **gitlab-ci:** isolate documentation preparation into 'docs/prepare.sh' ([5ad76f5](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5ad76f5ad6d86ece331457a640ee804550a00013))
- **gitlab-ci:** create 'serve' local jobs for 'mkdocs' tests ([017e0cf](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/017e0cfae85376472d99f1e02ece9090898f1235))
- **gitlab-ci:** use 'HEAD~1' instead of 'HEAD^' for Windows compatibility ([e2978b8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e2978b80d9ab67c72ca32de5258705acb7b2738f))
- **gitlab-ci:** patch '.pre-commit-config.yaml' asset version upon tag ([482c221](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/482c2214cb19394958a3fdf355a3699065f84c7a))
- **gitlab-ci:** use 'pre-commit-crocodile:build' image ([bb1e245](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/bb1e2450623e4570cc5189b33cfba1830a441961))
- **gitlab-ci:** check only Python files in 'typings' job ([b511437](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/b5114374c1ae1da2b2726e823dab367bdccbd5a4))
- **gitlab-ci:** use 'DEBUG_REVISION_SHA' for unreleased 'preview' use ([ab92cde](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ab92cde321d7af4ba34798e1426f089d0cfbabb8))
- **gitlab-ci:** implement SonarCloud quality analysis ([2b16fe9](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2b16fe923d946474f6692aa4dcf36758ea208e7c))
- **gitlab-ci:** implement 'deploy:*' release jobs from 'gcil' ([3d9ddff](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3d9ddff70f749878e57a5ad0fcb3e281df528257))
- **gitlab-ci:** deploy 'pages' on 'main' branch only ([1c61717](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1c61717b13fdf1df609f6416c1e25b84aa5c191e))
- **gitlab-ci:** run 'pages' jobs after successful tests and coverage ([ab223cc](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ab223cc5a2d67a2ad40fd91271ee6b5e0a953ccb))
- **gitlab-ci:** detect and refuse '^wip|^WIP' commits ([85291d1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/85291d1c9ed91a9251a1efab4d5abe9212a64472))
- **gitlab-ci:** isolate 'commits' job to 'templates/commit.yml' ([7305d70](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7305d70396b7cacbbadcf66060c6e4fddb3a7fda))
- **gitlab-ci:** watch 'docs/' changes for 'prepare.sh' in 'serve' job ([cbb3b33](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cbb3b33ce25bc49662ad53ba51d03737db08243c))
- **gitlab-ci, containers:** create 'pre-commit-crocodile:pages' image ([44470bc](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/44470bcffc5b72c7507a0cfd3146ace8568b0ce1))
- **gitlab-ci, containers:** create 'pre-commit-crocodile:codestyle' image ([987ec50](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/987ec50824379d4ec7c365227721f6276cc1a595))
- **gitlab-ci, containers:** create 'pre-commit-crocodile:preview' image ([215e1d3](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/215e1d332a2eabe67960abae1327347a966cb965))
- **gitlab-ci, tests:** implement coverage initial jobs and tests ([5169994](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/516999439e1aa0635034f2ef4755ac2df63eab65))

### 📦 Build

- **codestyle:** install 'pexpect-executor' in the ':codestyle' image ([7faf133](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/7faf13385f0cd972afd55b1c65ec645b72c8e8b7))
- **commits:** create 'pre-commit-crocodile:commits' simple image ([48fcf9e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/48fcf9e22787075370c224a6f53656b4b3e58e47))
- **preview:** install 'git' in the ':preview' image ([e03e6d0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/e03e6d0fe0d34e3440844a6fa139036fc2c739bf))
- **preview:** install 'nano' in the ':preview' image ([ae44cc0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ae44cc0f5a4e67cbeda1c39c53b329b39d0a736f))
- **requirements:** install 'pexpect-executor' in ':preview' image ([5587450](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5587450dc848462b8de593e57a644ce960e71fde))
- **requirements:** install 'pipx' in the ':preview' image ([250a536](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/250a53665bcdb4861d91050143f300a8089cf494))


<a name="1.1.0"></a>
## [1.1.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/1.0.1...1.1.0) (2024-08-17)

### ✨ Features

- **pre-commit-crocodile:** migrate to 'pre-commit-crocodile' name ([cd8bad7](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cd8bad75a4fdd63cd96a042f5965bb59c3df602d))

### 🚜 Code Refactoring

- **src:** isolate all sources under 'src/' ([894a161](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/894a161d32771ae6c64d1d4fae032a84a107d25f))

### 📚 Documentation

- **readme:** update project descriptions for developers ([cf33578](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cf335785989aa5ec7121a6c8767f7ecc8b3a7e31))
- **readme:** add 'Conventional Commits' URL as reference link ([d984931](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d984931f3f343a987958ceb3ec71cdc49dc86319))
- **readme:** document features and usage of 'prepare-commit-message' ([985524e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/985524e9c7e4cbbd5dde0b0a0692a9599187b2f4))

### 🚀 CI

- **gitlab-ci:** remove unused 'requirements' folder changes checks ([f1b5f64](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/f1b5f644b94993624601bf999d96ecf8cad4764b))


<a name="1.0.1"></a>
## [1.0.1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/compare/1.0.0...1.0.1) (2024-08-17)

### 📚 Documentation

- **cliff:** import 'git-cliff' configurations from 'gcil' ([584fea2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/584fea2b90eaa64fbfccd4cd1ccdc7ce4d1ec768))


<a name="1.0.0"></a>
## [1.0.0](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commits/1.0.0) (2024-08-17)

### ✨ Features

- **pre-commit:** bind 'prepare-commit-message' CLI entrypoint ([38257d2](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/38257d2dcc5493ead37750fada5b46fa69fc90c4))
- **pre-commit-hooks:** migrate to '.pre-commit-hooks.yaml' hook ([75ca0c1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/75ca0c1797ad17cbbfbfe5a04059392f2dd92153))
- **prepare-commit-msg-template:** evaluate 'pre_commit_hooks' path ([cce56ea](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cce56ea35e6e6aea020e479ce05cbfec70494cb2))
- **setup:** implement initial 'setup.py' packaging from 'gcil' ([337322a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/337322aed20bac65b6a4f2e7667595e38af23b37))

### 📚 Documentation

- **license:** apply Apache License 2.0 license to the project ([5796350](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/5796350db55b66d221de9d7ab771324984caf57f))
- **readme:** initial 'README.md' documentation with dependencies ([9108c38](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9108c3872174c4e418c1fa18fd5b28adb0f42485))
- **readme:** document RadianDevCore 'pre-commit-hooks' repository ([2b75e41](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2b75e410b5d44ce475289cb86e5f5d461e66492c))
- **readme:** document 'prepare-commit-message' as available hook ([27ae472](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/27ae472654f86bcd4a71358af1f35d2aec15635b))

### 🎨 Styling

- **commitizen, pre-commit:** implement 'commitizen' configurations ([ad3713b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ad3713b695a8099596b31e2c2417c7af8d9e59a6))
- **markdownlint:** import Markdown codestyle rules from 'gcil' ([2d2c43e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/2d2c43e7629bf1aa75a5c3d30a378d8d11d9d3f3))
- **mypy:** import Python Mypy linting rules from 'gcil' ([1fc611a](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/1fc611a28d43e64b8f5c9cd2e7187af3d7c59188))
- **pre-commit:** implement initial 'pre-commit' configurations ([cd9d252](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/cd9d252b26d6ac901d909e1bc94d70b4518e1d2c))
- **pre-commit:** enable 'check-hooks-apply' and 'check-useless-excludes' ([0a61f1b](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/0a61f1bcff0232c86e6338a21fa27945084cbde2))
- **yapf:** import Python YAPF codestyle rules from 'gcil' ([51983c4](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/51983c4a302cf1967885766b1a2dfeb12888747b))

### ⚙️ Cleanups

- **gitignore:** ignore Python compiled intermediates ([853f1ca](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/853f1ca7a90b38364835f9167daa6f303081782c))
- **gitignore:** ignore '.tmp' folder intermediates ([3737d2f](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/3737d2fcde139812b684036572dfd0e65f71c422))
- **hooks:** implement evaluators and matchers priority parser ([4975ec1](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/4975ec1cbb4633f1028b1f65a50aae7707ecaf38))
- **pre-commit:** fix 'commitizen-branch' for same commits ranges ([81ae190](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/81ae1900205e3589211352f98e1e210e681d162d))
- **pre-commit:** disable 'check-xml' and 'check-toml' unused hooks ([ecc2a18](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/ecc2a18da3ab60eab84215c9478078485ab52c90))
- **vscode:** import Visual Studio configurations from 'gcil' ([8ea708e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/8ea708ef1c6a19837c714be26d0d2912c056ea49))

### 🚀 CI

- **gitlab-ci:** import 'changelog' and quality jobs from 'gcil' ([9ce445e](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/9ce445e4d9fe096b5eb6d29b54715907ba4ede6c))

### 📦 Build

- **hooks:** implement 'prepare-commit-msg' template generator ([60221d8](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/60221d87cdd22a050b2892aa31ca729e84eb3b35))
- **hooks:** create './.hooks/manage' hooks manager for developers ([d731261](https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commit/d731261c93750eae2fc193f84d74869e888b97b8))


