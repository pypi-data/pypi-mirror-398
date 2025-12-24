//! Crate error type

use std::fmt::{self, Display, Formatter};

#[derive(Debug, Clone)]
pub struct NotEnoughFramesError;

pub type Result<T> = std::result::Result<T, NotEnoughFramesError>;

const MESSAGE: &str = "Not enough STFT frames to compute intermediate \
intelligibility measure after removing silent \
frames. Please check you wav files";

/// Implement Display for human-readable messages
impl Display for NotEnoughFramesError {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "{}", MESSAGE)
    }
}

/// Implement std::error::Error so it can be used with `?`
impl std::error::Error for NotEnoughFramesError {}
