mod auth_service;
mod router_service;

/// Runs the Auth and Router services
fn main() {
    println!(
        "Starting Bridge: the combined Auth and Router service.\nSwitching console output to logger."
    );

    // Start logs
    init_logger();

    // Block main thread and run service
    match tokio::runtime::Runtime::new() {
        Ok(runtime) => {
            log::debug!("Successfully started Tokio runtime.");
            runtime.block_on(async move { router_service::run().await });
        }
        Err(e) => {
            log::error!("Failed to start Tokio runtime. Reason: {e}");
        }
    }
}

/// Initialise logging with relevant level for release type
/// - Dev mode -> Include Debug messages
/// - Release mode -> No more detailed than Info messages
fn init_logger() {
    if let Err(e) = {
        if cfg!(debug_assertions) {
            simple_logger::init_with_level(log::Level::Debug)
        } else {
            simple_logger::init_with_level(log::Level::Info)
        }
    } {
        println!("Failed to launch logger. Reason: {e}");
    }
}
