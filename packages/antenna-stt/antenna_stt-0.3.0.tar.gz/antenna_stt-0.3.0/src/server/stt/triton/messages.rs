//! Triton gRPC message types
//!
//! Manually defined protobuf-compatible types for Triton's inference API.
//! Based on: https://github.com/triton-inference-server/common/tree/main/protobuf

use prost::Message;

/// Inference request for a model
#[derive(Clone, PartialEq, Message)]
pub struct ModelInferRequest {
    /// Model name
    #[prost(string, tag = "1")]
    pub model_name: String,

    /// Model version (empty for latest)
    #[prost(string, tag = "2")]
    pub model_version: String,

    /// Request ID for tracking
    #[prost(string, tag = "3")]
    pub id: String,

    /// Input tensors
    #[prost(message, repeated, tag = "5")]
    pub inputs: Vec<InferInputTensor>,

    /// Requested output tensors
    #[prost(message, repeated, tag = "6")]
    pub outputs: Vec<InferRequestedOutputTensor>,

    /// Raw input contents (binary data)
    #[prost(bytes = "vec", repeated, tag = "7")]
    pub raw_input_contents: Vec<Vec<u8>>,
}

/// Inference response from a model
#[derive(Clone, PartialEq, Message)]
pub struct ModelInferResponse {
    /// Model name
    #[prost(string, tag = "1")]
    pub model_name: String,

    /// Model version
    #[prost(string, tag = "2")]
    pub model_version: String,

    /// Request ID
    #[prost(string, tag = "3")]
    pub id: String,

    /// Output tensors
    #[prost(message, repeated, tag = "5")]
    pub outputs: Vec<InferOutputTensor>,

    /// Raw output contents (binary data)
    #[prost(bytes = "vec", repeated, tag = "6")]
    pub raw_output_contents: Vec<Vec<u8>>,
}

/// Input tensor specification
#[derive(Clone, PartialEq, Message)]
pub struct InferInputTensor {
    /// Tensor name
    #[prost(string, tag = "1")]
    pub name: String,

    /// Data type (e.g., "FP32", "INT64")
    #[prost(string, tag = "2")]
    pub datatype: String,

    /// Tensor shape
    #[prost(int64, repeated, tag = "3")]
    pub shape: Vec<i64>,
}

/// Requested output tensor
#[derive(Clone, PartialEq, Message)]
pub struct InferRequestedOutputTensor {
    /// Tensor name
    #[prost(string, tag = "1")]
    pub name: String,
}

/// Output tensor from inference
#[derive(Clone, PartialEq, Message)]
pub struct InferOutputTensor {
    /// Tensor name
    #[prost(string, tag = "1")]
    pub name: String,

    /// Data type
    #[prost(string, tag = "2")]
    pub datatype: String,

    /// Tensor shape
    #[prost(int64, repeated, tag = "3")]
    pub shape: Vec<i64>,
}

/// Server readiness check request
#[derive(Clone, PartialEq, Message)]
pub struct ServerReadyRequest {}

/// Server readiness response
#[derive(Clone, PartialEq, Message)]
pub struct ServerReadyResponse {
    #[prost(bool, tag = "1")]
    pub ready: bool,
}

/// Model readiness check request
#[derive(Clone, PartialEq, Message)]
pub struct ModelReadyRequest {
    #[prost(string, tag = "1")]
    pub name: String,

    #[prost(string, tag = "2")]
    pub version: String,
}

/// Model readiness response
#[derive(Clone, PartialEq, Message)]
pub struct ModelReadyResponse {
    #[prost(bool, tag = "1")]
    pub ready: bool,
}

/// Server metadata request
#[derive(Clone, PartialEq, Message)]
pub struct ServerMetadataRequest {}

/// Server metadata response
#[derive(Clone, PartialEq, Message)]
pub struct ServerMetadataResponse {
    #[prost(string, tag = "1")]
    pub name: String,

    #[prost(string, tag = "2")]
    pub version: String,

    #[prost(string, repeated, tag = "3")]
    pub extensions: Vec<String>,
}

/// Model metadata request
#[derive(Clone, PartialEq, Message)]
pub struct ModelMetadataRequest {
    #[prost(string, tag = "1")]
    pub name: String,

    #[prost(string, tag = "2")]
    pub version: String,
}

/// Model metadata response
#[derive(Clone, PartialEq, Message)]
pub struct ModelMetadataResponse {
    #[prost(string, tag = "1")]
    pub name: String,

    #[prost(string, repeated, tag = "2")]
    pub versions: Vec<String>,

    #[prost(string, tag = "3")]
    pub platform: String,

    #[prost(message, repeated, tag = "4")]
    pub inputs: Vec<TensorMetadata>,

    #[prost(message, repeated, tag = "5")]
    pub outputs: Vec<TensorMetadata>,
}

/// Tensor metadata
#[derive(Clone, PartialEq, Message)]
pub struct TensorMetadata {
    #[prost(string, tag = "1")]
    pub name: String,

    #[prost(string, tag = "2")]
    pub datatype: String,

    #[prost(int64, repeated, tag = "3")]
    pub shape: Vec<i64>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_infer_request_creation() {
        let request = ModelInferRequest {
            model_name: "whisper".to_string(),
            model_version: "".to_string(),
            id: "test-123".to_string(),
            inputs: vec![InferInputTensor {
                name: "audio".to_string(),
                datatype: "FP32".to_string(),
                shape: vec![1, 16000],
            }],
            outputs: vec![InferRequestedOutputTensor {
                name: "text".to_string(),
            }],
            raw_input_contents: vec![],
        };

        assert_eq!(request.model_name, "whisper");
    }
}
