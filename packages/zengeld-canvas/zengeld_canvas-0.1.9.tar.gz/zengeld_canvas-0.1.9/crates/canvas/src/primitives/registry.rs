//! Primitive Registry - factory pattern for creating primitives
//!
//! This allows adding new primitives without modifying DrawingManager.
//! Each primitive type registers itself with metadata and a factory function.

use super::core::{Primitive, PrimitiveKind};
use std::collections::HashMap;
use std::sync::{OnceLock, RwLock};

/// Factory function type for creating primitives
pub type PrimitiveFactory = fn(points: &[(f64, f64)], color: &str) -> Box<dyn Primitive>;

/// Metadata about a primitive type
#[derive(Clone)]
pub struct PrimitiveMetadata {
    /// Unique type ID (e.g., "trend_line")
    pub type_id: &'static str,
    /// Display name for UI
    pub display_name: &'static str,
    /// Category for toolbar organization
    pub kind: PrimitiveKind,
    /// Factory function
    pub factory: PrimitiveFactory,
    /// Whether this primitive supports text labels (shows "Text" tab in settings)
    pub supports_text: bool,
    /// Whether this primitive has configurable levels (Fibonacci, Gann, Pitchfork - shows "Levels" tab)
    pub has_levels: bool,
    /// Whether this primitive has configurable control points (Elliott, Patterns - shows "Points" tab)
    pub has_points_config: bool,
}

/// Global primitive registry
///
/// Use `PrimitiveRegistry::global()` to access.
pub struct PrimitiveRegistry {
    primitives: HashMap<&'static str, PrimitiveMetadata>,
    by_kind: HashMap<PrimitiveKind, Vec<&'static str>>,
}

impl PrimitiveRegistry {
    /// Create a new empty registry
    pub fn new() -> Self {
        Self {
            primitives: HashMap::new(),
            by_kind: HashMap::new(),
        }
    }

    /// Get the global registry instance
    pub fn global() -> &'static RwLock<PrimitiveRegistry> {
        static REGISTRY: OnceLock<RwLock<PrimitiveRegistry>> = OnceLock::new();
        REGISTRY.get_or_init(|| {
            let mut registry = PrimitiveRegistry::new();
            // Register built-in primitives
            registry.register_builtins();
            RwLock::new(registry)
        })
    }

    /// Register a primitive type
    pub fn register(&mut self, metadata: PrimitiveMetadata) {
        let type_id = metadata.type_id;
        let kind = metadata.kind;

        self.primitives.insert(type_id, metadata);
        self.by_kind.entry(kind).or_default().push(type_id);
    }

    /// Get metadata for a primitive type
    pub fn get(&self, type_id: &str) -> Option<&PrimitiveMetadata> {
        self.primitives.get(type_id)
    }

    /// Create a primitive by type ID
    pub fn create(
        &self,
        type_id: &str,
        points: &[(f64, f64)],
        color: Option<&str>,
    ) -> Option<Box<dyn Primitive>> {
        let meta = self.primitives.get(type_id)?;
        let color = color.unwrap_or("#2196F3"); // Default blue color
        Some((meta.factory)(points, color))
    }

    /// Get all primitive type IDs in a category
    pub fn by_kind(&self, kind: PrimitiveKind) -> &[&'static str] {
        self.by_kind.get(&kind).map(|v| v.as_slice()).unwrap_or(&[])
    }

    /// Get all registered primitive types
    pub fn all(&self) -> impl Iterator<Item = &PrimitiveMetadata> {
        self.primitives.values()
    }

    /// Check if primitive type has configurable levels (Fibonacci, Gann, Pitchfork)
    pub fn has_levels(&self, type_id: &str) -> bool {
        self.primitives
            .get(type_id)
            .map(|m| m.has_levels)
            .unwrap_or(false)
    }

    /// Check if primitive type supports text
    pub fn supports_text(&self, type_id: &str) -> bool {
        self.primitives
            .get(type_id)
            .map(|m| m.supports_text)
            .unwrap_or(false)
    }

    /// Check if primitive type has configurable control points (Elliott, Patterns)
    pub fn has_points_config(&self, type_id: &str) -> bool {
        self.primitives
            .get(type_id)
            .map(|m| m.has_points_config)
            .unwrap_or(false)
    }

    /// Create a primitive from JSON (for undo/redo)
    /// Note: This only supports primitives that implement serde
    pub fn from_json(&self, type_id: &str, json: &str) -> Option<Box<dyn Primitive>> {
        match type_id {
            "fib_retracement" => {
                use super::catalog::fibonacci::retracement::FibRetracement;
                serde_json::from_str::<FibRetracement>(json)
                    .ok()
                    .map(|p| Box::new(p) as Box<dyn Primitive>)
            }
            "trend_line" => {
                use super::catalog::lines::trend_line::TrendLine;
                serde_json::from_str::<TrendLine>(json)
                    .ok()
                    .map(|p| Box::new(p) as Box<dyn Primitive>)
            }
            "horizontal_line" => {
                use super::catalog::lines::horizontal_line::HorizontalLine;
                serde_json::from_str::<HorizontalLine>(json)
                    .ok()
                    .map(|p| Box::new(p) as Box<dyn Primitive>)
            }
            "vertical_line" => {
                use super::catalog::lines::vertical_line::VerticalLine;
                serde_json::from_str::<VerticalLine>(json)
                    .ok()
                    .map(|p| Box::new(p) as Box<dyn Primitive>)
            }
            "rectangle" => {
                use super::catalog::shapes::rectangle::Rectangle;
                serde_json::from_str::<Rectangle>(json)
                    .ok()
                    .map(|p| Box::new(p) as Box<dyn Primitive>)
            }
            // For other types, fall back to re-creating from points
            _ => {
                // Try to extract points from JSON and recreate
                if let Ok(value) = serde_json::from_str::<serde_json::Value>(json) {
                    if let Some(points_arr) = value.get("points").and_then(|p| p.as_array()) {
                        let points: Vec<(f64, f64)> = points_arr
                            .iter()
                            .filter_map(|p| {
                                let arr = p.as_array()?;
                                Some((arr.first()?.as_f64()?, arr.get(1)?.as_f64()?))
                            })
                            .collect();
                        let color = value
                            .get("data")
                            .and_then(|d| d.get("color"))
                            .and_then(|c| c.get("stroke"))
                            .and_then(|s| s.as_str());
                        return self.create(type_id, &points, color);
                    }
                }
                None
            }
        }
    }

    /// Register all built-in primitives
    fn register_builtins(&mut self) {
        // Lines
        self.register(super::catalog::lines::trend_line::metadata());
        self.register(super::catalog::lines::horizontal_line::metadata());
        self.register(super::catalog::lines::vertical_line::metadata());
        self.register(super::catalog::lines::ray::metadata());
        self.register(super::catalog::lines::extended_line::metadata());
        self.register(super::catalog::lines::info_line::metadata());
        self.register(super::catalog::lines::trend_angle::metadata());
        self.register(super::catalog::lines::horizontal_ray::metadata());
        self.register(super::catalog::lines::cross_line::metadata());

        // Channels
        self.register(super::catalog::channels::parallel_channel::metadata());
        self.register(super::catalog::channels::regression_trend::metadata());
        self.register(super::catalog::channels::flat_top_bottom::metadata());
        self.register(super::catalog::channels::disjoint_channel::metadata());

        // Shapes
        self.register(super::catalog::shapes::rectangle::metadata());
        self.register(super::catalog::shapes::circle::metadata());
        self.register(super::catalog::shapes::ellipse::metadata());
        self.register(super::catalog::shapes::triangle::metadata());
        self.register(super::catalog::shapes::arc::metadata());
        self.register(super::catalog::shapes::polyline::metadata());
        self.register(super::catalog::shapes::path::metadata());
        self.register(super::catalog::shapes::rotated_rectangle::metadata());
        self.register(super::catalog::shapes::curve::metadata());
        self.register(super::catalog::shapes::double_curve::metadata());

        // Fibonacci
        self.register(super::catalog::fibonacci::retracement::metadata());
        self.register(super::catalog::fibonacci::trend_extension::metadata());
        self.register(super::catalog::fibonacci::channel::metadata());
        self.register(super::catalog::fibonacci::time_zones::metadata());
        self.register(super::catalog::fibonacci::speed_resistance::metadata());
        self.register(super::catalog::fibonacci::trend_time::metadata());
        self.register(super::catalog::fibonacci::circles::metadata());
        self.register(super::catalog::fibonacci::spiral::metadata());
        self.register(super::catalog::fibonacci::arcs::metadata());
        self.register(super::catalog::fibonacci::wedge::metadata());
        self.register(super::catalog::fibonacci::fan::metadata());

        // Pitchforks
        self.register(super::catalog::pitchforks::pitchfork::metadata());
        self.register(super::catalog::pitchforks::schiff::metadata());
        self.register(super::catalog::pitchforks::modified_schiff::metadata());
        self.register(super::catalog::pitchforks::inside_pitchfork::metadata());

        // Gann
        self.register(super::catalog::gann::gann_box::metadata());
        self.register(super::catalog::gann::gann_square_fixed::metadata());
        self.register(super::catalog::gann::gann_square::metadata());
        self.register(super::catalog::gann::gann_fan::metadata());

        // Arrows
        self.register(super::catalog::arrows::arrow_marker::metadata());
        self.register(super::catalog::arrows::arrow_line::metadata());
        self.register(super::catalog::arrows::arrow_up::metadata());
        self.register(super::catalog::arrows::arrow_down::metadata());

        // Annotations
        self.register(super::catalog::annotations::text::metadata());
        self.register(super::catalog::annotations::anchored_text::metadata());
        self.register(super::catalog::annotations::note::metadata());
        self.register(super::catalog::annotations::price_note::metadata());
        self.register(super::catalog::annotations::signpost::metadata());
        self.register(super::catalog::annotations::callout::metadata());
        self.register(super::catalog::annotations::comment::metadata());
        self.register(super::catalog::annotations::price_label::metadata());
        self.register(super::catalog::annotations::sign::metadata());
        self.register(super::catalog::annotations::flag::metadata());
        self.register(super::catalog::annotations::table::metadata());

        // Patterns
        self.register(super::catalog::patterns::xabcd_pattern::metadata());
        self.register(super::catalog::patterns::cypher_pattern::metadata());
        self.register(super::catalog::patterns::head_shoulders::metadata());
        self.register(super::catalog::patterns::abcd_pattern::metadata());
        self.register(super::catalog::patterns::triangle_pattern::metadata());
        self.register(super::catalog::patterns::three_drives::metadata());

        // Elliott
        self.register(super::catalog::elliott::elliott_impulse::metadata());
        self.register(super::catalog::elliott::elliott_correction::metadata());
        self.register(super::catalog::elliott::elliott_triangle::metadata());
        self.register(super::catalog::elliott::elliott_double_combo::metadata());
        self.register(super::catalog::elliott::elliott_triple_combo::metadata());

        // Cycles
        self.register(super::catalog::cycles::cycle_lines::metadata());
        self.register(super::catalog::cycles::time_cycles::metadata());
        self.register(super::catalog::cycles::sine_wave::metadata());

        // Projection
        self.register(super::catalog::projection::long_position::metadata());
        self.register(super::catalog::projection::short_position::metadata());
        self.register(super::catalog::projection::forecast::metadata());
        self.register(super::catalog::projection::bars_pattern::metadata());
        self.register(super::catalog::projection::price_projection::metadata());
        self.register(super::catalog::projection::general::metadata());

        // Volume
        self.register(super::catalog::volume::anchored_vwap::metadata());
        self.register(super::catalog::volume::fixed_volume_profile::metadata());
        self.register(super::catalog::volume::anchored_volume_profile::metadata());

        // Measurement
        self.register(super::catalog::measurement::price_range::metadata());
        self.register(super::catalog::measurement::date_range::metadata());
        self.register(super::catalog::measurement::price_date_range::metadata());

        // Brushes
        self.register(super::catalog::brushes::brush::metadata());
        self.register(super::catalog::brushes::highlighter::metadata());

        // Icons
        self.register(super::catalog::icons::image::metadata());
        self.register(super::catalog::icons::emoji::metadata());

        // Events (strategy-generated markers)
        self.register(super::catalog::events::crossover_metadata());
        self.register(super::catalog::events::breakdown_metadata());
        self.register(super::catalog::events::divergence_metadata());
        self.register(super::catalog::events::pattern_match_metadata());
        self.register(super::catalog::events::zone_event_metadata());
        self.register(super::catalog::events::volume_event_metadata());
        self.register(super::catalog::events::trend_event_metadata());
        self.register(super::catalog::events::momentum_event_metadata());
        self.register(super::catalog::events::custom_event_metadata());
    }
}

impl Default for PrimitiveRegistry {
    fn default() -> Self {
        Self::new()
    }
}

/// Helper macro to define primitive metadata
#[macro_export]
macro_rules! define_primitive {
    (
        type_id: $type_id:literal,
        display_name: $display_name:literal,
        kind: $kind:expr,
        click_behavior: $click:expr,
        tooltip: $tooltip:literal,
        icon: $icon:literal,
        default_color: $color:literal,
        factory: $factory:expr $(,)?
    ) => {
        pub fn metadata() -> $crate::drawing::primitives::PrimitiveMetadata {
            $crate::drawing::primitives::PrimitiveMetadata {
                type_id: $type_id,
                display_name: $display_name,
                kind: $kind,
                tooltip: $tooltip,
                icon: $icon,
                default_color: $color,
                factory: $factory,
                supports_text: true,
                has_levels: false,
                has_points_config: false,
            }
        }
    };
}
