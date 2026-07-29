//! Per-section field visibility helpers.

use crate::schema::Config;

pub fn memory_backend_excludes(backend: &str) -> Vec<&'static str> {
    let mut out = Vec::new();
    if backend != "sqlite" {
        out.push("sqlite-open-timeout-secs");
        out.push("conversation-retention-days");
    }
    if backend != "qdrant" {
        out.push("qdrant.");
    }
    if backend != "postgres" {
        out.push("postgres.");
    }
    out
}

/// Returns config paths that should be hidden because the corresponding
/// Cargo feature was NOT enabled at compile time.
///
/// Each entry is either:
/// - an exact path like `"hardware"` (hides the whole section)
/// - a prefix ending with `.` like `"channels.discord."` (hides everything under it)
pub fn feature_disabled_paths() -> Vec<&'static str> {
    let mut out = Vec::new();

    // -- Subsystems ----------------------------------------------------
    if !cfg!(feature = "_cfg-gateway")            { out.push("gateway."); }
    if !cfg!(feature = "_cfg-hardware")           { out.push("hardware."); out.push("peripherals."); }
    if !cfg!(feature = "_cfg-plugins-wasm")       { out.push("plugins."); }
    if !cfg!(feature = "_cfg-webauthn")           { out.push("webauthn."); }
    if !cfg!(feature = "_cfg-acp-bridge")          { /* acp-bridge is a sidecar binary, no config to hide */ }
    if !cfg!(feature = "_cfg-browser-native")      { out.push("browser_delegate."); }
    if !cfg!(feature = "_cfg-channel-acp-server")   { out.push("acp."); }

    // -- Observability (hide when neither is enabled) ------------------
    if !cfg!(feature = "_cfg-observability-prometheus")
        && !cfg!(feature = "_cfg-observability-otel")
    {
        out.push("observability.");
    }

    // -- Channels -------------------------------------------------------
    // Each channel feature that is NOT compiled → hide its config subsection.
    // The field names below match the Rust struct field names in ChannelsConfig,
    // which become dot-separated config paths via #[derive(Configurable)].
    if !cfg!(feature = "_cfg-channel-acp-server")      { /* ACP server has no per-channel config section */ }
    if !cfg!(feature = "_cfg-channel-amqp")              { out.push("channels.amqp."); }
    if !cfg!(feature = "_cfg-channel-bluesky")           { out.push("channels.bluesky."); }
    if !cfg!(feature = "_cfg-channel-clawdtalk")         { out.push("channels.clawdtalk."); }
    if !cfg!(feature = "_cfg-channel-dingtalk")          { out.push("channels.dingtalk."); }
    if !cfg!(feature = "_cfg-channel-discord")           { out.push("channels.discord."); }
    if !cfg!(feature = "_cfg-channel-email")              { out.push("channels.email."); }
    if !cfg!(feature = "_cfg-channel-filesystem")        { out.push("channels.filesystem."); }
    if !cfg!(feature = "_cfg-channel-git")                { out.push("channels.git."); }
    if !cfg!(feature = "_cfg-channel-imessage")          { out.push("channels.imessage."); }
    if !cfg!(feature = "_cfg-channel-irc")                { out.push("channels.irc."); }
    if !cfg!(feature = "_cfg-channel-lark")               { out.push("channels.lark."); }
    if !cfg!(feature = "_cfg-channel-line")               { out.push("channels.line."); }
    if !cfg!(feature = "_cfg-channel-linq")               { out.push("channels.linq."); }
    if !cfg!(feature = "_cfg-channel-mattermost")        { out.push("channels.mattermost."); }
    if !cfg!(feature = "_cfg-channel-matrix")             { out.push("channels.matrix."); }
    if !cfg!(feature = "_cfg-channel-mochat")             { out.push("channels.mochat."); }
    if !cfg!(feature = "_cfg-channel-mqtt")               { out.push("channels.mqtt."); }
    if !cfg!(feature = "_cfg-channel-nextcloud")         { out.push("channels.nextcloud_talk."); }
    if !cfg!(feature = "_cfg-channel-nostr")              { out.push("channels.nostr."); }
    if !cfg!(feature = "_cfg-channel-notion")             { /* notion is a top-level Config field, not under channels */ }
    if !cfg!(feature = "_cfg-channel-qq")                 { out.push("channels.qq."); }
    if !cfg!(feature = "_cfg-channel-reddit")             { out.push("channels.reddit."); }
    if !cfg!(feature = "_cfg-channel-signal")             { out.push("channels.signal."); }
    if !cfg!(feature = "_cfg-channel-slack")              { out.push("channels.slack."); }
    if !cfg!(feature = "_cfg-channel-telegram")          { out.push("channels.telegram."); }
    if !cfg!(feature = "_cfg-channel-twitch")             { out.push("channels.twitch."); }
    if !cfg!(feature = "_cfg-channel-twitter")            { out.push("channels.twitter."); }
    if !cfg!(feature = "_cfg-channel-voice-call")        { out.push("channels.voice_call."); }
    if !cfg!(feature = "_cfg-channel-wati")               { out.push("channels.wati."); }
    if !cfg!(feature = "_cfg-channel-wechat")             { out.push("channels.wechat."); }
    if !cfg!(feature = "_cfg-channel-wecom")              { out.push("channels.wecom."); }
    if !cfg!(feature = "_cfg-channel-wecom-ws")          { out.push("channels.wecom_ws."); }
    if !cfg!(feature = "_cfg-channel-webhook")            { out.push("channels.webhook."); }
    if !cfg!(feature = "_cfg-channel-whatsapp-cloud")    { out.push("channels.whatsapp."); }
    if !cfg!(feature = "_cfg-whatsapp-web")               { out.push("channels.whatsapp."); }

    out
}

pub fn excluded_paths(cfg: &Config, prefix: &str) -> Vec<String> {
    let mut out: Vec<String> = Vec::new();

    // 1) Compile-time feature gates — always apply regardless of prefix.
    for p in feature_disabled_paths() {
        out.push(p.to_string());
    }

    // 2) Runtime memory-backend filter.
    if prefix == "memory" || prefix.is_empty() {
        let backend = if cfg.memory.backend.is_empty() {
            "sqlite"
        } else {
            cfg.memory.backend.as_str()
        };
        for leaf in memory_backend_excludes(backend) {
            out.push(format!("memory.{leaf}"));
        }
    }

    out
}

/// Test whether `path` is one of the excluded entries returned from
/// `excluded_paths`. Handles both exact matches and sub-table prefix
/// markers (`"memory.qdrant."` matches every `memory.qdrant.*`).
pub fn is_excluded(path: &str, excludes: &[String]) -> bool {
    excludes
        .iter()
        .any(|e| path == e || (e.ends_with('.') && path.starts_with(e)))
}

/// Test whether `path` equals `prefix` or sits beneath it at a `.` segment
/// boundary. A bare `starts_with` is wrong here: prefix `agents.aaa` must
/// not match `agents.aaalore.workspace`.
pub fn path_matches_prefix(path: &str, prefix: &str) -> bool {
    match path.strip_prefix(prefix) {
        Some(rest) => {
            prefix.is_empty() || rest.is_empty() || rest.starts_with('.') || prefix.ends_with('.')
        }
        None => false,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn memory_excludes_hide_inactive_backends() {
        // sqlite active → hide qdrant + postgres subsections, keep sqlite
        // open-timeout
        let ex = memory_backend_excludes("sqlite");
        assert!(ex.contains(&"qdrant."));
        assert!(ex.contains(&"postgres."));
        assert!(!ex.contains(&"sqlite-open-timeout-secs"));
        assert!(!ex.contains(&"conversation-retention-days"));

        // qdrant active → hide sqlite-only knobs + postgres
        let ex = memory_backend_excludes("qdrant");
        assert!(!ex.contains(&"qdrant."));
        assert!(ex.contains(&"postgres."));
        assert!(ex.contains(&"sqlite-open-timeout-secs"));
        assert!(ex.contains(&"conversation-retention-days"));
    }

    #[test]
    fn excluded_paths_for_memory_uses_active_backend() {
        let mut cfg = Config::default();
        cfg.memory.backend = "sqlite".into();
        let paths = excluded_paths(&cfg, "memory");
        assert!(paths.iter().any(|p| p == "memory.qdrant."));
        assert!(paths.iter().any(|p| p == "memory.postgres."));
    }

    #[test]
    fn is_excluded_handles_sub_table_marker() {
        let excludes = vec!["memory.qdrant.".to_string(), "memory.foo".to_string()];
        // Sub-table prefix matches anything under it.
        assert!(is_excluded("memory.qdrant.url", &excludes));
        assert!(is_excluded("memory.qdrant.api-key", &excludes));
        // Exact matches still work.
        assert!(is_excluded("memory.foo", &excludes));
        // Unrelated paths don't match.
        assert!(!is_excluded("memory.postgres.url", &excludes));
        assert!(!is_excluded("memory.foobar", &excludes));
    }

    #[test]
    fn postgres_backend_hides_sqlite_and_qdrant_subsections() {
        // postgres active → hide sqlite-only knobs and qdrant subsection,
        // keep postgres subsection visible
        let ex = memory_backend_excludes("postgres");
        assert!(ex.contains(&"sqlite-open-timeout-secs"));
        assert!(ex.contains(&"conversation-retention-days"));
        assert!(ex.contains(&"qdrant."));
        assert!(!ex.contains(&"postgres."));
    }

    #[test]
    fn path_matches_prefix_requires_segment_boundary() {
        // Exact match and children.
        assert!(path_matches_prefix("agents.aaa", "agents.aaa"));
        assert!(path_matches_prefix("agents.aaa.workspace", "agents.aaa"));
        assert!(path_matches_prefix("agents.aaa.memory.limit", "agents.aaa"));
        assert!(!path_matches_prefix(
            "agents.aaalore.workspace",
            "agents.aaa"
        ));
        assert!(!path_matches_prefix(
            "agents.aaatools.identity",
            "agents.aaa"
        ));
        assert!(!path_matches_prefix("agents.aaalore", "agents.aaa"));
        // Dot-terminated prefixes keep their sub-table semantics.
        assert!(path_matches_prefix("agents.aaa.workspace", "agents.aaa."));
        assert!(!path_matches_prefix("agents.aab.workspace", "agents.aaa."));
        // Top-level sections.
        assert!(path_matches_prefix("memory.backend", "memory"));
        assert!(!path_matches_prefix("memory.backend", "mem"));
        assert!(!path_matches_prefix("unrelated", "agents.aaa"));
        // Empty prefix matches everything (no-filter semantics, parity
        // with the bare starts_with behavior it replaced).
        assert!(path_matches_prefix("anything.at.all", ""));
        assert!(path_matches_prefix("", ""));
    }
}
