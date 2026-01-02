//! Strategy signals system
//!
//! This module provides types and management for strategy-generated signals:
//! - `SignalType` - types of trading signals (Buy, Sell, TakeProfit, etc.)
//! - `SystemSignal` - a signal instance with position and styling
//! - `SignalManager` - manages collections of signals by strategy

mod manager;
mod types;

pub use manager::SignalManager;
pub use types::{SignalType, StrategySignalConfig, SystemSignal};
