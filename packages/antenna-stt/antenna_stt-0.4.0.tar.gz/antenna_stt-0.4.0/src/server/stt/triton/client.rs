//! Triton Inference Server gRPC Client
//!
//! Provides async methods for communicating with Triton Inference Server.

use std::time::Duration;
use bytes::Buf;
use tonic::transport::{Channel, Endpoint};
use tonic::{Request, Status};
use prost::Message;

use super::messages::*;

/// Triton client configuration
#[derive(Debug, Clone)]
pub struct TritonConfig {
    /// Triton server URL (e.g., "http://localhost:8001")
    pub url: String,
    /// Connection timeout
    pub connect_timeout: Duration,
    /// Request timeout
    pub request_timeout: Duration,
    /// Model name in Triton (e.g., "whisper_base")
    pub model_name: String,
    /// Model version (empty for latest)
    pub model_version: String,
}

impl Default for TritonConfig {
    fn default() -> Self {
        Self {
            url: "http://localhost:8001".to_string(),
            connect_timeout: Duration::from_secs(10),
            request_timeout: Duration::from_secs(30),
            model_name: "whisper".to_string(),
            model_version: String::new(),
        }
    }
}

/// Error type for Triton client operations
#[derive(Debug, thiserror::Error)]
pub enum TritonError {
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),

    #[error("Request failed: {0}")]
    RequestFailed(String),

    #[error("Server not ready")]
    ServerNotReady,

    #[error("Model not ready: {0}")]
    ModelNotReady(String),

    #[error("Invalid response: {0}")]
    InvalidResponse(String),

    #[error("Encoding error: {0}")]
    EncodingError(String),
}

impl From<tonic::transport::Error> for TritonError {
    fn from(e: tonic::transport::Error) -> Self {
        TritonError::ConnectionFailed(e.to_string())
    }
}

impl From<Status> for TritonError {
    fn from(e: Status) -> Self {
        TritonError::RequestFailed(format!("{}: {}", e.code(), e.message()))
    }
}

/// Triton Inference Server gRPC client
#[derive(Debug, Clone)]
pub struct TritonClient {
    channel: Channel,
    config: TritonConfig,
}

impl TritonClient {
    /// Create a new Triton client
    pub async fn new(config: TritonConfig) -> Result<Self, TritonError> {
        let endpoint = Endpoint::from_shared(config.url.clone())
            .map_err(|e| TritonError::ConnectionFailed(e.to_string()))?
            .connect_timeout(config.connect_timeout)
            .timeout(config.request_timeout);

        let channel = endpoint.connect().await?;

        Ok(Self { channel, config })
    }

    /// Create with default configuration
    pub async fn connect(url: &str) -> Result<Self, TritonError> {
        let config = TritonConfig {
            url: url.to_string(),
            ..Default::default()
        };
        Self::new(config).await
    }

    /// Check if the server is ready
    pub async fn server_ready(&self) -> Result<bool, TritonError> {
        let request = ServerReadyRequest {};
        let response = self.unary_call("/inference.GRPCInferenceService/ServerReady", request).await?;
        let parsed: ServerReadyResponse = Message::decode(response.as_slice())
            .map_err(|e| TritonError::InvalidResponse(e.to_string()))?;
        Ok(parsed.ready)
    }

    /// Check if a model is ready
    pub async fn model_ready(&self, name: &str, version: &str) -> Result<bool, TritonError> {
        let request = ModelReadyRequest {
            name: name.to_string(),
            version: version.to_string(),
        };
        let response = self.unary_call("/inference.GRPCInferenceService/ModelReady", request).await?;
        let parsed: ModelReadyResponse = Message::decode(response.as_slice())
            .map_err(|e| TritonError::InvalidResponse(e.to_string()))?;
        Ok(parsed.ready)
    }

    /// Get server metadata
    pub async fn server_metadata(&self) -> Result<ServerMetadataResponse, TritonError> {
        let request = ServerMetadataRequest {};
        let response = self.unary_call("/inference.GRPCInferenceService/ServerMetadata", request).await?;
        Message::decode(response.as_slice())
            .map_err(|e| TritonError::InvalidResponse(e.to_string()))
    }

    /// Get model metadata
    pub async fn model_metadata(&self, name: &str, version: &str) -> Result<ModelMetadataResponse, TritonError> {
        let request = ModelMetadataRequest {
            name: name.to_string(),
            version: version.to_string(),
        };
        let response = self.unary_call("/inference.GRPCInferenceService/ModelMetadata", request).await?;
        Message::decode(response.as_slice())
            .map_err(|e| TritonError::InvalidResponse(e.to_string()))
    }

    /// Run inference on the model
    pub async fn infer(&self, request: ModelInferRequest) -> Result<ModelInferResponse, TritonError> {
        let response = self.unary_call("/inference.GRPCInferenceService/ModelInfer", request).await?;
        Message::decode(response.as_slice())
            .map_err(|e| TritonError::InvalidResponse(e.to_string()))
    }

    /// Run inference with audio samples
    ///
    /// Convenience method for Whisper-style models.
    /// Expects model to have "audio" input and "text"/"tokens" outputs.
    pub async fn infer_audio(
        &self,
        audio_samples: &[f32],
        request_id: &str,
    ) -> Result<ModelInferResponse, TritonError> {
        // Convert f32 samples to bytes (little-endian)
        let audio_bytes: Vec<u8> = audio_samples
            .iter()
            .flat_map(|f| f.to_le_bytes())
            .collect();

        let request = ModelInferRequest {
            model_name: self.config.model_name.clone(),
            model_version: self.config.model_version.clone(),
            id: request_id.to_string(),
            inputs: vec![InferInputTensor {
                name: "audio".to_string(),
                datatype: "FP32".to_string(),
                shape: vec![1, audio_samples.len() as i64],
            }],
            outputs: vec![
                InferRequestedOutputTensor {
                    name: "text".to_string(),
                },
            ],
            raw_input_contents: vec![audio_bytes],
        };

        self.infer(request).await
    }

    /// Helper for unary gRPC calls
    async fn unary_call<T: Message>(&self, path: &str, request: T) -> Result<Vec<u8>, TritonError> {
        use tonic::codec::{Codec, DecodeBuf, Decoder, EncodeBuf, Encoder};

        // Create a simple codec for raw bytes
        struct RawCodec;

        impl Codec for RawCodec {
            type Encode = Vec<u8>;
            type Decode = Vec<u8>;
            type Encoder = RawEncoder;
            type Decoder = RawDecoder;

            fn encoder(&mut self) -> Self::Encoder {
                RawEncoder
            }

            fn decoder(&mut self) -> Self::Decoder {
                RawDecoder
            }
        }

        struct RawEncoder;
        impl Encoder for RawEncoder {
            type Item = Vec<u8>;
            type Error = Status;

            fn encode(&mut self, item: Self::Item, dst: &mut EncodeBuf<'_>) -> Result<(), Self::Error> {
                dst.reserve(item.len());
                dst.put_slice(&item);
                Ok(())
            }
        }

        struct RawDecoder;
        impl Decoder for RawDecoder {
            type Item = Vec<u8>;
            type Error = Status;

            fn decode(&mut self, src: &mut DecodeBuf<'_>) -> Result<Option<Self::Item>, Self::Error> {
                let data = src.chunk().to_vec();
                src.advance(data.len());
                Ok(Some(data))
            }
        }

        // Encode the request
        let mut buf = Vec::new();
        request.encode(&mut buf)
            .map_err(|e| TritonError::EncodingError(e.to_string()))?;

        // Make the call
        let mut client = tonic::client::Grpc::new(self.channel.clone());
        client.ready().await.map_err(|e| TritonError::ConnectionFailed(e.to_string()))?;

        let request = Request::new(buf);
        let response = client
            .unary(request, path.try_into().unwrap(), RawCodec)
            .await?;

        Ok(response.into_inner())
    }

    /// Get the configuration
    pub fn config(&self) -> &TritonConfig {
        &self.config
    }
}

// Need bytes trait for EncodeBuf
use bytes::BufMut;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_defaults() {
        let config = TritonConfig::default();
        assert_eq!(config.url, "http://localhost:8001");
        assert_eq!(config.model_name, "whisper");
    }

    #[test]
    fn test_triton_error_display() {
        let err = TritonError::ModelNotReady("whisper".to_string());
        assert!(err.to_string().contains("whisper"));
    }
}
