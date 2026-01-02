//! Pitchfork primitives
//!
//! Andrew's Pitchfork and its variants - trend analysis tools
//! that use three points to define a median line with parallel support/resistance.

pub mod inside_pitchfork;
pub mod modified_schiff;
pub mod pitchfork;
pub mod schiff;

pub use inside_pitchfork::InsidePitchfork;
pub use modified_schiff::ModifiedSchiff;
pub use pitchfork::Pitchfork;
pub use schiff::SchiffPitchfork;
