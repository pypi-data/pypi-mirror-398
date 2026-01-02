//! Projection module - trading positions and forecasts

pub mod bars_pattern;
pub mod forecast;
pub mod general;
pub mod long_position;
pub mod price_projection;
pub mod short_position;

pub use bars_pattern::BarsPattern;
pub use forecast::Forecast;
pub use general::Projection;
pub use long_position::LongPosition;
pub use price_projection::PriceProjection;
pub use short_position::ShortPosition;
