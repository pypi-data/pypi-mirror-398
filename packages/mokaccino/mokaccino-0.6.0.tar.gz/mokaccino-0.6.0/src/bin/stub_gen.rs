#[cfg(feature = "stub-gen")]
use pyo3_stub_gen::Result;
#[cfg(not(feature = "stub-gen"))]
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

fn main() -> Result<()> {
    // `stub_info` is a function defined by `define_stub_info_gatherer!` macro.
    #[cfg(feature = "stub-gen")]
    let stub = mokaccino::stub_info()?;
    #[cfg(feature = "stub-gen")]
    stub.generate()?;
    #[cfg(not(feature = "stub-gen"))]
    println!("Stub generation is disabled. Enable the 'stub-gen' feature to generate stubs: cargo run -F stub-gen --bin stub_gen");
    Ok(())
}