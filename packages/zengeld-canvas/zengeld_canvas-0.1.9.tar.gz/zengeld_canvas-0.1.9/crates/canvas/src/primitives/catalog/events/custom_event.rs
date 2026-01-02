//! Custom Event - User-defined strategy events with plugin extensibility

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

/// Custom event primitive - for user-defined strategy events
///
/// Supports multiple visual styles and is extensible for plugins.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CustomEvent {
    pub data: PrimitiveData,
    pub bar: f64,
    pub price: f64,
    /// Custom event type identifier (plugin namespace)
    #[serde(default)]
    pub event_type: String,
    /// Visual style
    #[serde(default)]
    pub style: CustomEventStyle,
    #[serde(default = "default_size")]
    pub size: f64,
    /// Custom metadata as JSON string (for plugins)
    #[serde(default)]
    pub metadata: String,
    /// Source strategy/plugin identifier
    #[serde(default)]
    pub source: String,
    /// Priority/importance level (0-10)
    #[serde(default)]
    pub priority: u8,
}

fn default_size() -> f64 {
    16.0
}

/// Visual style for custom events
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum CustomEventStyle {
    /// Circle marker
    Circle {
        #[serde(default = "default_true")]
        filled: bool,
    },
    /// Square marker
    Square {
        #[serde(default = "default_true")]
        filled: bool,
    },
    /// Diamond marker
    Diamond {
        #[serde(default = "default_true")]
        filled: bool,
    },
    /// Triangle (up or down)
    Triangle {
        #[serde(default = "default_true")]
        up: bool,
        #[serde(default = "default_true")]
        filled: bool,
    },
    /// Star marker
    Star {
        #[serde(default = "default_5")]
        points: u8,
    },
    /// Cross (X)
    Cross,
    /// Plus (+)
    Plus,
    /// Arrow
    Arrow {
        #[serde(default = "default_true")]
        up: bool,
    },
    /// Icon with text (emoji or single char)
    Icon {
        #[serde(default)]
        icon: String,
    },
    /// Text label
    Label {
        #[serde(default)]
        text: String,
        #[serde(default)]
        background: bool,
    },
    /// Badge (rounded rectangle with text)
    Badge {
        #[serde(default)]
        text: String,
    },
    /// Custom path (SVG-like path data)
    Path {
        #[serde(default)]
        path_data: String,
    },
}

fn default_true() -> bool {
    true
}
fn default_5() -> u8 {
    5
}

impl Default for CustomEventStyle {
    fn default() -> Self {
        Self::Circle { filled: true }
    }
}

impl CustomEvent {
    pub fn new(bar: f64, price: f64, event_type: &str, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "custom_event".to_string(),
                display_name: event_type.to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar,
            price,
            event_type: event_type.to_string(),
            style: CustomEventStyle::default(),
            size: default_size(),
            metadata: String::new(),
            source: String::new(),
            priority: 5,
        }
    }

    pub fn circle(bar: f64, price: f64, color: &str) -> Self {
        let mut event = Self::new(bar, price, "custom", color);
        event.style = CustomEventStyle::Circle { filled: true };
        event
    }

    pub fn diamond(bar: f64, price: f64, color: &str) -> Self {
        let mut event = Self::new(bar, price, "custom", color);
        event.style = CustomEventStyle::Diamond { filled: true };
        event
    }

    pub fn star(bar: f64, price: f64, color: &str) -> Self {
        let mut event = Self::new(bar, price, "custom", color);
        event.style = CustomEventStyle::Star { points: 5 };
        event
    }

    pub fn icon(bar: f64, price: f64, icon: &str, color: &str) -> Self {
        let mut event = Self::new(bar, price, "custom", color);
        event.style = CustomEventStyle::Icon {
            icon: icon.to_string(),
        };
        event
    }

    pub fn badge(bar: f64, price: f64, text: &str, color: &str) -> Self {
        let mut event = Self::new(bar, price, "custom", color);
        event.style = CustomEventStyle::Badge {
            text: text.to_string(),
        };
        event
    }

    pub fn with_style(mut self, style: CustomEventStyle) -> Self {
        self.style = style;
        self
    }

    pub fn with_source(mut self, source: &str) -> Self {
        self.source = source.to_string();
        self
    }

    pub fn with_metadata(mut self, metadata: &str) -> Self {
        self.metadata = metadata.to_string();
        self
    }

    pub fn with_priority(mut self, priority: u8) -> Self {
        self.priority = priority.min(10);
        self
    }

    fn render_star(&self, ctx: &mut dyn RenderContext, x: f64, y: f64, points: u8, dpr: f64) {
        let outer_radius = self.size / 2.0;
        let inner_radius = outer_radius * 0.4;
        let n = points as usize;
        let step = std::f64::consts::PI / n as f64;

        ctx.begin_path();
        for i in 0..(n * 2) {
            let r = if i % 2 == 0 {
                outer_radius
            } else {
                inner_radius
            };
            let angle = (i as f64 * step) - std::f64::consts::FRAC_PI_2;
            let px = x + r * angle.cos();
            let py = y + r * angle.sin();
            if i == 0 {
                ctx.move_to(crisp(px, dpr), crisp(py, dpr));
            } else {
                ctx.line_to(crisp(px, dpr), crisp(py, dpr));
            }
        }
        ctx.close_path();
        ctx.fill();
    }
}

impl Primitive for CustomEvent {
    fn type_id(&self) -> &'static str {
        "custom_event"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Signal
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar, self.price)]
    }
    fn set_points(&mut self, points: &[(f64, f64)]) {
        if let Some(&(b, p)) = points.first() {
            self.bar = b;
            self.price = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar += bd;
        self.price += pd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let s = self.size;
        let half = s / 2.0;

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        match &self.style {
            CustomEventStyle::Circle { filled } => {
                ctx.begin_path();
                ctx.arc(
                    crisp(x, dpr),
                    crisp(y, dpr),
                    half,
                    0.0,
                    std::f64::consts::TAU,
                );
                if *filled {
                    ctx.fill();
                } else {
                    ctx.stroke();
                }
            }
            CustomEventStyle::Square { filled } => {
                if *filled {
                    ctx.fill_rect(crisp(x - half, dpr), crisp(y - half, dpr), s, s);
                } else {
                    ctx.stroke_rect(crisp(x - half, dpr), crisp(y - half, dpr), s, s);
                }
            }
            CustomEventStyle::Diamond { filled } => {
                ctx.begin_path();
                ctx.move_to(crisp(x, dpr), crisp(y - half, dpr));
                ctx.line_to(crisp(x + half, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + half, dpr));
                ctx.line_to(crisp(x - half, dpr), crisp(y, dpr));
                ctx.close_path();
                if *filled {
                    ctx.fill();
                } else {
                    ctx.stroke();
                }
            }
            CustomEventStyle::Triangle { up, filled } => {
                ctx.begin_path();
                if *up {
                    ctx.move_to(crisp(x, dpr), crisp(y - half, dpr));
                    ctx.line_to(crisp(x - half, dpr), crisp(y + half, dpr));
                    ctx.line_to(crisp(x + half, dpr), crisp(y + half, dpr));
                } else {
                    ctx.move_to(crisp(x, dpr), crisp(y + half, dpr));
                    ctx.line_to(crisp(x - half, dpr), crisp(y - half, dpr));
                    ctx.line_to(crisp(x + half, dpr), crisp(y - half, dpr));
                }
                ctx.close_path();
                if *filled {
                    ctx.fill();
                } else {
                    ctx.stroke();
                }
            }
            CustomEventStyle::Star { points } => {
                self.render_star(ctx, x, y, *points, dpr);
            }
            CustomEventStyle::Cross => {
                ctx.begin_path();
                ctx.move_to(crisp(x - half, dpr), crisp(y - half, dpr));
                ctx.line_to(crisp(x + half, dpr), crisp(y + half, dpr));
                ctx.move_to(crisp(x + half, dpr), crisp(y - half, dpr));
                ctx.line_to(crisp(x - half, dpr), crisp(y + half, dpr));
                ctx.stroke();
            }
            CustomEventStyle::Plus => {
                ctx.begin_path();
                ctx.move_to(crisp(x - half, dpr), crisp(y, dpr));
                ctx.line_to(crisp(x + half, dpr), crisp(y, dpr));
                ctx.move_to(crisp(x, dpr), crisp(y - half, dpr));
                ctx.line_to(crisp(x, dpr), crisp(y + half, dpr));
                ctx.stroke();
            }
            CustomEventStyle::Arrow { up } => {
                ctx.begin_path();
                if *up {
                    ctx.move_to(crisp(x, dpr), crisp(y - half, dpr));
                    ctx.line_to(crisp(x - half * 0.7, dpr), crisp(y + half * 0.5, dpr));
                    ctx.line_to(crisp(x + half * 0.7, dpr), crisp(y + half * 0.5, dpr));
                } else {
                    ctx.move_to(crisp(x, dpr), crisp(y + half, dpr));
                    ctx.line_to(crisp(x - half * 0.7, dpr), crisp(y - half * 0.5, dpr));
                    ctx.line_to(crisp(x + half * 0.7, dpr), crisp(y - half * 0.5, dpr));
                }
                ctx.close_path();
                ctx.fill();
            }
            CustomEventStyle::Icon { icon } => {
                if !icon.is_empty() {
                    ctx.set_font(&format!("{}px sans-serif", s));
                    ctx.fill_text(icon, x - s / 3.0, y + s / 3.0);
                }
            }
            CustomEventStyle::Label { text, background } => {
                if !text.is_empty() {
                    if *background {
                        let text_width = (text.len() as f64 * 7.0) + 8.0;
                        let text_height = 16.0;
                        ctx.set_global_alpha(0.8);
                        ctx.fill_rect(
                            crisp(x - text_width / 2.0, dpr),
                            crisp(y - text_height / 2.0, dpr),
                            text_width,
                            text_height,
                        );
                        ctx.set_global_alpha(1.0);
                        ctx.set_fill_color("#FFFFFF");
                    }
                    ctx.set_font("12px sans-serif");
                    ctx.fill_text(text, x - (text.len() as f64 * 3.5), y + 4.0);
                }
            }
            CustomEventStyle::Badge { text } => {
                if !text.is_empty() {
                    let text_width = (text.len() as f64 * 7.0) + 12.0;
                    let text_height = 18.0;
                    // Draw as regular rect (rounded rect not available in RenderContext)
                    ctx.fill_rect(
                        crisp(x - text_width / 2.0, dpr),
                        crisp(y - text_height / 2.0, dpr),
                        text_width,
                        text_height,
                    );

                    ctx.set_fill_color("#FFFFFF");
                    ctx.set_font("11px sans-serif");
                    ctx.fill_text(text, x - (text.len() as f64 * 3.0), y + 4.0);
                }
            }
            CustomEventStyle::Path { path_data: _ } => {
                // TODO: Parse and render SVG-like path data
                // For now, just draw a circle
                ctx.begin_path();
                ctx.arc(
                    crisp(x, dpr),
                    crisp(y, dpr),
                    half,
                    0.0,
                    std::f64::consts::TAU,
                );
                ctx.stroke();
            }
        }
    }

    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        let x = ctx.bar_to_x(self.bar);
        let y = ctx.price_to_y(self.price);
        let offset = self.size + text.font_size / 2.0;
        Some(TextAnchor::new(x, y - offset, &self.data.color.stroke))
    }

    fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
    fn clone_box(&self) -> Box<dyn Primitive> {
        Box::new(self.clone())
    }
}

pub fn metadata() -> PrimitiveMetadata {
    PrimitiveMetadata {
        type_id: "custom_event",
        display_name: "Custom Event",
        kind: PrimitiveKind::Signal,
        factory: |points, color| {
            let (b, p) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(CustomEvent::new(b, p, "custom", color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
