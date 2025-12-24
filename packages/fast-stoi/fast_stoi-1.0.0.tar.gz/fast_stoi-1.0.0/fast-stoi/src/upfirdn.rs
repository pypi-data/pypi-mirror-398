//! Upfirdn implementation

use faer::prelude::*;

/// Upfirdn implementation to mimic scipy.signal.resample_poly
/// internal behavior (not directly scipy.signal.upfirdn).
///
/// Normalization by up is applied to conserve signal energy
pub fn upfirdn(h: &[f32], x: &[f32], up: usize, down: usize) -> Vec<f32> {
    // Compute contiguous filter phases
    let phase_length = (h.len() as f32 / up as f32).ceil() as usize;
    let mut phases = vec![0.0; phase_length * up];
    for phase in 0..up {
        for n in 0..phase_length {
            let idx = n * up + phase;
            if idx >= h.len() {
                break;
            }
            phases[phase * phase_length + n] = h[idx];
        }
    }

    // Pad the input signal with zeros to avoid bound checks during filtering
    let padding = h.len() / (2 * up); // Padding at both ends
    let mut padded_x = vec![0.0; x.len() + 2 * padding + 1]; // +1 for h / 2*up flooring
    padded_x[padding..padding + x.len()].copy_from_slice(x);

    // Create output vector
    let mut target = vec![0.0; x.len() * up / down];

    // Prepare iteration indices
    let mut phase: usize = (h.len() / 2) % up;
    let phase_step = down % up; // Phase step within 0..up
    let x_step = down / up; // Base input step
    let mut x_start: usize = 0; // Padding ensures it starts at 0

    // Iterate over target samples
    for y in target.iter_mut() {
        let p = phase * phase_length;

        *y = RowRef::<f32>::from_slice(&phases[p..p + phase_length])
            * ColRef::<f32>::from_slice(&padded_x[x_start..x_start + phase_length])
            * up as f32;

        // Update phase and input start index
        x_start += x_step;
        if phase >= phase_step {
            phase -= phase_step;
        } else {
            phase += up - phase_step;
            x_start += 1; // Carry over
        }
    }

    target
}
