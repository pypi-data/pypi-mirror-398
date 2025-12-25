# django-pzip-storage

A FileSystemStorage subclass for Django that encrypts/compresses with [PZip](https://github.com/imsweb/pzip).

## Installation

`pip install django-pzip-storage`

## Usage

The simplest way to use `PZipStorage` is by setting your
[DEFAULT_FILE_STORAGE](https://docs.djangoproject.com/en/dev/ref/settings/#default-file-storage) to
`pzip_storage.PZipStorage`. By default, `PZipStorage` will use your `SECRET_KEY` setting as the encryption key.

**IMPORTANT**: Encrypting with `SECRET_KEY` means you **must** keep `SECRET_KEY` a secret, and if you lose or reset it
without first rotating the keys of all stored files, they will be lost forever.

`PZipStorage` may be used with existing unencrypted files, as a drop-in replacement for `FileSystemStorage`. If it
determined the requested file is not a PZip file, it will delegate to `FileSystemStorage` after emitting a
`needs_encryption` signal (see below).

You may also use `PZipStorage` as a custom storage backend anywhere Django allows it; see
[Managing Files](https://docs.djangoproject.com/en/dev/topics/files/) in the Django documentation for more information.

## Settings

* `PZIP_STORAGE_EXTENSION` - the extension to append to any file saved with `PZipStorage`. Defaults to `.pz`.
* `PZIP_STORAGE_NOCOMPRESS` - a set of file extensions (with leading period) which should not be compressed when
  saving. See `PZipStorage.DEFAULT_NOCOMPRESS` for the default list.
* `PZIP_STORAGE_KEYS` - an iterable (or callable returning an iterable) of keys to use. The first key on the list will
  be used for encrypting files. Defaults to `PZipStorage.default_keys`, which yields `SECRET_KEY`.

These settings may be overridden on a per-storage basis by instantiating `PZipStorage` manually with `extension` or
`nocompress` keyword arguments.

## Signals

`PZipStorage` emits a number of signals when opening files in various circumstances:

* `pzip_storage.needs_rotation` - sent when a file was decrypted using an old key, i.e. not the first key in the
  provided list.
* `pzip_storage.needs_encryption` - sent when an unencrypted file was opened.
* `pzip_storage.bad_keys` - sent when an encrypted file was opened, but no keys in the list could decrypt it.

You may listen for these signals to do things like gradual encryption, key rotation, or logging.
