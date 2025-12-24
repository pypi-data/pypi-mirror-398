use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::process::{Command, Stdio};
use rayon::prelude::*;

#[derive(Serialize, Deserialize, Clone)]
pub struct DecodedChunk {
    pub id: usize,
    pub text: String,
    pub frame: usize,
}

#[pyclass]
pub struct MemvidDecoder {
    video_path: String,
    index_path: String,
    frame_count: usize,
    #[pyo3(get)]
    total_chunks: usize,
}

#[pymethods]
impl MemvidDecoder {
    #[new]
    fn new(video_path: String, index_path: String) -> PyResult<Self> {
        // Load index to get frame count
        let index_content = std::fs::read_to_string(&index_path)
            .map_err(|e| PyValueError::new_err(format!("Failed to read index file: {}", e)))?;

        let index_data: serde_json::Value = serde_json::from_str(&index_content)
            .map_err(|e| PyValueError::new_err(format!("Failed to parse index file: {}", e)))?;

        let total_frames = index_data["total_frames"].as_u64().unwrap_or(0) as usize;
        let total_chunks = index_data["total_chunks"].as_u64().unwrap_or(0) as usize;

        Ok(MemvidDecoder {
            video_path,
            index_path,
            frame_count: total_frames,
            total_chunks,
        })
    }

    fn decode_frame(&self, frame_number: usize) -> PyResult<Option<String>> {
        let frame_data = self.extract_frame(frame_number)?;

        match self.decode_qr_from_bytes(&frame_data) {
            Ok(text) => Ok(Some(text)),
            Err(_) => Ok(None),
        }
    }

    fn decode_frames(&self, frame_numbers: Vec<usize>) -> PyResult<HashMap<usize, String>> {
        let results: Vec<(usize, Option<String>)> = frame_numbers
            .par_iter()
            .map(|&frame_num| {
                let result = self.extract_frame(frame_num)
                    .ok()
                    .and_then(|data| self.decode_qr_from_bytes(&data).ok());
                (frame_num, result)
            })
            .collect();

        let mut map = HashMap::new();
        for (frame_num, text) in results {
            if let Some(t) = text {
                map.insert(frame_num, t);
            }
        }
        Ok(map)
    }

    fn get_chunk_text(&self, chunk_id: usize) -> PyResult<Option<String>> {
        // In current implementation, chunk_id == frame_number
        let decoded = self.decode_frame(chunk_id)?;

        if let Some(json_str) = decoded {
            let data: serde_json::Value = serde_json::from_str(&json_str)
                .map_err(|e| PyValueError::new_err(format!("Failed to parse QR data: {}", e)))?;

            if let Some(text) = data["text"].as_str() {
                return Ok(Some(text.to_string()));
            }
        }

        Ok(None)
    }

    fn get_chunks_text(&self, chunk_ids: Vec<usize>) -> PyResult<HashMap<usize, String>> {
        let decoded = self.decode_frames(chunk_ids)?;

        let mut result = HashMap::new();
        for (frame_num, json_str) in decoded {
            if let Ok(data) = serde_json::from_str::<serde_json::Value>(&json_str) {
                if let Some(text) = data["text"].as_str() {
                    result.insert(frame_num, text.to_string());
                }
            }
        }

        Ok(result)
    }

    fn get_all_chunks(&self) -> PyResult<Vec<String>> {
        let frame_numbers: Vec<usize> = (0..self.frame_count).collect();
        let decoded = self.decode_frames(frame_numbers)?;

        let mut chunks: Vec<(usize, String)> = Vec::new();
        for (frame_num, json_str) in decoded {
            if let Ok(data) = serde_json::from_str::<serde_json::Value>(&json_str) {
                if let Some(text) = data["text"].as_str() {
                    chunks.push((frame_num, text.to_string()));
                }
            }
        }

        // Sort by frame number
        chunks.sort_by_key(|(num, _)| *num);
        Ok(chunks.into_iter().map(|(_, text)| text).collect())
    }

    fn get_video_info(&self) -> PyResult<HashMap<String, usize>> {
        let mut info = HashMap::new();
        info.insert("total_frames".to_string(), self.frame_count);
        info.insert("total_chunks".to_string(), self.total_chunks);
        Ok(info)
    }
}

impl MemvidDecoder {
    fn extract_frame(&self, frame_number: usize) -> PyResult<Vec<u8>> {
        // Use FFmpeg to extract a single frame as raw gray8 data
        let timestamp = frame_number as f64 / 30.0; // Assuming 30fps

        let output = Command::new("ffmpeg")
            .arg("-ss").arg(format!("{:.3}", timestamp))
            .arg("-i").arg(&self.video_path)
            .arg("-vframes").arg("1")
            .arg("-f").arg("rawvideo")
            .arg("-pix_fmt").arg("gray")
            .arg("-")
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .output()
            .map_err(|e| PyValueError::new_err(format!("Failed to run ffmpeg: {}", e)))?;

        if !output.status.success() {
            return Err(PyValueError::new_err(format!("FFmpeg failed to extract frame {}", frame_number)));
        }

        Ok(output.stdout)
    }

    fn decode_qr_from_bytes(&self, data: &[u8]) -> Result<String, String> {
        // Expected frame size: 1280x720 gray8
        let width = 1280usize;
        let height = 720usize;

        if data.len() < width * height {
            return Err("Invalid frame data size".to_string());
        }

        // Create grayscale image from raw bytes
        let img = image::GrayImage::from_raw(width as u32, height as u32, data[..width*height].to_vec())
            .ok_or("Failed to create image from frame data")?;

        // Prepare image for rqrr
        let mut prepared = rqrr::PreparedImage::prepare(img);

        // Find and decode QR codes
        let grids = prepared.detect_grids();

        if grids.is_empty() {
            return Err("No QR code found in frame".to_string());
        }

        // Decode the first QR code found
        let (_, content) = grids[0].decode()
            .map_err(|e| format!("Failed to decode QR: {:?}", e))?;

        Ok(content)
    }
}
