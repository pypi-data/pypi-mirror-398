//! Anchored Volume Profile - volume profile from anchor

use super::super::{
    Primitive, PrimitiveColor, PrimitiveData, PrimitiveKind, PrimitiveMetadata, RenderContext,
    crisp,
};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AnchoredVolumeProfile {
    pub data: PrimitiveData,
    pub anchor_bar: f64,
    #[serde(default = "default_rows")]
    pub rows: u16,
    #[serde(default = "default_true")]
    pub show_poc: bool,
}
fn default_rows() -> u16 {
    24
}
fn default_true() -> bool {
    true
}

impl AnchoredVolumeProfile {
    pub fn new(bar: f64, color: &str) -> Self {
        Self {
            data: PrimitiveData {
                type_id: "anchored_volume_profile".to_string(),
                display_name: "Anchored Volume Profile".to_string(),
                color: PrimitiveColor::new(color),
                width: 1.0,
                ..Default::default()
            },
            anchor_bar: bar,
            rows: 24,
            show_poc: true,
        }
    }
}

impl Primitive for AnchoredVolumeProfile {
    fn type_id(&self) -> &'static str {
        "anchored_volume_profile"
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
        vec![(self.anchor_bar, 0.0)]
    }
    fn set_points(&mut self, pts: &[(f64, f64)]) {
        if let Some(&(b, _)) = pts.first() {
            self.anchor_bar = b;
        }
    }
    fn translate(&mut self, bd: f64, _pd: f64) {
        self.anchor_bar += bd;
    }

    fn render(&self, ctx: &mut dyn RenderContext, _is_selected: bool) {
        let dpr = ctx.dpr();
        let x = ctx.bar_to_x(self.anchor_bar);
        let chart_width = ctx.chart_width();
        let chart_height = ctx.chart_height();

        // Draw vertical anchor line
        ctx.set_stroke_color(&self.data.color.stroke);
        ctx.set_stroke_width(self.data.width);
        ctx.set_line_dash(&[]);

        ctx.begin_path();
        ctx.move_to(crisp(x, dpr), 0.0);
        ctx.line_to(crisp(x, dpr), chart_height);
        ctx.stroke();

        // Draw volume histogram from anchor to right edge
        let row_height = chart_height / self.rows as f64;
        let max_profile_width = (chart_width - x) * 0.4; // Max histogram width

        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_global_alpha(0.5);

        for i in 0..self.rows {
            let y = i as f64 * row_height;
            // Placeholder volume calculation - would integrate with actual market data
            let volume_pct =
                ((i as f64 - self.rows as f64 / 2.0).abs() / (self.rows as f64 / 2.0)).min(1.0);
            let bar_width = max_profile_width * (1.0 - volume_pct);

            ctx.begin_path();
            ctx.rect(x, y, bar_width, row_height);
            ctx.fill();
        }

        ctx.set_global_alpha(1.0);

        // Draw POC (Point of Control) line if enabled
        if self.show_poc {
            let poc_y = chart_height / 2.0; // Placeholder - highest volume level
            let poc_x_end = x + max_profile_width;
            ctx.set_stroke_color("#FFEB3B");
            ctx.set_stroke_width(2.0 * dpr);
            ctx.begin_path();
            ctx.move_to(crisp(x, dpr), crisp(poc_y, dpr));
            ctx.line_to(crisp(poc_x_end, dpr), crisp(poc_y, dpr));
            ctx.stroke();
        }

        // Draw anchor marker
        let cy = chart_height / 2.0;
        ctx.set_fill_color(&self.data.color.stroke);
        ctx.set_global_alpha(1.0);
        ctx.begin_path();
        ctx.arc(x, cy, 4.0 * dpr, 0.0, std::f64::consts::TAU);
        ctx.fill();
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
        type_id: "anchored_volume_profile",
        display_name: "Anchored Volume Profile",
        kind: PrimitiveKind::Measurement,
        factory: |points, color| {
            let (b, _) = points.first().copied().unwrap_or((0.0, 0.0));
            Box::new(AnchoredVolumeProfile::new(b, color))
        },
        supports_text: true,
        has_levels: false,
        has_points_config: false,
    }
}
