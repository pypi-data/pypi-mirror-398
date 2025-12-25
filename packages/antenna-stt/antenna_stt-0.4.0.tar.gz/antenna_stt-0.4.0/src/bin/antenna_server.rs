//! Antenna Real-Time Speech-to-Text Server
//!
//! This binary provides an HTTP/WebSocket-based real-time transcription server.
//!
//! # Usage
//!
//! ```bash
//! cargo run --bin antenna-server --features server -- --help
//! ```
//!
//! # API Endpoints
//!
//! - `GET /health` - Basic health check
//! - `GET /health/live` - Kubernetes liveness probe
//! - `GET /health/ready` - Kubernetes readiness probe
//! - `GET /health/detailed` - Detailed health info
//! - `GET /info` - Server and backend information
//! - `POST /sessions` - Create a new transcription session
//! - `GET /sessions` - List all active sessions
//! - `GET /sessions/:id` - Get session details
//! - `DELETE /sessions/:id` - Close a session
//! - `POST /sessions/:id/audio` - Send audio chunk (binary f32 data)
//! - `GET /sessions/:id/ws` - WebSocket for real-time transcripts

use std::env;
use std::sync::Arc;
use std::time::Duration;

use antenna::server::{
    create_router, AppState, ServerConfig, SttBackend,
    stt::{WhisperBackend, WhisperBackendConfig},
};

#[tokio::main]
async fn main() {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("antenna=info".parse().unwrap())
                .add_directive("tower_http=debug".parse().unwrap()),
        )
        .init();

    // Parse arguments
    let args: Vec<String> = env::args().collect();

    if args.len() > 1 && (args[1] == "--help" || args[1] == "-h") {
        print_help();
        return;
    }

    println!("Antenna STT Server v{}", env!("CARGO_PKG_VERSION"));
    println!();

    // Parse options
    let model_size = get_arg(&args, "--model").unwrap_or("base".to_string());
    let device = get_arg(&args, "--device").unwrap_or("cpu".to_string());
    let host = get_arg(&args, "--host").unwrap_or("0.0.0.0".to_string());
    let port: u16 = get_arg(&args, "--port")
        .and_then(|p| p.parse().ok())
        .unwrap_or(8080);
    let shutdown_timeout: u64 = get_arg(&args, "--shutdown-timeout")
        .and_then(|t| t.parse().ok())
        .unwrap_or(30);

    println!("Configuration:");
    println!("  Model: {}", model_size);
    println!("  Device: {}", device);
    println!("  Host: {}", host);
    println!("  Port: {}", port);
    println!("  Shutdown timeout: {}s", shutdown_timeout);
    println!();

    // Initialize backend
    println!("Loading Whisper model...");
    let config = WhisperBackendConfig {
        model_size: model_size.clone(),
        device: device.clone(),
        ..Default::default()
    };

    let backend = match WhisperBackend::new(config) {
        Ok(backend) => {
            let info = backend.info();
            println!("Backend initialized:");
            println!("  Name: {}", info.name);
            println!("  Model: {}", info.model);
            println!("  Device: {}", info.device);
            println!("  Streaming: {}", info.capabilities.streaming);
            println!("  Language detection: {}", info.capabilities.language_detection);
            println!("  Translation: {}", info.capabilities.translation);
            println!();
            Arc::new(backend)
        }
        Err(e) => {
            eprintln!("Failed to initialize backend: {}", e);
            std::process::exit(1);
        }
    };

    // Create application state
    let state = Arc::new(AppState::new(backend));

    // Create router
    let app = create_router(state.clone());

    // Create server config
    let server_config = ServerConfig {
        host: host.clone(),
        port,
        trace_requests: true,
    };

    // Start server
    let bind_addr = server_config.bind_addr();
    println!("Starting HTTP server...");
    println!();
    println!("Server running on http://{}", bind_addr);
    println!();
    println!("Endpoints:");
    println!("  GET  /health              - Basic health check");
    println!("  GET  /health/live         - Liveness probe");
    println!("  GET  /health/ready        - Readiness probe");
    println!("  GET  /health/detailed     - Detailed health info");
    println!("  GET  /info                - Server info");
    println!("  POST /sessions            - Create session");
    println!("  GET  /sessions            - List sessions");
    println!("  GET  /sessions/:id        - Get session");
    println!("  DEL  /sessions/:id        - Close session");
    println!("  POST /sessions/:id/audio  - Send audio");
    println!("  GET  /sessions/:id/ws     - WebSocket");
    println!();
    println!("Press Ctrl+C to initiate graceful shutdown.");
    println!();

    let listener = tokio::net::TcpListener::bind(&bind_addr)
        .await
        .expect("Failed to bind to address");

    // Set up graceful shutdown
    let shutdown_timeout = Duration::from_secs(shutdown_timeout);
    let state_for_shutdown = state.clone();

    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal(shutdown_timeout, state_for_shutdown))
        .await
        .expect("Server error");

    println!();
    println!("Server shutdown complete.");
}

/// Graceful shutdown signal handler
async fn shutdown_signal(timeout: Duration, state: Arc<AppState<WhisperBackend>>) {
    // Wait for Ctrl+C or SIGTERM
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("Failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("Failed to install SIGTERM handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {
            println!();
            tracing::info!("Received Ctrl+C, initiating graceful shutdown...");
        },
        _ = terminate => {
            println!();
            tracing::info!("Received SIGTERM, initiating graceful shutdown...");
        },
    }

    // Report active sessions
    let session_count = state.session_manager.session_count();
    if session_count > 0 {
        tracing::info!("Closing {} active session(s)...", session_count);

        // Give sessions time to complete gracefully
        let start = std::time::Instant::now();
        while state.session_manager.session_count() > 0 {
            if start.elapsed() > timeout {
                tracing::warn!(
                    "Shutdown timeout reached, {} session(s) forcefully closed",
                    state.session_manager.session_count()
                );
                break;
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    }

    tracing::info!("Graceful shutdown complete");
}

fn get_arg(args: &[String], name: &str) -> Option<String> {
    args.iter()
        .position(|a| a == name)
        .and_then(|i| args.get(i + 1))
        .cloned()
}

fn print_help() {
    println!("Antenna Real-Time STT Server");
    println!();
    println!("USAGE:");
    println!("    antenna-server [OPTIONS]");
    println!();
    println!("OPTIONS:");
    println!("    --model <SIZE>           Whisper model size (tiny, base, small, medium, large)");
    println!("                             Default: base");
    println!("    --device <DEV>           Device to run on (cpu, cuda, cuda:0, cuda:1)");
    println!("                             Default: cpu");
    println!("    --host <HOST>            Host to bind to");
    println!("                             Default: 0.0.0.0");
    println!("    --port <PORT>            Port to listen on");
    println!("                             Default: 8080");
    println!("    --shutdown-timeout <S>   Graceful shutdown timeout in seconds");
    println!("                             Default: 30");
    println!("    -h, --help               Print this help message");
    println!();
    println!("ENVIRONMENT:");
    println!("    RUST_LOG          Log level (e.g., antenna=debug,tower_http=trace)");
    println!();
    println!("EXAMPLES:");
    println!("    antenna-server --model tiny --device cpu");
    println!("    antenna-server --model base --device cuda --port 3000");
    println!("    antenna-server --shutdown-timeout 60");
    println!();
    println!("API ENDPOINTS:");
    println!("    GET  /health              Basic health check");
    println!("    GET  /health/live         Kubernetes liveness probe");
    println!("    GET  /health/ready        Kubernetes readiness probe");
    println!("    GET  /health/detailed     Detailed health with metrics");
    println!("    GET  /info                Server and backend information");
    println!("    POST /sessions            Create a new transcription session");
    println!("    GET  /sessions            List all active sessions");
    println!("    GET  /sessions/:id        Get session details");
    println!("    DEL  /sessions/:id        Close a session");
    println!("    POST /sessions/:id/audio  Send audio chunk (binary f32 LE)");
    println!("    GET  /sessions/:id/ws     WebSocket for real-time transcripts");
}
