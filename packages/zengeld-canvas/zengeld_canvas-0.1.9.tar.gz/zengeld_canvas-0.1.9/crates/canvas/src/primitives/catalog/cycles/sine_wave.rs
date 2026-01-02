//! Sine Wave - sinusoidal wave pattern

use super::super::{
    LineStyle, Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata,
    RenderContext, TextAlign, TextAnchor, crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SineWave {
    pub data: PrimitiveData,
    pub bar1: f64,
    pub price1: f64,
    pub bar2: f64,
    pub price2: f64,
    #[serde(default = "default_amplitude")]
    pub amplitude: f64,
    #[serde(default = "default_cycles")]
    pub cycles: f64,
}
fn default_amplitude() -> f64 {
    10.0
}
fn default_cycles() -> f64 {
    2.0
}

impl SineWave {
    pub fn new(bar1: f64, price1: f64, bar2: f64, price2: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "sine_wave".to_string(),
                display_name: "Sine Wave".to_string(),
                color: PrimitiveColor::new(color),
                width: 2.0,
                ..Default::default()
            },
            bar1,
            price1,
            bar2,
            price2,
            amplitude: 10.0,
            cycles: 2.0,
        }
    }
}

impl Primitive for SineWave {
    fn type_id(&self) -> &'static str {
        "sine_wave"
    }
    fn display_name(&self) -> &str {
        &self.data.display_name
    }
    fn kind(&self) -> PrimitiveKind {
        PrimitiveKind::Measurement
    }
    fn data(&self) -> &PrimitiveData {
        &self.data
    }
    fn data_mut(&mut self) -> &mut PrimitiveData {
        &mut self.data
    }
    fn points(&self) -> Vec<(f64, f64)> {
        vec![(self.bar1, self.price1), (self.bar2, self.price2)]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, p)) = pts.first() {
            self.bar1 = b;
            self.price1 = p;
        }
        if let Some(&(b, p)) = pts.get(1) {
            self.bar2 = b;
            self.price2 = p;
        }
    }
    fn translate(&mut self, bd: f64, pd: f64) {
        self.bar1 += bd;
        self.bar2 += bd;
        self.price1 += pd;
        self.price2 += pd;
    }
    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        // Draw sine wave using small line segments
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);

        match self.data.style {
            LineStyle::Solid => ctx.set_line_dash(&[]),
            LineStyle::Dashed => ctx.set_line_dash(&[5.0, 5.0]),
            LineStyle::Dotted => ctx.set_line_dash(&[2.0, 3.0]),
            LineStyle::LargeDashed => ctx.set_line_dash(&[12.0, 6.0]),
            LineStyle::SparseDotted => ctx.set_line_dash(&[2.0, 8.0]),
        }

        ctx.begin_path();

        // Calculate sine wave parameters
        let steps = 100; // Number of line segments for smooth curve
        let mid_y = (y1 + y2) / 2.0;
        let amplitude = self.amplitude; // Use the amplitude field from the struct

        // Draw the sine wave
        for i in 0..=steps {
            let t = i as f64 / steps as f64;
            let px = x1 + (x2 - x1) * t;
            let py = mid_y + amplitude * (t * 2.0 * std::f64::consts::PI * self.cycles).sin();

            if i == 0 {
                ctx.move_to(crisp(px, dpr), crisp(py, dpr));
            } else {
                ctx.line_to(crisp(px, dpr), crisp(py, dpr));
            }
        }

        ctx.stroke();
    }
    fn text_anchor(&self, ctx: &dyn RenderContext) -> Option<TextAnchor> {
        let text = self.data.text.as_ref()?;
        if text.content.is_empty() {
            return None;
        }

        // Calculate bounding box including amplitude
        let x1 = ctx.bar_to_x(self.bar1);
        let y1 = ctx.price_to_y(self.price1);
        let x2 = ctx.bar_to_x(self.bar2);
        let y2 = ctx.price_to_y(self.price2);

        let mid_y = (y1 + y2) / 2.0;

        let left_x = x1.min(x2);
        let right_x = x1.max(x2);
        let top_y = mid_y - self.amplitude;
        let bottom_y = mid_y + self.amplitude;

        let x = match text.h_align {
            TextAlign::Start => left_x + 10.0,
            TextAlign::Center => (left_x + right_x) / 2.0,
            TextAlign::End => right_x - 10.0,
        };

        let y = match text.v_align {
            TextAlign::Start => top_y + 10.0 + text.font_size / 2.0,
            TextAlign::Center => mid_y,
            TextAlign::End => bottom_y - 10.0 - text.font_size / 2.0,
        };

        Some(TextAnchor::new(x, y, &self.data.color.stroke))
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
        type_id: "sine_wave",
        display_name: "Sine Wave",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b1, p1) = points.first().copied().unwrap_or((0.0, 100.0));
            let (b2, p2) = points.get(1).copied().unwrap_or((b1 + 40.0, p1));
            Box::new(SineWave::new(b1, p1, b2, p2, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
