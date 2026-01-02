//! Trade visualization - displays completed trades on chart
//!
//! Trade represents a completed trade with entry/exit points and PnL.
//! This is for visualization only - actual trade logic is external.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::str::FromStr;

/// Trade direction
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum TradeDirection {
    #[default]
    Long,
    Short,
}

impl TradeDirection {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::Long => "long",
            Self::Short => "short",
        }
    }

    pub fn parse(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "long" | "buy" => Self::Long,
            "short" | "sell" => Self::Short,
            _ => Self::Long,
        }
    }

    pub fn symbol(&self) -> &'static str {
        match self {
            Self::Long => "^",
            Self::Short => "v",
        }
    }
}

impl FromStr for TradeDirection {
    type Err = ();

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Self::parse(s))
    }
}

/// Configuration for creating a Trade
#[derive(Clone, Debug)]
pub struct TradeConfig {
    /// Trade direction
    pub direction: TradeDirection,
    /// Entry bar index
    pub entry_bar: f64,
    /// Entry price
    pub entry_price: f64,
    /// Exit bar index
    pub exit_bar: f64,
    /// Exit price
    pub exit_price: f64,
    /// Profit/Loss
    pub pnl: f64,
    /// Strategy tag
    pub strategy_tag: String,
}

/// A completed trade for visualization
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Trade {
    /// Unique trade ID
    pub id: u64,
    /// Trade direction
    pub direction: TradeDirection,
    /// Entry bar index
    pub entry_bar: f64,
    /// Entry price
    pub entry_price: f64,
    /// Exit bar index
    pub exit_bar: f64,
    /// Exit price
    pub exit_price: f64,
    /// Profit/Loss
    pub pnl: f64,
    /// Strategy tag
    pub strategy_tag: String,
    /// Visibility
    pub visible: bool,
}

impl Trade {
    /// Create a new trade from configuration
    pub fn new(id: u64, config: TradeConfig) -> Self {
        Self {
            id,
            direction: config.direction,
            entry_bar: config.entry_bar,
            entry_price: config.entry_price,
            exit_bar: config.exit_bar,
            exit_price: config.exit_price,
            pnl: config.pnl,
            strategy_tag: config.strategy_tag,
            visible: true,
        }
    }

    /// Check if trade is profitable
    pub fn is_profitable(&self) -> bool {
        self.pnl > 0.0
    }

    /// Get duration in bars
    pub fn duration_bars(&self) -> f64 {
        self.exit_bar - self.entry_bar
    }

    /// Serialize to JSON
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    /// Deserialize from JSON
    pub fn from_json(json: &str) -> Option<Self> {
        serde_json::from_str(json).ok()
    }
}

/// Manager for trade visualization
#[derive(Clone, Debug, Default)]
pub struct TradeManager {
    /// All trades, keyed by trade ID
    trades: HashMap<u64, Trade>,
    /// Next trade ID
    next_id: u64,
    /// Global visibility toggle
    visible: bool,
    /// Show trade lines on chart
    show_lines: bool,
}

impl TradeManager {
    pub fn new() -> Self {
        Self {
            trades: HashMap::new(),
            next_id: 1,
            visible: true,
            show_lines: true,
        }
    }

    // =========================================================================
    // Trade Management
    // =========================================================================

    /// Add a trade from configuration
    pub fn add_trade(&mut self, config: TradeConfig) -> u64 {
        let id = self.next_id;
        self.next_id += 1;

        let trade = Trade::new(id, config);
        self.trades.insert(id, trade);
        id
    }

    /// Remove a trade by ID
    pub fn remove_trade(&mut self, id: u64) -> Option<Trade> {
        self.trades.remove(&id)
    }

    /// Remove all trades from a strategy
    pub fn remove_strategy_trades(&mut self, strategy_tag: &str) {
        self.trades.retain(|_, t| t.strategy_tag != strategy_tag);
    }

    /// Clear all trades
    pub fn clear(&mut self) {
        self.trades.clear();
    }

    /// Get trade by ID
    pub fn get(&self, id: u64) -> Option<&Trade> {
        self.trades.get(&id)
    }

    /// Get all trades
    pub fn trades(&self) -> impl Iterator<Item = &Trade> + '_ {
        self.trades.values()
    }

    /// Get trades for a specific strategy
    pub fn trades_for_strategy<'a>(
        &'a self,
        strategy_tag: &'a str,
    ) -> impl Iterator<Item = &'a Trade> + 'a {
        self.trades
            .values()
            .filter(move |t| t.strategy_tag == strategy_tag)
    }

    /// Get trade count
    pub fn count(&self) -> usize {
        self.trades.len()
    }

    // =========================================================================
    // Statistics
    // =========================================================================

    /// Get total PnL
    pub fn total_pnl(&self) -> f64 {
        self.trades.values().map(|t| t.pnl).sum()
    }

    /// Get win count
    pub fn win_count(&self) -> usize {
        self.trades.values().filter(|t| t.pnl > 0.0).count()
    }

    /// Get loss count
    pub fn loss_count(&self) -> usize {
        self.trades.values().filter(|t| t.pnl <= 0.0).count()
    }

    /// Get win rate (0.0 - 1.0)
    pub fn win_rate(&self) -> f64 {
        let total = self.trades.len();
        if total == 0 {
            return 0.0;
        }
        self.win_count() as f64 / total as f64
    }

    // =========================================================================
    // Visibility
    // =========================================================================

    /// Get global visibility
    pub fn is_visible(&self) -> bool {
        self.visible
    }

    /// Set global visibility
    pub fn set_visible(&mut self, visible: bool) {
        self.visible = visible;
    }

    /// Get show lines setting
    pub fn show_lines(&self) -> bool {
        self.show_lines
    }

    /// Set show lines setting
    pub fn set_show_lines(&mut self, show: bool) {
        self.show_lines = show;
    }

    // =========================================================================
    // Serialization
    // =========================================================================

    /// Get all trades as JSON array
    pub fn to_json(&self) -> String {
        let trades: Vec<String> = self.trades.values().map(|t| t.to_json()).collect();
        format!("[{}]", trades.join(","))
    }

    /// Load trades from JSON array
    pub fn load_json(&mut self, json: &str) {
        if let Ok(trades) = serde_json::from_str::<Vec<Trade>>(json) {
            for trade in trades {
                let id = trade.id;
                if id >= self.next_id {
                    self.next_id = id + 1;
                }
                self.trades.insert(id, trade);
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add_trade() {
        let mut manager = TradeManager::new();
        let id = manager.add_trade(TradeConfig {
            direction: TradeDirection::Long,
            entry_bar: 100.0,
            entry_price: 50000.0,
            exit_bar: 110.0,
            exit_price: 51000.0,
            pnl: 1000.0,
            strategy_tag: "test_strategy".to_string(),
        });
        assert_eq!(id, 1);
        assert_eq!(manager.count(), 1);
    }

    #[test]
    fn test_trade_stats() {
        let mut manager = TradeManager::new();
        manager.add_trade(TradeConfig {
            direction: TradeDirection::Long,
            entry_bar: 100.0,
            entry_price: 50000.0,
            exit_bar: 110.0,
            exit_price: 51000.0,
            pnl: 1000.0,
            strategy_tag: "test".to_string(),
        });
        manager.add_trade(TradeConfig {
            direction: TradeDirection::Long,
            entry_bar: 120.0,
            entry_price: 51000.0,
            exit_bar: 130.0,
            exit_price: 50500.0,
            pnl: -500.0,
            strategy_tag: "test".to_string(),
        });
        manager.add_trade(TradeConfig {
            direction: TradeDirection::Short,
            entry_bar: 140.0,
            entry_price: 50500.0,
            exit_bar: 150.0,
            exit_price: 49500.0,
            pnl: 1000.0,
            strategy_tag: "test".to_string(),
        });

        assert_eq!(manager.count(), 3);
        assert_eq!(manager.win_count(), 2);
        assert_eq!(manager.loss_count(), 1);
        assert!((manager.win_rate() - 0.6666).abs() < 0.01);
        assert!((manager.total_pnl() - 1500.0).abs() < 0.01);
    }

    #[test]
    fn test_trade_serialization() {
        let trade = Trade::new(
            1,
            TradeConfig {
                direction: TradeDirection::Long,
                entry_bar: 100.0,
                entry_price: 50000.0,
                exit_bar: 110.0,
                exit_price: 51000.0,
                pnl: 1000.0,
                strategy_tag: "test".to_string(),
            },
        );
        let json = trade.to_json();
        let restored = Trade::from_json(&json).unwrap();
        assert_eq!(restored.pnl, 1000.0);
    }
}
