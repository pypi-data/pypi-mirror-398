# tarhash
Hashes the entries in a tarfile without extracting them.

The user interface could use some polish, but the actual functionality works excellently.

Supports all the hash functions and compression formats that Python does. By default, includes features to support zstd (on old python versions), [blake3], [xxhash].

[blake3]: https://github.com/BLAKE3-team/BLAKE3
[xxhash]: https://xxhash.com

## License
Licensed under either the [Apache 2.0 License](./LICENSE-APACHE.txt) or [MIT License](./LICENSE-MIT.txt) at your option.

Unless you explicitly state otherwise, any contribution intentionally submitted for inclusion in this project by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any additional terms or conditions.
