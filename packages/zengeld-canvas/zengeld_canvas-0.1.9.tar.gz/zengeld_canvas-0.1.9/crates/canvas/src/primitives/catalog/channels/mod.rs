//! Channel-based primitives
//!
//! This module contains channel drawing tools:
//! - Parallel Channel: two parallel trend lines
//! - Regression Trend: linear regression channel
//! - Flat Top/Bottom: channel with one horizontal line
//! - Disjoint Channel: non-parallel channel (widening/narrowing)

pub mod disjoint_channel;
pub mod flat_top_bottom;
pub mod parallel_channel;
pub mod regression_trend;

// Re-export primitive types
pub use disjoint_channel::DisjointChannel;
pub use flat_top_bottom::FlatTopBottom;
pub use parallel_channel::ParallelChannel;
pub use regression_trend::RegressionTrend;
