use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use qrcode::QrCode;
use image::Luma;
use serde::{Serialize, Deserialize};
use std::collections::HashMap;

#[derive(Serialize, Deserialize)]
struct ChunkData {
    id: usize,
    text: String,
    frame: usize,
}

#[derive(Serialize, Deserialize)]
struct ChunkMetadata {
    id: usize,
    frame: usize,
    text_length: usize,
}

#[derive(Serialize, Deserialize)]
struct IndexData {
    version: String,
    total_chunks: usize,
    total_frames: usize,
    chunks: Vec<ChunkMetadata>,
    frame_to_chunks: HashMap<usize, Vec<usize>>,
}

#[pyclass]
pub struct MemvidEncoder {
    chunks: Vec<String>,
}

#[pymethods]
impl MemvidEncoder {
    #[new]
    fn new() -> Self {
        MemvidEncoder { chunks: Vec::new() }
    }

    fn add_text(&mut self, text: String, chunk_size: usize, overlap: usize) {
        let mut start = 0;
        while start < text.len() {
            let mut end = start + chunk_size;
            if end > text.len() {
                end = text.len();
            } else {
                // Try to break at sentence boundary
                if let Some(last_period) = text[start..end].rfind('.') {
                    if last_period > (chunk_size as f64 * 0.8) as usize {
                        end = start + last_period + 1;
                    }
                }
            }
            
            let chunk = text[start..end].trim().to_string();
            if !chunk.is_empty() {
                self.chunks.push(chunk);
            }
            
            if end == text.len() {
                break;
            }
            start = end - overlap;
        }
    }

    fn build(&self, output_file: String, index_file: String) -> PyResult<()> {
        use std::process::{Command, Stdio};
        use std::io::Write;
        use std::fs::File;

        if self.chunks.is_empty() {
            return Err(PyValueError::new_err("No chunks to encode"));
        }

        // Build index data
        let mut chunks_metadata: Vec<ChunkMetadata> = Vec::new();
        let mut frame_to_chunks: HashMap<usize, Vec<usize>> = HashMap::new();

        for (i, chunk) in self.chunks.iter().enumerate() {
            chunks_metadata.push(ChunkMetadata {
                id: i,
                frame: i,
                text_length: chunk.len(),
            });
            frame_to_chunks.entry(i).or_insert_with(Vec::new).push(i);
        }

        let index_data = IndexData {
            version: "1.0".to_string(),
            total_chunks: self.chunks.len(),
            total_frames: self.chunks.len(),
            chunks: chunks_metadata,
            frame_to_chunks,
        };

        // Save index file
        let index_json = serde_json::to_string_pretty(&index_data)
            .map_err(|e| PyValueError::new_err(format!("Failed to serialize index: {}", e)))?;
        let mut file = File::create(&index_file)
            .map_err(|e| PyValueError::new_err(format!("Failed to create index file: {}", e)))?;
        file.write_all(index_json.as_bytes())
            .map_err(|e| PyValueError::new_err(format!("Failed to write index file: {}", e)))?;

        // Spawn FFmpeg process
        // Check for macOS to use hardware acceleration
        let is_macos = std::env::consts::OS == "macos";
        let codec = if is_macos { "hevc_videotoolbox" } else { "libx264" };

        // Spawn FFmpeg process
        let mut cmd = Command::new("ffmpeg");
        cmd.arg("-y")
            .arg("-f").arg("rawvideo")
            .arg("-pixel_format").arg("gray8")
            .arg("-video_size").arg("1280x720")
            .arg("-framerate").arg("30")
            .arg("-i").arg("-") // Read from stdin
            .arg("-c:v").arg(codec)
            .arg("-pix_fmt").arg("yuv420p");

        if is_macos {
             cmd.arg("-b:v").arg("5M"); // Optional bit rate for HW
        }

        let mut child = cmd.arg(&output_file)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped()) // Capture stderr for debugging
            .spawn()
            .map_err(|e| PyValueError::new_err(format!("Failed to spawn ffmpeg: {}", e)))?;

        {
            let stdin = child.stdin.as_mut().ok_or_else(|| PyValueError::new_err("Failed to open ffmpeg stdin"))?;

            // Generate and pipe frames
            for (i, chunk) in self.chunks.iter().enumerate() {
                let data = ChunkData {
                    id: i,
                    text: chunk.clone(),
                    frame: i,
                };
                let json_data = serde_json::to_string(&data).map_err(|e| PyValueError::new_err(e.to_string()))?;

                let code = QrCode::new(json_data).map_err(|e| PyValueError::new_err(e.to_string()))?;
                let image = code.render::<Luma<u8>>().build();
                let image = image::DynamicImage::ImageLuma8(image);

                // Resize while preserving aspect ratio (results in 720x720 for square)
                let resized = image.resize(1280, 720, image::imageops::FilterType::Lanczos3);
                // Convert back to luma8 buffer explicitly to match canvas
                let resized = resized.to_luma8();

                // Create 1280x720 canvas (gray background to be neutral or black)
                let mut canvas = image::ImageBuffer::from_pixel(1280, 720, Luma([0u8])); // Black background

                // Center the resized image on the canvas
                let x_offset = ((1280 - resized.width()) / 2) as i64;
                let y_offset = ((720 - resized.height()) / 2) as i64;

                image::imageops::overlay(&mut canvas, &resized, x_offset, y_offset);

                // Convert to raw gray8 bytes
                let raw_bytes = canvas.into_raw();

                stdin.write_all(&raw_bytes).map_err(|e| PyValueError::new_err(format!("Failed to write to ffmpeg stdin: {}", e)))?;
            }
        } // stdin is closed here, signaling EOF to ffmpeg

        let output = child.wait_with_output().map_err(|e| PyValueError::new_err(format!("Failed to wait on ffmpeg: {}", e)))?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(PyValueError::new_err(format!("FFmpeg encoding failed: {}", stderr)));
        }

        Ok(())
    }
    
    fn get_chunks(&self) -> Vec<String> {
        self.chunks.clone()
    }
}
