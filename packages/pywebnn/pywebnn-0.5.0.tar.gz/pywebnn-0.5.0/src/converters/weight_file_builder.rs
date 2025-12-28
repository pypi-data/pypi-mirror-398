use std::collections::HashMap;

use crate::error::GraphError;

const SENTINEL: u32 = 0xDEADBEEF;
const ALIGNMENT: usize = 64;

/// Builds a CoreML weight file with proper alignment and metadata.
///
/// CoreML MLProgram requires Float16 (and other) constants to be stored in
/// external weight files with specific formatting:
/// - 64-byte alignment for each entry
/// - Metadata header (sentinel + count)
/// - Raw data bytes
/// - Padding to next boundary
///
/// Reference: chromium/src/services/webnn/coreml/graph_builder_coreml.cc
pub struct WeightFileBuilder {
    /// Binary weight data with alignment and metadata
    data: Vec<u8>,

    /// Maps operand ID to file offset for BlobFileValue references
    offsets: HashMap<u32, u64>,
}

impl WeightFileBuilder {
    /// Creates a new empty weight file builder
    pub fn new() -> Self {
        Self {
            data: Vec::new(),
            offsets: HashMap::new(),
        }
    }

    /// Adds a weight entry for an operand with proper alignment and metadata.
    ///
    /// Format per entry:
    /// - Sentinel (4 bytes): 0xDEADBEEF
    /// - Count (8 bytes): number of elements
    /// - Data (N bytes): raw bytes
    /// - Padding (M bytes): zero padding to next 64-byte boundary
    ///
    /// Returns the file offset where this weight begins (for BlobFileValue).
    pub fn add_weight(
        &mut self,
        operand_id: u32,
        element_count: usize,
        data: &[u8],
    ) -> Result<u64, GraphError> {
        // Check if we already have this operand
        if self.offsets.contains_key(&operand_id) {
            return Err(GraphError::ConversionFailed {
                format: "coreml_mlprogram".to_string(),
                reason: format!("Duplicate weight for operand {}", operand_id),
            });
        }

        // Align current position to 64-byte boundary
        let current_len = self.data.len();
        let aligned_offset = align_to_64(current_len);

        // Add padding to reach alignment
        self.data.resize(aligned_offset, 0);

        // Record offset for this weight (before writing metadata)
        let offset = self.data.len() as u64;
        self.offsets.insert(operand_id, offset);

        // Write sentinel (4 bytes, little-endian)
        self.data.extend_from_slice(&SENTINEL.to_le_bytes());

        // Write element count (8 bytes, little-endian)
        self.data
            .extend_from_slice(&(element_count as u64).to_le_bytes());

        // Write actual data
        self.data.extend_from_slice(data);

        Ok(offset)
    }

    /// Returns the file offset for a previously added weight
    #[allow(dead_code)]
    pub fn get_offset(&self, operand_id: u32) -> Option<u64> {
        self.offsets.get(&operand_id).copied()
    }

    /// Finalizes the weight file and returns the complete binary data.
    ///
    /// Adds final padding to ensure the entire file is 64-byte aligned.
    pub fn finalize(mut self) -> Vec<u8> {
        // Align final size to 64-byte boundary
        let current_len = self.data.len();
        let aligned_len = align_to_64(current_len);
        self.data.resize(aligned_len, 0);

        self.data
    }

    /// Returns true if any weights have been added
    pub fn has_weights(&self) -> bool {
        !self.offsets.is_empty()
    }

    /// Returns the current size of the weight data (may not be aligned)
    #[allow(dead_code)]
    pub fn size(&self) -> usize {
        self.data.len()
    }
}

/// Aligns an offset to the next 64-byte boundary
fn align_to_64(offset: usize) -> usize {
    (offset + (ALIGNMENT - 1)) & !(ALIGNMENT - 1)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_align_to_64() {
        assert_eq!(align_to_64(0), 0);
        assert_eq!(align_to_64(1), 64);
        assert_eq!(align_to_64(63), 64);
        assert_eq!(align_to_64(64), 64);
        assert_eq!(align_to_64(65), 128);
        assert_eq!(align_to_64(127), 128);
        assert_eq!(align_to_64(128), 128);
    }

    #[test]
    fn test_empty_builder() {
        let builder = WeightFileBuilder::new();
        assert!(!builder.has_weights());
        assert_eq!(builder.size(), 0);

        let data = builder.finalize();
        assert_eq!(data.len(), 0);
    }

    #[test]
    fn test_single_weight() {
        let mut builder = WeightFileBuilder::new();

        // Add a small weight: 3 float16 values (6 bytes)
        let data = vec![0x00, 0x3C, 0x00, 0x40, 0x00, 0x42]; // f16: 1.0, 2.0, 3.0
        let offset = builder.add_weight(0, 3, &data).unwrap();

        // First weight starts at offset 0
        assert_eq!(offset, 0);
        assert!(builder.has_weights());
        assert_eq!(builder.get_offset(0), Some(0));

        let result = builder.finalize();

        // Check structure:
        // [0-3]: sentinel (4 bytes)
        // [4-11]: count (8 bytes)
        // [12-17]: data (6 bytes)
        // [18-63]: padding (46 bytes)
        // Total: 64 bytes (aligned)

        assert_eq!(result.len(), 64);

        // Verify sentinel
        assert_eq!(&result[0..4], &SENTINEL.to_le_bytes());

        // Verify count
        assert_eq!(&result[4..12], &3u64.to_le_bytes());

        // Verify data
        assert_eq!(&result[12..18], &data[..]);

        // Verify padding is zeros
        assert!(result[18..64].iter().all(|&b| b == 0));
    }

    #[test]
    fn test_multiple_weights() {
        let mut builder = WeightFileBuilder::new();

        // Add first weight (operand 0): 2 bytes
        let data1 = vec![0xAA, 0xBB];
        let offset1 = builder.add_weight(0, 1, &data1).unwrap();

        // Add second weight (operand 1): 4 bytes
        let data2 = vec![0x11, 0x22, 0x33, 0x44];
        let offset2 = builder.add_weight(1, 2, &data2).unwrap();

        // First starts at 0, second starts at 64 (after alignment)
        assert_eq!(offset1, 0);
        assert_eq!(offset2, 64);

        // Verify offsets can be retrieved
        assert_eq!(builder.get_offset(0), Some(0));
        assert_eq!(builder.get_offset(1), Some(64));
        assert_eq!(builder.get_offset(2), None);

        let result = builder.finalize();

        // Should be at least 128 bytes (2 aligned entries)
        assert!(result.len() >= 128);
        assert_eq!(result.len() % 64, 0); // Final size is aligned

        // Verify first entry sentinel
        assert_eq!(&result[0..4], &SENTINEL.to_le_bytes());

        // Verify second entry sentinel at offset 64
        assert_eq!(&result[64..68], &SENTINEL.to_le_bytes());
    }

    #[test]
    fn test_duplicate_operand_error() {
        let mut builder = WeightFileBuilder::new();

        let data = vec![0x00, 0x01];
        builder.add_weight(0, 1, &data).unwrap();

        // Try to add same operand again
        let result = builder.add_weight(0, 1, &data);
        assert!(result.is_err());

        match result {
            Err(GraphError::ConversionFailed { reason, .. }) => {
                assert!(reason.contains("Duplicate"));
            }
            _ => panic!("Expected ConversionFailed error"),
        }
    }

    #[test]
    fn test_large_weight() {
        let mut builder = WeightFileBuilder::new();

        // Add a large weight: 100 float16 values (200 bytes)
        let data = vec![0xAB; 200];
        let offset = builder.add_weight(0, 100, &data).unwrap();

        assert_eq!(offset, 0);

        let result = builder.finalize();

        // Metadata: 12 bytes (sentinel + count)
        // Data: 200 bytes
        // Total: 212 bytes -> aligns to 256 bytes (4 * 64)
        assert_eq!(result.len(), 256);

        // Verify data is present
        assert_eq!(&result[12..212], &data[..]);
    }
}
