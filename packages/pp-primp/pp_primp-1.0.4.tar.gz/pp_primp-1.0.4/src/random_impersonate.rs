use std::sync::LazyLock;
use rand::prelude::*;

// 定义所有可用的浏览器指纹
static CHROME_VERSIONS: LazyLock<Vec<&'static str>> = LazyLock::new(|| {
    vec![
        "chrome_100", "chrome_101", "chrome_104", "chrome_105", "chrome_106",
        "chrome_107", "chrome_108", "chrome_109", "chrome_110", "chrome_114", "chrome_116",
        "chrome_117", "chrome_118", "chrome_119", "chrome_120", "chrome_123",
        "chrome_124", "chrome_126", "chrome_127", "chrome_128", "chrome_129",
        "chrome_130", "chrome_131", "chrome_132", "chrome_133", "chrome_134", "chrome_135",
        "chrome_136", "chrome_137", "chrome_138", "chrome_139", "chrome_140", "chrome_141",
        "chrome_142", "chrome_143",
    ]
});

static FIREFOX_VERSIONS: LazyLock<Vec<&'static str>> = LazyLock::new(|| {
    vec![
        "firefox_109", "firefox_117", "firefox_128", "firefox_133", "firefox_135",
        "firefox_136", "firefox_139", "firefox_142", "firefox_143", "firefox_144",
        "firefox_145","firefox_146", "firefox_private_135", "firefox_private_136", "firefox_android_135",
    ]
});

static SAFARI_VERSIONS: LazyLock<Vec<&'static str>> = LazyLock::new(|| {
    vec![
        "safari_15.3", "safari_15.5", "safari_15.6.1", "safari_16",
        "safari_16.5", "safari_17.0", "safari_17.2.1", "safari_17.4.1",
        "safari_17.5", "safari_17.6", "safari_18", "safari_18.2", "safari_18.3",
        "safari_18.3.1", "safari_18.5", "safari_26", "safari_26.1","safari_26.2",
        "safari_ios_16.5", "safari_ios_17.2", "safari_ios_17.4.1", "safari_ios_18.1.1",
        "safari_ios_26", "safari_ipad_18", "safari_ipad_26","safari_ipad_26.2","safari_ios_26.2",
    ]
});

static EDGE_VERSIONS: LazyLock<Vec<&'static str>> = LazyLock::new(|| {
    vec![
        "edge_101", "edge_122", "edge_127", "edge_131", "edge_134", "edge_142",
    ]
});

static OPERA_VERSIONS: LazyLock<Vec<&'static str>> = LazyLock::new(|| {
    vec![
        "opera_116", "opera_117", "opera_118", "opera_119",
    ]
});

static OKHTTP_VERSIONS: LazyLock<Vec<&'static str>> = LazyLock::new(|| {
    vec![
        "okhttp_3.9", "okhttp_3.11", "okhttp_3.13", "okhttp_3.14", "okhttp_4.9",
        "okhttp_4.10", "okhttp_4.12", "okhttp_5",
    ]
});

/// 根据浏览器类型随机选择一个版本
pub fn random_impersonate(browser_type: &str) -> Result<String, anyhow::Error> {
    let mut rng = rand::rng();

    let browser_type_lower = browser_type.to_lowercase();

    let result = match browser_type_lower.as_str() {
        "chrome" => CHROME_VERSIONS.choose(&mut rng).map(|v| v.to_string()),
        "firefox" => FIREFOX_VERSIONS.choose(&mut rng).map(|v| v.to_string()),
        "safari" => SAFARI_VERSIONS.choose(&mut rng).map(|v| v.to_string()),
        "edge" => EDGE_VERSIONS.choose(&mut rng).map(|v| v.to_string()),
        "opera" => OPERA_VERSIONS.choose(&mut rng).map(|v| v.to_string()),
        "okhttp" => OKHTTP_VERSIONS.choose(&mut rng).map(|v| v.to_string()),
        "random" | "all" => {
            // 从所有浏览器中随机选择
            let all_versions: Vec<&str> = CHROME_VERSIONS.iter()
                .chain(FIREFOX_VERSIONS.iter())
                .chain(FIREFOX_VERSIONS.iter())
                .chain(SAFARI_VERSIONS.iter())
                .chain(EDGE_VERSIONS.iter())
                .chain(OPERA_VERSIONS.iter())
                .chain(OKHTTP_VERSIONS.iter())
                .copied()
                .collect();
            all_versions.choose(&mut rng).map(|v| v.to_string())
        }
        _ => return Err(anyhow::anyhow!("Unknown browser type: {}", browser_type)),
    };

    result.ok_or_else(|| anyhow::anyhow!("No versions available"))
}