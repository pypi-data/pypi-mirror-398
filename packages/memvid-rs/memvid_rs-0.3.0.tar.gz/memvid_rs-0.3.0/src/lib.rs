use pyo3::prelude::*;

mod encoder;
mod decoder;

use encoder::MemvidEncoder;
use decoder::MemvidDecoder;

#[pymodule]
fn _memvid_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<MemvidEncoder>()?;
    m.add_class::<MemvidDecoder>()?;
    Ok(())
}
