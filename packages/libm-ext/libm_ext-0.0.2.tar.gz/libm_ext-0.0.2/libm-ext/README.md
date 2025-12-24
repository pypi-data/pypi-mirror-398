<div align=center>
<h1>
libm-ext
</h1>
<p align="center">
An extension to <a href="https://crates.io/crates/libm">libm</a> providing essential mathematical special functions.
</p>
<p align="center">
<a href="https://crates.io/crates/libm-ext"> <img alt="Crates.io Version" src="https://img.shields.io/crates/v/libm-ext?style=for-the-badge"> </a>
<a href="https://docs.rs/libm-ext"> <img alt="docs.rs" src="https://img.shields.io/docsrs/libm-ext?style=for-the-badge"> </a>
<img alt="License: MIT OR Apache-2.0" src="https://img.shields.io/crates/l/libm-ext?style=for-the-badge"> 
</p>
</div>

## Usage

```rust
use libm_ext::{sinpi, sinpif};

println!("sinpi(1.0) = {}", sinpi(1.0));
println!("sinpif(1.0) = {}", sinpif(1.0));
```


## Trigonometric functions

- `sinpi` / `sinpif` for $\sin(\pi x)$ (`f64` / `f32`)
- `cospi` / `cospif` for $\cos(\pi x)$ (`f64` / `f32`)
- `sincospi` / `sincospif` for $\sin(\pi x)$ and $\cos(\pi x)$ (`f64` / `f32`)

## License

Licensed under either of:

 * Apache License, Version 2.0, ([LICENSE-APACHE](LICENSE-APACHE) or <https://www.apache.org/licenses/LICENSE-2.0>)
 * MIT license ([LICENSE-MIT](LICENSE-MIT) or <https://opensource.org/licenses/MIT>)

at your option.

### Contribution

Unless you explicitly state otherwise, any contribution intentionally submitted
for inclusion in the work by you, as defined in the Apache-2.0 license, shall be dual licensed as above, without any
additional terms or conditions.
