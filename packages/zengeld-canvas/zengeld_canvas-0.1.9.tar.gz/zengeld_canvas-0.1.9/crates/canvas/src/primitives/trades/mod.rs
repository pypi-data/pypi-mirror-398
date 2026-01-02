//! Trade visualization system
//!
//! This module provides types for visualizing completed trades on charts:
//! - `Trade` - a completed trade with entry/exit points and PnL
//! - `TradeDirection` - Long or Short
//! - `TradeManager` - manages collections of trades

mod types;

pub use types::{Trade, TradeDirection, TradeManager};
