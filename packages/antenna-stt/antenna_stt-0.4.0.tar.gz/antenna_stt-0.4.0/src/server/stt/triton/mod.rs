//! Triton Inference Server Client
//!
//! Provides a gRPC client for NVIDIA Triton Inference Server.
//! Used for production deployments with dynamic batching and TensorRT optimization.

mod client;
mod messages;

pub use client::{TritonClient, TritonConfig, TritonError};
pub use messages::*;
