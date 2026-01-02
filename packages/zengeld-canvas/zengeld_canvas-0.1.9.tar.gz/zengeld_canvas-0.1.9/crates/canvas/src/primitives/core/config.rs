//! Primitive Configuration System
//!
//! Provides a unified way to configure primitives through:
//! - Inline toolbar (quick settings: color, width, style)
//! - Context menu (clone, delete, lock, visibility, layer order)
//! - Settings modal (full configuration with tabs: Style, Coordinates, Visibility)
//!
//! # Architecture
//!
//! Each primitive can expose its configurable properties through the `Configurable` trait.
//! Properties are described as `ConfigProperty` which includes:
//! - Property ID and display name
//! - Property type (color, number, boolean, select, levels, etc.)
//! - Current value
//! - Constraints (min/max, options, etc.)

use serde::{Deserialize, Serialize};
use std::str::FromStr;

// =============================================================================
// Localization
// =============================================================================

/// Supported languages for UI labels
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
pub enum Language {
    #[default]
    English,
    Russian,
}

impl Language {
    /// Parse language from string (e.g., "en", "ru", "english", "russian")
    pub fn parse(s: &str) -> Self {
        match s.to_lowercase().as_str() {
            "ru" | "rus" | "russian" => Self::Russian,
            _ => Self::English,
        }
    }

    /// Get language code
    pub fn code(&self) -> &'static str {
        match self {
            Self::English => "en",
            Self::Russian => "ru",
        }
    }
}

impl FromStr for Language {
    type Err = ();

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        Ok(Self::parse(s))
    }
}

// =============================================================================
// Property Types
// =============================================================================

/// Type of configuration property
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum PropertyType {
    /// Color picker (hex string)
    Color,
    /// Numeric value with optional range
    Number {
        min: Option<f64>,
        max: Option<f64>,
        step: Option<f64>,
    },
    /// Integer value with optional range
    Integer { min: Option<i32>, max: Option<i32> },
    /// Boolean toggle
    Boolean,
    /// Select from predefined options
    Select { options: Vec<SelectOption> },
    /// Line style selector
    LineStyle,
    /// Text input
    Text {
        multiline: bool,
        max_length: Option<usize>,
    },
    /// Fibonacci levels (list of level configs)
    FibLevels,
    /// Coordinate (bar, price)
    Coordinate,
    /// Timeframe visibility settings
    TimeframeVisibility,
}

/// Option for Select property type
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct SelectOption {
    pub value: String,
    pub label: String,
}

impl SelectOption {
    pub fn new(value: &str, label: &str) -> Self {
        Self {
            value: value.to_string(),
            label: label.to_string(),
        }
    }
}

// =============================================================================
// Property Values
// =============================================================================

/// Value of a configuration property
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum PropertyValue {
    Color(String),
    Number(f64),
    Integer(i32),
    Boolean(bool),
    String(String),
    LineStyle(String), // "solid", "dashed", "dotted"
    FibLevels(Vec<FibLevelConfig>),
    Coordinate { bar: f64, price: f64 },
    TimeframeVisibility(TimeframeVisibilityConfig),
}

impl PropertyValue {
    pub fn as_color(&self) -> Option<&str> {
        match self {
            PropertyValue::Color(c) => Some(c),
            _ => None,
        }
    }

    pub fn as_number(&self) -> Option<f64> {
        match self {
            PropertyValue::Number(n) => Some(*n),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            PropertyValue::Boolean(b) => Some(*b),
            _ => None,
        }
    }

    pub fn as_string(&self) -> Option<&str> {
        match self {
            PropertyValue::String(s) => Some(s),
            PropertyValue::Color(s) => Some(s),
            PropertyValue::LineStyle(s) => Some(s),
            _ => None,
        }
    }

    pub fn as_coordinate(&self) -> Option<(f64, f64)> {
        match self {
            PropertyValue::Coordinate { bar, price } => Some((*bar, *price)),
            _ => None,
        }
    }
}

/// Configuration for a single Fibonacci level
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub struct FibLevelConfig {
    /// Level value (0.0, 0.236, 0.382, 0.5, 0.618, etc.)
    pub level: f64,
    /// Is this level visible
    pub visible: bool,
    /// Line color (if different from main color)
    pub color: Option<String>,
    /// Line width (if different from main width)
    pub width: Option<f64>,
    /// Line style
    pub style: String,
    /// Fill color for area below this level (to next level down)
    #[serde(default)]
    pub fill_color: Option<String>,
    /// Fill opacity (0.0 to 1.0)
    #[serde(default = "default_fill_opacity")]
    pub fill_opacity: f64,
    /// Whether fill is enabled for this level
    #[serde(default)]
    pub fill_enabled: bool,
}

fn default_fill_opacity() -> f64 {
    0.1
}

impl FibLevelConfig {
    pub fn new(level: f64) -> Self {
        Self {
            level,
            visible: true,
            color: None,
            width: None,
            style: "solid".to_string(),
            fill_color: None,
            fill_opacity: 0.1,
            fill_enabled: false,
        }
    }

    pub fn with_style(level: f64, style: &str) -> Self {
        Self {
            level,
            visible: true,
            color: None,
            width: None,
            style: style.to_string(),
            fill_color: None,
            fill_opacity: 0.1,
            fill_enabled: false,
        }
    }

    /// Create with fill enabled (for default preset with fills)
    pub fn with_fill(level: f64, fill_color: Option<String>, opacity: f64) -> Self {
        Self {
            level,
            visible: true,
            color: None,
            width: None,
            style: "solid".to_string(),
            fill_color,
            fill_opacity: opacity,
            fill_enabled: true,
        }
    }
}

/// Timeframe visibility configuration
#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq)]
pub struct TimeframeVisibilityConfig {
    /// Show on tick charts
    pub ticks: bool,
    /// Show on second charts (range: 1-59)
    pub seconds: Option<(u32, u32)>,
    /// Show on minute charts (range: 1-59)
    pub minutes: Option<(u32, u32)>,
    /// Show on hour charts (range: 1-24)
    pub hours: Option<(u32, u32)>,
    /// Show on day charts (range: 1-366)
    pub days: Option<(u32, u32)>,
    /// Show on week charts (range: 1-52)
    pub weeks: Option<(u32, u32)>,
    /// Show on month charts (range: 1-12)
    pub months: Option<(u32, u32)>,
    /// Show on range charts
    pub ranges: bool,
}

impl TimeframeVisibilityConfig {
    /// Create config that shows on all timeframes
    pub fn all() -> Self {
        Self {
            ticks: true,
            seconds: Some((1, 59)),
            minutes: Some((1, 59)),
            hours: Some((1, 24)),
            days: Some((1, 366)),
            weeks: Some((1, 52)),
            months: Some((1, 12)),
            ranges: true,
        }
    }

    /// Check if primitive is visible on a specific timeframe
    pub fn is_visible_on(&self, timeframe: &str, value: u32) -> bool {
        match timeframe {
            "tick" | "ticks" => self.ticks,
            "second" | "seconds" | "s" => self
                .seconds
                .is_some_and(|(min, max)| value >= min && value <= max),
            "minute" | "minutes" | "m" => self
                .minutes
                .is_some_and(|(min, max)| value >= min && value <= max),
            "hour" | "hours" | "h" => self
                .hours
                .is_some_and(|(min, max)| value >= min && value <= max),
            "day" | "days" | "d" | "D" => self
                .days
                .is_some_and(|(min, max)| value >= min && value <= max),
            "week" | "weeks" | "w" | "W" => self
                .weeks
                .is_some_and(|(min, max)| value >= min && value <= max),
            "month" | "months" | "M" => self
                .months
                .is_some_and(|(min, max)| value >= min && value <= max),
            "range" | "ranges" => self.ranges,
            _ => true,
        }
    }

    /// Check if this config shows on all timeframes
    pub fn is_all(&self) -> bool {
        self.ticks
            && self.seconds == Some((1, 59))
            && self.minutes == Some((1, 59))
            && self.hours == Some((1, 24))
            && self.days == Some((1, 366))
            && self.weeks == Some((1, 52))
            && self.months == Some((1, 12))
            && self.ranges
    }
}

// =============================================================================
// Config Property Definition
// =============================================================================

/// Category for grouping properties in UI
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum PropertyCategory {
    /// Style tab - colors, line styles, fills
    Style,
    /// Text tab - text content, font, alignment
    Text,
    /// Coordinates tab - points, bars, prices
    Coordinates,
    /// Visibility tab - timeframe visibility
    Visibility,
    /// Inputs tab - specific parameters (like Fib levels)
    Inputs,
}

/// A single configurable property
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ConfigProperty {
    /// Unique identifier for this property
    pub id: String,
    /// Display name (localized)
    pub name: String,
    /// Property type
    pub prop_type: PropertyType,
    /// Current value
    pub value: PropertyValue,
    /// Category for UI grouping
    pub category: PropertyCategory,
    /// Order within category (lower = first)
    pub order: i32,
    /// Is property read-only
    pub readonly: bool,
    /// Help text / tooltip
    pub tooltip: Option<String>,
}

impl ConfigProperty {
    /// Create a color property
    pub fn color(id: &str, name: &str, value: &str) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::Color,
            value: PropertyValue::Color(value.to_string()),
            category: PropertyCategory::Style,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Create a number property
    pub fn number(id: &str, name: &str, value: f64, min: Option<f64>, max: Option<f64>) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::Number {
                min,
                max,
                step: None,
            },
            value: PropertyValue::Number(value),
            category: PropertyCategory::Style,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Create a boolean property
    pub fn boolean(id: &str, name: &str, value: bool) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::Boolean,
            value: PropertyValue::Boolean(value),
            category: PropertyCategory::Style,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Create a line style property
    pub fn line_style(id: &str, name: &str, value: &str) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::LineStyle,
            value: PropertyValue::LineStyle(value.to_string()),
            category: PropertyCategory::Style,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Create a coordinate property
    pub fn coordinate(id: &str, name: &str, bar: f64, price: f64) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::Coordinate,
            value: PropertyValue::Coordinate { bar, price },
            category: PropertyCategory::Coordinates,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Create a text content property (multiline)
    pub fn text_content(id: &str, name: &str, value: &str) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::Text {
                multiline: true,
                max_length: Some(1000),
            },
            value: PropertyValue::String(value.to_string()),
            category: PropertyCategory::Text,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Create a text property (single line)
    pub fn text(id: &str, name: &str, value: &str) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::Text {
                multiline: false,
                max_length: Some(200),
            },
            value: PropertyValue::String(value.to_string()),
            category: PropertyCategory::Coordinates,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Create a select property
    pub fn select(id: &str, name: &str, value: &str, options: Vec<SelectOption>) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            prop_type: PropertyType::Select { options },
            value: PropertyValue::String(value.to_string()),
            category: PropertyCategory::Style,
            order: 0,
            readonly: false,
            tooltip: None,
        }
    }

    /// Set category
    pub fn with_category(mut self, category: PropertyCategory) -> Self {
        self.category = category;
        self
    }

    /// Set order
    pub fn with_order(mut self, order: i32) -> Self {
        self.order = order;
        self
    }

    /// Set tooltip
    pub fn with_tooltip(mut self, tooltip: &str) -> Self {
        self.tooltip = Some(tooltip.to_string());
        self
    }

    /// Set readonly
    pub fn readonly(mut self) -> Self {
        self.readonly = true;
        self
    }
}

// =============================================================================
// Configurable Trait
// =============================================================================

/// Trait for primitives that expose configuration properties
pub trait Configurable {
    /// Get all configurable properties
    fn get_properties(&self) -> Vec<ConfigProperty>;

    /// Set a property value by ID
    /// Returns true if property was found and updated
    fn set_property(&mut self, id: &str, value: PropertyValue) -> bool;

    /// Get timeframe visibility config (if supported)
    fn timeframe_visibility(&self) -> Option<&TimeframeVisibilityConfig> {
        None
    }

    /// Set timeframe visibility config
    fn set_timeframe_visibility(&mut self, _config: TimeframeVisibilityConfig) {
        // Default: do nothing (primitive doesn't support timeframe visibility)
    }
}

// =============================================================================
// Full Config Structure (for serialization to UI)
// =============================================================================

/// Full primitive configuration for UI
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PrimitiveFullConfig {
    /// Primitive ID
    pub id: u64,
    /// Type ID (e.g., "trend_line", "fib_retracement")
    pub type_id: String,
    /// Display name
    pub display_name: String,
    /// Is locked
    pub locked: bool,
    /// Is visible
    pub visible: bool,
    /// All properties grouped by category
    pub properties: Vec<ConfigProperty>,
}

impl PrimitiveFullConfig {
    /// Get properties by category
    pub fn properties_by_category(&self, category: PropertyCategory) -> Vec<&ConfigProperty> {
        self.properties
            .iter()
            .filter(|p| p.category == category)
            .collect()
    }

    /// Convert to JSON string
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
}

// =============================================================================
// Blanket Implementation for all Primitives
// =============================================================================

use super::Primitive;

/// Blanket implementation of Configurable for all Primitive types
/// This provides base configuration support (color, width, style, coordinates)
/// Individual primitives can override by implementing Configurable directly
impl<T: Primitive> Configurable for T {
    fn get_properties(&self) -> Vec<ConfigProperty> {
        let data = self.data();
        let mut props = data.base_properties();

        // Add text properties if primitive has text
        props.extend(data.text_properties());

        // Add coordinate properties from points()
        let points = self.points();
        for (i, (bar, price)) in points.iter().enumerate() {
            props.push(
                ConfigProperty::coordinate(
                    &format!("point{}", i + 1),
                    &format!("Point {}", i + 1),
                    *bar,
                    *price,
                )
                .with_order(100 + i as i32),
            );
        }

        props
    }

    fn set_property(&mut self, id: &str, value: PropertyValue) -> bool {
        // Handle base properties
        if self.data_mut().apply_property(id, &value) {
            return true;
        }

        // Handle coordinate properties (point1, point2, etc.)
        if let Some(suffix) = id.strip_prefix("point") {
            if let Some((bar, price)) = value.as_coordinate() {
                if let Ok(idx) = suffix.parse::<usize>() {
                    let idx = idx.saturating_sub(1); // point1 -> index 0
                    let mut points = self.points();
                    if idx < points.len() {
                        points[idx] = (bar, price);
                        self.set_points(&points);
                        return true;
                    }
                }
            }
        }

        false
    }

    fn timeframe_visibility(&self) -> Option<&TimeframeVisibilityConfig> {
        self.data().timeframe_visibility.as_ref()
    }

    fn set_timeframe_visibility(&mut self, config: TimeframeVisibilityConfig) {
        self.data_mut().timeframe_visibility = Some(config);
    }
}

// =============================================================================
// Settings Templates System
// =============================================================================

/// A saved template of primitive settings
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SettingsTemplate {
    /// Unique ID
    pub id: String,
    /// Display name (English)
    pub name: String,
    /// Display name (Russian) - for i18n
    #[serde(default)]
    pub name_ru: Option<String>,
    /// Type of primitive this applies to (e.g., "fib_retracement", "trend_line", or "*" for all)
    pub primitive_type: String,
    /// Style properties (color, width, line_style)
    pub style: TemplateStyle,
    /// Fib-specific settings (only for Fib primitives)
    pub fib_levels: Option<Vec<FibLevelConfig>>,
    /// Timeframe visibility (optional)
    pub timeframe_visibility: Option<TimeframeVisibilityConfig>,
    /// Is this a built-in template (non-deletable)
    pub builtin: bool,
    /// Creation timestamp
    pub created_at: u64,
}

/// Style portion of a template
#[derive(Clone, Debug, Serialize, Deserialize, Default)]
pub struct TemplateStyle {
    /// Main color
    pub color: Option<String>,
    /// Line width
    pub width: Option<f64>,
    /// Line style
    pub line_style: Option<String>,
    /// Fill color
    pub fill_color: Option<String>,
    /// Fill opacity
    pub fill_opacity: Option<f64>,
    /// Show labels
    pub show_labels: Option<bool>,
    /// Show prices
    pub show_prices: Option<bool>,
}

impl SettingsTemplate {
    /// Create a new template with given name and type
    pub fn new(id: &str, name: &str, primitive_type: &str) -> Self {
        Self {
            id: id.to_string(),
            name: name.to_string(),
            name_ru: None,
            primitive_type: primitive_type.to_string(),
            style: TemplateStyle::default(),
            fib_levels: None,
            timeframe_visibility: None,
            builtin: false,
            created_at: 0,
        }
    }

    /// Get localized name for the template
    pub fn localized_name(&self, lang: Language) -> &str {
        match lang {
            Language::Russian => self.name_ru.as_deref().unwrap_or(&self.name),
            Language::English => &self.name,
        }
    }

    /// Create from primitive JSON
    pub fn from_primitive_json(
        id: &str,
        name: &str,
        primitive_type: &str,
        json: &str,
    ) -> Option<Self> {
        // Parse JSON to extract style properties
        let value: serde_json::Value = serde_json::from_str(json).ok()?;

        let mut template = Self::new(id, name, primitive_type);

        // Extract style from data.color (or direct color field)
        if let Some(data) = value.get("data") {
            if let Some(color) = data.get("color") {
                if let Some(stroke) = color.get("stroke").and_then(|s| s.as_str()) {
                    template.style.color = Some(stroke.to_string());
                }
            }
            if let Some(width) = data.get("width").and_then(|w| w.as_f64()) {
                template.style.width = Some(width);
            }
            if let Some(line_style) = data.get("line_style").and_then(|s| s.as_str()) {
                template.style.line_style = Some(line_style.to_string());
            }
            if let Some(show_labels) = data.get("show_labels").and_then(|s| s.as_bool()) {
                template.style.show_labels = Some(show_labels);
            }
            if let Some(show_prices) = data.get("show_prices").and_then(|s| s.as_bool()) {
                template.style.show_prices = Some(show_prices);
            }
        }

        // Extract Fib levels if present
        if let Some(levels) = value.get("level_configs") {
            if let Ok(fib_levels) = serde_json::from_value::<Vec<FibLevelConfig>>(levels.clone()) {
                template.fib_levels = Some(fib_levels);
            }
        }

        // Extract timeframe visibility
        if let Some(data) = value.get("data") {
            if let Some(tfv) = data.get("timeframe_visibility") {
                if let Ok(config) = serde_json::from_value::<TimeframeVisibilityConfig>(tfv.clone())
                {
                    template.timeframe_visibility = Some(config);
                }
            }
        }

        Some(template)
    }

    /// Get builtin templates for a primitive type
    pub fn builtin_templates(primitive_type: &str) -> Vec<Self> {
        match primitive_type {
            "fib_retracement" => vec![
                Self::fib_standard(),
                Self::fib_extended(),
                Self::fib_colored_fills(),
            ],
            "trend_line" => vec![
                Self::line_standard(),
                Self::line_thick(),
                Self::line_dashed(),
            ],
            _ => vec![],
        }
    }

    // Built-in Fibonacci templates
    fn fib_standard() -> Self {
        use crate::primitives::catalog::fibonacci::retracement::default_level_configs;
        Self {
            id: "fib_standard".to_string(),
            name: "Standard".to_string(),
            name_ru: Some("Стандарт".to_string()),
            primitive_type: "fib_retracement".to_string(),
            style: TemplateStyle {
                color: Some("#787b86".to_string()),
                width: Some(1.0),
                line_style: Some("solid".to_string()),
                ..Default::default()
            },
            fib_levels: Some(default_level_configs()),
            timeframe_visibility: None,
            builtin: true,
            created_at: 0,
        }
    }

    fn fib_extended() -> Self {
        use crate::primitives::catalog::fibonacci::retracement::extended_level_configs;
        Self {
            id: "fib_extended".to_string(),
            name: "Extended".to_string(),
            name_ru: Some("Расширенный".to_string()),
            primitive_type: "fib_retracement".to_string(),
            style: TemplateStyle {
                color: Some("#787b86".to_string()),
                width: Some(1.0),
                line_style: Some("solid".to_string()),
                ..Default::default()
            },
            fib_levels: Some(extended_level_configs()),
            timeframe_visibility: None,
            builtin: true,
            created_at: 0,
        }
    }

    fn fib_colored_fills() -> Self {
        use crate::primitives::catalog::fibonacci::retracement::filled_level_configs;
        Self {
            id: "fib_filled".to_string(),
            name: "With Fill".to_string(),
            name_ru: Some("С заливкой".to_string()),
            primitive_type: "fib_retracement".to_string(),
            style: TemplateStyle {
                color: Some("#787b86".to_string()),
                width: Some(1.0),
                line_style: Some("solid".to_string()),
                ..Default::default()
            },
            fib_levels: Some(filled_level_configs()),
            timeframe_visibility: None,
            builtin: true,
            created_at: 0,
        }
    }

    // Built-in line templates
    fn line_standard() -> Self {
        Self {
            id: "line_standard".to_string(),
            name: "Standard".to_string(),
            name_ru: Some("Стандарт".to_string()),
            primitive_type: "trend_line".to_string(),
            style: TemplateStyle {
                color: Some("#2962ff".to_string()),
                width: Some(1.0),
                line_style: Some("solid".to_string()),
                ..Default::default()
            },
            fib_levels: None,
            timeframe_visibility: None,
            builtin: true,
            created_at: 0,
        }
    }

    fn line_thick() -> Self {
        Self {
            id: "line_thick".to_string(),
            name: "Thick".to_string(),
            name_ru: Some("Толстая".to_string()),
            primitive_type: "trend_line".to_string(),
            style: TemplateStyle {
                color: Some("#2962ff".to_string()),
                width: Some(3.0),
                line_style: Some("solid".to_string()),
                ..Default::default()
            },
            fib_levels: None,
            timeframe_visibility: None,
            builtin: true,
            created_at: 0,
        }
    }

    fn line_dashed() -> Self {
        Self {
            id: "line_dashed".to_string(),
            name: "Dashed".to_string(),
            name_ru: Some("Пунктирная".to_string()),
            primitive_type: "trend_line".to_string(),
            style: TemplateStyle {
                color: Some("#787b86".to_string()),
                width: Some(1.0),
                line_style: Some("dashed".to_string()),
                ..Default::default()
            },
            fib_levels: None,
            timeframe_visibility: None,
            builtin: true,
            created_at: 0,
        }
    }

    /// Convert to JSON
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    /// Parse from JSON
    pub fn from_json(json: &str) -> Option<Self> {
        serde_json::from_str(json).ok()
    }
}

/// Collection of templates
#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct TemplateCollection {
    /// User-created templates
    pub templates: Vec<SettingsTemplate>,
}

impl TemplateCollection {
    /// Create empty collection
    pub fn new() -> Self {
        Self {
            templates: Vec::new(),
        }
    }

    /// Add a template
    pub fn add(&mut self, template: SettingsTemplate) {
        // Remove existing template with same ID
        self.templates.retain(|t| t.id != template.id);
        self.templates.push(template);
    }

    /// Remove a template by ID
    pub fn remove(&mut self, id: &str) -> bool {
        let len_before = self.templates.len();
        self.templates.retain(|t| t.id != id || t.builtin);
        self.templates.len() < len_before
    }

    /// Get template by ID
    pub fn get(&self, id: &str) -> Option<&SettingsTemplate> {
        self.templates.iter().find(|t| t.id == id)
    }

    /// Get all templates for a primitive type (including built-in)
    pub fn templates_for_type(&self, primitive_type: &str) -> Vec<&SettingsTemplate> {
        self.templates
            .iter()
            .filter(|t| t.primitive_type == primitive_type || t.primitive_type == "*")
            .collect()
    }

    /// Get combined list of builtin + user templates for a type
    pub fn all_templates_for_type(&self, primitive_type: &str) -> Vec<SettingsTemplate> {
        let mut result = SettingsTemplate::builtin_templates(primitive_type);
        for t in &self.templates {
            if t.primitive_type == primitive_type || t.primitive_type == "*" {
                result.push(t.clone());
            }
        }
        result
    }

    /// To JSON
    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }

    /// From JSON
    pub fn from_json(json: &str) -> Self {
        serde_json::from_str(json).unwrap_or_default()
    }
}

// =============================================================================
// Property Labels i18n
// =============================================================================

/// Get localized label for a property ID
///
/// This function provides translated labels for common property identifiers.
/// Use this when displaying properties in the UI.
/// Returns None if the property ID is not found in the translation table.
pub fn localized_property_label(id: &str, lang: Language) -> Option<&'static str> {
    match lang {
        Language::English => match id {
            // Style properties
            "stroke_color" => Some("Stroke Color"),
            "fill_color" => Some("Fill Color"),
            "width" => Some("Width"),
            "line_style" => Some("Line Style"),
            "visible" => Some("Visible"),
            // Text properties
            "text_content" => Some("Text"),
            "text_font_size" => Some("Font Size"),
            "text_color" => Some("Text Color"),
            "text_bold" => Some("Bold"),
            "text_italic" => Some("Italic"),
            "text_h_align" => Some("Horizontal Align"),
            "text_v_align" => Some("Vertical Align"),
            // Alignment values
            "start" => Some("Start"),
            "center" => Some("Center"),
            "end" => Some("End"),
            // Alignment labels (UI display)
            "left" => Some("Left"),
            "right" => Some("Right"),
            "top" => Some("Top"),
            "bottom" => Some("Bottom"),
            _ => None,
        },
        Language::Russian => match id {
            // Style properties
            "stroke_color" => Some("Цвет линии"),
            "fill_color" => Some("Цвет заливки"),
            "width" => Some("Толщина"),
            "line_style" => Some("Стиль линии"),
            "visible" => Some("Видимость"),
            // Text properties
            "text_content" => Some("Текст"),
            "text_font_size" => Some("Размер шрифта"),
            "text_color" => Some("Цвет текста"),
            "text_bold" => Some("Жирный"),
            "text_italic" => Some("Курсив"),
            "text_h_align" => Some("Горизонтальное выравнивание"),
            "text_v_align" => Some("Вертикальное выравнивание"),
            // Alignment values
            "start" => Some("Начало"),
            "center" => Some("По центру"),
            "end" => Some("Конец"),
            // Alignment labels (UI display)
            "left" => Some("Слева"),
            "right" => Some("Справа"),
            "top" => Some("Сверху"),
            "bottom" => Some("Снизу"),
            _ => None,
        },
    }
}

/// Get localized select option labels for text alignment
pub fn localized_h_align_options(lang: Language) -> Vec<SelectOption> {
    match lang {
        Language::English => vec![
            SelectOption::new("start", "Left"),
            SelectOption::new("center", "Center"),
            SelectOption::new("end", "Right"),
        ],
        Language::Russian => vec![
            SelectOption::new("start", "Слева"),
            SelectOption::new("center", "По центру"),
            SelectOption::new("end", "Справа"),
        ],
    }
}

/// Get localized select option labels for vertical text alignment
pub fn localized_v_align_options(lang: Language) -> Vec<SelectOption> {
    match lang {
        Language::English => vec![
            SelectOption::new("start", "Top"),
            SelectOption::new("center", "Center"),
            SelectOption::new("end", "Bottom"),
        ],
        Language::Russian => vec![
            SelectOption::new("start", "Сверху"),
            SelectOption::new("center", "По центру"),
            SelectOption::new("end", "Снизу"),
        ],
    }
}
