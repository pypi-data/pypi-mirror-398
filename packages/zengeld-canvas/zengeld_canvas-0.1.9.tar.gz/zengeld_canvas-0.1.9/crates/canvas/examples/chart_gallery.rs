//! Chart Gallery Example
//!
//! Demonstrates chart rendering with different themes and primitives.
//! Generates selected SVG outputs showcasing the rendering engine.

use std::fs;
use zengeld_canvas::api::{
    Chart, ChartConfig, Indicator, MultichartRenderer, PrimitiveConfig, SeriesConfig, SignalConfig,
};
use zengeld_canvas::core::Bar;
use zengeld_canvas::layout::MultichartLayout;
use zengeld_canvas::{RuntimeTheme, UITheme};

fn main() {
    // Create output directory
    let output_dir = "chart_output";
    fs::create_dir_all(output_dir).expect("Failed to create output directory");

    // Generate sample data
    let bars = generate_sample_bars(200);

    println!("Generating chart gallery...\n");

    // =========================================================================
    // Theme Showcase
    // =========================================================================

    // 05. Chart with MACD Subpane (Dark theme - default)
    println!("05. Chart with MACD Subpane (Dark Theme)");
    let svg = Chart::new(800, 500)
        .bars(&bars)
        .candlesticks()
        .ema(12, "#2196F3")
        .ema(26, "#FF9800")
        .macd(12, 26, 9)
        .render_svg();
    save_svg(&svg, &format!("{}/05_with_macd.svg", output_dir));

    // 09. Light Theme Chart
    println!("09. Light Theme Chart");
    let light_theme = UITheme::light();
    let svg = Chart::new(800, 400)
        .bars(&bars)
        .candlesticks()
        .background(light_theme.chart.background)
        .colors(
            light_theme.series.candle_up_body,
            light_theme.series.candle_down_body,
        )
        .sma(20, "#2196F3")
        .render_svg();
    save_svg(&svg, &format!("{}/09_light_theme.svg", output_dir));

    // 09b. High Contrast Theme Chart
    println!("09b. High Contrast Theme Chart");
    let contrast_theme = UITheme::high_contrast();
    let svg = Chart::new(800, 400)
        .bars(&bars)
        .candlesticks()
        .background(contrast_theme.chart.background)
        .colors(
            contrast_theme.series.candle_up_body,
            contrast_theme.series.candle_down_body,
        )
        .sma(20, contrast_theme.colors.accent)
        .render_svg();
    save_svg(&svg, &format!("{}/09b_high_contrast_theme.svg", output_dir));

    // 09c. Cyberpunk Theme Chart
    println!("09c. Cyberpunk Theme Chart");
    let cyber_theme = UITheme::cyberpunk();
    let svg = Chart::new(800, 400)
        .bars(&bars)
        .candlesticks()
        .background(cyber_theme.chart.background)
        .colors(
            cyber_theme.series.candle_up_body,
            cyber_theme.series.candle_down_body,
        )
        .sma(20, cyber_theme.colors.accent)
        .render_svg();
    save_svg(&svg, &format!("{}/09c_cyberpunk_theme.svg", output_dir));

    // 09d. Runtime Theme (custom JSON-modifiable)
    println!("09d. Runtime Theme (Custom)");
    let mut runtime_theme = RuntimeTheme::from_preset("dark");
    runtime_theme.chart.background = "#1a0a2e".to_string(); // Deep purple
    runtime_theme.series.candle_up_body = "#00ffff".to_string(); // Cyan
    runtime_theme.series.candle_down_body = "#ff00ff".to_string(); // Magenta
    let svg = Chart::new(800, 400)
        .bars(&bars)
        .candlesticks()
        .background(&runtime_theme.chart.background)
        .colors(
            &runtime_theme.series.candle_up_body,
            &runtime_theme.series.candle_down_body,
        )
        .sma(20, "#ffff00")
        .render_svg();
    save_svg(&svg, &format!("{}/09d_runtime_theme.svg", output_dir));

    // =========================================================================
    // Multichart Examples
    // =========================================================================

    // 13. 2x2 Grid - Different Series Types
    println!("13. Multichart 2x2 - Different Series Types");
    let layout_2x2 = MultichartLayout::quad();

    let config_candlestick = ChartConfig {
        series: SeriesConfig::candlestick(),
        indicators: vec![Indicator::sma("sma", 20, "#2196F3")],
        ..Default::default()
    };
    let config_line = ChartConfig {
        series: SeriesConfig::line(),
        indicators: vec![Indicator::ema("ema", 12, "#FF9800")],
        ..Default::default()
    };
    let config_area = ChartConfig {
        series: SeriesConfig::area(),
        ..Default::default()
    };
    let config_bar = ChartConfig {
        series: SeriesConfig::bar(),
        indicators: vec![Indicator::bollinger("bb", 20)],
        ..Default::default()
    };

    let svg = MultichartRenderer::new(&layout_2x2, 1200, 800)
        .chart(&config_candlestick, &bars)
        .chart(&config_line, &bars)
        .chart(&config_area, &bars)
        .chart(&config_bar, &bars)
        .render_svg();
    save_svg(&svg, &format!("{}/13_multichart_2x2.svg", output_dir));

    // 14. 1+3 Layout - Main chart + indicators
    println!("14. Multichart 1+3 - Main + Indicators");
    let layout_1_3 = MultichartLayout::one_plus_three();

    let config_main = ChartConfig {
        series: SeriesConfig::candlestick(),
        indicators: vec![
            Indicator::sma("sma_20", 20, "#2196F3"),
            Indicator::sma("sma_50", 50, "#FF9800"),
            Indicator::bollinger("bb", 20),
        ],
        ..Default::default()
    };
    let config_rsi = ChartConfig {
        series: SeriesConfig::line(),
        indicators: vec![Indicator::rsi("rsi", 14)],
        ..Default::default()
    };
    let config_macd = ChartConfig {
        series: SeriesConfig::line(),
        indicators: vec![Indicator::macd("macd", 12, 26, 9)],
        ..Default::default()
    };
    let config_volume = ChartConfig {
        series: SeriesConfig::line(),
        indicators: vec![Indicator::volume("vol")],
        ..Default::default()
    };

    let svg = MultichartRenderer::new(&layout_1_3, 1200, 800)
        .chart(&config_main, &bars)
        .chart(&config_rsi, &bars)
        .chart(&config_macd, &bars)
        .chart(&config_volume, &bars)
        .render_svg();
    save_svg(&svg, &format!("{}/14_multichart_1_3.svg", output_dir));

    // =========================================================================
    // Primitives Showcase
    // =========================================================================

    // 19. Channels
    println!("19. Primitives - Channels");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(
            PrimitiveConfig::parallel_channel(
                (20.0, bars[20].low),
                (80.0, bars[80].low),
                (20.0, bars[20].high + 3.0),
            )
            .with_color("#2196F3")
            .with_fill("#2196F3", 0.1),
        )
        .primitive(
            PrimitiveConfig::regression_trend((100.0, bars[100].close), (160.0, bars[160].close))
                .with_color("#FF9800"),
        )
        .render_svg();
    save_svg(&svg, &format!("{}/19_primitives_channels.svg", output_dir));

    // 20. Shapes
    println!("20. Primitives - Shapes");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(
            PrimitiveConfig::rectangle((30.0, bars[30].high), (60.0, bars[45].low))
                .with_color("#4CAF50")
                .with_fill("#4CAF50", 0.2),
        )
        .primitive(
            PrimitiveConfig::ellipse((100.0, bars[100].close), (115.0, bars[100].close + 5.0))
                .with_color("#E91E63")
                .with_fill("#E91E63", 0.15),
        )
        .primitive(
            PrimitiveConfig::triangle(
                (140.0, bars[140].low),
                (160.0, bars[160].high),
                (180.0, bars[180].low),
            )
            .with_color("#9C27B0")
            .with_fill("#9C27B0", 0.1),
        )
        .render_svg();
    save_svg(&svg, &format!("{}/20_primitives_shapes.svg", output_dir));

    // 21. Fibonacci Tools
    println!("21. Primitives - Fibonacci");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(PrimitiveConfig::fib_retracement(
            (20.0, bars[20].low),
            (80.0, bars[50].high),
        ))
        .primitive(
            PrimitiveConfig::fib_fan((100.0, bars[100].low), (140.0, bars[120].high))
                .with_color("#FF9800"),
        )
        .render_svg();
    save_svg(&svg, &format!("{}/21_primitives_fibonacci.svg", output_dir));

    // 22. Gann Tools
    println!("22. Primitives - Gann");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(PrimitiveConfig::gann_box(
            (30.0, bars[30].low),
            (90.0, bars[60].high),
        ))
        .primitive(
            PrimitiveConfig::gann_fan((120.0, bars[120].low), (180.0, bars[150].high))
                .with_color("#9C27B0"),
        )
        .render_svg();
    save_svg(&svg, &format!("{}/22_primitives_gann.svg", output_dir));

    // 23. Pitchforks
    println!("23. Primitives - Pitchforks");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(
            PrimitiveConfig::pitchfork(
                (20.0, bars[20].high),
                (50.0, bars[50].low),
                (80.0, bars[80].high),
            )
            .with_color("#2196F3"),
        )
        .primitive(
            PrimitiveConfig::schiff_pitchfork(
                (100.0, bars[100].high),
                (130.0, bars[130].low),
                (160.0, bars[160].high),
            )
            .with_color("#FF9800"),
        )
        .render_svg();
    save_svg(
        &svg,
        &format!("{}/23_primitives_pitchforks.svg", output_dir),
    );

    // 24. Annotations
    println!("24. Primitives - Annotations");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(PrimitiveConfig::text(
            (50.0, bars[50].high + 3.0),
            "Important Level",
        ))
        .primitive(PrimitiveConfig::note(
            (80.0, bars[80].low - 2.0),
            "Support Zone",
        ))
        .primitive(PrimitiveConfig::callout(
            (120.0, bars[120].high + 2.0),
            "Breakout!",
        ))
        .primitive(PrimitiveConfig::flag((150.0, bars[150].high)))
        .primitive(PrimitiveConfig::arrow_up((30.0, bars[30].low - 1.0)).with_color("#4CAF50"))
        .primitive(PrimitiveConfig::arrow_down((60.0, bars[60].high + 1.0)).with_color("#F44336"))
        .render_svg();
    save_svg(
        &svg,
        &format!("{}/24_primitives_annotations.svg", output_dir),
    );

    // 25. Patterns
    println!("25. Primitives - Patterns");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(
            PrimitiveConfig::triangle_pattern(
                (40.0, bars[40].low),
                (70.0, bars[55].high),
                (100.0, bars[100].low),
            )
            .with_color("#2196F3"),
        )
        .primitive(
            PrimitiveConfig::abcd_pattern(vec![
                (120.0, bars[120].low),
                (140.0, bars[130].high),
                (155.0, bars[145].low),
                (175.0, bars[160].high),
            ])
            .with_color("#FF9800"),
        )
        .render_svg();
    save_svg(&svg, &format!("{}/25_primitives_patterns.svg", output_dir));

    // 26. Projections & Positions
    println!("26. Primitives - Projections & Positions");
    let entry_price = bars[80].close;
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .primitive(PrimitiveConfig::long_position(
            (80.0, entry_price),
            (100.0, entry_price + 10.0),
            (70.0, entry_price - 5.0),
        ))
        .primitive(PrimitiveConfig::short_position(
            (140.0, bars[140].close),
            (160.0, bars[140].close - 8.0),
            (130.0, bars[140].close + 4.0),
        ))
        .primitive(
            PrimitiveConfig::price_range((20.0, bars[20].low), (50.0, bars[35].high))
                .with_color("#9C27B0"),
        )
        .render_svg();
    save_svg(&svg, &format!("{}/26_primitives_positions.svg", output_dir));

    // =========================================================================
    // Signals Showcase
    // =========================================================================

    // 28. Trading Strategy Signals
    println!("28. Signals - Trading Strategy");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .sma(10, "#26a69a")
        .sma(30, "#ef5350")
        .signal(SignalConfig::buy(25, bars[25].low - 2.0).with_label("Long"))
        .signal(SignalConfig::take_profit(45, bars[45].high + 1.0).with_label("TP1"))
        .signal(SignalConfig::take_profit(55, bars[55].high + 1.0).with_label("TP2"))
        .signal(SignalConfig::exit(65, bars[65].close).with_label("Exit"))
        .signal(SignalConfig::sell(90, bars[90].high + 2.0).with_label("Short"))
        .signal(SignalConfig::stop_loss(95, bars[95].high + 3.0).with_label("SL"))
        .signal(SignalConfig::take_profit(110, bars[110].low - 1.0).with_label("TP"))
        .signal(SignalConfig::buy(140, bars[140].low - 2.0).with_label("Long"))
        .signal(SignalConfig::exit(170, bars[170].close).with_label("Close"))
        .render_svg();
    save_svg(&svg, &format!("{}/28_signals_strategy.svg", output_dir));

    // 29. Technical Events
    println!("29. Events - Technical");
    let svg = Chart::new(1000, 500)
        .bars(&bars)
        .candlesticks()
        .sma(20, "#2196F3")
        .ema(50, "#FF9800")
        .primitive(PrimitiveConfig::crossover((35.0, bars[35].close)).with_color("#4CAF50"))
        .primitive(PrimitiveConfig::breakdown((85.0, bars[85].close)).with_color("#F44336"))
        .primitive(
            PrimitiveConfig::divergence((100.0, bars[100].low), (130.0, bars[130].low))
                .with_color("#9C27B0"),
        )
        .primitive(PrimitiveConfig::trend_event((150.0, bars[150].high)).with_color("#00BCD4"))
        .primitive(PrimitiveConfig::momentum_event((170.0, bars[170].close)).with_color("#E91E63"))
        .render_svg();
    save_svg(&svg, &format!("{}/29_events_technical.svg", output_dir));

    println!("\n[OK] All charts generated in '{}/'\n", output_dir);
    println!("Generated files:");
    println!("  - 05_with_macd.svg (Dark theme)");
    println!("  - 09_light_theme.svg (Light theme)");
    println!("  - 09b_high_contrast_theme.svg");
    println!("  - 09c_cyberpunk_theme.svg");
    println!("  - 09d_runtime_theme.svg (Custom)");
    println!("  - 13_multichart_2x2.svg");
    println!("  - 14_multichart_1_3.svg");
    println!("  - 19_primitives_channels.svg");
    println!("  - 20_primitives_shapes.svg");
    println!("  - 21_primitives_fibonacci.svg");
    println!("  - 22_primitives_gann.svg");
    println!("  - 23_primitives_pitchforks.svg");
    println!("  - 24_primitives_annotations.svg");
    println!("  - 25_primitives_patterns.svg");
    println!("  - 26_primitives_positions.svg");
    println!("  - 28_signals_strategy.svg");
    println!("  - 29_events_technical.svg");

    // Print theme JSON example
    println!("\n--- RuntimeTheme JSON Example ---");
    let theme = RuntimeTheme::dark();
    println!("{}", theme.to_json());
}

/// Generate sample OHLCV bars with realistic price movement
fn generate_sample_bars(count: usize) -> Vec<Bar> {
    let mut bars = Vec::with_capacity(count);
    let mut price = 100.0;
    let base_volume = 1_000_000.0;
    let start_time = 1700000000i64;

    for i in 0..count {
        let trend = ((i as f64 / count as f64) * std::f64::consts::PI * 2.0).sin() * 10.0;
        let noise = pseudo_random(i as u64) * 4.0 - 2.0;
        let change = trend * 0.1 + noise;

        price += change;
        price = price.max(50.0);

        let volatility = 1.0 + pseudo_random(i as u64 + 1000) * 2.0;
        let high = price + volatility;
        let low = price - volatility;

        let open = if pseudo_random(i as u64 + 2000) > 0.5 {
            low + pseudo_random(i as u64 + 3000) * (high - low)
        } else {
            high - pseudo_random(i as u64 + 4000) * (high - low)
        };

        let close = if pseudo_random(i as u64 + 5000) > 0.5 {
            low + pseudo_random(i as u64 + 6000) * (high - low)
        } else {
            high - pseudo_random(i as u64 + 7000) * (high - low)
        };

        let volume = base_volume * (0.5 + pseudo_random(i as u64 + 8000) * 1.5);

        bars.push(Bar {
            timestamp: start_time + (i as i64 * 86400),
            open,
            high,
            low,
            close,
            volume,
        });
    }

    bars
}

/// Simple pseudo-random number generator (deterministic for reproducibility)
fn pseudo_random(seed: u64) -> f64 {
    let x = seed.wrapping_mul(1103515245).wrapping_add(12345);
    let x = x.wrapping_mul(1103515245).wrapping_add(12345);
    ((x >> 16) & 0x7fff) as f64 / 32767.0
}

/// Save SVG to file
fn save_svg(svg: &str, path: &str) {
    fs::write(path, svg).unwrap_or_else(|_| panic!("Failed to write {}", path));
    println!("  -> Saved: {}", path);
}
