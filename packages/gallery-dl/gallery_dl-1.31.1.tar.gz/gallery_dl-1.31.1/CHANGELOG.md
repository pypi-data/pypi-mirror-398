## 1.31.1 - 2025-12-20
### Extractors
#### Additions
- [2chen] implement generic `2chen` board extractors
  - support `https://schan.help/` ([#8680](https://github.com/mikf/gallery-dl/issues/8680))
- [aryion] add `watch` extractor ([#8705](https://github.com/mikf/gallery-dl/issues/8705))
- [comedywildlifephoto] add `gallery` extractor ([#8690](https://github.com/mikf/gallery-dl/issues/8690))
- [koofr] add `shared` extractor ([#8700](https://github.com/mikf/gallery-dl/issues/8700))
- [picazor] add `user` extractor ([#7083](https://github.com/mikf/gallery-dl/issues/7083) [#7504](https://github.com/mikf/gallery-dl/issues/7504) [#7795](https://github.com/mikf/gallery-dl/issues/7795) [#8717](https://github.com/mikf/gallery-dl/issues/8717))
- [weebdex] add support ([#8722](https://github.com/mikf/gallery-dl/issues/8722))
- [xenforo] support `allthefallen.moe/forum` ([#3249](https://github.com/mikf/gallery-dl/issues/3249) [#8268](https://github.com/mikf/gallery-dl/issues/8268))
#### Fixes
- [aryion:favorite] fix extraction ([#8705](https://github.com/mikf/gallery-dl/issues/8705) [#8723](https://github.com/mikf/gallery-dl/issues/8723) [#8728](https://github.com/mikf/gallery-dl/issues/8728))
- [aryion] fix `description` metadata
- [boosty] include `Authorization` header with file downloads ([#8704](https://github.com/mikf/gallery-dl/issues/8704))
- [fanbox] make `_extract_post()` non-fatal ([#8711](https://github.com/mikf/gallery-dl/issues/8711))
- [furaffinity] fix `tags` metadata ([#8724](https://github.com/mikf/gallery-dl/issues/8724))
- [mastodon] fix `AttributeError: 'parse_datetime_iso'` ([#8709](https://github.com/mikf/gallery-dl/issues/8709))
- [tenor] fix `title` metadata
- [twitter] fix `avatar` & `background` downloads with `"expand": true` ([#8698](https://github.com/mikf/gallery-dl/issues/8698))
#### Improvements
- [boosty] warn about expired `auth` cookie tokens ([#8704](https://github.com/mikf/gallery-dl/issues/8704))
- [misskey] implement `order-posts` option ([#8516](https://github.com/mikf/gallery-dl/issues/8516))
- [reddit] use `"videos": "dash"` by default ([#8657](https://github.com/mikf/gallery-dl/issues/8657))
- [pixiv] warn about invalid `PHPSESSID` cookie ([#8689](https://github.com/mikf/gallery-dl/issues/8689))
### Downloaders
- [ytdl] fix `UnboundLocalError: 'tries'` ([#8707](https://github.com/mikf/gallery-dl/issues/8707))
- [ytdl] respect `--no-skip`
### Miscellaneous
- [path] implement dynamic length directories ([#1350](https://github.com/mikf/gallery-dl/issues/1350))
- [formatter] add `I` format specifier - identity
- [tests] add `path` tests
