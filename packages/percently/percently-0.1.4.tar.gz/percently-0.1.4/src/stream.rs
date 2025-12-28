//! Streaming/online percentile estimation (approximate).
//!
//! This implements the P² (P-square) online quantile estimator (Jain & Chlamtac),
//! providing an approximate percentile estimate in a single pass with bounded
//! memory.

use crate::models::OrdF64;
use kolmogorov_smirnov as ks;
use pyo3::exceptions::PyStopIteration;
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyIterator;

#[derive(Debug, Clone)]
enum State {
    Empty,
    Min { n: usize, min: f64 },
    Max { n: usize, max: f64 },
    Warm { p: u8, values: Vec<f64> }, // len < 5
    P2 {
        n: [i32; 5],     // marker positions
        np: [f64; 5],    // desired marker positions
        dn: [f64; 5],    // desired position increments
        q: [f64; 5],     // marker heights
        count: usize,    // total observations
    },
}

/// Approximate, single-pass percentile estimator (bounded memory).
#[derive(Debug, Clone)]
pub struct P2Quantile {
    percentile: u8,
    state: State,
}

impl P2Quantile {
    /// Create an estimator for the given percentile in `[0, 100]`.
    pub fn new(percentile: u8) -> Self {
        let state = match percentile {
            0 => State::Empty,   // we'll switch to Min on first update
            100 => State::Empty, // we'll switch to Max on first update
            p => State::Warm {
                p,
                values: Vec::with_capacity(5),
            },
        };
        Self { percentile, state }
    }

    /// Feed one observation.
    pub fn update(&mut self, x: f64) {
        debug_assert!(
            x.is_finite(),
            "P2Quantile requires finite (non-NaN, non-infinite) floats"
        );

        match &mut self.state {
            State::Empty => match self.percentile {
                0 => {
                    self.state = State::Min { n: 1, min: x };
                }
                100 => {
                    self.state = State::Max { n: 1, max: x };
                }
                p => {
                    self.state = State::Warm {
                        p,
                        values: vec![x],
                    };
                }
            },
            State::Min { n, min } => {
                *n += 1;
                *min = min.min(x);
            }
            State::Max { n, max } => {
                *n += 1;
                *max = max.max(x);
            }
            State::Warm { p, values } => {
                values.push(x);
                if values.len() == 5 {
                    values.sort_by(|a, b| a.total_cmp(b));
                    let q = [values[0], values[1], values[2], values[3], values[4]];
                    let p_f = *p as f64 / 100.0;
                    self.state = State::P2 {
                        n: [1, 2, 3, 4, 5],
                        np: [
                            1.0,
                            1.0 + 2.0 * p_f,
                            1.0 + 4.0 * p_f,
                            3.0 + 2.0 * p_f,
                            5.0,
                        ],
                        dn: [0.0, p_f / 2.0, p_f, (1.0 + p_f) / 2.0, 1.0],
                        q,
                        count: 5,
                    };
                }
            }
            State::P2 {
                n,
                np,
                dn,
                q,
                count,
                ..
            } => {
                *count += 1;

                // Find cell k such that q[k] <= x < q[k+1], adjust extremes.
                let k = if x < q[0] {
                    q[0] = x;
                    0usize
                } else if x >= q[4] {
                    q[4] = x;
                    3usize
                } else {
                    let mut k = 0usize;
                    for i in 0..4 {
                        if q[i] <= x && x < q[i + 1] {
                            k = i;
                            break;
                        }
                    }
                    k
                };

                // Increment positions of markers above k.
                for i in (k + 1)..5 {
                    n[i] += 1;
                }

                // Update desired positions.
                for i in 0..5 {
                    np[i] += dn[i];
                }

                // Adjust heights of markers 2..4 (indices 1..3).
                for i in 1..4 {
                    let d = np[i] - (n[i] as f64);
                    if (d >= 1.0 && (n[i + 1] - n[i]) > 1)
                        || (d <= -1.0 && (n[i - 1] - n[i]) < -1)
                    {
                        let s: i32 = if d >= 1.0 { 1 } else { -1 };
                        let i_usize = i as usize;

                        let n_im1 = n[i_usize - 1] as f64;
                        let n_i = n[i_usize] as f64;
                        let n_ip1 = n[i_usize + 1] as f64;

                        let q_im1 = q[i_usize - 1];
                        let q_i = q[i_usize];
                        let q_ip1 = q[i_usize + 1];

                        let s_f = s as f64;
                        let denom = n_ip1 - n_im1;
                        let parabolic = q_i
                            + (s_f / denom)
                                * ((n_i - n_im1 + s_f) * (q_ip1 - q_i) / (n_ip1 - n_i)
                                    + (n_ip1 - n_i - s_f) * (q_i - q_im1) / (n_i - n_im1));

                        if q_im1 < parabolic && parabolic < q_ip1 {
                            q[i_usize] = parabolic;
                        } else {
                            // Linear step towards neighbor.
                            let j = (i as i32 + s) as usize;
                            q[i_usize] = q_i
                                + s_f * (q[j] - q_i) / ((n[j] - n[i_usize]) as f64);
                        }

                        n[i_usize] += s;
                    }
                }
            }
        }
    }

    /// Current estimate (if at least one sample has been seen).
    pub fn estimate(&self) -> Option<f64> {
        match &self.state {
            State::Empty => None,
            State::Min { min, .. } => Some(*min),
            State::Max { max, .. } => Some(*max),
            State::Warm { p, values } => {
                if values.is_empty() {
                    return None;
                }
                let mut wrapped: Vec<OrdF64> = values.iter().copied().map(OrdF64).collect();
                wrapped.sort();
                Some(ks::percentile(&wrapped, *p).0)
            }
            State::P2 { q, .. } => Some(q[2]),
        }
    }
}

/// Python iterator that yields running percentile estimates while consuming an input iterable.
#[pyclass]
pub struct PercentileStream {
    iter: Py<PyIterator>,
    every: usize,
    estimator: P2Quantile,
}

impl PercentileStream {
    pub fn new(iter: Py<PyIterator>, percentile: u8, every: usize) -> Self {
        Self {
            iter,
            every,
            estimator: P2Quantile::new(percentile),
        }
    }
}

#[pymethods]
impl PercentileStream {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(mut slf: PyRefMut<'_, Self>, py: Python<'_>) -> PyResult<Option<f64>> {
        let every = slf.every;
        let iter_handle = slf.iter.clone_ref(py);
        let iter = iter_handle.bind(py);
        let mut consumed = 0usize;

        while consumed < every {
            let obj = match iter.call_method0("__next__") {
                Ok(obj) => obj,
                Err(err) => {
                    if err.is_instance_of::<PyStopIteration>(py) {
                        break;
                    }
                    return Err(err);
                }
            };
            let x: f64 = obj.extract()?;
            if !x.is_finite() {
                return Err(PyValueError::new_err(
                    "percently.stream: all values must be finite floats (no NaN/inf)",
                ));
            }

            slf.estimator.update(x);
            consumed += 1;
        }

        if consumed == 0 {
            // StopIteration
            Ok(None)
        } else {
            Ok(slf.estimator.estimate())
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn exact_percentile(data: &[f64], percentile: u8) -> f64 {
        let mut wrapped: Vec<OrdF64> = data.iter().copied().map(OrdF64).collect();
        wrapped.sort();
        ks::percentile(&wrapped, percentile).0
    }

    #[test]
    fn p0_and_p100_track_running_min_max_exactly() {
        let data = [-1.0, 10.0, 3.0, 0.0, 42.0, -5.0];

        let mut min_est = P2Quantile::new(0);
        let mut max_est = P2Quantile::new(100);

        let mut running_min = f64::INFINITY;
        let mut running_max = f64::NEG_INFINITY;

        for &x in &data {
            min_est.update(x);
            max_est.update(x);

            running_min = running_min.min(x);
            running_max = running_max.max(x);

            assert_eq!(min_est.estimate().unwrap(), running_min);
            assert_eq!(max_est.estimate().unwrap(), running_max);
        }
    }

    #[test]
    fn final_estimate_is_close_to_exact_percentile() {
        // Deterministic data with duplicates and non-uniform distribution.
        let mut data = Vec::new();
        for i in 0..10_000u64 {
            // simple LCG-ish transform then fold to keep values in a sane range
            let v = i.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            let x = ((v % 10_000) as f64) / 10_000.0;
            data.push(x);
        }

        let p = 95u8;
        let exact = exact_percentile(&data, p);

        let mut est = P2Quantile::new(p);
        for &x in &data {
            est.update(x);
        }

        let approx = est.estimate().unwrap();
        let tol = 0.01; // 1% absolute tolerance in [0,1] space
        assert!(
            (approx - exact).abs() <= tol,
            "approx={approx} exact={exact} tol={tol}"
        );
    }

    #[test]
    fn running_estimate_stays_close_to_exact_at_checkpoints() {
        // Validate "yielding" semantics: as we consume a stream, the estimate
        // should remain reasonably close to the exact percentile of values seen
        // so far (checked at coarse checkpoints).
        let p = 95u8;
        let mut est = P2Quantile::new(p);

        let mut seen: Vec<f64> = Vec::new();
        seen.reserve(50_000);

        // Deterministic pseudo-random-ish stream in [0, 1).
        for i in 0..50_000u64 {
            let v = i.wrapping_mul(2862933555777941757).wrapping_add(3037000493);
            let x = ((v % 10_000) as f64) / 10_000.0;

            est.update(x);
            seen.push(x);

            // Check at increasing checkpoints to keep the test fast.
            let n = (i + 1) as usize;
            let is_checkpoint = matches!(n, 1 | 2 | 3 | 4 | 1_000 | 10_000 | 50_000);
            if is_checkpoint {
                let exact = exact_percentile(&seen, p);
                let approx = est.estimate().unwrap();

                // Tight for the exact warmup (n < 5), looser afterwards.
                let tol = if n < 5 { 0.0 } else { 0.02 };
                assert!(
                    (approx - exact).abs() <= tol,
                    "n={n} approx={approx} exact={exact} tol={tol}"
                );
            }
        }
    }
}
