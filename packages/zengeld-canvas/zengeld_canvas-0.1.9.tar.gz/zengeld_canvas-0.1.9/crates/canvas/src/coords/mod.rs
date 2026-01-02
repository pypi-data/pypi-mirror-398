//! Coordinate Systems for Financial Charts
//!
//! Core coordinate conversion between data space and pixel space:
//!
//! - **`Viewport`** - Main API combining TimeScale + PriceScale
//! - `TimeScale` - X-axis (bar ↔ pixel, navigation, time ticks)
//! - `PriceScale` - Y-axis (price ↔ pixel, modes, price ticks)
//!
//! # Usage
//!
//! ```rust
//! use zengeld_canvas::coords::Viewport;
//! use zengeld_canvas::Bar;
//!
//! let mut vp = Viewport::new(800.0, 600.0);
//! let bars = vec![Bar::new(1000, 100.0, 110.0, 95.0, 105.0)];
//! vp.set_bars(&bars);
//! vp.scroll_to_end();
//!
//! let x = vp.bar_to_x(0);
//! let y = vp.price_to_y(100.5);
//! ```

pub mod price_scale;
pub mod time_scale;
pub mod viewport;

// Primary API
pub use viewport::Viewport;

// X-axis (TimeScale)
pub use time_scale::{
    DAY, HOUR, MINUTE, TickMarkWeight, TimeScale, TimeTick, format_time_by_weight, format_time_full,
};

// Y-axis (PriceScale)
pub use price_scale::{
    NICE_MULTIPLIERS, PriceScale, PriceScaleMode, format_price, lwc_nice_number, nice_number,
    nice_price_step, price_precision,
};

// Legacy alias for ChartCoords users
#[deprecated(since = "0.2.0", note = "Use Viewport instead")]
pub type ChartCoords = Viewport;
